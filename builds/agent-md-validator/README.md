# agent-md-validator

A real, dependency-free Python linter for Claude Code's subagent
definition format (`.claude/agents/*.md`), built from an uploaded
Medium article ("Claude Code Agents: How to Build Your Own AI Team,"
cskumara2000) and the verification round it prompted — see
`/notes/claude-code-agents-ai-team-analysis.md`.

## Why this exists

Checking the article's claims against the real Claude Code docs (via
this session's own `claude-code-guide` subagent, built specifically for
exactly this class of question) surfaced one concrete, actionable fact:
**Claude Code silently ignores an unrecognized subagent frontmatter
field rather than raising an error.** A typo'd field name
(`discription` instead of `description`) fails invisibly — the product
gives no warning anywhere. This project had zero `.claude/agents/`
files before this round, so there was nothing to extend; this tool
exists to catch exactly that failure mode, plus a handful of other
real, verified constraints on the format, before a typo ships silently.

## What it checks

- `name` and `description` are present (required fields).
- Any field not in the real, documented set (`name`, `description`,
  `tools`, `disallowedTools`, `model`, `effort`, `permissionMode`,
  `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`,
  `isolation`, `color`, `initialPrompt`) is flagged — the typo-catcher
  this tool exists for.
- `effort`, if present, is one of the five real values
  (`low`/`medium`/`high`/`xhigh`/`max`).
- `permissionMode`/`isolation`, if present, are real values.
- `model`, if present, is a known alias (`sonnet`/`opus`/`haiku`/
  `fable`/`inherit`) or looks like a real model ID — a soft warning,
  since model IDs change and this isn't trying to be an exhaustive list.
- A tool confirmed to be **always stripped from subagents regardless of
  what's listed** (`AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode`,
  `Agent`) is flagged as a pointless no-op, not an error.
- The body (the subagent's actual system prompt) isn't empty.
- A trailing `# comment` on a YAML value (the article's own example
  uses `tools: Read, Grep, Glob        # read-only`) is parsed
  correctly, not treated as part of the value.

## What it's NOT

Not a reimplementation of the full YAML spec — same deliberate
narrowing as this project's own `skill_md_validator.py` (whose generic
frontmatter parser this one is structurally copied from, not imported,
per this project's established cross-build convention): simple
`key: value` lines only, raising rather than silently mis-parsing
anything more exotic. Not an exhaustive tool-name validator — the real
tool universe is large and evolving, so an unrecognized tool name is
never flagged; only the four confirmed-always-stripped names are.

## Built alongside two real, new agent files for this project

`.claude/agents/code-reviewer.md` and `.claude/agents/security-reviewer.md`
— this project had none before this round, despite its `review-loop`
skill explicitly naming "an external tool... otherwise a rigorous
self-review checklist" as its only fallback, with no isolated-context,
fresh-eyes reviewer option. `security-reviewer.md` adapts the
article's own literal worked example (the one piece of real,
complete, runnable content it gives) rather than inventing a different
one, since this project genuinely has security-relevant surface to
review: untrusted binary/file-format parsing
(`go-buildinfo-extractor`, `rust_cargo_auditable`), an MCP server over
stdio/HTTP (`prop-firm-mcp-server`), and approval/governance logic
(`policy-control-plane`, `agent-checkpoint-layer`).

## Proven

```
python3 -m pytest test_agent_md_validator.py -v   # 16/16 passing
python3 agent_md_validator.py ../../.claude/agents
```

```
[PASS] ../../.claude/agents/code-reviewer.md
[PASS] ../../.claude/agents/security-reviewer.md

2 agent file(s) checked, 0 error(s), 0 warning(s)
```

16/16 tests pass, including a discrimination test (a single planted
fixture with four distinct deliberate problems — a typo'd field, a
pointless always-stripped tool, an invalid `effort` value, and the
resulting missing real description — produces exactly those four
findings and nothing else) and a real subprocess CLI run against this
project's own two new agent files, both passing clean.

## What's deliberately not built

An interactive agent-creation wizard matching the article's own
"Step 3" — the real, current `/agents` slash command doesn't work that
way anymore (confirmed during this round's verification: that flow
existed through Claude Code v2.1.197 and current builds just point back
at asking Claude directly or editing files by hand), so reproducing the
old wizard behavior here would mean building something the product
itself no longer does.
