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
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationResult:
    computed: float
    stated: float | None
    delta: float | None
    matches: bool | None  # None when no stated figure was given to compare


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
