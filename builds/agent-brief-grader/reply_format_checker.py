"""reply_format_checker -- the "session habit" companion to
brief_grader.py/conversation_grader.py: checks an AGENT'S OWN reply
(not the human's brief) against Habit 3 from the same source listicle
("Anthropic's Latest Study Reveals How the Top 1% Use AI"), which this
project's own real, checked analysis
(/notes/anthropic-claude-usage-habits-analysis.md) traced to a real
October 2026 Anthropic internal workforce report: interactive sessions
spend ~80% of their time waiting for a human to respond, so the
listicle's own prescription is a fixed reply order --

  1. anything needed from the human (a decision, an approval)
  2. whether the task is actually finished
  3. a short summary of what was done
  4. what went wrong, if anything did

-- so a human skimming a reply hits the thing they need to act on
FIRST, not buried at the end. This module checks REAL ORDER, not just
presence: a reply that mentions "done" after its summary, when nothing
needed from the human came first, is checked for whether the sections
that DO appear come in the right relative sequence -- a reply that
never needed anything from the human, or never hit a problem, isn't
penalized for a section that genuinely had nothing to say.

Every finding carries the real matched text and its real character
position as evidence -- no score with no evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

NEEDS_FROM_YOU_PATTERNS = (
    r"\bneeds? (from|input) you\b",
    r"\bbefore (i|we) (continue|proceed)\b",
    r"\bcan you (confirm|approve|decide|clarify)\b",
    r"\bwaiting on you\b",
    r"\bblocking on you\b",
    r"\byour (call|decision|approval) (is )?needed\b",
)

DONE_STATUS_PATTERNS = (
    r"\bdone\.\s",
    r"\bnot done yet\b",
    r"\bstill (in progress|working)\b",
    r"\bfinished\b",
    r"\bcomplete[d]?\.\s",
    r"\ball (checks|tests) pass",
)

SUMMARY_PATTERNS = (
    r"\bsummary\b",
    r"\bin short\b",
    r"\bto recap\b",
    r"\bwhat (i|we) did\b",
    r"\bhere'?s what changed\b",
)

WHAT_WENT_WRONG_PATTERNS = (
    r"\bwhat went wrong\b",
    r"\bcouldn'?t (open|reach|access|run)\b",
    r"\bskipped\b",
    r"\bfailed to\b",
    r"\bone (real )?(bug|issue|problem) (found|remains)\b",
    r"\bnot (yet )?(verified|proven|tested)\b",
)

SECTION_ORDER = ("needs_from_you", "done_status", "summary", "what_went_wrong")
_PATTERNS_BY_SECTION = {
    "needs_from_you": NEEDS_FROM_YOU_PATTERNS,
    "done_status": DONE_STATUS_PATTERNS,
    "summary": SUMMARY_PATTERNS,
    "what_went_wrong": WHAT_WENT_WRONG_PATTERNS,
}


@dataclass
class SectionFinding:
    section: str
    present: bool
    position: Optional[int] = None
    evidence: Optional[str] = None


@dataclass
class ReplyFormatGrade:
    findings: list[SectionFinding] = field(default_factory=list)

    @property
    def present_in_order(self) -> list[SectionFinding]:
        return [f for f in self.findings if f.present]

    @property
    def follows_order(self) -> bool:
        """True iff every section that's actually present in the reply
        appears in the prescribed relative order. A reply with only
        some of the four sections isn't penalized for the missing
        ones -- "no problem" genuinely has nothing to put under
        what-went-wrong, and a reply that never needed anything from
        the human has nothing to put under needs_from_you."""
        present = self.present_in_order
        positions = [f.position for f in present]
        return positions == sorted(positions)

    @property
    def out_of_order(self) -> list[tuple[SectionFinding, SectionFinding]]:
        """Every adjacent (in SECTION_ORDER) pair of present sections
        that appears in the WRONG relative order in the real text."""
        present = self.present_in_order
        violations = []
        for i in range(len(present) - 1):
            if present[i].position > present[i + 1].position:
                violations.append((present[i], present[i + 1]))
        return violations


def _first_match(text: str, patterns: tuple[str, ...]):
    best = None
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and (best is None or m.start() < best.start()):
            best = m
    return best


def grade_reply_format(text: str) -> ReplyFormatGrade:
    grade = ReplyFormatGrade()
    for section in SECTION_ORDER:
        match = _first_match(text, _PATTERNS_BY_SECTION[section])
        if match:
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            grade.findings.append(SectionFinding(section, True, match.start(), text[start:end].replace("\n", " ")))
        else:
            grade.findings.append(SectionFinding(section, False))
    return grade


def render(grade: ReplyFormatGrade) -> str:
    lines = [f"Reply format: {'FOLLOWS the fixed order' if grade.follows_order else 'OUT OF ORDER'}"]
    for f in grade.findings:
        if f.present:
            lines.append(f"  [PRESENT @ {f.position}] {f.section} -- \"{f.evidence}\"")
        else:
            lines.append(f"  [absent]  {f.section}")
    for earlier, later in grade.out_of_order:
        lines.append(
            f"  OUT OF ORDER: '{later.section}' (pos {later.position}) appears before "
            f"'{earlier.section}' (pos {earlier.position}), which should come first"
        )
    return "\n".join(lines)


def main() -> None:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Check a reply's text against the fixed needs/done/summary/wrong order.")
    parser.add_argument("file", nargs="?")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    grade = grade_reply_format(text)
    if args.json:
        print(json.dumps({
            "follows_order": grade.follows_order,
            "findings": [
                {"section": f.section, "present": f.present, "position": f.position, "evidence": f.evidence}
                for f in grade.findings
            ],
        }, indent=2))
    else:
        print(render(grade))


if __name__ == "__main__":
    main()
