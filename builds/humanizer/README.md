# Humanizer

A real, dependency-free Python detector for AI-writing tells — built from
the "Humanizer" idea in the uploaded "7 claude skills that print money"
article ("catches 26 patterns of AI writing... 50k+ stars"). Neither the
26-pattern list nor the star count could be checked from this sandbox (no
live GitHub access to the repo named in the article, and the article
itself names no list of the 26), so this is an independent set of real
detectors built from first principles, not a reproduction of that repo's
actual rules.

Fills a real, previously-open gap in this project rather than duplicating
anything: `design-rules.md`'s existing "Generic-AI tells to avoid" section
covers *visual* tells (palettes, buttons, stock photos); nothing in this
project checked *prose* tells until now.

## What it does

`patterns.py` exports `scan(text)` (every match, in order, with a
suggestion) and `score(text)` (counts, density per 1000 words, em/en-dash
density, a per-category breakdown). 14 rules across 4 categories:
throat-clearing (filler openers, "it's important to note that," unneeded
conclusion signals), rhetorical tics (the "it's not just X, it's Y" false
contrast, stacked transitions, "whether you're a beginner or an expert"),
hedging (vague qualifiers, stacked intensifiers), and buzzwords (leverage,
seamless, robust, cutting-edge, revolutionize, delve into, and more).

```bash
python3 humanizer.py draft.md
python3 humanizer.py draft.md --max-per-1000-words 5   # exit 1 if too dense
python3 humanizer.py draft.md --json
cat draft.md | python3 humanizer.py -
```

## What's deliberately not built

A full automated rewriter — the article's own framing ("run that text
through Humanizer before it goes out") suggests it rewrites, but a
regex-based tool can reliably *detect* a tell with far more confidence
than it can *rewrite around* one without changing meaning or introducing
an even more generic replacement phrase. This tool reports the match,
its location, and a one-line fix direction; the actual rewording is left
to whoever (or whatever) is editing the draft — consistent with this
project's own established discipline of not shipping an automated step
that would need judgment it can't actually apply. A "rule of three"
listicle-density check was considered and cut: flagging arbitrary
three-item comma lists is too false-positive-prone (plenty of real,
specific three-item lists are not AI tells) to ship as a hard rule.

## Verification

`test_patterns.py`, 15/15 passing. The test that actually matters is
`test_ai_sounding_paragraph_scores_high` vs.
`test_human_sounding_paragraph_scores_at_or_near_zero`: a real paragraph
stacking the tells this project and the source article both name scores
11 findings across 4 categories; a real paragraph (an engineer describing
an actual bug fix, phrased plainly) scores exactly 0 — proving the tool
discriminates, not just that each regex matches something in isolation.
Every individual rule also has its own positive and negative test,
including two deliberate near-miss cases pinned down while writing the
tests (`"not just the one we expected"` with no `it's` beforehand must
not trip the false-contrast rule; `"and moreover it was cheaper"` with no
sentence-opening comma must not trip the stacked-transitions rule) — real
edge cases that would have been false positives if left unchecked, not
hypothetical ones.

**A real bug found while writing the tests**: the `stacked-intensifier`
rule's first version required the two intensifiers to be separated by
whitespace only (`truly really`), so it missed the more common real
phrasing with a comma between them (`truly, really`) — caught by a test
against realistic AI-sounding text, not synthetic edge cases, and fixed
by allowing an optional comma in the pattern.

```bash
python3 -m unittest test_patterns -v
```

## Using it

Point it at a draft before publishing — the CLI's `--max-per-1000-words`
flag makes it a real gate, not just a report, the same way the sales-page-
engine/launch-pad skills' don't-say-list grep already gates brand voice in
this project. The matching skill, `.claude/skills/humanizer`, wires this in
as the step that runs right before any drafted copy (a sales page, ad
copy, a proposal, an SEO page) is called finished.
