"""
Tests for winston_checker.py, including a real discrimination pair: a
deliberately well-built deck (should pass everything that's checkable)
and a deliberately badly-built deck (should fail/warn on every rule it
violates on purpose) -- proving the checks actually discriminate rather
than rubber-stamping everything.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from winston_checker import (
    Deck,
    Slide,
    Status,
    run_all_checks,
    summarize,
    check_opening_promise,
    check_final_slide_not_banned,
    check_final_slide_contributions_style,
    check_last_spoken_words_not_thank_you,
    check_slide_word_counts,
    check_main_idea_repeated,
    check_fence_present,
    check_signposting_present,
    check_question_to_room,
    check_clutter,
    check_five_elements_declared,
)


def findings_by_id(findings):
    return {f.rule_id: f for f in findings}


# ---------------------------------------------------------------------
# A real worked example matching the article's own described demo:
# "a 10-minute 'How I use Claude' talk for my team." The article never
# gives the actual deck content (only screenshots of Claude's output on
# it), so this is this build's own content, modeled on that description,
# not a transcription of anything the article shows -- stated plainly,
# same discipline as every other "the real file/content wasn't
# supplied" precedent in this project.
# ---------------------------------------------------------------------

GOOD_DECK = Deck(
    main_idea="claude turns a vague ask into a finished draft",
    five_elements={
        "symbol": "a half-finished draft turning solid",
        "slogan": "Claude turns a vague ask into a finished draft",
        "surprise": "most of the team thought AI tools only save typing time",
        "salient_idea": "the review time saved, not the draft time",
        "story": "how a Friday-afternoon report got done before the status meeting",
    },
    slides=[
        Slide(
            title="How I use Claude",
            bullets=["By the end you'll know one workflow you can copy this week"],
            notes="By the end of this talk you will know exactly one workflow you can copy this week: "
            "Claude turns a vague ask into a finished draft.",
        ),
        Slide(
            title="Not a typing shortcut",
            bullets=["This isn't about saving typing time"],
            notes="This is not about saving typing time -- that was the first thing, now the second: it's about saving review time.",
        ),
        Slide(
            title="The real idea",
            bullets=["Claude turns a vague ask into a finished draft"],
            notes="The idea I want you to leave with: Claude turns a vague ask into a finished draft. How many of you have rewritten the same status update three times this month?",
            has_logo_or_clutter=False,
        ),
        Slide(
            title="Contributions",
            bullets=[
                "Claude turns a vague ask into a finished draft",
                "One workflow you can copy today",
                "A 10-minute setup, reusable every week",
            ],
            notes="So that's it -- Claude turns a vague ask into a finished draft, and I hope you walk away ready to try it before Friday.",
            has_logo_or_clutter=False,
        ),
    ],
)

BAD_DECK = Deck(
    slides=[
        Slide(
            title="Agenda",
            bullets=["Today I will cover the history of AI, three tools, four workflows, and a Q&A at the end"],
            notes="Today I'm going to walk you through the history of AI, then three tools, then four workflows, then open it up for questions.",
        ),
        Slide(
            title="Background",
            bullets=["this is a very long sentence that just keeps going and going " * 10],  # ~90 words, deliberately > 40
            has_logo_or_clutter=True,
        ),
        Slide(
            title="Thank You",
            bullets=["Questions?"],
            notes="Well, thank you, thank you.",
        ),
    ],
)


class TestGoodDeck(unittest.TestCase):
    """Every rule the good deck was built to satisfy must PASS, not just not-fail."""

    def setUp(self):
        self.findings = findings_by_id(run_all_checks(GOOD_DECK))

    def test_opening_promise_passes(self):
        self.assertEqual(self.findings["opening_promise"].status, Status.PASS)

    def test_final_slide_not_banned_passes(self):
        self.assertEqual(self.findings["final_slide_not_banned"].status, Status.PASS)

    def test_final_slide_contributions_style_passes(self):
        self.assertEqual(self.findings["final_slide_contributions_style"].status, Status.PASS)

    def test_last_words_not_thank_you_passes(self):
        self.assertEqual(self.findings["last_words_not_thank_you"].status, Status.PASS)

    def test_slide_word_counts_passes(self):
        self.assertEqual(self.findings["slide_word_counts"].status, Status.PASS)

    def test_main_idea_repeated_passes(self):
        self.assertEqual(self.findings["main_idea_repeated"].status, Status.PASS)

    def test_fence_present_passes(self):
        self.assertEqual(self.findings["fence_present"].status, Status.PASS)

    def test_signposting_present_passes(self):
        self.assertEqual(self.findings["signposting_present"].status, Status.PASS)

    def test_question_to_room_passes(self):
        self.assertEqual(self.findings["question_to_room"].status, Status.PASS)

    def test_no_clutter_passes(self):
        self.assertEqual(self.findings["no_clutter"].status, Status.PASS)

    def test_five_elements_all_declared_passes(self):
        f = self.findings["five_elements_declared"]
        self.assertEqual(f.status, Status.PASS)
        self.assertIn("5/5", f.detail)


class TestBadDeck(unittest.TestCase):
    """Every rule the bad deck was built to violate must FAIL or WARN, not PASS."""

    def setUp(self):
        self.findings = findings_by_id(run_all_checks(BAD_DECK))

    def test_opening_promise_fails(self):
        self.assertEqual(self.findings["opening_promise"].status, Status.FAIL)

    def test_final_slide_not_banned_fails_on_thank_you(self):
        f = self.findings["final_slide_not_banned"]
        self.assertEqual(f.status, Status.FAIL)
        self.assertIn("Thank You", f.detail)

    def test_final_slide_contributions_style_warns(self):
        self.assertEqual(self.findings["final_slide_contributions_style"].status, Status.WARN)

    def test_last_words_not_thank_you_fails(self):
        self.assertEqual(self.findings["last_words_not_thank_you"].status, Status.FAIL)

    def test_slide_word_counts_fails(self):
        f = self.findings["slide_word_counts"]
        self.assertEqual(f.status, Status.FAIL)
        self.assertIn("slide 2", f.detail)

    def test_main_idea_repeated_not_assessable_when_undeclared(self):
        # BAD_DECK declares no main_idea at all -- an honest gap, not a fail.
        self.assertEqual(self.findings["main_idea_repeated"].status, Status.NOT_ASSESSABLE)

    def test_fence_present_warns(self):
        self.assertEqual(self.findings["fence_present"].status, Status.WARN)

    def test_question_to_room_warns(self):
        self.assertEqual(self.findings["question_to_room"].status, Status.WARN)

    def test_no_clutter_fails(self):
        f = self.findings["no_clutter"]
        self.assertEqual(f.status, Status.FAIL)
        self.assertIn("2", f.detail)  # BAD_DECK's slide index 1 (0-based) displays as slide 2

    def test_five_elements_not_assessable_when_undeclared(self):
        self.assertEqual(self.findings["five_elements_declared"].status, Status.NOT_ASSESSABLE)


class TestIndividualCheckLogic(unittest.TestCase):
    def test_promise_recognizes_multiple_phrasings(self):
        d = Deck(slides=[Slide(title="Intro", notes="You will learn how to do this by the end of the talk.")])
        self.assertEqual(check_opening_promise(d).status, Status.PASS)

    def test_promise_fails_on_bare_agenda(self):
        d = Deck(slides=[Slide(title="Agenda", bullets=["Topic A", "Topic B", "Topic C"])])
        self.assertEqual(check_opening_promise(d).status, Status.FAIL)

    def test_banned_final_title_is_case_and_punctuation_insensitive(self):
        d = Deck(slides=[Slide(title="Intro"), Slide(title="THANK YOU.")])
        self.assertEqual(check_final_slide_not_banned(d).status, Status.FAIL)

    def test_thank_you_mid_talk_is_fine_only_last_words_matter(self):
        # "Thank you to our sponsors" appears, but NOT in the final 60 characters
        # of the LAST slide's notes -- the rule is about the very end of the talk.
        notes = "Thank you to our sponsors for the room. " + ("Let's get started with the real content here. " * 3)
        d = Deck(slides=[Slide(title="Intro", notes=notes), Slide(title="Contributions", notes="And that's the whole idea, in one line.")])
        self.assertEqual(check_last_spoken_words_not_thank_you(d).status, Status.PASS)

    def test_thank_you_only_flagged_in_tail_of_final_slide(self):
        d = Deck(slides=[Slide(title="Contributions", notes="A very long explanation of everything we covered today, and thank you")])
        self.assertEqual(check_last_spoken_words_not_thank_you(d).status, Status.FAIL)

    def test_no_notes_on_final_slide_is_not_assessable(self):
        d = Deck(slides=[Slide(title="Contributions", bullets=["Point one"])])
        self.assertEqual(check_last_spoken_words_not_thank_you(d).status, Status.NOT_ASSESSABLE)

    def test_word_count_custom_threshold(self):
        d = Deck(slides=[Slide(title="X", bullets=["one two three four five"])])
        self.assertEqual(check_slide_word_counts(d, max_words=3).status, Status.FAIL)
        self.assertEqual(check_slide_word_counts(d, max_words=10).status, Status.PASS)

    def test_main_idea_plural_stemming(self):
        d = Deck(
            main_idea="finished drafts",
            slides=[
                Slide(title="Intro", notes="we talk about finished draft quality today"),
                Slide(title="Middle", notes="the finished draft matters most"),
                Slide(title="End", notes="remember: finished draft, every time"),
            ],
        )
        self.assertEqual(check_main_idea_repeated(d).status, Status.PASS)

    def test_main_idea_missing_from_middle_reported_precisely(self):
        d = Deck(
            main_idea="trust the process",
            slides=[
                Slide(title="Intro", notes="trust the process is today's idea"),
                Slide(title="Middle", notes="here is an unrelated case study"),
                Slide(title="End", notes="so, trust the process, always"),
            ],
        )
        f = check_main_idea_repeated(d)
        self.assertEqual(f.status, Status.FAIL)
        self.assertIn("middle", f.detail)
        self.assertNotIn("opening", f.detail)
        self.assertNotIn("closing", f.detail)

    def test_five_elements_rejects_unknown_keys(self):
        d = Deck(slides=[Slide(title="X")], five_elements={"symbol": "x", "punchline": "y"})
        f = check_five_elements_declared(d)
        self.assertEqual(f.status, Status.WARN)
        self.assertIn("punchline", f.detail)

    def test_summarize_counts_match_findings(self):
        findings = run_all_checks(GOOD_DECK)
        counts = summarize(findings)
        self.assertEqual(sum(counts.values()), len(findings))
        self.assertEqual(counts["pass"], sum(1 for f in findings if f.status == Status.PASS))


class TestEmptyDeckHandledCleanly(unittest.TestCase):
    def test_empty_deck_fails_cleanly_not_crash(self):
        d = Deck(slides=[])
        findings = run_all_checks(d)
        self.assertTrue(all(f is not None for f in findings))
        failing = [f for f in findings if f.status == Status.FAIL]
        self.assertTrue(len(failing) >= 2)  # opening_promise and final_slide checks should fail, not crash


if __name__ == "__main__":
    unittest.main(verbosity=2)
