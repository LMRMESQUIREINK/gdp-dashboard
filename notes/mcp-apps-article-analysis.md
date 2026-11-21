# Deep analysis: "Stop Returning JSON. Start Shipping UI with MCP Apps"

Source: a pasted Medium article by Andrii Tkachuk (same author as the
immediately preceding "Agent Plugins" round, same cc-unibrow plug at
the end) — MCP Apps, the real SEP-1865 extension letting MCP servers
ship interactive `ui://` resources alongside tools. No accompanying
instruction, so per this project's convention the article itself is
the instruction to run the deep-analysis-and-ship loop.

## What was checked, and how

Like last round's Agent Plugins article, this one names a primary,
version-controlled source rather than only secondary coverage — so this
round cloned both real repos directly: `modelcontextprotocol/
modelcontextprotocol` (the core spec, blog posts, SEPs) and
`modelcontextprotocol/ext-apps` (the MCP Apps extension itself,
including its full normative specification file,
`specification/2026-01-26/apps.mdx`). Read the actual spec text and the
actual dated blog posts rather than trusting the article's paraphrase.

## What checks out exactly — a clean verification round

Every specific, checkable claim in this article held up against the
primary source:

- **SEP-1865, Nov 21 2025**: the real blog post
  (`blog/content/posts/2025-11-21-mcp-apps.md`) names the exact same
  authorship the article implies — MCP Core Maintainers plus the
  MCP-UI creators (Ido Salomon, Liad Yosef) plus named engineers from
  OpenAI and Anthropic — and the real PR link (`modelcontextprotocol/
  modelcontextprotocol/pull/1865`) matches.
- **Jan 26 2026, "first official MCP extension"**: confirmed verbatim
  ("this is the first official MCP extension, and it's ready for
  production"), with ChatGPT, Claude, Goose, and Visual Studio Code all
  named as having shipped support — exact match to the article's list,
  down to Goose's and VS Code's own quoted representatives.
- **July 28 2026 Release Candidate**: the real post confirms "a formal
  extensions framework, with Tasks joining other extensions, such as
  MCP Apps and Enterprise Managed Authorization (EMA)" — matching the
  article's claim that MCP Apps was "explicitly listed among the
  official extensions."
- **Sep 11 2026 AWS Bedrock AgentCore example**: confirmed real via web
  search (the exact URL the article cites resolves, dated Sep 11 2026
  per a news aggregator), with the architecture matching the article's
  description (AgentCore Gateway → AgentCore Runtime hosting the MCP
  server → Lambda/DynamoDB behind it).
- **The `_meta.ui` mechanism**: `ui://` URI scheme, `text/html;
  profile=mcp-app` MIME type, `_meta.ui.resourceUri` linking a tool to
  its UI resource, and `_meta.ui.visibility` (`["model","app"]` default,
  narrowable to `["app"]`) — all confirmed character-for-character
  against the real spec's "Resource Discovery" section, including a
  precision the article doesn't mention: a flat, deprecated
  `_meta["ui/resourceUri"]` format exists and is explicitly marked for
  removal before GA, so a server reading an older convention would
  silently miss the link.
- The two host-side MUST rules the article describes in prose
  ("the host must not include [an app-only tool] in the tool list,"
  "it can only ever be called from inside the running App view") match
  the spec's own two explicit MUST statements exactly — and the real
  spec is slightly more precise than the article's paraphrase: it
  states a *second*, separate MUST ("Host MUST reject `tools/call`
  requests from apps for tools that don't include `'app'` in
  visibility"), which the article's prose doesn't call out as its own
  distinct enforcement point.

## A real, independently-confirmed technical finding the article doesn't flag

Before writing any code, probed the real official `mcp` Python SDK
(2.3.0, the same SDK `/builds/prop-firm-mcp-server/` already uses)
directly: registering two tools with `meta={"ui": {...}}` and a
resource with `mime_type="text/html;profile=mcp-app"` serializes
exactly as the spec describes (`_meta.ui.resourceUri`/`visibility` both
round-trip correctly through `list_tools()`). But the SDK's own
`list_tools()` and `call_tool()` enforce **neither** of the spec's two
host-side MUST rules — `list_tools()` still returns an `["app"]`-only
tool, and `call_tool()` will happily execute it regardless of who's
calling. That's correct per the spec (both rules are explicitly host
requirements, not server requirements), but it means a server built
with today's reference Python SDK gets **zero** enforcement for free —
a real, concrete integration detail this article's otherwise-accurate
description doesn't surface, confirmed directly rather than assumed.

## A real cross-article connection, visible only reading two rounds together

Harald Kirschner, Principal Product Manager for VS Code at Microsoft,
is quoted in this article's own primary source (the Jan 26 2026 MCP
Apps announcement) — and is separately listed as a named Core
Maintainer of the Agent Plugins 1.0.0 spec analyzed in the immediately
preceding round of this project (`/notes/
agent-plugins-article-analysis.md`). Neither article names the other
or states this connection; it's visible only by having read both real
primary sources back to back — the same single person represents
Microsoft/VS Code's position in both of this project's two most recent
MCP-ecosystem standardization rounds.

## Built

Checked `/builds/` first: this project already has one real, tested,
official-SDK-backed MCP server — `/builds/prop-firm-mcp-server/` — with
zero UI resources of any kind. That's exactly the gap this article's
mechanism fills, and extending already-proven, already-tested real
infrastructure is this project's established convention over starting
a new build from scratch.

**Extended `/builds/prop-firm-mcp-server/`** with real MCP Apps support:

- `prop_firm_mcp_server/ui_resources.py` — a real `ui://` HTML resource
  (`ui://prop-firm-mcp-server/compare-sizes-dashboard`) for the existing
  `prop_firm_compare_sizes` tool: a small, self-contained dashboard
  implementing the spec's two-way contract in real markup/JS (receives
  the host-delivered tool result via `window.addEventListener("message",
  ...)`, calls back through the host via a `callServerTool()` helper
  rather than holding its own server connection).
- `prop_firm_compare_sizes` now carries `_meta.ui.resourceUri` pointing
  at that resource, with the default `visibility: ["model", "app"]`.
- A genuinely new tool, `prop_firm_refresh_compare_sizes`
  (`visibility: ["app"]`) — the dashboard's own Refresh button, hidden
  from the model's tool-selection context entirely per the article's
  own point about keeping UI-only interactions out of the agent's
  context, while remaining callable from inside the App view.
- `prop_firm_mcp_server/host_shim.py` — since the real SDK enforces
  neither host-side MUST rule (confirmed above), this is a minimal,
  faithful stand-in built specifically to prove both rules end-to-end
  over a real stdio connection, in the absence of any live
  MCP-Apps-compatible host (Claude.ai, ChatGPT, VS Code) in this
  sandbox: filters a raw tool list down to what a model would actually
  see, and rejects a `tools/call` attempt when the declared caller role
  isn't in the tool's visibility.

`test_mcp_apps.py`, 15/15 checks pass, including:

- The real `_meta.ui.resourceUri`/`visibility` metadata round-tripping
  correctly through the real SDK's `list_tools()`.
- The host shim correctly excluding the app-only tool from the
  model-visible list, correctly rejecting a model-attributed call to
  it, and correctly allowing an app-attributed call to the exact same
  tool — proving the rejection is about caller role, not a broken tool.
- The real `ui://` resource read via `resources/read`: exactly the
  required `text/html;profile=mcp-app` MIME type, a genuine HTML5
  document, and content that actually wires the two-way contract
  (checked for the real `addEventListener("message"...)`/
  `callServerTool` code, not just a non-empty string).
- A numeric cross-check: the app-only tool's output matches a direct
  call to the same, already-proven `run_compare_sizes()` exactly — the
  new tool is a real alias of proven logic, not a stub.
- One informational (non-pass/fail) observation stated rather than
  assumed either way: the spec permits a server to omit a
  tool-discovered UI resource from `resources/list`, and this server's
  actual current behavior (via the real SDK, unmodified) is to include
  it — checked directly rather than guessed.

Re-ran the two pre-existing test suites for this build to confirm no
regression: `test_client.py` needed one real, expected update (its tool
count assertion from "all four" to "all five," since a fifth tool now
genuinely exists) and passes fully afterward; `test_http_client.py`
skips cleanly on its own pre-existing redis-not-installed path,
unrelated to this round's changes.

## Deliberately not built

The HOST's half of the contract — a sandboxed iframe, CSP construction
from declared domains, real `postMessage` delivery of tool results into
a rendered view. No MCP-Apps-compatible host exists in this sandbox
(Claude.ai, ChatGPT, Goose, VS Code), and building a toy host simulator
beyond the minimal `host_shim.py` visibility-enforcement stand-in would
risk mimicking a security-relevant component (CSP/sandbox enforcement)
badly enough to give false confidence — stated plainly rather than
faked. CSP/permission declarations (`ui.csp.connectDomains`, camera/
microphone/geolocation/clipboard permissions) — this server's one
dashboard needs none of them (no network calls, no device access), so
there's nothing here to exercise that machinery against honestly.
