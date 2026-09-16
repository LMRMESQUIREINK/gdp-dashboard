---
name: new-feature
description: Isolate a new feature or fix in its own git worktree/branch before touching code, so parallel work (multiple agents, multiple sessions) never overwrites or conflicts with other in-progress work. Use before starting any nontrivial feature, fix, or build — the "isolate" station of the software factory (isolate → build → prove → ship).
---

# New Feature (Isolate)

Every nontrivial change starts on its own branch, isolated from any other
work in progress. This is step 1 of the software factory: **isolate →
build → prove → ship**. The goal is simple — no agent, session, or
person overwrites another's in-progress work, and `main`/the shared PR
branch is never worked on directly for a multi-file change.

## When to use this

Before starting any feature, fix, or build that touches more than a
trivial one-line change — especially when you know or suspect another
agent/session might be working on this repo at the same time.

## Steps

1. **Sync with the base first.**
   ```
   git fetch origin <base-branch>
   ```
2. **Create an isolated workspace.**
   - If working locally with `git worktree` available and multiple
     parallel builds are genuinely needed:
     ```
     git worktree add ../<repo>-worktrees/<feature-slug> -b <feature-slug> origin/<base-branch>
     ```
   - In a single Claude Code on the web / cloud session (this
     environment), true worktrees aren't necessary — isolation instead
     means: **one feature per branch, one branch per PR, never mix
     unrelated changes into the same commit or PR.** If a second,
     unrelated ask comes in while one build is in flight, treat it as a
     separate branch/PR rather than folding it into the current one.
3. **Never build directly on `main` or the shared base branch.** Always
   work on a feature branch, even for something that feels small.
4. **When the feature is done** (after it has passed `build`, `prove`,
   and `review-loop`), merge it back — via PR merge, not by hand-editing
   the base branch — and clean up the branch/worktree.

## Why this matters

The failure mode this prevents: two lines of work touching the same
files at the same time, where one agent's edits silently clobber
another's, or a single agent conflates two unrelated asks into one messy
diff that's hard to review or revert. Isolation is what makes running
several features "in parallel" (multiple agents, multiple sessions) safe
instead of chaotic.
