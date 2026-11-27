# Deep analysis: a second bare Cloudera PDF bundle, uploaded together

Source: three more bare PDF uploads, no accompanying instruction — same
convention as the first Cloudera PDF-bundle round
(`/notes/cloudera-pdf-bundle-analysis.md`). All three are Cloudera ebooks;
unlike that first round, none is a brand-new 2026 report — all three are
from 2021–2022.

## What was measured first

| File | Pages | `CreationDate` |
|---|---|---|
| `7-elements-of-a-winning-data-strategy.pdf` | 14 | 2022-11-17 |
| `how-to-build-a-foundation-for-exploratory-data-science-with-cml-on-aws.pdf` | 11 | 2022-09-23 |
| `5-enterprise-public-cloud-use-cases.pdf` | 16 | 2021-03-23 |

Spread: ~20 months (Mar 2021 → Nov 2022) — under
`/builds/pdf-bundle-auditor/vintage_check.py`'s default 2-year threshold, so
the tool correctly does **not** flag this bundle, unlike the first round's
7-year spread. A useful negative-case confirmation that the threshold
actually discriminates rather than firing on every multi-PDF upload.

## "7 Elements of a Winning Enterprise Data Strategy" (2022)

**Credit — honest scope disclosure**: the intro states the source webinar
covered 5 elements, and this ebook "teased out an additional two" to make
7 — a direct, named expansion rather than an unexplained mismatch between a
"Top 5" webinar title (cited as footnote 2) and a "7 Elements" ebook title.

**The round's strongest finding**: footnote 5 cites
`datascienceassn.org/.../Measuring%20Business%20Impacts...` for "$2.01B in
additional total revenue" if the median Fortune 1000 firm increased data
usability by 10% — the **exact same claim, from the exact same unreachable
source URL**, that the first PDF-bundle round already flagged as
`UNCONFIRMED` in Cloudera's separate "Empowering Innovation" (2022) ebook.
This version adds one more specific detail not present in the earlier one
("equivalent to nearly $56,000 more annual revenue per employee") — checked
for internal consistency: $2.01B ÷ $56,000/employee implies ~35,900
employees for "the median Fortune 1000 firm," a plausible, not implausible,
figure for a company that size, so the added detail is at least
self-consistent even though the underlying $2.01B claim's ultimate source
remains unreachable. The real point: **the same unverified source appearing
twice across a vendor's own content library is not independent
corroboration** — it's one unchecked number copy-pasted into two decks, and
should not be treated as more trustworthy for having been repeated. Built
into `/builds/pdf-bundle-auditor/citation_tracker.py` as
`find_cross_document_echoes()`.

**A second, smaller finding**: footnotes 3 and 4 both cite the identical
ZDNet URL (`enterprises-are-collecting-more-data-but-do-they-know-what-to-
do-with-it`) for two different statistics (43% of captured data goes
unused; 44% of data goes uncaptured) on the same page. The article itself
could not be found via web search — ZDNet has restructured its archive
repeatedly over the years, so this is reported as unconfirmed-via-search,
not as evidence the article never existed.

**Three unfootnoted internal-survey stats** (page 6's "Top 3 Data Sources,"
page 7's "91% say data strategy is a prerequisite for resiliency," page 9's
"just 12% [are] engaged with each... component of the data lifecycle") carry
no footnote marker at all, unlike the NewVantage- and ThoughtSpot-sourced
stats elsewhere in this project's Cloudera-ebook rounds — a real, checkable
contrast in citation rigor within the same document, not a flag on any one
number.

**Two internal-consistency checks, both clean (`computed`)**: "hybrid/multi-
cloud adoption is set to triple (from 12% to 36%)" — 36 ÷ 12 = exactly 3,
checked directly via the new `check_claimed_multiple()`. And the "just 12%"
full-lifecycle-engagement figure against the six per-stage engagement rates
shown two pages earlier (64/62/61/56/51/50%): naive independence would
predict roughly 3.5% engaging with all six, so the real reported 12% is
higher than independence alone would produce — consistent with positively
correlated engagement across stages (data-mature orgs engage broadly) rather
than a contradiction, noted as a plausibility check rather than a flag.

## "How to Build a Foundation for Exploratory Data Science with CML on AWS" (2022)

**Credit — all three footnoted claims check out exactly.** Page 3 cites
NewVantage Partners' real 2022 "Data and AI Executive Survey" (94 Fortune
1000/leading-organization respondents) for three figures: "92.1% ... achieving
measurable results," "92% ... cultural challenges are the greatest
impediment," and the sidebar's implied "27%" data-driven-organization rate.
A first web search was contaminated by an unrelated firm's (Wavestone)
coincidentally similar 92.1% figure for a *different* question (investment
increase, not measurable results) — corrected with a second, more targeted
search that found NewVantage's actual release: 92.1% measurable results
(exact), 91.9% culture-as-impediment (rounds to 92%), 26.5% data-driven
organization (rounds to 27%). All three check out precisely against the
primary source. This is the cleanest fully-verified citation set in either
PDF-bundle round, and it matters for the echo-detection finding above: some
vendor citations genuinely hold up on inspection, so flagging a *repeated,
unverified* one is about the repetition, not a blanket "vendor numbers can't
be trusted."

**Globe Telecom case study**: the Cloudera/Globe Telecom customer-
segmentation relationship is real and well-documented across many
independent sources (AWS's own case-study page, Cloudera's customer page,
Light Reading, The Fast Mode, PRNewswire) — but the specific "600PB of data"
and "66% year-over-year growth in mobile data volume" figures in this ebook
were not corroborated by any of those other sources. A real, checkable
contrast: the relationship is solid, these two specific numbers aren't
independently echoed anywhere found.

## "Five Enterprise Public Cloud Use Cases" (2021)

This is the exact ebook a web search in the earlier "Empowering Innovation"
round surfaced as "a biopharmaceutical case study... doubled R&D
productivity" — reading it directly this round resolves that thread rather
than leaving it dangling: it's a **different, separate, fully anonymous**
biopharmaceutical customer (never named) with its own "2x R&D productivity"
metric, distinct from "Empowering Innovation"'s named IQVIA story (70 teams,
"insights in seconds not days") and distinct from that same ebook's
separately-anonymized, Forrester-TEI-quoted "Chief data and analytics
officer, pharmaceuticals" (preclinical trials 8mo→2mo, trial success
5%→10%). This ebook adds a **fourth** distinct life-sciences story on top
(a different anonymous customer: "4x faster patient qualification," "72x"
data-processing speed, "4x" prediction-accuracy improvement). All five case
studies in this ebook are fully anonymous — a real, checkable contrast with
the CML/AWS ebook's named Globe Telecom story. Worth naming plainly, not as
an accusation (anonymized case studies are completely normal practice), but
as context: Cloudera's own marketing library contains at least four
non-cross-referenced pharma/life-sciences "transformation" stories, three of
them fully anonymous, each with its own distinct multiplier metric, none
citing or reconciling with the others.

## Checked `/builds/` first

This round's findings are extensions of exactly the mechanism
`/builds/pdf-bundle-auditor/` already implements, not a new gap — extended
rather than duplicated. See that build's README for the two new functions
(`find_cross_document_echoes()`, `check_claimed_multiple()`) and their test
coverage.

## Built / extended

`/builds/pdf-bundle-auditor/citation_tracker.py` gained
`find_cross_document_echoes()` and a `document` field on `Claim`;
`breakdown_reconciler.py` gained `check_claimed_multiple()`. 36/36 tests
pass on the real run (up from 24), all new fixtures drawn from this round's
own real, independently-checked figures. No bug found in this round's own
extension, stated plainly rather than manufactured.

## Deliberately not built

- Resolving the ZDNet dual-citation (the article wasn't locatable via
  search — stated as unconfirmed, not disproven).
- A live fetch of the datascienceassn.org source to settle the $2.01B claim
  once and for all — still blocked by this sandbox's egress proxy, the same
  restriction already documented for this exact URL in the first
  PDF-bundle round.
