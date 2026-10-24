# Deep analysis: "Building the 11 Layers of a Production-Grade MCP Server + Agentic System"

Source: a Medium article by Fareed Khan (pasted in full, ~107 min read), with
an accompanying public GitHub repo
(`FareedKhan-dev/production-grade-mcp-agentic-system`). Unlike the Factory.ai
white paper analyzed in `/notes/software-factory-autonomy-maturity-model-analysis.md`,
this is **not vendor marketing** — it's a genuine, deep engineering
walkthrough with real, runnable code (Docker Compose, Postgres RLS SQL,
Python modules), and it should be read with different scrutiny than a sales
funnel. That distinction matters and is stated plainly rather than applying
the same skepticism reflexively to both.

## What it actually builds

"Atlas-MCP" — a from-scratch MCP server organized around twelve production
concerns, plus a four-agent customer-support copilot (Planner → Retriever →
Synthesizer → Critic) that uses the server's tools end to end. The article
is genuinely implementation-first: real `pyproject.toml`, real Docker
Compose with twelve services and healthchecks, real Postgres Row-Level
Security SQL, real Python for every layer.

## The twelve components, in one line each

1. **Modular codebase** — one package per concern (auth/, tools/, cache/,
   reliability/, observability/, governance/), not a single `server.py`.
2. **Data persistence** — Postgres with Row-Level Security: `SET LOCAL
   app.tenant_id` + a `USING (tenant_id = current_setting(...))` policy on
   every table, so tenant isolation holds even if application code has a bug.
3. **Transport & session** — dual stdio/Streamable-HTTP transport, stateless
   HTTP sessions so any replica can serve any request.
4. **Auth, policy, governance** — OAuth 2.1 as a resource server (never
   issues tokens itself), a YAML deny-by-default policy engine, tenant
   middleware, a Redis-backed human-approval gate for destructive tools, and
   a per-tenant outbound-HTTP allowlist against exfiltration.
5. **Structured Error Framework (SERF)** — every error is `{code,
   retryable, hint, context}`, carried in MCP's JSON-RPC `error.data` field,
   so an agent can decide whether to retry instead of reading a traceback.
6. **Tool execution engine** — a three-level hierarchy (atomic → composed →
   workflow), each tool a Pydantic-validated class with its own cache key
   and scopes.
7. **Reliability** — per-tool circuit breakers (count only `retryable`
   failures, never deterministic ones), full-jitter exponential backoff,
   and Adaptive Timeout Budget Allocation (ATBA) that caps total agent-turn
   latency across a chain of tool calls.
8. **Rate limiting** — a Redis token bucket consumed atomically via a Lua
   script, keyed on `(tenant, tool)`.
9. **Caching** — L1 in-process LRU + L2 Redis, write-through, with a
   Redis-lock single-flight pattern to prevent stampedes.
10. **Observability** — OpenTelemetry traces, Prometheus metrics (explicitly
    *not* labeled by tenant/caller, to avoid a cardinality explosion), and
    structured JSON-lines audit logs that hash arguments instead of logging
    them raw.
11. **Multi-agent copilot** — four narrow-role agents, each a separate LLM
    call with its own system prompt, orchestrated with at most one
    synthesize→critique→revise loop (bounded, not open-ended).
12. *(Implicit twelfth, folded into governance in the text)* — tenant
    isolation and approval gates as their own cross-cutting concern.

## What's genuinely well-reasoned here

- **SERF is the single most reusable idea in the whole piece.** A `{code,
  retryable, hint}` error a model can act on beats a traceback every time —
  this is the same lesson this project already applies in `outage_alert.py`
  (classify outcomes into a small fixed vocabulary) and the sales-page-engine
  skill (turn a style rule into a literal grep check, not a vibe).
- **"Only count retryable failures toward the circuit breaker."** A bad SQL
  query from the agent is a `ValidationError`, not a backend health signal
  — conflating the two would let a confused agent trip a breaker that then
  blocks *every other* caller. This is a real, non-obvious correctness
  point, not boilerplate.
- **The tiered tool hierarchy (atomic/composed/workflow)** is a genuinely
  different claim from "give the agent more tools" — it's "give the agent
  the *right altitude* of tool," which is a different and better lever.
- **Tenant isolation enforced at the database layer, not just application
  code** (Postgres RLS) is real defense-in-depth: even a buggy policy
  engine can't leak rows if the database itself won't return them.
- **No back doors**: the long-term-memory module is deliberately left as a
  `NotImplementedError` rather than writing to the vector store directly,
  because a direct write would bypass the same policy/audit machinery every
  other write goes through. Shipping an honest stub instead of a quietly
  unsafe shortcut is exactly this project's own discipline.

## What doesn't check out / can't be verified from the text

- **Three specific, uncited statistics appear as established fact**:
  "87 tools is the median number reported in the April 2026 production case
  study on large enterprise MCP deployments," "a ~40% reduction in erroneous
  tool calls after introducing a tiered tool hierarchy," and "41% of
  registry MCP servers in 2026 shipped with no authentication at all." None
  of these are linked to a source, dataset, or methodology in the article
  text. They read as real research summarized from memory, but nothing here
  confirms that — treated as *illustrative*, not cited, in this analysis.
- **"Asana's MCP-powered feature leaked customer data across 1,000
  organisations"** is stated twice, specifically, about a real company,
  with no citation or link. This is a serious claim to make about a named
  company without a source. It is **not repeated as fact anywhere in this
  project's own writeup or the build below** — if it's true, it's a real
  and important cautionary tale; if it's misremembered or conflated with a
  different incident, repeating it uncritically would be irresponsible. The
  underlying architectural lesson (enforce tenancy at the database layer,
  not just app code) stands on its own regardless of whether this specific
  anecdote checks out.
- **The GitHub repo linked in the article was not cloned or verified** —
  this sandbox has `LMRMESQUIREINK/gdp-dashboard` in scope, not
  `FareedKhan-dev/production-grade-mcp-agentic-system`; nothing here claims
  to have run or inspected that actual repository, only the code as printed
  inline in the article text.

## What was built from this (see `/builds/prop-firm-mcp-server/`)

The full twelve-component stack assumes things this project doesn't have
and doesn't need: real multiple tenants, a real OAuth authorization server,
a running Postgres/Redis/OTel-collector/Jaeger/Prometheus stack, and
multiple concurrent users. Standing up Docker Compose's twelve services to
wrap a single-user calculator would be the same mistake as every
over-engineered demo this project's own CLAUDE.md warns against ("don't add
abstractions beyond what's needed").

Instead, per the same move as the Factory.ai build (extract the
generalizable pattern, skip what the scale doesn't warrant, say so
explicitly): a **real MCP server**, built with the actual official `mcp`
Python SDK (not a hand-rolled approximation of the protocol) over stdio
transport, exposing the already-proven `/builds/prop-firm-sizing/` toolkit
as four MCP tools. It implements SERF, Pydantic tool validation, structured
audit logging, and in-process rate limiting for real — and explicitly
**does not** implement OAuth, Postgres RLS, Redis, circuit breakers, OTel,
or the multi-agent layer, each with a one-line reason in the build's
README, rather than silently omitting them.
