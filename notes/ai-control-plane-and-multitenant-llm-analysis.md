# Deep analysis: "Building an Enterprise AI Control Plane" + "Multi-Tenant LLM Systems" (Parts 1–3)

Source: four uploaded Medium articles by the same author (Sesha Giri) — one
describing a self-built "AI Control Plane" (ACP) for governing agentic AI
(policy enforcement, human-in-the-loop approval, audit evidence), and a
three-part series on multi-tenant LLM platform architecture (why single-
tenant design breaks, isolation strategies, and capacity-planning math).

## What kind of source this is

Better than the "Agentic Harness Frameworks" survey analyzed last round,
worse than the Fareed Khan deep-dives: no runnable code or repo link is
given for either piece, but the multi-tenant series' Part 3 does real,
checkable arithmetic (Little's Law sizing, a burst/backlog/drain-time
calculation, a token-cost invoice) rather than just asserting conclusions.
That arithmetic was independently recomputed for this analysis, not taken
on faith — see below.

## Part A: The AI Control Plane (ACP) article

### The design, in one line each

- **Three-state policy effects, not two**: `ALLOW`, `DENY`, and
  `REQUIRES_APPROVAL` as a first-class third state — human approval is
  "configuration, rather than a special-case branch hidden inside
  orchestration code."
- **Deterministic policy resolution**: disabled policies discarded →
  highest-priority applicable policy wins → ties broken by effect
  precedence `DENY > REQUIRES_APPROVAL > ALLOW` → no applicable policy
  defaults to `DENY`.
- **Parameter-level governance**: the same API operation can resolve to
  different effects depending on its arguments (`createRefund` with
  `amount > 1000` routes to `REQUIRES_APPROVAL`), which is "much closer to
  how enterprises actually think about risk" than a flat per-endpoint
  permission.
- **The agent never holds the execution credential.** It asks ACP to
  perform the operation; ACP's Runtime is the only thing that ever reaches
  the real tool. This is the single load-bearing design decision in the
  whole piece: without it, "if the agent holds the provider credential and
  the tool credential, then the agent itself becomes the enforcement
  point. That is not really enforcement. It is advice." That line is the
  best-stated idea in the article.
- **MCP tool discovery becomes a governance event**: an agent never
  inherits an MCP server's tool catalogue directly — onboarding registers
  each discovered operation as an independently governable ACP operation,
  idempotently (re-registration reconciles rather than duplicates).
- **Payload-hash-bound approval**: when a request is deferred, the exact
  request payload is hashed with canonical JSON + SHA-256 and bound to the
  approval record, so the system "retains proof of what was requested
  without storing a second copy of the business payload," and resuming
  re-verifies "the approval, trace, identity, operation, payload hash and
  policy revision before execution" — not just a boolean "was this
  approved."

### What's genuinely well-reasoned

All five points above. In particular, the payload-hash-binding step is a
real, specific defense against a bug that's easy to introduce by
accident: approving request A and then letting a *different* request B
execute under that same approval ID because nothing checked that the
payload hadn't changed between proposal and resume. Most HITL-approval
designs analyzed in this project before this (including this project's
own `/builds/agent-checkpoint-layer/`, built last round) never checked
for that — the approval was keyed only by run ID, not by what was
actually being approved.

### What doesn't check out, or can't be verified from here

- **"To explore this problem, I built an AI Control Plane"** is the only
  claim of a working system in the whole piece, and nothing in the pasted
  text is independently checkable: no repository link, no code snippet
  beyond none at all, and every diagram is a `Press enter or click to
  view image in full size` placeholder this analysis cannot see. The
  *design* is detailed and consistent enough to be worth taking
  seriously as a design; the claim that it was actually built and run is
  not verified here, same category as every other "I built X" claim this
  project has flagged rather than silently repeated as fact.
- **Microsoft Entra ID, FastAPI/PostgreSQL/SQLAlchemy, React/TypeScript,
  Redis** are named as the implementation stack with no version, no
  deployment detail, and no operational evidence (uptime, a real audit
  trace, a real approval latency) — asserted, not shown.

## Part B: Multi-Tenant LLM Systems (Parts 1–3)

### What's genuinely well-reasoned

- **"LLM cost = f(input tokens, output tokens, model size)", not request
  count** is the correct, specific reason RPS-based autoscaling (the
  default for ordinary REST APIs) doesn't transfer to LLM gateways — a
  real mechanism, not just an assertion.
- **Isolation as a spectrum across three independent dimensions** (data,
  compute, operational) rather than a single shared-vs-dedicated switch
  is a materially more useful framework than most "multi-tenancy" advice,
  and the recommended hybrid (`Region → Tier → Runtime → Data`) correctly
  separates *why* you isolate (compliance, SLA, blast radius) from *how*
  (namespace, cluster, queue, schema) at each layer.
- **"Policy defines the boundary. Optimization happens inside that
  boundary"** (compliance constraints are a hard limit the optimizer
  isn't allowed to cross, not another variable it trades off) is a
  precise way to keep a system from "optimizing" its way into a
  compliance violation nobody signed off on.

### The arithmetic — independently recomputed, and it holds up

Part 3's worked example is the first fully-checkable set of numbers in
this family of sources. Recomputed directly rather than trusted:

| Claim | Recomputed | Checks out? |
|---|---|---|
| Gold: `L = λW = 50×1 = 50` concurrent | 50 | ✅ |
| Gold: `50/6 ≈ 8.3 → 9` min workers | 8.33 → 9 | ✅ |
| Gold: `9/0.7 ≈ 12.8 → 13` workers w/ headroom | 12.86 → 13 | ✅ |
| Gold validation: `13×6=78` slots, `50/78≈64%` util | 78, 64.1% | ✅ |
| Silver: `40/10=4`, `4/0.8=5` workers, `40/50=80%` | exact | ✅ |
| Burst: `150/78≈1.92` utilization | 1.923 | ✅ |
| Burst: queue growth `150-78=72/s` | 72 | ✅ |
| Burst: 30s backlog `72×30=2,160` | 2,160 | ✅ |
| Drain rate `78-50=28/s`, clear time `2160/28≈77s` | 28, 77.1s | ✅ |
| Cost: `30M tokens × $0.50/1K × 1.25 = $18,750` | $18,750 | ✅ |

Every number the article states is reproducible from its own stated
inputs. That's a meaningfully higher evidentiary bar than most sources
analyzed in this project, and the author is explicit about the numbers
being illustrative ("intentionally simple... in a real system, these
numbers would come from production telemetry") rather than claiming
production validation it doesn't have — an honest framing, credited as
such.

### One real, specific imprecision worth flagging

The burst section is titled "p95 Under Burst: M/M/c-Inspired
Approximation," and the text does hedge ("I am not using the full M/M/c
formula... I am using the same basic idea"). But what's actually computed
— `queue growth = arrival rate − capacity`, a linear backlog accumulation
— isn't M/M/c at even an approximate level; it's a deterministic fluid
model with no stochastic machinery at all (no Poisson arrivals, no
Erlang-C waiting-probability formula, nothing memoryless about it). The
hedge is honest, but the "M/M/c-inspired" label still borrows more
queueing-theory credibility than the actual calculation uses — worth
naming precisely rather than letting the label stand unexamined, the
same way this project named TypeSafe's "RLCD" claim and the "ROOTS"
mnemonic for what they actually are two rounds ago.

## What was built from this (see `/builds/policy-control-plane/README.md`)

The ACP article's policy-evaluation model and payload-hash-bound approval
step are concrete, implementable, and immediately useful against real
tools already in this project — so they were built for real, extended
from (not duplicating) the HITL approval mechanism already built last
round in `/builds/agent-checkpoint-layer/`. The multi-tenant series' own
subject matter — real tenant traffic, Kubernetes namespaces, regional
deployments, Kafka usage-event streaming, Entra ID — describes
infrastructure this project doesn't have and isn't the right next build
for a single local codebase with no live traffic; its contribution here
is the independently-verified arithmetic above, not a new build.
