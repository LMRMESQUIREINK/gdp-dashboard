# PDF Bundle Auditor

A small, dependency-free Python toolkit for sanity-checking a bundle of
vendor/consulting PDFs uploaded together with no accompanying note — the
exact situation this project hit twice: first with three Cloudera/Microsoft
PDFs (`/notes/cloudera-pdf-bundle-analysis.md`), then with three more
Cloudera ebooks that extended the tool rather than duplicating it
(`/notes/cloudera-second-pdf-bundle-analysis.md`).

Three independent checks, each built from a real finding, and extended by a
second round's real findings:

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

**Extended in round two** with `find_cross_document_echoes()`: the exact
same `$2.01B`/`datascienceassn.org` claim above reappears nearly verbatim in
a second, separate Cloudera ebook ("7 Elements of a Winning Enterprise Data
Strategy," 2022) — the same unreachable source backing the same unverified
number in two documents from the same vendor. That's not independent
corroboration; it's one unconfirmed source copy-pasted. The function groups
claims by `source_url` across documents and flags any URL that backs a claim
in more than one document while never once reaching a `CONFIRMED` status —
and correctly leaves alone a source reused *within* one document, or a
source that's confirmed anywhere in its history. The same round also found
three claims from a different source (NewVantage Partners' real 2022 "Data
and AI Executive Survey") that check out exactly once actually located
(92.1% measurable results, 91.9%→92% culture-as-impediment, 26.5%→27%
data-driven organization) — proof the echo check isn't "vendor numbers are
always suspect," only that a repeated *unverified* one shouldn't gain
credibility from repetition.

`breakdown_reconciler.py` also gained `check_claimed_multiple()`: "7
Elements" states hybrid/multi-cloud adoption is "set to triple (from 12%
to 36%)" in the next 18 months — a self-contained before/after/multiplier
claim, recomputed directly (36 / 12 = 3.0 exactly) rather than a weighted
average. It checked out — included so the mechanism isn't only ever shown
catching a problem.

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

36/36 tests pass on the real run (`python3 -m unittest test_vintage_check.py
test_breakdown_reconciler.py test_citation_tracker.py`, up from 24), all
fixtures drawn from real, independently-checked findings across both rounds
(not synthetic data alone), plus discrimination tests proving each check
stays quiet on clean input (PDFs created the same week, a reconciliation
that matches exactly, an all-confirmed claim set, a source reused within one
document, a source confirmed anywhere in its history). No bug found in
either round's own first draft — all tests passed on the first real run
each time, stated plainly rather than manufactured.

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
