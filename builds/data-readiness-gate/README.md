# Data Readiness Gate

A `ruthless-gate` verdict page auditing three uploaded vendor PDFs about
AI agents, enterprise data readiness, and RAG — each audited alone, then
read against each other, per the skill's multi-source rule.

Open `index.html` (served locally, not `file://`, if you want the exact
rendering the screenshots show — though this page has no external
dependencies and does render fine from `file://` too) to see the full
page. Run `node test.js` to re-run the assertion suite.

## Sources

1. **AI Agents in Data Platforms For Dummies®, Cloudera® Special
   Edition** — Dipankar Mazumdar, published by John Wiley & Sons, Inc.,
   51 pages, © 2026.
2. **The Data Readiness Index: Understanding the Foundations for
   Successful AI** — Cloudera, 9 pages, © 2026.
3. **The RAG Cookbook: Best Practices for Configuring our
   Retrieval-Augmented Generation models** — Progress Software
   Corporation (Nasdaq: PRGS), 13 pages, © 2025.

Fresh sha256 (re-derived at build time, not carried across any gap —
see the CORRECTIONS section on the page for why that mattered this
round) and page/word counts for all three are in `data.js` under
`sources`, and rendered in the page's "Measured" table.

Source bundle fingerprint: `669ac0de7eaa06dc` (sha256 over the sorted
"filename sha256" rows of the three PDFs, first 16 chars — recomputed
independently inside `test.js` and asserted to match).

## What this gate found

20 findings across the four levels (DEEP/DEEPER/DEEPEREST/
DEEPEREST-EST): 13 credits, 7 stops. Every one of the three named
sources gets at least one credit and at least one stop, per the
skill's multi-source rule — tallies are on the rendered page's verdict
panel, not restated here, so they can't drift out of sync with
`data.js`.

The headline findings, in brief:

- **A clean verification round on pure factual existence.** All 9
  external, checkable claims across the three sources (2 arXiv paper
  citations, 1 GitHub repo, Neon's branching architecture, REMi's
  real open-source status, the "qualitative easing" financial term,
  a Harvard Business Review Analytic Services statistic, a 2025
  Cloudera survey statistic, and a webinar's real speaker) came back
  confirmed real. Zero fabricated citations found.
- **A real, well-evidenced internal seam in the Readiness Index**
  (finding R7): two adjacent catalog/lineage statistics (91% and 47%)
  are joined with "However," implying tension, but the text never
  states a shared denominator between them — they sum to 138% if
  read as mutually exclusive shares of one base, which is impossible.
  Confirmed as a real, isolated exception (not general carelessness)
  by checking that two OTHER paired sub-statistics elsewhere in the
  same document (38%+47%=85%, 8%+15%=23%) add up exactly (R8).
- **A cross-source finding that needed both Cloudera documents read
  together** (X2): the Dummies book presents catalog+lineage as a
  solved, foundational architecture pattern ("the catalog becomes the
  map"), while Cloudera's own separate survey shows real deployment
  of that exact capability is partial — only 47% describe it as
  enterprise-standardized rather than select-team usage.
- **A cross-VENDOR finding** (X3): the RAG Cookbook's (Progress)
  advanced retrieval techniques all presuppose well-integrated source
  data, while an unrelated vendor's (Cloudera) own independent survey
  shows only 30% of IT leaders say their data sources are fully
  integrated — the technique guidance assumes an infrastructure
  maturity most real enterprises, per that other vendor's own data,
  haven't reached.
- **A real, precisely dated finding** (E2): Cloudera ran two distinct,
  differently-sampled, differently-partnered AI-data-readiness surveys
  within about two days of each other in March 2026 (this document's
  own 1,270-respondent Researchscape survey, and a separate
  ~230-respondent Harvard Business Review Analytic Services study it
  cites as if merely corroborating) — confirmed via web search, not
  asserted from the PDF text alone.
- **A document-internal paradox the source itself half-states but
  never closes** (E4/E5): Telecommunications tops both the visibility
  (89%) and access (84%) charts, and separately reports the highest
  rate (60%) of infrastructure performance "always" hindering
  operations — the document explicitly connects the first two facts
  ("that success hasn't totally translated into operational
  success"), then immediately presents governance data showing Telecom
  is ALSO the worst-governed of the 7 surveyed industries, without
  ever stating that specific connection. A Spearman rank correlation
  recomputed independently in `test.js` (ρ ≈ -0.393 for both
  visibility-vs-governance and access-vs-governance) confirms this is
  a real, moderate pattern across all 7 industries, not a two-industry
  anecdote.
- **A precise, literal credit** (R3): Chapter 5's title, "More than Ten
  Key Takeaways," is exactly accurate — 10 core concept bullets
  (matching the chapter's own "Ten important concepts" preview) plus
  one explicitly separate forward-looking bonus section, 11 total,
  counted directly from the text.
- **A genuine gap, not a factual error** (R4): the one empirical
  benchmark paper the Dummies book cites is never referenced again
  anywhere in its 51-page body — confirmed by grep, zero hits beyond
  the single "Beyond This Book" citation line.
- **A minor, real copy-editing error** (R5): the RAG Cookbook's closing
  CTA reads "What to know more? Try it for Free!" — almost certainly
  meant to read "Want to know more?"

Full details, every piece of evidence, and all four levels of analysis
are on the rendered page itself (`index.html`), not duplicated here.

## A correction made in public

An earlier concern from this same working round — that a captured
sha256 hash for the Readiness Index PDF looked 65 characters long
(one over the correct SHA-256 length) — was checked directly before
this page was built. All three PDFs' hashes were re-derived fresh and
confirmed, by exact character count, to be 64 characters each. The
65-character appearance was a manual-counting error made while
reasoning about a transcribed tool result, not an actual data problem.
This is recorded on the page itself (CORRECTIONS section) rather than
silently dropped, per the skill's "correct yourself in public" rule.

## A real bug found and fixed while verifying this build

The first draft's mobile screenshot (375px viewport) rendered at
**466px wide**, not 375 — confirmed by reading the PNG's own header
bytes directly, not by eye. Isolated the same way this project's own
`wp-prompt-pack-gate` round found an equivalent bug: `overflow-x:
hidden` on `html, body` kept `document.documentElement.scrollWidth`
reporting a clean 375px (which is what the test suite's first draft
checked), while `document.body.scrollWidth` — what a full-page
screenshot actually measures — still showed 466px of real overflow,
all four `<table>` elements (measure/counts/rules/rights) growing past
their container because none had `table-layout: fixed`. Fixed by
adding `table-layout: fixed; width: 100%;` plus `overflow-wrap:
anywhere; word-break: break-word;` to every table cell (and to
`.f-evidence`, where long citation strings live). `test.js` was also
hardened to check `document.body.scrollWidth` in addition to
`document.documentElement.scrollWidth` at both 375px and 1280px, so a
regression of this exact bug can't hide behind the clipped
`documentElement` reading again. Re-screenshotted clean afterward
(confirmed 375×23050 and 1280×10922 via direct PNG header read).

## Verification

- `node test.js`: **345/345 assertions pass** on the real, final run.
- Three new detector types (the per-source credit/stop requirement,
  the source-fingerprint recompute, and the "`--stop` used as text
  colour" check) were each proven to actually fire by planting a real
  counterexample (removing `dummies`'s only stop finding, corrupting
  the stated fingerprint, and swapping `--stop-ink` for `--stop` on
  one CSS rule), confirming the suite failed exactly as expected, then
  restoring the originals and re-confirming a clean 345/345 run.
- Screenshots taken at 1280px and 375px and actually looked at (not
  just overflow-checked) — see `verification/desktop-1280.png` and
  `verification/mobile-375.png`.
- Folder scanned for credential-shaped lines, foreign absolute paths,
  TODO/placeholder text, and external resource loads — the one
  "placeholder" hit found is a finding's own claim text ("not a
  placeholder/invented URL"), read in full and confirmed to be no
  violation. Zero external `<script>`/`<link>`/`<img>` sources.
- `index.html` has no external script, no base64 blobs, and renders
  every number FROM `data.js` — nothing is hardcoded.

## Egress restrictions hit this round

`arxiv.org` is blocked by this sandbox's egress proxy (confirmed again
this round via a direct `curl`, HTTP 403) — consistent with every
other round in this project. The two arXiv papers the Dummies book
cites were verified by web search of their titles/abstracts, not by
downloading and reading the papers themselves; no finding here asserts
anything about either paper's internal content.
