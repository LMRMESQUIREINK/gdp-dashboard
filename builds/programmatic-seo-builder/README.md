# Programmatic SEO Page Builder

A real static-page generator built from the "Programmatic SEO Page
Builder" idea in the uploaded "7 claude skills that print money" article,
which names one hard rule: "strict about one thing: no thin pages."
Enforced here as a real, pre-write check (`pseo_guard.py`), not a
guideline — the generator refuses to write anything if any page fails it.

## Why this dataset, not a toy one

The article's own pitch ("a cheat code if you build it right... every row
in those databases is a page that can rank for a long-tail search") only
holds if each page genuinely says something different. So this build
generates against real data already proven elsewhere in this project —
`PropFirmAccount`/`TPT_TIERS`/`CONTRACT_SPECS` from
`/builds/prop-firm-sizing/` (`prop_firm_sizing.py`, copied here
unmodified, same convention every other build in this project follows) —
rather than a synthetic placeholder dataset. 5 TPT account tiers × 6
futures contracts = 30 real rows, each with genuinely distinct computed
numbers (daily loss limit in both dollars and instrument points, the
trailing-drawdown floor, max contracts, the 25%-rule "safe" contract
count, the evaluation fee), answering a real, distinct long-tail question
per page: "Can I trade {symbol} on a ${tier} TPT account?"

## What's built

- `pseo_dataset.py` — builds the 30-row dataset and each row's
  `unique_facts` dict (the data-derived values that must differ between
  pages — fed to the thin-page and duplicate-content checks).
- `pseo_guard.py` — pure functions, no file I/O: `check_page` (word count
  + unique-fact-count minimums) and `check_no_duplicate_facts` (catches
  two pages whose underlying data is byte-identical even if their
  boilerplate differs — a thin-content failure mode word count alone
  wouldn't catch).
- `generate_pages.py` — renders all 30 pages plus 5 tier-index pages (all
  symbols for one tier), 6 symbol-index pages (all tiers for one symbol),
  and one top-level index — real internal linking (each page links to its
  own tier index, its own symbol index, and 2–3 related pages), not just
  links back to the index. Runs every page through the thin-page and
  duplicate-content guards before writing anything; `SystemExit`s with the
  specific failing pages/reasons if any check fails.
- Styling reuses the already-established RUTHLESS TRADING GOLD palette
  (`design-rules.md`) since this is real data from that portfolio, not a
  generic template with invented branding.

## Verification

`test_pseo.py`, 10/10 passing, against the real dataset and real
generated files (a temp directory, not mocked I/O):

- Every one of the 30 real rows passes the thin-page guard with no
  overrides and has no duplicate facts with any other row.
- The guard is also checked against a deliberately thin page to confirm
  it actually rejects something, not just that it never fires.
- Generation writes the real file count (30 + 5 + 6 + 1 = 42) to a temp
  directory, then a real regex pass over one page's actual HTML extracts
  every `href="*.html"` it contains and asserts each linked file was
  genuinely written to disk — an internal-linking check against real
  output, not an assumption that the template is correct.
- No two pages render identical body text.

```bash
python3 -m unittest test_pseo -v
python3 generate_pages.py output   # writes the real 42 files
```

Screenshot-verified per this project's screenshot-before-done rule:
served locally (`python3 -m http.server`), a sample page
(`50k-es.html`) and the top index screenshotted with Playwright/Chromium
— clean on the first pass, no CSS leak or layout break, real distinct
numbers rendering per page.

## What's deliberately cut

- **Stage 1 (an AI-generated reference image)** from the flowchart-
  generator build's own established pattern doesn't apply here — there's
  no equivalent "look" to generate first; the page shell is simple,
  semantic HTML plus the already-locked RUTHLESS palette, not a new
  visual design needing a reference pass.
- **Schema.org JSON-LD markup**, which the article mentions pairing with
  ("pair it with the schema skill from the same repo"), is not added —
  it's a real, separate piece of work (choosing and validating the right
  schema type per page) out of proportion to what this build set out to
  demonstrate (the thin-page guard and real internal linking), and no
  schema-generation skill exists yet in this project to pair it with.
- **A live crawl/rank-tracking step** isn't built — this sandbox has no
  live search-engine access to check, and the article's own claim
  ("more pages that rank means more traffic") isn't something a sandbox
  build could verify either way.

## Reusing this for a different dataset

`pseo_dataset.py` and `generate_pages.py` are written against
`PageRow`/`unique_facts()` specifically for this prop-firm dataset;
reusing the generator for a different one means writing a new
`build_rows()`/`unique_facts()` pair against the new data and keeping
`pseo_guard.py`'s checks as-is — the guard itself has no prop-firm-specific
logic in it.
