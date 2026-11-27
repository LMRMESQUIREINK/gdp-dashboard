"""conversation_grader -- extends brief_grader.py to a short multi-turn
transcript, closing the one gap brief_grader.py's own docstring states
plainly: the real classifier's third signal --

  "...whether the user tends to correct Claude or Claude tends to
  correct the user."

-- needs more than one message, which `grade_brief()` never has. Given
a transcript (a list of {"role": "user"|"assistant", "text": str}
turns), this module counts real correction-language occurrences per
role, with the exact matched snippet as evidence for each, same
discipline as every check in brief_grader.py.

Deliberately NOT a verdict on which balance is "better" -- the real
report never states that a user correcting Claude more (or less) is
itself good or bad, only that the ratio is one of three signals its
own classifier uses. This module reports the real counts and the real
balance; `grade_conversation()`'s caller decides what, if anything, to
do with it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from brief_grader import BriefGrade, CheckResult, _evidence, _first_match, grade_brief

# Patterns for "no, that's not what I meant" / "that's wrong" style
# corrective language -- deliberately distinct from CONSTRAINT_PATTERNS
# (a boundary stated up front) and DONE_PATTERNS (a completion check):
# this is retrospective, pointing at something already said or done.
CORRECTION_PATTERNS = (
    r"\bthat['’]s (not|wrong|incorrect)\b",
    r"\bno[,.]? (that|this) (is|was)n['’]t\b",
    r"\bi meant\b",
    r"\byou (missed|misunderstood|got .{0,15} wrong)\b",
    r"\bactually[,]? (it|that|this) should\b",
    r"\bcorrection[:,]",
    r"\blet me (fix|correct) that\b",
    r"\bmy (mistake|bad|apologies)\b",
    r"\bsorry[,]? (i|that)\b.{0,20}\b(mistake|wrong|error)\b",
    r"\bnot quite\b",
)


@dataclass
class Turn:
    role: str  # "user" or "assistant"
    text: str


@dataclass
class CorrectionBalance:
    user_corrections: list[CheckResult] = field(default_factory=list)
    assistant_corrections: list[CheckResult] = field(default_factory=list)

    @property
    def user_count(self) -> int:
        return len(self.user_corrections)

    @property
    def assistant_count(self) -> int:
        return len(self.assistant_corrections)

    @property
    def balance(self) -> str:
        """Which role's corrective language appeared more often in this
        transcript -- "user", "assistant", or "even" (including the
        real zero-zero case, which is even, not undefined)."""
        if self.user_count > self.assistant_count:
            return "user"
        if self.assistant_count > self.user_count:
            return "assistant"
        return "even"


def check_correction_balance(turns: list[Turn]) -> CorrectionBalance:
    balance = CorrectionBalance()
    for turn in turns:
        match = _first_match(turn.text, CORRECTION_PATTERNS)
        if not match:
            continue
        result = CheckResult(f"{turn.role}_correction", True, _evidence(turn.text, match))
        if turn.role == "user":
            balance.user_corrections.append(result)
        elif turn.role == "assistant":
            balance.assistant_corrections.append(result)
    return balance


@dataclass
class ConversationGrade:
    brief_grade: BriefGrade
    correction_balance: CorrectionBalance


def grade_conversation(turns: list[Turn]) -> ConversationGrade:
    """Grades the first user turn as the brief (via grade_brief(), same
    three checks as a single message), then separately reports the
    correction balance across the WHOLE transcript -- the one real
    classifier signal that genuinely needs more than one message."""
    first_user_turn = next((t for t in turns if t.role == "user"), None)
    brief_text = first_user_turn.text if first_user_turn else ""
    return ConversationGrade(
        brief_grade=grade_brief(brief_text),
        correction_balance=check_correction_balance(turns),
    )


def render(grade: ConversationGrade) -> str:
    from brief_grader import render as render_brief

    lines = [render_brief(grade.brief_grade), "", "Correction balance (across the whole transcript):"]
    cb = grade.correction_balance
    lines.append(f"  user corrections: {cb.user_count}, assistant corrections: {cb.assistant_count} (balance: {cb.balance})")
    for r in cb.user_corrections:
        lines.append(f"    [user correction] \"{r.evidence}\"")
    for r in cb.assistant_corrections:
        lines.append(f"    [assistant correction] \"{r.evidence}\"")
    return "\n".join(lines)


def main() -> None:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Grade a short conversation (JSON list of {role, text} turns) for brief quality "
                    "plus the real correction-balance classifier signal."
    )
    parser.add_argument("file", nargs="?", help="path to a JSON file of turns; omit to read stdin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    turns = [Turn(role=t["role"], text=t["text"]) for t in json.loads(raw)]
    grade = grade_conversation(turns)

    if args.json:
        print(json.dumps({
            "brief": grade.brief_grade.as_dict(),
            "correction_balance": {
                "user_count": grade.correction_balance.user_count,
                "assistant_count": grade.correction_balance.assistant_count,
                "balance": grade.correction_balance.balance,
            },
        }, indent=2))
    else:
        print(render(grade))


if __name__ == "__main__":
    main()
