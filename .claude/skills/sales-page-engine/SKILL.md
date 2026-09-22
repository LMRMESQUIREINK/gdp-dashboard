---
name: sales-page-engine
description: Build a real, working single-page sales/landing page from an already-locked brand DNA and offer — direct-response skeleton (hero, pain, mechanism, offer stack, pricing, guarantee, who-for/not-for, FAQ), design-rules.md compliance, and mandatory screenshot verification before calling it done. Stage 5 of the Build Brain method (/prompts/build-brain-method.md) — use once DNA Lock (design-rules.md) and the offer/pricing (One Shot Engine) already exist. Triggers on phrases like "build a sales page", "landing page for this offer", "write the sales copy", or any request to turn a locked brand + offer into a page.
---

# Sales Page Engine (Build Brain, Stage 5)

Turns an already-locked brand DNA (`design-rules.md`) and offer/pricing
(from Stage 4, One Shot Engine) into one real, working page — not a
mockup, not a copy doc. See `/prompts/build-brain-method.md` for where
this sits in the full six-stage sequence, and
`/notes/ruthless-affiliate-gold-build-brain-analysis.md` for the worked
example this skeleton was distilled from.

## Before writing anything

Check that the inputs this stage needs actually exist:

1. **`design-rules.md` has a real brand colour**, not the unset
   placeholder (`#2D5C3E` with a "Status: starter defaults" note at the
   top means DNA Lock hasn't run yet). If it's still the placeholder,
   say so and run DNA Lock first — don't invent a palette here that
   `design-rules.md` doesn't already have.
2. **The offer is real**: a name, a price, and what's actually included.
   If pricing hasn't been decided (Stage 4 not done), stop and get that
   first — a sales page with a placeholder price is worse than no page.
3. **`business-brain.md` has enough audience context** to know who this
   page is talking to. If it's still empty/generic, the page will read
   generic no matter how good the copy skeleton is — flag that risk
   rather than papering over it with confident-sounding copy (see
   "Copy honesty" below — this is the same lazy-interview risk Build
   Brain's Stage 1 warns about, surfacing here as its consequence).

## The page skeleton

One page, in this order. Skip a section only if it genuinely doesn't
apply (e.g. no guarantee offered) — don't pad a thin offer with filler
sections just to hit the full list.

1. **Nav + hero** — logo/wordmark, one CTA in the nav. Hero: headline
   (the outcome, not the feature), one-sentence subhead, primary CTA,
   a low-friction trust line under the button (guarantee terms, "no
   credit card required," etc. — only if true).
2. **Pain** — bulleted, specific, in the audience's own language from
   `business-brain.md`, not generic pain-point templates. One sharp
   contrast statement (price, time, or effort comparison) as its own
   visual beat, not buried in a paragraph.
3. **Mechanism** — how it actually works, in plain terms. This is where
   most sales pages either go vague ("AI-powered magic") or overload
   with feature lists; aim for 3-4 concrete steps or components a
   skeptical reader can picture.
4. **Offer stack** — what's included, each item framed as an outcome
   ("push straight to your platform," not "OAuth integration").
5. **Pricing** — the actual tiers from Stage 4, exact numbers, no
   "starting at" vagueness unless the real pricing is genuinely usage-
   based.
6. **Guarantee** — only if one is real. Never invent a guarantee, refund
   window, or trial that Stage 4's offer didn't actually specify.
7. **Who this is for / not for** — both lists. The "not for" list is
   what makes the "for" list credible; don't skip it to seem more
   universally appealing.
8. **FAQ** — answer real objections (price, skill level, cancellation,
   what makes this different), not softball questions that exist only
   to repeat marketing copy.

## Design rules (non-negotiable)

Follow `design-rules.md` exactly — same as every other visual build in
this project, no exception for "it's just a sales page":

- Palette, fonts, spacing scale, shadow style, and motion rules come
  from `design-rules.md`'s locked values, not invented fresh per page.
- Avoid every item on `design-rules.md`'s "generic-AI tells" list —
  cream/terracotta palettes, identical rounded cards, tracked-out
  ALL-CAPS eyebrows, arrow-suffixed buttons, stock-photo hero gradients.
- A sales page has its own extra tells to avoid on top of that list:
  fake countdown timers, fabricated "X people bought this today"
  counters, stock testimonial avatars with generic names, and urgency
  language ("Only 3 spots left!") that isn't backed by something real.
  A page that resorts to fake scarcity is telling the reader the real
  offer isn't strong enough on its own — fix the offer or the copy, not
  the honesty.

## Copy rules

- **Voice**: pull `design-rules.md`'s do-say phrases and tone in
  directly; never contradict its don't-say list. Treat the don't-say
  list as a literal check, not a vibe — before calling the page done,
  grep the rendered copy for every banned word/phrase. This is the one
  idea worth keeping from the worked example that inspired this skill:
  a brand-voice constraint that's a real check, not just a guideline
  nobody verifies.
- **No lorem ipsum, ever** — every section ships with real copy for
  this specific offer, even in a first draft.
- **Copy honesty**: specificity is not the same as truth. A page can
  read as confident and specific while resting on a thin or generic
  `business-brain.md` — if the audience/offer context is genuinely
  thin, write pain points and mechanism copy that stay honest about
  what's actually known, rather than manufacturing precise-sounding
  detail (a "12,000 creators" stat, a named-but-fictional persona) that
  isn't backed by anything in `business-brain.md`. Confident and vague
  beats confident and fabricated.

## Self-check before calling it done

This produces a visual, working page — `CLAUDE.md`'s screenshot-before-
done rule applies in full, no exception:

1. Serve it on a local server (not a `file://` URL).
2. Screenshot it and actually look — compare against
   `design-rules.md` and the offer from Stage 4.
3. Check mobile width specifically — direct-response pages are read on
   phones more than desktop; a page that only looks right at 1440px has
   failed this check.
4. Fix anything off, re-screenshot. Minimum two passes.
5. Grep the rendered page's text content for every word/phrase in
   `design-rules.md`'s don't-say list — zero matches required.
6. Only then hand it off, and say plainly what was checked.
