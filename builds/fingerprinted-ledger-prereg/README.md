# Fingerprinted Ledger + Pre-Registration

Two small, dependency-free Python modules extracted from
`FareedKhan-dev/dynamic-workflow-agents` (a real two-edition — Claude and
Qwen — notebook build of a lead-agent/parallel-worker runtime, audited for
real against a 72-planted-bug code library). Not a port of the notebook's
own runtime, which needs a live model and a real code corpus to mean
anything — these two mechanisms, read directly from the real source and
independently reimplemented, generalize cleanly without either:

1. **`ledger.py` — `FingerprintedLedger`.** One SQLite table, keyed by a
   SHA-256 fingerprint of the normalized request (model + messages +
   params + an explicit sample index, so a deliberate repeat gets its own
   slot), gives three properties for free: a cache (don't pay twice for
   the same question), a replay source (run the same notebook offline and
   get the same answers), and a resume journal (a crash just means asking
   the same questions again — everything already answered comes back
   instantly, only the gap costs anything). Three modes: `collect` (call
   live on a genuine miss, cache it), `replay` (serve cache only, raise
   `LedgerMiss` rather than silently falling back to a live call), `smoke`
   (never touches the ledger at all).

2. **`prereg.py` — `Preregistration` + `resume_holds()`.** A hash-locked
   pre-registered hypothesis set: the rules are fixed and SHA-256'd before
   any result exists, and `verify_unchanged()` refuses to decide anything
   if the rule set drifted after the fact — a real anti-p-hacking guard,
   not a cosmetic one. `decide()` turns a boolean into SUPPORTED/NOT
   SUPPORTED/REPORTED (`None` holds means "no comparison exists this run,"
   reported rather than forced into a verdict).

## The real finding this build operationalizes

Verifying the source round, every one of its headline numbers checked out
to the decimal against the real committed artifacts (`exp_main.json`'s
recall/precision figures, the 856/98,028 and 849/97,269 file/line corpus
counts matched against the actual files on disk, the homework and intents
numbers) — the most precisely verifiable source this project has analyzed.
One hypothesis, **H8** ("a crashed run resumes without paying twice"), is
marked **NOT SUPPORTED in both editions** — `exp_claims.json` records
"paid 0 + 0 = 56 calls; same report: True" for Claude and "paid 0 + 1 = 20
calls; same report: True" for Qwen. Read casually, both of those look like
a pass: the report matched, nothing was visibly double-charged. The
notebook's own pre-registered rule is stricter than that, and it's stricter
for a good reason, confirmed by reading the real `decide("H8", H8["holds"],
...)` call site: `H8["holds"]` requires `paid_crash + paid_resume ==
total`, not just "the outcome matched." In both recorded runs,
`paid_crash + paid_resume` is 0 — the whole crash-then-resume sequence was
answered entirely from a pre-populated cache, with zero fresh evidence on
either side of the simulated crash. A naive "did it work" check would have
passed this; the real rule correctly refuses to, because a fully-cached
replay proves nothing about whether a genuinely interrupted, genuinely
resumed run avoids double payment. The source's own README's "Read the
numbers with their limits" section names H6 and H7 as the hypotheses that
"did not meet their stated rules in either edition" — it never mentions
H8, even though H8 fails the same way, for the same reason, in both
editions. `resume_holds()` is that exact rule, generalized, with the real
Claude and Qwen numbers as permanent regression tests proving it still
catches this specific gap.

3. **`plan_guard.py` — `check_program()`/`run_checked()` + `ApprovalPolicy`.**
   Added in a second round, from a full article behind this same repo
   ("Building Dynamic Workflows: A New Agentic System") rather than just the
   bare link the first round had — the lead model writes a short Python
   "plan" instead of a fixed pipeline, and before any worker runs, the plan
   is checked against an AST whitelist (a narrow, named set of syntax nodes,
   a method whitelist, a name whitelist, a length cap, a required `result`
   assignment), then priced and run through a three-way `approved`/`held`/
   `refused` gate against a budget. Independently reimplemented after
   confirming the real mechanism exists in the real notebook (`ALLOWED_NODES`,
   `rule_names`, `dry_run`, `approve`, `AUTO_APPROVE`, `PlanRejected`, all
   grepped directly, not assumed from the article's prose). This module
   covers the static checker and the approval policy — the generalizable,
   model-free halves; the actual dry-run-against-a-stand-in-model step needs
   a live model and is not reproduced.

## The real finding this build operationalizes

### Round 1 (the ledger/pre-registration mechanisms, from the bare repo link)

Verifying the source round, every one of its headline numbers checked out
to the decimal against the real committed artifacts (`exp_main.json`'s
recall/precision figures, the 856/98,028 and 849/97,269 file/line corpus
counts matched against the actual files on disk, the homework and intents
numbers) — the most precisely verifiable source this project has analyzed.
One hypothesis, **H8** ("a crashed run resumes without paying twice"), is
marked **NOT SUPPORTED in both editions** — `exp_claims.json` records
"paid 0 + 0 = 56 calls; same report: True" for Claude and "paid 0 + 1 = 20
calls; same report: True" for Qwen. Read casually, both of those look like
a pass: the report matched, nothing was visibly double-charged. The
notebook's own pre-registered rule is stricter than that, and it's stricter
for a good reason, confirmed by reading the real `decide("H8", H8["holds"],
...)` call site: `H8["holds"]` requires `paid_crash + paid_resume ==
total`, not just "the outcome matched." In both recorded runs,
`paid_crash + paid_resume` is 0 — the whole crash-then-resume sequence was
answered entirely from a pre-populated cache, with zero fresh evidence on
either side of the simulated crash. A naive "did it work" check would have
passed this; the real rule correctly refuses to, because a fully-cached
replay proves nothing about whether a genuinely interrupted, genuinely
resumed run avoids double payment. The source's own README's "Read the
numbers with their limits" section names H6 and H7 as the hypotheses that
"did not meet their stated rules in either edition" — it never mentions
H8, even though H8 fails the same way, for the same reason, in both
editions. `resume_holds()` is that exact rule, generalized, with the real
Claude and Qwen numbers as permanent regression tests proving it still
catches this specific gap.

### Round 2 (the plan-language checker, from the full article)

The full article arrived separately from the bare repo link round 1 used,
with its own file tree (a `build/` package of `config.py`/`bench.py`/
`llm.py`/`runtime.py`/`kit.py`/`plans.py`/`lead.py`) that does **not** match
the real repo on disk — same "article describes a package layout that is
actually one big notebook" pattern already found and documented for
`FareedKhan-dev/ontology-driven-observability` in this project's own prior
round. Confirmed directly: the real repo is still exactly the two notebooks
(`claude/dynamic_workflows.ipynb`, `qwen/dynamic_workflows.ipynb`) round 1
already found, same single commit, no `build/` directory anywhere. But the
mechanisms the article names under those module labels are real, grepped
directly in the actual notebook text rather than trusted from prose:
`class Ledger`, `class Budget`, `class Run`, `class Thread`, `ALLOWED_NODES`,
`rule_names`, `dry_run`, `approve`, `AUTO_APPROVE`, `PlanRejected`,
`check_program`, `class AuditKit`, `scan`/`check`/`vote`/`report`,
`class Lead`, `write_program`, `FIXED_PROGRAM`, `match`, `function_at` all
appear verbatim. Two of the article's named functions (`rule_syntax`,
`blind`) don't exist under those literal names, but the same behavior does
— the real node/method check is one unnamed inline block, and the real
stand-in model has a different name — found by searching for the behavior
once the literal name came up empty, the same discipline already applied to
`ladder.py`/`correlate.py` in the ontology-driven-observability round.

**A real, verified gap found in the source's own published whitelist while
writing this build's tests, not introduced here**: the real `ALLOWED_NODES`
set in the notebook (grepped verbatim) has no `ast.Pass` — meaning the real
system would reject a harmless, idiomatic empty loop body
(`for _ in range(n): pass`) outright, a genuine, if minor, gap in an
otherwise careful design. `plan_guard.py` adds `ast.Pass` deliberately, on
top of the real source's own whitelist, with a one-line stated reason in
the module itself — a backward-compatible widening of this project's own
independent reimplementation, not a silent fix of code this project does
not own. **A second, honestly-preserved limitation, not fixed**: the real
source's own worst-case hostile example — `for i in range(1000000): agent(...)`
— is explicitly reported by the source's own text as passing its static
check ("runaway passes the rules: True"), because a bound of exactly one
million is not "larger than" the million-literal limit; the real system
only catches it later, at dry-run time, via a separate runtime worker-count
cap. `plan_guard.py` reproduces the same static-check pass on that exact
input, rather than silently tightening the rule to make the test look
better than the real source's own documented behavior — a design decision,
not a bug, named directly in both the module's docstring and its test.

## Checked against `/builds/` first

`agent-checkpoint-layer/` does stage-level checkpoint/pause/resume with a
WAL table, not call-level request caching. `run-terminal-ledger/` is an
idempotent singleton-confirmation protocol for a run's terminal status, a
different concern entirely. `policy-control-plane/` governs whether a given
tool call's *parameters* may run, not whether an entire generated program is
syntactically safe to run at all. Neither implements "one fingerprinted
table gives cache+replay+resume for free," the hash-locked pre-registration
guard, or a static AST whitelist for an LLM-written program.

## Proven

53/53 tests across `test_ledger.py`, `test_prereg.py`, and
`test_plan_guard.py` (26 new in round 2, up from 27), including:
cross-process persistence (a fresh `FingerprintedLedger` instance against
the same file sees prior writes — not two in-process objects sharing one
Python process); replay mode genuinely never falls back to a live call on
a miss (asserted by a live-call counter, not just by not raising); the
hash lock catching both a changed claim and an added hypothesis; the
`resume_holds()` suite reproducing the real Claude and Qwen H8 numbers
exactly (correctly fails), the source's own toy S28 demo numbers exactly
(correctly passes), a genuine double-charge (correctly fails), and a
run that never actually crashed (correctly fails regardless of the
accounting); and `plan_guard.py`'s own suite, including a rejected program
genuinely never reaching `exec()` (asserted by a call counter inside the
would-be worker function, not just by the exception), the `ast.Pass`
widening confirmed working, and the runaway example confirmed to pass the
static check exactly as the real source's own text says it does.

## Deliberately not built

The notebook's actual lead/worker/runtime (needs a live Anthropic or
ModelScope key and a real multi-hour run to mean anything — this
sandbox has no live access to either, the same standing restriction as
every build here), the paired-bootstrap statistics behind the recall/
precision intervals (this project already has a real paired-bootstrap
significance gate in `/builds/paired-bootstrap-ratchet/`, built from a
different Fareed Khan source, and duplicating it here would add nothing),
the 72-bug planted-fault benchmark itself (specific to that one algorithm
corpus, not a generalizable mechanism), and the dry-run-against-a-free-
stand-in cost-estimation step (`dry_run()`/`blind()` in the real source) —
needs a scripted model-shaped stand-in wired through a real runtime to
mean anything, and this build's scope is the static checker and the
approval policy that consumes its output, not the runtime around it.
