"""Tracks per-claim citation confidence across a document's footnoted
figures, forcing a status and a one-line reason on every claim.

Built from a real finding: Cloudera's "Empowering Innovation" (2022) ebook
footnotes four quantitative claims to four different named sources. Checking
each one against what's actually findable produced four genuinely different
outcomes, not a uniform verdict: one confirmed close to exactly (the 87%
ThoughtSpot/HBR "New Decision Makers" figure), one confirmed with correctly-
hedged phrasing already matching the stat's real nature as a self-reported
expectation (the 17.9% DataIQ/Mango Solutions figure), one whose named source
document is real and locatable but unreachable from this sandbox (a Forrester
Total Economic Impact study, quoted anonymously as "Chief data and analytics
officer, pharmaceuticals"), and one with no independent corroboration found at
all (the "$2.01B Fortune 1000" revenue-usability figure, footnoted to a
specific Data Science Association URL that is also unreachable here). A
separate IDC claim from the companion edge/IoT ebook ("440x more data than
2006") was actively CONTRADICTED by the closest real IDC Digital Universe
figure found (a 300x growth from 2005, not 440x from 2006) -- a different base
year and a different multiplier from the same family of studies.
"""

from dataclasses import dataclass
from enum import Enum


class CitationStatus(Enum):
    CONFIRMED_EXACT = "confirmed_exact"
    CONFIRMED_APPROXIMATE = "confirmed_approximate"
    SOURCE_LOCATED_UNVERIFIED = "source_located_unverified"
    UNCONFIRMED = "unconfirmed"
    CONTRADICTED = "contradicted"


_REQUIRES_SOURCE = {
    CitationStatus.CONFIRMED_EXACT,
    CitationStatus.CONFIRMED_APPROXIMATE,
    CitationStatus.SOURCE_LOCATED_UNVERIFIED,
    CitationStatus.CONTRADICTED,
}


@dataclass(frozen=True)
class Claim:
    text: str
    source_url: str | None
    status: CitationStatus
    reason: str

    def __post_init__(self):
        if not self.reason.strip():
            raise ValueError(f"claim {self.text!r} has no reason given for its status")
        if self.status in _REQUIRES_SOURCE and self.source_url is None:
            raise ValueError(
                f"claim {self.text!r} has status {self.status} but no source_url"
            )


def summarize(claims: list[Claim]) -> dict[str, int]:
    counts = {status.value: 0 for status in CitationStatus}
    for c in claims:
        counts[c.status.value] += 1
    return counts


def require_minimum_confirmed(claims: list[Claim], minimum: int = 1) -> bool:
    """A document whose every footnoted claim is confirmed is suspiciously
    thorough for a vendor deck, and a document with zero confirmed claims
    means nothing in it was actually checkable -- both are worth a human
    second look, but the hard floor this enforces is just the latter."""
    confirmed = sum(
        1
        for c in claims
        if c.status in (CitationStatus.CONFIRMED_EXACT, CitationStatus.CONFIRMED_APPROXIMATE)
    )
    return confirmed >= minimum
