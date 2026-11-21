# Deep analysis: "The presentation rules MIT taught its students, turned into a Claude skill"

Source: a pasted Substack article by Frank Andrade (Artificial Corner),
dated Oct 28, 2026. No accompanying instruction, so per this project's
convention the article itself is the instruction to run the
deep-analysis-and-ship loop. A paywalled piece — the free portion
covers Patrick Winston's "How to Speak" (MIT RES.TLL-005) rules and
three free prompts for applying them to a deck; the paid portion
(behind the paywall, never seen by this round) describes a Claude
skill that does the same thing automatically plus exports to
PowerPoint in a company's brand colors.

## What was measured first

- Real, existing publication: Frank Andrade/Artificial Corner is a real
  Substack newsletter (confirmed via its own About page and a linked
  Substack profile for "thepycoach").
- The article's own claimed "93,000 people read it every week" could
  not be independently confirmed to that specific figure. The only
  public number found was a related Substack profile showing "51K+
  subscribers" — a different page, a different metric, not confirmed
  as the same count. Reported as self-stated, not verified, same
  discipline as every other unconfirmable subscriber/star-count claim
  this project has flagged (REA, deer-flow, AgentsKit.co).

## What was verified against the real underlying lecture

The article's central factual claim is that it accurately distills
Patrick Winston's real MIT lecture, "How to Speak" (RES.TLL-005, MIT
OpenCourseWare). This sandbox's egress proxy blocks `ocw.mit.edu`
directly (confirmed via a direct `curl`, connection refused — the same
restriction class as arxiv.org, Hugging Face, agentskills.io, dev.to,
medium.com, nocobase.com, now extended to MIT OCW), so the primary
transcript couldn't be read directly. Two independent GitHub Gists of
real student/reader notes on the actual 2018 lecture were read in full
instead (`almeidaraul`'s and `StevenMaude`'s), and the article's 7
specific, checkable claims were checked against both:

- **Confirmed by both independent sources**: no logos/clutter/
  background decoration on slides; use arrows on slides, never a laser
  pointer; the five memorable-talk elements, named exactly as the
  article states them (Symbol, Slogan, Surprise, Salient idea, Story).
- **Confirmed in substance, but more absolute in the article than in
  the real notes**: ending on a "Contributions" slide rather than
  "Thank you"/"Questions?", and not literally saying "thank you" as
  your last words. Both real sources agree on the *direction*, but one
  of them frames "Contributions" as *"perhaps better,"* not a hard
  rule, and lists "salute the audience" as one of three closing
  options rather than the article's implied single correct choice. A
  real, precise finding: the article states a softer, real recommendation
  as an absolute rule.
- **Not found in either independent source, despite being stated with
  specific confidence in the article**: waiting ~7 seconds after
  asking the audience a question; a minimum font size of "40 points or
  more" (both sources only say the font must be "large to be
  legible," no number given); and ~20% of any audience being mentally
  checked out at any given moment. These three specific, quotable
  numbers don't trace to either source — not proven false, since
  neither source is Winston's own verbatim transcript, but genuinely
  unconfirmed, consistent with this project's standing practice of
  flagging precise-sounding figures that don't trace back to a primary
  source (the "0.69 × 8 = 5.52" rounding finding, the AgentsKit.co "58
  agents/61 skills" unverifiable claim).

## Credited

The article's description of Winston's core mechanism — say the main
idea three times (start/middle/end) so whoever drifted off catches it
later, "fence" the idea by stating what it's not, signpost between
sections, and close on contributions rather than a bare "thank you" —
matches both independent sources closely and is a genuinely sound,
well-corroborated structure, not an invented framework.

## Built

Checked `/builds/` and `.claude/skills/` first: nothing in this project
checks presentation/deck content — the closest prior work
(`ten-k-website-grader`, `agent-readiness-scorecard`,
`ds-2027-skills-scorecard`) all score rendered pages or repos, not a
deck's own text structure. A genuinely new, generalizable gap.

**`/builds/winston-talk-checker/`** — a real, dependency-free Python
tool implementing the confirmed rules as mechanical checks over a
structured deck representation (slides + optional speaker notes), not
the paywalled Claude skill (never seen, nothing derived from it).
Deliberately does **not** implement checks around the three unverified
numbers above. Honestly marks two checks `not_assessable` by default
rather than faking them: whether a slide actually has visual
logo/clutter (this checker reads text, not a rendered slide image —
needs a hand-filled field or a future `.pptx` reader), and whether the
declared Symbol/Slogan/Surprise/Salient idea/Story are *genuinely*
memorable (an opt-in, self-reported field, never inferred from prose,
since judging real surprise/memorability isn't something a mechanical
checker can honestly claim to do).

38/38 tests pass, including a real discrimination pair (a deliberately
well-built deck passes every checkable rule; a deliberately bad one
fails/warns on every rule it violates on purpose, modeled on the
article's own described demo — a 10-minute "How I use Claude" team
talk — since the article never shows the actual deck content, only
screenshots of Claude's output on it, so this fixture is this build's
own content, stated plainly). Real subprocess CLI tests with clean
error handling for a missing file and malformed JSON.

**Three real bugs found and fixed in this build's own first draft, not
manufactured**: the "good" fixture's opening slide stated the promise
but not the main idea itself, so the newly-written `main_idea_repeated`
check correctly failed it on the very first run (Winston's rule is to
say the idea at the *start* too, not build up to it — fixed the
fixture, not the check); the "bad" fixture's deliberately-overlong
slide bullet was actually only ~32 words, under the 40-word threshold
it was meant to violate (fixed the fixture, not the threshold); and a
plain test-authoring mistake (`Deck(five_elements=...)` missing the
required `slides` argument), caught immediately by a `TypeError` on
the first real run.

## Deliberately not built

A `.pptx` reader to populate the clutter check automatically from a
real file — a real, separate piece of future work, not faked here. Any
reproduction of the paywalled Claude skill's actual prompt or export-
to-branded-PowerPoint behavior — never seen, so nothing here claims to
replicate it.
