"""SQLiteMemoryStore -- the persistence layer `memory_layer.MemoryStore`
doesn't have: that store is pure in-memory, which is honest for a demo
but is the one thing standing between agent-memory-layer and an actually
deployable memory layer for a long-running agent.

Follows the exact WAL convention already established in
/builds/agent-checkpoint-layer/checkpoint/store.py: SQLite's own
write-ahead-log journal mode (crash-safe writes to the .db file itself,
enabled via PRAGMA) PLUS an app-level, append-only `transitions` table
logging every lifecycle transition a memory goes through -- not a loose
analogy to a WAL, a real one, for the same reason agent-checkpoint-layer
built one: a durable audit trail of how a record got to its current
status, not just the current status itself.

This module never duplicates memory_layer.py's own validation logic --
`transition()` and `supersede()` from that module are the single source
of truth for what's a legal state change; this module only adds "and
also persist it, and also log it" around calls to them.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

from memory_layer import (
    MemoryRecord,
    MemoryStatus,
    LIVE_STATUSES,
    transition as _transition,
    supersede as _supersede,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL,
    valid_from REAL NOT NULL,
    valid_until REAL,
    confidence REAL NOT NULL,
    importance REAL NOT NULL,
    authority TEXT NOT NULL,
    status TEXT NOT NULL,
    supersedes TEXT,
    scope TEXT NOT NULL,
    last_accessed_at REAL,
    embedding_json TEXT
);

CREATE TABLE IF NOT EXISTS transitions (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    at REAL NOT NULL
);
"""


def _record_to_row(r: MemoryRecord) -> tuple:
    embedding_json = json.dumps(list(r.embedding)) if r.embedding is not None else None
    return (
        r.memory_id, r.type, r.subject_id, r.content, r.created_at, r.valid_from,
        r.valid_until, r.confidence, r.importance, r.authority, r.status.value,
        r.supersedes, r.scope, r.last_accessed_at, embedding_json,
    )


def _row_to_record(row: tuple) -> MemoryRecord:
    (memory_id, type_, subject_id, content, created_at, valid_from, valid_until,
     confidence, importance, authority, status, supersedes, scope,
     last_accessed_at, embedding_json) = row
    embedding = tuple(json.loads(embedding_json)) if embedding_json is not None else None
    return MemoryRecord(
        memory_id=memory_id, type=type_, subject_id=subject_id, content=content,
        created_at=created_at, valid_from=valid_from, valid_until=valid_until,
        confidence=confidence, importance=importance, authority=authority,
        status=status, supersedes=supersedes, scope=scope,
        last_accessed_at=last_accessed_at, embedding=embedding,
    )


class SQLiteMemoryStore:
    """A drop-in, durable alternative to `memory_layer.MemoryStore` --
    same `add`/`get`/`live_for_subject`/`supersede` surface, backed by a
    SQLite file instead of a plain dict, so state survives a process
    restart. A fresh instance pointed at the same db_path, in a BRAND NEW
    process, sees exactly what the previous process wrote -- that's the
    property this class exists to provide, proven in test_persistence.py
    via a real subprocess, not just a second in-process object.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def add(self, record: MemoryRecord) -> None:
        existing = self._conn.execute(
            "SELECT 1 FROM memories WHERE memory_id = ?", (record.memory_id,)
        ).fetchone()
        if existing is not None:
            raise ValueError(f"memory_id {record.memory_id!r} already exists")
        self._conn.execute(
            "INSERT INTO memories (memory_id, type, subject_id, content, created_at, "
            "valid_from, valid_until, confidence, importance, authority, status, "
            "supersedes, scope, last_accessed_at, embedding_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            _record_to_row(record),
        )
        self._conn.execute(
            "INSERT INTO transitions (memory_id, from_status, to_status, at) VALUES (?, ?, ?, ?)",
            (record.memory_id, "(none)", record.status.value, time.time()),
        )
        self._conn.commit()

    def get(self, memory_id: str) -> MemoryRecord:
        row = self._conn.execute(
            "SELECT memory_id, type, subject_id, content, created_at, valid_from, "
            "valid_until, confidence, importance, authority, status, supersedes, "
            "scope, last_accessed_at, embedding_json FROM memories WHERE memory_id = ?",
            (memory_id,),
        ).fetchone()
        if row is None:
            raise KeyError(memory_id)
        return _row_to_record(row)

    def _save(self, record: MemoryRecord) -> None:
        self._conn.execute(
            "UPDATE memories SET type=?, subject_id=?, content=?, created_at=?, "
            "valid_from=?, valid_until=?, confidence=?, importance=?, authority=?, "
            "status=?, supersedes=?, scope=?, last_accessed_at=?, embedding_json=? "
            "WHERE memory_id=?",
            _record_to_row(record)[1:] + (record.memory_id,),
        )

    def transition(self, memory_id: str, new_status: MemoryStatus) -> MemoryRecord:
        """Load, validate+apply via memory_layer.transition() (the single
        source of truth for legality), persist, and append a WAL row --
        the same "save state, log the transition" pairing
        agent-checkpoint-layer's CheckpointStore.save() does."""
        record = self.get(memory_id)
        old_status = record.status
        _transition(record, new_status)  # raises IllegalTransitionError in place, same as memory_layer
        self._save(record)
        self._conn.execute(
            "INSERT INTO transitions (memory_id, from_status, to_status, at) VALUES (?, ?, ?, ?)",
            (memory_id, old_status.value, record.status.value, time.time()),
        )
        self._conn.commit()
        return record

    def live_for_subject(self, subject_id: str) -> list[MemoryRecord]:
        placeholders = ",".join("?" for _ in LIVE_STATUSES)
        rows = self._conn.execute(
            f"SELECT memory_id, type, subject_id, content, created_at, valid_from, "
            f"valid_until, confidence, importance, authority, status, supersedes, "
            f"scope, last_accessed_at, embedding_json FROM memories "
            f"WHERE subject_id = ? AND status IN ({placeholders})",
            (subject_id, *[s.value for s in LIVE_STATUSES]),
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def supersede(self, old_id: str, new: MemoryRecord, *, now: float) -> None:
        """Mirrors MemoryStore.supersede(): load the old record, run it
        through the real memory_layer.supersede() (subject-mismatch guard
        and all), then persist both sides and log the WAL transition."""
        old = self.get(old_id)
        _supersede(old, new, now=now)  # mutates `old` in place, sets new.supersedes
        self._save(old)
        self._conn.execute(
            "INSERT INTO transitions (memory_id, from_status, to_status, at) VALUES (?, ?, ?, ?)",
            (old_id, "SUPERSEDED-pending", old.status.value, now),
        )
        self.add(new)

    def transitions_for(self, memory_id: str) -> list[dict]:
        """The WAL read path -- the full, ordered history of how a
        memory reached its current status, for audit, matching
        CheckpointStore.wal_for()."""
        rows = self._conn.execute(
            "SELECT seq, from_status, to_status, at FROM transitions "
            "WHERE memory_id = ? ORDER BY seq",
            (memory_id,),
        ).fetchall()
        return [{"seq": r[0], "from_status": r[1], "to_status": r[2], "at": r[3]} for r in rows]
