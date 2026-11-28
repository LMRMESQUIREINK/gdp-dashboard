"""
mandate.py -- a durable, SQLite-backed Mandate for a checkpointed run:
a grant of approval that, unlike the boolean `approvals` table in
checkpoint/store.py (set once, read forever, never re-checked against
anything), persists across a run pausing and resuming and is
RE-VALIDATED, against whatever the current rules are, specifically at
the moment of resume.

Read directly from this project's own `/builds/policy-control-plane/
policy/mandate_store.py` (itself read from `/builds/dsh-thread-mandate/`,
read from `deepseek-ai/dsh-superagent-prototype`'s real domain model),
this applies that same pattern to a genuinely different kind of "survives
ending and resuming" state: WAL-logged checkpoint stage transitions for
ONE linear workflow, rather than a standing tool-call authorization. The
three governing rules carried over unchanged:

  - **A unit of work ending does NOT revoke its Mandate.**
    `end_unit_of_work()` is a pure no-op on `status` -- the run pausing
    for approval, or finishing a stage and stopping, is not the same
    event as losing authority to resume it.
  - **Only an explicit `withdraw()`, or a failed revalidation AT RESUME,
    revokes it.** A rule change while the run is paused never
    retroactively touches a Mandate nobody has tried to resume yet --
    `end_unit_of_work()` never consults `revalidate_fn` at all; only
    `resume_unit_of_work()` does.
  - **Revalidation reuses whatever real decision function the caller
    already uses for real** -- here, `workflow.py` wires in the SAME
    `evaluate_size()` call it already runs for real, against CURRENT
    account rules, not a second, separate ad hoc check invented just for
    this module. `mandate.py` itself stays generic: it takes a plain
    `revalidate_fn(context) -> (ok, reason)` callable, never importing
    anything prop-firm-specific, so it's reusable the same way
    `checkpoint/store.py` is reusable across different workflows.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS mandates (
    mandate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    context_json TEXT NOT NULL,
    status TEXT NOT NULL,          -- active | withdrawn | revoked
    revoked_reason TEXT,
    created_at REAL NOT NULL,
    ended_at REAL,
    resumed_at REAL
);
"""

# What the caller plugs in to say whether a Mandate's ORIGINAL context is
# still good under whatever the current rules are: (ok, reason).
RevalidateFn = Callable[[dict[str, Any]], tuple[bool, str]]


class MandateRevoked(Exception):
    """Raised by `resume_unit_of_work()` when the Mandate is already
    withdrawn/revoked, or `revalidate_fn` says the current rules no
    longer approve its original context."""


@dataclass
class MandateRecord:
    mandate_id: str
    run_id: str
    context: dict[str, Any]
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
        mandate_id, run_id, context_json, status, revoked_reason = row
        return MandateRecord(mandate_id=mandate_id, run_id=run_id,
                              context=json.loads(context_json), status=status,
                              revoked_reason=revoked_reason)

    def grant(self, run_id: str, context: dict[str, Any]) -> str:
        """Records a new, active Mandate for this run, under its context
        AT THE MOMENT OF GRANT -- the thing revalidation later checks
        against whatever rules hold at resume time, which may by then
        have changed."""
        mandate_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO mandates (mandate_id, run_id, context_json, status, revoked_reason, "
            "created_at, ended_at, resumed_at) VALUES (?, ?, ?, 'active', NULL, ?, NULL, NULL)",
            (mandate_id, run_id, json.dumps(context, sort_keys=True, default=str), time.time()),
        )
        self._conn.commit()
        return mandate_id

    def get(self, mandate_id: str) -> Optional[MandateRecord]:
        row = self._conn.execute(
            "SELECT mandate_id, run_id, context_json, status, revoked_reason "
            "FROM mandates WHERE mandate_id = ?",
            (mandate_id,),
        ).fetchone()
        return None if row is None else self._row_to_record(row)

    def get_for_run(self, run_id: str) -> Optional[MandateRecord]:
        """The most recently granted Mandate for this run. `cli.py`'s
        `approve`/`resume` are separate process invocations that only
        ever carry a run_id on the command line, never a mandate_id, so
        this is how the resuming process finds the Mandate it's
        revalidating without the caller having to thread an extra id
        across the process boundary itself."""
        row = self._conn.execute(
            "SELECT mandate_id, run_id, context_json, status, revoked_reason FROM mandates "
            "WHERE run_id = ? ORDER BY created_at DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        return None if row is None else self._row_to_record(row)

    def withdraw(self, mandate_id: str, *, reason: str = "withdrawn by a person") -> None:
        """A person's explicit withdrawal. Unconditional -- never
        consults `revalidate_fn`, matching the real source's own
        distinction between a person's stop and a rules-driven
        revocation."""
        self._conn.execute(
            "UPDATE mandates SET status = 'withdrawn', revoked_reason = ? WHERE mandate_id = ?",
            (reason, mandate_id),
        )
        self._conn.commit()

    def end_unit_of_work(self, mandate_id: str) -> None:
        """The run this Mandate backs has paused (or finished a stage)
        for now. Deliberately a pure no-op on `status`: does NOT call
        `revalidate_fn`, does NOT touch `status`. Only
        `resume_unit_of_work()` ever re-checks standing -- a Mandate
        whose run paused, but was never resumed, just sits there
        `active`."""
        record = self.get(mandate_id)
        if record is None:
            raise ValueError(f"no such mandate: {mandate_id}")
        self._conn.execute("UPDATE mandates SET ended_at = ? WHERE mandate_id = ?",
                            (time.time(), mandate_id))
        self._conn.commit()

    def resume_unit_of_work(self, mandate_id: str, revalidate_fn: RevalidateFn) -> MandateRecord:
        """Revalidates the Mandate's ORIGINAL context against whatever
        `revalidate_fn` says the current rules allow, before letting the
        run pick back up. Raises `MandateRevoked` if: the Mandate was
        already withdrawn/revoked (checked BEFORE `revalidate_fn` is even
        called -- a withdrawal always wins, regardless of what the
        current rules would say), or `revalidate_fn` returns `ok=False`.
        On success, `status` stays `active` and `resumed_at` is recorded;
        on failure, `status` becomes `revoked` with `revalidate_fn`'s own
        reason attached, so the revocation is traceable to a real
        decision, not a bare exception.
        """
        record = self.get(mandate_id)
        if record is None:
            raise ValueError(f"no such mandate: {mandate_id}")
        if record.status in ("withdrawn", "revoked"):
            raise MandateRevoked(
                f"mandate {mandate_id} cannot resume: already {record.status} "
                f"({record.revoked_reason})"
            )

        ok, reason = revalidate_fn(record.context)
        if not ok:
            full_reason = f"current rules no longer approve this mandate's original context: {reason}"
            self._conn.execute(
                "UPDATE mandates SET status = 'revoked', revoked_reason = ? WHERE mandate_id = ?",
                (full_reason, mandate_id),
            )
            self._conn.commit()
            raise MandateRevoked(full_reason)

        self._conn.execute(
            "UPDATE mandates SET resumed_at = ? WHERE mandate_id = ?",
            (time.time(), mandate_id),
        )
        self._conn.commit()
        return self.get(mandate_id)
