"""
A durable, SQLite-backed approval store — extends the HITL approval
pattern built last round in /builds/agent-checkpoint-layer/
(checkpoint/store.py's `approvals` table) with the one property that
pattern didn't have: binding an approval to the EXACT payload it was
requested for, via canonical-JSON + SHA-256, matching the ACP article's
own step: "The request payload is hashed using canonical JSON and
SHA-256. The approval therefore retains proof of what was requested
without storing a second copy of the business payload."

Why this matters, concretely: without payload binding, a classic bug is
possible — a human approves request A ("refund 100 AED"), and because the
approval is only keyed by an ID, request B ("refund 10,000 AED") executes
under that same approval ID if a caller resumes it with different
arguments. `verify_and_consume()` below is the check that closes that
gap: it recomputes the hash of the payload being executed NOW and
compares it to the hash that was actually approved.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    tool TEXT NOT NULL,
    operation TEXT NOT NULL,
    policy_id TEXT,
    policy_version INTEGER,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL,          -- pending | approved | denied | consumed
    approver TEXT,
    note TEXT,
    created_at REAL NOT NULL,
    decided_at REAL
);
"""


def canonical_hash(payload: dict[str, Any]) -> str:
    """SHA-256 over canonical (sorted-key, separator-fixed) JSON — the
    same two properties ("canonical JSON and SHA-256") the article
    names, so two logically-identical payloads always hash identically
    regardless of key order."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class ApprovalRecord:
    approval_id: str
    agent: str
    tool: str
    operation: str
    policy_id: Optional[str]
    policy_version: Optional[int]
    payload_hash: str
    status: str
    approver: Optional[str]
    note: Optional[str]


class ApprovalStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def create(self, *, agent: str, tool: str, operation: str, payload: dict[str, Any],
               policy_id: Optional[str], policy_version: Optional[int]) -> str:
        approval_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO approvals (approval_id, agent, tool, operation, policy_id, policy_version, "
            "payload_hash, status, approver, note, created_at, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, ?, NULL)",
            (approval_id, agent, tool, operation, policy_id, policy_version,
             canonical_hash(payload), time.time()),
        )
        self._conn.commit()
        return approval_id

    def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        row = self._conn.execute(
            "SELECT approval_id, agent, tool, operation, policy_id, policy_version, "
            "payload_hash, status, approver, note FROM approvals WHERE approval_id = ?",
            (approval_id,),
        ).fetchone()
        if row is None:
            return None
        return ApprovalRecord(*row)

    def decide(self, approval_id: str, *, approved: bool, approver: str, note: str = "") -> None:
        self._conn.execute(
            "UPDATE approvals SET status = ?, approver = ?, note = ?, decided_at = ? WHERE approval_id = ?",
            ("approved" if approved else "denied", approver, note, time.time(), approval_id),
        )
        self._conn.commit()

    def verify_and_consume(self, approval_id: str, payload: dict[str, Any]) -> ApprovalRecord:
        """Raises ValueError if the approval doesn't exist, wasn't
        approved, or — the whole point of this store — was approved for
        a DIFFERENT payload than the one being executed now. On success,
        marks the approval 'consumed' so the same approval can't be
        replayed a second time for another execution."""
        record = self.get(approval_id)
        if record is None:
            raise ValueError(f"no such approval: {approval_id}")
        if record.status == "denied":
            raise ValueError(f"approval {approval_id} was denied")
        if record.status == "consumed":
            raise ValueError(f"approval {approval_id} was already consumed")
        if record.status != "approved":
            raise ValueError(f"approval {approval_id} is not yet decided (status={record.status})")
        actual_hash = canonical_hash(payload)
        if actual_hash != record.payload_hash:
            raise ValueError(
                f"payload hash mismatch for approval {approval_id}: "
                f"approved payload hash {record.payload_hash[:12]}... != "
                f"actual payload hash {actual_hash[:12]}... — refusing to execute a "
                f"different request than the one that was approved"
            )
        self._conn.execute("UPDATE approvals SET status = 'consumed' WHERE approval_id = ?", (approval_id,))
        self._conn.commit()
        return record
