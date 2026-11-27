"""Recomputes a weighted average from a stated segment breakdown plus sample
sizes, and compares it against a headline figure.

Built from a real finding: Cloudera's "The Great AI Re-Architecture" (2026)
gives a regional breakdown ("AI integration makes data governance more
complex" -- Americas 81% agree, EMEA 65%, APAC 61%) with exact sample sizes
in its own Methodology section (Americas n=800, EMEA n=400, APAC n=300). The
report's own body text states only a narrower "29% strongly agree" figure for
this question -- but independent press coverage (Campus Technology) reported
a separate "73% say..." headline for the same underlying question. Recomputing
the weighted average from the report's own regional table and sample sizes
gives 72.7%, matching the press figure almost exactly even though the report's
own prose never states it directly. The same mechanism also confirms the
report's two headline figures that ARE stated directly (72% overhaul-needed,
55% canceled-6+-projects) reconstruct cleanly from their own regional tables.

Extended from a second real finding, in a later round on three more Cloudera
ebooks: "7 Elements of a Winning Enterprise Data Strategy" (2022) claims "the
percentage of organizations that will be hybrid and multi-cloud is set to
triple (from 12% to 36%) in the next 18 months" -- a self-contained,
recomputable "before/after/claimed-multiple" statement rather than a
weighted-segment one. `check_claimed_multiple()` generalizes that check: any
document stating a before value, an after value, and a named multiplier
("triple," "doubled," "4x") can have that multiplier recomputed directly and
compared against what's claimed, the same discipline as `reconcile()` but for
a ratio instead of a weighted average. This one happened to check out exactly
(36 / 12 = 3.0) -- a credit, not a flag, and included so the mechanism isn't
only ever shown catching a problem.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationResult:
    computed: float
    stated: float | None
    delta: float | None
    matches: bool | None  # None when no stated figure was given to compare


@dataclass(frozen=True)
class MultipleCheckResult:
    computed_multiple: float
    claimed_multiple: float
    matches: bool


def check_claimed_multiple(
    before: float, after: float, claimed_multiple: float, tolerance: float = 0.05
) -> MultipleCheckResult:
    """Recomputes after/before and compares it to a stated multiplier
    ("triple" -> 3.0, "doubled" -> 2.0, "4x" -> 4.0). tolerance is a relative
    fraction (0.05 = within 5% of the claimed multiple)."""
    if before == 0:
        raise ValueError("before must be nonzero to compute a multiple")
    computed = after / before
    matches = abs(computed - claimed_multiple) <= tolerance * claimed_multiple
    return MultipleCheckResult(computed, claimed_multiple, matches)


def weighted_average(segment_values: dict[str, float], segment_weights: dict[str, int]) -> float:
    if set(segment_values) != set(segment_weights):
        raise ValueError("segment_values and segment_weights must cover the same keys")
    total_weight = sum(segment_weights.values())
    if total_weight <= 0:
        raise ValueError("total weight must be positive")
    return sum(segment_values[k] * segment_weights[k] for k in segment_values) / total_weight


def reconcile(
    segment_values: dict[str, float],
    segment_weights: dict[str, int],
    stated_headline: float | None = None,
    tolerance: float = 1.5,
) -> ReconciliationResult:
    """Recomputes the weighted average and, if a stated_headline is given,
    reports the delta and whether it's within tolerance (in percentage
    points). Pass tolerance=0 for an exact-match check."""
    computed = weighted_average(segment_values, segment_weights)
    if stated_headline is None:
        return ReconciliationResult(computed, None, None, None)
    delta = computed - stated_headline
    return ReconciliationResult(computed, stated_headline, delta, abs(delta) <= tolerance)
