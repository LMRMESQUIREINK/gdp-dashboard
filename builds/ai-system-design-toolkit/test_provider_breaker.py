import threading
import time
import unittest

from provider_breaker import (
    BreakerOpenError,
    CircuitState,
    ProviderBreaker,
    TimeBudgetExceededError,
)


class TransientError(Exception):
    """Simulates a provider error worth retrying (timeout, 5xx, etc.)."""


class PermanentError(Exception):
    """Simulates a definitive, non-retryable error (bad request, 404)."""


def is_transient(exc: Exception) -> bool:
    return isinstance(exc, TransientError)


class FakeClock:
    """Deterministic, manually-advanced clock for testing cooldowns and
    time budgets without real sleeping."""

    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def no_sleep_tracker():
    """A fake sleep() that records requested durations instead of
    actually sleeping, and returns the list it records into."""
    calls = []

    def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    return fake_sleep, calls


class TestClosedStateHappyPath(unittest.TestCase):
    def test_successful_call_passes_through_with_no_retry(self):
        sleep, sleeps = no_sleep_tracker()
        breaker = ProviderBreaker(retryable=is_transient, sleep=sleep)
        calls = []

        def fn(x):
            calls.append(x)
            return x * 2

        result = breaker.call(fn, 21)
        self.assertEqual(result, 42)
        self.assertEqual(calls, [21])
        self.assertEqual(sleeps, [])
        self.assertEqual(breaker.state, CircuitState.CLOSED)


class TestRetryBehavior(unittest.TestCase):
    def test_transient_error_retried_until_success(self):
        sleep, sleeps = no_sleep_tracker()
        breaker = ProviderBreaker(
            max_retries=5, retryable=is_transient, sleep=sleep, rand=lambda: 0.0
        )
        attempts = {"n": 0}

        def flaky():
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise TransientError("temporary")
            return "ok"

        result = breaker.call(flaky)
        self.assertEqual(result, "ok")
        self.assertEqual(attempts["n"], 3)
        # Two failed attempts before success -> two backoff sleeps, and
        # with rand() pinned to 0.0 the equal-jitter formula collapses to
        # exactly half the exponential term: base=0.5 -> attempt1 delay
        # = (0.5*2^0)/2 = 0.25, attempt2 delay = (0.5*2^1)/2 = 0.5.
        self.assertEqual(len(sleeps), 2)
        self.assertAlmostEqual(sleeps[0], 0.25, places=6)
        self.assertAlmostEqual(sleeps[1], 0.5, places=6)

    def test_permanent_error_fails_fast_with_no_retry(self):
        sleep, sleeps = no_sleep_tracker()
        breaker = ProviderBreaker(max_retries=5, retryable=is_transient, sleep=sleep)
        calls = {"n": 0}

        def always_404():
            calls["n"] += 1
            raise PermanentError("not found")

        with self.assertRaises(PermanentError):
            breaker.call(always_404)
        self.assertEqual(calls["n"], 1, "a non-retryable error must not be retried")
        self.assertEqual(sleeps, [])

    def test_retries_exhausted_raises_last_exception(self):
        sleep, _ = no_sleep_tracker()
        breaker = ProviderBreaker(max_retries=2, retryable=is_transient, sleep=sleep)
        calls = {"n": 0}

        def always_flaky():
            calls["n"] += 1
            raise TransientError(f"fail {calls['n']}")

        with self.assertRaises(TransientError):
            breaker.call(always_flaky)
        # 1 initial attempt + 2 retries = 3 calls total.
        self.assertEqual(calls["n"], 3)

    def test_fallback_used_when_retries_exhausted(self):
        sleep, _ = no_sleep_tracker()
        breaker = ProviderBreaker(max_retries=1, retryable=is_transient, sleep=sleep)

        def always_flaky():
            raise TransientError("down")

        result = breaker.call(always_flaky, fallback=lambda: "fallback-value")
        self.assertEqual(result, "fallback-value")


class TestTimeBudget(unittest.TestCase):
    def test_budget_exhausted_stops_retrying_before_max_retries(self):
        clock = FakeClock()
        sleep_calls = []

        def fake_sleep(seconds):
            sleep_calls.append(seconds)
            clock.advance(seconds)

        breaker = ProviderBreaker(
            max_retries=10, retryable=is_transient, time_budget_seconds=1.0,
            clock=clock, sleep=fake_sleep, rand=lambda: 0.0,
        )
        calls = {"n": 0}

        def always_flaky():
            calls["n"] += 1
            clock.advance(0.6)  # simulate a slow failing call
            raise TransientError("down")

        with self.assertRaises(TimeBudgetExceededError):
            breaker.call(always_flaky)
        # Budget (1.0s) should be exhausted well before 10 retries given
        # each attempt alone burns 0.6s.
        self.assertLess(calls["n"], 10)
        self.assertGreaterEqual(calls["n"], 1)

    def test_fallback_used_on_budget_exhaustion(self):
        clock = FakeClock()

        def fake_sleep(seconds):
            clock.advance(seconds)

        breaker = ProviderBreaker(
            max_retries=10, retryable=is_transient, time_budget_seconds=0.5,
            clock=clock, sleep=fake_sleep, rand=lambda: 0.0,
        )

        def always_flaky():
            clock.advance(0.6)
            raise TransientError("down")

        result = breaker.call(always_flaky, fallback=lambda: "safe-default")
        self.assertEqual(result, "safe-default")


class TestCircuitBreakerStateMachine(unittest.TestCase):
    def test_breaker_opens_after_consecutive_failures_and_short_circuits(self):
        clock = FakeClock()
        breaker = ProviderBreaker(
            failure_threshold=3, cooldown_seconds=10, max_retries=0,
            retryable=lambda e: False, clock=clock, sleep=lambda s: None,
        )
        calls = {"n": 0}

        def always_fails():
            calls["n"] += 1
            raise PermanentError("down")

        for _ in range(3):
            with self.assertRaises(PermanentError):
                breaker.call(always_fails)
        self.assertEqual(breaker.state, CircuitState.OPEN)
        self.assertEqual(calls["n"], 3)

        # A 4th call must be short-circuited -- fn must NOT be invoked.
        with self.assertRaises(BreakerOpenError):
            breaker.call(always_fails)
        self.assertEqual(calls["n"], 3, "breaker must not call fn while OPEN")

    def test_fallback_used_while_open(self):
        clock = FakeClock()
        breaker = ProviderBreaker(
            failure_threshold=1, cooldown_seconds=10, max_retries=0,
            retryable=lambda e: False, clock=clock, sleep=lambda s: None,
        )

        def always_fails():
            raise PermanentError("down")

        with self.assertRaises(PermanentError):
            breaker.call(always_fails)
        self.assertEqual(breaker.state, CircuitState.OPEN)

        result = breaker.call(always_fails, fallback=lambda: "cached-answer")
        self.assertEqual(result, "cached-answer")

    def test_half_open_probe_success_closes_breaker(self):
        clock = FakeClock()
        breaker = ProviderBreaker(
            failure_threshold=1, cooldown_seconds=10, max_retries=0,
            retryable=lambda e: False, clock=clock, sleep=lambda s: None,
        )

        def fails_once_then_succeeds():
            raise PermanentError("down")

        with self.assertRaises(PermanentError):
            breaker.call(fails_once_then_succeeds)
        self.assertEqual(breaker.state, CircuitState.OPEN)

        # Before cooldown elapses, still short-circuited.
        with self.assertRaises(BreakerOpenError):
            breaker.call(fails_once_then_succeeds)

        clock.advance(10.001)
        result = breaker.call(lambda: "recovered")
        self.assertEqual(result, "recovered")
        self.assertEqual(breaker.state, CircuitState.CLOSED)

        # Breaker is healthy again -- ordinary calls proceed normally.
        result2 = breaker.call(lambda: "still fine")
        self.assertEqual(result2, "still fine")

    def test_half_open_probe_failure_reopens_breaker_and_resets_cooldown(self):
        clock = FakeClock()
        breaker = ProviderBreaker(
            failure_threshold=1, cooldown_seconds=10, max_retries=0,
            retryable=lambda e: False, clock=clock, sleep=lambda s: None,
        )

        def always_fails():
            raise PermanentError("still down")

        with self.assertRaises(PermanentError):
            breaker.call(always_fails)
        self.assertEqual(breaker.state, CircuitState.OPEN)

        clock.advance(10.001)
        with self.assertRaises(PermanentError):
            breaker.call(always_fails)  # the half-open probe, and it fails
        self.assertEqual(breaker.state, CircuitState.OPEN)

        # Cooldown must have restarted from the probe's failure, not from
        # the original open time -- advancing only 1s (not enough from
        # the new opened_at) must still short-circuit.
        clock.advance(1)
        with self.assertRaises(BreakerOpenError):
            breaker.call(always_fails)


class TestConcurrentHalfOpenProbe(unittest.TestCase):
    """The real claim under test: when cooldown elapses, exactly ONE
    caller gets to be the probe, even if several threads race to be
    first -- proven with real OS threads, not reasoned about."""

    def test_only_one_thread_becomes_the_probe(self):
        clock = FakeClock()
        breaker = ProviderBreaker(
            failure_threshold=1, cooldown_seconds=10, max_retries=0,
            retryable=lambda e: False, clock=clock, sleep=lambda s: None,
        )

        def always_fails():
            raise PermanentError("down")

        with self.assertRaises(PermanentError):
            breaker.call(always_fails)
        self.assertEqual(breaker.state, CircuitState.OPEN)
        clock.advance(10.001)

        probe_started = threading.Event()
        release_probe = threading.Event()
        probe_call_count = {"n": 0}
        probe_lock = threading.Lock()

        def slow_probe_fn():
            with probe_lock:
                probe_call_count["n"] += 1
            probe_started.set()
            release_probe.wait(timeout=5)
            return "recovered"

        results = []
        results_lock = threading.Lock()
        start_barrier = threading.Barrier(8)

        def worker():
            start_barrier.wait()
            try:
                r = breaker.call(slow_probe_fn)
                outcome = ("ok", r)
            except BreakerOpenError:
                outcome = ("rejected", None)
            with results_lock:
                results.append(outcome)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        # Give the probe thread a moment to actually enter slow_probe_fn
        # before releasing it, so the other 7 threads are guaranteed to
        # race against a still-in-flight probe rather than a finished one.
        probe_started.wait(timeout=5)
        time.sleep(0.05)
        release_probe.set()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(probe_call_count["n"], 1, "exactly one thread must have become the probe")
        ok_results = [r for r in results if r[0] == "ok"]
        rejected_results = [r for r in results if r[0] == "rejected"]
        self.assertEqual(len(ok_results), 1)
        self.assertEqual(len(rejected_results), 7)
        self.assertEqual(ok_results[0][1], "recovered")
        self.assertEqual(breaker.state, CircuitState.CLOSED)


class TestValidation(unittest.TestCase):
    def test_invalid_failure_threshold_rejected(self):
        with self.assertRaises(ValueError):
            ProviderBreaker(failure_threshold=0)

    def test_invalid_cooldown_rejected(self):
        with self.assertRaises(ValueError):
            ProviderBreaker(cooldown_seconds=0)

    def test_negative_max_retries_rejected(self):
        with self.assertRaises(ValueError):
            ProviderBreaker(max_retries=-1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
