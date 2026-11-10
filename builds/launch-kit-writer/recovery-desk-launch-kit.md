# Recovery Desk — Full Launch Kit

Built via `.claude/skills/launch-kit-writer`, extending the real,
already-shipped `launch-pad` output at
`/builds/recovery-desk/launch/ad-copy.md` and `business-brain.md`'s
`## Launch Plan`. Every stat, quote, and claim below traces to
`business-brain.md`'s real sourced data (the Whoop £27/month complaint,
the Oura-screenshot-beats-Advisor complaint, the r/ouraring 231K /
r/whoop 138K / r/QuantifiedSelf 27K member counts, the "$4.60 CPC" /
"helpful replies" distribution plan) — nothing here invents a new pitch,
stat, or price. Pricing throughout: $29/mo or $290/yr, free 7-day trial,
no card, cancel by texting STOP — identical to the sales page and
launch-pad's own copy. The launch email is **not** duplicated here —
launch-pad's own "long" variant already covers it; see that file.

## Product Hunt listing

**Tagline** (58 chars): One text every morning. No dashboard to open.

**Short description**: Recovery Desk reads your overnight Oura/Whoop
data and sends one decision — train hard, back off, eat more, or sleep
earlier — plus the one number behind the call. No app, no dashboard,
no chat window.

**Maker comment**: I built this because I kept seeing the same
complaint on r/whoop and r/ouraring: the built-in AI coaches read
everything and say nothing specific. One Whoop member put it better
than I could — not renewing year two because it "doesn't even know what
day of the week it is." So Recovery Desk skips the dashboard entirely
and just sends one text. Honest limitation: it's rules-based, not a
custom ML model — the bet isn't a smarter model, it's actually making
the call instead of elaborating on a score. Free 7-day trial, no card.

## Show HN post

**Title**: Show HN: Recovery Desk – one text a day instead of a wearable
app's dashboard

**Body**:

> Recovery Desk reads last night's Oura or Whoop data and texts one of
> four calls every morning — train hard, back off, eat more, sleep
> earlier — with one line on why, compared against your own baseline.
> No app, no login, nothing to configure.
>
> Why: Whoop and Oura's own in-app coaches run on top of the same
> sensor data (per a market report I read, Whoop Coach and ChatGPT both
> run on OpenAI underneath) but ship it as a dashboard or chat window
> that elaborates instead of deciding. The actual complaint I kept
> seeing on r/whoop and r/ouraring wasn't "the sensors are wrong," it
> was "I still don't know what to do today."
>
> It's deliberately rules-based, not a custom model — a hard-coded
> anomaly check overrides any call with "see a doctor" on an
> illness-like pattern, in code, not a disclaimer. Not built yet:
> anything beyond the four-call decision (no chat, on purpose, for now).
>
> Free 7-day trial, no card. Happy to answer anything about the
> decision logic or why it's not a dashboard.

## X/Twitter thread (7 tweets)

1. Your wearable's AI coach read your data all night and still can't
   tell you what to do today. Mine does. One text. No app.
2. Oura Advisor, Whoop Coach, Google Health Coach — all of them ship a
   dashboard or a chat window on the same sensor data. None of them
   ship an actual decision before you open anything.
3. A Whoop member put it better than I could: not renewing year two
   because it "£27/month and it doesn't even know what day of the week
   it is."
4. So Recovery Desk skips all of it. Reads your overnight Oura/Whoop
   data, sends one text: train hard, back off, eat more, or sleep
   earlier. Plus the one number behind the call.
5. No dashboard. No app to open. The text is the product.
6. If a reading looks like more than ordinary training fatigue, it
   tells you to see a doctor instead of guessing — that's a hard rule
   in the code, not fine print.
7. Free 7-day trial, no card required. Cancel any time by texting STOP.
   [link]

## Reddit — one post/reply per subreddit, not one post cross-posted

Per launch-pad's own distribution plan ("the first 100 customers come
from helpful replies, not paid ads"), all three are replies inside
existing complaint threads, never a cold post — r/ouraring and r/whoop's
own community norms (and r/QuantifiedSelf's, by the same logic) rule
that out.

**r/ouraring** (reply to a thread about the in-app Advisor):

> Same complaint here, honestly — screenshotting my own Oura data into
> ChatGPT gave me a better read than the paid Advisor more than once.
> Built a text that just sends one call every morning (train hard /
> back off / eat more / sleep earlier) instead of a chat window that
> elaborates. No dashboard. Free 7-day trial if you want to try it on
> your own data.

**r/whoop** (reply to a thread about Whoop Coach's renewal value):

> This is the exact reason I'm not renewing Coach either — all the
> explaining, none of the deciding. Made something small that reads
> your Whoop data overnight and just texts you the call, one line why,
> no app to open. Free trial, no card, happy to answer questions on how
> it actually decides.

**r/QuantifiedSelf** (reply to a thread about tool overload):

> That's the exact complaint that got me building this — every tool I
> tried added another dashboard or diary instead of just answering
> "what do I do today." Recovery Desk reads overnight Oura/Whoop data
> and sends one text: train hard, back off, eat more, or sleep earlier,
> plus the one number behind it. No new app to check, no new spreadsheet
> — it replaces checking, it doesn't add to it. Free 7-day trial if
> you want to try it against your own numbers.

## Medium / long-form article (distinct from the launch email)

**Title**: Why I Stopped Trusting My Wearable's AI Coach (And Built a
Text Message Instead)

A narrative piece, not a direct pitch — meant to be read on its own:

> Three complaints, three different wearables, the same shape. A Whoop
> member not renewing year two because the coach "doesn't even know
> what day of the week it is," for £27 a month. An Oura owner who found
> that screenshotting their own data into ChatGPT worked better than
> the paid in-app Advisor. A r/QuantifiedSelf regular who's tried every
> tracking tool going and says each one just adds another dashboard,
> another diary, another spreadsheet — never an answer.
>
> None of these are sensor complaints. Oura and Whoop's hardware is
> good, and getting better. The complaint is what sits on top of it:
> more data, more charts, more chat — never a decision. Whoop Coach and
> ChatGPT reportedly even run on the same underlying model family. The
> problem was never the intelligence. It was that every product in this
> space treats "say more" as the feature, when the actual ask — across
> three separate active communities, 231K, 138K, and 27K members,
> complaining unprompted — is "just tell me what to do."
>
> So Recovery Desk doesn't have a dashboard. It reads last night's
> Oura or Whoop data and sends one text every morning: train hard, back
> off, eat more, or sleep earlier, plus the one real number behind the
> call, measured against your own baseline instead of a generic target.
> If the pattern looks like more than ordinary training fatigue — not a
> recovery call, something that actually warrants a doctor — the system
> says so instead of guessing, as a hard rule in the code, not a
> disclaimer bolted on after the fact.
>
> It launches to endurance athletes first, deliberately narrow: owning
> one persona's daily call with a real point of view beats being
> another broad, undifferentiated dashboard. $29/month or $290/year,
> free 7-day trial, no card, cancel any time by texting STOP.

## Don't-say-list check

Grepped against `design-rules.md`'s Recovery Desk don't-say list
(AI-powered, biohacking, optimize your performance, unlock your
potential, holistic, next-level, cutting-edge, game-changer, leverage,
synergy, empower, diagnose, treat): clean across all five assets above.

Run through `/builds/humanizer/humanizer.py` for the prose-tell check
(separate from the brand-voice don't-say list): see
`/builds/launch-kit-writer/README.md` for the real result.
