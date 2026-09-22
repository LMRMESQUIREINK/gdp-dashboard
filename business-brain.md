# Business Brain

The living source of truth for this person's business context. Updated
whenever new information comes up in conversation — not just during a
formal interview. Claude should read this before giving strategy advice
and should write back to it when something changes.

**Status: first real Build Brain run in progress (Recovery Desk).**
Filled in from an uploaded IdeaBrowser-style opportunity report, not a
live back-and-forth interview — see "What's a genuine answer vs. an
inferred one" below before treating anything here as confirmed. This
project also holds an unrelated RUTHLESS TRADING GOLD trading-tools
portfolio under `/builds/` — that work stands on its own and isn't part
of this business; this file tracks whichever business is actively
running through the Build Brain method, which is Recovery Desk now.

---

## What's a genuine answer vs. an inferred one

The source document is a third-party market-opportunity report (pain
evidence, competitor pricing, Reddit quotes, revenue model, a "founder
fit" profile) — not a first-person interview with the actual person
running this. Two consequences, stated plainly rather than glossed over:

1. **Audience, offer, pricing, and competition below are genuine,
   sourced answers** — the report cites real numbers (Reddit member
   counts, App Store revenue estimates, a Rock Health survey) rather
   than inventing them, so those sections are trustworthy as written.
2. **"Who I am" is NOT a genuine answer — it's the report's stated
   ideal-founder profile, not a confirmation that the actual person
   here matches it.** The report itself is explicit that founder fit is
   make-or-break: *"An endurance athlete or coach who already owns a
   Whoop and an Oura, spends time inside r/whoop and r/ouraring by
   choice... Bonus if they have a small (5K-30K) Instagram or Substack
   in the running, cycling, or strength world... The wrong founder for
   this is a generalist SaaS builder who wants to run ads and read
   charts."* Whether that's true of the actual person building this has
   never been asked. Treat every downstream stage's polish as evidence
   the *research* is good, not as evidence this particular founder is
   the right match — that's still an open, real question.

## Who I am

- Background / skills: **Unconfirmed — not asked yet.** The report's
  ideal profile: an endurance athlete or coach, hands-on with both Oura
  and Whoop personally, active by choice in r/whoop and r/ouraring,
  ideally with a small (5K–30K) running/cycling/strength audience. Ask
  directly before betting real time on this rather than assuming a fit.
- Time available per week: Not asked.
- Money available to invest: Not asked. Report's own estimate for a
  scoped v1: $5K–$20K capital in.
- Risk tolerance: Not asked. Worth knowing given the report's own
  "reasons not to build" list includes real regulatory/liability
  exposure (see Constraints).

## Audience

- Who I'm trying to serve: Quantified-self prosumers who already own a
  wearable (Oura or Whoop) and check its data daily. One persona at
  launch: **endurance athletes** — not a general wellness audience.
- What they struggle with: They trust the sensor data, not the advice
  built on top of it. Sourced complaints: a Whoop member (3 days before
  the report) won't renew year two because "£27/month and it doesn't
  even know what day of the week it is"; an Oura owner says
  screenshotting their own data into ChatGPT beats the paid in-app
  Advisor; a r/QuantifiedSelf user says every tool they've tried
  overloads them with dashboards, diaries, and spreadsheets instead of
  an answer.
- Where they already hang out: r/ouraring (231K members), r/whoop
  (138K), r/QuantifiedSelf (27K) — all three run active, recurring
  complaint threads about existing AI coaches, unprompted.

## Idea

- **chosen**: Recovery Desk — a standing agent that reads overnight
  Oura/Whoop data and sends one decision text every morning (train
  hard / back off / eat more / sleep earlier, plus a one-line why), no
  dashboard, no chat window, aimed at endurance athletes first.
- **alternatives considered, set aside** (all surfaced by the source
  report itself, not independently brainstormed — flagged as such
  rather than presented as a wider search than it was):
  - *CGM/metabolic variant* ($49/mo, bundled for Levels-sensor users) —
    the report lists this as a later value-ladder addition, not a
    launch persona. Set aside for now: launching two personas at once
    dilutes the "own one persona's daily call" positioning that's the
    whole defensibility argument.
  - *Broad multi-wearable coach* (500+ integrations, like Vora/ONVY) —
    set aside because it's the opposite of the wedge: the report's own
    case for defensibility is narrowness (one persona, no dashboard),
    and going broad-integration first would just recreate Vora/ONVY's
    undifferentiated position instead of avoiding it.
  - *Lead with the conversational "Coach Assist" upsell* instead of the
    daily text — set aside because the entire pain thesis is that
    people are already drowning in chat interfaces (that's literally
    what the Reddit complaints are about); leading with a chat product
    would repeat the exact failure mode this is positioned against.

## Offer

- What I'm selling: **Recovery Desk** — reads last night's Oura/Whoop
  data and sends one decision text each morning (train hard / back off
  / eat more / sleep earlier) plus a one-line why. No dashboard, no chat
  window — the product is the text, not an app to open.
- Price / pricing model: $29/mo (Recovery Desk Daily) or $290/yr (17%
  off, Recovery Desk Annual). Free 7-day "Morning Read" trial, no card
  required. Cancel by texting STOP.
- What makes it different: every competitor (Whoop Coach, Oura Advisor,
  Google Health Coach, Bevel, Vora, ONVY) ships a dashboard or a chat
  window on top of the same sensor data. None ship a single decision
  before the user opens any app. The moat isn't the underlying model
  (the report notes Whoop Coach and ChatGPT both run on OpenAI) — it's
  owning one persona's daily call with a real point of view, not
  another surface to configure.

## Constraints

- Things that are off the table: mass unsolicited DMs — the report's
  own distribution plan is *"the first 100 customers come from helpful
  replies [to existing complaint threads], not paid ads at $4.60 CPC"* —
  spamming the exact communities this depends on would burn the one
  channel that's actually open.
- Non-negotiables: this is a health-adjacent product sent by text, not
  inside an app with in-context disclaimers — the report itself flags
  this as the single biggest real risk ("One missed atrial fibrillation
  signal or one push-through-illness call is a business-ending event").
  Every build under this brand carries an explicit non-diagnostic
  disclaimer and a hard rule: any anomalous reading routes to "see a
  doctor," never to a training recommendation. See
  `/builds/recovery-desk/README.md` for how this is actually enforced
  in code, not just stated here.
- Also genuinely unresolved, not decided away: dependency on Oura/Whoop
  APIs the business doesn't own (they can cap access or ship a better
  coach and close the gap this depends on), and a "ai health coach"
  search trend that spiked in the May 2026 press cycle and had fallen
  back to near-zero by mid-September — growth has to come from
  community work, not search, for at least the first year.

## 90-day goal

- The one outcome this quarter is aimed at: first paying subscriber
  within 45 days (the low end of the report's own 45–90-day "first
  revenue" estimate), sourced entirely from helpful replies in
  r/ouraring and r/whoop threads, not paid acquisition.
- How I'll know it worked: at least one real $29/mo or $290/yr
  subscription, from someone outside the founder's own circle, still
  active after their first billing cycle (not just a free-trial signup).

## Launch Plan

Ad copy: `/builds/recovery-desk/launch/ad-copy.md` (short/medium/long
variants, all reusing the sales page's own hooks and `design-rules.md`'s
voice — none reinvent the pitch).

1. **Channel #1, and why**: r/ouraring (231K) and r/whoop (138K) —
   not a cold platform, an existing audience already complaining about
   this exact problem out loud, unprompted. Matches the source report's
   own distribution plan directly: *"the first 100 customers come from
   helpful replies, not paid ads at $4.60 CPC."* No paid acquisition at
   launch — "ai health coach" search volume fell from a May-2026 press
   spike back to near-zero by mid-September, so search isn't a channel
   yet either.
2. **Sequence**:
   - Days 1–7: reply to 10–15 active complaint threads across
     r/ouraring and r/whoop with the medium-length variant, one
     thoughtful reply per thread, only where it's genuinely relevant to
     what the person posted — never a mass-post, never unsolicited DMs.
   - Day 7: one original post in r/QuantifiedSelf (27K — the report's
     own "pressure-tested overflow" community) using the long-form
     variant, framed as a build-in-public share, not an ad.
   - Day 14: follow up individually with anyone from week 1 who engaged
     (replied, upvoted, DM'd back) but hadn't started a trial yet.
3. **First-customer target**: one paying subscriber ($29/mo or $290/yr)
   within 45 days — see the 90-day goal above; this is the near-term
   marker, not the report's year-one ceiling.
4. **What counts as working vs. not**: if the first 15–20 thread replies
   produce zero free-trial signups, the message or the targeting is
   wrong — revisit copy/thread selection before sending 15–20 more of
   the same rather than assuming volume alone will fix a 0% response
   rate.

All six Build Brain stages now have a real output for Recovery Desk:
Interview and Idea above, DNA Lock in `design-rules.md`, the actual
build in `/builds/recovery-desk/`, the sales page in
`/builds/recovery-desk/sales-page/`, and this launch plan.

## Decisions log

Append-only. Each entry: date, decision, why.

- 2026-09-22 — Ran the Build Brain method on Recovery Desk end-to-end
  from an uploaded IdeaBrowser opportunity report. Chose a rules-based
  (not LLM-generated) decision engine for the core "train hard / back
  off / eat more / sleep earlier" call, on purpose: the report's own
  analysis says the moat isn't model intelligence, it's a trusted,
  specific decision — a deterministic, explainable rule set matches
  that claim better than adding a generative-text dependency this
  product doesn't need. See `/builds/recovery-desk/README.md`.
- 2026-09-22 — Brand colour locked to a deep recovery green
  (`#3E7C5C`) on near-black, not the placeholder default. Deliberately
  distinct from Whoop's neon lime and Oura's teal/white so the product
  doesn't read as "yet another wearable app" in a screenshot. See
  `design-rules.md`.
- 2026-09-22 — Completed all six Build Brain stages for Recovery Desk in
  one pass. Two real bugs caught by actually running the code, not by
  reading it: `decision_engine.py`'s `train_hard`/`back_off` synthetic
  test fixtures didn't cross their own thresholds (`back_off` silently
  returned `TRAIN_HARD`) until recalculated — see
  `/builds/recovery-desk/README.md`. Also confirmed Google Fonts don't
  load in this sandbox (genuine network block, not a cert artifact), so
  the sales page's Space Grotesk/Inter pairing is unverified here — the
  page degrades to a system-font fallback, flagged rather than claimed
  as proven. **Real, unresolved gap carried forward from Stage 1**: "Who
  I am" was never actually asked — everything from the sourced report
  onward is solid, but founder fit (does the actual person building this
  match the report's own stated ideal profile?) is still an open
  question, not a confirmed yes.
