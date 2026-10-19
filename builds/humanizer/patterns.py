"""
A real, dependency-free set of AI-writing-tell detectors — built from
the "Humanizer" idea in the uploaded "7 claude skills that print money"
article (which claims 50k+ stars and "26 patterns," neither checkable
from this sandbox: no live GitHub access to verify the star count, and
the article names no list of the 26, so this is an independent set built
from first principles and this project's own established don't-say-list
instinct (`design-rules.md`'s "Generic-AI tells to avoid" section, which
covers *visual* design tells — this is the prose equivalent, a real gap
that section doesn't fill).

Each `Rule` is a compiled regex plus a human-readable name, category, and
a one-line fix suggestion. `scan()` returns every match in the text, in
order; `score()` summarizes density so a caller can set a threshold
without re-deriving regex counts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    name: str
    category: str
    pattern: re.Pattern[str]
    suggestion: str


@dataclass(frozen=True)
class Finding:
    rule_name: str
    category: str
    matched_text: str
    start: int
    end: int
    suggestion: str


def _rule(name: str, category: str, regex: str, suggestion: str, flags: int = re.IGNORECASE) -> Rule:
    return Rule(name=name, category=category, pattern=re.compile(regex, flags), suggestion=suggestion)


RULES: list[Rule] = [
    _rule(
        "filler-opener",
        "throat-clearing",
        r"\b(?:let'?s (?:dive|explore|unpack|break this down)|in today'?s (?:fast-paced|digital|ever-evolving) world|"
        r"in the (?:ever-evolving|rapidly changing) (?:landscape|world) of)\b",
        "Cut it — start with the actual point.",
    ),
    _rule(
        "throat-clearing-note",
        "throat-clearing",
        r"\bit'?s (?:important|worth|crucial|essential) to (?:note|mention|remember|understand) that\b",
        "Delete this phrase; say the thing it's introducing directly.",
    ),
    _rule(
        "needless-to-say",
        "throat-clearing",
        r"\bneedless to say,?\b",
        "If it's needless to say, don't say it.",
    ),
    _rule(
        "false-contrast-triplet",
        "rhetorical-tic",
        r"\bit'?s not (?:just|only) (?:about )?[\w\s]{1,40}?,?\s*it'?s (?:about )?[\w\s]{1,40}\b",
        "Rewrite as one direct claim instead of a not-X-but-Y contrast.",
    ),
    _rule(
        "conclusion-signal",
        "throat-clearing",
        r"\b(?:in conclusion|to sum up|to wrap (?:this|it) up|all in all),?\b",
        "Short content doesn't need a signposted conclusion — just end.",
    ),
    _rule(
        "stacked-transitions",
        "rhetorical-tic",
        r"\b(?:moreover|furthermore|additionally|what'?s more),\s",
        "These stack up fast; keep at most one per few paragraphs.",
    ),
    _rule(
        "hedge-phrase",
        "hedging",
        r"\b(?:it'?s worth noting that|arguably|in many cases|in some ways|to some extent|generally speaking)\b",
        "Either make the claim or don't — a hedge that adds no real caveat is filler.",
    ),
    _rule(
        "may-vary-hedge",
        "hedging",
        r"\b(?:results|experience|mileage) may vary\b",
        "Say what actually varies and why, or cut it.",
    ),
    _rule(
        "stacked-intensifier",
        "hedging",
        r"\b(?:truly|incredibly|remarkably|genuinely|really)\b,?\s+(?:truly|incredibly|remarkably|genuinely|really)\b",
        "One intensifier at most; two in a row (comma-separated or not) reads as padding.",
    ),
    _rule(
        "buzzword",
        "buzzword",
        r"\b(?:unlock(?:s|ing)?|unleash(?:es|ing)?|elevate(?:s|d)?|revolutioniz(?:e|es|ing)|game-?changer|"
        r"seamless(?:ly)?|robust|cutting-edge|leverage(?:s|d|ing)?|synerg(?:y|ies)|holistic(?:ally)?|empower(?:s|ing|ed)?|"
        r"next-level|best-in-class|world-class|paradigm shift)\b",
        "Name the real benefit in plain words instead.",
    ),
    _rule(
        "whether-youre-cliche",
        "rhetorical-tic",
        r"\bwhether you'?re a (?:beginner|novice|expert|pro)\b",
        "Say who this is actually for — this phrase tries to cover everyone and specifies no one.",
    ),
    _rule(
        "in-the-world-of",
        "throat-clearing",
        r"\bin the world of [\w\s]{1,30}\b",
        "Name the actual subject; \"the world of X\" adds no information.",
    ),
    _rule(
        "delve-into",
        "buzzword",
        r"\bdelve(?:s|d|ing)? into\b",
        "\"Delve into\" almost always means \"look at\" or \"cover\" — use the plain verb.",
    ),
]


def scan(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        for match in rule.pattern.finditer(text):
            findings.append(
                Finding(
                    rule_name=rule.name,
                    category=rule.category,
                    matched_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    suggestion=rule.suggestion,
                )
            )
    findings.sort(key=lambda f: f.start)
    return findings


_EM_DASH_PATTERN = re.compile(r"[—–]")
_WORD_PATTERN = re.compile(r"\b\w+\b")


def em_dash_density(text: str) -> float:
    """Em/en dashes per 100 words — a real, commonly cited LLM tell when it
    spikes well above ordinary prose, but reported as a density, not a hard
    flag, since dashes are also ordinary punctuation."""
    word_count = len(_WORD_PATTERN.findall(text))
    if word_count == 0:
        return 0.0
    dash_count = len(_EM_DASH_PATTERN.findall(text))
    return (dash_count / word_count) * 100


def score(text: str) -> dict:
    findings = scan(text)
    word_count = max(1, len(_WORD_PATTERN.findall(text)))
    by_category: dict[str, int] = {}
    for finding in findings:
        by_category[finding.category] = by_category.get(finding.category, 0) + 1

    return {
        "word_count": word_count,
        "finding_count": len(findings),
        "findings_per_1000_words": round(len(findings) / word_count * 1000, 1),
        "by_category": by_category,
        "em_dash_per_100_words": round(em_dash_density(text), 2),
        "findings": findings,
    }
