"""
Proves the detector discriminates — the thing that actually matters for a
tool like this, not just that each regex matches in isolation. A real
AI-sounding paragraph (deliberately stacking tells this project and the
source article both name) must score high; a real plain, human-sounding
paragraph (an engineer describing an actual bug fix) must score at or near
zero. Also unit-tests each rule individually so a future edit that breaks
one doesn't hide behind the aggregate score.

Run with:
    python3 -m unittest test_patterns -v
"""
from __future__ import annotations

import unittest

from patterns import em_dash_density, scan, score

AI_SOUNDING_PARAGRAPH = (
    "In today's fast-paced digital world, it's important to note that "
    "businesses need to leverage cutting-edge solutions to stay ahead. "
    "Let's dive into how our platform can help you unlock your true potential. "
    "It's not just a tool, it's a game-changer. Whether you're a beginner or "
    "an expert, our seamless, robust platform will revolutionize the way you work. "
    "Moreover, our holistic approach will truly, really transform your workflow. "
    "In conclusion, delve into the world of possibilities today."
)

HUMAN_SOUNDING_PARAGRAPH = (
    "We shipped the login fix Tuesday. It turned out the session cookie was "
    "being cleared on every redirect, not only on logout. Two lines fixed it. "
    "We added a test so it doesn't come back."
)


class TestDiscrimination(unittest.TestCase):
    def test_ai_sounding_paragraph_scores_high(self) -> None:
        result = score(AI_SOUNDING_PARAGRAPH)
        self.assertGreaterEqual(result["finding_count"], 10, result["findings"])

    def test_human_sounding_paragraph_scores_at_or_near_zero(self) -> None:
        result = score(HUMAN_SOUNDING_PARAGRAPH)
        self.assertEqual(result["finding_count"], 0, result["findings"])

    def test_ai_paragraph_hits_multiple_categories_not_one_rule_repeated(self) -> None:
        result = score(AI_SOUNDING_PARAGRAPH)
        self.assertGreaterEqual(len(result["by_category"]), 4, result["by_category"])


class TestIndividualRules(unittest.TestCase):
    def test_filler_opener(self) -> None:
        findings = scan("In today's fast-paced world, let's dive into the details.")
        names = {f.rule_name for f in findings}
        self.assertIn("filler-opener", names)

    def test_throat_clearing_note(self) -> None:
        findings = scan("It's important to note that the server restarted.")
        self.assertEqual(findings[0].rule_name, "throat-clearing-note")

    def test_false_contrast_triplet(self) -> None:
        findings = scan("It's not just a feature, it's a philosophy.")
        names = {f.rule_name for f in findings}
        self.assertIn("false-contrast-triplet", names)

    def test_buzzwords(self) -> None:
        findings = scan("We need to leverage our robust, seamless, cutting-edge platform.")
        names = {f.rule_name for f in findings}
        self.assertIn("buzzword", names)
        buzzword_matches = {f.matched_text.lower() for f in findings if f.rule_name == "buzzword"}
        self.assertTrue({"leverage", "robust", "seamless", "cutting-edge"} <= buzzword_matches)

    def test_whether_youre_cliche(self) -> None:
        findings = scan("Whether you're a beginner or an expert, this works.")
        names = {f.rule_name for f in findings}
        self.assertIn("whether-youre-cliche", names)

    def test_stacked_transitions(self) -> None:
        findings = scan("Moreover, this matters a lot.")
        names = {f.rule_name for f in findings}
        self.assertIn("stacked-transitions", names)

    def test_plain_transition_word_alone_is_not_flagged(self) -> None:
        # A bare "moreover" with no comma immediately after (not the stacked
        # sentence-opener pattern) should not be flagged — a real edge case
        # worth pinning down rather than over-matching.
        findings = scan("We considered that option, and moreover it was cheaper.")
        names = {f.rule_name for f in findings}
        self.assertNotIn("stacked-transitions", names)

    def test_delve_into(self) -> None:
        findings = scan("Let's delve into the quarterly numbers.")
        names = {f.rule_name for f in findings}
        self.assertIn("delve-into", names)

    def test_stacked_intensifier_with_comma(self) -> None:
        findings = scan("This will truly, really help.")
        names = {f.rule_name for f in findings}
        self.assertIn("stacked-intensifier", names)

    def test_ordinary_not_just_without_its_is_not_flagged(self) -> None:
        # The false-contrast rule should catch the "It's not just X, it's Y"
        # construction specifically, not any sentence containing "not just".
        findings = scan("The fix touched two files, not just the one we expected.")
        names = {f.rule_name for f in findings}
        self.assertNotIn("false-contrast-triplet", names)


class TestEmDashDensity(unittest.TestCase):
    def test_zero_dashes_in_plain_text(self) -> None:
        self.assertEqual(em_dash_density("No dashes in this sentence at all."), 0.0)

    def test_density_scales_with_dash_count(self) -> None:
        ten_words = "one two three four five six seven eight nine ten"
        one_dash = f"{ten_words} — end"
        self.assertGreater(em_dash_density(one_dash), 0.0)


if __name__ == "__main__":
    unittest.main()
