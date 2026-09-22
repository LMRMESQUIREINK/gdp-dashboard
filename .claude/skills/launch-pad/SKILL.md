---
name: launch-pad
description: Turn a locked brand DNA and finished sales page into ready-to-post ad copy variants and a concrete launch plan with a specific first-customer target — not vague "get some sales" advice. Stage 6, the last stage, of the Build Brain method (/prompts/build-brain-method.md) — use once DNA Lock (design-rules.md) and the Sales Page Engine output already exist. Triggers on phrases like "write ad copy", "launch plan", "how do I get my first customer", "ad assets for this", or any request to plan or write copy for a launch.
---

# Launch Pad (Build Brain, Stage 6)

The last stage: turns an already-built brand + sales page into ad copy
ready to post and a launch plan concrete enough to actually follow. See
`/prompts/build-brain-method.md` for the full six-stage sequence and
`/notes/ruthless-affiliate-gold-build-brain-analysis.md` for the source
analysis — this stage wasn't in the original wizard export (it showed as
"Build →", not yet run), so there's no worked example to distill from;
built directly from this project's own rules instead, the same way
`.claude/skills/sales-page-engine` was.

## Before writing anything

1. **DNA Lock and the Sales Page Engine output must already exist.** Ad
   copy that reinvents the pitch from scratch, instead of reusing the
   sales page's own pain points, mechanism, and offer framing, produces
   inconsistent messaging across channels. Pull the hooks from the
   sales page; don't write new ones.
2. **Check `business-brain.md`'s 90-day goal.** If it's still the
   generic placeholder ("a number, a launch, a first paying customer")
   rather than an actual number, say so before writing a launch plan —
   a plan needs something concrete to aim at (see "Copy honesty" in
   `sales-page-engine`; the same lazy-interview risk applies here to
   planning, not just copy).
3. **Check what channels and assets are actually being asked for.**
   Don't default to a fixed list of platforms — ask, or infer from
   `business-brain.md`'s stated audience/assets (an email list implies
   email copy; an X/Discord-native audience implies short-form social
   copy; neither implies both).

## Ad copy — reuse the pitch, vary the length and channel

Write 2–3 variants per requested channel, each reusing DNA Lock's
do-say phrases and the sales page's actual pain/mechanism/offer framing
— don't write a fourth, different pitch:

- **Short (social post / paid ad, ~1–3 sentences)**: one pain point +
  one outcome + CTA. This is the hardest one to get right — cutting the
  sales page down to its sharpest single beat, not a vaguer summary of
  the whole thing.
- **Medium (cold DM / outreach message, ~4–6 sentences)**: the sales
  page's price-contrast statement or strongest proof point, personalized
  with a placeholder for the recipient's specific situation (`[their
  actual pain point]`, not a generic "Hey there!").
- **Long (email / longer-form post)**: can follow more of the sales
  page's structure (pain → mechanism → offer), but still ends on the
  same CTA and price the sales page states — never a different
  price or a softer/harder offer than what's actually live.

If real visual ad creative (not just copy) is wanted and this
environment has Canva tools available, hand off DNA Lock's exact
palette/fonts/logo direction rather than letting a generic template
drive the look — same "no invented substitute for the locked DNA" rule
as everywhere else in Build Brain.

## Launch plan — concrete enough to actually follow

Not "post on social media and see what happens." A real launch plan
answers, in order:

1. **Where first, and why that one first.** Pick based on
   `business-brain.md`'s actual stated assets (an existing audience
   beats a cold platform) — if there's already an email list or a
   community presence, that's channel #1, not wherever's trendiest.
2. **What sequence.** A short, dated or day-numbered list — "Day 1: DM
   the medium-length variant to N warm contacts. Day 3: post the short
   variant. Day 7: follow up with anyone who engaged but didn't
   convert." Vague ordering ("build momentum, then scale") isn't a
   sequence.
3. **A specific first-customer target**, pulled from
   `business-brain.md`'s 90-day goal if it's a real number, or asked
   for directly if it's still the placeholder. "One paying customer by
   [date]" is a target; "some traction" is not.
4. **What counts as working vs. not**, so there's a decision point
   instead of drifting indefinitely — e.g. "if zero replies after the
   first 20 DMs, the message or the channel is wrong, revisit before
   sending 20 more of the same."

## Rules

- **No fabricated urgency or social proof** — same rule as
  `sales-page-engine`: no fake scarcity, no invented customer counts or
  testimonials. A launch with zero customers yet says so implicitly by
  not claiming any; it doesn't need a lie to fill the gap.
- **Every ad variant gets the same don't-say-list check** as the sales
  page: grep the copy against `design-rules.md`'s banned words before
  calling any variant done.
- **Stay inside the actual offer.** Ad copy promising something the
  sales page/offer doesn't (a discount that isn't live, a feature
  that's still a TODO in the build prompt) creates a mismatch the first
  visitor will catch immediately.

## When this stage completes

Per `CLAUDE.md`'s "Keeping the brain current" rule, write the finished
launch plan into `business-brain.md` under a `## Launch Plan` heading —
per `build-brain-method.md`'s Stage 6 note, this is where the whole arc
(interview → idea → brand → build → sales page → launch) ends up living
in one place. At that point all six Build Brain stages have a real
output for this business, not just a template — say so plainly rather
than treating "wrote a launch plan" as a quiet, unremarked event.
