# Paired-Bootstrap Ratchet

A real, dependency-free Python implementation of a statistically-honest
keep-or-revert gate for an iterative revision loop — built from a real
gap found while deep-reading `FareedKhan-dev/agentic-warehouse-analyst`
(Fareed Khan, "Engineering Multi-Agent AI for a 100 GB Data Warehouse").
Full analysis: `/notes/agentic-warehouse-analyst-analysis.md`.

## The gap this closes

That repo's real `revise()` function
(`notebook/agentic_data_analyst.py:3738`) computes and prints a 95%
paired-bootstrap confidence interval for every keep/revert decision —
but the decision itself,
`keep_if=lambda new, old: new["utility"] > old["utility"]`, never looks
at it. The interval is real, correctly computed, and genuinely
displayed next to every revision in the printed log and the CSV ledger
— it just isn't load-bearing. This module is the fix: a gate that
actually enforces what the printed interval implies.

Two modes, because the real ledger legitimately needs both:

- **`SIGNIFICANT_IMPROVEMENT`** — keep only when the whole interval sits
  above zero (`ci_lo > 0`): for a revision whose entire justification is
  "this metric got better."
- **`NON_REGRESSION`** — keep unless the whole interval sits below a
  floor (`ci_hi < -epsilon`): for a revision (like the real ledger's own
  "sorted copy + rollups" row) whose justification is a *different*
  metric improving while this one merely needs to not get significantly
  worse. An interval that straddles zero is not confident evidence of
  either an improvement or a regression — treated as "not confirmed
  worse," not forced into either label.

## What it found when applied to the real ledger

`tests/real_revisions_sf100.csv` is the actual, unmodified
`revisions_sf100.csv` from the real repo (MIT licensed), copied in for
testing — not a synthetic stand-in. Replaying its real reported
`(delta, ci_lo, ci_hi)` triples through a strict significance gate:

- **r01 (intake), r02 (glossary), r06 (fewshot), r12 (writer swap)** —
  all genuinely pass. Their real intervals do exclude zero; the strict
  gate agrees with the real repo's own KEPT calls here.
- **r09 (sorted copy + rollups)** — the exact case the analysis names:
  real `delta_lo = -0.0098`, which includes zero. Fails the strict
  accuracy-only gate. Passes `NON_REGRESSION` (`ci_hi = +0.0686`,
  nowhere near a significant drop) — correctly modeling that its real
  justification was a latency win, not a statistically confirmed
  accuracy gain.
- **r05 (repair=2)** — a second, more granular instance of the same
  phenomenon, found only by actually building and running the gate, not
  by reading the CSV by eye: real `delta_lo = 0.0` **exactly**. The
  interval touches zero but doesn't exclude it. KEPT in the real repo
  on point estimate alone (+2.9%); fails a strict significance gate,
  honestly, because it is not statistically distinguishable from noise
  at 95% confidence even though the real repo's own point-estimate rule
  called it an improvement.
- **r13 (second writer), r15 (15s budget)** — both real
  `delta_hi = 0.0` **exactly**. Both REVERTED in the real repo, but for
  a point-estimate drop, not a statistically confirmed regression —
  `ci_hi` touching exactly zero means "not significant evidence of
  improvement," not "confirmed evidence of a regression." This build's
  own tests deliberately stop at that honest distinction rather than
  forcing the non-regression gate to also reject these, which would
  overclaim beyond what the reported interval actually supports.

## Usage

```python
from bootstrap_ratchet import Ratchet, GateMode, paired_bootstrap_delta

ratchet = Ratchet()

# From raw paired per-item outcomes (the normal case):
decision = ratchet.evaluate_from_outcomes(
    "r_new_feature", new_outcomes, old_outcomes,
    GateMode.SIGNIFICANT_IMPROVEMENT, seed=42,
)

# From an already-reported (delta, ci_lo, ci_hi) triple -- e.g. a
# third party's own published ledger, where the raw per-item data
# that produced the interval isn't available:
decision = ratchet.evaluate_from_reported(
    "r09", 0.0294, -0.0098, 0.0686, GateMode.NON_REGRESSION,
)

print(decision.kept, decision.reason)
```

## Proven

```bash
python3 test_bootstrap_ratchet.py -v
```

**17/17 tests pass**, including:

- Exact-case correctness (`paired_bootstrap_delta`): identical paired
  sequences give delta=0 and a zero-width interval; every item flipping
  from wrong to right gives delta=1.0 and `[1.0, 1.0]`; mismatched or
  empty inputs rejected; same seed is fully deterministic.
- A real discrimination test at the article's own development-set size
  (102 items): a genuine injected improvement (half of the wrong items
  flip to right) produces an interval that excludes zero; pure noise
  (an independent random redraw at the same rate, no real signal)
  produces an interval that includes zero.
- **A real bug found and fixed while writing the gate tests, not a
  pre-planned design**: the first draft of `NON_REGRESSION` checked
  `ci_lo >= -epsilon`, which is actually a *strict* "must not dip below
  zero at all" rule — mathematically the wrong bound for "not
  significantly worse." The correct check is on `ci_hi`: a regression
  is only significant when the *entire* interval, including its
  best-case upper bound, sits below the floor. Caught immediately by
  the real-ledger tests: under the wrong logic, r09's own real interval
  (which the analysis names specifically) failed the gate it was
  supposed to pass. Fixed, and the corrected logic now matches every
  real case checked by hand.
- The five tests against the real, unmodified third-party
  `revisions_sf100.csv` described above — including two tests whose
  assertions were rewritten mid-build after the real data disagreed
  with the first draft's assumptions (r05 was assumed to clearly pass
  the strict gate; it sits exactly on the zero boundary instead), kept
  honest rather than adjusted to force a pass.

## What's not built here

- The TPC-DS-specific revision loop itself (the real article's
  `revise()`, `scorecard()`, the whole agent pipeline) — inseparable
  from a 28.6GB warehouse this sandbox doesn't have, and not the point:
  the gap found is in the statistics, not the warehouse.
- Multiple-comparisons correction across a whole revision sequence
  (e.g. a Bonferroni adjustment for running many sequential significance
  tests) — a real, known concern with this general pattern, not raised
  or addressed by the source article either, and out of scope for the
  one specific gap this build closes.
