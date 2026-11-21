# Deep analysis: "AI System Design: A Practical Guide to Production AI"

Source: a full article pasted directly into the conversation (Piyush
Kashyap, Medium), no accompanying instruction text — same bare-upload
pattern as every other source in this project, this time pure prose with
no code and no repo to clone. A 22-section practical guide to taking an
LLM prototype to production, built around one running fictional example
("Northstar," an AI IT helpdesk for 5,000 employees).

## What's different about this source

Every prior deep-dive in this project had either real code to run (Fareed
Khan's articles, REA, the MCP-server article) or specific, dated,
checkable external claims (incident reports, named benchmarks, company
statistics). This article has neither. It makes zero claims about the
real world — no company names, no incident reports, no cited benchmark,
no dated event. Its only genuinely checkable content is its own worked
arithmetic (the Northstar capacity-planning numbers) and the technical
accuracy of the mechanisms it names. That reshapes what "measure before
meaning" means here: there was nothing to run against a repo and nothing
to verify against a web search, so the check is a hand recompute of every
number plus a reading of the document against itself for internal
consistency.

## Measured, not assumed: recomputing every worked number

Independently recomputed in a standalone Python script, not read and
nodded along to:

| Quantity | Article's figure | Recomputed | Match |
| --- | --- | --- | --- |
| Daily requests (5,000 × 4) | 20,000 | 20,000 | exact |
| Avg RPS (20,000 ÷ 28,800s) | ≈0.69 | 0.69444... | matches at stated precision |
| Daily input tokens (20,000 × 1,200) | 24,000,000 | 24,000,000 | exact |
| Daily output tokens (20,000 × 300) | 6,000,000 | 6,000,000 | exact |
| Daily total tokens | 30,000,000 | 30,000,000 | exact |
| Monthly input tokens (×22 days) | 528,000,000 | 528,000,000 | exact |
| Monthly output tokens (×22 days) | 132,000,000 | 132,000,000 | exact |
| Monthly total tokens | 660,000,000 | 660,000,000 | exact |
| Monthly input cost ($0.50/M) | $264 | $264.00 | exact |
| Monthly output cost ($2.00/M) | $264 | $264.00 | exact |
| Total monthly cost | $528 | $528.00 | exact |
| Little's Law (λ=6, W=2) | L=12 | L=12 | exact |

Every figure checks out exactly — this is the cleanest arithmetic record
of any source analyzed in this project to date, ahead of the
multi-tenant LLM series' Part 3 capacity math (which also checked out,
but wasn't 12-for-12 clean at every step).

**One real, small finding, found only by recomputing rather than reading**:
the article's own peak-RPS figure is internally inconsistent at the third
significant digit because of where it rounds. It computes "Peak requests
per second = 0.69 × 8 ≈ 5.52" using the already-rounded 0.69 — but the
exact fraction is 20,000 ÷ 28,800 = 0.69444..., and 0.69444... × 8 =
5.5556, which rounds to 5.56, not 5.52. The article's very next sentence
calls the result "approximately 5.5 requests per second," which is
consistent with *either* 5.52 or 5.56 at that coarser precision, so the
practical conclusion is unaffected — but the intermediate "5.52" is a
rounding-propagation artifact (computing from a rounded input instead of
the exact fraction), not the number you get from the article's own stated
inputs. A ~0.7% gap, immaterial for sizing a system, but worth stating
precisely rather than waved through, same discipline as every other
small-precision finding in this project (the M/M/c label precision in the
multi-tenant series, the "9 vs 10 prompts" count in the WordPress prompt
pack).

## What's credited

- The layered architecture (client → entry → application/orchestrator →
  AI processing → data → operations) is a clean, defensible separation of
  concerns, and the article is explicit that "not every request needs
  every component" — a greeting doesn't need retrieval, a sensitive
  account action doesn't need a generated answer at all. This matches
  this project's own established discipline of narrowing scope to what a
  request actually needs rather than routing everything through the same
  expensive path.
- "The model requests an action; the application executes it" (Section
  10) is stated as a hard rule, with the corollary that the model's own
  claim that an action "succeeded" must never be trusted without the
  service's actual confirmation. This is independently the same principle
  this project's own `/builds/policy-control-plane/` and
  `/builds/defender-loop-verifier/` were built around — a deterministic,
  external check decides truth, never a model's self-report — arrived at
  here by a different author with no shared source, the same kind of
  convergent-finding this project has flagged before when two unrelated
  sources land on the same real principle independently.
- The approval-mechanism design note — "verify who approved it, what they
  approved, and whether the approval is still valid for the operation
  being executed... approval to unlock one employee's account should not
  automatically authorize changes to another account" — is exactly the
  payload-binding property `/builds/policy-control-plane/` was built to
  close (approving one request's parameters and having a *different*
  request execute under that same approval). The article states the
  requirement in prose; this project already has a working, tested
  implementation of it.
- The semantic-caching section is unusually careful for an introductory
  guide: it explicitly separates "two queries are worded similarly" from
  "two queries may share an answer," and lists six real dimensions
  (authorization scope, freshness, context, model/prompt version, TTL,
  risk level) that must all be checked before reusing a cached AI answer.
  Most production write-ups treat semantic caching as a pure
  latency/cost win; this one names the failure mode (a cache hit serving
  one employee's PTO balance to another) before the benefit.

## What doesn't fully hold up: an internal tension, not an external error

Section 9 contains two ideas back-to-back that are in real tension with
each other, and the article never reconciles them:

1. It proposes a **staged cascade** for model routing: "Try a low-cost
   processing path. Evaluate whether the result meets a defined quality
   threshold. Escalate difficult or uncertain cases to a more capable
   model" — and flags correctly that "this pattern only works when the
   application can recognize when the cheaper path is insufficient."
2. Two paragraphs later, in the very next subsection: **"Don't confuse
   confidence with correctness. A model can sound confident while being
   wrong. Its self-reported confidence score is not, by itself, a
   reliable measure of answer quality."**

The article never says what mechanism performs step 1's "evaluate
whether the result meets a defined quality threshold" without falling
into step 2's warned-against trap. If the evaluator is the cheap model's
own confidence score, the cascade inherits exactly the unreliability the
article just warned about two paragraphs later. If the evaluator is a
second, independent model call, the cascade's whole cost-saving premise
(skip the expensive path when possible) is undermined, since now every
request pays for at least two model-shaped calls regardless. The article
gestures at "observable signals, such as whether retrieval found
relevant sources, whether required fields were extracted successfully,
whether a response passed validation" as alternatives — which are real
and don't have this problem — but never connects that list back to the
cascade section a few paragraphs earlier as the actual answer to its own
open question. This project's own `/builds/jev-pattern-router/` hit a
concrete version of exactly this problem while being tested: a reworded
destructive request dropped from 0.77 to 0.50 confidence, under the
router's own escalation threshold — a live demonstration that a
confidence-threshold cascade can silently fail exactly where this
article's own warning says it will.

## What's not checkable, and why

No external, dated, or statistical claim appears anywhere in this
article to check against a web search — a genuine first among this
project's deep-analysis rounds. Every named technology (OIDC, Server-Sent
Events, Terraform, circuit breakers, idempotency keys, Little's Law) is
standard, stable, well-documented engineering, and every description of
each one checked against this project's own knowledge is accurate —
Little's Law is applied correctly as L=λW without overclaiming the
stochastic-queueing machinery it doesn't use (a precision issue this
project did flag in an earlier, different source's "M/M/c-inspired"
label), and the circuit-breaker description (temporarily block calls to
a failing dependency, then allow limited test requests after a recovery
interval) is an accurate plain-language description of the standard
closed/open/half-open pattern, even though it never uses that
terminology.

## What's built from this

`/builds/ai-system-design-toolkit/` — two of the article's concepts that
are genuinely new to this project (not already covered by
`/builds/policy-control-plane/`, `/builds/agent-checkpoint-layer/`,
`/builds/run-terminal-ledger/`, `/builds/jev-pattern-router/`, or
`/builds/prop-firm-mcp-server/`'s rate limiter), both fully mechanical
and independently testable:

1. **`capacity_planner.py`** — a real implementation of Section 3's exact
   formulas (daily request volume, average and peak RPS, Little's Law
   concurrency, daily/monthly token consumption, monthly cost), reusable
   for sizing any AI application's backend — not something any existing
   build in this project does (the prop-firm tools size trading risk, not
   AI infrastructure capacity).
2. **`provider_breaker.py`** — the Section 12 circuit-breaker/bounded-
   retry/backoff algorithm, built for real this time. `/builds/
   prop-firm-mcp-server/README.md` explicitly cut this ("no upstream
   network call exists to protect against") when it was the right call
   for a Monte Carlo calculator with no real network dependency; this
   article gives the exact algorithm and this build finally implements
   it against a real flaky-dependency simulation, for the first genuine
   case in this project of a tool meant to wrap an actual unreliable
   external call.

See the build's own README for what's tested and how.
