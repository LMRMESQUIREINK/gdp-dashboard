"""Real-fixture and synthetic tests for curriculum_auditor.py.

The fixtures under tests/fixtures/ are the real, unmodified READMEs of
three repos named in the 12-repo learning-path article this build came
from (huggingface/ml-intern, microsoft/AI-For-Beginners,
mlabonne/llm-course) -- not synthetic stand-ins, same discipline as
every other "test against this project's own real material" build.
"""

import os
import unittest

from curriculum_auditor import (
    AuditResult,
    RepoClaim,
    audit_manifest,
    audit_repo_claim,
    check_author_attribution,
    check_repo_exists_live,
    check_structure_keywords,
    detect_archived_banner,
    extract_lesson_count,
    extract_maintainer_handles,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "tests", "fixtures")


def _read_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


ML_INTERN_README = _read_fixture("ml-intern-README.md")
AI_FOR_BEGINNERS_README = _read_fixture("ai-for-beginners-README.md")
LLM_COURSE_README = _read_fixture("llm-course-README.md")


class TestLessonCountExtraction(unittest.TestCase):
    def test_extracts_the_real_24_lesson_claim(self):
        self.assertEqual(extract_lesson_count(AI_FOR_BEGINNERS_README), 24)

    def test_none_when_no_lesson_count_stated(self):
        self.assertIsNone(extract_lesson_count("Just a plain README with no lesson count."))

    def test_case_insensitive_and_hyphenated(self):
        self.assertEqual(extract_lesson_count("A 7-Lesson crash course."), 7)


class TestArchivedBannerDetection(unittest.TestCase):
    def test_detects_the_real_ml_intern_archive_banner(self):
        is_archived, evidence = detect_archived_banner(ML_INTERN_README)
        self.assertTrue(is_archived)
        self.assertIn("archived", evidence.lower())

    def test_no_false_positive_on_a_clean_active_readme(self):
        is_archived, evidence = detect_archived_banner(AI_FOR_BEGINNERS_README)
        self.assertFalse(is_archived)
        self.assertIsNone(evidence)

    def test_detects_deprecated_phrasing_too(self):
        is_archived, _ = detect_archived_banner("Note: this project is deprecated in favor of X.")
        self.assertTrue(is_archived)


class TestMaintainerHandleExtraction(unittest.TestCase):
    def test_finds_the_real_llm_course_maintainer_handles(self):
        handles = extract_maintainer_handles(LLM_COURSE_README)
        self.assertIn("maximelabonne", handles)
        self.assertIn("mlabonne", handles)

    def test_empty_when_readme_has_no_handles(self):
        self.assertEqual(extract_maintainer_handles("No links here at all."), set())


class TestAuthorAttribution(unittest.TestCase):
    """The real finding this build exists to catch: the article
    attributes mlabonne/llm-course to "Maarten Grootendorst" (a real,
    different AI author -- BERTopic/KeyBERT's creator) when the repo's
    own README names its real maintainer as Maxime Labonne."""

    def test_correct_author_is_confirmed(self):
        ok, reason = check_author_attribution(LLM_COURSE_README, "Maxime Labonne")
        self.assertTrue(ok)
        self.assertIn("maximelabonne", reason)

    def test_the_real_misattribution_is_flagged(self):
        ok, reason = check_author_attribution(LLM_COURSE_README, "Maarten Grootendorst")
        self.assertFalse(ok)
        self.assertIn("misattribution", reason)

    def test_no_handles_is_a_soft_pass_not_an_accusation(self):
        ok, reason = check_author_attribution("No social links in this README at all.", "Anyone")
        self.assertTrue(ok)
        self.assertIn("not checkable", reason)


class TestStructureKeywords(unittest.TestCase):
    def test_all_three_real_llm_course_sections_are_found(self):
        missing = check_structure_keywords(
            LLM_COURSE_README, ["LLM Fundamentals", "The LLM Scientist", "The LLM Engineer"]
        )
        self.assertEqual(missing, [])

    def test_a_fabricated_keyword_is_correctly_reported_missing(self):
        missing = check_structure_keywords(LLM_COURSE_README, ["The LLM Philosopher"])
        self.assertEqual(missing, ["The LLM Philosopher"])


class TestAuditRepoClaim(unittest.TestCase):
    def test_ml_intern_archived_claim_matches_clean(self):
        claim = RepoClaim(repo="huggingface/ml-intern", claimed_archived=True)
        result = audit_repo_claim(ML_INTERN_README, claim)
        self.assertTrue(result.clean)
        self.assertEqual(len(result.matches), 1)

    def test_ai_for_beginners_lesson_count_claim_matches_clean(self):
        claim = RepoClaim(repo="microsoft/AI-For-Beginners", claimed_lesson_count=24)
        result = audit_repo_claim(AI_FOR_BEGINNERS_README, claim)
        self.assertTrue(result.clean)

    def test_llm_course_full_claim_set_surfaces_exactly_the_real_misattribution(self):
        """The article's real, full claim set for this repo: correct
        structure, but the wrong author. This is the test that proves
        the tool discriminates rather than flagging everything or
        nothing -- structure passes, author fails, in the same call."""
        claim = RepoClaim(
            repo="mlabonne/llm-course",
            claimed_author="Maarten Grootendorst",
            claimed_structure_keywords=["LLM Fundamentals", "The LLM Scientist", "The LLM Engineer"],
        )
        result = audit_repo_claim(LLM_COURSE_README, claim)
        self.assertFalse(result.clean)
        self.assertEqual(len(result.matches), 1)
        self.assertEqual(len(result.mismatches), 1)
        self.assertIn("structure", result.matches[0])
        self.assertIn("author attribution", result.mismatches[0])

    def test_wrong_lesson_count_claim_is_caught(self):
        claim = RepoClaim(repo="microsoft/AI-For-Beginners", claimed_lesson_count=99)
        result = audit_repo_claim(AI_FOR_BEGINNERS_README, claim)
        self.assertFalse(result.clean)
        self.assertEqual(len(result.mismatches), 1)


class TestAuditManifest(unittest.TestCase):
    def test_runs_all_real_article_claims_in_one_pass(self):
        claims = [
            RepoClaim(repo="huggingface/ml-intern", claimed_archived=True),
            RepoClaim(repo="microsoft/AI-For-Beginners", claimed_lesson_count=24),
            RepoClaim(
                repo="mlabonne/llm-course",
                claimed_author="Maarten Grootendorst",
                claimed_structure_keywords=["LLM Fundamentals", "The LLM Scientist", "The LLM Engineer"],
            ),
        ]
        readmes = {
            "huggingface/ml-intern": ML_INTERN_README,
            "microsoft/AI-For-Beginners": AI_FOR_BEGINNERS_README,
            "mlabonne/llm-course": LLM_COURSE_README,
        }
        results = audit_manifest(claims, readmes)
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].clean)
        self.assertTrue(results[1].clean)
        self.assertFalse(results[2].clean)

    def test_missing_readme_is_flagged_not_silently_skipped(self):
        results = audit_manifest([RepoClaim(repo="nobody/nothing")], {})
        self.assertEqual(len(results), 1)
        self.assertIn("no README text supplied", results[0].flags[0])


class TestLiveExistenceCheck(unittest.TestCase):
    """The one network-dependent function in this module -- kept
    separate from everything above so a sandboxed/offline test run
    never needs it. Skips cleanly rather than failing when the
    network call itself can't be made (same convention as this
    project's go/gcc-on-PATH skip in go-buildinfo-extractor's tests)."""

    def test_a_real_known_repo_reports_as_existing(self):
        exists = check_repo_exists_live("octocat/Hello-World", timeout=10.0)
        if exists is False:
            self.skipTest("no live network access to GitHub from this environment")
        self.assertTrue(exists)

    def test_a_fabricated_repo_name_reports_as_not_existing(self):
        exists = check_repo_exists_live("this-owner-does-not-exist-zzz/nope-zzz", timeout=10.0)
        self.assertFalse(exists)


if __name__ == "__main__":
    unittest.main(verbosity=2)
