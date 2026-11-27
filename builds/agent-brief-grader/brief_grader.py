"""agent-brief-grader -- checks a single agent-directed brief/prompt (the
text a person is about to send Claude, Claude Code, or any other agent)
for the textual signals Anthropic's own "Agentic coding and persistent
returns to expertise" report (published 2026-06-16, ~400,000 Claude Code
sessions from ~235,000 people) says its expertise classifier actually
looks for -- NOT a vibe check, a report built from three real, quoted
signals:

  "The expertise classifier looks for three signals: how precisely the
  user frames their directions, what they ask Claude to verify, and
  whether the user tends to correct Claude or Claude tends to correct
  the user."

Only the first two are checkable from a single brief's text alone (the
third needs a multi-turn transcript, which this module never has) --
stated honestly rather than faked. This module checks three concrete,
evidenced components of a brief, plus one informational-only flag it
can't fully verify:

  - WHY        a stated reason, so Claude has something to steer small
               judgment calls by.
  - CONSTRAINTS a stated boundary/off-limits.
  - DONE        a stated way to tell the work is finished, and whether
                that way is CONCRETE (git/tests/a number/a screenshot --
                the same kind of "hard verifiable signal" the report's
                own `verified success` measure requires: "git activity
                like commits and pull requests matching the work, as
                well as test suites passing, and explicit affirmation
                from the user") or VAGUE ("looks good," "feels right").

Every check carries the exact matched text as evidence -- no finding is
reported without the snippet that produced it.

What this module deliberately does NOT claim to check, stated plainly:
whether the brief states an outcome/goal versus a micromanaged list of
steps is the one remaining classifier signal this module can't reliably
tell apart from text alone -- "build me X" and a literal numbered recipe
for X both commonly appear in a perfectly good brief, so a hard pass/
fail here would be guessing. It's surfaced only as an informational
flag (`pure_step_list_flag`), never folded into the overall score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

WHY_PATTERNS = (
    r"\bbecause\b",
    r"\bso that\b",
    r"\bin order to\b",
    r"\bthe reason (is|this matters|i['’]m asking)\b",
    r"\bthis matters because\b",
    r"\bwhy this matters\b",
    r"\bso (i|we|you) can\b",
)

CONSTRAINT_PATTERNS = (
    r"\bdo(n['’]t| not)\b",
    r"\bnever\b",
    r"\bmust not\b",
    r"\bshould not\b",
    r"\bavoid\b",
    r"\bout of scope\b",
    r"\boff[- ]limits\b",
    r"\bwithout (touching|changing|modifying|breaking)\b",
    r"\bonly (use|touch|change|modify|edit)\b",
    r"\bleave .{1,40}? alone\b",
    r"\bno (new|additional) dependenc",
)

DONE_PATTERNS = (
    r"\b(done|finished|complete[d]?) when\b",
    r"\bverify that\b",
    r"\bcheck that\b",
    r"\bconfirm that\b",
    r"\bhow (we|you|i)['’]ll know\b",
    r"\bsuccess (criteria|looks like|means)\b",
    r"\bacceptance criteria\b",
    r"\buntil it\b",
)

CONCRETE_DONE_PATTERNS = (
    # "tests pass" / "the test suite still passes" / "all tests passing" --
    # allow up to a few words between "test(s)" and "pass", since real
    # phrasing almost never puts them directly adjacent ("test suite
    # still passes", not "test passes").
    r"\btests?\b[^.!?\n]{0,30}\bpass(es|ing)?\b",
    r"\brun(s|ning)? (the )?tests?\b",
    r"\bno (errors|warnings)\b",
    r"\bcompiles?\b",
    r"\blints? clean\b",
    r"\bexit code\b",
    r"\bscreenshot\b",
    r"\b\d+(\.\d+)?\s?%\b",
    r"\bgit (commit|diff|status|log)\b",
    r"\bpull request\b",
    r"\bci (is )?green\b",
)

VAGUE_DONE_PATTERNS = (
    r"\blooks good\b",
    r"\bfeels right\b",
    r"\bseems fine\b",
    r"\bwhen it['’]s ready\b",
    r"\bwhen you think it['’]s done\b",
    r"\buse your (best )?judg?ment\b",
)

# A line that's purely a numbered/bulleted imperative step, e.g.
# "1. Open the file" / "- Click save" / "* Run the script".
_STEP_LINE_RE = re.compile(r"^\s*(\d+[.)]|[-*•])\s+\S", re.MULTILINE)
GOAL_SENTENCE_PATTERNS = (
    r"\bthe goal is\b",
    r"\bi want\b",
    r"\bi need\b",
    r"\bwe need\b",
    r"\bthe (outcome|point) is\b",
    r"\bend result\b",
    r"\bultimately\b",
    r"\bfigure out\b",
    r"\byour (choice|call)\b",
    r"\bhowever you\b",
    r"\bup to you\b",
    r"\bbest way\b",
)


def _first_match(text: str, patterns: tuple[str, ...]) -> Optional[re.Match]:
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m
    return None


def _evidence(text: str, match: re.Match, context: int = 40) -> str:
    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    snippet = text[start:end].strip().replace("\n", " ")
    return ("…" if start > 0 else "") + snippet + ("…" if end < len(text) else "")


@dataclass
class CheckResult:
    name: str
    present: bool
    evidence: Optional[str] = None
    note: str = ""


@dataclass
class BriefGrade:
    checks: list[CheckResult] = field(default_factory=list)
    informational: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return sum(1 for c in self.checks if c.present)

    @property
    def max_score(self) -> int:
        return len(self.checks)

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "max_score": self.max_score,
            "checks": [
                {"name": c.name, "present": c.present, "evidence": c.evidence, "note": c.note}
                for c in self.checks
            ],
            "informational": list(self.informational),
        }


def check_why(text: str) -> CheckResult:
    m = _first_match(text, WHY_PATTERNS)
    if m:
        return CheckResult("why", True, _evidence(text, m))
    return CheckResult("why", False, note="no reason/justification language found")


def check_constraints(text: str) -> CheckResult:
    m = _first_match(text, CONSTRAINT_PATTERNS)
    if m:
        return CheckResult("constraints", True, _evidence(text, m))
    return CheckResult("constraints", False, note="no boundary/off-limits language found")


def check_done_criteria(text: str) -> tuple[CheckResult, Optional[CheckResult]]:
    """Returns (done_check, concreteness_check). concreteness_check is
    None when no done-criteria language was found at all -- there's
    nothing to grade for concreteness in that case."""
    m = _first_match(text, DONE_PATTERNS)
    if not m:
        return CheckResult("done_criteria", False, note="no completion/verification language found"), None

    done = CheckResult("done_criteria", True, _evidence(text, m))

    concrete_m = _first_match(text, CONCRETE_DONE_PATTERNS)
    if concrete_m:
        concreteness = CheckResult(
            "done_criteria_concrete", True, _evidence(text, concrete_m),
            note="a hard, checkable signal (git/tests/a number/a screenshot) -- "
                 "the kind the report's own verified-success measure requires",
        )
        return done, concreteness

    vague_m = _first_match(text, VAGUE_DONE_PATTERNS)
    evidence = _evidence(text, vague_m) if vague_m else None
    concreteness = CheckResult(
        "done_criteria_concrete", False, evidence,
        note="done-criteria language was found, but it reads as a subjective "
             "judgment call rather than anything checkable",
    )
    return done, concreteness


def check_pure_step_list(text: str) -> Optional[str]:
    """Informational only, per this module's own docstring -- never
    folded into the score. Flags only the clearest case: every
    non-blank line is a numbered/bulleted imperative step, AND no
    sentence anywhere states an overall goal or hands Claude latitude
    on how to get there."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    step_lines = _STEP_LINE_RE.findall(text)
    if len(step_lines) < len(lines):
        return None  # not EVERY line is a step -- some other prose exists
    if len(step_lines) < 2:
        return None  # a single bullet isn't a "step list"
    if _first_match(text, GOAL_SENTENCE_PATTERNS):
        return None
    return (
        "every line reads as a numbered/bulleted imperative step, with no "
        "sentence stating the overall goal or leaving Claude latitude on how "
        "to get there -- the report's own framing is that command of a "
        "domain, not a literal recipe, is what actually steers success"
    )


def grade_brief(text: str) -> BriefGrade:
    grade = BriefGrade()
    grade.checks.append(check_why(text))
    grade.checks.append(check_constraints(text))
    done, concreteness = check_done_criteria(text)
    grade.checks.append(done)
    if concreteness is not None:
        grade.checks.append(concreteness)
    flag = check_pure_step_list(text)
    if flag:
        grade.informational.append(flag)
    return grade


def render(grade: BriefGrade) -> str:
    lines = [f"Brief grade: {grade.score}/{grade.max_score}"]
    for c in grade.checks:
        mark = "PASS" if c.present else "MISS"
        detail = f' -- "{c.evidence}"' if c.evidence else (f" -- {c.note}" if c.note else "")
        lines.append(f"  [{mark}] {c.name}{detail}")
    for flag in grade.informational:
        lines.append(f"  [INFO] {flag}")
    return "\n".join(lines)


def main() -> None:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Grade an agent brief against three evidenced signals.")
    parser.add_argument("file", nargs="?", help="path to the brief's text file; omit to read stdin")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    grade = grade_brief(text)
    if args.json:
        print(json.dumps(grade.as_dict(), indent=2))
    else:
        print(render(grade))


if __name__ == "__main__":
    main()
