"""Tests for extract_claims.py -- the raw-article-text auto-extraction
mode. tests/fixtures/12-repo-learning-path-article.txt is a condensed
reconstruction of the real article this build came from (same repo
links, same lesson-count figures, same byline wording, same archived
notice, in the same numbered-heading shape) -- not a byte-for-byte copy
of the full ~2,500-word article, which also carries a lot of prose
(prerequisites, mini-projects, "why now") this module was never meant
to parse. What matters for these tests is that the extractable facts
are worded exactly as the real article worded them.
"""

import os
import unittest

from curriculum_auditor import RepoClaim, audit_manifest
from extract_claims import (
    auto_extract_manifest,
    extract_archived_claim,
    extract_author_byline,
    extract_lesson_count_claim,
    extract_repo_links,
    split_into_sections,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "tests", "fixtures")

with open(os.path.join(FIXTURES, "12-repo-learning-path-article.txt"), encoding="utf-8") as f:
    ARTICLE_TEXT = f.read()

EXPECTED_REPOS = [
    "mml-book/mml-book.github.io",
    "microsoft/AI-For-Beginners",
    "microsoft/generative-ai-for-beginners",
    "dair-ai/Prompt-Engineering-Guide",
    "mlabonne/llm-course",
    "rasbt/LLMs-from-scratch",
    "FareedKhan-dev/train-llm-from-scratch",
    "karpathy/nanochat",
    "huggingface/ml-intern",
    "harvard-edge/cs249r_book",
    "labmlai/annotated_deep_learning_paper_implementations",
    "rohitg00/ai-engineering-from-scratch",
]


class TestExtractRepoLinks(unittest.TestCase):
    def test_finds_all_12_real_repos_in_order_no_duplicates(self):
        self.assertEqual(extract_repo_links(ARTICLE_TEXT), EXPECTED_REPOS)

    def test_strips_utm_query_params(self):
        repos = extract_repo_links("See https://github.com/foo/bar?utm_campaign=x&utm_source=y")
        self.assertEqual(repos, ["foo/bar"])

    def test_a_link_into_a_repo_subpath_still_resolves_to_that_repo(self):
        # .../issues/12 and .../blob/main/x.py are both still about
        # repo foo/bar -- a listicle linking to a repo's issues page
        # is citing that repo, not a different, nonexistent one.
        repos = extract_repo_links("https://github.com/foo/bar/issues/12 and https://github.com/foo/bar/blob/main/x.py")
        self.assertEqual(repos, ["foo/bar"])

    def test_a_real_repo_link_alongside_a_sub_path_link_is_still_found_once(self):
        repos = extract_repo_links(
            "https://github.com/foo/bar and also https://github.com/foo/bar/tree/main/docs"
        )
        self.assertEqual(repos, ["foo/bar"])


class TestSplitIntoSections(unittest.TestCase):
    def test_splits_into_exactly_12_sections(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertEqual(len(sections), 12)

    def test_each_section_starts_with_its_own_numbered_heading(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertTrue(sections[4].lstrip().startswith("5. LLM Course"))
        self.assertTrue(sections[8].lstrip().startswith("9. Hugging Face ML Intern"))


class TestLessonCountExtraction(unittest.TestCase):
    def test_extracts_the_real_24_lesson_claim_from_its_section(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertEqual(extract_lesson_count_claim(sections[1]), 24)

    def test_extracts_the_real_21_lesson_claim_from_its_section(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertEqual(extract_lesson_count_claim(sections[2]), 21)

    def test_none_for_a_section_with_no_lesson_count(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertIsNone(extract_lesson_count_claim(sections[0]))


class TestArchivedClaimExtraction(unittest.TestCase):
    def test_the_real_ml_intern_section_is_flagged_archived(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertTrue(extract_archived_claim(sections[8]))

    def test_an_ordinary_active_section_is_not_flagged(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertIsNone(extract_archived_claim(sections[1]))


class TestAuthorBylineExtraction(unittest.TestCase):
    def test_extracts_the_real_misattributed_byline(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertEqual(extract_author_byline(sections[4]), "Maarten Grootendorst")

    def test_no_byline_on_a_heading_with_no_by_clause(self):
        sections = split_into_sections(ARTICLE_TEXT)
        self.assertIsNone(extract_author_byline(sections[0]))

    def test_does_not_mistake_a_body_sentence_for_a_byline(self):
        # "by" appears in body prose elsewhere in the article (e.g.
        # "written by the community") -- only the heading line counts.
        section = "9. Some Tool\nRepository: foo/bar\nThis was reviewed by Jane Smith last year."
        self.assertIsNone(extract_author_byline(section))


class TestAutoExtractManifest(unittest.TestCase):
    def test_extracts_exactly_12_claims_matching_the_real_repos(self):
        claims = auto_extract_manifest(ARTICLE_TEXT)
        self.assertEqual([c.repo for c in claims], EXPECTED_REPOS)

    def test_the_real_claim_shape_matches_the_hand_written_manifest(self):
        """The test that matters: auto-extraction from raw text should
        reproduce the same facts this build's hand-written
        manifest_12_repo_learning_path.json encodes for the same 5
        claims, without a human transcribing them."""
        claims = {c.repo: c for c in auto_extract_manifest(ARTICLE_TEXT)}

        self.assertEqual(claims["microsoft/AI-For-Beginners"].claimed_lesson_count, 24)
        self.assertEqual(claims["microsoft/generative-ai-for-beginners"].claimed_lesson_count, 21)
        self.assertEqual(claims["mlabonne/llm-course"].claimed_author, "Maarten Grootendorst")
        self.assertTrue(claims["huggingface/ml-intern"].claimed_archived)
        # A repo with no stated lesson count, author byline, or archived
        # notice should extract no false claims about it either.
        self.assertIsNone(claims["karpathy/nanochat"].claimed_lesson_count)
        self.assertIsNone(claims["karpathy/nanochat"].claimed_author)
        self.assertIsNone(claims["karpathy/nanochat"].claimed_archived)

    def test_end_to_end_auto_extracted_claims_audit_the_same_as_hand_written_ones(self):
        """Full pipeline: raw article text in, audit results out, with
        no RepoClaim written by hand -- and the result matches exactly
        what the hand-written manifest produced in the original round
        (4 clean matches + 1 real misattribution)."""
        claims = auto_extract_manifest(ARTICLE_TEXT)
        readmes = {}
        for fname, repo in [
            ("ml-intern-README.md", "huggingface/ml-intern"),
            ("ai-for-beginners-README.md", "microsoft/AI-For-Beginners"),
            ("llm-course-README.md", "mlabonne/llm-course"),
        ]:
            with open(os.path.join(FIXTURES, fname), encoding="utf-8") as f:
                readmes[repo] = f.read()

        results = {r.repo: r for r in audit_manifest(claims, readmes)}

        self.assertTrue(results["microsoft/AI-For-Beginners"].clean)
        self.assertTrue(results["huggingface/ml-intern"].clean)
        llm_course = results["mlabonne/llm-course"]
        self.assertFalse(llm_course.clean)
        self.assertEqual(len(llm_course.mismatches), 1)
        self.assertIn("author attribution", llm_course.mismatches[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
