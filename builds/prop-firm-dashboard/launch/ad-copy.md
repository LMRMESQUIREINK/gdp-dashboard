# The Pass Line — Launch Copy (Build Brain Stage 6)

Built via `.claude/skills/launch-pad`, on the DNA locked in `/design-rules.md`
("Brand: The Pass Line") and the sales page at `/builds/prop-firm-dashboard/sales-page/`.
Every variant below reuses that page's own hooks — real numbers, the
honest "it refuses to run without your data" mechanism, the $0/no-signup
offer — none of these invent a new pitch. Per the same community-norms
reasoning as `/builds/recovery-desk/launch/ad-copy.md`, the medium format
is a **reply inside an existing thread or Discord channel**, not a cold
DM: someone already asking "how many contracts is too many" or "what are
my real odds on this eval" is the exact person this is for, and replying
to that question is the whole distribution strategy — no unsolicited
outreach.

## Short (Reddit/X post or reply, 1–3 sentences)

> Prop firm eval and no real idea what your pass odds are? Built a free
> tool that runs a Monte Carlo sim on your own journal numbers — no
> signup, and it flat-out refuses to run without your real P&L. [link]

> Sizing up on a funded-account eval by feel instead of math? Made a
> free tool that shows exactly where adding contracts stops helping your
> pass rate and starts working against it. Your numbers, not a demo.

## Medium (reply inside an existing eval/sizing thread, ~4–6 sentences)

> Same question I had going into my eval. Every "how many contracts"
> answer in here is a feeling, not a number — so I built something small:
> you put in your tier, balance, days left, and your own avg/std daily
> P&L from your journal, and it runs a real Monte Carlo sim against the
> actual trailing-drawdown floor (the one that follows your high-water
> mark, not your starting balance — that part trips people up). It
> won't run without your real numbers, on purpose — no assumed win rate
> standing in for your edge. Free, no signup, runs locally. Happy to
> share the link if you want to try it on your own account.

## Long (X/Discord standalone post — pain → mechanism → offer, same CTA as the sales page)

> **Your prop firm eval has real odds. Nobody tells you what they are.**
>
> You pay $150–$360 for a TPT eval, get a profit target and a drawdown
> limit, and are left to guess your own sizing. Size up because it feels
> aggressive-but-fine, hit the trailing drawdown floor on a bad Tuesday
> — the floor follows your high-water mark, not your starting balance,
> so a good morning shrinks your room instead of growing it — and pay
> the entry fee again.
>
> Built The Pass Line to fix the guessing part: put in your tier,
> balance, days remaining, and your own journal's avg/std daily P&L, and
> it runs a real Monte Carlo simulation against the actual trailing-DD
> rule. You get a pass probability, the drawdown-fail vs. time-fail
> split, and a side-by-side comparison across contract counts — so you
> can see exactly where sizing up stops helping.
>
> It refuses to run without your real numbers. No demo win rate standing
> in for your edge — that's the whole honest-hook, not a slogan.
>
> Free. No signup, no card, runs locally. [Get the tool →]

## What's out of scope for launch copy

No fake "X traders passed" counters, no invented testimonials, no
"guaranteed pass" language anywhere — the entire pitch is that this tool
refuses to oversell, so the marketing copy can't either. The one example
run cited in the sales page's mechanism section (1.7%/27.1%/49.7%/70.8%
across 1/2/3/6 contracts) is real output from this project's own prior
testing, labeled explicitly as one illustrative run — never reused here
as a "typical result" claim.

---

## Launch Plan

1. **Channel #1, and why**: prop-firm evaluation Discords (Topstep/Apex/TPT-
   focused communities) — the highest-intent audience there is: people
   literally mid-eval, actively asking sizing/drawdown questions in real
   time. Unlike Recovery Desk, this build has no pre-existing audience or
   asset to lead with (Stages 1–2 were explicitly skipped this round), so
   the channel choice here is "where the exact question this tool answers
   gets asked out loud," not an owned asset.
2. **Sequence**:
   - Days 1–7: reply to 10–15 genuine sizing/drawdown/eval-odds questions
     across prop-firm Discords and r/Daytrading with the medium variant —
     only where it's a real fit for what was asked, never a mass-post.
   - Day 7: one long-form standalone post on FuturesTrading-tagged X and/or
     r/Daytrading, framed as a build-in-public share (built this because I
     had the same question), not an ad.
   - Day 14: follow up individually with anyone from week 1 who engaged
     (replied, reacted, asked for the link) but hadn't tried it yet.
3. **First-customer target**: the product is free with no accounts or
   analytics wired in (see README — no billing/signup layer built), so
   "paying subscriber" doesn't apply here the way it does for Recovery
   Desk. The closest honest equivalent, stated as a real assumption
   rather than left vague: **25 people actively request or run the tool
   on their own numbers within 30 days** (tracked the only way currently
   possible — thread replies, reactions, and DMs asking for the link).
   Flagged plainly: this is a stand-in target chosen because Stage 1/2
   (Interview/Idea) were skipped and no `business-brain.md` 90-day goal
   exists for this build; revisit if a real usage-tracking mechanism gets
   built later.
4. **What counts as working vs. not**: if the first 15–20 replies produce
   zero requests for the tool, the message or the channel is wrong —
   revisit copy or channel selection before sending 15–20 more of the
   same rather than assuming volume alone fixes a 0% response rate. Same
   decision rule as `/builds/recovery-desk/launch/ad-copy.md`.
