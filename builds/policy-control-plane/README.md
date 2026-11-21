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
