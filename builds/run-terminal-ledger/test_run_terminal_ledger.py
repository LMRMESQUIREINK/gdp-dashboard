"""Real tests for run_terminal_ledger.py -- no mocked store. Every test hits
a real SQLite file (fresh tempfile per test) through real threads where the
property under test is concurrency, not just sequential logic."""

import multiprocessing
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_terminal_ledger import (
    LifecycleRejected,
    RecoveryPublisher,
    RecoveryTargetConsumed,
    TerminalConfirmation,
    TerminalLedger,
    confirm_terminal_event,
)


def _cross_process_confirm_worker(db_path, status, start_barrier, out_queue):
    """Runs in its own OS process with its own TerminalLedger instance (own
    connection, own in-process lock) -- the ONLY thing that can prevent two
    of these from both inserting is SQLite's UNIQUE constraint on
    (thread_id, run_id, event_type), not this module's threading.Lock, since
    each process has a separate lock object entirely. This is what actually
    exercises the IntegrityError fallback path in put_if_absent()."""
    store = TerminalLedger(db_path)
    start_barrier.wait()
    result = confirm_terminal_event(
        store, thread_id="t1", run_id="cross-process-race", status=status, authorized=lambda: True
    )
    out_queue.put(result.value)
    store.close()


def fresh_store():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return TerminalLedger(path), path


class TestBasicConfirmation(unittest.TestCase):
    def setUp(self):
        self.store, self.path = fresh_store()

    def tearDown(self):
        self.store.close()
        os.unlink(self.path)
        for suffix in ("-wal", "-shm"):
            p = self.path + suffix
            if os.path.exists(p):
                os.unlink(p)

    def test_first_confirmation_is_new(self):
        result = confirm_terminal_event(
            self.store, thread_id="t1", run_id="r1", status="success", authorized=lambda: True
        )
        self.assertEqual(result, TerminalConfirmation.CONFIRMED_NEW)

    def test_retry_of_same_outcome_is_existing_not_an_error(self):
        # Simulates a Worker whose ACK was lost over the wire and retries:
        # the write already landed, so the retry must see CONFIRMED_EXISTING,
        # not a crash and not a second row.
        confirm_terminal_event(self.store, thread_id="t1", run_id="r1", status="success", authorized=lambda: True)
        result = confirm_terminal_event(
            self.store, thread_id="t1", run_id="r1", status="success", authorized=lambda: True
        )
        self.assertEqual(result, TerminalConfirmation.CONFIRMED_EXISTING)

    def test_contradictory_status_is_conflict_and_does_not_overwrite(self):
        confirm_terminal_event(self.store, thread_id="t1", run_id="r1", status="success", authorized=lambda: True)
        result = confirm_terminal_event(
            self.store, thread_id="t1", run_id="r1", status="error", authorized=lambda: True
        )
        self.assertEqual(result, TerminalConfirmation.CONFLICT)
        # The original outcome must still be the one on record.
        event, created = self.store.put_if_absent(thread_id="t1", run_id="r1", status="error", recovered=False)
        self.assertFalse(created)
        self.assertEqual(event.status, "success")

    def test_unauthorized_caller_cannot_confirm(self):
        with self.assertRaises(RuntimeError):
            confirm_terminal_event(
                self.store, thread_id="t1", run_id="r1", status="success", authorized=lambda: False
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            confirm_terminal_event(
                self.store, thread_id="t1", run_id="r1", status="not-a-real-status", authorized=lambda: True
            )

    def test_lifecycle_guard_rejection_is_conflict(self):
        result = confirm_terminal_event(
            self.store,
            thread_id="t1",
            run_id="r1",
            status="success",
            authorized=lambda: True,
            lifecycle_guard=lambda: False,
        )
        self.assertEqual(result, TerminalConfirmation.CONFLICT)
        # And nothing was actually written.
        event, created = self.store.put_if_absent(thread_id="t1", run_id="r1", status="success", recovered=False)
        self.assertTrue(created)


class TestSeqWatermark(unittest.TestCase):
    def setUp(self):
        self.store, self.path = fresh_store()

    def tearDown(self):
        self.store.close()
        os.unlink(self.path)
        for suffix in ("-wal", "-shm"):
            p = self.path + suffix
            if os.path.exists(p):
                os.unlink(p)

    def test_seq_never_reused_after_delete(self):
        event1, _ = self.store.put_if_absent(thread_id="t1", run_id="r1", status="success", recovered=False)
        first_seq = event1.seq
        self.store.delete_run("t1", "r1")
        event2, created = self.store.put_if_absent(thread_id="t1", run_id="r2", status="success", recovered=False)
        self.assertTrue(created)
        self.assertGreater(event2.seq, first_seq)

    def test_seq_is_per_thread_independent(self):
        event_a, _ = self.store.put_if_absent(thread_id="thread-a", run_id="r1", status="success", recovered=False)
        event_b, _ = self.store.put_if_absent(thread_id="thread-b", run_id="r1", status="success", recovered=False)
        # Different threads start their own watermark at 1, not sharing a
        # single global counter -- the real doc says seq is thread-global,
        # not run-local, meaning scoped to the thread, not to all threads.
        self.assertEqual(event_a.seq, 1)
        self.assertEqual(event_b.seq, 1)


class TestRecoveryTakeover(unittest.TestCase):
    def setUp(self):
        self.store, self.path = fresh_store()
        self.publisher = RecoveryPublisher(self.store)

    def tearDown(self):
        self.store.close()
        os.unlink(self.path)
        for suffix in ("-wal", "-shm"):
            p = self.path + suffix
            if os.path.exists(p):
                os.unlink(p)

    def test_no_claim_means_no_target(self):
        target = self.publisher.authorize_takeover(claimed=False, thread_id="t1", run_id="r1")
        self.assertIsNone(target)

    def test_successful_claim_publishes_recovered_error_terminal(self):
        target = self.publisher.authorize_takeover(claimed=True, thread_id="t1", run_id="r1")
        self.assertIsNotNone(target)
        result = self.publisher.publish(target)
        self.assertEqual(result, TerminalConfirmation.CONFIRMED_NEW)
        event, created = self.store.put_if_absent(thread_id="t1", run_id="r1", status="error", recovered=True)
        self.assertFalse(created)
        self.assertEqual(event.status, "error")
        self.assertTrue(event.recovered)

    def test_target_is_one_shot(self):
        target = self.publisher.authorize_takeover(claimed=True, thread_id="t1", run_id="r1")
        self.publisher.publish(target)
        with self.assertRaises(RecoveryTargetConsumed):
            self.publisher.publish(target)

    def test_two_racing_recovery_processes_each_with_their_own_claim_converge_on_one_row(self):
        # Simulates two recovery processes that both independently believe
        # they won a takeover claim (a real bug the atomic claim itself is
        # supposed to prevent, but this proves the terminal ledger is a
        # second, independent line of defense): both publish, only one row
        # should exist and both calls should report a confirmed outcome.
        target_a = self.publisher.authorize_takeover(claimed=True, thread_id="t1", run_id="r1")
        target_b = self.publisher.authorize_takeover(claimed=True, thread_id="t1", run_id="r1")
        result_a = self.publisher.publish(target_a)
        result_b = self.publisher.publish(target_b)
        self.assertTrue(result_a.confirmed)
        self.assertTrue(result_b.confirmed)
        self.assertEqual({result_a, result_b}, {TerminalConfirmation.CONFIRMED_NEW, TerminalConfirmation.CONFIRMED_EXISTING})

    def test_stale_target_cannot_resurrect_a_deleted_run(self):
        # "a completed thread deletion wins, so a stale target cannot
        # recreate an orphan event" -- the lifecycle guard is what enforces
        # this; a target issued before deletion must still be rejected.
        target = self.publisher.authorize_takeover(claimed=True, thread_id="t1", run_id="r1")
        deleted = {"flag": False}
        self.store.delete_run("t1", "r1")
        deleted["flag"] = True
        result = self.publisher.publish(target, lifecycle_guard=lambda: not deleted["flag"])
        self.assertEqual(result, TerminalConfirmation.CONFLICT)
        event, created = self.store.put_if_absent(thread_id="t1", run_id="r1", status="success", recovered=False)
        self.assertTrue(created, "deletion must not have left an orphaned recovery row behind")


class TestConcurrency(unittest.TestCase):
    """The real claim this project is checking: SQLite's UNIQUE constraint
    (not a Python-level lock) is what makes put_if_absent atomic across
    threads. Prove it by actually racing threads against it, not by
    reasoning about the code."""

    def setUp(self):
        self.store, self.path = fresh_store()

    def tearDown(self):
        self.store.close()
        os.unlink(self.path)
        for suffix in ("-wal", "-shm"):
            p = self.path + suffix
            if os.path.exists(p):
                os.unlink(p)

    def test_concurrent_confirmations_produce_exactly_one_created_row(self):
        results = []
        results_lock = threading.Lock()
        barrier = threading.Barrier(20)

        def worker():
            barrier.wait()
            r = confirm_terminal_event(
                self.store, thread_id="t1", run_id="race", status="success", authorized=lambda: True
            )
            with results_lock:
                results.append(r)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 20)
        self.assertTrue(all(r.confirmed for r in results))
        new_count = sum(1 for r in results if r == TerminalConfirmation.CONFIRMED_NEW)
        existing_count = sum(1 for r in results if r == TerminalConfirmation.CONFIRMED_EXISTING)
        self.assertEqual(new_count, 1, "exactly one of the 20 racing confirmations must be the real insert")
        self.assertEqual(existing_count, 19)

    def test_concurrent_confirmations_with_different_statuses_yield_one_winner_and_conflicts(self):
        # A harsher race: half the threads think the outcome is "success",
        # half think it's "error" (a real bug scenario -- two code paths
        # disagreeing about the final status). Exactly one status must win,
        # and every loser with a *different* status must see CONFLICT, not
        # a silently-swallowed success.
        results = []
        results_lock = threading.Lock()
        barrier = threading.Barrier(20)

        def worker(status):
            barrier.wait()
            r = confirm_terminal_event(
                self.store, thread_id="t1", run_id="disputed", status=status, authorized=lambda: True
            )
            with results_lock:
                results.append((status, r))

        threads = [
            threading.Thread(target=worker, args=("success" if i % 2 == 0 else "error",))
            for i in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final_event, _ = self.store.put_if_absent(thread_id="t1", run_id="disputed", status="success", recovered=False)
        winning_status = final_event.status
        for status, result in results:
            if status == winning_status:
                self.assertTrue(result.confirmed, f"matching status {status} should confirm, got {result}")
            else:
                self.assertEqual(result, TerminalConfirmation.CONFLICT, f"mismatched status {status} must conflict")


class TestCrossProcessConcurrency(unittest.TestCase):
    """The threaded TestConcurrency class above proves this module's
    put_if_absent() is safe under concurrent callers *within one process* --
    but its own self._write_lock is what's actually enforcing that there,
    which leaves the sqlite3.IntegrityError fallback branch unexercised.
    This class proves the real claim made in the module docstring: the
    atomicity holds at the database level, independent of any single
    process's lock, by racing separate OS processes that each construct
    their own TerminalLedger (and therefore their own, mutually-unaware
    lock) against the same database file."""

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        # Pre-create the schema once before forking, so every child race
        # is purely about the terminal row, not table creation.
        TerminalLedger(self.path).close()

    def tearDown(self):
        os.unlink(self.path)
        for suffix in ("-wal", "-shm"):
            p = self.path + suffix
            if os.path.exists(p):
                os.unlink(p)

    def test_separate_processes_racing_converge_on_one_row(self):
        n = 6
        ctx = multiprocessing.get_context("fork")
        barrier = ctx.Barrier(n)
        out_queue = ctx.Queue()
        procs = [
            ctx.Process(target=_cross_process_confirm_worker, args=(self.path, "success", barrier, out_queue))
            for _ in range(n)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=30)
        self.assertTrue(all(p.exitcode == 0 for p in procs), "every worker process must exit cleanly")

        results = [out_queue.get(timeout=5) for _ in range(n)]
        new_count = sum(1 for r in results if r == TerminalConfirmation.CONFIRMED_NEW.value)
        existing_count = sum(1 for r in results if r == TerminalConfirmation.CONFIRMED_EXISTING.value)
        self.assertEqual(new_count, 1, "exactly one of the racing processes must be the real insert")
        self.assertEqual(existing_count, n - 1)

        # Independently re-open the database (a third connection, unrelated
        # to any racer) and confirm exactly one row exists for this run.
        verify_store = TerminalLedger(self.path)
        cur = verify_store._conn.execute(
            "SELECT COUNT(*) FROM terminal_events WHERE thread_id = ? AND run_id = ?",
            ("t1", "cross-process-race"),
        )
        self.assertEqual(cur.fetchone()[0], 1)
        verify_store.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
