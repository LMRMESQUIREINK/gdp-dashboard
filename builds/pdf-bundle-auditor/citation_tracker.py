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

Extended from a second real finding, in a later round on three more Cloudera
ebooks: the exact same "$2.01B Fortune 1000 / datascienceassn.org" claim
above reappears, nearly verbatim, as a footnote in "7 Elements of a Winning
Enterprise Data Strategy" (2022) -- the same unreachable source backing the
same unverified number in two separate documents from the same vendor. That
repetition is not independent corroboration; it's one unconfirmed source
copy-pasted. `find_cross_document_echoes()` generalizes the check: group
claims by source_url across documents, and flag any URL that backs a claim
in more than one document while never once reaching CONFIRMED status. The
same round also found three claims from a different source
(NewVantage Partners' real 2022 "Data and AI Executive Survey") that check
out exactly against the primary report once actually found (92.1% measurable
results, 91.9%->92% culture-as-impediment, 26.5%->27% data-driven
organization) -- the discipline that makes the echo-detection meaningful:
some vendor citations really do hold up on inspection, so flagging a repeat
is about the repetition itself, not a blanket "vendor numbers are suspect."
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
    document: str | None = None

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


_CONFIRMED = (CitationStatus.CONFIRMED_EXACT, CitationStatus.CONFIRMED_APPROXIMATE)


@dataclass(frozen=True)
class EchoFinding:
    source_url: str
    claim_texts: tuple[str, ...]
    documents: tuple[str, ...]


def find_cross_document_echoes(claims: list[Claim]) -> list[EchoFinding]:
    """Groups claims by source_url and flags any URL that backs a claim in
    more than one distinct document while never reaching a CONFIRMED status
    in any of them. Reusing the same unverified source across a vendor's own
    content library is not independent corroboration -- it's the same
    unchecked number copy-pasted, and should not read as more trustworthy
    for having appeared twice. A URL that backs repeated claims within a
    SINGLE document isn't flagged here (ordinary footnote reuse); this is
    about the same source recurring across documents. A source that reaches
    CONFIRMED in at least one appearance is not flagged, even if it also
    backs an unconfirmed claim elsewhere -- the confirmation already settles
    whether the underlying source is real and accurate."""
    by_source: dict[str, list[Claim]] = {}
    for c in claims:
        if c.source_url is None:
            continue
        by_source.setdefault(c.source_url, []).append(c)

    findings = []
    for url, group in by_source.items():
        documents = {c.document for c in group if c.document is not None}
        if len(documents) < 2:
            continue
        if any(c.status in _CONFIRMED for c in group):
            continue
        findings.append(
            EchoFinding(
                source_url=url,
                claim_texts=tuple(c.text for c in group),
                documents=tuple(sorted(documents)),
            )
        )
    return findings
