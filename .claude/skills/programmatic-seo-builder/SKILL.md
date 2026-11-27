---
name: programmatic-seo-builder
description: Build a batch of real, distinct pages from a dataset (a directory, a product catalog, a combinatorial set like tiers x symbols) instead of one page per idea — with a hard thin-page guard that refuses to generate if any page lacks enough real, data-derived content, or two pages turn out to say the same thing. Triggers on phrases like "build pSEO pages", "programmatic SEO", "generate pages from this dataset", "directory site", or any request to turn rows of data into many real pages at once.
---

# Programmatic SEO Page Builder

Builds many real pages from a dataset, not a template with a few words
swapped per row. The hard rule the source article names ("strict about
one thing: no thin pages") is implemented as an actual pre-write check in
`/builds/programmatic-seo-builder/pseo_guard.py`, not a guideline to
remember — full build notes, the real dataset used to prove it, and
what's deliberately cut: `/builds/programmatic-seo-builder/README.md`.

## Before generating anything

1. **The dataset has to produce genuinely distinct pages.** If two rows
   would render the same facts with only a name swapped, that's not a
   programmatic-SEO dataset, it's duplicate content with extra steps —
   either the dataset needs more real per-row data, or this isn't the
   right tool for the content in question.
2. **Reuse real, already-computed data when it exists in this project**
   rather than inventing placeholder numbers — the reference build uses
   `PropFirmAccount`'s real tier/contract math specifically so every page
   says something true and specific, not generic. The same discipline
   applies to any other dataset: pull from a real source of truth.
3. **Decide the keyword pattern up front**: one real, distinct long-tail
   query per page (the reference build's is "Can I trade {symbol} on a
   ${tier} account?"), not a vague topic umbrella that every page would
   answer identically.

## Building it

1. Write a `build_rows()` that returns one row per real combination in
   the dataset, each carrying the fields that make it different from
   every other row.
2. Write a `unique_facts(row)` that extracts just the data-derived values
   — fed to both the thin-page check and a duplicate-facts check (two
   rows with identical `unique_facts` are duplicate content even if
   their rendered boilerplate differs).
3. Render real body copy using those facts — plain sentences stating the
   actual numbers/claims, not filler padding to hit a word count. Run it
   through `.claude/skills/humanizer` before calling the copy done, same
   as any other drafted prose in this project.
4. Build real internal links: each page links to at least one grouping
   index (e.g., "all pages in this row's category") and a few genuinely
   related rows — not just a link back to the top index, which the
   article's own gap analysis names as a thin link structure.
5. Run the thin-page guard (`pseo_guard.check_page`) and the duplicate-
   facts check (`pseo_guard.check_no_duplicate_facts`) on every page
   **before** writing any file — refuse to generate, naming the specific
   failing pages and reasons, rather than writing thin pages and fixing
   them after.
6. Follow `design-rules.md` for styling — reuse an already-locked brand
   if the dataset belongs to one (the reference build reuses RUTHLESS
   TRADING GOLD since the data is from that portfolio); never default to
   a generic template palette.
7. Screenshot-verify per `CLAUDE.md`'s screenshot-before-done rule: serve
   locally, screenshot a sample page and the index, minimum two passes.

## What this skill does not do

No live crawl or rank-tracking step — "more pages that rank means more
traffic" is the article's own claim, unverifiable from this sandbox
either way, so this skill stops at generating real, non-thin pages with
real internal linking, not at proving they rank.
