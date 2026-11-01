# SKILL.md Validator

A real, dependency-free Python linter for Claude Code's `SKILL.md`
format, built from a pasted three-article AgentsKit.co bundle — full
analysis in `/notes/agentskit-claude-tooling-bundle-analysis.md`. The
bundle names a "free SKILL.md validator" tool
(`agentskit.co/claude-skill-md-validator`), but that's a web product
with no inspectable source, so this is an independent build of the
idea, grounded in reading this project's own eleven real skills
(`.claude/skills/*`) rather than a port of theirs.

## What it checks

1. `SKILL.md` exists and has parseable frontmatter (a deliberately
   minimal parser — simple `key: value` lines only; anything more
   exotic raises rather than silently mis-parsing).
2. `name` exists, is lowercase-hyphenated, and matches the skill's own
   directory name exactly.
3. `description` exists, isn't too short to plausibly state both what
   the skill does and when to use it, and isn't so long it risks
   crowding the always-loaded skill index. (These length bounds are
   this project's own stated heuristic — this build could not find or
   confirm an Anthropic-documented hard limit, so it doesn't claim one.)
4. `description` states a usage condition (advisory warning, not a
   hard failure, since this is observed best practice across this
   project's own skills, not a documented requirement).
5. The body (after the frontmatter) is non-empty and isn't just the
   description restated with nothing added.
6. Every file reference in the body resolves to a real file — checked
   against **both** the skill's own directory (for
   `references/foo.md`-style same-folder links) and the repo root (for
   `/builds/...`, `/notes/...`, or bare `.claude/skills/other-skill`
   style cross-references) — see the real bug below for why both.
7. No two sibling skills declare the same `name` — the exact failure
   class `bytedance/deer-flow`'s own `docs/SKILL_NAME_CONFLICT_FIX.md`
   documents (analyzed in an earlier round of this project,
   `/notes/deer-flow-analysis.md`), not a hypothetical one invented for
   this build.

## Usage

```bash
python3 skill_md_validator.py .claude/skills          # a directory of skills
python3 skill_md_validator.py .claude/skills/humanizer  # a single skill
python3 skill_md_validator.py .claude/skills --json
```

Auto-detects the repo root by walking up for a `.git` directory, prints
which root it resolved references against, and exits non-zero if any
skill has an error (warnings don't fail the run).

## Two real bugs found and fixed while testing, both in this build's own first draft, not in the real skills it was tested against

1. **The broken-reference check's first draft assumed every reference
   is relative to the skill's own folder.** Running it against this
   project's real `.claude/skills/` immediately produced **16
   false-positive `broken-reference` errors across 7 of the 11 real
   skills** — every one of them a reference like `/builds/humanizer/
   README.md`, `/notes/ruthless-affiliate-gold-build-brain-analysis.md`,
   or a bare `.claude/skills/voice-extractor`, all genuinely valid,
   repo-root-relative cross-references this project's skills actually
   use. Fixed by trying both resolutions (skill-dir-relative and
   repo-root-relative) and only flagging a reference broken if neither
   resolves — `test_repo_root_relative_references_resolve_with_repo_root_given`
   locks in both the original false positive (reproduced deliberately,
   as a sanity check) and the fix.
2. **The "states a usage condition" heuristic missed real, correctly-
   phrased trigger language.** `.claude/skills/code-structure` and
   `.claude/skills/review-loop` both state exactly when to use them
   ("Use while implementing any feature or fix...", "Before calling a
   build finished, run it through a review pass...") but phrased it as
   "Use while" and "Before calling," neither of which the first
   draft's trigger-word list recognized — caught by reading the two
   flagged files by hand rather than trusting the tool's own warning,
   confirming it was the heuristic's gap, not a real gap in those two
   skills. Fixed by widening the trigger-word list; both skills now
   pass clean.

## Proven

```bash
python3 test_skill_md_validator.py -v
```

**19/19 tests pass**, including:

- Every check exercised against a dedicated, deliberately-broken
  fixture (`tests/fixtures/*`) — a bad name format, a name/directory
  mismatch, a missing or too-short description, a missing trigger
  phrase (confirmed advisory, not blocking), an empty body, a thin
  body that just restates the description, unparseable frontmatter, a
  missing `SKILL.md` entirely, and a genuinely broken same-folder
  reference.
- A dedicated two-skill fixture root (`tests/fixtures-dup-root/`) both
  declaring `name: shared-name`, proving the duplicate-name check fires
  on both siblings, and a separate check that distinct names across
  siblings never get falsely flagged.
- Both real bugs above, each with its own named regression test that
  reproduces the original false positive as a sanity check before
  proving the fix.
- **The actual deliverable**: `test_all_real_skills_pass_clean` runs
  the validator against this repo's real `.claude/skills/` directory
  and asserts all eleven skills pass with zero findings — spot-checked
  by hand (not just trusted) by reading the two files that produced
  warnings before the second bug fix, confirming the warning was a
  tooling gap and not a real documentation gap in those skills.

## What's not built here

- A check for whether a skill's description length sits within any
  Anthropic-documented hard limit — not built, because this project
  could not confirm such a limit exists with enough confidence to
  enforce it as fact; the length checks here are stated plainly as
  this project's own heuristic bounds, not a cited specification.
- Validation of multi-skill plugin manifests, `allowed-tools`
  restrictions, or any YAML beyond simple `key: value` lines — this
  project's own eleven real skills never use any of that, so there was
  no real material to build or test it against.
