import unittest
import tempfile
from pathlib import Path

from ledger import FingerprintedLedger, LedgerMiss


class TestFingerprint(unittest.TestCase):
    def test_identical_requests_get_the_same_fingerprint(self):
        a = FingerprintedLedger.fingerprint("m", [{"role": "user", "content": "hi"}], {"temp": 0})
        b = FingerprintedLedger.fingerprint("m", [{"role": "user", "content": "hi"}], {"temp": 0})
        self.assertEqual(a, b)

    def test_different_sample_index_gives_a_different_fingerprint(self):
        a = FingerprintedLedger.fingerprint("m", [{"role": "user", "content": "same question"}], {}, sample_index=0)
        b = FingerprintedLedger.fingerprint("m", [{"role": "user", "content": "same question"}], {}, sample_index=1)
        self.assertNotEqual(a, b)

    def test_different_content_gives_a_different_fingerprint(self):
        a = FingerprintedLedger.fingerprint("m", [{"role": "user", "content": "a"}], {})
        b = FingerprintedLedger.fingerprint("m", [{"role": "user", "content": "b"}], {})
        self.assertNotEqual(a, b)


class TestCollectMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ledger = FingerprintedLedger(Path(self.tmp) / "ledger.sqlite", mode="collect")

    def test_a_fresh_call_hits_live_fn_and_is_cached(self):
        calls = []

        def live():
            calls.append(1)
            return {"text": "real answer"}

        answer, cached = self.ledger.call("m", [{"role": "user", "content": "q"}], {}, live_fn=live)
        self.assertEqual(answer, {"text": "real answer"})
        self.assertFalse(cached)
        self.assertEqual(len(calls), 1)

    def test_a_repeat_call_is_served_from_cache_without_touching_live_fn(self):
        calls = []

        def live():
            calls.append(1)
            return {"text": "real answer"}

        self.ledger.call("m", [{"role": "user", "content": "q"}], {}, live_fn=live)
        answer, cached = self.ledger.call("m", [{"role": "user", "content": "q"}], {}, live_fn=live)
        self.assertEqual(answer, {"text": "real answer"})
        self.assertTrue(cached)
        self.assertEqual(len(calls), 1, "live_fn must not be called a second time")

    def test_collect_mode_without_live_fn_raises(self):
        with self.assertRaises(RuntimeError):
            self.ledger.call("m", [{"role": "user", "content": "q"}], {})


class TestReplayMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = Path(self.tmp) / "ledger.sqlite"
        collector = FingerprintedLedger(self.db_path, mode="collect")
        collector.call("m", [{"role": "user", "content": "known"}], {}, live_fn=lambda: {"text": "cached answer"})
        self.replay = FingerprintedLedger(self.db_path, mode="replay")

    def test_a_cached_fingerprint_replays_without_a_live_call(self):
        answer, cached = self.replay.call("m", [{"role": "user", "content": "known"}], {})
        self.assertEqual(answer, {"text": "cached answer"})
        self.assertTrue(cached)

    def test_a_genuine_miss_raises_ledgermiss_not_a_silent_live_call(self):
        calls = []
        with self.assertRaises(LedgerMiss):
            self.replay.call(
                "m",
                [{"role": "user", "content": "never asked before"}],
                {},
                live_fn=lambda: calls.append(1),
            )
        self.assertEqual(calls, [], "replay mode must never fall back to a live call")


class TestSmokeMode(unittest.TestCase):
    def test_smoke_mode_never_touches_the_ledger_file(self):
        tmp = tempfile.mkdtemp()
        db_path = Path(tmp) / "ledger.sqlite"
        ledger = FingerprintedLedger(db_path, mode="smoke")
        answer, cached = ledger.call("m", [{"role": "user", "content": "q"}], {}, smoke_fn=lambda: {"text": "scripted"})
        self.assertEqual(answer, {"text": "scripted"})
        self.assertFalse(cached)
        self.assertFalse(db_path.exists(), "smoke mode must not create a ledger file")

    def test_smoke_mode_without_smoke_fn_raises(self):
        ledger = FingerprintedLedger(Path(tempfile.mkdtemp()) / "ledger.sqlite", mode="smoke")
        with self.assertRaises(RuntimeError):
            ledger.call("m", [{"role": "user", "content": "q"}], {})


class TestCrossProcessPersistence(unittest.TestCase):
    def test_a_fresh_ledger_instance_against_the_same_file_sees_prior_writes(self):
        tmp = tempfile.mkdtemp()
        db_path = Path(tmp) / "ledger.sqlite"
        first = FingerprintedLedger(db_path, mode="collect")
        first.call("m", [{"role": "user", "content": "persisted"}], {}, live_fn=lambda: {"text": "v1"})

        second = FingerprintedLedger(db_path, mode="collect")
        answer, cached = second.call("m", [{"role": "user", "content": "persisted"}], {}, live_fn=lambda: {"text": "should not run"})
        self.assertEqual(answer, {"text": "v1"})
        self.assertTrue(cached)
        self.assertEqual(second.count(), 1)


if __name__ == "__main__":
    unittest.main()
