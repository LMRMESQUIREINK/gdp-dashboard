# Vendoring three real external Claude skills: Emil Kowalski, Impeccable, Taste Skill

Source: a pasted repo link (`github.com/pbakaus/impeccable.git`), a
YouTube Shorts link, and the instruction "3 SKILLS FIRST 'PLUS' 2
CONNECTORS" with a numbered list: 1) Emil Kowalski, 2) Impeccable,
3) Taste Skill. Unlike most sources this project analyzes, this isn't
an article to audit — it's a direct setup instruction, so this round's
work is installing real skills, not writing a critique.

## What was checked first

The YouTube Shorts URL is blocked from this sandbox
(`getaddrinfo ENOTFOUND youtube.com`, same egress-restriction class as
arxiv.org/Hugging Face/agentskills.io/dev.to/medium.com/nocobase.com/
puter.com, now extended to youtube.com) — tried directly via a
web-fetch subagent before concluding this, not assumed. A web search
instead confirmed the three named items are three real, independent,
actively-maintained GitHub repos, not one bundle:

1. **`pbakaus/impeccable`** (Apache 2.0) — Paul Bakaus's "Impeccable,"
   a 24-command design-polish skill with a compiled Rust detection
   engine, a slop detector (62 deterministic rules), a live-mode
   browser overlay, and hooks for Claude Code/Cursor/Codex/etc.
2. **`emilkowalski/skills`** (MIT) — Emil Kowalski's 19-skill
   collection on animation/UI craft, built from his work at Vercel and
   Linear; the README itself names `emil-design-eng` "the main skill."
3. **`Leonxlnx/taste-skill`** (MIT) — "Taste Skill" (`tasteskill
   2.5.1`), an anti-slop frontend-build skill targeting a figma.com/
   x.ai-level result, with its own 40MB asset library (photos, 3D
   objects, scenes) and asset-production tooling.

All three cloned and read directly rather than installed via `npx`
(none of their own install commands were run — `npx impeccable
install`, `npx skills@latest add emilkowalski/skills`, `taste-skill`'s
`install.sh` — since those each write hooks/global config this session
shouldn't touch; files were copied in by hand instead, same convention
as every other cross-build file copy in this project).

## What was vendored, and what deliberately wasn't

Per this project's established "extract the generalizable pattern,
never clone a vendor's own branded instance disproportionately" rule
(the same call made for `morluto/rea`, `bytedance/deer-flow`, and the
RUTHLESS AFFILIATE GOLD wizard before it):

- **`.claude/skills/impeccable/`** — a full, faithful copy. Confirmed
  the real repo ships *two different* `SKILL.md` variants for the same
  version (4.10.0) under `.claude/` and `.agent/` — not a stale
  duplicate, as a first glance at matching filenames suggested, but a
  genuinely different, Claude-Code-specific description and path
  resolution, confirmed by diffing file *content*, not just listing
  file paths (a real instance of this project's own "read the line,
  never just the match" discipline). Copied the real `.claude/`
  variant — the one the repo's own README names as the Claude Code
  target. 2.4MB, 63 files, including the launcher scripts; its
  self-contained detection-engine binary is downloaded on first run
  and wasn't fetched here (see `ATTRIBUTION.md`).
- **`.claude/skills/emil-design-eng/`** — `SKILL.md` only (32KB, no
  runtime dependencies), matching the single named item in the
  instruction rather than all 19 skills in the source repo.
- **`.claude/skills/design-taste-frontend/`** — `SKILL.md` plus all 22
  files under `references/` (468KB total, pure prose: house rules,
  layout/copy/motion/effects rubrics, the gate checklist). Deliberately
  **not** vendored: the real skill folder is 40MB/1,631 files, almost
  all of it a photo/3D-object/scene asset library (38MB) and
  asset-production/browser-check tooling (1.6MB) — disproportionate to
  commit into this project. One real, checked consequence: the file's
  own frontmatter declares a `Stop` hook pointing at `scripts/gate.mjs`,
  which isn't vendored — but the hook's own shell logic degrades
  gracefully when none of its candidate paths exist (writes a note,
  exits 0), confirmed by reading the actual hook script before
  assuming it would error.

## Verified with this project's own `skill_md_validator.py`

Ran the existing validator (built across the marketingskills,
mattpocock-skills, and Scrapling-ecosystem rounds) against the whole
`.claude/skills/` directory — the same "test the tool against new real
material" discipline that's already found real gaps in it three times
before.

- **`impeccable`** passes clean — except a real, genuine false
  positive: `no-trigger-condition` fired against its real description,
  "Use to design, redesign, critique, audit, polish or animate a
  frontend..." — a clearly-stated usage condition the validator's
  `TRIGGER_WORDS` list didn't recognize, because it had "use for" but
  not "use to." Fixed by widening the list, with a regression test
  using this exact real fixture.
- **`design-taste-frontend`** and **`emil-design-eng`** both correctly
  fail with `broken-reference` errors — pointing exactly at the
  `assets/`/`scripts/` paths and the `../choreograph/SKILL.md` sibling
  reference that were deliberately left out, per each skill's own
  `ATTRIBUTION.md`. Not bugs in the vendored copies; the honest,
  expected result of a partial copy whose source cross-references
  content that isn't here — not "fixed" by forcing a pass, same
  discipline as every other "a real, correct fail stays a fail" case
  in this project (`ten-k-website-grader`'s colour-heuristic failure on
  `prop-firm-dashboard`'s real palette, most recently).
- Updated five existing tests whose assertions hardcoded "12 skills"
  (now 15) and the exact failing/warning sets, computed fresh from a
  real run rather than guessed. 37/37 tests pass.

## `design-rules.md` updated

Added a short section establishing precedence: these three skills each
carry their own opinionated default aesthetic (most visibly
`design-taste-frontend`'s figma.com/x.ai house rules), which could
otherwise collide with this project's four already-locked brand DNAs
(RUTHLESS TRADING GOLD, Recovery Desk, The Pass Line, Creator Empire
AI, Solo Claude Bot Business). Stated plainly: when a brand is already
locked, `design-rules.md`'s own values win — these skills are most
useful here as craft/motion/accessibility reviewers layered on top of
an already-locked brand, not as a second source of what a brand should
look like.

## What's still open

**"PLUS 2 CONNECTORS"** — neither the YouTube short (blocked) nor
either skill repo's own docs name two specific connectors meant to pair
with this setup; a web search found no source tying these three skills
to any particular pair. Rather than guess (a Claude connector is an
account-level OAuth integration — wrong guesses here cost real setup
effort, not just a quick edit), this is left for the user to name.
