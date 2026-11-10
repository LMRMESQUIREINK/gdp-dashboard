# orchestration-decision-engine

A real, standalone implementation of the Observe-Evaluate-Choose-Execute-
Verify orchestration loop from "Building Your First Orchestration Agent"
(rajesh yemul, Medium) — not the article's own fictional "QE Orchestrator"
pipeline (Requirement Analyzer/Scenario Designer/Playwright Test
Generator/etc.), which is just that article's worked-example flavor, but
the generalizable mechanism underneath it: a pluggable multi-producer
router driven by declarative decision rules, with retry-bounded recovery
and escalation. Analyzed in
`/notes/orchestration-agent-loop-analysis.md`.

## What's real here, and the gap it closes

The source article is a purely pedagogical piece — no external repo,
paper, or product to verify against (confirmed by reading the whole
article; there's nothing here like `google-research/harness2` or
`morluto/rea` to clone). The verification surface was entirely internal:
does the article's own worked example and its own configuration artifact
agree with each other?

**They don't, and that's the real finding this build closes.** The
article's "Choose" stage narrative explicitly credits a content-dependent
judgment: *"because the business requirement already exists in the
Requirement Package, clarification isn't necessary. The missing capability
simply hasn't been transformed into executable scenarios."* But the
article's own YAML "Agent Configuration" — the artifact it presents as
*"this becomes executable orchestration logic"* — only has flat numeric
conditions (`condition: coverage < 90`). A flat condition like that can
never check whether a specific requirement is documented; there's no field
for it anywhere in the schema. The YAML literally cannot represent the
reasoning the prose credits it with encoding.

`decision_engine.py`'s `Rule.condition` is a real Python callable over the
**full** evaluated-facts dict, not a flat comparison string — specifically
so a rule *can* express that judgment. `test_decision_engine.py` proves it
directly: the same facts function branches to `Scenario Designer` when the
missing requirement is documented and to `Request Business Clarification`
when it isn't — the exact distinction the article's own config schema has
no way to reach.

## The four "Common Mistakes" the article names, refused structurally

Not just avoided by convention — each one is tested directly:

1. **The orchestrator performing producer work itself.** `Router.execute()`
   is the *only* path any action ever runs through, and it only ever calls
   a registered producer callable. Calling an unregistered action raises
   `UnknownActionError` loudly rather than falling back to an inline
   implementation.
2. **Assuming success without verification.** `OrchestrationAgent` never
   marks a workflow done on execution alone — only a `True` from
   `verify_fn` can produce `VERIFIED`, proven even with a zero-retry
   budget.
3. **Ignoring workflow state → the named infinite loop** (the article's
   own "Coverage: 88% → Scenario Designer → Coverage: 88% → Scenario
   Designer → ...forever" example). Reproduced with a producer that never
   improves anything and a `verify_fn` that never passes: the engine runs
   exactly `max_retries + 1` cycles, then reports `ESCALATED` — not an
   infinite loop, with the real call count checked directly, not just a
   status string.
4. **Embedding business logic inside orchestration.** Nothing in
   `DecisionEngine`, `Router`, or `RecoveryEngine` computes an engineering
   artifact — they only read facts, pick an action name, and dispatch to
   caller-registered functions.

## A real design bug found and fixed in this build's own first draft

Reproducing the article's own worked example (coverage 82% → 88% → 100%,
two named cycles) as a test caught a real gap in the first version of
`run_cycle()`: when no decision rule matches — which is exactly what
happens once the objective is *already* met (coverage=100, nothing is
`< 90`) — the first draft returned a bare "no matching rule" result and
never checked verification at all. The article's own final cycle hits
precisely this state, and the test failed immediately: `NO_MATCHING_RULE`
instead of `VERIFIED`.

Fixed architecturally: "no rule matched" is now treated as "nothing to
execute," not an error — verification still runs, against whatever facts
are current. And since the article's own `Verify` step always means
*"check the state **after** something ran,"* a rule firing now re-observes
fresh state immediately after `Execute`, rather than letting `Verify` ever
check a stale, pre-execution observation. `CycleOutcome.NO_MATCHING_RULE`
was removed entirely once this was fixed — it was never reachable again.

One honestly-stated resolution, not forced to match the source exactly:
with this fix, the reproduced worked example runs in **2 cycles** (observe
82 → execute → re-observe 88 → not verified; observe 100 → already met,
nothing to execute → verified), matching the article's own "CYCLE 1" /
"CYCLE 2" naming — but the real `Scenario Designer` producer in this
reproduction is called **once**, not twice as the article's cycle-2 prose
literally states ("routes to the Scenario Designer once again"). The
article's own narrative is a little loose about whether cycle 2's starting
observation is a fresh read or a restatement of cycle 1's own
post-execution check; this build resolved it toward the cleaner, testable
semantic (verify always re-observes immediately after execute) rather than
forcing an exact match to an inherently ambiguous bit of prose.

## Proven

```bash
python3 test_decision_engine.py
```

**17/17 assertions pass**, including:

- The article's own worked example reproduced exactly (82% → 88% → 100%,
  `RETRYING` then `VERIFIED`, `retry_count` reaching exactly 1 — matching
  the article's own mid-example "Retry Count: 1" value).
- The content-dependent `Rule.condition` branching test that proves the
  schema gap is closed.
- The named infinite-loop failure mode, reproduced and refused by
  construction.
- `Router.execute()` refusing an unregistered action.
- A zero-retry-budget cycle still never claiming `VERIFIED` on a failed
  verification.
- `DecisionEngine.choose()` proven pure (same facts in → same `Rule`
  object out, no mutation, no hidden state).
- `WorkflowState.retry_count` proven isolated per `workflow_id` — never
  shared across runs, matching the article's own explicit "state is not
  memory" distinction.

## What's deliberately not built here

- **Any real "producer" logic** (an actual test generator, coverage
  analyzer, etc.) — the article's own domain is a worked-example flavor,
  not something to build literally; producers here are test doubles that
  record calls and return canned results, which is all the orchestration
  mechanism itself needs to be proven correct.
- **Cross-run memory / an experience library** — the article explicitly
  scopes this out of its own series ("Today we are building autonomous
  execution... later in Season 4, we'll introduce workflow memory"), and
  this build respects that same boundary: `WorkflowState` is per-run only.
- **Multi-agent coordination** — the article's own closing section names
  this as future work ("one orchestration agent eventually becomes
  another bottleneck... multiple specialized agents collaborate"), out of
  scope for a single-orchestrator decision loop.
