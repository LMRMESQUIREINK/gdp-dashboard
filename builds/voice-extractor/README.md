# Voice Extractor

A real, dependency-free tool that extracts a quantifiable voice profile
from a sample of someone's own writing, and scores a new draft against
it — built from the tone.md/humor.md technique in one of three uploaded
WordPress-via-Claude tutorials ("How I Built INSANE WordPress Websites
In 20 Minutes"), which pastes a real passage and has Claude "decode" it
into a reusable style guide. Full comparative analysis of all three
tutorials this round's upload bundled:
`/notes/wordpress-claude-elementor-tutorials-analysis.md`.

This is the one technique across all three WordPress tutorials that
doesn't depend on a live WordPress install, Hostinger account, Claude
Design, or the Novamira bridge plugin — none of which this sandbox has
— so it's the one piece of that bundle that could actually be built and
tested here, rather than just described. It's also a direct complement
to last round's `/builds/humanizer/`: Humanizer strips generic AI tells
*out* of a draft; this puts a specific, real person's measured voice
*back in*.

## What it does

`voice_profile.py` extracts 8 real, counted signals from a text:
average sentence length, average word length, contraction rate,
first-person rate, exclamation/question/em-dash rates, how often
sentences open with a conjunction (And/But/So), and the most common
sentence openers — all plain regex and arithmetic, no NLP library, same
discipline as every other text-pattern tool in this project.
`voice_match.py` scores a new draft against a saved profile, per metric
and overall, with concrete suggestions ("more first-person voice",
"shorter sentences") for whatever diverges most.

```bash
python3 voice_extractor.py extract sample.txt --save profile.json
python3 voice_extractor.py score draft.md --profile profile.json
python3 voice_extractor.py score draft.md --profile profile.json --min-score 0.8
```

## A real design flaw found and fixed during testing — not assumed away

The first version scored each metric by *relative* difference
(`|reference - draft| / max(reference, draft)`). It looked reasonable
and passed a quick read-through, but the discrimination test caught a
real problem: a hand-written draft intentionally written to sound like
the reference voice scored **lower** (0.526) than an intentionally
generic, corporate-sounding draft on the same topic (0.753) — the
opposite of what the tool exists to measure. Debugged by printing the
actual extracted numbers rather than guessing: on a short sample, a
rare-event metric (first-person use, em dashes) sitting near zero in
the reference turns *any* nonzero value in the draft into a maximal
penalty under relative difference, regardless of how small that value
actually is in absolute terms — a mathematically "correct" computation
that doesn't track real stylistic distance. Fixed by switching to fixed,
declared **absolute tolerances per metric** (8 words of sentence-length
difference, 6 percentage points of first-person-rate difference, and so
on) instead of a self-normalizing relative scale. Re-verified against
the same two drafts: the matching one now scores 0.873, the generic one
0.61 — the direction the tool is supposed to show. The first attempt at
a "matching" test draft also turned out not to statistically match the
reference as well as it read to the eye (shorter sentences, much lower
first-person rate than intended) — caught by printing the real extracted
profile rather than trusting the draft looked right, and rewritten to
actually hit the reference's measured sentence-length and first-person
numbers.

## Verification

`test_voice_extractor.py`, 14/14 passing. The discrimination tests are
the ones that matter, same principle as `humanizer`'s own test suite:
a draft deliberately written to match a reference voice scores 0.873; a
generic draft on the same topic scores 0.61 and gets real, correct
suggestions ("more first-person voice," "shorter sentences") naming
exactly what's different. A CLI round-trip test runs the actual
`extract` and `score` subcommands as real subprocesses against real
files in a temp directory (not in-memory function calls), proving the
saved JSON profile survives a real file round trip. All sample text in
the test suite was written fresh for this build, not reproduced from
the source video transcripts.

```bash
python3 -m unittest test_voice_extractor -v
```

## What's deliberately not built

No actual text rewriting — same reasoning `humanizer`'s README states
for the same cut: a regex-and-arithmetic tool can reliably *measure*
stylistic distance far more confidently than it can *rewrite* a draft
to close that distance without flattening it into something generic.
This tool reports the gap and names the specific signal; closing it is
left to whoever (or whatever) is actually drafting. No semantic/topic
matching either — this measures *how* something is written, not
*what* it says; two drafts about completely different topics in the
same voice should (and do) score well, which is the intended scope, not
a gap.
