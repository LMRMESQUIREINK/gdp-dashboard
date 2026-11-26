# PDF Bundle Auditor

A small, dependency-free Python toolkit for sanity-checking a bundle of
vendor/consulting PDFs uploaded together with no accompanying note — the
exact situation this project hit with three Cloudera/Microsoft PDFs uploaded
at once. Full write-up: `/notes/cloudera-pdf-bundle-analysis.md`.

Three independent checks, each built from a real finding in that round:

## `vintage_check.py`

Flags a bundle whose PDFs span suspiciously far apart in creation date, or
whose own forward-looking forecast year has already passed. The three
uploaded PDFs turned out to span **2019, 2022, and 2026** — confirmed from
each file's own `CreationDate` metadata via `pdfinfo`, not guessed from
content — with the 2019 ebook's own "30 billion connected devices by 2020"
forecast already 6 years lapsed as of today.

## `breakdown_reconciler.py`

Recomputes a weighted average from a document's own stated regional/segment
breakdown and sample sizes, and compares it against a headline figure. Used
to confirm two of Cloudera's "The Great AI Re-Architecture" headline stats
reconstruct cleanly from its own regional table (72% overhaul-needed, 55%
canceled-6+-projects) — and, more interestingly, to recover a **73%**
governance-complexity figure that independent press (Campus Technology)
reported for the same underlying question, which the report's own body text
never states directly (it states only a narrower "29% strongly agree"
figure for that question). Recomputing the weighted average from the
report's own regional "agree" breakdown and its own stated sample sizes
gives 72.7% — matching the press figure almost exactly, and correctly
*failing* to match the report's own "29%" when checked against that instead
(proof the tool can tell two differently-worded questions apart rather than
forcing a reconciliation).

## `citation_tracker.py`

Tracks per-claim citation confidence, forcing a status and a one-line reason
on every claim — no claim can carry a "confirmed" status without a reason
and a source URL. Applied to the four footnoted quantitative claims in
Cloudera's "Empowering Innovation" (2022) ebook, checking each one against
what's actually findable produced four genuinely different outcomes, not a
uniform verdict:

| Claim | Status | Why |
|---|---|---|
| 17.9% revenue uptick, "mature" data science | `CONFIRMED_APPROXIMATE` | Real 2021 DataIQ/Mango Solutions survey of 103 practitioners; the ebook's own "could lead to" hedge already matches the stat's real nature as a self-reported expectation |
| $2.01B Fortune 1000 revenue from 10% usability gain | `UNCONFIRMED` | Named source (datascienceassn.org) is blocked by this sandbox's egress proxy; no independent source repeats the figure |
| 87% of executives say frontline staff would benefit | `CONFIRMED_APPROXIMATE` | Real 2020 HBR Analytic Services/ThoughtSpot report, 464 executives, confirmed via independent coverage |
| IQVIA/pharma CDO quote (preclinical trials 8mo→2mo, trial success 5%→10%) | `SOURCE_LOCATED_UNVERIFIED` | A real Forrester TEI study for CDP Public Cloud exists at the cited URL, but de.cloudera.com is blocked here, so the exact figures inside weren't independently read |

A fifth claim, from the companion edge/IoT ebook ("440x more data than
2006"), is recorded as `CONTRADICTED`: the closest real IDC "Digital
Universe" figure found is a 300x growth **from 2005** (not 2006) — a
different base year and a different multiplier from the same family of IDC
studies.

## Checked `/builds/` first

`manifest-drift-guard` checks file-hash drift against a manifest, not PDF
vintage. `content-provenance-check` checks textual/binary reuse between two
corpora, not citation reliability. `curriculum-link-auditor` and
`readme-link-auditor` check a curated list's claims against a real repo's
README, not a vendor PDF's footnotes or a weighted regional recomputation.
`paired-bootstrap-ratchet` and `provisional-data-gate` check statistical
significance and provisional-data propagation — a different domain. None of
these cover a vendor-PDF-bundle's vintage spread, a regional-breakdown
reconciliation, or a per-claim citation-confidence gradient. Genuinely new.

## Proven

24/24 tests pass on the real run (`python3 -m unittest test_vintage_check.py
test_breakdown_reconciler.py test_citation_tracker.py`), all fixtures drawn
from this round's own real, independently-checked findings (not synthetic
data alone), plus discrimination tests proving each check stays quiet on
clean input (PDFs created the same week, a reconciliation that matches
exactly, an all-confirmed claim set). No bug found in this build's own first
draft — all 24 passed on the first real run, stated plainly rather than
manufactured.

## Deliberately not built

- Automatic PDF metadata extraction wired into the module itself — `pdfinfo`
  was run by hand this round; wiring it in would need a `pypdf`/`pdfplumber`
  dependency this toolkit deliberately stays free of, matching the
  dependency-free convention of `manifest-drift-guard` and
  `skill-md-validator`.
- A live fetcher for the two blocked source domains (datascienceassn.org,
  de.cloudera.com) — both are blocked by this sandbox's egress proxy, the
  same restriction class already documented across this project for
  medium.com, dev.to, nocobase.com, arxiv.org, Hugging Face, Substack, and
  several others.
