# Deep analysis: a third bare Cloudera/Kyndryl/AWS PDF bundle

Source: three more bare PDF uploads, no accompanying instruction — same
convention as the first two Cloudera PDF-bundle rounds
(`/notes/cloudera-pdf-bundle-analysis.md`,
`/notes/cloudera-second-pdf-bundle-analysis.md`).

## What was measured first

| File | Publisher | Pages | `CreationDate` |
|---|---|---|---|
| `blueprint-for-continuous-operations-for-production-machine-learning.pdf` | Cloudera | 27 | 2021-11-16 |
| `achieving-a-data-driven-transformation.pdf` | Kyndryl / Cloudera | 11 | 2022-09-15 |
| `how-to-take-ai-applications-from-concept-to-reality-with-cml-on-aws.pdf` | Cloudera (AWS Partner) | 13 | 2022-09-23 |

Spread: ~10 months (Nov 2021 → Sep 2022) — well under
`/builds/pdf-bundle-auditor/vintage_check.py`'s default 2-year threshold, a
second negative-case confirmation (round two's bundle, ~20 months, was also
correctly left unflagged).

**Notable by itself**: the third PDF here (`concept-to-reality-cml-aws`) and
round two's "How to Build a Foundation for Exploratory Data Science with CML
on AWS" were both created **2022-09-23** — the same day, per each PDF's own
`CreationDate` metadata — a zero-day spread between two documents from two
different upload rounds, not just a tight bundle within one round.

## "Blueprint for Continuous Operations for Production Machine Learning" (2021)

By Jeff Fletcher and Ade Adewumni — introduces "Continuous Operations for
Production Machine Learning" (COPML), a methodology distinct from generic
Continuous Delivery, covering workflow, infrastructure, automation, and
regulatory requirements (auditability, reproducibility, explainability) for
production ML. Two real GitHub-linked example projects
(`fastforwardlabs/COPML-AMP-1-telco-churn`, `COPML-AMP-2-xray`) illustrate the
methodology end to end.

**Credit**: the document's "Hidden Technical Debt of Machine Learning
Systems" diagram (page 5) — a small ML Code box surrounded by Configuration,
Data Collection, Feature Extraction, Data Verification, Analysis Tools,
Process Management Tools, Serving Infrastructure, Monitoring, and Resource
Management — accurately reproduces the real, well-known figure from Sculley
et al.'s widely-cited 2015 NeurIPS paper of the same name. No fabrication or
distortion found in a document this project could otherwise have expected to
oversimplify a technical source.

**A genuinely well-reasoned, checkable illustration, not a vendor stat**: the
pneumonia-detection scenario's worked base-rate example (1-in-100 patients
has pneumonia; a model that always predicts "normal" would be 99% accurate
while catching zero real cases) is correct, internally consistent arithmetic
used to make a real point about why statistical accuracy alone is
insufficient for an imbalanced classification problem — credited as sound
reasoning rather than treated as a claim needing external verification, since
it's a worked illustration, not an empirical result.

No footnoted external statistics appear in this document beyond the Hidden
Technical Debt paper citation and a GDPR Article 22 reference (both checked
out as real, accurately described).

## "Achieving a Data-Driven Transformation" (Kyndryl/Cloudera, 2022)

A joint Kyndryl/Cloudera ebook (authors: Monique Mol Kobeh, Cloudera;
Naveen Kamat, Kyndryl) built around four named customer case studies, each
attributed to a named company logo (Numberly, BT Group, FinOps
Foundation/an unnamed manufacturing client, RingCentral) plus two unnamed
healthcare/smart-factory engagements.

**Checked**: BT Group's "200-250 percent ROI in one year" claim traces to a
real, specific source — a direct quote from Phillip Radley, BT's own chief
data architect, in Cloudera's August 2015 press release and an accompanying
slide deck ("Our one-year return on investment from Hadoop deployment is in
the 200 percent to 250 percent range"). Recorded `SOURCE_LOCATED_UNVERIFIED`,
not `CONFIRMED`: it's a real, traceable vendor-channel customer quote, never
independently audited — and this 2022 ebook presents a 2015-vintage case
study (7 years stale by republication) with no date attached anywhere in the
text, the same undated-case-study pattern found below in the Western Union
case.

**Credit**: Numberly's "50 countries" and "20 percent reduction in customer
acquisition costs" and FinOps Foundation's "nine PaaS services... 80 percent
of costs" are both specific, plausible, internally consistent figures — none
contradicted by anything found, though none independently re-confirmed this
round either (lower priority given BT Group and Western Union's sharper,
checkable claims in this bundle).

A quoted endorsement from Shelly Kramer, Futurum Research, dated "March
2021," is a real analyst/real firm (Futurum Research, now part of The
Futurum Group) — the attribution itself checks out; the substance of the
quote (a general partnership endorsement, not a quantitative claim) isn't
independently checkable.

## "How to Take AI Applications from Concept to Reality with CML on AWS" (2022)

**The round's sharpest finding**: page 3 headlines, in large display type,
"**44%** of high AI performers have a clear data strategy that supports and
enables AI, compared to **21%** of other respondents," footnoted to
McKinsey's "The state of AI in 2020" (17 November 2020). McKinsey's own 2020
report is itself blocked by this sandbox's egress proxy (`mckinsey.com`,
extending the same restriction class already documented for
datascienceassn.org and de.cloudera.com), so this was checked via two
independent secondary sources that each quote the report's own exhibit
directly: the real pairing for this exact item ("a clear data strategy
supports and enables AI") is **44% (AI high performers) vs. 31% (all other
respondents)** — not 21%. The 44% half of the claim is correct; the
comparison figure is wrong, and wrong in a direction that inflates the
apparent gap: the ebook's own arithmetic implies a 23-point gap (44−21),
nearly double the real 13-point gap (44−31). Recorded `CONTRADICTED`.

One secondary source also surfaced a different, earlier McKinsey figure for a
near-identical item from the *2019* survey (65% vs. 20%) — flagged explicitly
as a separate year's number, not to be confused with the 2020 figure this
ebook cites.

**Checked and confirmed**: Gartner's "80% of organizations seeking to scale
digital business will fail because they do not take a modern approach to
data and analytics governance" (cited to a 12 January 2021 Gartner piece)
matches a real 2021 Gartner strategic planning assumption tied to that year's
Market Guide for Data and Analytics Governance Platforms, corroborated by
independent secondary coverage (a PRNewswire release quoting the same Market
Guide, Architecture & Governance Magazine). One precision note worth
recording: a *different*, later Gartner prediction (2024, about 2027) uses
the same "80%" figure for a related but distinct governance-initiative
claim — the two should not be conflated, and this ebook's citation matches
the 2021 one, not the 2024 one. Algorithmia's "40% of companies take more
than 30 days to deploy a single ML model" (cited to "The 2020 state of
enterprise machine learning") matches Algorithmia's real, hosted 2020 survey
report (745 respondents, Oct 2019 fieldwork) almost exactly — "more than a
month" and "more than 30 days" are the same claim. Both `CONFIRMED_
APPROXIMATE`.

**A real, instructive finding in how a case study gets assembled**: the
Western Union sidebar states, as one seamless sentence, "Processing 29
transactions per second, Western Union's data set exceeds 100 terabytes.
With an enterprise data hub from Cloudera, Western Union is able to support
60X faster data loading." Checked piece by piece rather than as a unit: the
"29 transactions per second" figure is real, traceable to Cloudera's own
February 2014 press release (based on 2013 data) — but a 2018 Datanami
article citing 2017 data gives 32/second instead, so even this figure is a
dated snapshot presented with no date attached. The "100 terabytes" figure
does **not** come from any Cloudera-published source found; it traces to an
independent InformationWeek estimate ("roughly 100 terabytes of data
generated by 700 million transactions a year") — a different outlet's
number, blended into the same sentence as Cloudera's own figure as if both
came from one unified, current source. The "60X faster data loading" claim
has no corroborating source found anywhere. Recorded as three separate
claims with three different outcomes (`CONFIRMED_APPROXIMATE`,
`SOURCE_LOCATED_UNVERIFIED`, `UNCONFIRMED`) rather than one bundled verdict,
since the three sub-claims genuinely have three different evidentiary
footings.

## The round's structural finding: an uncitable echo across two upload rounds

This ebook and round two's "How to Build a Foundation for Exploratory Data
Science with CML on AWS" — created the **same day** per their own
`CreationDate` metadata — both state a near-identical Globe Telecom claim:

> "Globe Telecom manages 600PB of data with CML on AWS, driving **[a strategy
> that supports]** 66% year-over-year growth in mobile data volume."

(The bracketed clause is present only in this round's version.) Round two
already found that neither the 600PB nor the 66% YoY figure is independently
corroborated anywhere, despite the broader Globe Telecom/Cloudera
relationship itself being real and well-documented. The new finding this
round is structural, not just a repeat: this claim carries **no footnoted
source_url at all** — it's Cloudera's own self-authored customer metric, not
an external citation — so `/builds/pdf-bundle-auditor/citation_tracker.py`'s
existing `find_cross_document_echoes()` (which groups claims by `source_url`)
is structurally unable to catch it being recycled across documents. Confirmed
directly: running the existing function against both claims returns zero
findings.

**Built**: `find_cross_document_text_echoes()`, which groups claims by their
own normalized text instead of an external citation, closing the gap for
exactly this shape of claim — a vendor's own case-study number, reused
verbatim across its content library with no new verification attached either
time. **A real bug was found and fixed in this new function's own first
draft**: it originally grouped claims by exact normalized-string equality,
and failed on its own motivating test case on the first real run, because the
two Globe Telecom sentences are near-verbatim, not byte-identical (one
inserts "a strategy that supports" mid-sentence) — real-world repetition is
near-verbatim, not identical, so exact-match grouping was the wrong tool.
Fixed by switching to a `difflib.SequenceMatcher`-based similarity threshold
(0.85) over normalized text, confirmed against both the real catching case
and a deliberately differently-worded pair of Globe Telecom sentences that
correctly does not match.

## Checked `/builds/` first

Same toolkit as the first two rounds — extended, not duplicated.
`manifest-drift-guard` checks file-hash drift, not claim-text similarity;
`content-provenance-check` checks textual reuse between two independent
corpora (e.g. two different authors' code), a different shape of problem
from one vendor's own marketing claim recurring across its own documents.

## Built / extended

`/builds/pdf-bundle-auditor/citation_tracker.py` gained
`find_cross_document_text_echoes()` (plus the `TextEchoFinding` dataclass).
49/49 tests pass on the real run (up from 36), including the real bug found
and fixed in this function's own first draft, documented as a permanent
regression test rather than silently corrected.

## Deliberately not built

- A live fetch of mckinsey.com to read the 2020 report's exhibit directly —
  blocked by this sandbox's egress proxy, the same restriction class already
  documented for datascienceassn.org and de.cloudera.com.
- Merging `find_cross_document_echoes()` and `find_cross_document_text_echoes()`
  into one function — they catch genuinely different failure shapes (a
  shared external citation vs. a bare self-authored sentence), and keeping
  them separate keeps "why did this fire" legible.
