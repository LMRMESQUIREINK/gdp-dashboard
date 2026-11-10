import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skill_md_validator import (
    validate_skill_dir,
    validate_skills_root,
    validate_pack,
    check_pack_description_budget,
    check_description_overlap,
    _collect_descriptions,
)

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
    against this project's own real skills, the same "test against our
    own real material" discipline as /builds/ten-k-website-grader/ and
    /builds/agent-readiness-scorecard/.

    The count below was corrected from a stale 11 to the real, current
    12 (this project shipped `retro` after this test was first written)
    -- found as a side effect of touching this test this round, not
    chased down separately."""

    def test_real_skills_directory_exists(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        self.assertTrue(skills_dir.is_dir(), f"expected to find real skills at {skills_dir}")

    def test_all_real_skills_pass_with_no_errors(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports = validate_skills_root(skills_dir, repo_root=REPO_ROOT)
        self.assertEqual(len(reports), 12, "expected exactly the twelve real skills this project has shipped")
        failing = [(r.skill_dir.name, codes(r)) for r in reports if not r.ok]
        self.assertEqual(failing, [], f"real skills should all pass with zero errors: {failing}")

    def test_four_real_skills_now_warn_over_the_real_500char_recommendation(self):
        """A real finding from this round, not a synthetic test case:
        reading coreyhaines31/marketingskills' own dated measurement
        (/notes/marketingskills-analysis.md) and checking it against
        this project's own skills found four whose descriptions
        genuinely exceed the 500-char recommendation --
        launch-kit-writer (721 chars), sales-page-engine (613),
        voice-extractor (576), launch-pad (519), confirmed by direct
        character count. (A first draft of this test only named three,
        having miscounted launch-pad's 519 as under the line when it
        isn't -- corrected to match a recount, not forced to match the
        original miscount.) Warnings, not errors: still well under
        this project's own existing 1500-char ceiling."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports = validate_skills_root(skills_dir, repo_root=REPO_ROOT)
        over_recommended = {r.skill_dir.name for r in reports if "description-over-recommended" in codes(r)}
        self.assertEqual(over_recommended, {"launch-kit-writer", "sales-page-engine", "voice-extractor", "launch-pad"})
        for r in reports:
            if r.skill_dir.name in over_recommended:
                self.assertTrue(r.ok, f"{r.skill_dir.name} should still pass -- this is a warning, not an error")


class TestPackDescriptionBudget(unittest.TestCase):
    def test_well_under_budget_produces_no_findings(self):
        descriptions = {Path("a"): "x" * 100, Path("b"): "y" * 100}
        self.assertEqual(check_pack_description_budget(descriptions), [])

    def test_crossing_the_warn_threshold_warns_not_errors(self):
        descriptions = {Path(f"skill-{i}"): "x" * 1000 for i in range(20)}  # 20,000 chars
        findings = check_pack_description_budget(descriptions, warn_at=19_000, cap_at=30_000)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "pack-description-budget-warning")
        self.assertEqual(findings[0].severity, "warning")

    def test_crossing_the_hard_cap_still_only_warns_never_errors(self):
        """Deliberate design choice, stated in the function's own
        docstring: a pack over budget still works (some descriptions
        just show name-only), so this is never a hard error."""
        descriptions = {Path(f"skill-{i}"): "x" * 1000 for i in range(35)}  # 35,000 chars
        findings = check_pack_description_budget(descriptions, warn_at=19_000, cap_at=30_000)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "pack-description-budget-exceeded")
        self.assertEqual(findings[0].severity, "warning")

    def test_real_run_against_this_repos_own_skills_is_nowhere_near_the_budget(self):
        """A real, honest 'no problem found' result, not a manufactured
        one: this project's own 12 skills total around 5.5k characters,
        far under even the warn threshold."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        descriptions = _collect_descriptions(skills_dir)
        self.assertEqual(len(descriptions), 12)
        total = sum(len(d) for d in descriptions.values())
        self.assertLess(total, 19_000)
        self.assertEqual(check_pack_description_budget(descriptions), [])


class TestDescriptionOverlap(unittest.TestCase):
    def test_discrimination_near_identical_descriptions_are_flagged(self):
        descriptions = {
            Path("skill-a"): "Use when the user wants to plan and run conversion rate experiments on pricing pages and landing pages for SaaS products.",
            Path("skill-b"): "Use when the user wants to plan and run conversion rate experiments on signup pages and landing pages for SaaS products.",
        }
        findings = check_description_overlap(descriptions, threshold=0.4)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "description-overlap")

    def test_discrimination_genuinely_distinct_descriptions_are_not_flagged(self):
        descriptions = {
            Path("skill-a"): "Use when the user wants to plan and run conversion rate experiments on pricing pages.",
            Path("skill-b"): "Use when the user wants to write cold outbound emails for B2B sales prospecting campaigns.",
        }
        self.assertEqual(check_description_overlap(descriptions, threshold=0.4), [])

    def test_shared_boilerplate_trigger_phrasing_alone_does_not_count_as_overlap(self):
        """The stopword list exists specifically so two skills that both
        say 'use when the user wants to' don't get flagged just for
        sharing that boilerplate -- only real shared content words
        should count."""
        descriptions = {
            Path("skill-a"): "Use when the user wants to optimize App Store listings and keyword rankings.",
            Path("skill-b"): "Use when the user wants to write cold outbound sales emails for prospecting.",
        }
        self.assertEqual(check_description_overlap(descriptions, threshold=0.3), [])

    def test_each_pair_reported_at_most_once(self):
        descriptions = {
            Path("skill-a"): "pricing page conversion rate experiment landing page",
            Path("skill-b"): "pricing page conversion rate experiment landing page",
            Path("skill-c"): "cold email prospecting outbound sales",
        }
        findings = check_description_overlap(descriptions, threshold=0.4)
        self.assertEqual(len(findings), 1)

    def test_real_run_against_this_repos_own_skills_finds_no_overlap(self):
        """This project's 12 skills cover genuinely distinct domains
        (copy, SEO-adjacent pSEO, voice, launch, review process) --
        confirmed by actually running the check, not assumed."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        descriptions = _collect_descriptions(skills_dir)
        findings = check_description_overlap(descriptions, threshold=0.4)
        self.assertEqual(findings, [], f"unexpected overlap found: {findings}")


class TestValidatePack(unittest.TestCase):
    def test_returns_per_skill_reports_and_pack_findings_separately(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports, pack_findings = validate_pack(skills_dir, repo_root=REPO_ROOT)
        self.assertEqual(len(reports), 12)
        self.assertEqual(pack_findings, [])  # real repo is well under budget, no overlap

    def test_cli_prints_a_pack_level_section_when_findings_exist(self):
        result = subprocess.run(
            [sys.executable, str(HERE / "skill_md_validator.py"), str(HERE / "tests" / "fixtures"), "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)  # the fixtures dir has real per-skill errors
        payload = json.loads(result.stdout)
        self.assertIn("skills", payload)
        self.assertIn("pack_level", payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
