# Analysis: "Claude Code Agents: How to Build Your Own AI Team" (cskumara2000, Medium)

Source: a pasted Medium article about Claude Code's subagents feature —
`.claude/agents/*.md` files, their frontmatter, how they differ from
Skills, and a step-by-step guide to writing one. Unlike every prior
round in this project, this source is checkable against this session's
own real, authoritative tool (the `claude-code-guide` subagent, built
specifically for exactly this class of question) rather than a web
search or a cloned repo — so that's what was used, against the real
current Claude Code docs (`code.claude.com/docs/en/sub-agents.md`,
`skills.md`, `commands.md`).

## What checked out, and what didn't

1. **`.claude/agents/your-agent-name.md`** — accurate. Project
   subagents live there (shared, checked into the repo); personal ones
   live in `~/.claude/agents/`. The article omits that subagents can
   also come from a `--agents` CLI flag, managed settings, or a
   plugin's `agents/` directory, with a documented priority order.

2. **The `security-reviewer.md` frontmatter example** — mostly accurate,
   and one specific suspicion going into this check turned out to be
   **wrong**: `effort: high` looked unlikely to be a real subagent
   frontmatter field (easily confusable with the SDK's `effort`
   parameter elsewhere), but it genuinely is — real, documented,
   accepting `low`/`medium`/`high`/`xhigh`/`max`. `name`/`description`/
   `tools`/`model` are all real too. What the article's one example
   doesn't show: `disallowedTools`, `permissionMode`, `maxTurns`,
   `skills`, `mcpServers`, `hooks`, `memory`, `background`,
   `isolation: worktree`, `color`, `initialPrompt` all exist as real
   fields. **The single most concrete, actionable fact surfaced by this
   check**: unrecognized frontmatter fields are silently ignored rather
   than raising an error — a typo'd field name fails invisibly, with no
   warning anywhere.

3. **"Step 3 — use the `/agent` command"** — **genuinely wrong, not
   just imprecise**. The real command is `/agents` (plural); `/agent`
   doesn't exist as a slash command. More importantly, the article's
   described behavior ("opens an interactive flow... asking what the
   agent should do, what files it needs, what tools") is outdated: that
   wizard existed through Claude Code v2.1.197, but on current builds
   `/agents` just prints a reminder to ask Claude directly or edit the
   files by hand. This is the one claim in the article that doesn't
   just need a footnote — it actively tells a reader to do something
   that no longer works as described.

4. **Context window / system prompt / tool access / permission mode** —
   mostly accurate, two real corrections. A subagent does **not**
   inherit the conversation history, invoked skills, or files already
   read — it works from a delegation message plus its own system
   prompt, not a continuation of the main context (the article implies
   isolation without being this specific about what "isolation" means).
   And permission mode is **inherited from the main session** unless
   `permissionMode` is explicitly set — if the main session runs in
   `bypassPermissions`/`acceptEdits`/auto mode, a subagent's own setting
   is ignored. The article's stated *rationale* (keeping noisy tool
   output out of the main context) is a fair practical consequence of
   isolation, but not what the docs themselves state as the reason
   subagents exist — a reasonable inference presented a little more
   confidently than the source material supports.

5. **Skills vs. agents, "recipe vs. chef"** — a reasonable simplification,
   but more binary than reality: a skill with `context: fork` runs
   inside an isolated subagent; a subagent can preload skills via its
   own `skills` field; and custom commands have been merged into skills
   entirely (`.claude/commands/deploy.md` and
   `.claude/skills/deploy/SKILL.md` both create `/deploy`). The
   metaphor is a fine first mental model, not a complete one.

## A real, well-evidenced gap in this project itself

This project has 12 real skills (`.claude/skills/`) and one slash
command, but **zero subagent definitions** — confirmed by checking the
filesystem directly, not assumed. The CLAUDE.md "Software Factory
method" implements its four stations (isolate/build/prove/ship) as
skills running in one continuous session; the `review-loop` skill's own
stated fallback, "an external tool like Greptile/CodeRabbit if one's
configured, otherwise a rigorous self-review checklist," has no
isolated-context, fresh-eyes reviewer option at all — exactly the gap
this article's own credited "Reviewer" pattern (fresh eyes, a
checklist, no ego because it didn't write the code) fills.

## Built

- **`.claude/agents/code-reviewer.md`** and
  **`.claude/agents/security-reviewer.md`** — two real, read-only
  (`Read, Grep, Glob`) subagents for this project, giving `review-loop`
  a concrete isolated-context reviewer it didn't have before.
  `security-reviewer` adapts the article's own literal worked example
  rather than inventing a different one, since this project genuinely
  has security-relevant surface to review (parsing untrusted binaries
  in `go-buildinfo-extractor`/`rust_cargo_auditable`, the MCP server in
  `prop-firm-mcp-server`, the approval/governance logic in
  `policy-control-plane`/`agent-checkpoint-layer`). Both report
  PASS/FAIL per rule with file:line references and write nothing,
  matching the article's own credited design exactly.
- **`/builds/agent-md-validator/`** — a small, dependency-free Python
  checker for `.claude/agents/*.md` frontmatter, built directly from
  today's verification rather than guessed: required `name`/
  `description`, a `KNOWN_FIELDS` set built from the real documented
  field list above (flagging anything else as a likely silent-typo
  risk — operationalizing the single most concrete finding from this
  round), valid `effort` values, a permissive (warn-not-fail) check for
  the three tools confirmed always stripped from subagents regardless
  of what's listed (`AskUserQuestion`, plan-mode tools, `Agent` at the
  depth limit), and valid `permissionMode`/`isolation` values where
  present. Run against this project's own two new real agent files —
  both pass cleanly. A deliberately planted bad fixture (a typo'd
  `discription` field, an invalid `effort: extreme`, a listed
  `AskUserQuestion` tool) correctly produces three distinct findings,
  proving the checks actually fire rather than rubber-stamping
  everything.

## What's deliberately not built

A `/agent`-command-shaped interactive wizard — the real, current
`/agents` command doesn't work that way anymore, and reimplementing the
old wizard behavior the article describes would mean building something
Claude Code itself no longer does. A Planner/Coder pair matching the
article's "3 Classic Agents" pattern — this project's existing
`new-feature`/`code-structure` skills already cover that ground within
one continuous session, and splitting them into separate-context
subagents here would duplicate rather than fill a gap, unlike the
Reviewer, which had no equivalent at all.
