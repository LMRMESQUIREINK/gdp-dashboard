"""A paired-bootstrap significance gate for a keep-or-revert revision
ratchet -- built from a real gap found while reading
FareedKhan-dev/agentic-warehouse-analyst (see
/notes/agentic-warehouse-analyst-analysis.md).

That repo's real `revise()` function (notebook/agentic_data_analyst.py:
3738) computes and prints a 95% paired-bootstrap confidence interval for
every keep/revert decision (`paired_delta()`, same file, line 3544) --
but the actual decision, `keep_if=lambda new, old: new["utility"] >
old["utility"]`, never looks at that interval. It's real, correctly
computed, and genuinely displayed next to every decision -- just not
load-bearing. This module is the fix: a gate that actually enforces
what the printed interval implies, with two modes, because the real
ledger legitimately needs both:

  - SIGNIFICANT_IMPROVEMENT: keep only when the interval's lower bound
    excludes zero -- for a revision whose entire justification is "this
    metric got better."
  - NON_REGRESSION: keep when the interval doesn't show a real drop --
    for a revision (like the real ledger's own "sorted copy + rollups"
    row) whose justification is a *different* metric improving (there,
    latency) while this one merely needs to not get worse.

Dependency-free: the bootstrap resampling uses the standard library's
`random` module, not numpy, matching this project's established
convention for small standalone tools.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


@dataclass(frozen=True)
class BootstrapResult:
    delta: float
    ci_lo: float
    ci_hi: float


def paired_bootstrap_delta(
    new_outcomes: Sequence[float],
    old_outcomes: Sequence[float],
    *,
    n_resamples: int = 2000,
    seed: int | None = None,
) -> BootstrapResult:
    """The same statistic the source article computes: the mean paired
    difference between two equal-length, item-aligned outcome
    sequences, with a 95% confidence interval from resampling the
    per-item differences with replacement.

    `new_outcomes`/`old_outcomes` are whatever per-item score the
    caller is comparing -- 1.0/0.0 for correct/incorrect, a continuous
    utility value, anything paired and numeric. Both must be the same
    length and in the same item order (paired, not independent
    samples) -- the entire point of a *paired* bootstrap is that each
    resample redraws matched (new_i, old_i) pairs together.
    """
    if len(new_outcomes) != len(old_outcomes):
        raise ValueError("new_outcomes and old_outcomes must be the same length (paired)")
    if len(new_outcomes) == 0:
        raise ValueError("cannot bootstrap zero paired items")
    diffs = [float(n) - float(o) for n, o in zip(new_outcomes, old_outcomes)]
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(n_resamples):
        resample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(resample) / n)
    means.sort()
    ci_lo = _percentile(means, 2.5)
    ci_hi = _percentile(means, 97.5)
    return BootstrapResult(delta=sum(diffs) / n, ci_lo=ci_lo, ci_hi=ci_hi)


def _percentile(sorted_values: list[float], pct: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (pct / 100.0) * (len(sorted_values) - 1)
    lo_idx, hi_idx = int(idx), min(int(idx) + 1, len(sorted_values) - 1)
    frac = idx - lo_idx
    return sorted_values[lo_idx] * (1 - frac) + sorted_values[hi_idx] * frac


class GateMode(Enum):
    SIGNIFICANT_IMPROVEMENT = "significant-improvement"
    NON_REGRESSION = "non-regression"


def gate_decision(
    result: BootstrapResult,
    mode: GateMode,
    *,
    epsilon: float = 0.0,
) -> tuple[bool, str]:
    """Decide keep/revert from the interval itself, not the point
    estimate. `epsilon` widens the non-regression floor slightly for
    noisy metrics; it defaults to zero (a strict "must not cross
    zero")."""
    if mode is GateMode.SIGNIFICANT_IMPROVEMENT:
        if result.ci_lo > 0:
            return True, f"ci_lo={result.ci_lo:+.4f} excludes zero: improvement is significant"
        return False, f"ci_lo={result.ci_lo:+.4f} does not exclude zero: not distinguishable from noise"
    if mode is GateMode.NON_REGRESSION:
        # A regression is significant only when the WHOLE interval sits
        # below the floor -- i.e. even the best-case resampled outcome
        # (ci_hi) is still a real drop. An interval that merely dips
        # below zero at ci_lo while ci_hi stays at or above the floor
        # is not significant evidence of a regression; it is evidence
        # of nothing in particular, which is what "non-regression"
        # means here.
        if result.ci_hi >= -epsilon:
            return True, f"ci_hi={result.ci_hi:+.4f} shows no significant drop (floor {-epsilon:+.4f})"
        return False, f"ci_hi={result.ci_hi:+.4f} is a significant drop below the {-epsilon:+.4f} floor"
    raise ValueError(f"unknown gate mode: {mode}")


@dataclass
class RevisionDecision:
    rev: str
    mode: GateMode
    delta: float
    ci_lo: float
    ci_hi: float
    kept: bool
    reason: str


@dataclass
class Ratchet:
    """Bookkeeping for a sequence of revision decisions, each actually
    gated by its own bootstrap interval rather than a bare point
    estimate."""

    ledger: list[RevisionDecision] = field(default_factory=list)

    def evaluate_from_outcomes(
        self,
        rev: str,
        new_outcomes: Sequence[float],
        old_outcomes: Sequence[float],
        mode: GateMode,
        *,
        n_resamples: int = 2000,
        seed: int | None = None,
        epsilon: float = 0.0,
    ) -> RevisionDecision:
        result = paired_bootstrap_delta(new_outcomes, old_outcomes, n_resamples=n_resamples, seed=seed)
        return self._record(rev, mode, result, epsilon)

    def evaluate_from_reported(
        self,
        rev: str,
        delta: float,
        ci_lo: float,
        ci_hi: float,
        mode: GateMode,
        *,
        epsilon: float = 0.0,
    ) -> RevisionDecision:
        """For when raw paired outcomes aren't available but a
        (delta, ci_lo, ci_hi) triple already was computed and reported
        elsewhere -- exactly the situation with a third party's own
        published revision ledger, where only the aggregate numbers
        survive, not the per-item data that produced them."""
        return self._record(rev, mode, BootstrapResult(delta, ci_lo, ci_hi), epsilon)

    def _record(self, rev: str, mode: GateMode, result: BootstrapResult, epsilon: float) -> RevisionDecision:
        kept, reason = gate_decision(result, mode, epsilon=epsilon)
        decision = RevisionDecision(rev, mode, result.delta, result.ci_lo, result.ci_hi, kept, reason)
        self.ledger.append(decision)
        return decision

    def to_csv_rows(self) -> list[dict]:
        return [
            {
                "rev": d.rev,
                "mode": d.mode.value,
                "delta": f"{d.delta:.4f}",
                "ci_lo": f"{d.ci_lo:.4f}",
                "ci_hi": f"{d.ci_hi:.4f}",
                "decision": "KEPT" if d.kept else "REVERTED",
                "reason": d.reason,
            }
            for d in self.ledger
        ]


def load_real_revision_ledger(csv_path: str) -> list[dict]:
    """Read the real revisions_sf100.csv columns this module cares
    about: rev, short, change, delta_correct, delta_lo, delta_hi.
    Rows with no delta (the baseline, which has nothing to compare
    against) are skipped."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("delta_correct", "") == "":
                continue
            rows.append(row)
    return rows
