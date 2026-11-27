"""
A durable checkpoint store — the one piece of
/notes/agentic-harness-frameworks-analysis.md's five-layer taxonomy this
project was missing for real: "this logic of managing workflow pausing,
resuming and checkpointing is very complex and MUST be there." Implements
the article's own six-step list literally:

  1. Save the context and state of the LLM/workflow in the DB
  2. Generate a unique UUID for the workflow state
  3. (the caller generates a partial response for the user — workflow.py)
  4. Find the workflow in the DB (by that UUID)
  5. Reinstate the workflow state and context
  6. Start executing again from that point onwards
     (looping back to the same HITL gate if approval still isn't granted)

Two senses of "WAL" meet here, deliberately: SQLite's own write-ahead-log
journal mode (crash-safe writes to the .db file itself, enabled below via
PRAGMA) and the app-level `wal` table, an append-only log of every stage
transition a run goes through — the article's own "Checkpoints & WALs"
concept, implemented as a real table rather than a loose analogy.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,           -- running | paused_for_approval | approved | completed | failed
    context_json TEXT NOT NULL,     -- the reinstated "context" the article's step 5 talks about
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS wal (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT,
    at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    run_id TEXT PRIMARY KEY,
    granted INTEGER NOT NULL,
    note TEXT,
    at REAL NOT NULL
);
"""


@dataclass
class RunState:
    run_id: str
    stage: str
    status: str
    context: dict[str, Any]
    updated_at: float


class CheckpointStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def new_run_id(self) -> str:
        return str(uuid.uuid4())

    def save(self, run_id: str, stage: str, status: str, context: dict[str, Any], note: str = "") -> None:
        """Step 1+2 of the article's list: persist the run's state and
        context under its UUID, and append the transition to the WAL so
        the full history of how it got here is never lost, only the
        latest snapshot is overwritten."""
        now = time.time()
        self._conn.execute(
            "INSERT INTO runs (run_id, stage, status, context_json, updated_at) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(run_id) DO UPDATE SET stage=excluded.stage, status=excluded.status, "
            "context_json=excluded.context_json, updated_at=excluded.updated_at",
            (run_id, stage, status, json.dumps(context), now),
        )
        self._conn.execute(
            "INSERT INTO wal (run_id, stage, status, note, at) VALUES (?, ?, ?, ?, ?)",
            (run_id, stage, status, note, now),
        )
        self._conn.commit()

    def load(self, run_id: str) -> Optional[RunState]:
        """Steps 4+5: find the run by its UUID and reinstate its state
        and context exactly as last saved."""
        row = self._conn.execute(
            "SELECT run_id, stage, status, context_json, updated_at FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        run_id, stage, status, context_json, updated_at = row
        return RunState(run_id=run_id, stage=stage, status=status,
                         context=json.loads(context_json), updated_at=updated_at)

    def wal_for(self, run_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT seq, stage, status, note, at FROM wal WHERE run_id = ? ORDER BY seq",
            (run_id,),
        ).fetchall()
        return [{"seq": r[0], "stage": r[1], "status": r[2], "note": r[3], "at": r[4]} for r in rows]

    def request_approval(self, run_id: str) -> None:
        self._conn.execute(
            "INSERT INTO approvals (run_id, granted, note, at) VALUES (?, 0, '', ?) "
            "ON CONFLICT(run_id) DO NOTHING",
            (run_id, time.time()),
        )
        self._conn.commit()

    def grant_approval(self, run_id: str, note: str = "") -> None:
        now = time.time()
        self._conn.execute(
            "INSERT INTO approvals (run_id, granted, note, at) VALUES (?, 1, ?, ?) "
            "ON CONFLICT(run_id) DO UPDATE SET granted=1, note=excluded.note, at=excluded.at",
            (run_id, note, now),
        )
        self._conn.commit()

    def is_approved(self, run_id: str) -> bool:
        row = self._conn.execute("SELECT granted FROM approvals WHERE run_id = ?", (run_id,)).fetchone()
        return bool(row and row[0])
