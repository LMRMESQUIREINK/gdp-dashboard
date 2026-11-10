# Analysis: "Building Your First Orchestration Agent" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 18 of a "Quality Engineering"
tutorial series (Aug 29, 2026) — a purely pedagogical piece: the author's
own original teaching framework for a fictional "QE Orchestrator"
pipeline (Requirement Analyzer → Scenario Designer → Playwright Test
Generator → Test Reviewer → Quality Gate → Coverage Analyzer). Measured
first (156 lines / 1,570 words in the saved condensed copy,
`sha256sum`'d) before reading for meaning.

## No external claim to verify — confirmed, not assumed

Unlike most sources this project has analyzed, there's no GitHub repo,
paper, company, or statistic named anywhere in this article (confirmed
by grepping the saved copy for `github.com`/`arxiv`/any `http(s)://`
link — none found, and a full read confirms the only links in the
original are the author's own Medium byline). This is closer in kind to
the earlier "AI System Design" and "Agentic Harness Frameworks" rounds
than the GitHub-repo rounds: the verification surface is entirely
internal — does the article's own worked example and its own
configuration artifact agree with each other, and does its one piece of
arithmetic (the retry-count/coverage sequence) hold together.

## What checked out

- The retry-count arithmetic is internally consistent: coverage 82% →
  (execute, re-observe) → 88% → not verified → retry_count becomes 1 →
  (execute again) → 100% → verified. The article's own stated
  `recovery.retries: 2` budget is never exceeded (only 1 retry used),
  and the mid-example "Retry Count: 1" value matches exactly what the
  described sequence would actually produce.
- The explicit Evaluate/Choose separation — "if those two stages
  collapse into one, the agent immediately becomes another black box" —
  is a genuinely sound architectural discipline, and the article states
  it plainly and correctly: Evaluate produces facts, Choose consumes
  them, with no side effects in between.
- "Mistake #3: Ignoring Workflow State" is a concrete, correctly-reasoned
  failure mode, illustrated cleanly: a router with no retry-count
  tracking really would loop forever on a producer that improves
  coverage without ever crossing the threshold — the article's own
  worked illustration (82 → 88 → 88 → 88 → ...) is exactly the failure
  this project's own `agent-checkpoint-layer` and `defender-loop-
  verifier` builds independently guard against in their own domains,
  arrived at the same way (bounded retry, explicit state, never assume).

## The real gap: the article's own prose and its own config artifact disagree

The article's "Choose" stage, in its own worked example, credits a
specific judgment: *"because the business requirement already exists in
the Requirement Package, clarification isn't necessary. The missing
capability simply hasn't been transformed into executable scenarios."*
That's a judgment over the **content** of the Requirement Package — is
"Refund Workflow" actually documented there, yes or no.

The article then presents a YAML "Agent Configuration" as the artifact
that *"becomes executable orchestration logic"* for exactly this
reasoning. But every `decision_rules` entry in that YAML is a flat
numeric check — `condition: coverage < 90`, `condition: review_failed`,
`condition: approval_rejected` — with no field anywhere that could
represent "is this specific requirement documented." Read the two
artifacts against each other, not either alone: the YAML schema the
article presents as *encoding* the prose's reasoning structurally
**cannot** encode it. The "Request Business Clarification" branch the
prose lists as one of four considered actions has no corresponding rule
in the config at all — it exists only in narrative, never in the
artifact claimed to make that narrative executable.

This is exactly the kind of finding this project's own standing
discipline is built to surface: reading one source's own two halves
against each other, which the source itself never does.

## Build: `orchestration-decision-engine`

`/builds/orchestration-decision-engine/` — not the article's own
fictional QE pipeline, but the generalizable orchestration mechanism:
a pluggable multi-producer router driven by declarative decision rules
(`Rule.condition` as a real callable over the full facts dict, closing
the gap found above — a rule *can* depend on content, not just flat
numeric thresholds), with retry-bounded recovery and escalation. Checked
`/builds/` first: `policy-control-plane` (policy evaluation + approval),
`agent-checkpoint-layer` (checkpoint/resume), `gate-floor-checker`
(gate classification), `defender-loop-verifier` (host-side
re-verification), and `ai-system-design-toolkit`'s `provider_breaker.py`
(retry/backoff for upstream calls) are all adjacent but none implement
this specific mechanism: a full Observe→Evaluate→Choose→Execute→Verify
loop with bounded per-workflow retry state, refusing the article's own
four named "Common Mistakes" by construction rather than convention.

17/17 tests pass, including the article's own worked example reproduced
exactly and the schema-gap finding proven directly (the same facts
function branches to two different actions depending on requirement
content — something the article's own flat YAML condition structurally
cannot do).

**One real design bug found and fixed in this build's own first draft**,
not the source: reproducing the worked example as a test caught that
the first version of `run_cycle()` returned a bare "no matching rule"
result whenever nothing needed fixing — exactly the state the article's
own final cycle reaches (coverage=100, no rule fires) — and never
checked verification at all. Fixed by treating "no rule matched" as
"nothing to execute, verify current facts directly" rather than an
error, and by always re-observing fresh state immediately after any
rule *does* fire, so `Verify` never checks stale, pre-execution facts.
One honestly-stated resolution of an ambiguity in the source rather than
forcing an exact match: the fix reproduces the article's exact two
named cycles and exact coverage sequence, but calls the real producer
once, not twice as the article's own cycle-2 prose states — the
article's own narrative doesn't fully specify whether cycle 2's
starting observation is a fresh read or a restatement of cycle 1's
post-execution check, and this build resolved that ambiguity toward the
cleaner, testable semantic.
