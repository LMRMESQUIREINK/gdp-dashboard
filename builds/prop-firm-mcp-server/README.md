# ♛ prop-firm-mcp-server

A real MCP server — built with the actual official `mcp` Python SDK, not
a hand-rolled approximation of the protocol — exposing the already-proven
`/builds/prop-firm-sizing/` toolkit (`PropFirmAccount`, `AccountRules`,
`SessionState`, `PassSimulator`) as four MCP tools: `prop_firm_size_check`,
`prop_firm_session_report`, `prop_firm_pass_probability`,
`prop_firm_compare_sizes`. Same math, same classes every other interface
in this project already uses — this is a fifth interface on the same
underlying code (CLI → `run_strategy.py`, Claude tool-use →
`jarvis_orchestrator.py`, which now cross-references this build — see its
new "ALTERNATE INTERFACE" docstring section — web → `streamlit_app.py`'s
dashboard, now MCP), not a reimplementation.

Supports both stdio (one subprocess per client — the original build) and
Streamable HTTP (one server serving multiple concurrent clients, added
this round along with Redis-backed rate limiting — see below).

Built from the pattern analysis of an uploaded Fareed Khan article,
"Building the 11 Layers of a Production-Grade MCP Server + Agentic
System" — see `/notes/production-grade-mcp-server-analysis.md` for the
full critique (what's genuinely well-reasoned in it, what's stated as fact
without a citation, and why this build deliberately implements only a
scoped-down subset).

## What's actually built vs. what the source article covers

The article's "Atlas-MCP" assumes real multiple tenants, a real OAuth
authorization server, and a running Postgres/Redis/OTel/Jaeger/Prometheus
stack. This tool is a single-user local calculator with no network calls
and no sensitive data to protect across users — standing up twelve
production services to wrap it would be the exact over-engineering this
project's own CLAUDE.md warns against ("don't add abstractions beyond
what the task requires"). So:

| Article's component | Here | Why |
|---|---|---|
| Modular codebase | **Built** (`prop_firm_mcp_server/{server,tools,errors,ratelimit,audit}.py`) | Directly transferable regardless of scale. |
| Postgres + Row-Level Security | **Cut** | No database, no tenants — this tool processes numbers the caller types in; there's nothing to isolate. |
| Dual stdio/HTTP transport, stateless sessions | **Built** — `--transport stdio\|http` | Originally cut for "no remote deployment need yet." Built this round once a real reason existed: being reachable as more than a local subprocess. `--stateless_http` itself still isn't exposed as a flag — nothing here needs cross-node session resumption, so that's left at the SDK's default rather than wired through for its own sake. |
| OAuth 2.1 + JWT + policy engine | **Cut** | No real users, no auth server. Faking one would be security theater, not security — see `.well-known` style discovery is also skipped for the same reason. Still true even over HTTP: this is bind-to-localhost-or-your-own-network reachability, not a public multi-tenant deployment — that would need real auth before anything else. |
| Redis human-approval gate for destructive tools | **Cut** | All four tools are read-only calculations; nothing here is destructive. |
| Outbound HTTP allowlist | **Cut** | This server makes zero outbound HTTP calls. |
| **Structured Error Framework (SERF)** | **Built**, adapted | See `errors.py`'s module docstring — the installed SDK's wire format differs from the article's, verified by actually running a probe server before writing this. |
| Three-tier tool hierarchy (atomic/composed/workflow) | **Atomic tier only** | Four independent, already-narrow calculations with no natural fan-out between them — padding in a composed/workflow tier that wraps nothing would be hollow. |
| Circuit breakers, retry+backoff, ATBA | **Cut** | `PropFirmAccount`/`PassSimulator` are pure local computation — no upstream network call exists to protect against. |
| Redis token-bucket rate limiting via Lua | **Built**, real Redis+Lua, auto-selected over HTTP | Originally in-process only, with the trigger condition for needing Redis stated rather than built. That condition (multiple clients, possibly multiple processes, sharing a quota) is now real — see "Transports & rate limiting" below. Falls back to in-process (with a printed reason) if Redis isn't configured or isn't reachable; stdio still defaults to in-process since it's still correct there. |
| Two-tier cache + stampede lock | **Cut** | `PassSimulator` runs are seeded (deterministic) and cheap enough (sub-second) that caching buys little, and even with multiple HTTP clients now possible, there's still no expensive shared computation worth a stampede lock. |
| OTel traces, Prometheus metrics | **Cut** | No tracing/metrics backend running in this sandbox or needed for a local tool. |
| **Structured audit log** | **Built**, scoped down | See `audit.py` — no `trace_id`/`delegator`/`tenant` fields (none apply here). |
| Four-agent LLM copilot (Planner/Retriever/Synthesizer/Critic) | **Cut** | Wrapping a deterministic Monte Carlo calculator in a 4-agent LLM orchestrator would be solving a problem that doesn't exist — there's no judgment call here, just arithmetic. |

## Install & run

```bash
pip install -r requirements.txt       # redis is optional — only needed for --transport http
python3 -m prop_firm_mcp_server.server                                    # stdio (default)
python3 -m prop_firm_mcp_server.server --transport http                   # HTTP, 127.0.0.1:8000/mcp
python3 -m prop_firm_mcp_server.server --transport http \
    --redis-url redis://localhost:6379/0                                  # HTTP + shared Redis rate limit
```

An `audit.jsonl` file is created next to this README on first tool call,
either way.

### Using it from Claude Desktop

Claude Desktop launches MCP servers over stdio itself, so point it at the
same command used above. Add this to Desktop's `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`;
Windows: `%APPDATA%\Claude\claude_desktop_config.json`), using the real
absolute path to this build on your machine:

```json
{
  "mcpServers": {
    "prop-firm": {
      "command": "python3",
      "args": ["-m", "prop_firm_mcp_server.server"],
      "cwd": "/absolute/path/to/builds/prop-firm-mcp-server"
    }
  }
}
```

Restart Desktop, and the four `prop_firm_*` tools become available in
any chat — ask something like "check sizing for 3 ES contracts on a 50K
TPT account" and Desktop will call `prop_firm_size_check` itself.

**Honestly flagged, not faked**: this sandbox is a headless cloud
container with no Desktop app and no GUI to click through, and no live
Anthropic API access either (same restriction every other build in this
project has stated) — so the config above is real and was built from
the SDK's actual stdio contract (the same one `test_client.py` drives
and passes against), but it has not been clicked through in a real
Desktop window from in here. That step needs your own machine.

## Verification — real end-to-end test, not just "it imports"

`test_client.py` spawns the server as a real subprocess and drives it
with a real `mcp.ClientSession` over actual stdio transport — the full
protocol round trip (`initialize` → `tools/list` → `tools/call`), not a
unit test that imports the tool functions directly. Every numeric
assertion compares the MCP response against the **same underlying
class/function called directly in the same script**, so a pass proves the
MCP layer is a faithful, non-lossy wrapper, not just that the server
doesn't crash. Run it yourself:

```bash
python3 test_client.py
```

Actual output from this build (full log, not excerpted):

```
=== list_tools ===
  [PASS] all four tools registered

=== prop_firm_size_check ===
  [PASS] size_check not an error
  [PASS] size_check matches direct evaluate_size() call

=== prop_firm_session_report ===
  [PASS] session_report not an error
  [PASS] session_report current_balance matches
  [PASS] session_report warning_level matches
  [PASS] session_report safe_contracts matches

=== prop_firm_pass_probability ===
  [PASS] pass_probability not an error
  [PASS] pass_probability matches direct PassSimulator run (seed=42, deterministic)
  [PASS] pass_probability matches this project's previously-verified figure (~36.7%)

=== prop_firm_compare_sizes ===
  [PASS] compare_sizes not an error
  [PASS] compare_sizes matches direct per-scenario PassSimulator runs
  [PASS] compare_sizes matches this project's previously-verified figures (1.7/27.1/49.7/70.8%)

=== SERF validation error (unknown tier) ===
  [PASS] unknown tier returns is_error=True
  [PASS] error message carries SERF code
  [PASS] error message carries retryable=false

=== rate limiting (prop_firm_compare_sizes, capacity=5) ===
  [PASS] at least one of 7 rapid calls hit the rate limit (capacity=5)
  [PASS] rate-limit error carries SERF code

============================================================
ALL CHECKS PASSED
```

Specifically proven, not just asserted:
- **Numeric fidelity**: `prop_firm_pass_probability` and
  `prop_firm_compare_sizes` reproduce this project's own
  previously-verified figures exactly (36.7% pass probability at the
  dashboard's standard inputs; 1.7%/27.1%/49.7%/70.8% across the
  1/2/3/6-contract comparison) — `PassSimulator` seeds its RNG
  (`seed=42`), so this is a deterministic exact match, not "close enough."
- **SERF actually fires and is parseable**: an unknown tier (`"999K"`)
  returns `isError=True` with a JSON payload containing
  `{"code": "unknown_tier", "retryable": false, "hint": "..."}` in the
  message text — confirmed by substring-checking the real response, not
  assumed from reading the code.
- **Rate limiting actually trips**: 7 rapid calls to
  `prop_firm_compare_sizes` (bucket capacity 5) produced real
  `rate_limited` SERF errors with a computed `retry_after_seconds`,
  not a hypothetical.

## Transports & rate limiting — HTTP + Redis, built for real this round

`server.py --transport http` serves `prop_firm_mcp_server` over Streamable
HTTP (the SDK's `run_streamable_http_async`) instead of stdio, so more than
one MCP client can talk to the same running process — the actual trigger
condition `ratelimit.py` named (back when it only had the in-process
bucket) for when a shared, Redis-backed rate limiter stops being optional.
That condition is now real, so `ratelimit.py` gained `RedisTokenBucket`: an
atomic refill+check+decrement Lua script (the same pattern the source
article uses, run server-side so concurrent callers can't race each other),
selected automatically whenever `--redis-url` (or `$REDIS_URL`) points at a
reachable Redis; `--transport stdio` keeps the in-process bucket by default
since it's still correct there (exactly one replica per client), and HTTP
mode itself falls back to in-process — with a printed reason, not silently
— if Redis isn't configured or isn't reachable.

`test_http_client.py` proves this is real shared state, not just "the HTTP
transport works": it starts the server with `--transport http --redis-url
...`, calls a tool through it with the official SDK's streamable-HTTP
client, then **drains `prop_firm_compare_sizes`'s 5-token bucket from one
client session and shows a second, brand-new session (a fresh TCP
connection) is still rate-limited** — the only way that's possible is if
the quota lives in Redis rather than in either connection's own memory.
Real output from this build, Redis actually running locally during the
test:

```bash
python3 test_http_client.py
```
```
=== Streamable HTTP: basic tool call ===
  [PASS] all four tools registered over HTTP
  [PASS] compare_sizes over HTTP not an error
  [PASS] compare_sizes over HTTP matches previously-verified figure (1.7%)

=== Redis-backed rate limit is SHARED across separate client sessions ===
  [PASS] session A could spend the full bucket of 5
  [PASS] a fresh session B is still rate-limited (bucket shared via Redis)
  [PASS] rate-limit error carries SERF code

============================================================
ALL CHECKS PASSED
```

`test_client.py` (the original stdio suite) was re-run after these changes
and still passes unmodified — the stdio path's behavior didn't change.

## A real SDK-version finding, not a guess

The source article's code targets `mcp>=1.2.0`, where a tool handler could
return an `ErrorData` object that rode in the JSON-RPC `error.data` field.
The version actually installable in this sandbox (`mcp==2.3.0`) is a
different, newer high-level API
(`mcp.server.mcpserver.MCPServer`/`.tool()`) whose `ToolError` instead
returns a normal `CallToolResult` with `isError=True` and the message as
plain text — confirmed by writing a small probe server+client and running
it before committing to this pattern in `errors.py`, rather than
transcribing the article's code against a different SDK version and
hoping it still worked.
