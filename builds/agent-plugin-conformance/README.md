# Agent Plugin Conformance Checker

A real, dependency-free Python conformance checker for the **Agent
Plugins 1.0.0** specification
(`agentplugins/agent-plugins-spec`, `spec/1.0.0.md`) — built by reading
the actual, current spec document directly, not guessed from an article
describing it.

Checks a plugin package directory against:

1. **§5 Manifest** — `plugin.json`'s closed top-level schema, the
   required `$schema`/`name` fields, the `name` character-set/length
   rules, the `author` object's closed field set, and the spec's exact
   fatal-vs-non-fatal distinction: an unknown top-level field, or
   `extensions` itself being non-object, are reported and ignored —
   every other schema violation rejects the whole plugin.
2. **§6 Component discovery** — the two fixed component locations
   (`skills/` subdirectories containing `SKILL.md`, `mcp.json`). Missing
   is fine. Present-but-wrong-kind invalidates only that component type,
   never the whole plugin.
3. **§8 Client extensions** — the `extensions` object/value shape, and
   namespace-to-directory correspondence.

Plus one check that isn't in the spec itself: detecting when a directory
uses **Claude Code's own plugin layout** (`.claude-plugin/plugin.json`
instead of a root-level `plugin.json`) — which is not
Agent-Plugins-1.0.0-portable, confirmed directly against real material
rather than assumed.

## Why this, and why now

Checked `/builds/` first: `skill-md-validator` validates `SKILL.md`
frontmatter and body references; `agent-md-validator` validates
`.claude/agents/*.md` subagent frontmatter. Neither validates a
`plugin.json`/`mcp.json` *package* manifest, or the spec's specific
fatal-vs-non-fatal distinction, or component-discovery rules. This is a
different, generalizable gap — checking a plugin author's package
against the real governing spec before they ship it.

## Source

A pasted Medium article ("Stop Shipping Individual MCP Servers. Start
Shipping Agent Plugins," Andrii Tkachuk) describing MCP → Agent Skills →
Agent Plugins as a progression, and the August 2026 Agent Plugins 1.0
specification as the formalization of the third layer. Full analysis in
`/notes/agent-plugins-article-analysis.md`, including:

- A real finding: the article's claim that "Google joined as a core
  maintainer" doesn't match the spec's own current `MAINTAINERS.md`
  (five Core Maintainers listed — Amazon, Cursor, Microsoft, OpenAI,
  Vercel — no Google), checked twice independently against the primary
  governance document rather than repeated from secondary press.
- A claim independently confirmed first-hand: Claude Code's own plugin
  format really doesn't conform to the spec — checked directly against
  this project's own three previously-shipped `/builds/claude-code-mods/`
  plugins and the real, currently-shipping `andriitk/cc-unibrow` repo the
  article itself plugs.

## One precise reading worth flagging

§5.2 of the real spec names exactly two non-fatal exceptions: an unknown
top-level field, and `extensions` itself being non-object. §8.1
separately requires every *value* inside an object-shaped `extensions`
field to itself be an object. That requirement isn't one of §5.2's named
exceptions, so — read literally — a non-object value for one extension
namespace is a **fatal** schema violation, even though the field as a
whole being non-object is not. Implemented and tested as its own
distinct case (`test_non_object_extension_value_is_fatal`) rather than
assumed either way.

## Tests

23/23 pass, including:

- The real spec's own worked examples (`hello-plugin`, `reports-plugin`,
  the full-manifest example, the §8.2 extension-directory example)
  reproduced verbatim as fixtures — all confirmed to conform cleanly,
  proving this doesn't just reject everything.
- §5.5's own listed valid/invalid plugin names, taken directly from the
  spec text, not invented.
- The real, unmodified `andriitk/cc-unibrow` `.claude-plugin/plugin.json`
  committed as a fixture (`tests/fixtures/cc-unibrow-real/`) — confirmed
  missing `$schema` and the root-level manifest the spec requires.
- This project's own real `/builds/claude-code-mods/` plugins, audited
  **in place** (not copied into a fixture) — a second, independent real-
  world source confirming the exact same non-portable-layout finding.
- Every §6 missing-vs-wrong-kind distinction (missing `skills/`/`mcp.json`
  is fine; `skills` resolving to a file, or `mcp.json` to a directory,
  invalidates only that component; malformed `mcp.json` JSON is a
  warning, not fatal).

## Deliberately not built

A fix or PR against either external repo — read-only clone access only.
A checker for the 1.1.0 working draft's proposed portable-hooks
addition — it's an unpublished, unstable draft, and building against it
now risks mismatching whatever 1.1.0 actually finalizes to.
