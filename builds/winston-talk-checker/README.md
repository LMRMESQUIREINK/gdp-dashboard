# winston-talk-checker

A dependency-free Python tool that mechanically checks a deck (slides +
optional speaker notes) against Patrick Winston's "How to Speak" rules
(MIT RES.TLL-005) — built from a pasted Substack article and verified
against the real lecture before anything was implemented. Full analysis:
`/notes/winston-talk-checker-analysis.md`.

## Why this exists

The source article ("The presentation rules MIT taught its students,
turned into a Claude skill," Frank Andrade/Artificial Corner) describes
a paid Claude skill that applies Winston's rules to a deck — the skill
itself is paywalled and was never seen by this build. What's here is
independently written from the real, underlying MIT lecture (verified
via two separate sets of real lecture notes, not the article's
paraphrase), the same "extract the generalizable mechanism, never clone
the vendor's paywalled instance" discipline this project applies
whenever a source names a paid/closed product (REA, deer-flow,
AgentsKit.co's tools, NocoBase's own listicle series).

## What was verified, and what wasn't

Before writing any check, every one of the article's 7 specific
claims about the real lecture was checked against two independent sets
of real lecture notes (not the article's own paraphrase):

| Claim | Status |
|---|---|
| No logos/clutter/background decoration on slides | **Confirmed**, both sources |
| Use arrows on slides, not a laser pointer | **Confirmed**, both sources |
| Five things make a talk memorable: Symbol/Slogan/Surprise/Salient idea/Story | **Confirmed**, both sources, exact wording |
| End on a "Contributions" slide, not "Thank you"/"Questions?"; don't literally say "thank you" last | **Confirmed in substance** — but one of the two sources frames "Contributions" as *"perhaps better,"* not an absolute rule, and "salute the audience" as one of three closing options, not the only one. The article states both as firm rules; the real notes are softer. |
| Wait ~7 seconds after asking the audience a question | **Not found** in either source |
| Minimum slide font size of "40 points or more" | **Not found** in either source — both only say the font "must be large to be legible," no number |
| ~20% of any audience is mentally checked out at any moment | **Not found** in either source |

Three specific, confident-sounding numbers in the article (7 seconds,
40 points, 20%) don't trace to either independently-checked source —
not proven false, just unconfirmed, and this build does not implement
checks around any of the three unverified numbers (no timed-pause
check, no literal "40pt" font check, no 20%-of-room simulation).

Frank Andrade / Artificial Corner is a real, existing Substack
newsletter (confirmed via its own About page and a linked Substack
profile) — but the article's own claimed "93,000 people read it every
week" couldn't be independently confirmed to that exact figure; the
only public number found (a related Substack profile) shows "51K+,"
a different metric from a different page, not confirmed as the same
count.

## What this checks (and what it honestly doesn't)

Real, mechanical checks over a deck's own text:

- Opening states a promise (not just an agenda)
- Final slide isn't "Thank You"/"Questions?"/"Conclusions"/"The End"
- Final slide reads as a contributions-style summary (**warning**, not
  a hard failure — per the real-notes nuance above)
- Final spoken words don't literally end on "thank you"
- Per-slide word count stays under a threshold (default 40)
- A declared main idea actually appears in the opening, a middle
  slide, and the closing (Winston's "say it three times")
- A "fence" statement (what the idea is NOT) is present somewhere
- Signpost language between sections is present
- A question to the room appears in the speaker notes

Honestly marked **not assessable**, never faked:

- Whether a slide actually has a logo/clutter/background decoration —
  this checker works from plain text, not a rendered slide image; the
  `has_logo_or_clutter` field must be filled in by hand (or a future
  version would need to read a real `.pptx` and look at it)
- Whether the deck's declared Symbol/Slogan/Surprise/Salient idea/Story
  are *actually* memorable or surprising — judging that is a human
  call this checker doesn't claim to make; it only checks that they
  were declared at all, as an opt-in, self-reported field

## Usage

```
python3 cli.py deck.json
```

See `cli.py`'s docstring for the exact JSON shape, or
`tests/fixtures/good_deck.json` for a complete worked example — modeled
on the article's own described demo ("a 10-minute 'How I use Claude'
talk for my team"), since the article never shows the actual deck
content, only screenshots of Claude's output on it. Stated plainly:
this fixture's content is this build's own, not a transcription of
anything the article shows.

## Proof

`python3 -m unittest tests.test_winston_checker tests.test_cli -v` —
**38/38 tests pass**, including a real discrimination pair (a
deliberately well-built deck that passes every checkable rule, and a
deliberately badly-built deck that fails or warns on every rule it
violates on purpose) and real subprocess CLI runs with clean,
non-traceback error handling for a missing file and malformed JSON.

**Three real bugs found and fixed in this build's own first draft, not
manufactured**: (1) the "good" deck fixture's opening slide stated only
the promise, not the main idea itself, so the newly-written
`main_idea_repeated` check correctly failed it on the first run — Winston's
own rule is to say the idea at the *start* too, not just build up to it;
fixed by adding the main-idea phrase to the opening slide's notes, not by
loosening the check. (2) the "bad" deck fixture's over-long-slide bullet
was accidentally only ~32 words, under the 40-word threshold it was meant
to violate — fixed the fixture, not the threshold. (3) a test-authoring
mistake: a test constructed `Deck(five_elements=...)` without the
required `slides` argument, caught immediately by `TypeError` on the
first real run.

## Deliberately not built

- A `.pptx` reader to populate `has_logo_or_clutter` automatically from
  a real file — this build works from a structured text representation
  only; reading a real PowerPoint file's visual layout is a real,
  separate piece of work for a future round, not faked here.
- Checks around the three unverified numbers (7-second pause, 40pt
  font, 20% checked-out) — see the verification table above.
- Anything resembling the paywalled Claude skill's own actual prompt/
  implementation — never seen, nothing here is derived from it.
