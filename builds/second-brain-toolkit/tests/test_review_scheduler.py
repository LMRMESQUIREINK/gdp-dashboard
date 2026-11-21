import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from review_scheduler import (
    DEFAULT_INTERVALS,
    SavedItem,
    compare_first_review_lag,
    days_until_due,
    is_overdue,
    next_review_due,
    next_sunday_on_or_after,
    weekly_batch_lag_days,
    weekly_lag_profile,
)


class TestNextReviewDue(unittest.TestCase):
    def test_first_interval_from_save_date(self):
        item = SavedItem("x", date(2027, 1, 4))
        self.assertEqual(next_review_due(item), date(2027, 1, 5))  # +1 day

    def test_advances_after_each_completed_review(self):
        item = SavedItem("x", date(2027, 1, 4), reviews=[date(2027, 1, 5)])
        self.assertEqual(next_review_due(item), date(2027, 1, 7))  # +3 days

    def test_graduates_past_schedule(self):
        item = SavedItem(
            "x",
            date(2027, 1, 4),
            reviews=[date(2027, 1, 5), date(2027, 1, 7), date(2027, 1, 11), date(2027, 1, 18), date(2027, 2, 3)],
        )
        self.assertIsNone(next_review_due(item))

    def test_custom_intervals_respected(self):
        item = SavedItem("x", date(2027, 1, 4))
        self.assertEqual(next_review_due(item, intervals=(2, 9)), date(2027, 1, 6))


class TestOverdueAndDaysUntil(unittest.TestCase):
    def test_overdue_true_when_past_due_date(self):
        item = SavedItem("x", date(2027, 1, 4))
        self.assertTrue(is_overdue(item, today=date(2027, 1, 10)))

    def test_not_overdue_on_due_date_itself(self):
        item = SavedItem("x", date(2027, 1, 4))
        self.assertFalse(is_overdue(item, today=date(2027, 1, 5)))

    def test_graduated_item_never_overdue(self):
        item = SavedItem(
            "x",
            date(2027, 1, 4),
            reviews=[date(2027, 1, 5), date(2027, 1, 7), date(2027, 1, 11), date(2027, 1, 18), date(2027, 2, 3)],
        )
        self.assertFalse(is_overdue(item, today=date(2030, 1, 1)))

    def test_days_until_due_positive_before_due(self):
        item = SavedItem("x", date(2027, 1, 4))
        self.assertEqual(days_until_due(item, today=date(2027, 1, 4)), 1)

    def test_days_until_due_none_once_graduated(self):
        item = SavedItem(
            "x",
            date(2027, 1, 4),
            reviews=[date(2027, 1, 5), date(2027, 1, 7), date(2027, 1, 11), date(2027, 1, 18), date(2027, 2, 3)],
        )
        self.assertIsNone(days_until_due(item, today=date(2027, 2, 10)))


class TestWeeklyBatchCadence(unittest.TestCase):
    def test_sunday_itself_lags_zero(self):
        sunday = date(2027, 1, 10)
        self.assertEqual(sunday.weekday(), 6)
        self.assertEqual(next_sunday_on_or_after(sunday), sunday)
        self.assertEqual(weekly_batch_lag_days(sunday), 0)

    def test_monday_lags_six_days_to_next_sunday(self):
        monday = date(2027, 1, 4)
        self.assertEqual(monday.weekday(), 0)
        self.assertEqual(next_sunday_on_or_after(monday), date(2027, 1, 10))
        self.assertEqual(weekly_batch_lag_days(monday), 6)

    def test_saturday_lags_one_day(self):
        saturday = date(2027, 1, 9)
        self.assertEqual(saturday.weekday(), 5)
        self.assertEqual(weekly_batch_lag_days(saturday), 1)


class TestRealComputedLagFinding(unittest.TestCase):
    """The actual finding from the analysis: recomputed here, not asserted."""

    def test_monday_save_lags_five_days_behind_expanding_schedule(self):
        result = compare_first_review_lag(date(2027, 1, 4))  # a Monday
        self.assertEqual(result["expanding_first_review_lag_days"], 1)
        self.assertEqual(result["weekly_batch_first_review_lag_days"], 6)
        self.assertEqual(result["extra_delay_days"], 5)

    def test_saturday_save_is_close_to_expanding_schedule(self):
        result = compare_first_review_lag(date(2027, 1, 9))  # a Saturday
        self.assertEqual(result["weekly_batch_first_review_lag_days"], 1)
        self.assertEqual(result["extra_delay_days"], 0)

    def test_weekly_lag_profile_worst_and_average_case(self):
        profile = weekly_lag_profile()
        self.assertEqual(len(profile["per_weekday"]), 7)
        # Mon..Sun extra delays, recomputed directly: [5, 4, 3, 2, 1, 0, -1]
        self.assertEqual(profile["worst_case_extra_delay_days"], 5)
        self.assertEqual(profile["best_case_extra_delay_days"], -1)
        expected_avg = (5 + 4 + 3 + 2 + 1 + 0 - 1) / 7
        self.assertAlmostEqual(profile["average_extra_delay_days"], expected_avg)

    def test_default_intervals_match_sourced_schedule(self):
        self.assertEqual(DEFAULT_INTERVALS, (1, 3, 7, 14, 30))


if __name__ == "__main__":
    unittest.main(verbosity=2)
