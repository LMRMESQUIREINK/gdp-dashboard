# Deep analysis: a bare multi-article PDF bundle on OKF and production agentic AI

Source: a bare PDF upload, no accompanying instruction —
`r_Google_s_New_OKF_Could_Change_How_We_Build_RAG_Systems_for_AI_Agents________mm.pdf`
(sha256 `61b9ba6f36a2f43588615247478c6862a1b4ad780605362e1f2bde697942ba0`,
64 pages, 213,528 bytes, `CreationDate` 2026-11-26).

## Measured first, before reading for meaning

`pdftotext -layout` extraction: 15,933 words total. Reading past the
first article's own "Final Thoughts" section (rather than stopping there)
showed this is **not one article** — it's a Reddit/Medium "print to PDF"
capture of **five distinct articles**, four of them by one author,
Natarajan Selvaraj (confirmed real via web search, published on
Medium/Towards AI), forming one coherent, cross-referencing
production-AI-systems pattern series:

1. "Google's New Open Knowledge Format (OKF) Could Change How We Build
   RAG Systems for AI Agents" (the title article)
2. "A Blueprint for Production Agentic AI Systems in the Enterprise"
3. "A Practical Pattern to Implement Secure Enterprise AI Search"
   (Security-Trimmed Index / STI)
4. "The Unified RAG Evaluation Schema" (URES)
5. "The Verified Identity Agent Bridge" (VIAB)

**A real structural PDF-conversion artifact, not a content fabrication**:
article 4 (URES) appears **twice** in the PDF, byte-for-byte identical
(confirmed via direct text comparison of both ranges) — a duplicate
full-text embed, consistent with how a print-to-PDF capture of a
multi-tab or multi-link Reddit/Medium page can pull the same linked
article in twice. Noted plainly as a conversion quirk, not an error to
"fix" or a sign of fabricated content.

## Article 1: Google's Open Knowledge Format (OKF)

**Confirmed real, and unusually precisely accurate.** Cloned
`GoogleCloudPlatform/knowledge-catalog` (Apache 2.0) directly and read
the real `okf/SPEC.md` (v0.2) in full. Every specific technical claim in
the article matched the real spec text verbatim or near-verbatim:

- §5.1 provenance fields (`generated: { by, at }`, `verified: [{ by,
  at }, ...]`)
- §5.3's exact three-tier trust model (unverified / machine-confirmed /
  human-reviewed), including the spec's own explicit statement that
  trust tiers are advisory, never access control
- §5.5's `stale_after` as an absolute instant, not a relative TTL
- §6.1's two link forms (absolute bundle-relative, recommended; ordinary
  relative) and its explicit tolerance for broken links ("not-yet-written
  knowledge")
- §10's real, named "Attested Computation" concept type — matching the
  article's own claim about sanctioned, checkable calculations exactly
- The `index.md` progressive-disclosure convention, confirmed in both the
  spec text and in real sample bundles

**One precision note, not an error**: the article's citation of
`GoogleCloudPlatform/knowledge-catalog`'s `okf/` path was accurate at the
time it and this clone were made — the real repo's own README now states
that path is a "frozen snapshot, no longer maintained," with current work
continuing at the separate `GoogleCloudPlatform/open-knowledge-format`
repo. A dated-but-accurate-at-the-time finding, the same category as
several earlier rounds' "the repo moved since the source was written"
notes (`bytedance/deer-flow`'s star-count drift, REA's growth curve).

This is one of the most rigorously self-verifying sources this project
has analyzed to date — essentially every checkable technical claim held
up exactly against primary source text, not paraphrase.

## Article 2: A Blueprint for Production Agentic AI Systems in the Enterprise

A 13-section component-by-component reference architecture: channel/
identity/assistant API → input guardrails → PII redaction → orchestrator
→ domain agents → authorization (a three-credential token-exchange
chain: Assistant API token, MCP server token, system-of-record token) →
domain MCP servers/systems of record → model layer (sensitivity-then-task
routing, token budgets) → session store (conversation history,
inter-agent shared state, long-term memory, PII vault — each with a
different lifetime) → output guardrails/redaction → observability →
evaluation/batch testing → resilience/human handoff.

The key mechanism: a **stage/confirm/commit write-tier pattern**, with a
backend-signed context pinning exactly what will be written
(`immediate`/`confirm`/`step_up` risk tiers), enforced outside the model
by a `guard_write()` function — not a prompt instruction. Illustrated with
a real worked example: an employee's compound leave request routed
through HR/workplace/procurement/travel domains.

This pattern is directly adjacent to, but distinct from, work already in
this project: `/builds/policy-control-plane/`'s `REQUIRES_APPROVAL` gate
and payload-hash binding cover a similar "don't let the model commit a
risky action unilaterally" goal, and `/builds/agent-checkpoint-layer/`
covers durable pause/resume state — but neither implements this
article's specific three-tier risk classification with a
backend-signed-context mechanism. A real candidate next move, not built
this round (see below).

MCP specification version "2026-07-28" is cited and confirmed real and
current via web search (the official GA release,
`blog.modelcontextprotocol.io/posts/2026-07-28/`).

## Article 3: Security-Trimmed Index (STI)

Normalizes heterogeneous sources into one search index (an Azure AI
Search worked example) with a per-document ACL field (`allowedGroupIds`)
populated at ingest time. The key, correctly-reasoned mechanism: access
control is enforced by injecting the caller's identity as a security
filter **inside the query itself** — not as a post-filter on returned
results — so ranking, counting, and faceting all operate correctly over
only the authorized subset. (A post-filter approach would compute
facets/counts over the full unfiltered set and then discard results,
giving a caller statistically leaky information about documents they
can't actually see — the article doesn't spell this failure mode out
explicitly, but the architecture it describes correctly avoids it.)

Not built this round (see below) — a genuinely new, testable mechanism,
left as a candidate next move.

## Article 4: Unified RAG Evaluation Schema (URES)

A schema-first, vendor-neutral evaluation record format: input/output
JSON schemas with real example fields (`evaluationId`, `evaluationType`
across ST/MT/MT_SESSION/MT_AUTOMATION, metrics on a unified 0–1 scale,
`evaluatorMetadata`), with pluggable adapters (RAGAS, Amazon Bedrock,
custom LLM-as-judge) and an AWS S3/Athena/QuickSight persistence/
consumption path. Appears twice in the PDF, byte-identical — the
structural duplication noted above.

## Article 5: Verified Identity Agent Bridge (VIAB)

When a downstream low-code agent (the worked example: Microsoft Copilot
Studio) cannot validate a user-audience OAuth token directly, a bridge
verifies the human via a delegated OAuth Authorization Code + PKCE flow
against the enterprise IdP, resolves canonical identity from the IdP's
own source of truth (Microsoft Graph `/me`), and asserts the verified
identity downstream as explicit per-request context over an
authenticated channel — **never forwarding the user's own token**.
Distinct from the article's own named companion pattern, "Delegated
Boundary OAuth" (DBO), which forwards a token the downstream service
*can* validate directly — VIAB is specifically for when it can't. The
real MCP spec version "2026-07-28" is also cited here, matching article
2's citation exactly.

## What was built, and why

Checked `/builds/` first across all five articles' mechanisms before
building anything. The OKF article's concept-graph model was chosen as
this round's build — `/builds/okf-navigator/` — because it was both the
most rigorously self-verified source (making it the safest foundation to
build an independent reimplementation against) and had no existing
overlap anywhere in this project's `/builds/` tree, unlike the Blueprint/
STI/VIAB patterns, which each have partial adjacent coverage already
(`policy-control-plane`, `agent-checkpoint-layer`, `html-ai-sanitizer`)
that a new build would risk half-duplicating without clearly improving.

`/builds/okf-navigator/` implements OKF's real trust-tier (§5.3),
staleness (§5.5), and link-resolution (§6.1) rules exactly, plus a
bounded-depth "progressive disclosure" traversal built from the
article's own worked authentication-impact scenario. Proven against
three real, unmodified sample files copied from Google's own repo
(Apache 2.0) as well as a reconstructed version of the article's own
scenario. **Found and fixed one real bug** in the module's own first
draft (`load_bundle()` crashed on a real non-concept `.md` file with no
frontmatter) and **one real, checked finding** from the real fixtures
(OKF's real `index.md` convention carries no frontmatter at all, a
genuine property of the spec confirmed directly rather than assumed —
see the build's README for the full account). 41/41 tests pass.

## Deliberately not built this round

- **STI's ACL-filtered-query pattern** — a real, testable mechanism
  (build a toy in-process search index, confirm a caller's query results/
  facets/counts only ever reflect documents their `allowedGroupIds`
  permit) with zero existing coverage in this project. A same-day-sized
  candidate next move.
- **VIAB/DBO's three-credential token-exchange chain** — would extend
  `/builds/policy-control-plane/` naturally (a verified-identity
  assertion layer sitting in front of its existing approval gate), but is
  a larger, multi-day-sized build given the real OAuth Authorization
  Code + PKCE flow modeling involved.
- **The Blueprint's stage/confirm/commit write-tier pattern** — the
  single most load-bearing mechanism across all five articles, and the
  most directly comparable to this project's own existing governance
  builds; left as the most substantial candidate (2–3 weeks sized) rather
  than attempted as a rushed partial implementation this round.
- **Wiring `okf-navigator` into an existing tool-dispatch build** (e.g.
  `trading-jarvis` or `interface-lift-toolkit`) as a new tool category —
  a natural, concrete follow-up once the module itself is proven, matching
  this project's established pattern of standalone-mechanism-then-wire-in
  (the prop-firm tools, `agent-memory-layer` into `jarvis_orchestrator.py`).

## Addendum 1: all three suggested next-moves, done in one follow-up round

All three — same-day, within-a-week, and 2-3-week — built in the
immediate next round, not a subset.

**STI (same-day)**: `/builds/security-trimmed-index/` — a new,
standalone build (zero existing `/builds/` coverage of access-controlled
search ranking/counting/faceting). The article states the correct
architecture (filter by `allowedGroupIds` *inside* the query, before
ranking/counting/faceting) but never spells out the concrete failure
mode of getting it backwards, so `naive_post_filter_search()` makes that
failure mode real and testable against the correct `SecurityTrimmedIndex`
path, on the same documents and the same caller. Three leaks proven on
one shared fixture (a "finance" caller whose only relevant, authorized
document scores lower than two "engineering"-only documents): a
`total_count` that includes documents the caller can't see, facet
buckets drawn from documents the caller can't see, and — the sharpest
one — a genuinely **missing** result: with `top_k=2`, naive ranking
truncates to the two unauthorized documents *before* the ACL filter
runs, so the caller's one authorized match is dropped entirely, not
merely ranked lower. 12/12 tests pass; no bug found in this build's own
first draft, stated plainly.

**VIAB/DBO (within a week)**: extended `/builds/policy-control-plane/`
with `policy/identity_bridge.py` rather than starting a new build
(checked `/builds/` first — this is the same governance domain
`governed_call`/`approval_store.py` already live in). `SimulatedIdP`
stands in for a real enterprise IdP (no live one reachable here);
`IdentityBridge` implements VIAB (delegated OAuth Authorization Code +
PKCE, resolves identity from the IdP's directory, asserts it downstream
as an explicit context dict — never a token); `DelegatedBoundaryToken`
implements the article's own named companion pattern DBO (mints a token
scoped to one specific downstream audience, for when the downstream CAN
validate a token directly). Kept as two structurally distinct
mechanisms rather than one function with a flag, proven directly:
VIAB's context dict never contains a token-shaped string; DBO never
returns a bare context dict. 15/15 tests pass, including single-use
authorization-code enforcement, PKCE-mismatch rejection, and a
wrong-signing-key check.

**The Blueprint's stage/confirm/commit write-tier pattern (2-3 weeks)**:
also extended `/builds/policy-control-plane/`, with `policy/
write_tiers.py` — `immediate`/`confirm`/`step_up` risk tiers,
`classify_tier()` reusing the existing safe condition evaluator,
`guard_write()` (the article's own named function) and a `WriteStager`
reusing `approval_store.py`'s `canonical_hash()` directly. The `step_up`
tier ties directly into VIAB from the same round: committing a
`step_up` write requires a `VerifiedIdentity` re-verified within a
60-second freshness window, refusing even a genuinely-verified but
stale identity — "step_up" implemented as literal re-authentication,
not a bigger rubber stamp on whatever identity the agent's session
already had. Demonstrated against this project's own real prop-firm
domain (`demo_write_tiers.py` reuses `demo_policies.py`'s real
`size_check_tool()` unmodified) rather than the article's own
HR/workplace/procurement/travel example, which needs systems-of-record
this sandbox doesn't have. 16/16 tests pass — including a real
test-fixture bug caught on the first run (the test payloads used an
invalid tier string, `"TPT50K"`, against the real `PropFirmAccount`'s
actual valid tiers; fixed in the test, the module needed no change) —
and all 31 of this round's own new unittest-based tests plus the two
pre-existing custom-runner suites (`test_policy.py`,
`test_clarification.py`) re-run to confirm zero regression.

## Addendum 2: `okf-navigator` wired into `trading-jarvis` as a fourth tool category

Per request, after the three next-moves above. `/builds/trading-jarvis/
jarvis_orchestrator.py` gains `check_module_impact`, independent of the
existing symbol-trading/prop-firm/memory flows. `okf_navigator.py` is
copied in unmodified (same convention `memory_layer.py`/`persistence.py`
already follow there), paired with a genuinely new OKF-formatted
knowledge bundle, `okf_knowledge/` (13 concept files) — not fictional
data: describes *this build's own actual module dependency graph*,
written only after directly grepping every real `import` statement in
`trading-jarvis/` (`data_pipeline.py`, `signal_generator.py`,
`risk_manager.py`, `positions_store.py`, `swamp_intelligence.py`,
`jarvis_swamp_bridge.py`, `prop_firm_sizing.py`,
`prop_firm_position_sizing.py`, `prop_pass_simulator.py`,
`memory_layer.py`, `persistence.py`, `jarvis_memory.py`,
`jarvis_orchestrator.py`). Every concept honestly reports the
`machine-confirmed` trust tier (never `human-reviewed`) per OKF's real
§5.3 model — this session's own grep verified the graph, no human has
reviewed it, and the system prompt instructs Claude to say so plainly
if asked rather than overclaiming the stronger tier.

`jarvis_okf.py`'s `check_module_impact()` resolves either a real
filename (`"risk_manager.py"`) or the bundle's own concept-file name
and returns a plain error naming all 13 known modules on an
unrecognized one, rather than a raw `KeyError`. `test_jarvis_okf.py`
(19/19 assertions) proves the real import graph's actual hop structure,
not an assumed one: direct calls at varying `max_hops`, dispatch-through-
`_run_tool()` parity, and the full `ask_jarvis()` mocked-Anthropic
dispatch loop. **One real test-assumption bug caught and fixed on the
first run, not a module bug**: a first draft expected
`memory_layer.py`'s own real consumer `jarvis_memory.py` to be a 2-hop
relationship, but the real grep shows `jarvis_memory.py` imports
directly from *both* `memory_layer.py` and `persistence.py` — a genuine
1-hop edge — so the test's wrong assumption was corrected to match the
real graph (a second, deliberately-chosen real 2-hop case —
`persistence.py` → `jarvis_memory.py` → `jarvis_orchestrator.py` — was
added alongside it to keep the hop-boundary behavior covered). Both
pre-existing `trading-jarvis` test suites re-run (`test_jarvis_memory.py`,
16/16; `test_policy.py`/`test_clarification.py` not applicable here) to
confirm zero regression from this round's edits to
`jarvis_orchestrator.py`.
