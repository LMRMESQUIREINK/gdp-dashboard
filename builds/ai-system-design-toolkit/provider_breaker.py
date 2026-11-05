"""Real implementation of the circuit-breaker + bounded-retry + backoff
algorithm from "AI System Design: A Practical Guide to Production AI"
(Piyush Kashyap) Section 12 -- the exact 7-step failure-handling strategy
that article names for calls to an external AI model provider:

    1. Apply a bounded timeout to the model request.
    2. Retry only errors that are likely to be temporary.
    3. Use exponential backoff with jitter to reduce synchronized retries.
    4. Stop retrying when the request's time budget is exhausted.
    5. Open a circuit breaker if the provider continues failing.
    6. Route eligible requests to a tested alternative or return a
       controlled fallback.
    7. Record the failure and alert the responsible team when appropriate
       (left to the caller -- this module raises typed exceptions and
       exposes a `state` property for the caller's own observability to
       hook into, rather than embedding logging/alerting policy itself).

This project's own /builds/prop-firm-mcp-server/ explicitly cut a circuit
breaker, stated plainly in its README: "no upstream network call exists
to protect against." This module is the first real implementation of one
in this project, built against a genuine simulated flaky dependency
rather than a toy example that always happens to work.
"""

from __future__ import annotations

import random
import threading
import time
from enum import Enum
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class BreakerOpenError(RuntimeError):
    """Raised when the breaker is OPEN and no fallback was supplied."""


class TimeBudgetExceededError(RuntimeError):
    """Raised when retrying further would exceed the call's time budget."""


class ProviderBreaker:
    """Wraps calls to an unreliable external dependency (an AI model
    provider, in the source article's framing, but this has no AI-specific
    logic at all -- any flaky call fits).

    Thread-safe: state transitions are guarded by a lock, and the
    half-open state allows exactly one trial call through at a time --
    other callers that arrive while a probe is in flight are treated as
    still OPEN, matching the standard closed/open/half-open pattern the
    source article describes in plain language without naming it.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.5,
        max_backoff_seconds: float = 10.0,
        time_budget_seconds: float | None = None,
        retryable: Callable[[Exception], bool] = lambda e: True,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if cooldown_seconds <= 0:
            raise ValueError("cooldown_seconds must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._max_retries = max_retries
        self._base_backoff = base_backoff_seconds
        self._max_backoff = max_backoff_seconds
        self._time_budget = time_budget_seconds
        self._retryable = retryable
        self._clock = clock
        self._sleep = sleep
        self._rand = rand

        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._half_open_probe_in_flight = False

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    def _backoff_delay(self, attempt: int) -> float:
        # Exponential backoff with equal jitter: half the exponential
        # delay is fixed, half is random, which avoids both the
        # synchronized-retry-storm risk of no jitter and the
        # occasionally-too-short delay of full jitter.
        exponential = min(self._base_backoff * (2 ** (attempt - 1)), self._max_backoff)
        return (exponential / 2) + (exponential / 2) * self._rand()

    def _enter_call(self):
        """Decide, under the lock, whether this call may proceed, and if
        so, whether it is an ordinary call or the single half-open
        probe. Returns True if the caller should attempt fn(), False if
        the caller must treat this as a short-circuited OPEN rejection."""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            if self._state == CircuitState.OPEN:
                assert self._opened_at is not None
                if self._clock() - self._opened_at < self._cooldown_seconds:
                    return False
                if self._half_open_probe_in_flight:
                    # Cooldown elapsed, but another caller already
                    # claimed the one allowed probe -- still short-circuit.
                    return False
                self._state = CircuitState.HALF_OPEN
                self._half_open_probe_in_flight = True
                return True
            if self._state == CircuitState.HALF_OPEN:
                # A probe is already in flight; everyone else is rejected
                # until it resolves.
                return False
        raise AssertionError("unreachable circuit state")

    def _record_success(self):
        with self._lock:
            was_probe = self._state == CircuitState.HALF_OPEN
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            if was_probe:
                self._half_open_probe_in_flight = False

    def _record_failure(self):
        with self._lock:
            was_probe = self._state == CircuitState.HALF_OPEN
            if was_probe:
                self._half_open_probe_in_flight = False
            self._consecutive_failures += 1
            if was_probe or self._consecutive_failures >= self._failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()

    def call(self, fn: Callable[..., T], *args, fallback: Callable[..., T] | None = None, **kwargs) -> T:
        if not self._enter_call():
            if fallback is not None:
                return fallback(*args, **kwargs)
            raise BreakerOpenError("circuit is open; provider call was not attempted")

        start = self._clock()
        attempt = 0
        last_exc: Exception | None = None
        while True:
            if self._time_budget is not None and attempt > 0 and (self._clock() - start) >= self._time_budget:
                self._record_failure()
                if fallback is not None:
                    return fallback(*args, **kwargs)
                raise TimeBudgetExceededError(
                    f"time budget of {self._time_budget}s exhausted after {attempt} attempt(s)"
                ) from last_exc
            try:
                result = fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if not self._retryable(e):
                    self._record_failure()
                    raise
                attempt += 1
                if attempt > self._max_retries:
                    self._record_failure()
                    if fallback is not None:
                        return fallback(*args, **kwargs)
                    raise
                self._sleep(self._backoff_delay(attempt))
                continue
            else:
                self._record_success()
                return result
