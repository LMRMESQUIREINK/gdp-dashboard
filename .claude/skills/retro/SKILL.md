---
name: retro
description: After a build, a ruthless-gate round, or an analyze-and-ship round — especially one that found a real bug or went sideways — look back at the session and suggest changes to the environment (CLAUDE.md, a skill, design-rules.md, a test/check) rather than the code just shipped. Use when a round is finished, before starting the next one.
---

# Retro

Adapted from the real retro skill in Matt Pocock's open-source
mattpocock/skills repository (github.com/mattpocock/skills — analyzed
in /notes/mattpocock-skills-analysis.md), rebuilt for this project's own
environment rather than ported: that repo assumes an issue tracker, a
CI pipeline, and `CODING_STANDARDS.md`; this project's equivalents are
`CLAUDE.md`, `design-rules.md`, this project's own skills, and the
build-local test suites every round already writes.

This is not a code review (that's what the screenshot-before-done rule
and each build's own test suite already do). It asks a narrower
question: **given what just happened, should the *environment* change
so the next round starts from a better position?** The answer is never
"edit the code again" — that round is already shipped.

## The five lenses

Work through each one. Not every round needs a change on every lens —
"no change needed" is a legitimate, common answer, same as this
project's own "no build needed" outcome on a survey-type source.

1. **Navigation** — did this round spend real effort finding something
   that a pointer would have made instant? (A fact buried in a long
   `CLAUDE.md` status entry, a build's own convention not written down
   anywhere a cold session would see it.) *Fix*: a short cross-reference
   added where the next session will actually look, not a new document
   nobody will open.

2. **Automated checks** — did a bug get caught by *reading* something
   carefully, when a script could have caught it on every future run
   for free? This project's own history has several: `skill-md-
   validator`'s two real bugs were each caught by running the tool
   against this project's own real skills, not by inspection;
   `ten-k-website-grader`'s real accessibility gap was found by running
   the grader against Recovery Desk's already-shipped page. *Fix*: a new
   assertion in the relevant build's test suite, or — if the gap is
   project-wide, like the "found via direct recomputation, not from the
   source's own claim about itself" discipline — a line in this skill
   or in `CLAUDE.md` naming the check explicitly enough that a cold
   session reproduces it instead of reinventing it.

3. **Standing rules** (`CLAUDE.md`, `design-rules.md`, a skill) — same
   mechanical-vs-judgement split the real `retro` skill draws: a
   **mechanical** miss (a fixed pattern — a banned phrase, a missing
   file, a specific wrong regex shape) belongs in a deterministic check
   per lens 2, never a prose rule alone. A **judgement-call** miss
   (reading a claim in context before flagging it, deciding whether a
   build is warranted) belongs in a rule here, because no script can
   make that call. This project already does this correctly in several
   places — the `design-rules.md` don't-say-list grep *plus* `humanizer`
   as the deterministic check behind it, not a rule standing alone.

4. **Tool economy** — did this round repeat an expensive step (a full
   repo clone, a long `WebSearch`, re-deriving a fact already measured
   in a prior round) that a pointer to the earlier result would have
   skipped? *Fix*: cite the earlier `/notes/` file or build directly
   instead of re-measuring, the way `/builds/curriculum-link-auditor`'s
   second round reused its own first round's fixtures rather than
   re-cloning.

5. **Information access** — was there a fact this round needed but
   couldn't get (no live API key, no network access to a given host,
   no account to click through)? If it's a real, standing sandbox
   restriction, it belongs in the finished build's README as a named
   limitation (this project's standing convention), not silently
   worked around or silently dropped.

## When to run it

- After any round that found and fixed a real bug in this project's own
  build (the "found and fixed a real bug" pattern that appears in
  nearly every `CLAUDE.md` status entry) — ask whether the *next* round
  would hit the same class of bug, and whether a check now prevents
  that.
- After a `ruthless-gate` or `analyze-and-ship` round goes sideways (a
  wrong first-pass finding later corrected, a detector that had to be
  widened rather than the evidence rejected — see `ruthless-gate`'s own
  "fix the value, never the threshold" rule, which is lens 3's
  mechanical case stated for an audit instead of a build).
- Skip it after a round with nothing to report — a clean first-pass
  build, a "no build needed" survey round. Forcing a finding where none
  exists is the same failure mode `ruthless-gate` warns against for
  padding credits: don't manufacture a retro finding to look thorough.

## Worked example, against this project's own real history

Applying the five lenses to the `FareedKhan-dev/ontology-driven-
observability` `ruthless-gate` round (`/builds/ontology-observability-
gate/`):

- **Navigation**: no change — the round's own `/notes/` pointer already
  cross-references the build and the generalizable spinoff.
- **Automated checks**: real finding. The round's central discovery (a
  committed fingerprint manifest no longer matching its own files) was
  caught by hand, once, for one repo. `/builds/manifest-drift-guard/`
  is exactly this lens's fix — a reusable check, not a one-off
  observation, built in the same round rather than deferred to a retro
  that might never run.
- **Standing rules**: no change — the finding was a fact about the
  *audited* repo, not a gap in this project's own gate procedure.
- **Tool economy**: no change — the round's own clone and measurement
  were the first ones for this source.
- **Information access**: real, already-stated finding — no live
  Netflix Technology Blog access, already named in the build's coverage
  section rather than silently worked around.

Three of five lenses returned "no change," which is the expected
outcome for a round that already shipped its own fix inline — a retro
isn't owed a finding on every lens every time.
