"""
ask_human() / answer_clarification() — a durable, SQLite-backed
clarification primitive, matching the distinction made in "The Harness Is
the Product: How Agents Are Actually Built in 2026" (Andrii Tkachuk) —
see /notes/harness-is-the-product-analysis.md:

    "Model-initiated clarification and policy-enforced approval look
    similar on screen, but they belong to different layers."

This project already had the policy-enforced half (`governed_call`'s
REQUIRES_APPROVAL path, `approval_store.py`) before this round, built
from a different source two rounds ago. What it didn't have is this
half: a primitive the MODEL itself calls, voluntarily, when it's missing
information it needs before it can even construct a sensible payload —
"which month to report on," "which of two connected task systems to use,"
whether "the payments service" means staging or production. The article's
own architectural point is that these are NOT the same mechanism wearing
two faces, and conflating them is a real risk: approval must never depend
on the model choosing to ask for it, so it is deliberately a harness-
enforced interception (`governed_call`), never a model-callable primitive;
`ask_human` is the opposite -- optional, model-initiated, and has nothing
to do with risk policy.

Deliberately a SEPARATE store with its own table, not a second status
value bolted onto `approvals` -- answering a clarification must never be
able to satisfy, consume, or otherwise touch a pending approval, and vice
versa. test_clarification.py proves this with a cross-contamination check,
not just by reading the schema.
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
CREATE TABLE IF NOT EXISTS clarifications (
    clarification_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    question TEXT NOT NULL,
    options_json TEXT,
    context_json TEXT,
    status TEXT NOT NULL,          -- pending | answered
    answer TEXT,
    created_at REAL NOT NULL,
    answered_at REAL
);
"""


@dataclass
class ClarificationRecord:
    clarification_id: str
    agent: str
    question: str
    options: Optional[list[str]]
    context: dict[str, Any]
    status: str
    answer: Optional[str]


class ClarificationStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def ask(self, *, agent: str, question: str, options: Optional[list[str]] = None,
            context: Optional[dict[str, Any]] = None) -> str:
        """The model-initiated primitive itself. Creates a pending
        clarification and returns its id -- the agent's turn ends here
        until a human answers, same pause-and-resume shape as
        `governed_call`'s pending_approval path, but an entirely separate
        table and id space."""
        clarification_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO clarifications (clarification_id, agent, question, options_json, "
            "context_json, status, answer, created_at, answered_at) "
            "VALUES (?, ?, ?, ?, ?, 'pending', NULL, ?, NULL)",
            (clarification_id, agent, question,
             json.dumps(options) if options is not None else None,
             json.dumps(context or {}), time.time()),
        )
        self._conn.commit()
        return clarification_id

    def get(self, clarification_id: str) -> Optional[ClarificationRecord]:
        row = self._conn.execute(
            "SELECT clarification_id, agent, question, options_json, context_json, "
            "status, answer FROM clarifications WHERE clarification_id = ?",
            (clarification_id,),
        ).fetchone()
        if row is None:
            return None
        clarification_id_, agent, question, options_json, context_json, status, answer = row
        return ClarificationRecord(
            clarification_id=clarification_id_, agent=agent, question=question,
            options=json.loads(options_json) if options_json else None,
            context=json.loads(context_json) if context_json else {},
            status=status, answer=answer,
        )

    def answer(self, clarification_id: str, answer: str) -> ClarificationRecord:
        """Called from whatever surface the question reached (a Slack
        reply, a card in Teams, a CLI prompt) -- never by the model
        itself. Raises if the id doesn't exist or was already answered,
        same replay-safety discipline as `verify_and_consume`."""
        record = self.get(clarification_id)
        if record is None:
            raise ValueError(f"no such clarification: {clarification_id}")
        if record.status != "pending":
            raise ValueError(f"clarification {clarification_id} is already {record.status}, not pending")
        if record.options is not None and answer not in record.options:
            raise ValueError(f"answer {answer!r} is not one of the offered options {record.options}")
        self._conn.execute(
            "UPDATE clarifications SET status = 'answered', answer = ?, answered_at = ? "
            "WHERE clarification_id = ?",
            (answer, time.time(), clarification_id),
        )
        self._conn.commit()
        return self.get(clarification_id)
