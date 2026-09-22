# Build Brain Method

For taking a business idea from "I have a vague thought" all the way to
a launch-ready product: a build prompt, a brand identity, a sales page,
and a launch plan — in that order, each stage feeding the next. Distilled
from a six-stage wizard pattern (Interview → Idea → DNA Lock → One Shot
Engine → Sales Page Engine → Launch Pad) seen in an uploaded worked
example; see `/notes/ruthless-affiliate-gold-build-brain-analysis.md`
for the full source analysis, including two lessons folded into the
stages below.

This is this project's third named technique, alongside the Goal/Loop
method (verifying any multi-step build) and the Software Factory method
(isolate→build→prove→ship for the build itself). Build Brain sits
*before* both of those — it's how you decide what to build and how it
should look and sound, before Software Factory's "build" station starts.

## The six stages

### 1. Interview — capture the real business context

**Input:** the person's actual answers — name/working title, current
offer (or "nothing yet"), what's been tried already, existing assets
(list, audience, website, skill, content), 90-day goal, target audience.

**Output:** filled-in `business-brain.md` (this project already has the
file; this stage is how it gets filled in, per its own "living document"
rule in `CLAUDE.md`).

**Watch for:** vague or placeholder answers ("nothing yet," "a number, a
launch") don't block the later stages — they'll still produce a
confident, specific-looking result. That specificity is not evidence the
later stages understood the real business; it's evidence the defaults
are good. Don't mistake a polished Stage 4 output for validation of a
lazy Stage 1 answer — if the interview was thin, say so before treating
anything downstream as tailored.

### 2. Idea — pick one concrete idea, with named alternatives

**Input:** Stage 1's business-brain.md.

**Output:** one chosen idea (name + one-sentence pitch) + 2–3 named
alternatives that were considered and set aside, with a one-line reason
each. Keeping the alternatives visible is what makes this an actual
decision rather than the only option that occurred to anyone.

**No existing project file for this stage** — write it as a short
`## Idea` section appended to `business-brain.md` under a `chosen` /
`alternatives` heading, so it lives next to the context it was chosen
from.

### 3. DNA Lock — brand identity, once, then reused everywhere downstream

**Input:** Stage 2's chosen idea + the person's stated taste (or default
to `design-rules.md`'s existing starter rules if they have no
preference).

**Output:** fills in `design-rules.md`'s real brand colour (replacing
the placeholder) plus:
- **Visual**: vibe, display font, body font, real hex palette (not
  object references — see the analysis note's flagged export bug;
  whatever writes this down must extract actual hex strings).
- **Voice**: a do-say list, a don't-say list, 2–3 signature phrases.
- **Brand**: name, tagline, one-paragraph logo direction.

**The one idea worth keeping from the source example**: turn the
don't-say list into an actual acceptance-criteria line in Stage 4's
build prompt — *"no banned words in the codebase; add a lint script
that greps for them"* — not just a style note nobody checks later.

### 4. One Shot Engine — the build prompt itself

**Input:** Stages 1–3.

**Output:** a complete, copy-paste build prompt (role/context → what's
being built → who it's for → recommended stack → numbered core features
→ data model → design system with exact hex/fonts from Stage 3 →
constraints/do-nots → testable acceptance criteria → a closing
instruction that says explicitly: don't ask questions, make smart
defaults, record each one). This is where this project's Software
Factory method (`.claude/skills/new-feature` →
`.claude/skills/code-structure` → `.claude/skills/evidence-driven-testing`
→ `.claude/skills/review-loop`) actually runs — Stage 4 produces the
brief; Software Factory executes it.

**Acceptance criteria must be checkable**, the same standard as a
Goal/Loop Goal document: "a third free export within 30 days is
blocked" is checkable, "quota should work" is not.

### 5. Sales Page Engine — a real page, not a mockup

**Input:** Stage 3's DNA (exact hex/fonts/voice) + Stage 4's offer/pricing.

**Output:** a single working page following the direct-response
skeleton that showed up in the source example and is reusable
independent of any one product: hero → pain (bulleted, sharpened by one
concrete price-contrast statement) → mechanism (how it actually works,
in plain terms) → offer stack → pricing → guarantee → who this is
for/not for → FAQ.

**Follow this project's screenshot-before-done rule here** — this stage
produces a visual artifact, so it's not done until served locally,
screenshotted, and checked against `design-rules.md`/DNA Lock, same as
any other page in this project.

### 6. Launch Pad — ad assets + a launch plan

**Input:** Stages 3–5.

**Output:** a short set of ad variants (using Stage 3's do-say phrases
and Stage 5's core pain/offer framing, not reinvented copy) + a launch
plan: where to post first, in what order, and what the first-customer
target looks like (a specific number, not "get some sales").

**No existing project file for this stage either** — new territory for
this project, same as Stage 2. Write it as `## Launch Plan` in
`business-brain.md` once a real build reaches this stage, so the whole
arc (interview → idea → brand → build → sales page → launch) lives in
one place per business, the same way `business-brain.md` was already
meant to be the shared source of truth.

## Copy-paste starter prompt

```
Run this build through the Build Brain method (/prompts/build-brain-method.md):
1. Interview me for real business context — ask one question at a time,
   accept "skip," and flag if my answers are too thin to produce a
   tailored result rather than a generic one.
2. Propose one concrete idea plus 2-3 alternatives you set aside, with
   why.
3. Lock a brand DNA (colour, fonts, voice do-say/don't-say, name,
   tagline) — write it into design-rules.md.
4. Write the full build prompt (stack, features, data model, testable
   acceptance criteria) and then actually build it, following the
   Software Factory method.
5. Build the sales page from the same DNA, screenshot it before calling
   it done.
6. Draft ad variants and a launch plan with a specific first-customer
   target.
Show me each stage's output before moving to the next one.
```
