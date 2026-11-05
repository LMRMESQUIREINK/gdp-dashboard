"""
governed_call / resume_governed_call — the enforcement boundary, matching
the ACP article's central principle: "Agents reason. ACP governs. Runtime
executes." The caller never reaches the real tool (`fn`) directly; it
goes through governed_call first, and the decision — not the caller —
decides whether `fn` ever runs.

Three outcomes, matching the article's three-state model exactly:
  DENY               -> fn is never called. Nothing executes.
  REQUIRES_APPROVAL  -> fn is never called. An approval is created,
                        bound to the exact payload, and its ID returned.
  ALLOW              -> fn is called now, for real.
"""
from __future__ import annotations

from typing import Any, Callable

from policy.approval_store import ApprovalStore
from policy.evaluator import PolicyEvaluator
from policy.model import Effect


def governed_call(evaluator: PolicyEvaluator, approvals: ApprovalStore, *,
                   agent: str, tool: str, operation: str, payload: dict[str, Any],
                   fn: Callable[..., dict]) -> dict[str, Any]:
    decision = evaluator.evaluate(agent=agent, tool=tool, operation=operation, context=payload)

    if decision.effect == Effect.DENY:
        return {"status": "denied", "reason": decision.reason, "policy_id": decision.policy_id}

    if decision.effect == Effect.REQUIRES_APPROVAL:
        approval_id = approvals.create(
            agent=agent, tool=tool, operation=operation, payload=payload,
            policy_id=decision.policy_id, policy_version=decision.policy_version,
        )
        return {
            "status": "pending_approval", "approval_id": approval_id,
            "reason": decision.reason, "policy_id": decision.policy_id,
            "approval_role": decision.approval_role,
        }

    # ALLOW
    result = fn(**payload)
    return {"status": "executed", "policy_id": decision.policy_id, "result": result}


def resume_governed_call(approvals: ApprovalStore, approval_id: str, *,
                          payload: dict[str, Any], fn: Callable[..., dict]) -> dict[str, Any]:
    """Re-verifies the approval — status AND payload hash — before
    calling `fn`, matching the article's step 6: 'verifies the approval,
    trace, identity, operation, payload hash and policy revision before
    execution.' Raises if the approval isn't valid for this exact
    payload; `fn` is never reached in that case."""
    approvals.verify_and_consume(approval_id, payload)
    result = fn(**payload)
    return {"status": "executed", "approval_id": approval_id, "result": result}
