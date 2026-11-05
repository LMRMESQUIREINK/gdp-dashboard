---
name: voice-extractor
description: Extract a measurable voice profile from a real writing sample (sentence length, first-person rate, contraction rate, em-dash/question/exclamation patterns, common sentence openers) and score a new draft against it, so drafted content sounds like a specific real person instead of generic AI output. Use alongside humanizer — humanizer strips AI tells out, this puts a real voice back in. Triggers on phrases like "match my voice", "sound like me", "write this in my tone", "extract my writing style", or any request to make content sound like a specific person's real writing.
---

# Voice Extractor

Built from the tone.md/humor.md technique described in one of three
uploaded WordPress-via-Claude tutorials — pasting a real writing sample
and decoding it into a reusable style guide. This skill builds the
measurable half of that idea: real counted signals from
`/builds/voice-extractor/`, not a vague prescriptive rule set. Full
build notes, the real scoring-design bug found and fixed during
testing, and what's deliberately not automated:
`/builds/voice-extractor/README.md`.

## Before using this

1. **Get a real writing sample from the actual person** — an email,
   a past post, a Slack message, anything they actually wrote
   themselves. Never invent a "style guide" from a vague description
   like "casual but professional" — that produces the same generic
   output this tool exists to avoid. If no real sample exists yet, say
   so and ask for one rather than guessing at a voice.
2. **One sample is enough to start, more is better.** The tool's own
   signals (sentence length, first-person rate, contraction rate) are
   more stable with more text, but a single solid paragraph is enough
   to extract something real and useful.

## How to use it

```bash
python3 /home/user/gdp-dashboard/builds/voice-extractor/voice_extractor.py \
  extract sample.txt --save profile.json

python3 /home/user/gdp-dashboard/builds/voice-extractor/voice_extractor.py \
  score draft.md --profile profile.json
```

1. Extract a profile from the real sample once, save it.
2. Draft the content normally.
3. Score the draft against the profile. For anything scoring below
   roughly 80%, read the suggestions and rewrite toward them — shorter
   or longer sentences, more or less first-person language, and so on.
4. Re-score after rewriting. Don't call content "in their voice" on the
   strength of a first draft alone.

## Where this fits with other skills

Run `.claude/skills/humanizer` first to strip generic AI tells, then
this to check the draft actually matches a specific person's measured
voice — they check different things (Humanizer: does this sound like
generic AI output; Voice Extractor: does this sound like *this specific
person*) and a draft can pass one while failing the other. For
`proposal-generator`, `launch-kit-writer`, and `sales-page-engine`,
reach for this when a real writing sample from the actual client or
business owner exists and matching their specific voice matters more
than just avoiding AI-sounding filler.

## What this doesn't do

It measures *how* something is written, not *what* it says — two
drafts on completely different topics in the same voice should score
well, and that's correct, not a gap. It also doesn't rewrite content
for you: it names what's different (sentence length, first-person
rate, and so on) and leaves the actual rewording to whoever's drafting,
same reasoning `humanizer` states for the same cut.
