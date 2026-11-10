"""
The policy layer — thresholds live here, in plain readable code, never
inside the judge. This is the one rule every source in
/notes/jev-typesafe-judgment-model-analysis.md repeats: Jev (or here,
TrainedJudge) makes the judgment, your code decides what to do with it.

Thresholds below are illustrative teaching values, not tuned against a
production workload — same caveat jevpad's own policy.py states about its
own thresholds. Don't reword a question or retune a threshold to fix one
disliked example; that's overfitting to that example, not a real policy
decision (the source tutorial's own explicit warning).
"""
from __future__ import annotations

LOW_CATEGORY_CONFIDENCE = 0.25
HIGH_DESTRUCTIVE_PROBABILITY = 0.70
HIGH_PRIORITY_SCORE = 1.5


def route(answers: dict) -> dict:
    """answers: {"category": ChoiceAnswer, "destructive": NoulAnswer,
    "priority": ScoreAnswer}. Returns {"route": <tool category name or
    'needs_human'>, "reason": <why>} — the route names match
    /builds/trading-jarvis/jarvis_orchestrator.py's real tool categories
    (signal_pipeline, prop_firm, swamp_decompose, other)."""
    category = answers["category"]
    destructive = answers["destructive"]
    priority = answers["priority"]

    if destructive.probability >= HIGH_DESTRUCTIVE_PROBABILITY:
        return {
            "route": "needs_human",
            "reason": f"high destructive-intent probability ({destructive.probability:.2f})",
        }
    if category.confidence < LOW_CATEGORY_CONFIDENCE:
        return {
            "route": "needs_human",
            "reason": f"low routing confidence (margin {category.confidence:.2f})",
        }
    if priority.score >= HIGH_PRIORITY_SCORE:
        return {
            "route": category.choice,
            "reason": f"urgent (priority {priority.score:.2f}) -> fast-path to {category.choice}",
        }
    return {"route": category.choice, "reason": f"routine -> {category.choice}"}
