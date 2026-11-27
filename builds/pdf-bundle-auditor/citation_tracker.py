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

Extended again from a third real finding, in a later round on three more
Cloudera ebooks: "How to Build a Foundation for Exploratory Data Science with
CML on AWS" (2022) and "How to Take AI Applications from Concept to Reality
with CML on AWS" (2022, created the same day per each PDF's own CreationDate)
both carry the near-verbatim sentence "Globe Telecom manages 600PB of data
with CML on AWS, driving [a strategy that supports] 66% year-over-year growth
in mobile data volume" -- but this is a bare, self-authored customer-metric
claim with NO footnoted source_url at all, so `find_cross_document_echoes()`
(which only groups by source_url) cannot catch it. `find_cross_document_text_echoes()`
closes that gap: it normalizes and groups claims by their own text instead of
by an external citation, catching the case where a vendor's own case-study
number is recycled verbatim across its content library with no new
verification attached either time -- the same underlying problem the
source_url-based check targets, just without a footnote to key off of.
"""

from dataclasses import dataclass
from enum import Enum
import re


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


def _normalize_for_echo(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9%$.]+", " ", text)
    return " ".join(text.split())


@dataclass(frozen=True)
class TextEchoFinding:
    normalized_text: str
    claim_texts: tuple[str, ...]
    documents: tuple[str, ...]


def find_cross_document_text_echoes(
    claims: list[Claim],
    min_normalized_length: int = 20,
    similarity_threshold: float = 0.85,
) -> list[TextEchoFinding]:
    """Groups claims by NEAR-verbatim text (not by source_url, and not by
    exact-string equality) and flags any claim repeated across two or more
    distinct documents while never reaching CONFIRMED in any of them.

    An earlier draft of this function grouped by exact normalized-text
    equality and missed its own motivating case on the first real run: two
    Cloudera ebooks state "Globe Telecom manages 600PB of data with CML on
    AWS, driving [...] 66% year-over-year growth in mobile data volume" with
    one extra clause inserted in one of the two ("a strategy that supports")
    -- real-world repetition is near-verbatim, not byte-identical, so exact
    matching is the wrong tool and was fixed here (not the test) once the
    first real run against this round's own fixture failed. Similarity is
    measured with difflib's SequenceMatcher ratio on normalized text.

    Complements find_cross_document_echoes(): that function can only catch an
    echo when both appearances cite the same external source_url, so it has
    nothing to key off of for a bare, self-authored claim (source_url=None)
    -- exactly the shape of a vendor's own customer case-study metric. Claims
    shorter than min_normalized_length are skipped (short phrases like
    "Cloudera" or "CML" would otherwise match everywhere and swamp the result
    with noise)."""
    import difflib

    candidates = [
        c for c in claims if len(_normalize_for_echo(c.text)) >= min_normalized_length
    ]
    normalized_texts = [_normalize_for_echo(c.text) for c in candidates]

    findings = []
    used = set()
    for i, a in enumerate(candidates):
        if i in used:
            continue
        group_idxs = {i}
        for j in range(i + 1, len(candidates)):
            if j in used:
                continue
            ratio = difflib.SequenceMatcher(
                None, normalized_texts[i], normalized_texts[j]
            ).ratio()
            if ratio >= similarity_threshold:
                group_idxs.add(j)
        if len(group_idxs) < 2:
            continue
        group = [candidates[k] for k in sorted(group_idxs)]
        documents = {c.document for c in group if c.document is not None}
        if len(documents) < 2:
            continue
        if any(c.status in _CONFIRMED for c in group):
            continue
        used |= group_idxs
        findings.append(
            TextEchoFinding(
                normalized_text=normalized_texts[i],
                claim_texts=tuple(c.text for c in group),
                documents=tuple(sorted(documents)),
            )
        )
    return findings
