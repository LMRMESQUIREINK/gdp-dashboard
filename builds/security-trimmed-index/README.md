# Security-Trimmed Index (STI)

The real mechanism from "A Practical Pattern to Implement Secure
Enterprise AI Search" (Natarajan Selvaraj), one of five articles in the
PDF bundle analyzed in `/notes/okf-rag-agentic-bundle-analysis.md`. This
was that round's named "same-day" next move — built in the immediate
follow-up round.

## The real pattern, and the anti-pattern it's compared against

The article's worked example is an Azure AI Search index with a
per-document `allowedGroupIds` field populated at ingest, and its central
claim is that access control must be enforced **inside the query** — as a
security filter applied before ranking, counting, and faceting — never as
a filter on already-computed results. The article states the
architecture but never spells out what goes wrong if you get this
backwards; `sti.py` makes both sides concrete and testable:

- `SecurityTrimmedIndex.search()` — the correct pattern. The caller's
  group membership filters the corpus first; every number returned
  (results, `total_count`, `facet_counts`) reflects only what that caller
  is actually authorized to see.
- `naive_post_filter_search()` — the anti-pattern, built only so it can be
  compared against the correct path on the same documents and the same
  caller. Nothing in this build recommends calling it for real use.

## Three leaks, one shared fixture

Checked `/builds/` first — nothing else in this project does
access-controlled search ranking/counting/faceting, a genuinely new
mechanism. `test_sti.py` builds one scenario (a "finance" caller
searching "quarterly revenue report," where two "engineering"-only
documents score higher than the one "finance"-authorized document) and
proves all three leaks on it directly, rather than three unrelated
hand-picked examples:

1. **Count leak** — the naive path's `total_count` is 3 (every matching
   document in the whole corpus); the correct path's is 1 (what the
   caller can actually see).
2. **Facet leak** — the naive path's facet counts include an
   `engineering: 2` bucket the caller has no access to; the correct
   path's facets never mention it.
3. **The sharpest leak: a genuinely missing result, not an over-count.**
   With `top_k=2`, the naive path ranks and truncates over the *full*
   corpus first, so the two higher-scoring, unauthorized engineering
   documents fill both result slots — the caller's one authorized,
   relevant document is dropped entirely, not merely ranked lower. A
   follow-up test confirms this is specifically a truncation-order bug
   (not permanent): with `top_k` large enough to cover the whole corpus,
   the authorized document survives the later filter, though the count
   and facet leaks still apply.

## Proven

`python3 -m unittest test_sti.py` — 12/12 pass on the real run, including
multi-group-membership (union of access across groups a caller belongs
to), a caller with no matching group, no-match queries, and an empty
index. No bug found in this build's own first draft — stated plainly
rather than manufactured.

## Deliberately not built

- A real scoring algorithm (BM25, vector similarity) — the point of this
  build is the access-control boundary around ranking, not the ranking
  algorithm itself; any real scorer slots into `_rank()`'s `_score()` call
  without touching the boundary.
- A real Azure AI Search / OpenSearch integration — no live service
  access from this sandbox, same standing restriction as every other
  build here needing a live external system.
