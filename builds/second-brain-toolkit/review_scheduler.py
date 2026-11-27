"""
Per-item spaced review scheduling, built to check a real tension in the
source article ("How to build a second brain with NotebookLM," Hamza
Khalid/Frank Andrade): the article justifies urgency with Ebbinghaus's
forgetting curve (decay is fastest in the first hours/days) but then
prescribes a flat weekly batch review ("every Sunday, add what you saved
that week") with no per-item spacing at all.

DEFAULT_INTERVALS is a commonly-cited expanding review schedule (1, 3, 7,
14, 30 days) -- sourced from multiple independent spaced-repetition guides,
distinct from SM-2's ease-factor-driven schedule (1, 6, ~15 days) and from
the Leitner box system (box-driven, not day-driven). Stated honestly: there
is no single proven-optimal interval set -- Karpicke & Roediger (2007) found
equally-spaced retrieval beat expanding retrieval on recall after two days
in at least one study. DEFAULT_INTERVALS is offered as a reasonable,
well-documented default, not as the one correct answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

DEFAULT_INTERVALS = (1, 3, 7, 14, 30)


@dataclass
class SavedItem:
    title: str
    saved_on: date
    reviews: list[date] = field(default_factory=list)


def next_review_due(
    item: SavedItem, intervals: tuple[int, ...] = DEFAULT_INTERVALS
) -> date | None:
    """The next date this item is due for review, or None once it has
    graduated past every interval in the schedule."""
    completed = len(item.reviews)
    if completed >= len(intervals):
        return None
    return item.saved_on + timedelta(days=intervals[completed])


def is_overdue(item: SavedItem, today: date, intervals: tuple[int, ...] = DEFAULT_INTERVALS) -> bool:
    due = next_review_due(item, intervals)
    return due is not None and due < today


def days_until_due(item: SavedItem, today: date, intervals: tuple[int, ...] = DEFAULT_INTERVALS) -> int | None:
    due = next_review_due(item, intervals)
    if due is None:
        return None
    return (due - today).days


def next_sunday_on_or_after(d: date) -> date:
    """The article's own cadence: 'every Sunday, add what you saved that
    week.' Monday=0 .. Sunday=6 in date.weekday()."""
    lag = (6 - d.weekday()) % 7
    return d + timedelta(days=lag)


def weekly_batch_lag_days(saved_on: date) -> int:
    """How many days after saving, under the article's own flat weekly-
    Sunday cadence, the item first gets reviewed."""
    return (next_sunday_on_or_after(saved_on) - saved_on).days


def compare_first_review_lag(saved_on: date, intervals: tuple[int, ...] = DEFAULT_INTERVALS) -> dict:
    """Real, computed comparison of the two cadences' FIRST review point
    for one item, in days-after-saving. This is the concrete number behind
    the finding: a flat weekly cadence delays the first review relative to
    an expanding schedule, and by how much depends entirely on which day
    of the week the item happened to be saved."""
    expanding_first = intervals[0]
    weekly_first = weekly_batch_lag_days(saved_on)
    return {
        "saved_on_weekday": saved_on.strftime("%A"),
        "expanding_first_review_lag_days": expanding_first,
        "weekly_batch_first_review_lag_days": weekly_first,
        "extra_delay_days": weekly_first - expanding_first,
    }


def weekly_lag_profile(intervals: tuple[int, ...] = DEFAULT_INTERVALS) -> dict:
    """The same comparison recomputed across all 7 possible save-weekdays
    (a fixed reference Monday-start week), giving the worst-case and
    average extra delay a flat weekly cadence adds versus the expanding
    schedule's first checkpoint -- not asserted, actually recomputed."""
    monday = date(2027, 1, 4)  # a real Monday, arbitrary anchor
    results = [compare_first_review_lag(monday + timedelta(days=i), intervals) for i in range(7)]
    extra = [r["extra_delay_days"] for r in results]
    return {
        "per_weekday": results,
        "worst_case_extra_delay_days": max(extra),
        "best_case_extra_delay_days": min(extra),
        "average_extra_delay_days": sum(extra) / len(extra),
    }
