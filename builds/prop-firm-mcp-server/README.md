# ♛ prop-firm-mcp-server

A real MCP server — built with the actual official `mcp` Python SDK over
stdio transport, not a hand-rolled approximation of the protocol —
exposing the already-proven `/builds/prop-firm-sizing/` toolkit
(`PropFirmAccount`, `AccountRules`, `SessionState`, `PassSimulator`) as
four MCP tools: `prop_firm_size_check`, `prop_firm_session_report`,
`prop_firm_pass_probability`, `prop_firm_compare_sizes`. Same math, same
classes every other interface in this project already uses — this is a
fifth interface on the same underlying code (CLI → `run_strategy.py`,
Claude tool-use → `jarvis_orchestrator.py`, web → `streamlit_app.py`'s
dashboard, now MCP), not a reimplementation.

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
| Dual stdio/HTTP transport, stateless sessions | **stdio only** | No remote deployment, no load balancer, no horizontal scaling need. |
| OAuth 2.1 + JWT + policy engine | **Cut** | No real users, no auth server. Faking one would be security theater, not security — see `.well-known` style discovery is also skipped for the same reason. |
| Redis human-approval gate for destructive tools | **Cut** | All four tools are read-only calculations; nothing here is destructive. |
| Outbound HTTP allowlist | **Cut** | This server makes zero outbound HTTP calls. |
| **Structured Error Framework (SERF)** | **Built**, adapted | See `errors.py`'s module docstring — the installed SDK's wire format differs from the article's, verified by actually running a probe server before writing this. |
| Three-tier tool hierarchy (atomic/composed/workflow) | **Atomic tier only** | Four independent, already-narrow calculations with no natural fan-out between them — padding in a composed/workflow tier that wraps nothing would be hollow. |
| Circuit breakers, retry+backoff, ATBA | **Cut** | `PropFirmAccount`/`PassSimulator` are pure local computation — no upstream network call exists to protect against. |
| Redis token-bucket rate limiting via Lua | **Built**, in-process | See `ratelimit.py`'s module docstring for the exact trigger condition under which this stops being sufficient. |
| Two-tier cache + stampede lock | **Cut** | `PassSimulator` runs are seeded (deterministic) and cheap enough (sub-second) that caching buys little, and there's one caller, so there's no stampede to prevent. |
| OTel traces, Prometheus metrics | **Cut** | No tracing/metrics backend running in this sandbox or needed for a local tool. |
| **Structured audit log** | **Built**, scoped down | See `audit.py` — no `trace_id`/`delegator`/`tenant` fields (none apply here). |
| Four-agent LLM copilot (Planner/Retriever/Synthesizer/Critic) | **Cut** | Wrapping a deterministic Monte Carlo calculator in a 4-agent LLM orchestrator would be solving a problem that doesn't exist — there's no judgment call here, just arithmetic. |

## Install & run

```bash
pip install -r requirements.txt
python3 -m prop_firm_mcp_server.server
```

Point an MCP host (Claude Desktop's config, or any MCP client) at that
command over stdio. An `audit.jsonl` file is created next to this README
on first tool call.

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
