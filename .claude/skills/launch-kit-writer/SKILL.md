---
name: launch-kit-writer
description: Produce the full set of platform-native launch assets (Product Hunt listing, Show HN post, X/Twitter thread, Reddit posts adapted per subreddit's own norms, a Medium/long-form article, a launch email) from a brand and sales page that already exist — not a single generic post copy-pasted everywhere. Extends launch-pad rather than replacing it: run launch-pad first for the launch plan and the short/medium/long ad-copy variants; use this skill when more platforms are actually needed than launch-pad's three lengths cover. Triggers on phrases like "write my Product Hunt listing", "write a Show HN post", "launch thread for X", "full launch kit", or any request for launch assets across several specific named platforms.
---

# Launch Kit Writer

Built from the "Launch Kit Writer" idea in the uploaded "7 claude skills
that print money" article. **This is not a replacement for
`.claude/skills/launch-pad`** (Build Brain Stage 6) — it's what to reach
for once launch-pad's own launch plan and short/medium/long ad copy
exist and the actual ask covers more *specific platforms* than those
three generic lengths name (Product Hunt's own listing fields, a Show HN
post's particular unwritten-rules tone, a proper X thread's per-tweet
structure, Reddit posts that genuinely differ by subreddit rather than
one post cross-posted everywhere). A worked example extending Recovery
Desk's real, already-shipped launch-pad output is at
`/builds/launch-kit-writer/`.

## Before writing anything

1. **`launch-pad`'s output must already exist** — the locked DNA
   (`design-rules.md`), the sales page, and `launch-pad`'s own ad copy
   and launch plan. Every asset this skill produces reuses those real
   hooks, stats, and voice; it does not invent a second, different
   pitch per platform. If launch-pad hasn't run yet, run it first.
2. **Ask which platforms are actually wanted** — don't default to
   writing all six formats below if only two are needed. The article's
   own framing ("I give it one product brief and ask for every asset in
   one go") is a convenience, not a requirement to always produce the
   full set.
3. **Check each platform's actual norms before writing for it** — Show
   HN posts read very differently from Product Hunt listings, and
   r/subreddit-a's posting culture can differ sharply from r/subreddit-b
   even for the same product (this project's own launch-pad output for
   Recovery Desk already establishes that distribution has to be a
   reply inside an existing thread on Reddit, never a cold post — carry
   that same platform-specific judgment into every new one here, not
   just Reddit).

## The formats

- **Product Hunt listing**: tagline (≤60 chars, the sharpest single
  hook — not a restated product name), a short description, and a
  "maker comment" (first-person, why this was built, one honest
  limitation stated rather than hidden — PH's own culture rewards
  candor over a polished pitch).
- **Show HN post**: title in HN's own terse style ("Show HN: X – one
  line on what it does"), body that leads with *what it does and why*,
  states the tech/approach plainly (HN's audience reads code, not
  marketing copy), and is honest about what's not built yet — oversold
  Show HN posts get called out in the comments immediately.
- **X/Twitter thread**: 5–8 tweets, tweet 1 is the hook alone (must work
  with zero context, same discipline as launch-pad's own "short"
  format), each following tweet one beat (the pain, the mechanism, the
  proof point, the offer), last tweet the CTA — reusing the sales page's
  actual structure stretched across tweets, not a new argument.
- **Reddit posts, per subreddit**: one post per named subreddit,
  genuinely adapted to that community's own norms and vocabulary, not
  one post with the subreddit name swapped. If the audience's norms rule
  out a direct post (as they do for Recovery Desk's r/ouraring/r/whoop),
  write the reply-in-thread version instead and say so plainly, same as
  launch-pad already does.
- **Medium/long-form article**: distinct from launch-pad's own "long"
  email variant — a narrative piece (the problem, what existing options
  get wrong, how this is different, what's next), meant to be read on
  its own rather than opened as a direct pitch.
- **Launch email**: if launch-pad's own long-form email variant already
  covers this, don't duplicate it — point to that output instead of
  writing a second one.

## Rules

- Every asset reuses launch-pad's real hooks, launch-pad's locked
  do-say/don't-say voice, and the sales page's actual claims — no new
  pitch invented per platform.
- Run every asset through `.claude/skills/humanizer` before calling the
  kit done.
- Same anti-fabrication rules as launch-pad: no fake urgency, no
  invented social proof, no promising anything the actual offer or
  build doesn't have.
- Write where finished kits for a tracked business live the same way
  launch-pad's own output does: inside that business's own launch
  folder (or `business-brain.md`'s `## Launch Plan`, if that's where the
  business tracks its launch work), not scattered as untracked chat
  output.
