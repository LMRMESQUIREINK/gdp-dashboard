# Deep analysis: three bare Cloudera/Microsoft PDFs, uploaded together

Source: three bare PDF uploads, no accompanying instruction — per this
project's convention, the upload itself is the instruction. All three are
Cloudera (one co-branded with Microsoft Azure) marketing/research PDFs,
uploaded as one bundle with no note about how they relate to each other.

## What was measured first

Computed sha256 and real metadata (`pdfinfo`) for all three before reading
any for meaning — the exact thing that turned out to matter most:

| File | Pages | Title | `CreationDate` |
|---|---|---|---|
| `the-great-ai-re-architecture1.pdf` | 10 | The Great AI Re-Architecture | **2026-08-06** |
| `msft-cloudera-edge-ebook.pdf` | 10 | Insights from the Edge (Cloudera + Microsoft Azure) | **2019-08-09** |
| `empowering-innovation-...pdf` | 17 | Empowering Innovation | **2022-07-25** |

**These three PDFs span 2019, 2022, and 2026 — a 2,554-day (7.0-year) gap
between the oldest and the newest, with no accompanying note that two of the
three are years old.** This is the headline structural finding, confirmed
directly from each file's own embedded metadata, not inferred from content.
The 2019 ebook's own content corroborates its real age independently: it
cites an IDC forecast for "30 billion connected devices worldwide by
2020" as forward-looking, and today (2026-11-26) that forecast year is 6
years in the past.

## PDF 1: "The Great AI Re-Architecture" (real, current, independently corroborated)

This is a real, brand-new Cloudera survey report (commissioned with Wakefield
Research, 1,500 Enterprise Architects/Cloud Infrastructure Leads/Data
Architects, fielded June 5–22, 2026). Confirmed via web search against
Cloudera's own August 11, 2026 press release and multiple independent trade
outlets (HPCwire, Campus Technology, CXOToday, ITWire, Data Center Dynamics'
Brazilian edition) — all corroborating the same headline figures (95%
delayed/canceled an AI project, 77% actively using AI, 72% need an
architecture overhaul, 66% repatriated AI workloads from public cloud). A
real, current, well-documented report, not fabricated or exaggerated.

**Internal consistency check (recomputed, not assumed):** the report's own
Methodology section gives exact regional sample sizes (Americas n=800, EMEA
n=400, APAC n=300, total n=1,500). Recomputing the weighted average from its
own regional breakdown reconstructs both of its directly-stated headline
figures almost exactly:

- "72% say their architecture needs a significant overhaul" ← regional data
  (AMER 70%, EMEA 81%, APAC 68%) weighted-averages to **72.53%**.
- "55% delayed/canceled 6+ projects" ← regional data (AMER 54%, EMEA 60%,
  APAC 50%) weighted-averages to **54.8%**.

**The more interesting finding:** the report's own body text states only a
narrower "(29%) strongly agree that AI integration has made data governance
more complex" for one question, but its regional breakdown for that same
question (AMER 81% *agree*, EMEA 65%, APAC 61%) weighted-averages to
**72.73%** — matching a separate **"73%"** figure that independent press
(Campus Technology) reported for this exact question, a number the report's
own prose never states directly even though the data to compute it sits in
its own regional chart two pages later. Checked that this isn't a
coincidence: recomputing against the report's own "29%" instead (the
narrower "strongly agree" subset) correctly fails to reconcile (43.7-point
gap) — proof these are two different questions/metrics, not an error in
either number, and that the 73% press figure is the real rolled-up answer to
the "agree" version of the question the regional chart actually measures.

Minor precision notes, not real errors: several single-select "which
environment" questions on page 7 (hardest to govern: 29/24/20/14/9=96%; best
performance: 30/29/23/9=91%; where inference runs: 31/30/22/8=91%) don't sum
to 100%, most likely an unshown "other/don't know" residual rather than a
data error — flagged, not treated as a finding, since nothing in the report
claims these are exhaustive.

## PDF 2: "Insights from the Edge" (Cloudera + Microsoft Azure, 2019 — stale, not disclosed as such)

Real content for its era, but it is a 7-year-old ebook recirculated with no
date disclosed anywhere in its own visible text (confirmed only by PDF
metadata). Its "30 billion connected devices by 2020, 440x more data than
2006" claim is half-right: the 30-billion/2020 IDC IoT forecast is real and
well-documented (confirmed via multiple independent 2013–2015 tech-press
sources). The "440x since 2006" half could not be corroborated — the closest
real analog found is IDC's own "Digital Universe" study, which states a
**300x** growth from **2005** (not 2006) to 2020 (130 exabytes → 40,000
exabytes). Different base year, different multiplier, same family of IDC
studies — recorded as `CONTRADICTED`, not `UNCONFIRMED`, since a real,
specific, conflicting figure was found rather than silence.

The Harvard Business Review citation (Davenport, "What's Your Data
Strategy?") is real, but two small precision points: the article is
co-authored with Leandro DalleMule (not Davenport alone, as the footnote's
single-author framing implies), and its real wording is "less than half" of
structured data and "less than 1%" of unstructured data — the ebook's "only
50%"/"only 1%" is a reasonable rounding of "less than half"/"less than 1%,"
not a distortion.

**Credit:** the Clearsense case study is real and independently
corroborated — a genuine Cloudera customer relationship (confirmed via
Cloudera's own hosted case-study PDF and a third-party casestudies.com
listing), and Clearsense appears to still be an active company as of 2026
(a February 2026 press release referencing it was found), with no evidence
of the acquisition-or-shutdown pattern this project has had to check for in
other rounds. The specific product/positioning claims in the case study
("first to deliver smart, real-time streaming data... Inception™ product")
are consistent with real third-party coverage, not found to be exaggerated.

## PDF 3: "Empowering Innovation" (Cloudera, 2022 — explicitly dated, but still 4 years stale)

Unlike PDF 2, this one honestly states its own vintage ("© 2022 Cloudera,
Inc.," "Second in our Data Leaders series") — a real, checkable contrast
within the same three-PDF bundle: one ebook hides its age, one states it
plainly.

Four footnoted quantitative claims, checked individually — see
`/builds/pdf-bundle-auditor/README.md` for the full table. In short: the
17.9% revenue-uptick figure and the 87% ThoughtSpot/HBR figure both check out
(the former correctly hedged by the ebook's own "could lead to" phrasing,
since it's a self-reported survey expectation, not a measured outcome); the
$2.01B Fortune 1000 figure could not be independently corroborated at all
(its named source, datascienceassn.org, is blocked by this sandbox's egress
proxy, and no secondary source repeats it); and the anonymized pharma-CDO
quote (CDP Public Cloud, preclinical trials 8→2 months, trial success
5%→10%) traces to a real, locatable primary source — a Forrester Total
Economic Impact study for CDP Public Cloud, found via web search at a real
URL — but de.cloudera.com is also blocked here, so the exact figures inside
that study weren't independently read. This is a genuinely different
category from a bare, unsourced claim: the document did cite a real,
specific, findable report; this sandbox's network restrictions, not the
document's own rigor, are what's incomplete here.

## Checked `/builds/` first

No existing build in this project checks PDF bundle vintage via metadata,
reconciles a weighted regional breakdown against a stated headline, or
tracks per-claim citation confidence across a document's footnotes.
`manifest-drift-guard` checks byte-hash drift, `content-provenance-check`
checks textual reuse, `curriculum-link-auditor`/`readme-link-auditor` check
a list's claims against a repo's README, `paired-bootstrap-ratchet` and
`provisional-data-gate` check statistical significance and provisional-data
propagation. A genuinely new gap.

## Built

`/builds/pdf-bundle-auditor/` — three small, dependency-free Python modules
(`vintage_check.py`, `breakdown_reconciler.py`, `citation_tracker.py`),
tested against this round's own real, independently-checked figures as
fixtures (not synthetic data alone), plus discrimination tests proving each
check stays quiet on clean input. 24/24 tests pass on the real run. No bug
found in this build's own first draft — all 24 passed first try, stated
plainly rather than manufactured. Full README in the build directory.

## Deliberately not built

- Automatic PDF metadata/text extraction wired into the toolkit itself —
  `pdfinfo` and the PDF-reading tool were run by hand this round; adding a
  `pypdf`/`pdfplumber` dependency would break the dependency-free convention
  this toolkit shares with `manifest-drift-guard` and `skill-md-validator`.
- Resolving the two genuinely blocked verification gaps (the Data Science
  Association PDF, the Forrester TEI PDF) — both domains are blocked by this
  sandbox's egress proxy, confirmed via direct fetch attempts, the same
  restriction class already documented across this project for dozens of
  other domains.
