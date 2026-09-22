# "RUTHLESS AFFILIATE GOLD" Build Wizard — Deep Analysis

Source: a plain-text export of a six-stage SaaS-idea-to-launch wizard
session, captured mid-run (Ad assets and Launch plan still show "Build →"
rather than "Open →" — those two stages hadn't been run yet when this was
exported). The worked example inside it is a fictional/demo product
called **RemixForge** (a video-remix SaaS), built from maximally generic
interview answers ("A Product & A Service", "Nothing yet", "A number, a
launch, a first paying customer"). Per this turn's own instruction, the
RemixForge specifics are **not** being built here — this file treats
them purely as a worked example to extract a reusable pattern from. The
actual deliverable is `/prompts/build-brain-method.md` (below).

---

## DEEP — what this actually is

A six-stage pipeline, each stage producing one artifact that feeds the
next:

| # | Stage (as labeled) | Produces |
|---|---|---|
| 1 | Interview Builder | Business context: name, offer, what's been tried, existing assets, 90-day goal, audience |
| 2 | Idea Engine | One chosen idea (name + one-line pitch) + 2 alternatives |
| 3 | DNA Lock | Visual identity (vibe, fonts, palette) + voice (do-say/don't-say/signature phrases) + brand (name, tagline, logo direction) |
| 4 | One Shot Engine | Pricing/offer model + a complete, copy-paste Claude Code build prompt + a recommended tech stack |
| 5 | Sales Page Engine | A finished, single-file HTML landing page styled from the DNA Lock output |
| 6 | Launch Pad | Ad assets + a launch plan — **not yet run** in this export |

Every later stage visibly consumes the earlier ones: the Sales Page's
CSS uses DNA Lock's exact hex codes and both fonts; the build prompt's
"Design system" section repeats the same hex codes and font pair a
third time; the sales copy uses DNA Lock's do-say phrases
("Built for people who ship, not people who plan") and mostly avoids
its don't-say list — see DEEPER for the one place it doesn't.

## DEEPER — quality of the artifact, and one real bug

- **The interview answers are lazy/placeholder-grade, but the output
  isn't.** "Nothing yet" and "A number, a launch, a first paying
  customer" are template defaults, not real answers — yet the Idea
  Engine still produced a fully specific product (RemixForge: three
  named remix styles, a concrete data model, exact pricing). That's a
  strength for demoing the wizard (it never produces an empty or
  generic result even from a lazy run) and a real risk for actually
  using it: a user who breezes through the interview with placeholder
  answers gets a **confidently specific** result that has no actual
  connection to their real business — the specificity can read as
  "the wizard understood me" when it didn't, because there was nothing
  real to understand yet. Worth flagging in the template below as an
  explicit warning, not just an implicit hope that users fill it in
  properly.
- **A real export bug**: the `palette` field renders as
  `[object Object], [object Object], [object Object], [object Object],
  [object Object]` — five palette entries whose JS objects got
  stringified via default `toString()` instead of having their hex
  values extracted before being written to this export. Not a design
  issue, a plumbing one: whatever serializes this wizard's state into
  a shareable/copyable format has at least one field (palette) it
  doesn't handle. The sales-page HTML that came out of the *same*
  session correctly has real hex codes (`#F5C518` etc.), so the DNA
  Lock stage clearly has the real values internally — they just didn't
  survive this particular export path.
- **One don't-say-list violation, self-inflicted by a later stage.**
  DNA Lock's own `dontSay` list bans "next-level," "cutting-edge,"
  "game-changer," "leverage," "synergy," "empower" — and the sales page
  the *later* Sales Page Engine stage generated stays clean of all six.
  Good discipline propagating a constraint forward. The build prompt
  (One Shot Engine, also downstream of DNA Lock) reinforces this itself
  with an actual acceptance-criteria line — *"no banned words in the
  codebase (add a lint script that greps for them)"* — turning a style
  guideline into a testable, CI-enforceable check. That's the single
  best idea in the whole export: a brand voice constraint that isn't
  just documentation, it's a grep the build has to pass.
- **The build prompt is genuinely well-engineered**, independent of
  RemixForge's specific content. Its shape: role/context → what's being
  built → who it's for → recommended stack → numbered core features →
  explicit data model → **constraints and do-nots** → **acceptance
  criteria** (testable, specific: "a third free export within 30 days
  is blocked," not "quota should work") → a closing instruction that
  explicitly says *"do not ask questions... make smart defaults... note
  each in `DECISIONS.md`."* That closing instruction is structurally
  identical to this project's own general working rule — *"when
  something is ambiguous, make a reasonable assumption, state it in one
  line, and proceed"* — arrived at independently by whatever built this
  wizard. That convergence is worth noting as validation, not
  coincidence to shrug off.
- **The sales page is a template-quality direct-response landing page**:
  hero → pain agitation (bulleted, sharpened by one "here's the exact
  price contrast" card) → mechanism → offer stack → pricing grid →
  guarantee → who-it's-for/who-it's-not → FAQ. That structure is
  reusable independent of RemixForge, and it's the same skeleton this
  Claude environment's own `ruthless-pdf-codegen` and
  `ruthless-call-debrief` skills produce for affiliate/sales
  deliverables — this wizard is clearly part of the same "RUTHLESS"
  branded tool family already present as skills here, not an unrelated
  product.
- **The export is truncated**, not just incomplete-by-design: the FAQ's
  last answer cuts off mid-sentence ("No contracts, no canc...").
  That's a data-loss artifact of the `.txt` capture, separate from the
  Launch Pad stage being legitimately not-yet-run (that one shows as
  "Build →" in the UI, not a truncation).

## DEEPEST — the pattern underneath, and why it matters to this project specifically

This wizard's six stages aren't a random SaaS-building checklist — they
map almost exactly onto files and rules this project's own `CLAUDE.md`
already has, plus two the project doesn't:

| Wizard stage | This project's equivalent | Status here |
|---|---|---|
| Interview Builder | `business-brain.md` | Exists (empty template) |
| DNA Lock | `design-rules.md` | Exists (starter defaults) |
| One Shot Engine | Software Factory method (isolate→build→prove→ship) | Exists |
| Idea Engine | — | **No equivalent** |
| Sales Page Engine | — | **No equivalent** |
| Launch Pad | — | **No equivalent** |

The DEEPEST-level read: this upload isn't "build me RemixForge" — it's
a worked example of a capability this project doesn't have three pieces
of yet (a structured idea-selection step, a sales-page generation step,
and a launch-assets/plan step), shown via a product built by a
tool in the same branded family as skills already installed here. Given
this turn's explicit "use this as a template only," the right move is
to generalize the six-stage shape into a reusable method — the same way
`/prompts/goal-loop-method.md` already generalizes "write a Goal
document, then loop against it" into something reusable across builds
— rather than either building RemixForge or leaving the pattern
implicit in one uploaded export.

## DEEPEST-EST — what actually got built from this

`/prompts/build-brain-method.md`: a six-stage, domain-agnostic template
with the RemixForge specifics stripped out and replaced by placeholders,
each stage naming its required inputs, its output artifact, which
existing project file/method it maps to (or that it's new), and the two
lessons pulled directly from this analysis: the "lazy interview →
confidently specific output" risk (Stage 1 now says so explicitly), and
the don't-say-list-as-a-lint-script idea (folded into Stage 3's output
spec). Added as a new "Build Brain method" entry under TECHNIQUES in
`CLAUDE.md`, alongside Goal/Loop method and Software Factory method —
this project's third named, reusable technique.
