"""Security-Trimmed Index (STI) — the real mechanism from "A Practical
Pattern to Implement Secure Enterprise AI Search" (Natarajan Selvaraj),
part of the 5-article OKF/production-AI-systems bundle analyzed in
/notes/okf-rag-agentic-bundle-analysis.md. See that build's README for
why this got its own module rather than extending an existing one:
checked /builds/ first and found nothing else here does access-controlled
search ranking/counting/faceting.

The article's real worked example is an Azure AI Search index with a
per-document `allowedGroupIds` field populated at ingest, and its central,
correctly-reasoned claim is that access control must be enforced INSIDE
the query — as a security filter applied before ranking, counting, and
faceting — never as a post-filter on already-computed results. The
article states the architecture but never spells out the concrete failure
mode of getting this wrong; `naive_post_filter_search()` below exists
specifically to make that failure mode real, testable, and demonstrably
different from the correct `SecurityTrimmedIndex.search()` path, on the
exact same documents and the exact same caller.

Three distinct leaks a post-filter approach produces, each proven by a
dedicated test in test_sti.py:

1. total_count leaks the size of the full, unfiltered match set, not the
   caller's own authorized subset.
2. facet_counts leak category buckets drawn from documents the caller can
   never see.
3. Pagination can silently DROP an authorized, relevant document entirely:
   if ranking and top_k truncation happen before the ACL filter, an
   authorized document that would have ranked #1 among documents the
   caller can actually see can still fall outside the unfiltered top_k and
   never reach the caller at all — not merely over-counted, genuinely
   missing from their results.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    allowed_group_ids: frozenset[str]
    facets: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    score: float


@dataclass(frozen=True)
class SearchResponse:
    results: tuple[SearchResult, ...]
    total_count: int
    facet_counts: dict[str, dict[str, int]]


def _score(doc: Document, query_terms: set[str]) -> float:
    """A deterministic, dependency-free relevance score (shared-term
    count) — simple on purpose, since the point of this build is the
    access-control boundary around ranking, not the ranking algorithm
    itself. Any real scorer (BM25, a vector similarity) slots in here
    without changing anything about how the boundary is enforced."""
    return float(len(set(doc.text.lower().split()) & query_terms))


def _rank(docs: list[Document], query: str) -> list[tuple[Document, float]]:
    query_terms = set(query.lower().split())
    scored = [(d, _score(d, query_terms)) for d in docs]
    scored = [pair for pair in scored if pair[1] > 0]
    scored.sort(key=lambda pair: (-pair[1], pair[0].id))
    return scored


def _facet_counts(scored: list[tuple[Document, float]], facet_fields: tuple[str, ...]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for facet_field in facet_fields:
        counts: dict[str, int] = {}
        for doc, _score_value in scored:
            value = doc.facets.get(facet_field)
            if value is not None:
                counts[value] = counts.get(value, 0) + 1
        out[facet_field] = counts
    return out


class SecurityTrimmedIndex:
    """The correct pattern: the caller's authorized group membership is
    applied as a filter BEFORE ranking, counting, or faceting — every
    number this returns reflects only what the caller is actually
    entitled to see."""

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}

    def add(self, doc: Document) -> None:
        self._docs[doc.id] = doc

    def _authorized(self, caller_group_ids) -> list[Document]:
        caller = frozenset(caller_group_ids)
        return [d for d in self._docs.values() if d.allowed_group_ids & caller]

    def search(self, query: str, caller_group_ids, *, top_k: int = 10,
               facet_fields: tuple[str, ...] = ()) -> SearchResponse:
        authorized = self._authorized(caller_group_ids)
        scored = _rank(authorized, query)
        total_count = len(scored)
        facet_counts = _facet_counts(scored, facet_fields)
        top = scored[:top_k]
        return SearchResponse(
            results=tuple(SearchResult(d.id, s) for d, s in top),
            total_count=total_count,
            facet_counts=facet_counts,
        )


def naive_post_filter_search(index: SecurityTrimmedIndex, query: str, caller_group_ids, *,
                              top_k: int = 10, facet_fields: tuple[str, ...] = ()) -> SearchResponse:
    """The anti-pattern the article's own architecture correctly avoids,
    made concrete so it can be tested against: rank, count, and facet over
    the FULL, unfiltered corpus, THEN filter the already-truncated top_k
    results down to what the caller is authorized to see. This is wrong in
    three distinct, independently testable ways — see the module
    docstring. Exists only for comparison in test_sti.py; nothing in this
    build's own README recommends calling it."""
    all_docs = list(index._docs.values())
    scored = _rank(all_docs, query)
    total_count = len(scored)  # LEAK #1: includes unauthorized documents
    facet_counts = _facet_counts(scored, facet_fields)  # LEAK #2: same
    top = scored[:top_k]  # truncation happens BEFORE the ACL filter
    caller = frozenset(caller_group_ids)
    filtered_top = [(d, s) for d, s in top if d.allowed_group_ids & caller]
    # LEAK #3: an authorized document ranked outside the UNFILTERED top_k
    # is gone — not demoted, not merged back in, simply never returned.
    return SearchResponse(
        results=tuple(SearchResult(d.id, s) for d, s in filtered_top),
        total_count=total_count,
        facet_counts=facet_counts,
    )
