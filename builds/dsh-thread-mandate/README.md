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

`thread_mandate.py`:

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

The real repo's Eval itself (a deterministic *gate* layer plus a model
*assessment* layer, producing `accept`/`stop`/`ignore`/`unavailable`) is
read and credited in `/notes/dsh-superagent-analysis.md` but not
reimplemented -- its assessment layer needs a live model call, and this
project already has adjacent governance mechanisms
(`/builds/policy-control-plane/`, `/builds/agent-checkpoint-layer/`)
covering related ground from different source articles. The real GitHub/
Feishu Source implementations, the panel UI, and the actual DeepSeek
Harness Executor integration are all out of scope here -- none are
testable from this sandbox without a live GitHub App or a live DSH
runtime, and none of them is the generalizable mechanism this build set
out to extract.
