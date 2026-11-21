"""
winston_checker.py -- a real, mechanical implementation of Patrick
Winston's ("How to Speak," MIT RES.TLL-005) rules for structuring a
talk, applied to a plain-text/structured deck representation.

Built from a pasted Substack article ("The presentation rules MIT
taught its students, turned into a Claude skill," Frank Andrade/
Artificial Corner) describing Winston's rules and a paid Claude skill
implementing them -- the skill itself is paywalled and was never seen,
so nothing here is copied from it. Every rule below was independently
verified against two separate sets of real notes on the actual MIT
lecture before being implemented (see the build's README and
/notes/winston-talk-checker-analysis.md for exactly what was and
wasn't independently confirmed).

Design discipline, matching this project's other scorers
(ten-k-website-grader, agent-readiness-scorecard): every check is
either a real, mechanical check over the deck's own text, or is
explicitly marked NOT_ASSESSABLE rather than faked. Nothing here claims
to judge genuine semantic qualities (is this actually surprising? is
the "symbol" actually memorable?) that only a human audience could
judge -- those are opt-in, self-declared fields the deck author fills
in, checked structurally, never inferred from prose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"  # a softer rule, confirmed as "perhaps better," not absolute
    NOT_ASSESSABLE = "not_assessable"


@dataclass
class Slide:
    title: str = ""
    bullets: list[str] = field(default_factory=list)
    notes: str = ""  # spoken words for this slide, if supplied
    has_logo_or_clutter: bool | None = None  # None = not supplied, honestly unassessed


@dataclass
class Deck:
    slides: list[Slide]
    main_idea: str | None = None  # the deck author's own declared main idea/slogan
    five_elements: dict[str, str] = field(default_factory=dict)
    # ^ opt-in self-report: keys among {"symbol","slogan","surprise",
    # "salient_idea","story"}, values are the deck author's own short
    # description of each -- never inferred from the slide text, since
    # judging whether something is genuinely surprising or memorable
    # isn't something this checker claims to do.


@dataclass
class Finding:
    rule_id: str
    status: Status
    detail: str


BANNED_FINAL_TITLES = {
    "thank you",
    "thanks",
    "questions",
    "questions?",
    "the end",
    "q&a",
    "conclusions",
}

CONTRIBUTIONS_HINTS = ("contribution", "what you now have", "what you leave with")

PROMISE_PATTERNS = [
    re.compile(r"\byou(?:'ll| will)\s+(?:know|learn|leave with|be able to|walk away)", re.I),
    re.compile(r"\bby the end\b.{0,40}\byou\b", re.I),
]

FENCE_PATTERNS = [
    re.compile(r"\bis not\b", re.I),
    re.compile(r"\bnot to be confused with\b", re.I),
    re.compile(r"\bthis isn'?t\b", re.I),
]

SIGNPOST_PATTERNS = [
    re.compile(r"\bthat was\b.{0,60}\bnow\b", re.I),
    re.compile(r"\bfirst\b.{0,40}\bsecond\b.{0,40}\bthird\b", re.I),
    re.compile(r"\bnext\s*(?:,|:)?\s*(?:we'?ll|let'?s)\b", re.I),
]

THANK_YOU_LAST_WORDS = re.compile(r"\bthank(?:s| you)\b", re.I)

MAX_WORDS_PER_SLIDE = 40  # the general "few words, large font" rule, as a word-count proxy


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def check_opening_promise(deck: Deck) -> Finding:
    if not deck.slides:
        return Finding("opening_promise", Status.FAIL, "deck has no slides")
    first = deck.slides[0]
    haystack = " ".join([first.title, " ".join(first.bullets), first.notes])
    if any(p.search(haystack) for p in PROMISE_PATTERNS):
        return Finding("opening_promise", Status.PASS, "opening states what the audience will know/get by the end")
    return Finding(
        "opening_promise",
        Status.FAIL,
        "opening slide/notes don't state a promise of what the audience will know by the end "
        '(looked for phrasing like "you will know/learn/leave with...")',
    )


def check_final_slide_not_banned(deck: Deck) -> Finding:
    if not deck.slides:
        return Finding("final_slide_not_banned", Status.FAIL, "deck has no slides")
    last = deck.slides[-1]
    title_norm = last.title.strip().lower().rstrip(".")
    if title_norm in BANNED_FINAL_TITLES:
        return Finding(
            "final_slide_not_banned",
            Status.FAIL,
            f'final slide title is "{last.title}" -- Winston\'s lecture (per two independent sets of notes) '
            'names exactly this kind of slide ("Thank You"/"Questions?"/"Conclusions"/"The End") as what NOT to end on',
        )
    return Finding("final_slide_not_banned", Status.PASS, f'final slide title "{last.title}" is not one of the banned closers')


def check_final_slide_contributions_style(deck: Deck) -> Finding:
    if not deck.slides:
        return Finding("final_slide_contributions_style", Status.FAIL, "deck has no slides")
    last = deck.slides[-1]
    haystack = (last.title + " " + " ".join(last.bullets)).lower()
    if any(h in haystack for h in CONTRIBUTIONS_HINTS):
        return Finding("final_slide_contributions_style", Status.PASS, "final slide reads as a contributions-style summary")
    # WARN not FAIL: independently verified as "perhaps better," not an absolute rule
    return Finding(
        "final_slide_contributions_style",
        Status.WARN,
        "final slide doesn't obviously read as a contributions-style summary -- recommended, "
        "but one of the two independently-checked secondary sources on the real lecture frames "
        'this as "perhaps better," not an absolute requirement, so this is a warning, not a failure',
    )


def check_last_spoken_words_not_thank_you(deck: Deck) -> Finding:
    if not deck.slides:
        return Finding("last_words_not_thank_you", Status.FAIL, "deck has no slides")
    last_notes = deck.slides[-1].notes.strip()
    if not last_notes:
        return Finding("last_words_not_thank_you", Status.NOT_ASSESSABLE, "no speaker notes supplied for the final slide")
    # Check only the tail of the notes -- the rule is about the LAST words, not whether
    # "thank you" appears anywhere earlier (e.g. thanking collaborators mid-talk is fine).
    tail = last_notes[-60:]
    if THANK_YOU_LAST_WORDS.search(tail):
        return Finding(
            "last_words_not_thank_you",
            Status.FAIL,
            'the final spoken words contain "thank you" -- both independently-checked sets of notes on the '
            "real lecture report Winston discouraging this as the literal last words",
        )
    return Finding("last_words_not_thank_you", Status.PASS, 'final spoken words do not end on "thank you"')


def check_slide_word_counts(deck: Deck, max_words: int = MAX_WORDS_PER_SLIDE) -> Finding:
    overloaded = []
    for i, s in enumerate(deck.slides):
        count = _word_count(s.title) + sum(_word_count(b) for b in s.bullets)
        if count > max_words:
            overloaded.append((i, count))
    if overloaded:
        detail = ", ".join(f"slide {i + 1} ({c} words)" for i, c in overloaded)
        return Finding(
            "slide_word_counts",
            Status.FAIL,
            f"{len(overloaded)} slide(s) exceed {max_words} words (a few words per slide, not full sentences): {detail}",
        )
    return Finding("slide_word_counts", Status.PASS, f"every slide is at or under {max_words} words")


def check_main_idea_repeated(deck: Deck) -> Finding:
    if not deck.main_idea:
        return Finding("main_idea_repeated", Status.NOT_ASSESSABLE, "no main_idea declared for this deck")
    if len(deck.slides) < 3:
        return Finding("main_idea_repeated", Status.NOT_ASSESSABLE, "fewer than 3 slides -- no real start/middle/end to check")

    needle = deck.main_idea.strip().lower()
    stem = needle[:-1] if needle.endswith("s") else needle

    def mentions(s: Slide) -> bool:
        hay = (s.title + " " + " ".join(s.bullets) + " " + s.notes).lower()
        return needle in hay or (len(stem) >= 4 and stem in hay)

    first_hit = mentions(deck.slides[0])
    last_hit = mentions(deck.slides[-1])
    middle_slides = deck.slides[1:-1]
    middle_hit = any(mentions(s) for s in middle_slides)

    missing = []
    if not first_hit:
        missing.append("opening")
    if not middle_hit:
        missing.append("middle")
    if not last_hit:
        missing.append("closing")

    if not missing:
        return Finding("main_idea_repeated", Status.PASS, f'main idea "{deck.main_idea}" appears in opening, middle, and closing')
    return Finding(
        "main_idea_repeated",
        Status.FAIL,
        f'main idea "{deck.main_idea}" is missing from: {", ".join(missing)} '
        "-- Winston's rule (confirmed across multiple independent summaries) is to say it three times "
        "so whoever drifted off the first time catches it later",
    )


def check_fence_present(deck: Deck) -> Finding:
    for s in deck.slides:
        hay = s.title + " " + " ".join(s.bullets) + " " + s.notes
        if any(p.search(hay) for p in FENCE_PATTERNS):
            return Finding("fence_present", Status.PASS, "a 'fence' statement (what the idea is NOT) was found")
    return Finding(
        "fence_present",
        Status.WARN,
        "no 'fence' statement found (saying what your idea is NOT, so it isn't confused with something "
        "the audience already knows) -- a named technique in the real lecture, implemented as a warning "
        "since whether it's needed depends on how novel the idea actually is, which this checker can't judge",
    )


def check_signposting_present(deck: Deck) -> Finding:
    for s in deck.slides:
        hay = s.title + " " + " ".join(s.bullets) + " " + s.notes
        if any(p.search(hay) for p in SIGNPOST_PATTERNS):
            return Finding("signposting_present", Status.PASS, "signpost language found between sections")
    return Finding(
        "signposting_present",
        Status.WARN,
        'no signpost language found (e.g. "that was the first thing, now the second...") to help '
        "anyone who drifted off get back on track",
    )


def check_question_to_room(deck: Deck) -> Finding:
    for s in deck.slides:
        if "?" in s.notes:
            return Finding("question_to_room", Status.PASS, "a question to the audience was found in the speaker notes")
    return Finding(
        "question_to_room",
        Status.WARN,
        "no question mark found in any slide's speaker notes -- Winston's lecture asks for one real "
        "question to the room per talk; this checker can't judge whether a question elsewhere in the "
        "deck is addressed to the room vs. rhetorical, so this is a warning, not a hard failure",
    )


def check_clutter(deck: Deck) -> Finding:
    assessed = [s for s in deck.slides if s.has_logo_or_clutter is not None]
    if not assessed:
        return Finding(
            "no_clutter",
            Status.NOT_ASSESSABLE,
            "no slide supplied a has_logo_or_clutter flag -- this checker works from a plain-text deck "
            "representation and can't see a slide's actual visual design; this check needs that field "
            "filled in by hand (or a future version that reads a real .pptx) to mean anything",
        )
    cluttered = [i for i, s in enumerate(deck.slides) if s.has_logo_or_clutter]
    if cluttered:
        return Finding(
            "no_clutter",
            Status.FAIL,
            f"{len(cluttered)} slide(s) flagged with a logo/clutter/background decoration: "
            f"{', '.join(str(i + 1) for i in cluttered)}",
        )
    return Finding("no_clutter", Status.PASS, "no slide was flagged with logo/clutter/background decoration")


def check_five_elements_declared(deck: Deck) -> Finding:
    known = {"symbol", "slogan", "surprise", "salient_idea", "story"}
    declared = set(deck.five_elements.keys()) & known
    unknown = set(deck.five_elements.keys()) - known
    if unknown:
        return Finding(
            "five_elements_declared",
            Status.WARN,
            f"unrecognized key(s) in five_elements: {sorted(unknown)} (expected a subset of {sorted(known)})",
        )
    if not declared:
        return Finding(
            "five_elements_declared",
            Status.NOT_ASSESSABLE,
            "no five_elements declared -- Winston's lecture names Symbol/Slogan/Surprise/Salient idea/Story "
            "as what makes a talk memorable, confirmed by two independent sets of real lecture notes; whether "
            "a given slogan is actually surprising or memorable isn't something this checker judges, so it's "
            "an opt-in, self-declared field, never inferred from the slide text",
        )
    missing = known - declared
    status = Status.PASS if not missing else Status.WARN
    detail = f"{len(declared)}/5 elements declared: {sorted(declared)}"
    if missing:
        detail += f" -- not declared: {sorted(missing)}"
    return Finding("five_elements_declared", status, detail)


ALL_CHECKS = [
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
]


def run_all_checks(deck: Deck) -> list[Finding]:
    return [check(deck) for check in ALL_CHECKS]


def summarize(findings: list[Finding]) -> dict:
    counts = {s: 0 for s in Status}
    for f in findings:
        counts[f.status] += 1
    return {s.value: counts[s] for s in Status}
