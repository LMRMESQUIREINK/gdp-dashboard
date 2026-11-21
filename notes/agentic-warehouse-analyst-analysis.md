# Deep analysis: "Engineering Multi-Agent AI for a 100 GB Data Warehouse"

Source: a pasted Fareed Khan article (Medium, Oct 26 2026), no accompanying
instruction — run through the new `/analyze-and-ship` command for the
first time. A repeat author for this project (five prior rounds:
production-grade MCP servers, interface lifting, and the three-article
"agentic systems deep dive"), but this is a new article, confirmed by
title before touching anything.

## Measured, not assumed

Unlike every prior Fareed Khan round, this one names a real companion
repo (`FareedKhan-dev/agentic-warehouse-analyst`) and the article itself
is overwhelmingly real executable code with "left out" notes at the end
of nearly every section — a strong signal there's more real material
behind it than what's pasted. Cloned and read directly rather than
trusted on the article's word:

- MIT licensed, single commit (`e8922eb...`, Oct 22 2026), real
  `tools/`, `notebook/`, `ALLOWED_MODELS.md`.
- `notebook/agentic_data_analyst.py` — 6,679 lines, the real literate
  source the article's own file tree (`config.py`, `data.py`, `guard.py`,
  etc.) is distilled from as sections, not separate files.
- `notebook/artifacts/` contains **real recorded run output**, not just
  code: `run_manifest_sf100.json` (machine specs, package versions,
  warehouse byte counts, model prices), `revisions_sf100.csv` (the full
  12-row revision ledger — every KEPT/REVERTED decision with its exact
  utility/accuracy/latency numbers), and `llm_cache.sqlite` with
  **4,005 real cached model calls** — consistent with roughly a dozen
  revisions times ~100 dev questions times several calls per question,
  not a number that's easy to fake convincingly.
- Every specific number checked against the real executed notebook
  output (`notebook/agentic_data_analyst.executed.ipynb`) matched
  exactly: "92/93 official answers reproduced," "469,796x" planner
  underestimate, "85,927,834,294,703" rows (this project's own
  estimator's figure) against "135,299,781,560,539" (the real exact
  count) — ratio 1.575, matching the article's own "within a factor of
  1.6" claim precisely. The warehouse byte count (28,609,622,016) and
  every dated test/live-stopwatch figure (66.7%→90.9%, 47.1%→9.8%,
  3.82s/24.55s) all appear verbatim in the real notebook source, not
  only in the article's retelling of it.

This is the most thoroughly independently-verifiable source this
project has analyzed to date — ahead even of REA (which had real code
but no recorded execution artifacts) and the multi-tenant LLM series
(verified arithmetic but no underlying run data at all).

## What's credited

- **Full, unprompted self-disclosure of missed targets.** The article's
  own "Known Limits" section states plainly that both the false-success
  rate (9.8% vs. a 5% target) and the live p95 latency (24.55s vs. a
  15s target) missed their stated goals — not buried, not spun, placed
  right where the numbers appear. This is the same honest-negative-result
  credit this project has given before (the Jev article's "does not
  seem to be doing well," the quantum article's "only 2 of 5 seeds") and
  it's rarer here because almost everything else in this piece reads as
  a clean win.
- The statement guard's custom row-cost estimator — distinct selectivity
  rules for fact-stream fan-out vs. ticket/order-number joins vs.
  grouping vs. filtering, with a correction ratio propagated up through
  the plan tree — is genuinely careful, specific engineering, not a
  hand-wave "we added guardrails" claim, and it's backed by a concrete,
  checkable before/after (a 469,796x planner error, corrected to within
  1.6x of the true count).
- The security section runs 11 real attacks against four wall
  configurations and reports that the "read-only" connection alone let
  5 through — an honest demonstration that read-only mode is not the
  security boundary it sounds like, matching this project's own
  standing "the model requests, the application enforces" principle
  from several earlier rounds (`/builds/policy-control-plane/`, the AI
  System Design article round).

## What doesn't fully hold up: the bootstrap CI is informational, not load-bearing

Checked directly in the real source, not inferred from the article's
prose. Section 10 computes a 95% paired-bootstrap confidence interval
for every revision decision (`paired_delta()`, `notebook/
agentic_data_analyst.py:3544`) and prints it alongside every
KEPT/REVERTED call — giving the strong visual impression that each
decision is statistically gated. It isn't. `revise()`
(`notebook/agentic_data_analyst.py:3738`) has this exact signature:

```python
def revise(rev, cfg, change, hypothesis, budget=80.0,
           keep_if=lambda new, old: new["utility"] > old["utility"]):
```

`kept = keep_if(new, old)` is computed from the scorecard dict alone —
it never receives or inspects the `(delta, lo, hi)` tuple that
`log_revision()` separately computes and writes to the CSV a few lines
later. The confidence interval is real, correctly computed, and
genuinely printed next to every decision — but the decision itself is a
bare point-estimate comparison. Checked against the real
`revisions_sf100.csv`: r09 ("sorted copy + rollups") was KEPT with
`delta_correct=+0.0294, delta_lo=-0.0098, delta_hi=+0.0686` — a
confidence interval that **includes zero**, meaning the accuracy
improvement alone isn't statistically distinguishable from noise at
95% confidence, yet the revision reads as validated by the same
interval sitting right next to it in the ledger. This isn't a wrong
call — r09's real justification is a latency win with accuracy merely
not regressing, a legitimate and different criterion the article's own
prose states plainly ("warehouse time drops while every answer stays
the same") — but the printed CI creates an appearance of statistical
rigor for the accuracy claim specifically that the code doesn't
actually enforce anywhere.

## What's unverifiable, stated as such

- The opening paragraph's four citations (ECNU/Gartner/Google
  Research/NN Group links for accuracy/governance/speed/latency
  tolerance) were not independently fetched and checked this round —
  one of them (the NN/g "Response Times: The 3 Important Limits"
  reference) is a well-known, genuinely real UX source independent of
  this check; the other three are plausible but not verified here.
- The repo's own GitHub description and commit message round the
  warehouse to "1B-row," while the body text throughout the article and
  the real manifest both state the precise figure (959,031,513 rows) —
  a minor, non-deceptive headline-vs-body rounding, not a discrepancy
  worth treating as a finding on its own, noted for precision.
- The architecture diagram and several other embedded images are not
  independently checkable from text.

## What's built from this

`/builds/paired-bootstrap-ratchet/` — not a port of the article's own
TPC-DS-specific revision loop (that's inseparable from a 28.6GB
warehouse this sandbox doesn't have), but the one generalizable
mechanism the finding above points directly at: a paired-bootstrap
significance gate that actually enforces what the printed CI implies,
with two modes (strict significant-improvement, and non-regression for
the legitimate r09-style case), tested against synthetic data and
directly against the real `revisions_sf100.csv` numbers. See the
build's own README for what it found when applied to the real ledger.
