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
   crowding the always-loaded skill index. Two separate thresholds now,
   not one: a hard `1500`-char "too long" error (this project's own
   original heuristic, since this build could not find or confirm an
   Anthropic-documented hard limit), and a new, softer `500`-char
   "over the recommendation" **warning** — a real, dated figure from
   `coreyhaines31/marketingskills`' own measured character budget, not
   invented here (see below).
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
8. **Pack-level, not just per-skill** (new this round, `validate_pack()`):
   the total character budget of every description in the pack combined
   (warn at 19,000 / flag at 30,000 — marketingskills' own real,
   dated measurement of Claude Code's skill-listing character cap), and
   pairwise description overlap across the whole pack (Jaccard
   similarity ≥ 0.4 on significant words, a heuristic proxy for "these
   two skills might compete for the same trigger," never a real
   live-model trigger-accuracy test — see below for what that would
   actually take).

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

**31/31 tests pass**, including:

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
- **The actual deliverable**: `test_all_real_skills_pass_with_no_errors`
  runs the validator against this repo's real `.claude/skills/`
  directory (now 12 skills, not 11) and asserts zero **errors** — spot-
  checked by hand (not just trusted) by reading the two files that
  produced warnings before the second bug fix above, confirming the
  warning was a tooling gap and not a real documentation gap in those
  skills.
- `test_four_real_skills_now_warn_over_the_real_500char_recommendation`
  — a real finding from this round, not synthetic: against this
  project's own real skills, `launch-kit-writer` (721 chars),
  `sales-page-engine` (613), `voice-extractor` (576), and `launch-pad`
  (519) all genuinely exceed the new 500-char recommendation. (A first
  draft of this test only named three, having miscounted `launch-pad`'s
  519 as under the line when it isn't — the test suite itself caught
  the miscount on its first real run, and the test was corrected to
  match the real count rather than the other way around.) All four are
  warnings, not errors — still comfortably under this project's own
  pre-existing 1500-char hard ceiling.
- `TestPackDescriptionBudget` (4 tests) and `TestDescriptionOverlap`
  (5 tests) — both exercised against synthetic fixtures that cross
  the warn/cap thresholds and deliberately-overlapping descriptions,
  *and* against this project's own real 12-skill pack: total
  description budget is ~5,549 characters (`test_real_run_against_
  this_repos_own_skills_is_nowhere_near_the_budget`), nowhere close to
  either the 19,000-char warn line or the 30,000-char hard cap, and zero
  cross-skill description overlap is found (`test_real_run_against_
  this_repos_own_skills_finds_no_overlap`) — both honest, non-
  manufactured "no problem found" results, not failures forced into
  existence to pad the test count.
- `test_shared_boilerplate_trigger_phrasing_alone_does_not_count_as_
  overlap` — proves the overlap check's dedicated stopword list
  (`OVERLAP_STOPWORDS`, distinct from the generic `_similarity()`
  helper's unfiltered Jaccard used for thin-body detection) actually
  does what it's for: two skills that only share this project's own
  trigger-phrase boilerplate ("use when the user wants to...") don't
  get falsely flagged as content overlap.
- `TestValidatePack` (2 tests) — including a real subprocess CLI run
  confirming the new `{"skills": [...], "pack_level": [...]}` JSON
  output shape.

## The marketingskills round: where the 500/19,000/30,000 figures come from

Added from a bare repo link, `coreyhaines31/marketingskills` — a real,
MIT-licensed, actively-maintained 53-skill Claude Skills marketplace by
Corey Haines (independently confirmed real via web search: SaaS
marketing consultant, Swipe Files, Conversion Factory), with its own
real CI (`regression-tests.yml`, `validate-skill.yml`,
`skill-packaging.yml`, `sync-skills.yml`, `check-versions.yml`) and a
disclosed-sponsorship `tools/PARTNERS.md` with a stated non-influence
boundary. Full write-up in `/notes/marketingskills-analysis.md`.

The one figure worth building a real check around:
`evals/triggers/README.md` documents, with a dated, reproducible
methodology ("Checked on 2026-11-09 with Claude Code 2.1.319 by reading
the `skill_listing` the session recorded"), that Claude Code caps the
total skill-listing text sent to the model at roughly **30,000
characters** — skills past that cap show as a bare name with no
description at all, silently losing their only shot at triggering
correctly. Their own measured table across pack versions: before
2.14.3, 42,105 chars (26/53 skills name-only even installed alone,
29/53 once crowded with other skills); by 2.14.3, cut to 19,259 chars
(0/53 alone, 2/53 crowded); by 2.14.8–2.14.9, 18,676–18,662 chars (0/0
either way). Their own recommendation from that data: keep each
skill's description at ≤500 characters.

**A real three-way discrepancy found, not resolved by picking one
side**: `AGENTS.md`'s own stated claim is "the spec allows 1024 (this
repo caps it at 500)" for the Agent Skills open spec's documented max —
unverified from this sandbox, since `agentskills.io` doesn't resolve
here (`getaddrinfo ENOTFOUND agentskills.io`, the same restriction
class already documented in this project for EODHD/FMP/Hugging
Face/arXiv/ui.oiloil.org). So there are three different numbers in
play: the Agent Skills spec's claimed 1024-char max (unverified),
marketingskills' own real, dated 500-char self-imposed cap, and this
validator's own pre-existing 1500-char "too long" error threshold
(looser than even the unverified spec max). Resolved here by adding the
500-char figure as a new, separate, softer **warning** threshold
(`description-over-recommended`) rather than replacing or tightening
the existing 1500-char error — the two measure different things ("will
this description get silently truncated in a crowded install" vs.
"is this description so long it's clearly not a description anymore"),
and conflating them into one number would have lost that distinction.

`check_pack_description_budget()` operationalizes the same 19,000/
30,000 figures at the pack level, and `check_description_overlap()`
operationalizes a different, related risk the marketingskills eval
harness measures directly but this sandbox can't reproduce (see below):
two skills whose descriptions read too similarly are exactly the kind
of pair the real trigger-eval harness's `wrong-skill`/`other-skill`/
`near-miss` outcomes are measuring. Both pack-level checks are
deliberately warning-only, never error-level — a design choice, not an
oversight, since neither is a hard failure the way a broken reference
or a missing frontmatter field is.

## What's not built here

- **A live-model trigger-accuracy eval**, the one thing
  marketingskills actually has that this validator doesn't and
  structurally can't from this sandbox:
  `evals/triggers/scripts/trigger-eval.mjs` runs several hundred real
  prompts through headless `claude -p` with the pack loaded as a
  plugin and scores which skill actually gets invoked
  (`pass`/`wrong-skill`/`other-skill`/`no-trigger`/`false-trigger`/
  `error`) — a real measurement of trigger *accuracy*, not just
  description *length/overlap*. This sandbox has no live Anthropic API
  access to run a nested nested `claude -p` nondeterministically
  against real prompts, the same standing restriction as every other
  build in this project that needs a live model call.
  `check_description_overlap()`'s Jaccard-similarity flag is stated
  plainly, in both this README and the module's own docstring, as a
  cheap static *proxy* for that risk, not a substitute for it — marketingskills'
  own harness reports real measurement noise even with a live model
  (three identical crowded runs scoring 80.2%/84.0%/87.7%), which a
  static text check has no way to reproduce or approximate.
- A check for whether a skill's description length sits within any
  Anthropic-documented hard limit as a cited specification — still not
  built, for the same reason as before: this project could not
  independently confirm the Agent Skills spec's claimed 1024-char
  figure from this sandbox (see above).
- Validation of multi-skill plugin manifests, `allowed-tools`
  restrictions, or any YAML beyond simple `key: value` lines — this
  project's own twelve real skills never use any of that, so there was
  no real material to build or test it against.
