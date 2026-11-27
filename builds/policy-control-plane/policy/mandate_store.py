"""
mandate_store.py -- a durable, SQLite-backed Mandate: a grant of
authority that, unlike `ApprovalRecord` (one-shot: pending -> approved ->
consumed, spent the moment it's used), persists across a long-running
unit of work ending and resuming many times.

Read directly from this project's own `/builds/dsh-thread-mandate/`
(itself read from `deepseek-ai/dsh-superagent-prototype`'s real domain
model), this closes the one gap that build's README named as left for
`/builds/policy-control-plane/` specifically: this build already has
payload-hash-bound, single-use approvals, but no concept of a grant that
outlives one execution. The three governing rules, carried over directly
rather than re-derived:

  - **A Mandate's end does NOT revoke it.** Ending the unit of work it
    backs is not the same event as losing authority to resume it.
  - **Only an explicit `withdraw()` or a failed revalidation AT RESUME
    revokes it.** A Policy change while the unit of work is still
    running never retroactively touches a live Mandate -- the real
    source's own stated reason ("a cancelled change leaves half-finished
    work; the change is recorded and delivered instead") is why
    `end_unit_of_work()` below never calls the evaluator at all.
  - **Revalidation reuses THIS build's own real `PolicyEvaluator`**
    (`policy/evaluator.py`) against the Mandate's ORIGINAL selector and
    context, not a second, separate ad hoc rule -- "the current policy
    set no longer grants this" means exactly the same ALLOW/DENY/
    REQUIRES_APPROVAL resolution every other call in this build already
    goes through.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .evaluator import PolicyEvaluator
from .model import Effect

SCHEMA = """
CREATE TABLE IF NOT EXISTS mandates (
    mandate_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    tool TEXT NOT NULL,
    operation TEXT NOT NULL,
    context_json TEXT NOT NULL,
    granted_policy_id TEXT,
    granted_policy_version INTEGER,
    status TEXT NOT NULL,          -- active | ended | withdrawn | revoked
    revoked_reason TEXT,
    created_at REAL NOT NULL,
    ended_at REAL,
    resumed_at REAL
);
"""


class MandateRevoked(Exception):
    """Raised by `resume_unit_of_work()` when the Mandate is either
    already withdrawn/revoked, or the current policy set no longer
    resolves its original selector to ALLOW."""


@dataclass
class MandateRecord:
    mandate_id: str
    agent: str
    tool: str
    operation: str
    context: dict[str, Any]
    granted_policy_id: Optional[str]
    granted_policy_version: Optional[int]
    status: str
    revoked_reason: Optional[str]


class MandateStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def _row_to_record(self, row) -> MandateRecord:
        (mandate_id, agent, tool, operation, context_json, policy_id, policy_version,
         status, revoked_reason) = row
        return MandateRecord(
            mandate_id=mandate_id, agent=agent, tool=tool, operation=operation,
            context=json.loads(context_json), granted_policy_id=policy_id,
            granted_policy_version=policy_version, status=status, revoked_reason=revoked_reason,
        )

    def grant(self, *, agent: str, tool: str, operation: str, context: dict[str, Any],
               policy_id: Optional[str], policy_version: Optional[int]) -> str:
        """Records a new, active Mandate. Mirrors an ALLOW decision that
        backs ongoing work, not a single call -- the caller decides when
        a decision is "ongoing work" versus a one-shot `governed_call`."""
        mandate_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO mandates (mandate_id, agent, tool, operation, context_json, "
            "granted_policy_id, granted_policy_version, status, revoked_reason, "
            "created_at, ended_at, resumed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, NULL, NULL)",
            (mandate_id, agent, tool, operation, json.dumps(context, sort_keys=True, default=str),
             policy_id, policy_version, time.time()),
        )
        self._conn.commit()
        return mandate_id

    def get(self, mandate_id: str) -> Optional[MandateRecord]:
        row = self._conn.execute(
            "SELECT mandate_id, agent, tool, operation, context_json, granted_policy_id, "
            "granted_policy_version, status, revoked_reason FROM mandates WHERE mandate_id = ?",
            (mandate_id,),
        ).fetchone()
        return None if row is None else self._row_to_record(row)

    def withdraw(self, mandate_id: str, *, reason: str = "withdrawn by a person") -> None:
        """A person's explicit withdrawal. Unconditional -- unlike
        `resume_unit_of_work()`'s revalidation, this never consults the
        evaluator, matching the real source's own distinction between a
        person's stop and a policy-driven revocation."""
        self._conn.execute(
            "UPDATE mandates SET status = 'withdrawn', revoked_reason = ? WHERE mandate_id = ?",
            (reason, mandate_id),
        )
        self._conn.commit()

    def end_unit_of_work(self, mandate_id: str) -> None:
        """The unit of work this Mandate backs has finished for now. This
        is deliberately a NO-OP on the Mandate's own standing: it does
        NOT call the evaluator, does NOT touch `status`, and does NOT
        revoke anything. Only `resume_unit_of_work()` ever re-checks
        standing -- a Mandate whose work ended, but was never resumed,
        just sits there `active`, exactly as the real source intends."""
        record = self.get(mandate_id)
        if record is None:
            raise ValueError(f"no such mandate: {mandate_id}")
        self._conn.execute("UPDATE mandates SET ended_at = ? WHERE mandate_id = ?",
                            (time.time(), mandate_id))
        self._conn.commit()

    def resume_unit_of_work(self, mandate_id: str, evaluator: PolicyEvaluator) -> MandateRecord:
        """Revalidates the Mandate against the CURRENT policy set before
        letting the unit of work pick back up. Raises `MandateRevoked`
        if: the Mandate was already withdrawn or revoked, or the
        evaluator — re-run against this Mandate's ORIGINAL (agent, tool,
        operation, context) selector, under whatever policies exist
        right now — no longer resolves to ALLOW. On a successful
        revalidation, `status` stays 'active' and `resumed_at` is
        recorded; on failure, `status` becomes 'revoked' with the
        evaluator's own reason attached, so the revocation is traceable
        to a real decision, not a bare exception.
        """
        record = self.get(mandate_id)
        if record is None:
            raise ValueError(f"no such mandate: {mandate_id}")
        if record.status in ("withdrawn", "revoked"):
            raise MandateRevoked(
                f"mandate {mandate_id} cannot resume: already {record.status} "
                f"({record.revoked_reason})"
            )

        decision = evaluator.evaluate(
            agent=record.agent, tool=record.tool, operation=record.operation,
            context=record.context,
        )
        if decision.effect is not Effect.ALLOW:
            reason = (
                f"current policy set resolves to {decision.effect.value} on resume "
                f"(originally granted under policy {record.granted_policy_id!r} "
                f"v{record.granted_policy_version}): {decision.reason}"
            )
            self._conn.execute(
                "UPDATE mandates SET status = 'revoked', revoked_reason = ? WHERE mandate_id = ?",
                (reason, mandate_id),
            )
            self._conn.commit()
            raise MandateRevoked(reason)

        self._conn.execute(
            "UPDATE mandates SET resumed_at = ? WHERE mandate_id = ?",
            (time.time(), mandate_id),
        )
        self._conn.commit()
        return self.get(mandate_id)
