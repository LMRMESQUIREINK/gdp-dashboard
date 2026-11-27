"""
Checks a "Configure Chat" custom-instructions block (the text you'd paste
into NotebookLM/Gemini Notebook's Custom chat style, confirmed real and
current against Google's own help docs) against the specific properties
the source article's own worked example instruction block actually has.

This does not call NotebookLM -- there is no live access to it from this
sandbox (it requires a real Google account login). It mechanically checks
the TEXT of an instructions block for the presence of each required
property, the same static-analysis-of-a-system-prompt approach as
winston_checker.py's deck-text checks and skill_md_validator.py's
frontmatter checks elsewhere in this project.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class Finding:
    rule_id: str
    status: Status
    detail: str


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def check_grounding_only(text: str) -> Finding:
    """Must instruct the model to answer only from the notebook's own
    sources -- the article's own text: 'Answer only from the sources in
    this notebook.'"""
    ok = _has_any(
        text,
        [r"only\s+from\s+(the\s+)?sources", r"only\s+answer\s+from", r"sources\s+in\s+this\s+notebook"],
    )
    return Finding(
        "grounding_only",
        Status.PASS if ok else Status.FAIL,
        "instructs answering only from the notebook's own sources" if ok
        else "no instruction restricting answers to the notebook's own sources -- the model can answer from its general training instead",
    )


def check_fallback_phrase(text: str) -> Finding:
    """Must specify an explicit fallback behavior/phrase for missing
    information -- the article's own text: 'say "Not in my sources"'."""
    ok = _has_any(
        text,
        [r"not in my sources", r"if the sources don'?t contain", r"don'?t contain the answer"],
    )
    return Finding(
        "fallback_phrase",
        Status.PASS if ok else Status.FAIL,
        "specifies an explicit fallback phrase for missing information" if ok
        else "no explicit fallback phrase for when the sources lack the answer -- without one, a gap is more likely to get silently filled in rather than flagged",
    )


def check_suggests_missing_source_type(text: str) -> Finding:
    """A step beyond the bare fallback: the article's own text also asks
    the model to suggest what kind of source to add. Treated as a WARN,
    not a FAIL, when absent -- useful, but not the load-bearing
    anti-fabrication clause the other checks are."""
    ok = _has_any(text, [r"suggest what kind of source", r"suggest.*source.*add", r"what.*should.*add"])
    return Finding(
        "suggests_missing_source_type",
        Status.PASS if ok else Status.WARN,
        "asks the model to suggest what kind of source would fill the gap" if ok
        else "doesn't ask the model to suggest what's missing -- a real nice-to-have the article's own example includes, not required for grounding safety",
    )


def check_citation_required(text: str) -> Finding:
    """Must require citations on claims -- the article's own text: 'give
    the supporting points with citations.'"""
    ok = _has_any(text, [r"citation", r"\bcite\b", r"with citations"])
    return Finding(
        "citation_required",
        Status.PASS if ok else Status.FAIL,
        "requires citations on supporting claims" if ok
        else "no citation requirement -- an answer that sounds grounded can't actually be checked against the source without one",
    )


def check_disagreement_surfacing(text: str) -> Finding:
    """Must instruct surfacing disagreement between sources -- the
    article's own text: 'Point out when two sources disagree.'"""
    ok = _has_any(text, [r"disagree", r"point out when.*sources", r"conflict.*sources"])
    return Finding(
        "disagreement_surfacing",
        Status.PASS if ok else Status.WARN,
        "instructs surfacing disagreement between sources" if ok
        else "no instruction to surface disagreement between sources -- a real notebook with sources from different dates/authors can silently blend contradictory claims into one confident answer",
    )


def check_plain_english(text: str) -> Finding:
    """Must instruct plain language / no filler -- the article's own
    text: 'Use plain English. No filler.'"""
    ok = _has_any(text, [r"plain english", r"no filler", r"no jargon", r"plain language"])
    return Finding(
        "plain_english",
        Status.PASS if ok else Status.WARN,
        "instructs plain language with no filler" if ok
        else "no plain-language/no-filler instruction -- a style preference, not a safety property, so this is a WARN",
    )


ALL_CHECKS = [
    check_grounding_only,
    check_fallback_phrase,
    check_suggests_missing_source_type,
    check_citation_required,
    check_disagreement_surfacing,
    check_plain_english,
]


def audit(text: str) -> list[Finding]:
    return [check(text) for check in ALL_CHECKS]


def summarize(findings: list[Finding]) -> dict:
    counts = {"pass": 0, "fail": 0, "warn": 0}
    for f in findings:
        counts[f.status.value] += 1
    return counts
