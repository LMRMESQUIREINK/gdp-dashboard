---
name: proposal-generator
description: Turn discovery-call notes or a client email into a complete, client-ready proposal — project understanding written in the client's own words first, scope, timeline, three pricing tiers, and terms. Use whenever raw notes from a sales or discovery call need to become something a client can actually read and sign. Triggers on phrases like "write a proposal", "turn these call notes into a proposal", "quote this project", or any request to draft a scope-and-price document for a client.
---

# Proposal & Quote Generator

Built from the "Agency Proposal & Quote Generator" idea in the uploaded
"7 claude skills that print money" article. Its one genuinely good
insight, worth keeping front and center: **lead with "project
understanding," written in the client's own words, not a feature list.**
Clients sign when they feel heard, not when they see the longest scope
document. A worked example built from synthetic discovery-call notes
(clearly marked as a demonstration, not a real client's information) is
at `/builds/proposal-generator/example-proposal.md`.

## Before writing anything

1. **Read the raw notes in full first** — a recording transcript, rough
   notes, or a client email. Pull out: what they actually said their
   problem is (in their words, not reframed into generic business
   language), their stated budget range if given, any hard deadline,
   and anything they said they do and don't want.
2. **Never invent a number that wasn't in the notes or confirmed by the
   person asking.** A budget range, a rate, a timeline — if it's not in
   the source material, ask rather than guess. This mirrors the lazy-
   interview-answers warning already documented for
   `sales-page-engine`/`launch-pad`: a proposal built on invented
   specifics looks confident and is wrong, which is worse for a signed
   deal than asking one clarifying question first.
3. **If this project (or the person's own business-brain.md) has an
   established day rate, service menu, or standard terms, use those** —
   don't invent a different rate per proposal. If none exists, ask.

## Structure, in order

1. **Project understanding** — 2–4 sentences, in the client's own
   words/framing where possible ("You mentioned your current
   onboarding flow loses about a third of signups before they finish
   setup, and you want that fixed before your Q2 launch" beats "We will
   improve user onboarding conversion"). This section exists to prove
   the notes were actually read, not summarized generically.
2. **Scope** — a concrete, bulleted list of what's included, specific
   enough that "is this in scope" has an obvious answer later. Name
   what's explicitly **out** of scope too, when the notes suggest the
   client might assume otherwise — an unstated scope boundary is where
   a project quietly grows past its price.
3. **Timeline** — real dates or week numbers tied to the notes'
   deadline, with named milestones, not just a single end date.
4. **Pricing — three tiers.** Not one number: a lean/standard/premium
   (or similarly named) structure, each tier's scope difference stated
   plainly, not just a price difference. Most clients pick the middle
   one when given three real options instead of one take-it-or-leave-it
   number — offer a real middle, not a decoy.
5. **Terms** — payment schedule, what happens on scope change, and
   anything the notes flagged as a client concern (a cancellation
   clause if they asked about one, an IP/ownership line if that came
   up).

## Rules

- Run the finished proposal through `.claude/skills/humanizer` before
  calling it done — a proposal full of "leverage," "seamless," and
  "robust solutions" undercuts the "I actually listened to you" framing
  the whole structure exists to deliver.
- No fabricated urgency or scarcity ("limited availability this
  month") unless the person asking confirmed it's genuinely true — same
  no-invented-pressure rule as every sales page/launch asset this
  project produces.
- Keep the project-understanding section first in the actual document,
  not just first in this list — leading with scope or price is the
  generic-template failure mode this skill exists to avoid.
