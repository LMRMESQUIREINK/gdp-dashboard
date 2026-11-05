import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bootstrap_ratchet import (
    GateMode,
    Ratchet,
    gate_decision,
    load_real_revision_ledger,
    paired_bootstrap_delta,
)

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_LEDGER_CSV = os.path.join(HERE, "tests", "real_revisions_sf100.csv")


class TestPairedBootstrapDeltaCorrectness(unittest.TestCase):
    def test_identical_outcomes_give_zero_delta_and_zero_width_interval(self):
        outcomes = [1.0, 0.0, 1.0, 1.0, 0.0] * 10
        result = paired_bootstrap_delta(outcomes, outcomes, seed=1)
        self.assertEqual(result.delta, 0.0)
        self.assertEqual(result.ci_lo, 0.0)
        self.assertEqual(result.ci_hi, 0.0)

    def test_every_item_flips_from_wrong_to_right_gives_delta_one(self):
        new = [1.0] * 20
        old = [0.0] * 20
        result = paired_bootstrap_delta(new, old, seed=2)
        self.assertEqual(result.delta, 1.0)
        self.assertEqual(result.ci_lo, 1.0)
        self.assertEqual(result.ci_hi, 1.0)

    def test_mismatched_lengths_rejected(self):
        with self.assertRaises(ValueError):
            paired_bootstrap_delta([1.0, 0.0], [1.0])

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            paired_bootstrap_delta([], [])

    def test_same_seed_is_deterministic(self):
        new = [1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
        old = [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0]
        a = paired_bootstrap_delta(new, old, seed=42)
        b = paired_bootstrap_delta(new, old, seed=42)
        self.assertEqual(a, b)

    def test_different_seeds_can_give_different_intervals(self):
        new = [1.0, 0.0] * 10
        old = [0.0, 0.0] * 10
        a = paired_bootstrap_delta(new, old, seed=1, n_resamples=200)
        b = paired_bootstrap_delta(new, old, seed=2, n_resamples=200)
        self.assertEqual(a.delta, b.delta)  # point estimate never depends on resampling
        # the resampled interval itself is allowed to differ slightly between seeds


class TestDiscrimination(unittest.TestCase):
    """The property that actually matters: a real improvement produces
    an interval that excludes zero, and pure noise does not -- proven
    against a dev-set-sized (102 item) synthetic sample, matching the
    real article's own development set size."""

    def test_real_injected_improvement_excludes_zero(self):
        rng = random.Random(7)
        n = 102
        old = [1.0 if rng.random() < 0.60 else 0.0 for _ in range(n)]
        # 15% of the still-wrong items flip to right under "new" -- a real signal.
        new = list(old)
        wrong_idx = [i for i, v in enumerate(old) if v == 0.0]
        for i in rng.sample(wrong_idx, k=max(1, int(0.5 * len(wrong_idx)))):
            new[i] = 1.0
        result = paired_bootstrap_delta(new, old, seed=99)
        self.assertGreater(result.delta, 0)
        self.assertGreater(result.ci_lo, 0, "a real injected improvement should exclude zero")

    def test_pure_noise_includes_zero(self):
        rng = random.Random(11)
        n = 102
        old = [1.0 if rng.random() < 0.70 else 0.0 for _ in range(n)]
        # "new" is an independent random re-draw at the SAME rate -- no real improvement.
        new = [1.0 if rng.random() < 0.70 else 0.0 for _ in range(n)]
        result = paired_bootstrap_delta(new, old, seed=13)
        self.assertLessEqual(result.ci_lo, 0)
        self.assertGreaterEqual(result.ci_hi, 0, "pure noise should not exclude zero in either direction")


class TestGateDecision(unittest.TestCase):
    def test_significant_improvement_mode_requires_ci_lo_above_zero(self):
        from bootstrap_ratchet import BootstrapResult

        kept, _ = gate_decision(BootstrapResult(0.05, 0.01, 0.09), GateMode.SIGNIFICANT_IMPROVEMENT)
        self.assertTrue(kept)
        kept, _ = gate_decision(BootstrapResult(0.05, -0.01, 0.09), GateMode.SIGNIFICANT_IMPROVEMENT)
        self.assertFalse(kept, "a positive point estimate with a CI touching zero must not pass this gate")
        kept, _ = gate_decision(BootstrapResult(0.05, 0.0, 0.09), GateMode.SIGNIFICANT_IMPROVEMENT)
        self.assertFalse(kept, "ci_lo exactly at zero does not exclude zero")

    def test_non_regression_mode_tolerates_a_ci_that_straddles_zero(self):
        from bootstrap_ratchet import BootstrapResult

        # ci_lo dips negative but ci_hi stays positive -- not confident
        # evidence of a drop (or of an improvement), so non-regression holds.
        kept, _ = gate_decision(BootstrapResult(0.02, -0.01, 0.06), GateMode.NON_REGRESSION)
        self.assertTrue(kept, "an interval straddling zero is not significant evidence of a drop")
        # ci_hi itself is still negative -- the WHOLE interval is below zero,
        # which is confident evidence of a real regression.
        kept, _ = gate_decision(BootstrapResult(-0.10, -0.20, -0.02), GateMode.NON_REGRESSION)
        self.assertFalse(kept, "a CI entirely below zero is a real, significant drop")

    def test_non_regression_epsilon_widens_the_floor(self):
        from bootstrap_ratchet import BootstrapResult

        # ci_hi is -0.02: a whole interval just barely below zero.
        result = BootstrapResult(-0.03, -0.08, -0.02)
        kept, _ = gate_decision(result, GateMode.NON_REGRESSION, epsilon=0.0)
        self.assertFalse(kept, "with no tolerance, a ci_hi below zero is a significant drop")
        kept, _ = gate_decision(result, GateMode.NON_REGRESSION, epsilon=0.05)
        self.assertTrue(kept, "a wider floor tolerates this small a drop")


class TestRatchetBookkeeping(unittest.TestCase):
    def test_evaluate_from_outcomes_records_a_decision(self):
        ratchet = Ratchet()
        new = [1.0] * 20
        old = [0.0] * 20
        decision = ratchet.evaluate_from_outcomes("r_test", new, old, GateMode.SIGNIFICANT_IMPROVEMENT, seed=1)
        self.assertTrue(decision.kept)
        self.assertEqual(len(ratchet.ledger), 1)
        rows = ratchet.to_csv_rows()
        self.assertEqual(rows[0]["rev"], "r_test")
        self.assertEqual(rows[0]["decision"], "KEPT")


class TestAgainstTheRealArticleLedger(unittest.TestCase):
    """The actual point of this build: replay the real, third-party
    revisions_sf100.csv (copied from the MIT-licensed
    FareedKhan-dev/agentic-warehouse-analyst repo, see
    /notes/agentic-warehouse-analyst-analysis.md) through a gate that
    actually enforces the confidence interval their own code computes
    but never checks."""

    def setUp(self):
        self.rows = load_real_revision_ledger(REAL_LEDGER_CSV)
        self.assertTrue(self.rows, "the real revision ledger fixture must be present and non-empty")

    def test_fixture_matches_the_real_repos_kept_reverted_calls(self):
        # Sanity check that the copied fixture is unmodified: reproduce
        # the real repo's own decision column exactly before doing
        # anything else with it.
        by_rev = {r["rev"]: r for r in self.rows}
        self.assertEqual(by_rev["r01"]["decision"], "KEPT")
        self.assertEqual(by_rev["r03"]["decision"], "REVERTED")
        self.assertEqual(by_rev["r04"]["decision"], "REVERTED")
        self.assertEqual(by_rev["r09"]["decision"], "KEPT")
        self.assertEqual(by_rev["r13"]["decision"], "REVERTED")

    def test_strict_significance_gate_on_clear_accuracy_claims(self):
        # Revisions whose own stated change is an accuracy claim, and
        # whose real reported interval clearly excludes zero: the
        # strict gate should agree with the real repo's own KEPT calls.
        clear_accuracy_claims = {"r01", "r02", "r06", "r12"}
        ratchet = Ratchet()
        results = {}
        for row in self.rows:
            if row["rev"] not in clear_accuracy_claims:
                continue
            d = ratchet.evaluate_from_reported(
                row["rev"], float(row["delta_correct"]), float(row["delta_lo"]), float(row["delta_hi"]),
                GateMode.SIGNIFICANT_IMPROVEMENT,
            )
            results[row["rev"]] = d
        for rev, d in results.items():
            self.assertTrue(d.kept, f"{rev} should pass the strict gate: {d.reason}")

    def test_r05_sits_exactly_on_the_zero_boundary(self):
        # A second, more granular instance of the same phenomenon the
        # analysis found for r09, surfaced by actually building and
        # running the gate rather than reading the CSV by eye: r05
        # ("repair=2") was KEPT in the real repo with
        # delta_lo == 0.0 EXACTLY -- the interval touches zero but
        # does not exclude it. A strict significance gate correctly
        # refuses to call this "significant," which is the honest
        # answer: this revision's accuracy gain is not statistically
        # distinguishable from noise at 95% confidence, even though
        # its point estimate (+2.9%) looks like a real improvement.
        row = next(r for r in self.rows if r["rev"] == "r05")
        delta, lo, hi = float(row["delta_correct"]), float(row["delta_lo"]), float(row["delta_hi"])
        self.assertEqual(lo, 0.0, "confirms the real reported lower bound is exactly zero")
        decision = gate_decision(_result(delta, lo, hi), GateMode.SIGNIFICANT_IMPROVEMENT)
        self.assertFalse(decision[0], "a lower bound of exactly zero does not exclude zero")

    def test_r09_fails_the_strict_accuracy_gate_but_passes_non_regression(self):
        # The exact finding from the analysis: r09 ("sorted copy +
        # rollups") was KEPT in the real repo with an accuracy CI of
        # roughly [-0.0098, +0.0686] -- it includes zero, so a strict
        # accuracy-only significance gate would NOT keep it on that
        # basis alone. Its real justification was a latency
        # improvement with accuracy merely not regressing, which is
        # exactly what the non-regression mode is for.
        row = next(r for r in self.rows if r["rev"] == "r09")
        delta, lo, hi = float(row["delta_correct"]), float(row["delta_lo"]), float(row["delta_hi"])
        self.assertLess(lo, 0, "confirms the real reported interval does include zero")

        strict = Ratchet()
        strict_decision = strict.evaluate_from_reported("r09", delta, lo, hi, GateMode.SIGNIFICANT_IMPROVEMENT)
        self.assertFalse(strict_decision.kept, "accuracy alone does not significantly improve here")

        lenient = Ratchet()
        lenient_decision = lenient.evaluate_from_reported("r09", delta, lo, hi, GateMode.NON_REGRESSION)
        self.assertTrue(lenient_decision.kept, "but accuracy also did not significantly regress")

    def test_r13_and_r15_fail_the_strict_gate_but_are_not_confirmed_regressions(self):
        # Both were REVERTED in the real repo because their point-
        # estimate utility was lower than the best-so-far -- the real
        # repo's own keep_if is point-estimate-only (the finding this
        # build exists to fix), not because the interval showed a
        # significant drop. Checked precisely: both report
        # delta_hi == 0.0 exactly. A strict significance gate correctly
        # refuses these (they don't improve), but the honest reading of
        # ci_hi touching exactly zero is "not significant evidence of
        # an improvement" -- NOT "confirmed evidence of a regression."
        # Forcing the non-regression gate to also reject these would be
        # overclaiming beyond what the reported interval actually shows.
        for rev in ("r13", "r15"):
            row = next(r for r in self.rows if r["rev"] == rev)
            delta, lo, hi = float(row["delta_correct"]), float(row["delta_lo"]), float(row["delta_hi"])
            self.assertEqual(hi, 0.0, f"{rev}: confirms the real reported upper bound is exactly zero")
            d_strict = gate_decision(_result(delta, lo, hi), GateMode.SIGNIFICANT_IMPROVEMENT)
            d_lenient = gate_decision(_result(delta, lo, hi), GateMode.NON_REGRESSION)
            self.assertFalse(d_strict[0], f"{rev} should fail the strict gate")
            self.assertTrue(d_lenient[0], f"{rev}: ci_hi=0.0 is not significant evidence of a regression")


def _result(delta, lo, hi):
    from bootstrap_ratchet import BootstrapResult
    return BootstrapResult(delta, lo, hi)


if __name__ == "__main__":
    unittest.main(verbosity=2)
