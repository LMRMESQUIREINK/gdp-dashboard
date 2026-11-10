"""
Extracts a quantifiable, reusable voice profile from a real sample of
someone's own writing — built from the tone.md/humor.md technique in one
of the three uploaded WordPress-via-Claude tutorials ("How I Built INSANE
WordPress Websites In 20 Minutes"), which pastes a real passage and has
Claude "decode" it into a style guide. This builds the measurable half of
that idea: real signals extracted by counting, not a vague prescriptive
rule set invented from nothing.

Dependency-free, same discipline as every other text-pattern tool in this
project (humanizer, pseo_guard): plain regex and arithmetic, no NLP
library. Sentence/word splitting is a documented, honest approximation —
see `_split_sentences()` — not a claim of linguistic correctness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
_WORD_PATTERN = re.compile(r"[A-Za-z']+")
_CONTRACTION_PATTERN = re.compile(r"\b\w+'(?:t|re|ve|ll|d|s|m)\b", re.IGNORECASE)
_FIRST_PERSON_PATTERN = re.compile(r"\b(I|me|my|mine|myself)\b")
_EM_DASH_PATTERN = re.compile(r"[—–]|--")
_SENTENCE_STARTING_CONJUNCTION = re.compile(
    r"^(and|but|so|because|or|yet)\b", re.IGNORECASE
)
_STOPWORD_OPENERS = frozenset({"the", "a", "an"})


def _split_sentences(text: str) -> list[str]:
    """A regex-based approximation, not a real sentence tokenizer: splits
    on .!? followed by whitespace and a capital letter, digit, or quote.
    Known, accepted failure modes — stated plainly rather than hidden:
    "Mr. Smith arrived." splits after "Mr." (an abbreviation, not a real
    sentence end); "3.14 is pi." does not split on the decimal point
    (digits after the period don't match the capital/digit/quote
    lookahead in the way an abbreviation's capital letter does, so this
    one is usually fine); a sentence ending a paragraph with no trailing
    punctuation is dropped. Good enough for the statistical signals
    below, which average over many sentences and aren't sensitive to a
    few mis-split edge cases — not good enough for anything that needs
    exact sentence boundaries."""
    text = text.strip()
    if not text:
        return []
    parts = _SENTENCE_END.split(text)
    return [p.strip() for p in parts if p.strip()]


def _words(text: str) -> list[str]:
    return _WORD_PATTERN.findall(text)


@dataclass(frozen=True)
class VoiceProfile:
    sentence_count: int
    word_count: int
    avg_sentence_length_words: float
    avg_word_length_chars: float
    contractions_per_100_words: float
    first_person_per_100_words: float
    exclamations_per_100_sentences: float
    questions_per_100_sentences: float
    em_dashes_per_100_sentences: float
    sentence_starting_conjunction_pct: float
    top_sentence_openers: tuple[tuple[str, int], ...]


def extract_profile(text: str, top_openers: int = 5) -> VoiceProfile:
    sentences = _split_sentences(text)
    words = _words(text)
    word_count = len(words)
    sentence_count = len(sentences)

    if sentence_count == 0 or word_count == 0:
        return VoiceProfile(
            sentence_count=0,
            word_count=0,
            avg_sentence_length_words=0.0,
            avg_word_length_chars=0.0,
            contractions_per_100_words=0.0,
            first_person_per_100_words=0.0,
            exclamations_per_100_sentences=0.0,
            questions_per_100_sentences=0.0,
            em_dashes_per_100_sentences=0.0,
            sentence_starting_conjunction_pct=0.0,
            top_sentence_openers=(),
        )

    avg_sentence_length = word_count / sentence_count
    avg_word_length = sum(len(w) for w in words) / word_count

    contractions = len(_CONTRACTION_PATTERN.findall(text))
    first_person = len(_FIRST_PERSON_PATTERN.findall(text))
    exclamations = text.count("!")
    questions = text.count("?")
    em_dashes = len(_EM_DASH_PATTERN.findall(text))

    starting_conjunctions = sum(
        1 for s in sentences if _SENTENCE_STARTING_CONJUNCTION.match(s)
    )

    opener_counts: dict[str, int] = {}
    for s in sentences:
        first_word_match = _WORD_PATTERN.search(s)
        if not first_word_match:
            continue
        opener = first_word_match.group(0).lower()
        if opener in _STOPWORD_OPENERS:
            continue
        opener_counts[opener] = opener_counts.get(opener, 0) + 1
    top = tuple(sorted(opener_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_openers])

    return VoiceProfile(
        sentence_count=sentence_count,
        word_count=word_count,
        avg_sentence_length_words=round(avg_sentence_length, 2),
        avg_word_length_chars=round(avg_word_length, 2),
        contractions_per_100_words=round(contractions / word_count * 100, 2),
        first_person_per_100_words=round(first_person / word_count * 100, 2),
        exclamations_per_100_sentences=round(exclamations / sentence_count * 100, 2),
        questions_per_100_sentences=round(questions / sentence_count * 100, 2),
        em_dashes_per_100_sentences=round(em_dashes / sentence_count * 100, 2),
        sentence_starting_conjunction_pct=round(starting_conjunctions / sentence_count * 100, 2),
        top_sentence_openers=top,
    )
