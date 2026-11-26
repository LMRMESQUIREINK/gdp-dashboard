import unittest

from breakdown_reconciler import weighted_average, reconcile


# Real sample sizes from "The Great AI Re-Architecture"'s own Methodology
# section: Americas (US 600 + Canada 100 + Brazil 100 = 800), EMEA
# (S. Africa 100 + Spain 100 + UK 200 = 400), APAC (Singapore 100 + India 100
# + Japan 100 = 300). Total n=1500, matching the report's own stated total.
REAL_WEIGHTS = {"AMER": 800, "EMEA": 400, "APAC": 300}


class TestRealReportFiguresReconcileCleanly(unittest.TestCase):
    """The report's own two headline figures that ARE stated directly in its
    body text reconstruct almost exactly from its own regional breakdown."""

    def test_overhaul_needed_72_percent(self):
        values = {"AMER": 70, "EMEA": 81, "APAC": 68}
        result = reconcile(values, REAL_WEIGHTS, stated_headline=72)
        self.assertAlmostEqual(result.computed, 72.53, places=2)
        self.assertTrue(result.matches)

    def test_six_plus_projects_canceled_55_percent(self):
        values = {"AMER": 54, "EMEA": 60, "APAC": 50}
        result = reconcile(values, REAL_WEIGHTS, stated_headline=55)
        self.assertAlmostEqual(result.computed, 54.8, places=1)
        self.assertTrue(result.matches)


class TestRealFinding_UnstatedGovernanceFigure(unittest.TestCase):
    """The round's central finding: recomputing the weighted average of the
    report's own regional "agree" breakdown for data-governance complexity
    (AMER 81%, EMEA 65%, APAC 61%) gives 72.7% -- matching a "73%" figure
    independent press (Campus Technology) reported for this same question,
    even though the report's own body text never states that rolled-up
    number directly. It only states a narrower "29% strongly agree" figure
    for the same question, which is NOT the same metric and correctly fails
    to reconcile against the regional "agree" breakdown."""

    def setUp(self):
        self.values = {"AMER": 81, "EMEA": 65, "APAC": 61}

    def test_recomputed_figure_matches_the_press_reported_73_percent(self):
        result = reconcile(self.values, REAL_WEIGHTS, stated_headline=73)
        self.assertAlmostEqual(result.computed, 72.73, places=2)
        self.assertTrue(result.matches)

    def test_recomputed_figure_does_not_match_the_reports_own_stated_29_percent(self):
        # Correctly fails: "29% strongly agree" is a different, narrower
        # question than "% who agree" -- this is not a reconciliation bug,
        # it's proof the tool can tell these apart rather than forcing a
        # match against the wrong headline.
        result = reconcile(self.values, REAL_WEIGHTS, stated_headline=29)
        self.assertFalse(result.matches)
        self.assertGreater(abs(result.delta), 40)

    def test_with_no_stated_headline_just_reports_the_computed_value(self):
        result = reconcile(self.values, REAL_WEIGHTS)
        self.assertAlmostEqual(result.computed, 72.73, places=2)
        self.assertIsNone(result.stated)
        self.assertIsNone(result.delta)
        self.assertIsNone(result.matches)


class TestDiscrimination(unittest.TestCase):
    def test_exact_match_at_zero_tolerance(self):
        values = {"A": 50, "B": 50}
        weights = {"A": 1, "B": 1}
        result = reconcile(values, weights, stated_headline=50, tolerance=0)
        self.assertEqual(result.computed, 50)
        self.assertTrue(result.matches)

    def test_mismatch_is_reported_not_hidden(self):
        values = {"A": 10, "B": 90}
        weights = {"A": 1, "B": 1}
        result = reconcile(values, weights, stated_headline=10, tolerance=1)
        self.assertAlmostEqual(result.computed, 50.0)
        self.assertFalse(result.matches)
        self.assertAlmostEqual(result.delta, 40.0)

    def test_mismatched_keys_raise(self):
        with self.assertRaises(ValueError):
            weighted_average({"A": 1}, {"B": 1})

    def test_zero_total_weight_raises(self):
        with self.assertRaises(ValueError):
            weighted_average({"A": 1}, {"A": 0})


if __name__ == "__main__":
    unittest.main()
