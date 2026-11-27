"""
Tool-group shortlisting — adapted from the source article's
toolkit/shortlist.py. The mechanism (a cheap regex scorer per group, a
clear-winner-takes-all vs. top-N fallback) is what's reused; the SIGNALS
table itself is specific to whatever tool groups a real agent registers
(Photoshop/Blender/Slack for the article's 118-program Windows agent;
nothing of the kind exists in this toolkit's demo), so it's a parameter
here rather than a hardcoded module-level dict.
"""
from __future__ import annotations

import re


def score_groups(message: str, signals: dict[str, list[tuple[str, float]]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for group, sigs in signals.items():
        hits = sorted((weight for pattern, weight in sigs if re.search(pattern, message, re.I)), reverse=True)
        if hits:
            scores[group] = hits[0] + 0.5 * (len(hits) - 1)
    return scores


def shortlist_groups(message: str, signals: dict[str, list[tuple[str, float]]],
                      min_score: float = 5.0, min_lead: float = 1.5,
                      top_n_fallback: int = 3) -> list[str]:
    """A single group wins outright if it scores at least min_score and
    leads the next group by at least min_lead; otherwise the top
    top_n_fallback groups all go in, same as the article's rule."""
    scores = score_groups(message, signals)
    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if len(ranked) == 1 or (ranked[0][1] >= min_score and ranked[0][1] - ranked[1][1] >= min_lead):
        return [ranked[0][0]]
    return [g for g, _ in ranked[:top_n_fallback]]
