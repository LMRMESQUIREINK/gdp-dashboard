---
name: reference-builder
description: Use for ANY request to build, redesign or improve a website, landing page or web page. Studies reference designs first, writes a spec, builds, then screenshots and fixes its own work.
---

# Reference Builder

Source: the "Make Claude Design From Real References" guide (the Motion
Sites Method), vendored per its own Step 5 instruction to create this file
"with exactly this content." This project already has `design-rules.md`
(locked brand palettes/voice) and three other vendored design skills
(`impeccable`, `emil-design-eng`, `design-taste-frontend`) — this skill
fills a real, specific gap none of them cover: picking 2-3 curated real
reference designs from a personal mood board *before* writing a spec, with
a per-reference "steal: X" note. Where this skill's own generic guidance
(fonts, colour, "no purple gradients") would collide with an
already-locked brand in `design-rules.md`, the locked brand wins — same
precedence rule already stated there for the other three vendored skills.
This project's screenshot-before-done rule already covers step 4 below
(this sandbox has direct Playwright access via Bash, used in every visual
build to date — no separate `claude mcp add playwright` step is needed
here; that step in the source guide is for a user's own local Claude Code
install, not this session).

## 1. Study references (always first)
- Read references/INDEX.md and pick the 2 or 3 references closest to the
brief.
- Open those images. Note their type sizes, spacing, colour count, media
use and level of detail.
- Tell the user which references you picked and why, in 3 lines.

## 2. Write the spec (before any code)
Write a short spec and wait for approval:
- Audience and the one action the page must drive
- Sections in order, each with its purpose
- Fonts (one display, one body), exact sizes for h1, h2 and body
- Colours: one accent plus neutrals, with hex codes
- Media: what goes behind the hero and where it comes from
- Motion: what moves, how long, and what does NOT move

If a build is under a brand already locked in `design-rules.md`, pull
fonts/colours/voice from there instead of inventing new ones — the locked
brand's own values stand in for this step, not a second source of truth.

## 3. Build
- Follow the spec exactly. Use the frontend-design skill for taste
decisions.
- Real copy only. No lorem ipsum, no fake testimonials.
- No purple gradients, no emoji icons, no three identical feature cards.

## 4. Look and fix (never skip)
- Open the page with the Playwright tools.
- Screenshot at 1440px wide (laptop) and 390px wide (phone).
- Score it 1 to 10 on: hierarchy, spacing, typography, media, mobile,
polish.
- Check for: cut-off text, overlapping elements, broken images or video,
  horizontal scrolling on phone, text hard to read on its background.
- Fix the 3 worst problems, screenshot again. Up to 3 rounds.

- Report the final scores and what you fixed, with the screenshots.

Why it works: the description line tells Claude when to use it automatically, and the steps force the order that
produces quality: look, plan, build, check.
