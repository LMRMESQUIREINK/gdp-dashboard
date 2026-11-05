import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skill_md_validator import validate_skill_dir, validate_skills_root

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "tests" / "fixtures"
DUP_ROOT = HERE / "tests" / "fixtures-dup-root"
REPO_ROOT = HERE.parent.parent  # builds/skill-md-validator -> builds -> repo root


def codes(report):
    return {f.code for f in report.findings}


class TestGoodSkillPasses(unittest.TestCase):
    def test_well_formed_skill_has_no_findings(self):
        report = validate_skill_dir(FIXTURES / "good-skill")
        self.assertTrue(report.ok)
        self.assertEqual(report.findings, [])


class TestNameChecks(unittest.TestCase):
    def test_name_directory_mismatch_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "bad-name-mismatch")
        self.assertFalse(report.ok)
        self.assertIn("name-directory-mismatch", codes(report))

    def test_bad_name_format_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "bad-name-format")
        self.assertFalse(report.ok)
        self.assertIn("bad-name-format", codes(report))


class TestDescriptionChecks(unittest.TestCase):
    def test_missing_description_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "missing-description")
        self.assertFalse(report.ok)
        self.assertIn("missing-description", codes(report))

    def test_too_short_description_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "short-description")
        self.assertFalse(report.ok)
        self.assertIn("description-too-short", codes(report))

    def test_missing_trigger_phrase_is_a_warning_not_an_error(self):
        report = validate_skill_dir(FIXTURES / "no-trigger-phrase")
        self.assertTrue(report.ok, "a missing trigger phrase must be advisory, not blocking")
        self.assertIn("no-trigger-condition", codes(report))

    def test_use_while_phrasing_is_recognized_as_a_trigger_condition(self):
        # Regression test for a real false positive this build's own
        # first draft produced against this repo's real
        # .claude/skills/code-structure and review-loop: both state a
        # clear usage condition ("Use while implementing...", "Before
        # calling a build finished, run it through...") that the
        # original TRIGGER_WORDS list didn't recognize. Confirmed by
        # reading the real files before fixing the heuristic.
        report = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "code-structure")
        self.assertNotIn("no-trigger-condition", codes(report))
        report2 = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "review-loop")
        self.assertNotIn("no-trigger-condition", codes(report2))


class TestBodyChecks(unittest.TestCase):
    def test_empty_body_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "empty-body")
        self.assertFalse(report.ok)
        self.assertIn("empty-body", codes(report))

    def test_thin_body_is_a_warning_not_an_error(self):
        report = validate_skill_dir(FIXTURES / "thin-body")
        self.assertTrue(report.ok)
        self.assertIn("thin-body", codes(report))


class TestFrontmatterParsing(unittest.TestCase):
    def test_unparseable_frontmatter_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "unparseable-frontmatter")
        self.assertFalse(report.ok)
        self.assertIn("unparseable-frontmatter", codes(report))

    def test_missing_skill_md_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "no-skill-md")
        self.assertFalse(report.ok)
        self.assertIn("missing-skill-md", codes(report))


class TestReferenceResolution(unittest.TestCase):
    def test_broken_same_folder_reference_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "broken-reference")
        self.assertFalse(report.ok)
        self.assertIn("broken-reference", codes(report))

    def test_good_skills_same_folder_reference_resolves(self):
        report = validate_skill_dir(FIXTURES / "good-skill")
        self.assertNotIn("broken-reference", codes(report))

    def test_repo_root_relative_references_resolve_with_repo_root_given(self):
        # Regression test for the real bug found running this validator
        # against this repo's own real skills: without repo_root, every
        # skill using a repo-root-relative reference (a leading '/', or
        # a bare '.claude/skills/other-skill') was false-flagged as
        # broken, 16 false positives across 7 real, correct skills on
        # the very first run.
        report_without_root = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "humanizer")
        self.assertIn("broken-reference", codes(report_without_root), "sanity check: without repo_root this must still reproduce the original false positive")

        report_with_root = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "humanizer", repo_root=REPO_ROOT)
        self.assertNotIn("broken-reference", codes(report_with_root))

    def test_genuinely_broken_reference_still_caught_even_with_repo_root(self):
        # A reference that resolves under neither the skill's own
        # directory NOR the repo root must still fail -- repo_root
        # should widen what counts as valid, never silence a real gap.
        report = validate_skill_dir(FIXTURES / "broken-reference", repo_root=REPO_ROOT)
        self.assertIn("broken-reference", codes(report))


class TestDuplicateNameDetection(unittest.TestCase):
    def test_sibling_skills_sharing_a_name_are_both_flagged(self):
        reports = validate_skills_root(DUP_ROOT)
        self.assertEqual(len(reports), 2)
        for report in reports:
            self.assertFalse(report.ok)
            self.assertIn("duplicate-skill-name", codes(report))

    def test_distinct_names_across_siblings_are_not_flagged(self):
        reports = validate_skills_root(FIXTURES, repo_root=REPO_ROOT)
        for report in reports:
            self.assertNotIn("duplicate-skill-name", codes(report))


class TestAgainstThisRepositorysRealSkills(unittest.TestCase):
    """The actual deliverable this round: run the validator for real
    against this project's own eleven real skills, the same
    "test against our own real material" discipline as
    /builds/ten-k-website-grader/ and /builds/agent-readiness-scorecard/."""

    def test_real_skills_directory_exists(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        self.assertTrue(skills_dir.is_dir(), f"expected to find real skills at {skills_dir}")

    def test_all_real_skills_pass_clean(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports = validate_skills_root(skills_dir, repo_root=REPO_ROOT)
        self.assertEqual(len(reports), 11, "expected exactly the eleven real skills this project has shipped")
        failing = [(r.skill_dir.name, codes(r)) for r in reports if not r.ok]
        self.assertEqual(failing, [], f"real skills should all pass clean: {failing}")
        for r in reports:
            self.assertEqual(r.findings, [], f"{r.skill_dir.name} should have zero findings, got {r.findings}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
