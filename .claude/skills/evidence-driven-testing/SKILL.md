---
name: evidence-driven-testing
description: Prove a fix or feature actually works by capturing concrete before/after evidence (screenshots, or numbers for non-visual work like performance or data correctness) instead of just asserting it's done. Use before reporting any build complete. The "prove" station of the software factory (isolate → build → prove → ship).
---

# Evidence-Driven Testing (Prove)

Step 3 of the software factory: **isolate → build → prove → ship**.
An agent (or a person) can be wrong about whether something works.
Evidence isn't optional — it's what turns "I think this works" into
"here's proof this works."

This is the general-purpose version of the screenshot-before-done rule
in `CLAUDE.md` — that rule covers visual builds specifically; this skill
covers everything, visual or not.

## The rule

Never report a fix or feature as done without a **before state** and an
**after state**, captured the same way:

1. **Capture the before state first**, ideally before writing the fix —
   reproduce the bug, or show the missing feature, or record the current
   (bad) number. If the before state can't be captured after the fact,
   say so explicitly rather than fabricating or assuming what it was.
2. **Make the change.**
3. **Capture the after state** the same way.
4. **Compare them honestly.** If the after state doesn't actually show
   the fix working, don't report success — go back to `code-structure`
   (build) and keep working. This loop-back happens on your own
   initiative; don't wait to be told the after-shot failed.

## How to capture evidence, by type of work

- **Visual work (pages, components, UI states):** screenshot or short
  recording, served from a real local server (not a `file://` URL). Two
  images side by side, or a labeled before/after pair, embedded in the
  PR description or final report.
- **Performance work:** a concrete number before and after (e.g. "page
  load: 815ms → 61ms"), from an actual measurement, not an estimate.
- **Data/logic correctness:** a test run, a query result, or a specific
  input/output pair shown before and after — actual output, not a
  description of expected output.
- **Bug fixes with no visual surface:** reproduce the error/log line
  before, show the clean run/log after.

## Presenting the evidence

Put both states in the final report to the person, not just in internal
reasoning — they should be able to see the proof, not just be told it
exists. Keep it brief (per `how-i-work.md`'s "brief explain-as-you-go"
style) but never skip showing the actual before/after.
