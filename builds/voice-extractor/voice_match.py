"""
Scores how closely a draft's own voice profile matches a reference
profile extracted earlier — the second half of the tone-file technique:
not just extracting a style guide, but actually checking a new draft
against it, the way `humanizer.py`'s `--max-per-1000-words` turns a style
rule into a real pass/fail gate instead of a guideline to remember.
"""

from __future__ import annotations

from dataclasses import dataclass

from voice_profile import VoiceProfile, extract_profile

# Each metric's tolerance: how much absolute difference before a draft
# stops reading as "the same voice" on that one signal. Fixed, declared
# constants rather than a value derived from the reference text itself —
# a relative-difference scheme was tried first and rejected for a real,
# tested reason: on short samples, a rare-event metric (first-person use,
# em dashes) near zero in the reference turns any nonzero draft value into
# a maximal penalty, which doesn't reflect real stylistic distance. See
# this build's README for the test that caught it.
_METRIC_TOLERANCES: dict[str, float] = {
    "avg_sentence_length_words": 8.0,
    "avg_word_length_chars": 1.5,
    "contractions_per_100_words": 6.0,
    "first_person_per_100_words": 6.0,
    "exclamations_per_100_sentences": 40.0,
    "questions_per_100_sentences": 40.0,
    "em_dashes_per_100_sentences": 40.0,
    "sentence_starting_conjunction_pct": 40.0,
}
_METRICS = tuple(_METRIC_TOLERANCES.keys())

# (suggestion when the draft has LESS of this than the reference,
#  suggestion when the draft has MORE of this than the reference)
_SUGGESTIONS = {
    "avg_sentence_length_words": ("longer sentences", "shorter sentences"),
    "avg_word_length_chars": ("more complex vocabulary", "simpler, shorter words"),
    "contractions_per_100_words": ("more contractions (don't, it's, I've)", "fewer contractions"),
    "first_person_per_100_words": ("more first-person voice (I, my, me)", "less first-person voice"),
    "exclamations_per_100_sentences": ("more exclamation points", "fewer exclamation points"),
    "questions_per_100_sentences": ("more rhetorical questions", "fewer questions"),
    "em_dashes_per_100_sentences": ("more em-dash asides", "fewer em-dash asides"),
    "sentence_starting_conjunction_pct": (
        "start more sentences with And/But/So",
        "start fewer sentences with And/But/So",
    ),
}

# A per-metric score below this is treated as a real mismatch worth
# surfacing as a suggestion; above it is close enough not to nag about.
_SUGGESTION_THRESHOLD_SCORE = 0.85


@dataclass(frozen=True)
class MatchResult:
    overall_score: float
    per_metric_score: dict[str, float]
    suggestions: tuple[str, ...]
    draft_profile: VoiceProfile


def _metric_score(reference_value: float, draft_value: float, tolerance: float) -> float:
    """1.0 at an exact match, falling off linearly to 0.0 once the
    absolute difference reaches this metric's tolerance."""
    diff = abs(reference_value - draft_value)
    return max(0.0, 1.0 - diff / tolerance)


def score_match(draft_text: str, reference: VoiceProfile) -> MatchResult:
    draft_profile = extract_profile(draft_text)

    per_metric: dict[str, float] = {}
    suggestions: list[str] = []

    for metric in _METRICS:
        reference_value = getattr(reference, metric)
        draft_value = getattr(draft_profile, metric)
        score = _metric_score(reference_value, draft_value, _METRIC_TOLERANCES[metric])
        per_metric[metric] = round(score, 3)

        if score < _SUGGESTION_THRESHOLD_SCORE:
            draft_has_less, draft_has_more = _SUGGESTIONS[metric]
            suggestions.append(draft_has_less if draft_value < reference_value else draft_has_more)

    overall = sum(per_metric.values()) / len(per_metric) if per_metric else 0.0

    return MatchResult(
        overall_score=round(overall, 3),
        per_metric_score=per_metric,
        suggestions=tuple(suggestions),
        draft_profile=draft_profile,
    )
