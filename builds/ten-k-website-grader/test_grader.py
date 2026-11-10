"""
The test that matters: a deliberately well-built site scores high and a
deliberately generic AI-site-shaped one scores low, on real fixture
files on disk (not synthetic in-memory HTML strings) — same
discrimination-test discipline as every other text/pattern tool in this
project (humanizer, voice-extractor, agent-readiness-scorecard).

Run with:
    python3 -m unittest test_grader -v
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from ten_k_grader import grade_site

HERE = Path(__file__).parent
GOOD_SITE = HERE / "fixtures" / "good-site"
GENERIC_SITE = HERE / "fixtures" / "generic-site"


class TestDiscrimination(unittest.TestCase):
    def test_good_site_scores_high(self) -> None:
        report = grade_site(GOOD_SITE)
        self.assertGreaterEqual(report.overall_score, 0.85, report.to_dict())

    def test_generic_site_scores_lower_than_good_site(self) -> None:
        good = grade_site(GOOD_SITE)
        generic = grade_site(GENERIC_SITE)
        self.assertLess(generic.overall_score, good.overall_score)

    def test_point_of_view_is_never_assessable(self) -> None:
        for site in (GOOD_SITE, GENERIC_SITE):
            report = grade_site(site)
            pov = next(p for p in report.pillars if p.name == "point-of-view")
            self.assertFalse(pov.assessable)
            self.assertIsNone(pov.passed)

    def test_eight_pillars_always_reported(self) -> None:
        report = grade_site(GOOD_SITE)
        self.assertEqual(len(report.pillars), 8)


class TestIndividualPillars(unittest.TestCase):
    def setUp(self) -> None:
        self.good = grade_site(GOOD_SITE)
        self.generic = grade_site(GENERIC_SITE)

    def _pillar(self, report, name):
        return next(p for p in report.pillars if p.name == name)

    def test_typography_fails_on_flat_single_font_single_size(self) -> None:
        self.assertFalse(self._pillar(self.generic, "typography").passed)
        self.assertTrue(self._pillar(self.good, "typography").passed)

    def test_inter_usage_flagged_but_not_fatal_by_itself(self) -> None:
        self.assertTrue(any("Inter" in f for f in self.generic.flags))

    def test_default_blue_flagged(self) -> None:
        self.assertTrue(any("2563eb" in f for f in self.generic.flags))

    def test_motion_requires_both_presence_and_reduced_motion_support(self) -> None:
        self.assertFalse(self._pillar(self.generic, "motion").passed)
        self.assertTrue(self._pillar(self.good, "motion").passed)

    def test_mobile_requires_viewport_meta_and_breakpoint(self) -> None:
        self.assertFalse(self._pillar(self.generic, "mobile").passed)
        self.assertTrue(self._pillar(self.good, "mobile").passed)

    def test_invisible_stuff_catches_broken_ref_and_duplicate_id(self) -> None:
        pillar = self._pillar(self.generic, "invisible-stuff")
        self.assertFalse(pillar.passed)
        self.assertIn("1 broken local reference", pillar.reason)
        self.assertIn("1 duplicate id", pillar.reason)

    def test_imagery_fails_on_missing_alt_text(self) -> None:
        self.assertFalse(self._pillar(self.generic, "imagery").passed)
        self.assertTrue(self._pillar(self.good, "imagery").passed)


class TestEdgeCases(unittest.TestCase):
    def test_empty_directory_does_not_crash(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            report = grade_site(Path(tmp))
            self.assertEqual(report.overall_score, 0.0)
            self.assertEqual(len(report.pillars), 8)


class TestCli(unittest.TestCase):
    def test_cli_json_round_trip_real_subprocess(self) -> None:
        result = subprocess.run(
            [sys.executable, "ten_k_grader.py", str(GOOD_SITE), "--json"],
            cwd=HERE, capture_output=True, text=True, check=True,
        )
        import json
        payload = json.loads(result.stdout)
        self.assertEqual(payload["total_pillars"], 8)
        self.assertGreaterEqual(payload["overall_score"], 0.85)

    def test_cli_min_score_exit_code(self) -> None:
        result = subprocess.run(
            [sys.executable, "ten_k_grader.py", str(GENERIC_SITE), "--min-score", "0.9"],
            cwd=HERE, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)

    def test_cli_nonexistent_dir_gives_clean_error(self) -> None:
        result = subprocess.run(
            [sys.executable, "ten_k_grader.py", "/no/such/dir"],
            cwd=HERE, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
