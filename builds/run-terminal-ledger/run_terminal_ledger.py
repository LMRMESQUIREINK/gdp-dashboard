"""Standalone reimplementation of DeerFlow's authoritative run-terminal-outcome
protocol (bytedance/deer-flow, backend/packages/harness/deerflow/runtime/events/
terminal.py + backend/docs/RUN_EVENT_STREAM.md), built from reading the real
source, not guessed from the docs prose alone.

The property this protects: a long-running agent run has exactly one true
final outcome (success/error/interrupted/timeout), but two different code
paths can each think they are the one allowed to record it -- the Worker that
actually ran it, and a separate recovery process that takes over after a
crash. If both are allowed to write, or the same Worker retries a lost
acknowledgement and writes twice, the ledger can end up with two
contradictory "final" answers for one run. This module makes that
structurally impossible: the terminal row is a singleton confirmed through an
atomic check-and-insert, and a recovery process may publish one only by first
winning a one-shot takeover claim that can never be exercised twice.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

TERMINAL_STATUSES = frozenset({"success", "error", "interrupted", "timeout"})
PROTOCOL_VERSION = 1


class LifecycleRejected(Exception):
    """Raised by a lifecycle guard to refuse publication (e.g. the run's
    parent record was deleted, or the caller no longer owns the run)."""


class RecoveryTargetConsumed(RuntimeError):
    """A one-shot recovery takeover target was published more than once."""


class TerminalConfirmation(Enum):
    CONFIRMED_NEW = "CONFIRMED_NEW"
    CONFIRMED_EXISTING = "CONFIRMED_EXISTING"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"

    @property
    def confirmed(self) -> bool:
        return self in (TerminalConfirmation.CONFIRMED_NEW, TerminalConfirmation.CONFIRMED_EXISTING)


@dataclass(frozen=True)
class TerminalEvent:
    thread_id: str
    run_id: str
    seq: int
    status: str
    recovered: bool
    protocol_version: int


class TerminalLedger:
    """SQLite-backed store for terminal events and the thread-global seq
    watermark. SQLite's own UNIQUE constraint is the real atomic
    check-and-insert -- not an in-process lock -- so this holds correctly
    across multiple OS threads or processes sharing one database file,
    matching the source doc's own claim: "JSONL only provides this guarantee
    within one process; shared multi-process deployments must use the
    database store."
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._write_lock = threading.Lock()
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS terminal_events (
                thread_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                seq INTEGER NOT NULL,
                status TEXT NOT NULL,
                recovered INTEGER NOT NULL,
                protocol_version INTEGER NOT NULL,
                PRIMARY KEY (thread_id, run_id, event_type)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS thread_seq_watermark (
                thread_id TEXT PRIMARY KEY,
                next_seq INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def _next_seq(self, thread_id: str) -> int:
        # Deleting a run's events must never lower this: the watermark row
        # is independent of the event rows themselves, so a delete-then-
        # reinsert on the same thread still allocates seq numbers strictly
        # above everything ever handed out for that thread.
        cur = self._conn.execute(
            "SELECT next_seq FROM thread_seq_watermark WHERE thread_id = ?", (thread_id,)
        )
        row = cur.fetchone()
        current = row[0] if row else 1
        self._conn.execute(
            "INSERT INTO thread_seq_watermark (thread_id, next_seq) VALUES (?, ?) "
            "ON CONFLICT(thread_id) DO UPDATE SET next_seq = excluded.next_seq",
            (thread_id, current + 1),
        )
        return current

    def put_if_absent(
        self,
        *,
        thread_id: str,
        run_id: str,
        status: str,
        recovered: bool,
        lifecycle_guard: Callable[[], bool] | None = None,
    ) -> tuple[TerminalEvent, bool]:
        """Atomic check-and-insert of the (thread_id, run_id, "run.terminal")
        singleton. Returns (event, created) -- created is False when a
        matching row already existed, in which case its ORIGINAL status/
        recovered marker is returned unchanged, never overwritten."""
        with self._write_lock:
            if lifecycle_guard is not None and not lifecycle_guard():
                raise LifecycleRejected(
                    f"Run lifecycle no longer admits terminal evidence for {thread_id}/{run_id}"
                )
            cur = self._conn.execute(
                "SELECT seq, status, recovered, protocol_version FROM terminal_events "
                "WHERE thread_id = ? AND run_id = ? AND event_type = 'run.terminal'",
                (thread_id, run_id),
            )
            existing = cur.fetchone()
            if existing is not None:
                seq, existing_status, existing_recovered, version = existing
                return (
                    TerminalEvent(thread_id, run_id, seq, existing_status, bool(existing_recovered), version),
                    False,
                )
            seq = self._next_seq(thread_id)
            try:
                self._conn.execute(
                    "INSERT INTO terminal_events "
                    "(thread_id, run_id, event_type, seq, status, recovered, protocol_version) "
                    "VALUES (?, ?, 'run.terminal', ?, ?, ?, ?)",
                    (thread_id, run_id, seq, status, int(recovered), PROTOCOL_VERSION),
                )
                self._conn.commit()
            except sqlite3.IntegrityError:
                # Lost the race between the SELECT above and this INSERT --
                # someone else's row won. Re-read and report it as existing,
                # the same outcome a real lost-ACK retry should see.
                cur = self._conn.execute(
                    "SELECT seq, status, recovered, protocol_version FROM terminal_events "
                    "WHERE thread_id = ? AND run_id = ? AND event_type = 'run.terminal'",
                    (thread_id, run_id),
                )
                seq2, existing_status, existing_recovered, version = cur.fetchone()
                return (
                    TerminalEvent(thread_id, run_id, seq2, existing_status, bool(existing_recovered), version),
                    False,
                )
            return TerminalEvent(thread_id, run_id, seq, status, recovered, PROTOCOL_VERSION), True

    def delete_run(self, thread_id: str, run_id: str) -> None:
        with self._write_lock:
            self._conn.execute(
                "DELETE FROM terminal_events WHERE thread_id = ? AND run_id = ?",
                (thread_id, run_id),
            )
            self._conn.commit()


def confirm_terminal_event(
    store: TerminalLedger,
    *,
    thread_id: str,
    run_id: str,
    status: str,
    authorized: Callable[[], bool],
    recovered: bool = False,
    lifecycle_guard: Callable[[], bool] | None = None,
) -> TerminalConfirmation:
    """Confirm the singleton. One bounded retry resolves a lost ACK (the
    caller's own write landed, but the response was lost, so it retries and
    must see CONFIRMED_EXISTING rather than erroring)."""
    if status not in TERMINAL_STATUSES:
        raise ValueError(f"not a terminal status: {status!r}")
    for attempt in range(2):
        if not authorized():
            raise RuntimeError("terminal confirmation lacks an attributable final commit")
        try:
            event, created = store.put_if_absent(
                thread_id=thread_id,
                run_id=run_id,
                status=status,
                recovered=recovered,
                lifecycle_guard=lifecycle_guard,
            )
        except LifecycleRejected:
            return TerminalConfirmation.CONFLICT
        except sqlite3.OperationalError:
            if attempt == 0:
                continue
            return TerminalConfirmation.UNKNOWN
        if event.status != status:
            # A different outcome already won the singleton -- never
            # overwrite it, and never report success for a mismatch.
            return TerminalConfirmation.CONFLICT
        return TerminalConfirmation.CONFIRMED_NEW if created else TerminalConfirmation.CONFIRMED_EXISTING
    return TerminalConfirmation.UNKNOWN


_RECOVERY_ISSUER = object()


class RecoveryTarget:
    """One-shot authority to publish exactly one 'error' terminal, issued
    only after a genuine takeover claim succeeded elsewhere. Consuming it
    twice (two recovery processes both thinking they won, or one process
    retrying blindly) raises rather than silently publishing twice."""

    __slots__ = ("_thread_id", "_run_id", "_consumed", "_lock", "_issuer_check")

    def __init__(self, *, thread_id: str, run_id: str, _issuer: object):
        if _issuer is not _RECOVERY_ISSUER:
            raise TypeError("RecoveryTarget must be issued by RecoveryPublisher.authorize_takeover")
        object.__setattr__(self, "_thread_id", thread_id)
        object.__setattr__(self, "_run_id", run_id)
        object.__setattr__(self, "_consumed", False)
        object.__setattr__(self, "_lock", threading.Lock())

    def __setattr__(self, name, value):
        raise AttributeError("RecoveryTarget is immutable")

    @property
    def thread_id(self) -> str:
        return self._thread_id

    @property
    def run_id(self) -> str:
        return self._run_id

    def _consume(self) -> None:
        with self._lock:
            if self._consumed:
                raise RecoveryTargetConsumed(f"recovery target for run {self._run_id} already consumed")
            object.__setattr__(self, "_consumed", True)


class RecoveryPublisher:
    """Publishes one confirmed 'error' terminal per successful takeover
    claim. ``claimed`` must come from the caller's own atomic
    claim-for-takeover against its run registry -- this class never derives
    authority from a later read of that registry, only from the boolean the
    claim itself returned."""

    def __init__(self, store: TerminalLedger):
        self._store = store

    def authorize_takeover(self, *, claimed: bool, thread_id: str, run_id: str) -> RecoveryTarget | None:
        if claimed is not True:
            return None
        return RecoveryTarget(thread_id=thread_id, run_id=run_id, _issuer=_RECOVERY_ISSUER)

    def publish(self, target: RecoveryTarget, *, lifecycle_guard: Callable[[], bool] | None = None) -> TerminalConfirmation:
        if not isinstance(target, RecoveryTarget):
            raise TypeError("publish() requires a RecoveryTarget")
        target._consume()
        return confirm_terminal_event(
            self._store,
            thread_id=target.thread_id,
            run_id=target.run_id,
            status="error",
            authorized=lambda: True,
            recovered=True,
            lifecycle_guard=lifecycle_guard,
        )
