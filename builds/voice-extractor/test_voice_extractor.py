"""
The test that actually matters: a draft written to deliberately match a
reference voice scores high, and a generic/corporate-sounding draft on
the same topic scores low — proving the tool discriminates, not just
that each metric computes a number. Mirrors the discrimination-test
discipline already established in /builds/humanizer/test_patterns.py.

All sample text below is written fresh for this test, not reproduced
from the source video transcripts this build was analyzed from.

Run with:
    python3 -m unittest test_voice_extractor -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from voice_match import score_match
from voice_profile import extract_profile

REFERENCE_VOICE = (
    "I broke the build again. Second time this week, which my teenage "
    "daughter would say is basically a personality trait at this point. "
    "Here's what actually happened: I shipped the config change on a "
    "Friday, because apparently I hate myself. The rollback took four "
    "minutes. The explaining-it-to-the-team took forty."
)

MATCHING_DRAFT = (
    "I broke the deploy pipeline again today. My team watched the whole "
    "thing happen in the group chat. I shipped the config change during "
    "lunch, which in hindsight was not my smartest move. The fix took "
    "five minutes. The standup explanation took twenty."
)

GENERIC_DRAFT = (
    "In today's fast-paced software development landscape, deployment "
    "errors are a common occurrence that development teams must "
    "navigate. It is important to implement robust rollback procedures "
    "to mitigate potential downtime and ensure business continuity for "
    "the organization."
)


class TestExtraction(unittest.TestCase):
    def test_extracts_sentence_and_word_counts(self) -> None:
        profile = extract_profile(REFERENCE_VOICE)
        self.assertEqual(profile.sentence_count, 5)
        self.assertGreater(profile.word_count, 20)

    def test_empty_text_returns_zeroed_profile_not_a_crash(self) -> None:
        profile = extract_profile("")
        self.assertEqual(profile.sentence_count, 0)
        self.assertEqual(profile.avg_sentence_length_words, 0.0)

    def test_contraction_rate_is_real(self) -> None:
        profile = extract_profile("I don't know. I can't tell. It's fine.")
        self.assertGreater(profile.contractions_per_100_words, 0)

    def test_no_contractions_scores_zero_not_a_crash(self) -> None:
        profile = extract_profile("This is a sentence. This is another sentence.")
        self.assertEqual(profile.contractions_per_100_words, 0.0)

    def test_first_person_rate(self) -> None:
        profile = extract_profile("I went to the store. My car broke down. Help me.")
        self.assertGreater(profile.first_person_per_100_words, 0)

    def test_em_dash_detection(self) -> None:
        profile = extract_profile("This is one thing — and this is another.")
        self.assertGreater(profile.em_dashes_per_100_sentences, 0)

    def test_double_hyphen_counted_as_em_dash(self) -> None:
        profile = extract_profile("This is one thing -- and this is another.")
        self.assertGreater(profile.em_dashes_per_100_sentences, 0)

    def test_sentence_starting_conjunction_detected(self) -> None:
        profile = extract_profile("I tried it once. But it broke immediately. So I gave up.")
        self.assertGreater(profile.sentence_starting_conjunction_pct, 0)

    def test_top_openers_excludes_bare_articles(self) -> None:
        profile = extract_profile("The cat sat. The dog ran. The bird flew. A fish swam.")
        openers = [word for word, _ in profile.top_sentence_openers]
        self.assertNotIn("the", openers)
        self.assertNotIn("a", openers)


class TestDiscrimination(unittest.TestCase):
    def test_matching_voice_scores_high(self) -> None:
        reference = extract_profile(REFERENCE_VOICE)
        result = score_match(MATCHING_DRAFT, reference)
        self.assertGreaterEqual(result.overall_score, 0.8, result.per_metric_score)

    def test_generic_voice_scores_lower_than_matching_voice(self) -> None:
        reference = extract_profile(REFERENCE_VOICE)
        matching_result = score_match(MATCHING_DRAFT, reference)
        generic_result = score_match(GENERIC_DRAFT, reference)
        self.assertLess(generic_result.overall_score, matching_result.overall_score)

    def test_generic_voice_gets_real_suggestions(self) -> None:
        reference = extract_profile(REFERENCE_VOICE)
        result = score_match(GENERIC_DRAFT, reference)
        self.assertGreater(len(result.suggestions), 0)
        self.assertIn("more first-person voice (I, my, me)", result.suggestions)
        self.assertIn("shorter sentences", result.suggestions)

    def test_identical_text_scores_perfectly(self) -> None:
        reference = extract_profile(REFERENCE_VOICE)
        result = score_match(REFERENCE_VOICE, reference)
        self.assertEqual(result.overall_score, 1.0)
        self.assertEqual(result.suggestions, ())


class TestCliRoundTrip(unittest.TestCase):
    """Proves extract -> save -> load -> score works as a real file-based
    round trip, not just in-memory function calls."""

    def test_profile_json_round_trips_through_a_real_file(self) -> None:
        import subprocess
        import sys as _sys

        with tempfile.TemporaryDirectory() as tmp:
            sample_path = os.path.join(tmp, "sample.txt")
            profile_path = os.path.join(tmp, "profile.json")
            draft_path = os.path.join(tmp, "draft.txt")

            with open(sample_path, "w", encoding="utf-8") as f:
                f.write(REFERENCE_VOICE)
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write(MATCHING_DRAFT)

            here = os.path.dirname(os.path.abspath(__file__))
            extract_result = subprocess.run(
                [_sys.executable, "voice_extractor.py", "extract", sample_path, "--save", profile_path],
                cwd=here, capture_output=True, text=True, check=True,
            )
            self.assertIn("Saved voice profile", extract_result.stdout)
            self.assertTrue(os.path.exists(profile_path))

            with open(profile_path, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["sentence_count"], 5)

            score_result = subprocess.run(
                [_sys.executable, "voice_extractor.py", "score", draft_path, "--profile", profile_path, "--json"],
                cwd=here, capture_output=True, text=True, check=True,
            )
            payload = json.loads(score_result.stdout)
            self.assertGreaterEqual(payload["overall_score"], 0.8)


if __name__ == "__main__":
    unittest.main()
