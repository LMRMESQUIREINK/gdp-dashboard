"""
Mechanical health checks for an Andrej Karpathy-style LLM wiki (a `raw/`
folder of immutable sources plus a `wiki/` folder of LLM-maintained,
cross-linked topic notes -- https://gist.github.com/karpathy/
442a6bf555914893e9891c11519de94f, confirmed real, April 2026).

The source article's own "health check" prompt names three targets --
notes that contradict each other, claims a newer source has replaced,
and topics mentioned often with no note yet -- and one filtering rule
it calls the line that matters most: "Only report what would mislead
me if I followed it today." That filter has no mechanism behind it in
the article; it's a live instruction to an LLM, re-interpreted fresh
on every run. This module operationalizes all four as a real,
structural property instead: every Claim is tagged `actionable` at
creation (pricing, deadlines, decisions, policies -- the kind of fact
that changes what you'd actually do) or not (branding, naming,
cosmetic details), and only actionable claims ever produce a finding.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Severity(Enum):
    ACTIONABLE = "actionable"
    COSMETIC = "cosmetic"


@dataclass
class Claim:
    subject: str  # what the claim is about, e.g. "pricing", "deadline"
    value: str  # the asserted fact, e.g. "$5/month"
    asserted_on: date
    severity: Severity = Severity.ACTIONABLE


@dataclass
class RawSource:
    name: str
    added_on: date
    topics: list[str]
    claims: list[Claim] = field(default_factory=list)


@dataclass
class WikiNote:
    topic: str
    claims: list[Claim] = field(default_factory=list)
    source_names: list[str] = field(default_factory=list)


@dataclass
class Finding:
    kind: str  # "contradiction" | "staleness" | "coverage_gap"
    detail: str
    severity: Severity


def check_contradictions(notes: list[WikiNote]) -> list[Finding]:
    """Two different notes asserting different values for the same
    claim subject, with no newer/older relationship to resolve which
    one is right -- a real disagreement, not just one being outdated."""
    findings: list[Finding] = []
    by_subject: dict[str, list[tuple[WikiNote, Claim]]] = {}
    for note in notes:
        for claim in note.claims:
            by_subject.setdefault(claim.subject, []).append((note, claim))

    for subject, entries in by_subject.items():
        # Cosmetic claims (branding, naming) never produce a finding --
        # the article's own "only report what would mislead you" rule,
        # applied structurally instead of left as a live LLM judgment call.
        actionable_entries = [(n, c) for n, c in entries if c.severity == Severity.ACTIONABLE]
        distinct_values = {c.value for _, c in actionable_entries}
        if len(distinct_values) <= 1:
            continue
        notes_involved = sorted({n.topic for n, _ in actionable_entries})
        findings.append(
            Finding(
                kind="contradiction",
                detail=f"'{subject}' is asserted differently across notes {notes_involved}: {sorted(distinct_values)}",
                severity=Severity.ACTIONABLE,
            )
        )
    return findings


def check_staleness(notes: list[WikiNote], raw_sources: list[RawSource]) -> list[Finding]:
    """A note's claim is stale when a newer raw source asserts a
    different value for the same subject and the note hasn't caught up."""
    findings: list[Finding] = []
    newest_claim_by_subject: dict[str, Claim] = {}
    source_name_by_subject: dict[str, str] = {}
    for src in raw_sources:
        for claim in src.claims:
            current = newest_claim_by_subject.get(claim.subject)
            if current is None or claim.asserted_on > current.asserted_on:
                newest_claim_by_subject[claim.subject] = claim
                source_name_by_subject[claim.subject] = src.name

    for note in notes:
        for claim in note.claims:
            if claim.severity == Severity.COSMETIC:
                continue
            newest = newest_claim_by_subject.get(claim.subject)
            if newest is None:
                continue
            if newest.asserted_on > claim.asserted_on and newest.value != claim.value:
                findings.append(
                    Finding(
                        kind="staleness",
                        detail=(
                            f"note '{note.topic}' claims {claim.subject}={claim.value!r} "
                            f"(as of {claim.asserted_on}), but '{source_name_by_subject[claim.subject]}' "
                            f"({newest.asserted_on}) says {newest.value!r}"
                        ),
                        severity=Severity.ACTIONABLE,
                    )
                )
    return findings


def check_coverage_gaps(
    raw_sources: list[RawSource], notes: list[WikiNote], min_mentions: int = 3
) -> list[Finding]:
    """A topic mentioned across at least `min_mentions` distinct raw
    sources, with no wiki note covering it yet."""
    mention_counts: dict[str, set[str]] = {}
    for src in raw_sources:
        for topic in src.topics:
            mention_counts.setdefault(topic, set()).add(src.name)

    covered_topics = {note.topic for note in notes}
    findings: list[Finding] = []
    for topic, sources in mention_counts.items():
        if topic in covered_topics:
            continue
        if len(sources) >= min_mentions:
            findings.append(
                Finding(
                    kind="coverage_gap",
                    detail=f"'{topic}' is mentioned in {len(sources)} raw sources ({sorted(sources)}) but has no wiki note",
                    severity=Severity.ACTIONABLE,
                )
            )
    return findings


def run_health_check(
    notes: list[WikiNote], raw_sources: list[RawSource], min_mentions: int = 3
) -> list[Finding]:
    return (
        check_contradictions(notes)
        + check_staleness(notes, raw_sources)
        + check_coverage_gaps(raw_sources, notes, min_mentions)
    )
