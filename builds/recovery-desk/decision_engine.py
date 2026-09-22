"""
Recovery Desk — decision engine.

Deliberately rules-based, not LLM-generated. The source opportunity
report's own competitive analysis notes that Whoop Coach and ChatGPT
Health both run on the same underlying model family, so "smarter text
generation" isn't the differentiator here — a trusted, explainable
decision is. A fixed rule set that always produces the same call for
the same inputs is easier to trust, cheaper to run, and has no failure
mode where a language model invents a plausible-sounding but wrong
reason. See /notes/recovery-desk-build-brief.md and
/business-brain.md's Decisions log for the reasoning behind this call.

SAFETY, NOT A STYLE CHOICE: this only ever recommends training
decisions. If the overnight data pattern looks like it could reflect
illness or a genuine health anomaly (not just normal training fatigue),
it routes to a "see a doctor" message and refuses to recommend training
of any kind that day. This is enforced in code (see `_check_anomaly`),
not left as a prompt instruction a generative step could ignore.
"""

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    TRAIN_HARD = "TRAIN_HARD"
    BACK_OFF = "BACK_OFF"
    EAT_MORE = "EAT_MORE"
    SLEEP_EARLIER = "SLEEP_EARLIER"
    SEE_A_DOCTOR = "SEE_A_DOCTOR"


DECISION_TEXT = {
    Decision.TRAIN_HARD: "Train hard today.",
    Decision.BACK_OFF: "Back off today.",
    Decision.EAT_MORE: "Eat more today.",
    Decision.SLEEP_EARLIER: "Sleep earlier tonight.",
    Decision.SEE_A_DOCTOR: (
        "Your overnight data looks unusual, not just tired. "
        "Skip training today and check in with a doctor if it "
        "doesn't look normal by tomorrow."
    ),
}


@dataclass
class OvernightReading:
    """One night's data, already normalized to the same shape regardless
    of source (Oura vs. Whoop) — see data_pipeline.py for the adapter
    that produces this from each provider's actual API response."""
    hrv_ms: float
    hrv_baseline_ms: float           # trailing 14-day rolling average
    resting_hr: float
    resting_hr_baseline: float       # trailing 14-day rolling average
    sleep_hours: float
    sleep_score: float               # 0-100, provider-normalized
    respiratory_rate: float
    respiratory_rate_baseline: float
    prior_day_strain: float          # 0-100, provider-normalized


@dataclass
class DecisionResult:
    decision: Decision
    text: str
    reason: str                      # the one-line "why"
    is_anomaly: bool


# ── Thresholds — named constants, not magic numbers, so the actual
# decision logic below reads as a sequence of real judgment calls. ──

HRV_ANOMALY_DROP_PCT = 0.30          # HRV this far below baseline...
RHR_ANOMALY_RISE_PCT = 0.15          # ...combined with RHR this far above...
RESP_RATE_ANOMALY_RISE_PCT = 0.15    # ...or respiratory rate this far above baseline
SLEEP_SCORE_ANOMALY_MAX = 55         # ...and sleep this poor -> anomaly, not fatigue

RECOVERY_SCORE_HIGH = 67             # >= this -> train hard territory
RECOVERY_SCORE_LOW = 34              # <= this -> back off territory
HIGH_STRAIN_THRESHOLD = 70           # prior day strain this high -> eat-more candidate
LOW_SLEEP_HOURS_THRESHOLD = 6.5      # sleep this short -> sleep-earlier candidate


def _pct_delta(value: float, baseline: float) -> float:
    """Positive = above baseline, negative = below. Guards baseline<=0."""
    if baseline <= 0:
        return 0.0
    return (value - baseline) / baseline


def _check_anomaly(r: OvernightReading) -> bool:
    """
    Illness/anomaly pattern, not ordinary training fatigue: HRV
    substantially depressed AND (elevated resting HR OR elevated
    respiratory rate) AND poor sleep. Ordinary hard-training fatigue
    usually depresses HRV alone without this combination — requiring
    multiple simultaneous signals is deliberate, to avoid over-flagging
    a normal hard-training week as a medical concern.
    """
    hrv_drop = _pct_delta(r.hrv_ms, r.hrv_baseline_ms) <= -HRV_ANOMALY_DROP_PCT
    rhr_spike = _pct_delta(r.resting_hr, r.resting_hr_baseline) >= RHR_ANOMALY_RISE_PCT
    resp_spike = (
        _pct_delta(r.respiratory_rate, r.respiratory_rate_baseline)
        >= RESP_RATE_ANOMALY_RISE_PCT
    )
    poor_sleep = r.sleep_score <= SLEEP_SCORE_ANOMALY_MAX
    return hrv_drop and (rhr_spike or resp_spike) and poor_sleep


def _recovery_score(r: OvernightReading) -> float:
    """
    0-100 composite: HRV-vs-baseline and RHR-vs-baseline each contribute
    up to 40 points, sleep score contributes up to 20 — HRV is weighted
    most heavily because it's the most training-relevant signal among
    the three, RHR second, sleep score last since it's already a
    provider-computed composite rather than a raw signal.
    """
    hrv_component = max(0.0, min(1.0, 0.5 + _pct_delta(r.hrv_ms, r.hrv_baseline_ms))) * 40
    rhr_component = max(0.0, min(1.0, 0.5 - _pct_delta(r.resting_hr, r.resting_hr_baseline))) * 40
    sleep_component = (r.sleep_score / 100) * 20
    return round(hrv_component + rhr_component + sleep_component, 1)


def decide(r: OvernightReading) -> DecisionResult:
    """The one call this whole product exists to make."""
    if _check_anomaly(r):
        return DecisionResult(
            decision=Decision.SEE_A_DOCTOR,
            text=DECISION_TEXT[Decision.SEE_A_DOCTOR],
            reason=(
                f"HRV is {abs(_pct_delta(r.hrv_ms, r.hrv_baseline_ms)):.0%} "
                f"below your baseline alongside an elevated resting HR/"
                f"breathing rate and poor sleep — that combination looks "
                f"more like illness than training fatigue."
            ),
            is_anomaly=True,
        )

    score = _recovery_score(r)

    if score >= RECOVERY_SCORE_HIGH and r.sleep_hours >= LOW_SLEEP_HOURS_THRESHOLD:
        return DecisionResult(
            decision=Decision.TRAIN_HARD,
            text=DECISION_TEXT[Decision.TRAIN_HARD],
            reason=f"Recovery score {score}/100 — HRV and resting HR are both in your normal range.",
            is_anomaly=False,
        )

    if score <= RECOVERY_SCORE_LOW:
        return DecisionResult(
            decision=Decision.BACK_OFF,
            text=DECISION_TEXT[Decision.BACK_OFF],
            reason=f"Recovery score {score}/100 — your body hasn't caught up yet.",
            is_anomaly=False,
        )

    if r.prior_day_strain >= HIGH_STRAIN_THRESHOLD:
        return DecisionResult(
            decision=Decision.EAT_MORE,
            text=DECISION_TEXT[Decision.EAT_MORE],
            reason=f"Yesterday's training load was high (strain {r.prior_day_strain:.0f}) — refuel before you go again.",
            is_anomaly=False,
        )

    if r.sleep_hours < LOW_SLEEP_HOURS_THRESHOLD:
        return DecisionResult(
            decision=Decision.SLEEP_EARLIER,
            text=DECISION_TEXT[Decision.SLEEP_EARLIER],
            reason=f"Only {r.sleep_hours:.1f}h last night — recovery is fine today, but that catches up.",
            is_anomaly=False,
        )

    return DecisionResult(
        decision=Decision.TRAIN_HARD,
        text=DECISION_TEXT[Decision.TRAIN_HARD],
        reason=f"Recovery score {score}/100 — nothing here says hold back.",
        is_anomaly=False,
    )
