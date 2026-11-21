import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from provenance_check import (
    ProvenanceReport,
    check_provenance,
    extract_literal_tokens,
    find_binary_reuse,
    find_literal_token_reuse,
    find_reuse,
    is_disclosed,
    ngram_fingerprints,
    normalize,
)

HERE = os.path.dirname(os.path.abspath(__file__))


def fixture(name: str) -> str:
    with open(os.path.join(HERE, "fixtures", name), "r", encoding="utf-8") as f:
        return f.read()


REFERENCE_RAG_FROM_SCRATCH = fixture("reference_rag_from_scratch_cell32.txt")
CANDIDATE_RAG_ECOSYSTEM = fixture("candidate_rag_ecosystem_cell53.txt")
ARTICLE_PROSE_LANGCHAIN_MENTION = fixture("article_prose_langchain_mention.txt")

# A second, independent real-world case -- from a different Fareed Khan
# article/repo ("Building a Multi-Agent AI System with LangGraph and
# LangSmith"), checked against the real langchain-ai/langgraph-101 repo
# it names and links directly. Unlike the rag-ecosystem case above, this
# article's own image captions ("From LangChain — OpenSource") and a
# direct repo link disclose the reuse plainly.
REFERENCE_LANGGRAPH101_CHINOOK = fixture("reference_langgraph101_chinook_cell.txt")
CANDIDATE_MULTIAGENT_CHINOOK = fixture("candidate_multiagent_chinook_cell.txt")
ARTICLE_PROSE_LANGGRAPH101_DISCLOSURE = fixture("article_prose_langgraph101_disclosure.txt")

# A third, independent real-world case -- "Building DeepSeek R1 from
# Scratch" (Fareed Khan) checked against the real reward-function
# implementations in Hugging Face's own open-r1 project. Unlike either
# case above, this one needed two different detection mechanisms: the
# repetition-penalty function shares enough surrounding prose to show up
# under find_reuse()'s n-gram approach, but the reasoning-steps function's
# one character-for-character identical element -- its regex pattern --
# is a single whitespace-free token that n-gram fingerprinting can't see
# at all once the surrounding docstrings/comments diverge.
CANDIDATE_DEEPSEEKR1_REPETITION = fixture("candidate_deepseekr1_repetition_cell.py")
REFERENCE_OPENR1_REPETITION = fixture("reference_openr1_repetition_cell.py")
CANDIDATE_DEEPSEEKR1_REASONING_STEPS = fixture("candidate_deepseekr1_reasoning_steps_cell.py")
REFERENCE_OPENR1_REASONING_STEPS = fixture("reference_openr1_reasoning_steps_cell.py")
ARTICLE_PROSE_OPENR1_CITATION = fixture("article_prose_openr1_citation.txt")


class TestNormalizeAndFingerprints(unittest.TestCase):
    def test_normalize_collapses_whitespace_and_case(self):
        self.assertEqual(normalize("Hello   World\n\n"), "hello world")

    def test_fingerprints_short_text_returns_whole_text(self):
        grams = ngram_fingerprints("one two three", n=8)
        self.assertEqual(grams, {"one two three"})

    def test_fingerprints_empty_text_returns_empty_set(self):
        self.assertEqual(ngram_fingerprints("", n=8), set())

    def test_fingerprints_sliding_window_count(self):
        text = "a b c d e f g h i j"  # 10 words
        grams = ngram_fingerprints(text, n=8)
        self.assertEqual(len(grams), 3)  # 10 - 8 + 1
        self.assertIn("a b c d e f g h", grams)
        self.assertIn("c d e f g h i j", grams)


class TestFindReuse(unittest.TestCase):
    def test_no_overlap_with_unrelated_text(self):
        matches = find_reuse(
            "a completely different paragraph about cooking pasta with garlic and olive oil today",
            {"unrelated": "the quick brown fox jumps over the lazy dog near the riverbank"},
        )
        self.assertEqual(matches, [])

    def test_exact_duplicate_scores_overlap_ratio_one(self):
        text = "this exact sentence appears identically in both the candidate and the reference corpus here"
        matches = find_reuse(text, {"ref": text})
        self.assertEqual(len(matches), 1)
        self.assertAlmostEqual(matches[0].overlap_ratio, 1.0)

    def test_real_police_example_matches_across_both_real_repos(self):
        matches = find_reuse(CANDIDATE_RAG_ECOSYSTEM, {"rag-from-scratch": REFERENCE_RAG_FROM_SCRATCH})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].reference_name, "rag-from-scratch")
        self.assertGreater(matches[0].shared_ngrams, 5)
        # the specific verbatim phrase this round's investigation found
        self.assertTrue(any("members of the police" in s for s in matches[0].sample_matches))

    def test_multiple_references_sorted_by_overlap_descending(self):
        # candidate has 3 n-gram windows at n=8 (10 words -> 10-8+1=3)
        text = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
        high_overlap_ref = text  # shares all 3 windows -> ratio 1.0
        # shares only the candidate's last window (8 consecutive words),
        # padded with unrelated words so it isn't a full duplicate
        low_overlap_ref = "gamma delta epsilon zeta eta theta iota kappa plus some unrelated extra words here"
        matches = find_reuse(text, {"low": low_overlap_ref, "high": high_overlap_ref})
        self.assertEqual([m.reference_name for m in matches], ["high", "low"])
        self.assertAlmostEqual(matches[0].overlap_ratio, 1.0)
        self.assertAlmostEqual(matches[1].overlap_ratio, 1 / 3)


class TestIsDisclosed(unittest.TestCase):
    def test_specific_marker_found_counts_as_disclosed(self):
        self.assertTrue(is_disclosed("built on langchain-ai/rag-from-scratch", ["rag-from-scratch"]))

    def test_bare_brand_mention_is_not_in_marker_list_so_not_disclosed(self):
        # The actual finding: the article mentions "LangChain" as a tool
        # being used, never names the specific source repo/series.
        self.assertFalse(is_disclosed(ARTICLE_PROSE_LANGCHAIN_MENTION, ["rag-from-scratch", "lance martin"]))

    def test_case_and_whitespace_insensitive_marker_match(self):
        self.assertTrue(is_disclosed("See   RAG-FROM-SCRATCH for details", ["rag-from-scratch"]))

    def test_no_markers_means_never_disclosed(self):
        self.assertFalse(is_disclosed("anything at all", []))


class TestCheckProvenanceRealFinding(unittest.TestCase):
    """Reproduces this round's actual, by-hand-verified finding as a
    permanent regression test: the rag-ecosystem article's Step-Back
    Prompting example is verbatim-identical to LangChain's own real
    rag-from-scratch notebook, and the article's own prose (which
    mentions "LangChain" only as a library being used, confirmed via
    the real README text) never specifically names that source."""

    def test_real_finding_reproduced(self):
        report = check_provenance(
            candidate_text=CANDIDATE_RAG_ECOSYSTEM,
            references={"langchain-rag-from-scratch": REFERENCE_RAG_FROM_SCRATCH},
            disclosure_text=ARTICLE_PROSE_LANGCHAIN_MENTION,
            source_markers={"langchain-rag-from-scratch": ["rag-from-scratch", "lance martin", "rlm/rag-prompt"]},
        )
        self.assertIsInstance(report, ProvenanceReport)
        self.assertEqual(len(report.reuse), 1)
        self.assertEqual(len(report.undisclosed_reuse), 1)
        self.assertEqual(report.undisclosed_reuse[0].reference_name, "langchain-rag-from-scratch")

    def test_same_reuse_passes_once_properly_disclosed(self):
        # if the disclosure text had actually named the source, this
        # same reuse would no longer be flagged
        honest_disclosure = "This walkthrough builds on LangChain's own rag-from-scratch notebook series."
        report = check_provenance(
            candidate_text=CANDIDATE_RAG_ECOSYSTEM,
            references={"langchain-rag-from-scratch": REFERENCE_RAG_FROM_SCRATCH},
            disclosure_text=honest_disclosure,
            source_markers={"langchain-rag-from-scratch": ["rag-from-scratch"]},
        )
        self.assertEqual(report.undisclosed_reuse, [])

    def test_report_with_no_references_given_finds_nothing(self):
        report = check_provenance(
            candidate_text=CANDIDATE_RAG_ECOSYSTEM,
            references={},
            disclosure_text=ARTICLE_PROSE_LANGCHAIN_MENTION,
            source_markers={},
        )
        self.assertEqual(report.reuse, [])
        self.assertEqual(report.undisclosed_reuse, [])


class TestSecondRealWorldCaseProperDisclosure(unittest.TestCase):
    """Generalization test: a second, independent real-world pair,
    proving this tool doesn't just reproduce one fixed finding. This
    time, checked against "Building a Multi-Agent AI System with
    LangGraph and LangSmith" and the real `langchain-ai/langgraph-101`
    repo it names directly: 9 of 11 shared-filename images between the
    two real repos are byte-identical (confirmed via sha256), and the
    article's own real captions ("From LangChain — OpenSource") plus a
    direct repo link disclose exactly that reuse -- the opposite
    verdict from the rag-ecosystem case, and just as real."""

    def test_real_reuse_is_found(self):
        matches = find_reuse(CANDIDATE_MULTIAGENT_CHINOOK, {"langgraph-101": REFERENCE_LANGGRAPH101_CHINOOK})
        self.assertEqual(len(matches), 1)
        self.assertGreater(matches[0].shared_ngrams, 5)

    def test_real_disclosure_text_names_the_specific_repo(self):
        self.assertTrue(is_disclosed(ARTICLE_PROSE_LANGGRAPH101_DISCLOSURE, ["langgraph-101", "langchain-ai"]))

    def test_full_check_finds_no_undisclosed_reuse(self):
        # unlike the rag-ecosystem case, this real pairing should come
        # back clean -- the reuse is real, but so is the disclosure
        report = check_provenance(
            candidate_text=CANDIDATE_MULTIAGENT_CHINOOK,
            references={"langgraph-101": REFERENCE_LANGGRAPH101_CHINOOK},
            disclosure_text=ARTICLE_PROSE_LANGGRAPH101_DISCLOSURE,
            source_markers={"langgraph-101": ["langgraph-101", "langchain-ai"]},
        )
        self.assertEqual(len(report.reuse), 1)
        self.assertEqual(report.undisclosed_reuse, [])

    def test_bare_langchain_brand_mention_alone_would_not_have_sufficed(self):
        # confirms the marker design choice generalizes correctly here too:
        # a disclosure text could easily have said "LangChain" without
        # naming the specific repo, and that must NOT count as disclosed
        bare_mention = "We used LangChain throughout this project."
        self.assertFalse(is_disclosed(bare_mention, ["langgraph-101", "langchain-ai"]))


class TestThirdRealWorldCaseDeepSeekR1OpenR1(unittest.TestCase):
    """A third, independent real-world pair: "Building DeepSeek R1 from
    Scratch" (Fareed Khan) vs. the real reward-function implementations
    in Hugging Face's open-r1 project. Real, measurable n-gram overlap
    (12.3%, 22/179 windows) exists on the repetition-penalty function,
    including the verbatim `raise ValueError(f"max_penalty {max_penalty}
    should not be positive")` line. The repo's own real README.md (lines
    1661-1673) carries an explicit "## Citation" section naming the
    source by project title and URL -- genuine, specific disclosure,
    not a bare brand mention -- so this, like the langgraph-101 case,
    should come back as disclosed reuse, not undisclosed."""

    def test_repetition_penalty_reuse_is_found_by_ngrams(self):
        matches = find_reuse(
            CANDIDATE_DEEPSEEKR1_REPETITION, {"open-r1": REFERENCE_OPENR1_REPETITION}, max_samples=25
        )
        self.assertEqual(len(matches), 1)
        self.assertGreater(matches[0].shared_ngrams, 15)
        self.assertTrue(any("should not be positive" in s for s in matches[0].sample_matches))

    def test_real_citation_names_the_specific_project_and_url(self):
        self.assertTrue(
            is_disclosed(ARTICLE_PROSE_OPENR1_CITATION, ["open-r1", "huggingface/open-r1"])
        )

    def test_full_check_finds_no_undisclosed_reuse(self):
        report = check_provenance(
            candidate_text=CANDIDATE_DEEPSEEKR1_REPETITION,
            references={"open-r1": REFERENCE_OPENR1_REPETITION},
            disclosure_text=ARTICLE_PROSE_OPENR1_CITATION,
            source_markers={"open-r1": ["open-r1", "huggingface/open-r1"]},
        )
        self.assertEqual(len(report.reuse), 1)
        self.assertEqual(report.undisclosed_reuse, [])

    def test_bare_hugging_face_brand_mention_alone_would_not_have_sufficed(self):
        # the design choice generalizes a third time: a disclosure could
        # easily say "Hugging Face" without naming the specific project
        bare_mention = "We used several Hugging Face libraries in this project."
        self.assertFalse(is_disclosed(bare_mention, ["open-r1", "huggingface/open-r1"]))

    def test_ngram_overlap_on_reasoning_steps_is_low_despite_identical_regex(self):
        # the real blind spot this round found: the regex pattern itself
        # is character-for-character identical, but n-gram overlap on
        # the surrounding function is low because the docstrings/comments
        # around it were independently rewritten
        matches = find_reuse(
            CANDIDATE_DEEPSEEKR1_REASONING_STEPS, {"open-r1": REFERENCE_OPENR1_REASONING_STEPS}
        )
        self.assertEqual(len(matches), 1)
        self.assertLess(matches[0].overlap_ratio, 0.05)


class TestFindLiteralTokenReuse(unittest.TestCase):
    """Closes the blind spot found above: `find_reuse()`'s n-gram window
    can't see a single identical token with no internal whitespace (a
    regex pattern, an f-string format literal) once the words around it
    differ. find_literal_token_reuse() checks for those directly,
    against the same real reasoning-steps-reward pair."""

    def test_identical_regex_pattern_is_caught_as_a_literal_token(self):
        matches = find_literal_token_reuse(
            CANDIDATE_DEEPSEEKR1_REASONING_STEPS, {"open-r1": REFERENCE_OPENR1_REASONING_STEPS}
        )
        tokens = {m.token for m in matches}
        self.assertTrue(any("First,|Second,|Next,|Finally," in t for t in tokens))

    def test_short_tokens_below_min_len_are_not_flagged(self):
        matches = find_literal_token_reuse("the cat sat", {"ref": "the cat sat"}, min_len=20)
        self.assertEqual(matches, [])

    def test_unrelated_texts_produce_no_matches(self):
        matches = find_literal_token_reuse(
            "a completely unrelated paragraph about something else entirely",
            {"ref": "nothing in common with the candidate text whatsoever here"},
        )
        self.assertEqual(matches, [])

    def test_extract_literal_tokens_respects_min_len(self):
        tokens = extract_literal_tokens("short ab reallylongtokenabove20chars", min_len=20)
        self.assertEqual(tokens, {"reallylongtokenabove20chars"})


class TestFindBinaryReuse(unittest.TestCase):
    """Images carry no words to fingerprint with find_reuse(), but this
    round's own investigation found 9 of 11 shared-filename diagram
    images between two real repos were byte-identical (sha256) -- the
    fixtures here are small synthetic stand-ins modeling that exact
    shape (same filename + identical bytes vs. same filename + different
    bytes vs. a filename only on one side), stated plainly as synthetic
    rather than committing large real PNGs disproportionate to a test."""

    def setUp(self):
        self.candidate_dir = os.path.join(HERE, "fixtures", "candidate_images")
        self.reference_dir = os.path.join(HERE, "fixtures", "reference_images")

    def test_identical_filename_and_bytes_is_flagged(self):
        matches = find_binary_reuse(self.candidate_dir, {"ref": self.reference_dir})
        matched_files = {m.filename for m in matches}
        self.assertIn("architecture.png", matched_files)

    def test_same_filename_different_bytes_is_not_flagged(self):
        matches = find_binary_reuse(self.candidate_dir, {"ref": self.reference_dir})
        matched_files = {m.filename for m in matches}
        self.assertNotIn("single-step.png", matched_files)

    def test_candidate_only_file_is_not_flagged(self):
        matches = find_binary_reuse(self.candidate_dir, {"ref": self.reference_dir})
        matched_files = {m.filename for m in matches}
        self.assertNotIn("my_own_screenshot.png", matched_files)

    def test_exactly_one_match_found(self):
        matches = find_binary_reuse(self.candidate_dir, {"ref": self.reference_dir})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].filename, "architecture.png")
        self.assertEqual(matches[0].reference_name, "ref")


if __name__ == "__main__":
    unittest.main(verbosity=2)
