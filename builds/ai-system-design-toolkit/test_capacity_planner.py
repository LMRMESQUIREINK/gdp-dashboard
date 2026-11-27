import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capacity_planner import CapacityPlan, Workload, plan_capacity

HERE = os.path.dirname(os.path.abspath(__file__))


def northstar_workload():
    # Exactly the source article's Section 3 Northstar assumptions.
    return Workload(
        users=5000,
        requests_per_user_per_day=4,
        working_hours_per_day=8,
        working_days_per_month=22,
        peak_multiplier=8,
        avg_input_tokens_per_request=1200,
        avg_output_tokens_per_request=300,
        price_per_million_input_tokens=0.50,
        price_per_million_output_tokens=2.00,
    )


class TestReproducesArticleNumbers(unittest.TestCase):
    """Every one of these matches a number independently recomputed by
    hand before this module was written (see
    /notes/ai-system-design-guide-analysis.md) -- this test locks that
    recompute in as regression coverage."""

    def setUp(self):
        self.plan = plan_capacity(northstar_workload())

    def test_daily_requests(self):
        self.assertEqual(self.plan.daily_requests, 20000)

    def test_avg_rps_matches_article_rounding(self):
        self.assertAlmostEqual(self.plan.avg_requests_per_second, 0.6944, places=4)

    def test_peak_rps_uses_exact_fraction_not_articles_rounded_intermediate(self):
        # The article computes peak as 0.69 (already rounded) x 8 = 5.52.
        # This module carries full precision throughout, so it correctly
        # gets 5.5556, not 5.52 -- the real finding from this round's
        # analysis: the article's own intermediate rounding shifts its
        # answer by about 0.7%. Both round to "approximately 5.5", which
        # is why the article's own prose conclusion still holds even
        # though its exact figure doesn't match a full-precision redo.
        self.assertAlmostEqual(self.plan.peak_requests_per_second, 5.5556, places=3)
        rounded_intermediate = round(self.plan.avg_requests_per_second, 2) * 8
        self.assertAlmostEqual(rounded_intermediate, 5.52, places=2)
        self.assertNotAlmostEqual(self.plan.peak_requests_per_second, rounded_intermediate, places=2)

    def test_daily_tokens(self):
        self.assertEqual(self.plan.daily_input_tokens, 24_000_000)
        self.assertEqual(self.plan.daily_output_tokens, 6_000_000)
        self.assertEqual(self.plan.daily_total_tokens, 30_000_000)

    def test_monthly_tokens(self):
        self.assertEqual(self.plan.monthly_input_tokens, 528_000_000)
        self.assertEqual(self.plan.monthly_output_tokens, 132_000_000)
        self.assertEqual(self.plan.monthly_total_tokens, 660_000_000)

    def test_monthly_cost(self):
        self.assertAlmostEqual(self.plan.monthly_input_cost, 264.0, places=2)
        self.assertAlmostEqual(self.plan.monthly_output_cost, 264.0, places=2)
        self.assertAlmostEqual(self.plan.monthly_total_cost, 528.0, places=2)

    def test_littles_law_separate_illustrative_example(self):
        # The article's Little's Law worked example uses its own separate
        # hypothetical (lambda=6, W=2 -> L=12), not Northstar's avg_rps.
        # Reproduce that exact example directly against the formula.
        self.assertEqual(self.plan.concurrency(0) , 0)  # sanity: zero time in system -> zero concurrency
        # Build a plan whose avg_rps is exactly 6 to replicate the article's L=12 example.
        six_rps_workload = Workload(
            users=6 * 3600, requests_per_user_per_day=1, working_hours_per_day=1,
            working_days_per_month=22, peak_multiplier=1,
            avg_input_tokens_per_request=0, avg_output_tokens_per_request=0,
            price_per_million_input_tokens=0, price_per_million_output_tokens=0,
        )
        six_rps_plan = plan_capacity(six_rps_workload)
        self.assertAlmostEqual(six_rps_plan.avg_requests_per_second, 6.0, places=6)
        self.assertAlmostEqual(six_rps_plan.concurrency(2.0), 12.0, places=6)


class TestWorkloadValidation(unittest.TestCase):
    def test_negative_field_rejected(self):
        with self.assertRaises(ValueError):
            Workload(
                users=100, requests_per_user_per_day=-1, working_hours_per_day=8,
                working_days_per_month=22, peak_multiplier=8,
                avg_input_tokens_per_request=100, avg_output_tokens_per_request=50,
                price_per_million_input_tokens=0.5, price_per_million_output_tokens=2.0,
            )

    def test_zero_users_rejected(self):
        with self.assertRaises(ValueError):
            Workload(
                users=0, requests_per_user_per_day=4, working_hours_per_day=8,
                working_days_per_month=22, peak_multiplier=8,
                avg_input_tokens_per_request=100, avg_output_tokens_per_request=50,
                price_per_million_input_tokens=0.5, price_per_million_output_tokens=2.0,
            )

    def test_zero_working_hours_rejected(self):
        with self.assertRaises(ValueError):
            Workload(
                users=100, requests_per_user_per_day=4, working_hours_per_day=0,
                working_days_per_month=22, peak_multiplier=8,
                avg_input_tokens_per_request=100, avg_output_tokens_per_request=50,
                price_per_million_input_tokens=0.5, price_per_million_output_tokens=2.0,
            )

    def test_negative_concurrency_time_rejected(self):
        plan = plan_capacity(northstar_workload())
        with self.assertRaises(ValueError):
            plan.concurrency(-1)


class TestRealCliSubprocess(unittest.TestCase):
    """Real subprocess calls, not direct function calls -- proving the
    CLI wiring itself, same discipline as every other CLI build in this
    project."""

    def test_cli_reproduces_article_numbers(self):
        result = subprocess.run(
            [
                sys.executable, os.path.join(HERE, "capacity_planner.py"),
                "--users", "5000", "--requests-per-user-per-day", "4",
                "--avg-input-tokens", "1200", "--avg-output-tokens", "300",
                "--price-per-million-input", "0.50", "--price-per-million-output", "2.00",
                "--concurrency-avg-seconds", "2",
            ],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Daily requests:        20,000", result.stdout)
        self.assertIn("$528.00", result.stdout)
        self.assertIn("Little's Law concurrency", result.stdout)

    def test_cli_rejects_invalid_workload_cleanly(self):
        result = subprocess.run(
            [
                sys.executable, os.path.join(HERE, "capacity_planner.py"),
                "--users", "0", "--requests-per-user-per-day", "4",
                "--avg-input-tokens", "100", "--avg-output-tokens", "50",
                "--price-per-million-input", "0.5", "--price-per-million-output", "2.0",
            ],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid workload", result.stdout)

    def test_cli_missing_required_flag_gives_argparse_error(self):
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "capacity_planner.py"), "--users", "100"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stderr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
