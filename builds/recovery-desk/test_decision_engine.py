"""
Recovery Desk — decision engine tests.

Run with: .venv/bin/python -m pytest test_decision_engine.py -v
(or just: .venv/bin/python test_decision_engine.py — runs without pytest too)

Every synthetic scenario is asserted against the SPECIFIC branch it
claims to exercise, not just "did it return something." This is the
check that caught two real bugs during this build: the train_hard and
back_off fixtures were originally hand-picked numbers that looked
directionally right but didn't actually cross decision_engine's own
thresholds — back_off silently fell through to the TRAIN_HARD
catch-all. Fixed by recalculating the fixtures against the real
thresholds, not by loosening the thresholds to fit sloppy fixtures.
"""

from data_pipeline import synthetic_reading, SYNTHETIC_SCENARIOS
from decision_engine import decide, Decision, _recovery_score, RECOVERY_SCORE_HIGH, RECOVERY_SCORE_LOW


def test_train_hard_clears_high_threshold():
    r = synthetic_reading("train_hard")
    score = _recovery_score(r)
    assert score >= RECOVERY_SCORE_HIGH, f"train_hard fixture scores {score}, doesn't clear {RECOVERY_SCORE_HIGH}"
    result = decide(r)
    assert result.decision == Decision.TRAIN_HARD
    assert not result.is_anomaly


def test_back_off_clears_low_threshold():
    r = synthetic_reading("back_off")
    score = _recovery_score(r)
    assert score <= RECOVERY_SCORE_LOW, f"back_off fixture scores {score}, doesn't clear {RECOVERY_SCORE_LOW}"
    result = decide(r)
    assert result.decision == Decision.BACK_OFF
    assert not result.is_anomaly


def test_eat_more_is_mid_score_high_strain():
    r = synthetic_reading("eat_more")
    score = _recovery_score(r)
    assert RECOVERY_SCORE_LOW < score < RECOVERY_SCORE_HIGH, f"eat_more fixture scores {score}, should be mid-range"
    result = decide(r)
    assert result.decision == Decision.EAT_MORE
    assert not result.is_anomaly


def test_sleep_earlier_is_mid_score_low_strain_short_sleep():
    r = synthetic_reading("sleep_earlier")
    score = _recovery_score(r)
    assert RECOVERY_SCORE_LOW < score < RECOVERY_SCORE_HIGH, f"sleep_earlier fixture scores {score}, should be mid-range"
    result = decide(r)
    assert result.decision == Decision.SLEEP_EARLIER
    assert not result.is_anomaly


def test_anomaly_overrides_everything_and_never_recommends_training():
    r = synthetic_reading("anomaly")
    result = decide(r)
    assert result.decision == Decision.SEE_A_DOCTOR
    assert result.is_anomaly
    # The actual safety property: no anomaly reading should ever produce
    # a training recommendation, regardless of what the raw score is.
    assert result.decision not in (Decision.TRAIN_HARD, Decision.BACK_OFF,
                                    Decision.EAT_MORE, Decision.SLEEP_EARLIER)


def test_all_five_scenarios_exist_and_are_distinct_decisions():
    decisions = {name: decide(synthetic_reading(name)).decision for name in SYNTHETIC_SCENARIOS}
    assert len(set(decisions.values())) == 5, f"expected 5 distinct decisions, got {decisions}"


def test_anomaly_requires_all_three_signals_not_just_low_hrv():
    """A hard-training week alone (low HRV, everything else normal)
    should NOT trigger the anomaly/see-a-doctor branch — only the
    combination should. This is the over-flagging guard described in
    decision_engine._check_anomaly's docstring, verified directly."""
    from decision_engine import OvernightReading
    hard_training_only = OvernightReading(
        hrv_ms=40, hrv_baseline_ms=60,          # HRV well down, like real fatigue
        resting_hr=50, resting_hr_baseline=50,   # but RHR normal
        sleep_hours=7.0, sleep_score=75,          # and sleep normal
        respiratory_rate=14.0, respiratory_rate_baseline=14.0,
        prior_day_strain=60,
    )
    result = decide(hard_training_only)
    assert not result.is_anomaly, "low HRV alone (no RHR/resp spike, decent sleep) should not trigger anomaly"
    assert result.decision != Decision.SEE_A_DOCTOR


if __name__ == "__main__":
    import sys
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {test.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
