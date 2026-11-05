# AI System Design Toolkit

Two real, dependency-free Python modules built from a pasted article,
"AI System Design: A Practical Guide to Production AI" (Piyush Kashyap,
Medium) — full analysis in `/notes/ai-system-design-guide-analysis.md`.
Unlike every other deep-dive in this project, this source had no code and
no checkable external/dated claim — just prose and worked arithmetic — so
the only things to verify were its own numbers (all 12 recomputed by
hand, all correct, with one small rounding-propagation finding) and
whether anything in it was both genuinely new to this project and fully
mechanical enough to build and test for real.

Two things qualified. Everything else in the article (RAG, HITL
approval, model routing, caching, observability, deployment) already has
a real, tested implementation elsewhere in this project — see the
analysis note for the full cross-reference.

## `capacity_planner.py` — Section 3's math, made real

The article's exact formulas for sizing an AI application's backend from
workload assumptions: daily request volume, average and peak requests
per second, Little's Law concurrency (`L = λW`), daily/monthly token
consumption, and a monthly cost estimate from per-million-token pricing.

This project already has sizing tools (`prop_firm_sizing.py` and
friends) — but those size *trading risk*, not an AI application's own
infrastructure. Nothing before this build answered "how many requests
per second will this chatbot actually need to handle, and what will it
cost per month" for a project in this repo.

```bash
python3 capacity_planner.py \
  --users 5000 --requests-per-user-per-day 4 \
  --avg-input-tokens 1200 --avg-output-tokens 300 \
  --price-per-million-input 0.50 --price-per-million-output 2.00 \
  --concurrency-avg-seconds 2
```

Reproduces the article's own Northstar example exactly — 20,000 daily
requests, 24M/6M daily input/output tokens, $528/month — **except** for
one real finding from checking the arithmetic rather than trusting it:
the article computes peak RPS as `0.69 × 8 ≈ 5.52`, using its own
already-*rounded* 0.69. The exact fraction is `20,000 ÷ 28,800 =
0.69444...`, and `0.69444... × 8 = 5.5556`. Both round to "approximately
5.5" at the article's own stated precision, so its practical conclusion
holds — but 5.52 is a rounding-propagation artifact of computing from a
rounded intermediate rather than the exact input, not what the article's
own stated assumptions actually produce. This module carries full
precision throughout and gets 5.5556; `test_capacity_planner.py`'s
`test_peak_rps_uses_exact_fraction_not_articles_rounded_intermediate`
locks both the correct figure and the discrepancy in as a permanent,
named regression test rather than a one-off note.

## `provider_breaker.py` — Section 12's failure-handling algorithm, built for real

The article's 7-step recipe for calling an unreliable external AI
provider: bounded timeout, retry only transient errors, exponential
backoff with jitter, stop at a time budget, open a circuit breaker after
repeated failures, route to a fallback while open, and (left to the
caller, since it's a policy choice, not a mechanism) log/alert on
failure.

`/builds/prop-firm-mcp-server/README.md` explicitly cut a circuit
breaker in an earlier round, for the right reason at the time: "no
upstream network call exists to protect against" — a deterministic
Monte Carlo calculator has nothing flaky to guard against. This article
gives the exact algorithm this project had deferred, and this build
finally implements it, proven against a genuinely simulated flaky
dependency rather than a toy that always happens to succeed.

```python
from provider_breaker import ProviderBreaker

def is_retryable(exc):
    return isinstance(exc, (TimeoutError, ConnectionError))

breaker = ProviderBreaker(
    failure_threshold=5, cooldown_seconds=30,
    max_retries=3, time_budget_seconds=10,
    retryable=is_retryable,
)

answer = breaker.call(call_the_model, prompt, fallback=lambda prompt: cached_or_safe_default(prompt))
```

Implements the standard closed → open → half-open state machine (named
only in plain language by the source article, not by that terminology)
with real thread safety: while the breaker is `OPEN` and its cooldown has
elapsed, exactly one caller becomes the half-open probe; every other
concurrent caller is still short-circuited until that probe resolves.

### Proven

```bash
python3 -m unittest test_capacity_planner test_provider_breaker -v
```

**29/29 tests pass**, including:

- `capacity_planner`: all 12 of the article's Northstar numbers
  reproduced exactly (14 tests — the 12 figures plus the rounding
  finding plus workload validation plus three real subprocess CLI
  calls, including a clean `argparse` error on a missing required flag).
- `provider_breaker` (15 tests): a transient error retried to success
  with the exact equal-jitter backoff values checked by hand (deterministic
  `rand`/`sleep` injection, no real sleeping); a permanent error failing
  fast with zero retries; retries correctly exhausting to the original
  exception; a fallback used both on retry exhaustion and on time-budget
  exhaustion; the breaker opening after `failure_threshold` consecutive
  failures and then genuinely **not calling the wrapped function at all**
  on the next call (checked with a call counter, not just an exception
  type); a successful half-open probe closing the breaker and resetting
  failures; a failed half-open probe reopening the breaker **with its
  cooldown restarted from the probe's own failure time**, not the
  original open time; and — the test that actually proves the
  thread-safety claim rather than asserting it — **8 real OS threads**
  racing the instant cooldown elapses, with the wrapped function made
  deliberately slow (held open with a `threading.Event`) to widen the
  race window: exactly 1 thread becomes the probe and calls the
  underlying function, the other 7 are rejected while it's in flight,
  and the breaker ends up `CLOSED` with the probe's own result returned
  to exactly one caller.

## What's not built here, and why

Everything else the article covers already has a real build in this
project, so building it again from a second source would add nothing:
HITL approval and payload-bound authorization
(`/builds/policy-control-plane/`, `/builds/agent-checkpoint-layer/`),
idempotent singleton confirmation for disputed outcomes
(`/builds/run-terminal-ledger/`), confidence-gated routing — including a
live demonstration of the exact self-confidence failure mode this
article warns about in Section 9 but doesn't fully resolve for its own
cascade-routing proposal (`/builds/jev-pattern-router/`), rate limiting
(`/builds/prop-firm-mcp-server/ratelimit.py`), and tool-call validation
with a least-privilege registry (`/builds/interface-lift-toolkit/`). See
`/notes/ai-system-design-guide-analysis.md` for the full cross-reference
and the Section 9 internal-tension finding.

Semantic-cache eligibility (the article's six dimensions — authorization
scope, freshness, context, model/prompt version, TTL, risk level) was
considered and deliberately not built this round: it's a real, useful
idea, but it's a decision table, not an algorithm with the same kind of
concurrency/state-machine subtlety that made the circuit breaker worth
building for real — a direct port would mostly just be an `if` chain
with no interesting behavior to prove wrong by testing.
