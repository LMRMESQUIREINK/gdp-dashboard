"""
Demo: route a natural-language query to one of
/builds/trading-jarvis/jarvis_orchestrator.py's real tool categories using
TrainedJudge + the policy layer — the "cheap decision in front of a bunch
of expensive things" pattern repeated across every source in
/notes/jev-typesafe-judgment-model-analysis.md (TypeSafe's own "intent
routing" pattern, the podcast's "AI traffic cop," the "10 levels" video's
level 5 "model, agent, workflow routing"). This never calls the real
jarvis_orchestrator.py (that needs a live Anthropic key this sandbox
doesn't have) — it answers the question one level up: WHICH of that
file's tool categories should handle this query, and how confident is
that pick.

Run with:
    python3 router_demo.py "your query here"
"""
from __future__ import annotations

import sys

from judge.primitives import ChoiceQuestion, NoulQuestion, ScoreQuestion
from judge.judge import TrainedJudge
from judge.policy import route
from training_data import TRAIN

QUESTIONS = {
    "category": ChoiceQuestion(
        instructions="Which RUTHLESS TRADING GOLD tool category should handle this query?",
        options={
            "signal_pipeline": "EODHD/FMP market signal or fundamentals check",
            "prop_firm": "TPT funded-account sizing, drawdown, or pass-probability question",
            "swamp_decompose": "decompose a trading objective into a task tree",
            "other": "none of the above",
        },
    ),
    "destructive": NoulQuestion(
        instructions="Would acting on this query, if auto-executed, do something irreversible "
                      "(deleting data, force-closing positions, wiping history)?",
    ),
    "priority": ScoreQuestion(
        instructions="How urgent is this query?",
        levels=["routine", "elevated", "urgent"],
    ),
}


def ask_and_route(judge: TrainedJudge, query: str) -> dict:
    answers = judge.ask(query, QUESTIONS)
    decision = route(answers)
    return {"query": query, "answers": answers, "decision": decision}


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Check AAPL for a signal and size a position at 1% risk"
    judge = TrainedJudge(TRAIN)
    result = ask_and_route(judge, query)

    cat = result["answers"]["category"]
    des = result["answers"]["destructive"]
    pri = result["answers"]["priority"]

    print(f"query: {query!r}")
    print(f"  category: {cat.choice} (confidence {cat.confidence:.2f}) {cat.probabilities}")
    print(f"  destructive: probability={des.probability:.2f}")
    print(f"  priority: score={pri.score:.2f} (confidence {pri.confidence:.2f}) levels={pri.level_probabilities}")
    print(f"  -> route: {result['decision']['route']} ({result['decision']['reason']})")


if __name__ == "__main__":
    main()
