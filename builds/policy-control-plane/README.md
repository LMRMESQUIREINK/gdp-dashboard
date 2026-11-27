# policy-control-plane

A real, working implementation of the policy-evaluation and
payload-hash-bound approval model from an uploaded article, "Building an
Enterprise AI Control Plane for Agentic AI" (ACP) — applied to this
project's own already-proven tools, not a toy example. Full critical
analysis, including an uploaded three-part multi-tenant LLM architecture
series whose capacity-planning arithmetic was independently recomputed
and checks out, in
`/notes/ai-control-plane-and-multitenant-llm-analysis.md`.

## What's built, matching the article's own design

- **Three governance effects, not two** (`policy/model.py`'s `Effect`
  enum): `ALLOW`, `DENY`, `REQUIRES_APPROVAL` as a first-class third
  state, matching the article's own point that human approval should be
  "configuration, rather than a special-case branch hidden inside
  orchestration code."
- **The article's exact deterministic resolution rules**
  (`policy/evaluator.py`): disabled policies discarded → the
  highest-priority applicable policy wins → ties resolve by effect
  precedence `DENY > REQUIRES_APPROVAL > ALLOW` → no applicable policy
  defaults to `DENY`.
- **Parameter-level governance on the same operation**
  (`demo_policies.py`): the article's own example is
  `Billing Agent → Telco Billing MCP → createRefund → amount > 1000 →
  REQUIRES_APPROVAL → Finance`. This project's version is
  `trading-jarvis → prop-firm-mcp-server → prop_firm_size_check →
  contracts > 5 → REQUIRES_APPROVAL → Risk Desk` — same tool name, same
  operation, different governance outcome depending on the argument,
  via priority ordering between two policies on the identical selector.
- **The agent never reaches the real tool directly**
  (`governed_call.py`): `fn` (the real tool) is only ever invoked on
  `ALLOW` or on a successfully-verified resume. Proven with a call
  counter in `test_policy.py`, not just by checking the returned status
  string.
- **Payload-hash-bound approvals** (`policy/approval_store.py`): the
  one property the article names that this project's own prior HITL
  work (`/builds/agent-checkpoint-layer/`, built last round) didn't have
  — an approval is bound via canonical-JSON + SHA-256 to the *exact*
  payload it was requested for, and `verify_and_consume()` re-checks that
  hash before ever calling the real tool on resume.

## The security property this is really about

Without payload binding, a believable bug: a human approves "size check
for 10 contracts," and because the approval is only keyed by an ID, a
caller resumes it with *different* arguments — say, 999 contracts — and
that executes under the same approval. `test_policy.py` reproduces this
exact attack and shows it's rejected:

```
=== the single most important security property: payload-hash tamper detection ===
  [PASS] a resume with a TAMPERED payload (different contracts) was rejected
  [PASS] the real tool was NEVER called for the tampered payload
  [PASS] resuming with the ACTUAL approved payload (after the tamper attempt) succeeds

=== an approval can't be replayed twice ===
  [PASS] replaying an already-consumed approval is rejected
```

## A deliberate security choice worth stating explicitly

The article never says how its "condition tree evaluates to true" is
actually implemented. `policy/conditions.py` is deliberately **not**
`eval()` against a string expression — a policy condition is data a
non-engineer might plausibly edit, and `eval()` against anything short of
fully-trusted code is a real vulnerability, not a hypothetical one.
Conditions here are plain nested dicts (`{"field": "amount", "op": ">",
"value": 1000}`, `{"all": [...]}`, `{"any": [...]}`, `{"not": ...}`) —
JSON-serializable, safe to store, and interpreted by a fixed set of six
operators, never executed as code.

## Verification — real tests, no mocks for the enforcement boundary

```bash
python3 test_policy.py
```

25 checks, all passing on the real run: condition-tree evaluation
(comparisons, AND/OR/NOT, nesting, fail-closed on a missing field),
policy precedence and the default-DENY fallback, `governed_call`'s DENY
and REQUIRES_APPROVAL paths proven (via a call counter) to never reach
the real tool, the ALLOW path's result checked against a direct
`evaluate_size()` call, the full approve→resume cycle executing for
real, the payload-hash tamper rejection above, replay rejection, and
`canonical_hash`'s key-order independence.

## Using it

```python
from policy.evaluator import PolicyEvaluator
from policy.approval_store import ApprovalStore
from governed_call import governed_call, resume_governed_call
from demo_policies import POLICIES, size_check_tool

evaluator = PolicyEvaluator(POLICIES)
approvals = ApprovalStore("approvals.db")

result = governed_call(
    evaluator, approvals, agent="trading-jarvis", tool="prop-firm-mcp-server",
    operation="prop_firm_size_check", payload={"tier": "50K", "symbol": "ES", "contracts": 10},
    fn=size_check_tool,
)
# result["status"] == "pending_approval" — 10 > 5, so a human needs to look.

approvals.decide(result["approval_id"], approved=True, approver="risk.desk@firm.example")

final = resume_governed_call(
    approvals, result["approval_id"],
    payload={"tier": "50K", "symbol": "ES", "contracts": 10},  # must match exactly
    fn=size_check_tool,
)
# final["status"] == "executed"
```

## Extended: ask_human() as a distinct, model-initiated primitive

Added from a second source — "The Harness Is the Product: How Agents Are
Actually Built in 2026" (Andrii Tkachuk) — see
`/notes/harness-is-the-product-analysis.md`. The article draws a sharp
architectural line this build didn't have until this round: "Model-
initiated clarification and policy-enforced approval look similar on
screen, but they belong to different layers." `governed_call`'s
REQUIRES_APPROVAL path is the policy-enforced half — the model never
calls it, the harness intercepts unconditionally. `policy/clarification.py`
is the other half: `ask_human()`/`answer()`, a primitive the model itself
chooses to call when it's missing information it needs — "which of two
connected task systems to use," whether "the payments service" means
staging or production — with its own separate SQLite-backed store, not a
second status bolted onto `approvals`.

`test_clarification.py` (16 checks, all passing) proves the two stay
genuinely separate rather than just asserting it: answering a pending
clarification leaves an unrelated pending approval's status completely
untouched, and deciding an approval leaves an unrelated clarification's
status untouched too — then runs the article's own worked example
end to end (resolving "staging" vs. "production" via `ask_human()`
changes what `governed_call` later sees and decides), and proves the
one invariant that actually matters for security: a production restart
is gated by `REQUIRES_APPROVAL` identically whether or not the model
ever called `ask_human()` first — approval enforcement is a property of
the payload and the policy, never of whether a clarification round-trip
happened.

```bash
python3 test_clarification.py
```

## What's cut, and why

This implements the ACP article's policy-evaluation and approval-binding
model — the part that's concrete, implementable, and immediately usable
against real tools this project already has. Not built: the FastAPI/
PostgreSQL/React/Entra-ID enterprise portal, Redis runtime cache, agent
registry UI, or role-based admin console the article describes — none of
that is needed to prove the governance *model* works, and building a
web portal nobody asked for around a single local Python project would
be padding, not substance. The companion multi-tenant LLM series'
subject matter (Kubernetes namespaces, regional deployment, Kafka
usage-event streaming, real tenant traffic) describes infrastructure
this project doesn't have and isn't the right next build here either —
its contribution to this round was the independently-verified capacity-
planning arithmetic in the analysis note, not a second build.

From the Harness-article round: of the 12 harness components that
article names, most already have a real build elsewhere in this project
(credited, not re-built, in `/notes/harness-is-the-product-analysis.md`)
— `ask_human()` above was the one genuine gap. Not built: the operation-
catalog progressive-disclosure layer (`list_capabilities`/
`search_operations`/`load_operation`), a sandboxed code-execution
runtime, model routing, and channel-agnostic surface adapters — each
real and credited as a plausible future gap, but materially bigger scope
than this round's one addition, and none of them has the same direct,
narrow "this project clearly doesn't have this specific thing" signal
`ask_human()` did.

## Extended: VIAB/DBO verified-identity token-exchange chain

Added from the OKF/production-AI-systems article bundle — "The Verified
Identity Agent Bridge" (Natarajan Selvaraj), one of five articles
analyzed in `/notes/okf-rag-agentic-bundle-analysis.md`. That round's
named "within a week" next move. `policy/identity_bridge.py`:

- **`SimulatedIdP`** — a stand-in for a real enterprise IdP (no live one
  reachable from this sandbox, same standing restriction as every build
  here needing a live external service), implementing only the two
  steps VIAB actually depends on: a user directory (the IdP's own
  source of truth) and PKCE-bound authorization-code issuance/exchange.
- **`IdentityBridge` (VIAB)** — verifies a human via delegated OAuth
  Authorization Code + PKCE, resolves canonical identity from the IdP's
  directory, and `assert_downstream()` returns an explicit per-request
  context dict — never a token of any kind. For when the downstream
  surface (the article's own example: a low-code agent platform) cannot
  validate a user-audience token directly.
- **`DelegatedBoundaryToken` (DBO)** — the article's own named companion
  pattern, for the opposite case: downstream CAN validate a token
  directly, so the bridge mints one scoped to that specific audience
  (a minimal HMAC-signed claim set, not a full JWT library, since no
  live IdP signing keys exist here to fetch) and forwards that instead.

Kept as two structurally distinct mechanisms rather than one function
with a flag — `test_identity_bridge.py`'s `TestViabAndDboStayDistinct`
proves it directly: VIAB's context dict never contains a token-shaped
string, DBO never returns a bare context dict. 15/15 checks pass,
including single-use authorization codes, PKCE-verifier mismatch
rejection, expired-code rejection, token audience/expiry/signature
rejection, and a wrong-signing-key check (a downstream service that was
never given the real shared key can't validate a token forged for it).

## Extended: the Blueprint article's stage/confirm/commit write-tier pattern

Added from the same bundle's "A Blueprint for Production Agentic AI
Systems in the Enterprise" — credited in the analysis note as "the
single most load-bearing mechanism across all five articles." That
round's named "2-3 week" next move, extending this build rather than
starting a new one. `policy/write_tiers.py`:

- **Three risk tiers** (`RiskTier`): `immediate` (commits on request, no
  staging), `confirm` (staged, then committed only against the exact
  pinned payload), `step_up` (confirm, plus a FRESHLY re-verified
  identity at commit time).
- **`classify_tier()`** reuses `policy/conditions.py`'s safe nested-dict
  evaluator — the same non-`eval()` discipline as `PolicyEvaluator` —
  and fails toward MORE friction, not less: an unmatched write defaults
  to `step_up`, never `immediate`.
- **`guard_write()`** — the article's own named enforcement function.
  **`WriteStager`** is the "backend-signed context pinning exactly what
  will be written," reusing `approval_store.py`'s `canonical_hash()`
  directly so the two modules' notion of "the same payload" can never
  drift apart.
- **The `step_up` tie-in to VIAB**: committing a `step_up` write requires
  a `VerifiedIdentity` from `identity_bridge.py` verified within a
  configurable freshness window (default 60s) — a stale identity, even a
  genuinely-verified one from earlier in the session, is refused. This
  operationalizes "step_up" literally (re-authentication), not as a
  bigger rubber stamp on an identity the agent already had lying around.

How this differs from `governed_call`'s existing `REQUIRES_APPROVAL`,
deliberately: that answers "is a human allowed to approve this at all,"
gated by an org-written policy; this answers "how much friction does
*committing* it need," a classification independent of whether a
separate approval workflow exists. `demo_write_tiers.py` reuses
`demo_policies.py`'s real `size_check_tool()` unmodified, with tier
rules set at the same 1/5-contract thresholds — so a large position-size
write is both routed to Risk Desk (via the existing policy) AND requires
step-up re-authentication to commit (via the new tier).

16/16 checks pass in `test_write_tiers.py`, including the full real
stage→commit cycle executing `size_check_tool()` for real, a tampered
commit payload rejected with the real tool proven (via a call counter)
never reached, double-commit rejection, and the step_up path exercised
three ways: no identity at all (refused), a stale identity (refused),
and a genuinely fresh one from a real `IdentityBridge.verify()` call
(succeeds). **One real test-fixture bug found on the first run, not in
the module itself**: the test payloads used `"TPT50K"` as the tier
string, but `PropFirmAccount`'s real valid tiers are `"25K"/"50K"/
"75K"/"100K"/"150K"` — caught immediately by the first real run against
the real class, fixed in the test fixtures (the module needed no
change). `python3 -m unittest discover -p "test_*.py"` across the whole
build: 31/31 (the two newer unittest-based suites; the two earlier
custom-runner suites, `test_policy.py`/`test_clarification.py`, still
pass cleanly when run directly — confirmed no regression from this
round's changes, since neither existing module was touched).

## Extended: okf-navigator's check_module_impact, adapted (not forced)

`/builds/okf-navigator/`'s OKF-format module-dependency-impact mechanism
is wired in a third time (first `/builds/trading-jarvis/`, then
`/builds/interface-lift-toolkit/`), but this build has no LLM
tool-dispatch loop to register it as a tool against — it's a plain
governance library, not an agent harness. Stated plainly rather than
forced into a pattern that doesn't fit: `okf_impact.py`'s
`check_module_impact(module, max_hops=2)` is a directly-importable
Python function plus a small CLI, the same way every other function in
this build is exposed.

```bash
python3 okf_impact.py policy/evaluator.py
python3 okf_impact.py policy/write_tiers.py --max-hops 1
```

`okf_knowledge/` is a new, 13-concept bundle (not shared with
trading-jarvis's or interface-lift-toolkit's), built by grepping this
build's own real imports first. Two real, honestly-reported findings
from that grep: `policy/__init__.py` re-exports most of this package but
is itself never imported anywhere in this repo (confirmed zero hits for
a bare `import policy`/`from policy import`) — AND, separately,
`policy/__init__.py`'s own re-export list predates three later modules
(`policy/clarification.py`, `policy/identity_bridge.py`,
`policy/write_tiers.py`), none of which it imports at all; and
`policy/clarification.py` is itself a real, shipped, test-covered module
with zero real consumers among this build's own shipped modules. Neither
is a bug — nothing in this repo relies on the package-level surface
either way — both are stated because the real import graph makes them
directly checkable rather than assumed. `test_okf_impact.py` (20/20)
proves the real hop structure, including a genuine 2-hop-only chain
(`policy/approval_store.py` → `policy/write_tiers.py` →
`demo_write_tiers.py`) confirmed by hand against the real grep, and a
permanent regression test for the exact negated-reference-markdown-link
bug class found and fixed in interface-lift-toolkit's bundle last round
— this bundle's own negative statements were written as plain code text
from the start, specifically to avoid it, and the test confirms they
didn't recreate it.

Also ran `/builds/okf-navigator/drift_check.py` (a new tool, built the
same round, generalizing a real before/after staleness demonstration
into a reusable AST-based re-grep against any `okf_knowledge/` bundle)
against this build's own bundle: **zero drift found on the very first
real run** — the only one of the four bundles checked that round to
come back clean immediately, confirming this one was built completely
the first time. Trading-jarvis's and interface-lift-toolkit's bundles
each had real, previously-undocumented drift the same tool found and
fixed — see `/builds/okf-navigator/README.md` for what.

## What's cut from this round's three articles, and why

Checked against all five bundle articles' mechanisms before building:
`SecurityTrimmedIndex`'s ACL-filtered-query pattern (the bundle's third
named next move) got its own standalone build,
`/builds/security-trimmed-index/`, rather than extending this one — it's
a search-ranking boundary, not a governance-decision boundary, and
forcing it in here would blur what each module is actually for. Not
built in `write_tiers.py`: the article's own full HR/workplace/
procurement/travel multi-domain leave-request example — the
generalizable tier mechanism it depends on is what's proven here,
against this project's own real prop-firm domain, rather than
re-narrating a four-department example this sandbox has no systems-of-
record for.

## Extended: Mandate-revalidation-on-resume (`policy/mandate_store.py`)

Closes a gap this build's own README previously left open, named
directly by `/builds/dsh-thread-mandate/`'s own write-up (that build's
standalone reimplementation of `deepseek-ai/dsh-superagent-prototype`'s
domain model): this package already had `ApprovalStore`'s single-use
approvals (pending → approved → consumed, spent the moment it's used),
but no concept of a grant that outlives one execution and gets
revalidated only at resume.

`MandateStore` carries the three governing rules over directly rather
than re-deriving them: ending a unit of work (`end_unit_of_work()`)
never revokes its Mandate and never consults the evaluator at all; only
an explicit `withdraw()`, or a failed revalidation **at an actual
resume**, revokes it; and revalidation reuses this package's own real
`PolicyEvaluator` against the Mandate's original `(agent, tool,
operation, context)` selector, so "the current policy set no longer
grants this" means exactly the same ALLOW/DENY/REQUIRES_APPROVAL
resolution every other call in this build already goes through — not a
second, disconnected rule.

Proven against this build's own real `demo_policies.py`/
`size_check_tool()` (the same classes every other interface in this
project calls, not a toy example): a Mandate granted for a 5-contract
size check under the baseline policy (ALLOW up to 5 contracts) ends its
unit of work cleanly, then is correctly revoked on resume once a
stricter policy set (REQUIRES_APPROVAL above 3 contracts) is introduced
— the exact same context, re-evaluated fresh at resume time, not
re-checked the moment the stricter policy appeared. 18/18 tests pass on
the real run (`test_mandate_store.py`), including a real SQLite close/
reopen round trip proving the revoked/withdrawn status is durable, not
in-memory only, and a direct proof that withdrawal and policy-driven
revocation are structurally distinct (resuming a withdrawn Mandate
fails on the withdrawal check even when the evaluator would still say
ALLOW). No bug found in this module's own first draft, stated plainly
rather than manufactured.

The new module's own `okf_knowledge/policy-mandate-store.md` concept
file was added to this build's existing OKF bundle, and
`/builds/okf-navigator/drift_check.py` was re-run afterward — it
correctly flagged the real, undocumented new consumer edges onto
`policy/evaluator.py` and `policy/model.py` before the bundle was
updated, then came back clean once they were added, the same real
drift-detection discipline that bundle's own build round established.
