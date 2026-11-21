# Deep analysis: "Stop Shipping Individual MCP Servers. Start Shipping Agent Plugins"

Source: a pasted Medium article by Andrii Tkachuk, arguing that MCP
(connectivity) and Agent Skills (procedural knowledge) are converging
into a new distribution layer — Agent Plugins, formalized as an open,
vendor-neutral spec in August 2026. No accompanying instruction, so per
this project's convention the article itself is the instruction to run
the deep-analysis-and-ship loop.

## What was checked, and how

Unlike most sources this project analyzes, the article's central claim
has a primary source with its own version-controlled governance
document, not just secondary press coverage — so this round went
straight to it: cloned `agentplugins/agent-plugins-spec` directly and
read `spec/1.0.0.md`, `MAINTAINERS.md`, and `GOVERNANCE.md` in full,
rather than trusting the article's paraphrase. Also cloned the real
`andriitk/cc-unibrow` repo the article plugs at the end, and checked this
project's own previously-shipped `/builds/claude-code-mods/` plugins
directly, since the article makes a specific claim about Claude Code's
plugin format that this project could verify first-hand against real,
already-tested material of its own.

## What checks out exactly

- MCP (Nov 2024) and Agent Skills (2025, later published as an open,
  portable format) — both accurately described, consistent with this
  project's own extensive prior history building and testing both.
- The real spec repo is genuinely active (80 merged PRs, most recent
  Nov 13, 2026) with a real, current `spec/1.0.0.md` matching the
  article's description precisely: the portable v1.0.0 core really
  does define exactly two fixed component types — `skills/` (subdirectories
  containing `SKILL.md`) and `mcp.json` — confirmed by reading §6
  (Component discovery) directly, not inferred from the article.
- The extension-namespace mechanism — a reverse-domain key under
  `extensions` in `plugin.json`, optionally paired with a top-level
  directory of the same name (`com.vendor.client/`) — matches §8 of the
  real spec exactly, including the article's own `com.vendor.client/hooks/`
  example shape.
- The Core Maintainer roster the article implies (Amazon, Cursor,
  Microsoft, OpenAI, Vercel) matches the real, current `MAINTAINERS.md`
  exactly: Clare Liguori (Amazon), Roshan Sadanani (Cursor), Harald
  Kirschner (Microsoft), Gav Verma (OpenAI), Jonathan Hefner (Vercel,
  Lead Core Maintainer).
- Launch client list (GitHub shipping support in VS Code/Copilot
  CLI/Copilot app Aug 12, ChatGPT/Codex/Cursor/Kiro following) is
  corroborated across multiple independent secondary sources found via
  web search (devclass, Visual Studio Magazine, GitHub's own changelog,
  aiweekly.co).
- The cc-unibrow plug at the end of the article is accurate and
  verified real: a genuinely active repo (release 0.2.8, two days before
  this analysis), a real Swift Package with real tests, and the exact
  install command (`/plugin install cc-unibrow --marketplace
  andriitk/cc-unibrow`) matching the real README verbatim.

## The real finding: "Google joining as a core maintainer" doesn't match the spec's own current governance file

The article states the spec was "initiated by Vercel and developed
together with Amazon, Anysphere (Cursor's maker), Microsoft, and OpenAI,
**with Google joining shortly after as a core maintainer**." Checked
directly against the primary source rather than repeated: the real,
current `MAINTAINERS.md` — fetched twice independently, once via this
session's own git clone and once via a separate live GitHub page fetch —
lists exactly five Core Maintainers (Amazon, Cursor, Microsoft, OpenAI,
Vercel). **Google does not appear anywhere in it.**

A web search for independent corroboration found the claim isn't
invented from nothing — several secondary press sources from around the
August 2026 launch do report Google "joining" the effort, and one
summary states Google's own developer blog frames its support as a TSC
publication by the original five organizations' maintainers, not a claim
of Core Maintainer status for itself. That's a real, precise distinction
the article's wording collapses: "joining shortly after" and "joining
*as a core maintainer*" are different claims, and the second one doesn't
match the spec's own authoritative governance document as it stands
today (Nov 18, 2026). This could reflect a real change since August
(Google's seat added then later not retained in the roster file) or
simply secondary coverage overstating Google's formal role and the
article following that coverage — this analysis can't fully resolve
which from here, but states the primary-source fact precisely rather
than repeating the secondary framing.

Also noted without treating it as an error: one secondary source
(Visual Studio Magazine) reportedly gives July 24, 2026 as the spec's
publication date rather than the Aug 6 date most sources (and the
article) use — a minor date discrepancy across secondary coverage, not
something this analysis can resolve from the spec repo's own files
alone (its earliest commit isn't visible in a shallow clone).

## A claim independently confirmed first-hand, not just taken on the article's word

The article states Claude's own plugin format "wasn't among the launch
clients for the Agent Plugins 1.0 spec in August — it still uses its own
layout." This was checked directly, twice, against real material rather
than trusted: (1) this project's own three previously-shipped, previously-
tested Claude Code plugins in `/builds/claude-code-mods/` each put
`plugin.json` inside a `.claude-plugin/` subdirectory, with no `$schema`
field and no root-level `plugin.json` at all; (2) the real, currently-
shipping `andriitk/cc-unibrow` repo's own Claude Code plugin does the
exact same thing. Both independently confirm the article's claim is
accurate — the real spec requires `plugin.json` at the plugin root
(§5.1) and a specific `$schema` value (§5.2), and Claude Code's real
format does neither.

One thing the article doesn't mention: the real spec repo's README
states a 1.1.0 **working draft** already exists, adding "portable
hooks" — directly relevant to the article's own point that hooks are
currently one of the client-specific mechanisms that aren't portable.
Not a flaw in the article (it's specifically about the published 1.0.0),
but worth flagging as the most likely place this exact gap narrows next.

## Built

Checked `/builds/` first: `skill-md-validator` checks SKILL.md
frontmatter/structure (recently extended with Sigstore signature
verification and pack-level checks); `agent-md-validator` checks
`.claude/agents/*.md` subagent frontmatter; neither validates a
`plugin.json`/`mcp.json` package manifest against the actual Agent
Plugins 1.0.0 schema, its fixed-vs-fatal distinction, or its component-
discovery rules. A genuinely new, well-specified gap.

**`/builds/agent-plugin-conformance/`** — a real, dependency-free Python
conformance checker implementing the spec exactly as read from the
primary document: the closed top-level manifest schema (§5.2), the
required `$schema`/`name` fields and the name character-set rules
(§5.3–§5.5), the author object's closed field set, the extensions
object/value shape (§8.1), the two fixed component locations and their
missing-vs-wrong-kind distinction (§6), and extension-directory
correspondence (§8.2) — plus the real, twice-confirmed detection that a
plugin using Claude Code's own `.claude-plugin/plugin.json` layout isn't
Agent-Plugins-1.0.0-portable.

One precise, deliberately-reasoned reading worth flagging: §5.2 states
only two specific exceptions are non-fatal (an unknown top-level field,
or `extensions` itself being non-object) — "any schema violation other
than" those is fatal. §8.1 separately requires every *value* inside an
object-shaped `extensions` field to itself be an object. Since that
requirement isn't one of §5.2's two named exceptions, a non-object value
for one extension namespace is fatal under the spec's own letter, even
though the field as a whole being non-object is not. Implemented and
tested as its own distinct case rather than assumed either way.

23/23 tests pass, including:

- The real spec's own worked examples (`hello-plugin`, `reports-plugin`,
  the full-manifest example, the §8.2 extension-directory example),
  reproduced verbatim from `spec/1.0.0.md` and confirmed to conform
  cleanly — proving the checker doesn't just reject everything.
- §5.5's own listed valid (`my-plugin`, `acme.tools`, `lint3r`, `a`) and
  invalid (`My-Plugin`, `-start`, `has--double`, `too.many..dots`) plugin
  names, taken directly from the spec text.
- The real, unmodified `andriitk/cc-unibrow` plugin manifest, committed
  as a fixture, confirmed to be missing `$schema` and the root-level
  manifest the spec requires.
- This project's own real `/builds/claude-code-mods/` plugins, audited
  **in place** (not copied) — all three confirmed non-portable by the
  same two findings, a second independent real-world source for the
  identical result.

## Deliberately not built

A fix or PR against either external repo — read-only clone access only,
same limit as every other external-repo build in this project. A
checker for the 1.1.0 working draft's proposed portable-hooks addition —
it's explicitly a draft, not a published spec, and building against an
unpublished, unstable draft risks shipping something that doesn't match
whatever 1.1.0 actually finalizes to.
