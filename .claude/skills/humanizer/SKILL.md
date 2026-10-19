---
name: humanizer
description: Scan a piece of drafted copy for AI-writing tells (filler openers, throat-clearing, buzzwords, false-contrast "it's not just X, it's Y," hedging, stacked transitions) and fix what it finds before calling the copy done. Run this on any sales page, ad copy, proposal, SEO page, or other drafted prose right before presenting it as finished. Triggers on phrases like "humanize this", "does this sound like AI", "check for AI tells", or any request to make copy sound less robotic.
---

# Humanizer

A real pattern-detection check for prose, the equivalent of
`design-rules.md`'s "Generic-AI tells to avoid" section but for
*writing* instead of *visual design* — that section never covered prose
tells, so this fills a real gap rather than duplicating it. Built from
`/builds/humanizer/` (`patterns.py` — 14 real regex rules across 4
categories, dependency-free Python, 15/15 tests passing). Full build
notes, what's deliberately not automated, and the real bug found while
testing it: `/builds/humanizer/README.md`.

## When to run this

Right before calling any drafted copy finished — a sales page
(`sales-page-engine`), ad copy or a launch plan (`launch-pad`), an
agency proposal, an SEO page, or any other prose this project produces.
Same discipline as the don't-say-list grep those two skills already run:
a style rule is only real once it's an actual check, not a guideline
someone has to remember to apply by eye.

## How to run it

```bash
python3 /home/user/gdp-dashboard/builds/humanizer/humanizer.py <file> --max-per-1000-words 5
```

Adjust the threshold by content type — a short, punchy ad variant
tolerates less density than a longer proposal before it starts to read
as padded; when in doubt, look at the actual findings list, not just the
number, before deciding whether a given match is a real problem or a
reasonable turn of phrase.

## What to do with the findings

1. Run it against the draft.
2. For each finding, either cut the phrase (most throat-clearing and
   buzzword matches should just be deleted) or rewrite the sentence to
   say the same thing more directly (false-contrast triplets and hedges
   usually need a rewrite, not a deletion).
3. Re-run it. Don't call the copy done until the count is at a level
   that reflects a deliberate choice, not an unexamined first draft —
   a single buzzword that's genuinely the clearest word available is
   fine; eleven findings in one paragraph is not.
4. Say what you checked and the before/after numbers, briefly — same
   "show the verification step happened" rule `CLAUDE.md` states for
   every other kind of check in this project.

## What this doesn't do

It does not rewrite the copy for you — regex can reliably spot a tell
far more confidently than it can rewrite around one without flattening
the voice into an even more generic replacement. It reports the match,
where it is, and a one-line fix direction; the actual rewording takes
judgment, same reasoning the build's own README states for why an
automated rewriter was cut. It's also not a substitute for
`design-rules.md`'s own do-say/don't-say voice check on a specific
brand — run both: this one catches generic AI-sounding prose, the
brand-specific check catches a brand saying something off-voice.
