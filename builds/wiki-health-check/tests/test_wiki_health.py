import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_health import (
    Claim,
    RawSource,
    Severity,
    WikiNote,
    check_contradictions,
    check_coverage_gaps,
    check_staleness,
    run_health_check,
)


def claim(subject, value, on, severity=Severity.ACTIONABLE):
    return Claim(subject=subject, value=value, asserted_on=date.fromisoformat(on), severity=severity)


# -- A clean, healthy wiki: nothing should fire. ----------------------------

HEALTHY_NOTES = [
    WikiNote(
        topic="acme-client",
        claims=[claim("pricing-sent-by", "friday", "2027-01-05")],
        source_names=["2027-01-03-client-call.md"],
    ),
    WikiNote(
        topic="obsidian-setup",
        claims=[claim("sync-price", "$5/month", "2027-01-01")],
        source_names=["obsidian-pricing-page.md"],
    ),
]

HEALTHY_RAW = [
    RawSource(
        name="2027-01-03-client-call.md",
        added_on=date(2027, 1, 3),
        topics=["acme-client"],
        claims=[claim("pricing-sent-by", "friday", "2027-01-03")],
    ),
    RawSource(
        name="obsidian-pricing-page.md",
        added_on=date(2027, 1, 1),
        topics=["obsidian-setup"],
        claims=[claim("sync-price", "$5/month", "2027-01-01")],
    ),
]


class TestHealthyWikiStaysClean(unittest.TestCase):
    def test_no_findings_on_healthy_wiki(self):
        findings = run_health_check(HEALTHY_NOTES, HEALTHY_RAW, min_mentions=3)
        self.assertEqual(findings, [])


# -- A broken wiki, modeled on the article's own worked scenarios. ---------
# A pricing decision reversed in a June meeting but the note's still March's
# figure (staleness); two notes citing different values for the same client
# deadline with no clear newer/older relation (contradiction); "budget" and
# "pricing" each mentioned in 3+ raw sources with no dedicated note yet
# (coverage gap); a renamed folder -- cosmetic, must NOT trigger anything.

BROKEN_NOTES = [
    WikiNote(
        topic="q1-budget-meeting",
        claims=[claim("budget-cap", "$50k", "2027-03-10")],  # stale: June raised it
        source_names=["march-meeting.md"],
    ),
    WikiNote(
        topic="acme-client",
        claims=[claim("delivery-deadline", "March 1", "2027-02-01")],
        source_names=["jan-call.md"],
    ),
    WikiNote(
        topic="acme-client-followup",
        claims=[claim("delivery-deadline", "April 15", "2027-02-01")],
        source_names=["feb-call.md"],
    ),
    WikiNote(
        topic="vault-rename",
        claims=[claim("vault-folder-name", "work-vault", "2027-01-01", severity=Severity.COSMETIC)],
        source_names=["rename-note.md"],
    ),
]

BROKEN_RAW = [
    RawSource(
        name="march-meeting.md",
        added_on=date(2027, 3, 10),
        topics=["q1-budget-meeting", "budget"],
        claims=[claim("budget-cap", "$50k", "2027-03-10")],
    ),
    RawSource(
        name="june-meeting.md",
        added_on=date(2027, 6, 2),
        topics=["q1-budget-meeting", "budget"],
        claims=[claim("budget-cap", "$80k", "2027-06-02")],
    ),
    RawSource(name="jan-call.md", added_on=date(2027, 2, 1), topics=["acme-client", "pricing"]),
    RawSource(name="feb-call.md", added_on=date(2027, 2, 1), topics=["acme-client-followup", "pricing"]),
    RawSource(name="mar-call.md", added_on=date(2027, 3, 1), topics=["pricing", "budget"]),
    RawSource(
        name="rename-note.md",
        added_on=date(2027, 1, 1),
        topics=["vault-rename"],
        claims=[claim("vault-folder-name", "notes-vault", "2027-02-01", severity=Severity.COSMETIC)],
    ),
]


class TestBrokenWikiFiresEveryRealCheck(unittest.TestCase):
    def test_staleness_catches_the_reversed_budget(self):
        findings = check_staleness(BROKEN_NOTES, BROKEN_RAW)
        self.assertEqual(len(findings), 1)
        self.assertIn("$50k", findings[0].detail)
        self.assertIn("$80k", findings[0].detail)
        self.assertIn("june-meeting.md", findings[0].detail)

    def test_contradiction_catches_the_two_deadlines(self):
        findings = check_contradictions(BROKEN_NOTES)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "contradiction")
        self.assertIn("March 1", findings[0].detail)
        self.assertIn("April 15", findings[0].detail)

    def test_coverage_gap_catches_pricing_and_budget(self):
        findings = check_coverage_gaps(BROKEN_RAW, BROKEN_NOTES, min_mentions=3)
        gap_subjects = {f.detail.split("'")[1] for f in findings}
        self.assertIn("pricing", gap_subjects)
        self.assertIn("budget", gap_subjects)

    def test_cosmetic_rename_never_fires_anything(self):
        all_findings = run_health_check(BROKEN_NOTES, BROKEN_RAW, min_mentions=3)
        for f in all_findings:
            self.assertNotIn("vault-folder-name", f.detail)
            self.assertNotIn("work-vault", f.detail)
            self.assertNotIn("notes-vault", f.detail)

    def test_full_run_finds_all_three_kinds(self):
        kinds = {f.kind for f in run_health_check(BROKEN_NOTES, BROKEN_RAW, min_mentions=3)}
        self.assertEqual(kinds, {"staleness", "contradiction", "coverage_gap"})


class TestCoverageGapThreshold(unittest.TestCase):
    def test_below_threshold_does_not_fire(self):
        raw = [
            RawSource(name="a.md", added_on=date(2027, 1, 1), topics=["rare-topic"]),
            RawSource(name="b.md", added_on=date(2027, 1, 2), topics=["rare-topic"]),
        ]
        findings = check_coverage_gaps(raw, notes=[], min_mentions=3)
        self.assertEqual(findings, [])

    def test_already_covered_topic_never_flagged(self):
        raw = [
            RawSource(name=f"s{i}.md", added_on=date(2027, 1, i + 1), topics=["covered"]) for i in range(5)
        ]
        notes = [WikiNote(topic="covered")]
        findings = check_coverage_gaps(raw, notes, min_mentions=3)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
