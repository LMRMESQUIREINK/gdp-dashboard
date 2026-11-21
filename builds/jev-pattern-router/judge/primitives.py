"""
The three question types, matching TypeSafe's documented Jev primitives
(see /notes/jev-typesafe-judgment-model-analysis.md): Choice, Noul, Score.
Each declares its own answer space up front — the real mechanism this
project's analysis verified (restricted softmax over only the declared
labels) only works because the caller commits to that answer space before
asking, and these dataclasses are where that commitment lives.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChoiceQuestion:
    """Pick one of `options`. instructions is the question itself;
    each option name maps to a short description — the description is
    where you draw the boundary between two options that overlap, same
    as TypeSafe's own documented guidance."""
    instructions: str
    options: dict[str, str]


@dataclass
class NoulQuestion:
    """A yes/no judgment. TypeSafe's own name for this primitive — a
    Noul never returns a confidence, only a probability of yes, since
    the probability itself already carries that information (0.5 means
    genuinely uncertain, not 'medium')."""
    instructions: str
    criteria: str = ""


@dataclass
class ScoreQuestion:
    """A position on an ordered scale. `levels` lists each rung's
    description, numbered 0..len(levels)-1 in the order given — the
    answer is the probability-weighted average across every rung, not
    just the top pick, exactly as TypeSafe documents it."""
    instructions: str
    levels: list[str]
