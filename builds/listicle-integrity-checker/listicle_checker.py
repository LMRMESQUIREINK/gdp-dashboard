"""
listicle_checker.py -- integrity checks for vendor-published "Top N" /
"Best X" listicle articles.

Built from a real pattern found reading four NocoBase-authored Medium
articles together: the same publisher ran a years-long series of
"Top N open-source X on GitHub" posts, cross-posted to Medium/dev.to/
Hashnode/translated. Reading the four side by side surfaced three
distinct, checkable problems a single listicle read in isolation would
not show:

1. The publisher's own product appears inside its own "Top N" ranking
   of that same product category -- a real conflict-of-interest signal,
   whether or not it is disclosed.
2. Two different entries' title hyperlinks pointed at the exact same
   external URL (a likely copy-paste artifact, not two products that
   happen to share a homepage).
3. The same project, named in two dated snapshots of a related list
   published months apart by the same author, had a metric (GitHub
   stars) that *decreased* -- which real GitHub star counts essentially
   never do on their own, so it is worth a second look rather than a
   silent accept.

None of this requires live network access: every check operates on a
list of entries the caller already extracted from the article(s).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Entry:
    """One item in a "Top N" listicle."""

    name: str
    rank: int
    title_link: Optional[str] = None
    metric_value: Optional[float] = None
    metric_label: str = "stars"


@dataclass
class Listicle:
    """One article: an ordered (or grouped) set of entries plus metadata."""

    title: str
    publisher: str
    entries: list[Entry]
    published_date: Optional[str] = None  # ISO 8601, e.g. "2026-09-05"
    total_count: Optional[int] = None  # the "N" the title claims, if stated


# ---------------------------------------------------------------------
# 1. Self-referential ranking detection
# ---------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[^a-z0-9]+")


def _normalize(name: str) -> str:
    return _PUNCT_RE.sub("", name.lower())


@dataclass
class SelfReferenceFinding:
    listicle_title: str
    publisher: str
    matched_entry: str
    rank: int
    total_count: Optional[int]

    @property
    def summary(self) -> str:
        total = f" of {self.total_count}" if self.total_count else ""
        return (
            f'"{self.listicle_title}" (by {self.publisher}) ranks its own '
            f'publisher\'s product, "{self.matched_entry}", at #{self.rank}{total}.'
        )


def check_self_reference(listicle: Listicle) -> list[SelfReferenceFinding]:
    """Flag any entry whose name matches the publisher's own identity.

    Matching is substring-based after normalizing away punctuation/case,
    in both directions (publisher name contains entry name, or vice
    versa), so "NocoBase" matches an entry literally named "NocoBase"
    without needing an exact string match, but stays conservative enough
    not to flag an unrelated entry that happens to share a short common
    word with the publisher's name.
    """
    pub_norm = _normalize(listicle.publisher)
    if not pub_norm:
        return []

    findings: list[SelfReferenceFinding] = []
    for entry in listicle.entries:
        name_norm = _normalize(entry.name)
        if not name_norm:
            continue
        if name_norm == pub_norm or (
            len(name_norm) >= 4
            and len(pub_norm) >= 4
            and (name_norm in pub_norm or pub_norm in name_norm)
        ):
            findings.append(
                SelfReferenceFinding(
                    listicle_title=listicle.title,
                    publisher=listicle.publisher,
                    matched_entry=entry.name,
                    rank=entry.rank,
                    total_count=listicle.total_count,
                )
            )
    return findings


# ---------------------------------------------------------------------
# 2. Link-collision detection
# ---------------------------------------------------------------------


@dataclass
class LinkCollisionFinding:
    listicle_title: str
    url: str
    entries: list[str]

    @property
    def summary(self) -> str:
        names = ", ".join(f'"{n}"' for n in self.entries)
        return (
            f'"{self.listicle_title}": {len(self.entries)} different entries '
            f"({names}) all have their title link pointing at the exact same "
            f"URL ({self.url}) -- almost certainly a copy-paste artifact, not "
            f"{len(self.entries)} unrelated products sharing one homepage."
        )


def check_link_collisions(listicle: Listicle) -> list[LinkCollisionFinding]:
    """Flag a URL reused as the title link for 2+ *different* entries.

    A real homepage URL legitimately reused for the SAME entry (e.g. its
    GitHub link and its title link both pointing at github.com/org/repo)
    is not a collision; this only fires when the identical URL is the
    title link for entries with different names.
    """
    by_url: dict[str, list[str]] = {}
    for entry in listicle.entries:
        if not entry.title_link:
            continue
        by_url.setdefault(entry.title_link, []).append(entry.name)

    findings = []
    for url, names in by_url.items():
        distinct_names = list(dict.fromkeys(names))  # preserve order, dedupe
        if len(distinct_names) >= 2:
            findings.append(
                LinkCollisionFinding(
                    listicle_title=listicle.title, url=url, entries=distinct_names
                )
            )
    return findings


# ---------------------------------------------------------------------
# 3. Cross-snapshot metric monotonicity
# ---------------------------------------------------------------------


@dataclass
class MonotonicityFinding:
    project_name: str
    earlier_listicle: str
    earlier_date: Optional[str]
    earlier_value: float
    later_listicle: str
    later_date: Optional[str]
    later_value: float
    metric_label: str

    @property
    def delta(self) -> float:
        return self.later_value - self.earlier_value

    @property
    def direction(self) -> str:
        if self.delta > 0:
            return "increased"
        if self.delta < 0:
            return "decreased"
        return "unchanged"

    @property
    def summary(self) -> str:
        return (
            f'"{self.project_name}" {self.metric_label} {self.direction} from '
            f"{self.earlier_value:g} ({self.earlier_listicle}, "
            f"{self.earlier_date or 'undated'}) to {self.later_value:g} "
            f"({self.later_listicle}, {self.later_date or 'undated'}) -- "
            f"delta {self.delta:+g}."
        )


def check_metric_monotonicity(
    listicles: list[Listicle], expect_increasing: bool = True
) -> list[MonotonicityFinding]:
    """Across 2+ dated listicles, find the same project named in more than
    one, and report every pair whose metric moved -- flagging decreases
    when the metric (like GitHub stars) is expected to only increase.

    Only listicles with a `published_date` participate in ordering; an
    undated listicle is skipped entirely for this check (there is nothing
    to order it against).
    """
    dated = [l for l in listicles if l.published_date]
    dated.sort(key=lambda l: l.published_date)

    # project name (normalized) -> list of (listicle, entry) in date order
    by_project: dict[str, list[tuple[Listicle, Entry]]] = {}
    for listicle in dated:
        for entry in listicle.entries:
            if entry.metric_value is None:
                continue
            key = _normalize(entry.name)
            by_project.setdefault(key, []).append((listicle, entry))

    findings: list[MonotonicityFinding] = []
    for appearances in by_project.values():
        if len(appearances) < 2:
            continue
        for (earlier_l, earlier_e), (later_l, later_e) in zip(
            appearances, appearances[1:]
        ):
            if later_e.metric_value == earlier_e.metric_value:
                continue
            decreased = later_e.metric_value < earlier_e.metric_value
            if expect_increasing and not decreased:
                continue  # an increase is the expected, unremarkable case
            findings.append(
                MonotonicityFinding(
                    project_name=earlier_e.name,
                    earlier_listicle=earlier_l.title,
                    earlier_date=earlier_l.published_date,
                    earlier_value=earlier_e.metric_value,
                    later_listicle=later_l.title,
                    later_date=later_l.published_date,
                    later_value=later_e.metric_value,
                    metric_label=earlier_e.metric_label,
                )
            )
    return findings


# ---------------------------------------------------------------------
# Convenience: run all three checks over a set of listicles
# ---------------------------------------------------------------------


@dataclass
class Report:
    self_references: list[SelfReferenceFinding] = field(default_factory=list)
    link_collisions: list[LinkCollisionFinding] = field(default_factory=list)
    metric_regressions: list[MonotonicityFinding] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (
            self.self_references or self.link_collisions or self.metric_regressions
        )


def audit(listicles: list[Listicle]) -> Report:
    report = Report()
    for listicle in listicles:
        report.self_references.extend(check_self_reference(listicle))
        report.link_collisions.extend(check_link_collisions(listicle))
    report.metric_regressions = check_metric_monotonicity(listicles)
    return report
