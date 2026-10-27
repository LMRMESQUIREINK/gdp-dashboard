"""
TrainedJudge — a real implementation of the Jev contract (state + typed
questions in, calibrated-probability answers out), backed by a real
trained classifier instead of Jev's closed transformer.

HONEST SCOPE, stated rather than hidden (full reasoning in
/notes/jev-typesafe-judgment-model-analysis.md and this build's README):
Jev's actual mechanism — a language model reading a question's criteria in
natural language and scoring a restricted softmax over declared answer
tokens, with no training needed per question — cannot be reproduced here.
Reproducing that for real (as one of the source articles did on an open
model) needs a downloaded pretrained transformer; this sandbox's network
policy returns a real HTTP 403 for huggingface.co (checked directly, not
assumed — same egress restriction already documented for Yahoo Finance,
EODHD, FMP and the Anthropic API in every other build in this project).

So TrainedJudge is a genuinely different, much simpler kind of model: a
TF-IDF + logistic-regression classifier, trained per question from a small
labeled example set (see training_data.py), with no built-in semantic
understanding of a question's wording — it only knows the labeled examples
it was shown. What IS faithfully reproduced is the *contract*: probabilities
restricted to exactly the declared answer space (logistic regression's
own softmax/sigmoid output already only ever covers the classes it was
fit on — the same "restricted softmax" idea, just over a simpler model),
a margin-based confidence for Choice and Score, a probability-weighted
average for Score, and no confidence field at all for Noul — matching
TypeSafe's own documented answer shapes exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .primitives import ChoiceQuestion, NoulQuestion, ScoreQuestion

Question = Union[ChoiceQuestion, NoulQuestion, ScoreQuestion]


@dataclass
class ChoiceAnswer:
    choice: str
    probabilities: dict[str, float]
    confidence: float  # margin: top probability minus the runner-up's


@dataclass
class NoulAnswer:
    probability: float  # no confidence field — matches TypeSafe's own Noul shape


@dataclass
class ScoreAnswer:
    score: float  # probability-weighted average across levels, 0..len(levels)-1
    level_probabilities: list[float]
    confidence: float  # same margin definition as ChoiceAnswer


def _margin(probabilities: list[float]) -> float:
    """Confidence as the gap between the best answer and its closest
    rival — the definition the source analysis's most rigorous article
    uses, not the raw winning probability by itself. A 0.52 winner next
    to a 0.46 runner-up is a near coin flip even though 0.52 'won.'"""
    ranked = sorted(probabilities, reverse=True)
    if len(ranked) < 2:
        return 1.0
    return ranked[0] - ranked[1]


class TrainedJudge:
    """One classifier per named question, trained once at construction
    from `training_examples`: a list of dicts with a "text" key and one
    key per question name holding that example's label for that question
    (a Noul's label is "yes"/"no"; a Score's label is an integer level
    index). Mirrors Jev's real request shape at ask() time: `ask(state,
    questions)` takes a dict of {name: Question} and returns a dict of
    {name: Answer}, one entry per question, from a single pass of the
    already-trained models (no retraining per call — the "single pass"
    property is real here too, just over a much smaller model)."""

    def __init__(self, training_examples: list[dict]):
        self._texts = [ex["text"] for ex in training_examples]
        self._raw_examples = training_examples
        self._pipelines: dict[str, Pipeline] = {}

    def _pipeline_for(self, question_name: str) -> Pipeline:
        if question_name not in self._pipelines:
            labels = [ex[question_name] for ex in self._raw_examples]
            # C=20 and class_weight="balanced" were picked by hand against
            # this training set (see test_judge.py's confidence checks) —
            # the regularization strength that lets a tiny TF-IDF model
            # commit confidently on clear-cut examples without being so
            # unregularized it memorizes noise. Not a universal default;
            # retune if the training set changes materially.
            pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
                ("clf", LogisticRegression(max_iter=3000, C=20.0, class_weight="balanced")),
            ])
            pipeline.fit(self._texts, labels)
            self._pipelines[question_name] = pipeline
        return self._pipelines[question_name]

    def ask(self, state: str, questions: dict[str, Question]) -> dict[str, object]:
        answers: dict[str, object] = {}
        for name, question in questions.items():
            pipeline = self._pipeline_for(name)
            proba = pipeline.predict_proba([state])[0]
            classes = list(pipeline.named_steps["clf"].classes_)

            if isinstance(question, ChoiceQuestion):
                prob_by_option = {str(c): float(p) for c, p in zip(classes, proba)}
                for option in question.options:
                    prob_by_option.setdefault(option, 0.0)
                choice = max(prob_by_option, key=prob_by_option.get)
                answers[name] = ChoiceAnswer(
                    choice=choice,
                    probabilities=prob_by_option,
                    confidence=_margin(list(prob_by_option.values())),
                )
            elif isinstance(question, NoulQuestion):
                yes_index = classes.index("yes") if "yes" in classes else None
                probability = float(proba[yes_index]) if yes_index is not None else 0.0
                answers[name] = NoulAnswer(probability=probability)
            elif isinstance(question, ScoreQuestion):
                n_levels = len(question.levels)
                level_probs = [0.0] * n_levels
                for c, p in zip(classes, proba):
                    level_probs[int(c)] = float(p)
                score = sum(i * p for i, p in enumerate(level_probs))
                answers[name] = ScoreAnswer(
                    score=score, level_probabilities=level_probs,
                    confidence=_margin(level_probs),
                )
            else:
                raise TypeError(f"unknown question type for {name!r}: {type(question)}")
        return answers
