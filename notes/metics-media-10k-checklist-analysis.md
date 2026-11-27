# Deep analysis: "The $10K Checklist" (Metics Media, Field Guide No. 01)

Source: a single-page PDF, uploaded with no accompanying text — same
bare-file-reference pattern as the WordPress prompt pack round, handled
the same way (no trigger phrase needed; a bare PDF upload is this
project's own established signal to run the deep-analysis treatment).

## Measured, not assumed

- `sha256: 8c864c56b7de1905a0826800772c9028b5a78a83c37a1b69bcf3ce28b1eb6163`,
  114,807 bytes, single page.
- Extracted via `pdftotext -layout` (reproducible, not retyped by eye):
  **297 words**, 8 numbered items, a title block, and a footer.
- Branding: "METICS MEDIA · FIELD GUIDE NO. 01 · CLAUDE CODE ERA ·
  MMXXVI" (2026 in Roman numerals) at the top; "METICS MEDIA · A FIELD
  GUIDE FOR THE CLAUDE CODE ERA · ONE OF ONE" at the foot.
- **Zero links, URLs, or affiliate markers anywhere in the document** —
  checked by grepping the full extracted text for `http`/`www.`/`.com`/
  `affiliate`/`click`/`bit.ly`: zero matches. Worth stating precisely
  because it's a real, checkable contrast with the other two Metics
  Media pieces this project has already audited (the WordPress prompt
  pack, `-HZU` tracking suffix; the "10k-websites" Higgsfield skill,
  `-ESVT` tracking suffix) — both of those carried embedded funnel
  links, and this one carries none. Most likely read: this is the
  free, top-of-funnel "field guide" stage of a content family whose
  monetization lives in the other pieces, not a funnel artifact itself
  — stated as the most likely explanation, not confirmed, since nothing
  in the document itself says so.

## The one finding that matters: an exact, mechanically-confirmed 8/8 match

This project already built `/builds/ten-k-website-grader/` several
rounds ago, from a separate source: a YouTube transcript, "Build
$10,000 Websites using Claude Code (Ultimate Guide)," whose own
8-pillar checklist was credited in `/notes/10k-website-claude-code-
analysis.md` as "point of view, typography, colour, hierarchy,
imagery, motion, mobile, 'the invisible stuff.'"

Checked directly, not from memory: `grep`'d
`builds/ten-k-website-grader/ten_k_grader.py` for its own pillar
names. Its `for name in (...)` loop and its individual
`PillarResult(...)` calls name exactly: **point-of-view, typography,
colour, hierarchy, imagery, motion, mobile, invisible-stuff** — eight
items, in that exact order.

Metics Media's checklist, independently: **01 Point of view, 02
Typography, 03 Color (system), 04 Hierarchy, 05 Imagery, 06 Motion, 07
Mobile, 08 The invisible expensive stuff** — eight items, same order,
near-identical wording on several (both single out "Inter or Roboto"/
`Inter` as the specific tell of a cheap site; both use "felt"/"feel"
as the operative word for pillar 8).

That is an 8-for-8 category match, in identical order, between two
documents with no citation of each other. Neither the video (per the
earlier round's analysis) nor this PDF credits the other, or any
shared source, for the taxonomy. Three things are now true at once,
and none of them resolve which is true:

1. One operator produced both the video and this field guide, and
   simply didn't cross-link them.
2. Both draw on a shared, uncited original (a designer's checklist
   that's become informally standard in this exact "vibe-coded
   premium site" niche) that neither source discloses.
3. Pure coincidence — possible, but an 8/8 ordered match on a
   subjective design taxonomy is a much higher bar to attribute to
   chance than, say, two sources independently naming "typography" or
   "mobile" as a factor.

Stated as an open finding, not resolved in either direction, since
nothing in either document settles it. What *is* resolved: this
project's own grader, built independently in an earlier round before
this PDF ever arrived, is now an unplanned third data point confirming
the taxonomy is stable across at least two unrelated-by-citation
sources — not evidence that Metics Media originated it, since the
grader was built from the video, not from this PDF.

## What doesn't need checking here

Unlike every other source this project has audited, this one makes no
factual, numeric, or technical claims to verify — no statistics, no
named tools, no version numbers, no dated events. It's eight sentences
of design opinion. The only genuinely checkable thing in it is the
taxonomy match above, which has been checked directly rather than
eyeballed.

## What's built from this

Nothing new. The one concrete idea in this document — the 8-pillar
checklist — is already implemented, more rigorously than this PDF
states it, in `/builds/ten-k-website-grader/`, including the honest
caveat that document already carries (point of view, most of imagery
quality, and whether motion *feels* premium are not checkable from
files on disk alone — this PDF's own prose confirms the same limits:
"the felt difference," "a designer would nod," "feels chosen" are all
explicitly subjective-judgment language, not something a script can
grade). Building a second implementation of the same eight categories
from a shorter, less detailed restatement of them would add nothing.
