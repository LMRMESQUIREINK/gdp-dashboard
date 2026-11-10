# Analysis: Matt Pocock's AI Coding Skills (mattpocock/skills)

Source: a pasted article, "Matt Pocock's AI Coding Skills: A Complete
Workflow From Idea to Production-Ready Code," covering the real,
open-source GitHub repo `mattpocock/skills` — cloned and read directly
(`GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1
https://github.com/mattpocock/skills.git`, commit `4ae2317`, 2026-10-31,
MIT licensed, real plugin `mattpocock-skills@1.3.2` with 27 shipped
skills). A genuinely new source for this project — no prior round has
analyzed it.

## What checked out

- The six skills the article walks through — `grill-with-docs`,
  `to-spec`, `to-tickets`, `implement`, `code-review`, `retro` — all
  exist exactly as named under `skills/engineering/`, all shipped in
  the real plugin manifest (`.claude-plugin/plugin.json`), plus the
  `/ask-matt` router it names.
- `code-review`'s description is the most precisely accurate part of
  the article: the real `SKILL.md` runs two **parallel sub-agents**
  (Standards, Spec) and explicitly refuses to merge or rerank their
  findings — matching the article's description closely, down to the
  Standards axis's Fowler-smell baseline (Duplicated Code, Mysterious
  Name, Speculative Generality, Divergent Change — all four the article
  paraphrases are real, named smells in the file).
- `retro`'s five categories (Navigation, Automated checks, Coding
  standards, Tool economy, Information access) match the real
  `SKILL.md` almost verbatim, including the mechanical-vs-judgement-call
  distinction the article describes ("a lint rule can prevent the
  mistake... a paragraph in AGENTS.md may not be enough").
- The real `claude-plugin install` / `npx skills@latest add` ecosystem
  is real and the `mattpocock-skills` plugin name is real (confirmed in
  both `package.json` and `.claude-plugin/plugin.json`).

## What's a real, well-evidenced gap

**The article's install command for Claude Code has a real, checkable
mismatch with the repo's own documented command.** The article gives:

```
claude plugins install mattpocock-skills
```

The repo's own README gives:

```
claude plugin install mattpocock-skills@claude-plugins-official
```

Two differences, not one: "plugins" (plural) vs. the documented
"plugin" (singular), and the article drops the
`@claude-plugins-official` marketplace suffix the repo's own README
requires. A reader copy-pasting the article's exact command would be
running something the repository itself never documents.

**The article names only one of two real, documented downstream-of-
tickets paths.** `skills/engineering/implement/SKILL.md` is a thin
17-line orchestrator (drive TDD per ticket, review, commit) — matches
the article's "implement" description. But a second, separate skill,
`implement-spec` (42 lines), exists specifically for the output of
`to-spec`/`to-tickets`: it reads the tickets as a task graph, runs
implementer sub-agents across the ready "frontier" in parallel, each in
its own git worktree, lands everything on one integration branch, and
runs one `code-review` over the whole thing. The real `/ask-matt`
router names this explicitly as the alternative to driving tickets one
by one ("Reach for it when you'd rather orchestrate the build than
drive each ticket yourself") — the article's own `to-tickets` section
even describes the concept this skill is built for (blocking edges
between tickets) without ever naming the skill that actually consumes
them this way. Not an error in what the article says about
`implement` — a real omission of a second, more-matched skill the repo
documents as the natural next step after the two stages the article
covers just before it.

**A pure naming coincidence, not a derivation either way**: the repo
has an in-progress, unshipped `software-factory` skill — a glossary for
designing a *fully autonomous* ticket/PR/schedule-driven multi-agent
build system. This project's own, unrelated "Software Factory method"
(the isolate→build→prove→ship discipline behind `new-feature`/
`code-structure`/`evidence-driven-testing`/`review-loop`) predates any
knowledge of this repo and means something different — stated here only
because the name-collision is worth knowing about, not because either
influenced the other.

## Build: `.claude/skills/retro`

This project had no retrospective/self-improvement mechanism at all —
every prior round fixes the code in front of it and moves on, with no
step that asks whether the *environment* (CLAUDE.md, a skill,
design-rules.md, a test convention) should change so the next round
starts better. The real `retro` skill is the one mechanism in this
source that's both genuinely new to this project and cleanly portable
without needing an issue tracker, CI pipeline, or multi-agent worktree
infrastructure this sandbox doesn't have.

Rebuilt (not ported) for this project's real environment: the same five
lenses, retargeted at `CLAUDE.md`/`design-rules.md`/this project's own
skills/each build's own test suite instead of `CODING_STANDARDS.md`/CI,
and a worked example applying it to a real round already in this
project's history (the `ontology-driven-observability` `ruthless-gate`
round) rather than a hypothetical — three of five lenses correctly
return "no change," matching the real retro skill's own stance that not
every lens needs a finding every time.

**Verified with this project's own existing `skill-md-validator`
tool**, run against the whole `.claude/skills/` directory, not just the
new file — real bugs in the first draft caught exactly this way, not
by re-reading it: a bare `mattpocock/skills` reference inside backticks
and a not-yet-written `/notes/` path both false-tripped the validator's
broken-reference check (the validator's own regex, confirmed by reading
it, only matches backtick/link-wrapped path-shaped tokens — the first
was a prose fix, wrapping the repo name instead in a plain sentence; the
second resolved once this very file was written), and the description
didn't literally contain a "use when" phrase the trigger-condition
check looks for, fixed by rewording without changing the actual trigger
condition. Clean run afterward: all 12 skills in this project, retro
included, pass with zero errors and zero warnings.
