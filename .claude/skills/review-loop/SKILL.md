---
name: review-loop
description: Before calling a build finished, run it through a review pass (an external code-review tool if one is configured, otherwise a rigorous self-review checklist) and loop back to build/prove until it actually passes — never merge or hand off a build that hasn't cleared review. The "ship" station of the software factory (isolate → build → prove → ship).
---

# Review Loop (Ship)

Step 4 of the software factory: **isolate → build → prove → ship**.
Passing review isn't a formality tacked on at the end — it's the gate
that decides whether the build is actually ready to hand off.

## How to run it

1. **Open the PR with evidence already embedded** — the before/after
   proof from `evidence-driven-testing` goes in the PR description, not
   just in chat.
2. **Check for a configured code-review tool** (Greptile, CodeRabbit,
   Macroscope, or similar). If one is set up for this repo, run it and
   read the feedback plus its confidence score.
   - If none is configured, don't skip review — do a rigorous self-review
     against the checklist below, playing the part of a skeptical
     reviewer rather than the author.
3. **Score against the checklist:**
   - [ ] Matches `code-structure` rules (readable, no duplication, no
     dead code, concerns separated)
   - [ ] Matches `design-rules.md` exactly, for anything visual
   - [ ] Before/after evidence is attached and actually shows the fix
     working
   - [ ] No console errors / no broken states introduced
   - [ ] Nothing outside the scope of this feature got changed
     incidentally
4. **If anything fails:** go back to `code-structure` (build), fix it,
   re-run `evidence-driven-testing` (prove), then come back through this
   skill again. Repeat until everything passes — this loop runs on its
   own; don't stop and ask permission each cycle, and don't lower the
   bar to escape the loop.
5. **Once everything passes:** present the PR to the person as ready.
   **Never merge autonomously** — per `CLAUDE.md`'s general working
   rules, merging is a human decision; this skill's job is to get the
   build to a state where merging is a safe, easy "yes."

## What "five out of five" means here

Whether or not an external reviewer tool is wired up, the standard is
the same: don't report something as ship-ready because it technically
works — report it ready because it would survive a real reviewer's
scrutiny. A build that only "mostly" passes the checklist isn't done;
loop back.
