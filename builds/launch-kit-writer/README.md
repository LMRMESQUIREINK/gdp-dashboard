# Launch Kit Writer — worked example (Recovery Desk)

A real instantiation of `.claude/skills/launch-kit-writer`, extending
Recovery Desk's real, already-shipped `launch-pad` output
(`/builds/recovery-desk/launch/ad-copy.md`) and `business-brain.md`'s
sourced data — not a new business, not invented stats. The skill itself
is the actual deliverable; this file proves it produces something
concrete and correctly reuses what already exists rather than reinventing
the pitch per platform.

`recovery-desk-launch-kit.md` holds five platform-native assets (Product
Hunt listing, Show HN post, a 7-tweet X thread, three per-subreddit
Reddit replies, a Medium-style long-form article) — deliberately **not**
a sixth, duplicate launch email, since launch-pad's own "long" variant
already covers that and the skill's own rule says not to duplicate it.

## Verified against the real checks, not just read over by eye

**Don't-say-list grep** (`design-rules.md`'s Recovery Desk list —
AI-powered, biohacking, holistic, leverage, diagnose, treat, etc.): clean
in the actual asset content (the five real platform pieces). **A real,
instructive false positive found while checking this**: a naive grep of
the whole file hits 13 times, all inside this file's own "Don't-say-list
check" section, which literally spells out the banned-word list by name
to document what was checked — the exact same false-positive class this
project already documented for Recovery Desk's "diagnose"/"treat" hits
on its sales page disclaimer, now showing up for a different, simpler
reason (quoting the rule itself, not negated medical language). Confirmed
by checking line numbers and excluding the checklist section, not by
assuming it was fine.

**Humanizer** (`/builds/humanizer/humanizer.py`, prose tells, a
different check from the brand don't-say list): same result — 8 findings,
all on the same checklist line, 0 in the actual asset content.

```bash
python3 /home/user/gdp-dashboard/builds/humanizer/humanizer.py \
  /home/user/gdp-dashboard/builds/launch-kit-writer/recovery-desk-launch-kit.md \
  --max-per-1000-words 8
```

## What's reused vs. what's new here

Reused, not reinvented: the pricing ($29/mo, $290/yr, free trial, STOP
to cancel), the core mechanism copy (train hard / back off / eat more /
sleep earlier), the sourced complaint quotes (Whoop £27/month, the
Oura-screenshot-beats-Advisor line), the subreddit member counts, and the
reply-in-thread (never cold-post) distribution strategy — all pulled
directly from `business-brain.md` and the existing launch-pad output, not
redrafted. New in this file: the platform-specific structuring each
format actually needs (a Show HN post's terse, tech-literate tone; a
Product Hunt maker comment's first-person candor, including a stated
honest limitation; a 7-tweet thread's per-tweet beat structure; three
distinct Reddit replies instead of one cross-posted).
