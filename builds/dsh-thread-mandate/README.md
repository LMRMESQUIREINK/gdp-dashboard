# dsh-thread-mandate

A real, standalone, dependency-free Python reimplementation of the one
mechanism in `deepseek-ai/dsh-superagent-prototype` that is both genuinely
new to this project and fully specified enough to build for real: **Thread
Subscription fan-out**, and the **Policy / Eval / Mandate** authorization
split that keeps "who may act" separate from "who gets to see what."
Analyzed from a pasted Medium article plus the real linked repo in
`/notes/dsh-superagent-analysis.md`.

## What this is NOT

Not a port of dsh-superagent's actual product -- that needs a live GitHub
App, a live Feishu bot, and a live model, none available here. Not the
Router/Worker dispatch loop itself either (no model call exists in this
build). This is the real repo's own `docs/001-domain.md` domain model,
read directly and reimplemented independently from its concept table and
its "Rejected concepts" table -- not copied from the real TypeScript
source (`src/core/*.ts`), which this build never needed to read line by
line once the domain model's own prose rules were clear enough to
reimplement from.

## The real finding this build operationalizes

The Medium article frames DSH's Router/Worker split as better than a
main-agent-coordinates-subagents pattern because "Workers... perceive
conflicts by subscribing to the same Thread" rather than needing central
coordination. Read against the real repo's own domain-model document,
that line understates how deliberate the design actually is: **Subscription
has no admission check at all** -- "A matching Trigger fans out to every
live subscribed Ticket, with no check of who sent it" -- while
**authorization (Mandate) is a separate concept Eval alone can grant**. The
real repo's own "Rejected concepts" table states the reasoning explicitly:
*"Admission checks on Subscriptions" was rejected because "A Subscription
covers the whole Thread; the Mandate separates authorization from
context."* That's the actual mechanism making decentralized conflict
perception safe: a Worker-equivalent can see everything happening on a
Thread it's subscribed to, for free, with no risk of that visibility
quietly becoming new authority, because nothing about Subscription ever
touches a Mandate.

A second real, separately-stated rule closes a gap a naive version of this
idea would have: an ended Ticket's Subscriptions stay alive, and **a
person's message resumes it under its original Mandate with no new
Eval** -- but **a bot or CI message reaching the same subscription does
not resume it at all** ("messages from bots and CI do not reach it, since
its Executor reads its Threads again when it resumes"). Without that
actor-kind distinction, an ended Ticket sitting on a busy CI-heavy Thread
would resume constantly on noise it was never asked to act on again.

A third rule, read from the same table, distinguishes two mechanisms this
build keeps genuinely separate rather than conflating: a person's explicit
**stop** withdraws a Mandate outright, while a **Policy version that no
longer grants a Mandate's scope** also revokes it -- but only when that
Mandate is *revalidated*, which the real repo states happens specifically
"before an ended Ticket resumes," never retroactively against a Ticket
that's still running. "A Policy change on a live Ticket... does not revoke
Mandates" is itself a named rejected-concept entry ("Cancelling running
Tickets on a Policy change" -- rejected: "A cancelled change leaves
half-finished work; the change is recorded and delivered instead").

## Checked `/builds/` first

`/builds/fingerprinted-ledger-prereg/` (from a different source,
`FareedKhan-dev/dynamic-workflow-agents`) already covers a Lead/Worker
runtime's request-fingerprinting and pre-registered-hypothesis mechanisms
-- a different concern (caching/replay/anti-p-hacking, not authorization or
decentralized conflict perception). `/builds/policy-control-plane/`
already covers a three-effect (`ALLOW`/`DENY`/`REQUIRES_APPROVAL`) policy
evaluator with payload-hash-bound human approval -- a different shape of
governance problem (gating a single tool call, not managing a Ticket's
authorization lifecycle across resumes). `/builds/agent-checkpoint-layer/`
covers SQLite-WAL stage checkpoint/resume for a single linear workflow, not
many-to-many Thread/Ticket subscription. `/builds/orchestration-decision-
engine/` covers a single-agent Observe-Evaluate-Choose-Execute-Verify retry
loop, not multi-worker conflict perception. None of them implement
Subscription-based fan-out or a Mandate that survives a Ticket's end and is
only revalidated on resume -- a genuinely new gap.

## What's built

### `eval_gate.py` and `assessment.py` -- the real two-layer Eval, gate built, assessment's interface typed

Real repo: *"Eval -- The judgement on a batch of Triggers, in two layers:
gate and assessment... Gate -- The deterministic first layer of Eval: who
may originate work, and with what strength... Assessment -- The model's
judgement during Eval."* The README above originally said Eval itself was
"read and credited... but not reimplemented" -- that's now only true of
the model call inside the assessment layer; the gate layer is built and
tested, and the assessment layer's typed contract is too.

`eval_gate.py`'s `run_gate_eval(batch, policy, gate_rules, *,
expired_attempts=0, assessor=None)` takes an `EvalBatch` straight off
`Thread.start_eval()` and produces a real `EvalResult` (`decision`,
`mandate`, `strength`, `matched_scope`, `reason`). `accept_ticket()` and
`apply_stop()` are the two things an `EvalResult` is ever used for: create
a real, Subscription-fan-out-ready `Ticket` on `ACCEPT`, or withdraw a
targeted `Ticket`'s `Mandate` on `STOP`.

`assessment.py` closes a real gap in the gate-only version: with no
assessment layer, `run_gate_eval()` returned `IGNORE` the instant no gate
rule matched -- collapsing "no deterministic rule exists" into the same
bare decision as "a real assessment layer was consulted and declined,"
even though the real repo's Strength group (`explicit`/`inferred`) implies
these are different situations: only the assessment layer can ever grant
`inferred` strength (a gate rule only ever grants `explicit`), so a gate
miss was never itself a reason to stop looking. `AssessmentRequest`/
`AssessmentResult`/`Assessor` (a plain `Callable[[AssessmentRequest],
AssessmentResult]`) are the typed contract an assessor would plug into;
`EvalResult.reason` now distinguishes, in plain text, "no gate rule
matched; no assessment layer is configured" from "no gate rule matched;
assessment layer was consulted and declined." **No live model
implementation of an `Assessor` exists in this sandbox** -- the same
standing restriction as every other build here needing a live model call.
`test_assessment.py` exercises the real hand-off with a scripted stand-in
assessor, same mocking convention this project uses throughout for a
model-dependent component.

An assessor is held to exactly the same check the gate layer already
enforces for its own rules: it can name an `ACCEPT`/`STOP` scope, but that
scope still has to be one the *current* `Policy` grants, or it's refused
and falls through to the real `IGNORE`. A matching gate rule always
decides the batch *without ever calling the assessor at all* -- proven
directly in the test by a call-counter assessor that's wired in but never
invoked when the gate layer already matched.

```bash
python3 test_eval_gate.py      # 22/22
python3 test_assessment.py     # 20/20
```

### `thread_mandate.py`

- `Trigger` -- one immutable event, carrying an `ActorKind` (`PERSON`,
  `BOT`, or `CI`), matching the real repo's own actor-kind distinction.
- `Policy` -- a versioned set of granted scopes.
- `Mandate` -- immutable except for one state transition (`withdraw()`,
  called only by a person's explicit stop); `revalidate(policy)` raises
  `MandateRevoked` if the *current* Policy no longer grants the Mandate's
  scope, even if it was valid under the Policy version it was created
  under.
- `Ticket` -- `stop()` withdraws its Mandate and marks it permanently
  unreachable; `receive_context()` is the one thing Subscription fan-out
  ever does to a Ticket, and it never raises, never checks authorization,
  and never triggers an Eval.
- `Thread` -- holds Subscriptions (many Tickets to one Thread, matching the
  real repo's rejected "at most one live Ticket per Thread" rule),
  `ingest()` fans a Trigger out to every live subscribed Ticket with no
  admission check, and `start_eval()`/`end_eval()` enforce at-most-one-
  running-Eval-per-Thread, merging Triggers that arrive mid-Eval into the
  *next* batch rather than the one already taken.

## Verification

```bash
python3 test_thread_mandate.py
```

16/16 checks pass on the real run, each one a direct, named reproduction
of a specific rule or rejected-concept entry from the real repo's
`docs/001-domain.md` (quoted in both the module's docstrings and the test
labels, so a failure here means a real disagreement with the source, not
an arbitrary synthetic expectation):

- Fan-out with zero admission check.
- Two independently-subscribed Tickets perceiving the same Trigger with no
  central coordinator -- the actual "perceive conflicts by subscribing to
  the same Thread" mechanism the source article names.
- Fan-out never triggers a fresh Eval.
- A stopped Ticket receives nothing further, and its Mandate is withdrawn.
- An ended Ticket resumes under its *original* Mandate on a person's
  message, but a bot/CI message on the same subscription does not resume
  it at all.
- A Ticket ending normally (not via `stop()`) leaves its Mandate intact.
- A Policy that no longer grants a Mandate's scope revokes it on
  revalidation -- a mechanism kept structurally distinct from a person's
  stop (the test asserts the Mandate was never *withdrawn*, only
  *revoked by revalidation*).
- A Policy change never retroactively touches a still-running Ticket's
  Mandate.
- At most one Eval runs on a Thread at a time; a second `start_eval()`
  call while one is running raises.
- A Trigger arriving mid-Eval lands in the *next* batch, not the one
  already taken.

**No bug found in this build's own first draft** -- all 16 checks passed
on the first real run, stated plainly rather than manufactured. (One
typo was caught and fixed before the first run: several docstrings in
the first draft of `thread_mandate.py` closed with four quote characters
instead of three, a straightforward syntax error caught immediately by
`python3 -c "import ast; ast.parse(...)"` before any test was written.)

## What's deliberately not built here

A live `Assessor` implementation -- the actual model call behind
`assessment.py`'s typed contract -- needs a real model API, the same
standing restriction as every other build in this project needing one;
`test_assessment.py`'s scripted stand-in proves the hand-off mechanism
itself, not a real model's judgement. This project already has adjacent
governance mechanisms (`/builds/policy-control-plane/`,
`/builds/agent-checkpoint-layer/`) covering related ground from different
source articles, so a second, redundant general-purpose policy engine
wasn't built here either -- `eval_gate.py`'s `GateRule` is deliberately
narrow (originate/stop scopes keyed to actor names), matching only what
the real repo's own Gate concept actually is.

The real GitHub/Feishu Source implementations, the panel UI, and the
actual DeepSeek Harness Executor integration are all out of scope here --
none are testable from this sandbox without a live GitHub App or a live
DSH runtime, and none of them is the generalizable mechanism this build
set out to extract.

## Where this is used elsewhere in the project

`/builds/interface-lift-toolkit/thread_gate_tool.py` copies
`thread_mandate.py` and `eval_gate.py` in unmodified (this project's
standard cross-build convention: a static, point-in-time snapshot, not a
live sync -- that copy does not carry this round's `assessment.py`
addition, since the toolkit's gate wiring has no present need for it) and
wires `run_gate_eval()`/`accept_ticket()`/`apply_stop()` onto that
toolkit's real `ToolRegistry`, so a Ticket's Mandate genuinely gates real
tool dispatch (`prop_firm_size_check`) rather than staying a standalone
demo. See that build's own README/`okf_knowledge/` bundle for the details.
