"""
Real tests of ask_human()/answer_clarification(), and — the part that
actually matters — that it stays architecturally separate from
governed_call's policy-enforced approval gate, matching "The Harness Is
the Product" article's claim that the two "look similar on screen, but
... belong to different layers."

Run with:
    python3 test_clarification.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from governed_call import governed_call
from policy.approval_store import ApprovalStore
from policy.clarification import ClarificationStore
from policy.evaluator import PolicyEvaluator
from policy.model import Effect, Policy

FAILURES: list[str] = []
APPROVALS_DB = "test_approvals_clarify.db"
CLARIFY_DB = "test_clarifications.db"


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


DEPLOY_POLICIES = [
    Policy(
        id="allow-deploy-baseline",
        name="Allow service restarts by default",
        effect=Effect.ALLOW,
        priority=10,
        agent="deploy-agent",
        tool="deploy-service",
        operation="restart_service",
        condition=None,
    ),
    Policy(
        id="require-approval-production-restart",
        name="Require approval for a production restart",
        effect=Effect.REQUIRES_APPROVAL,
        priority=50,
        agent="deploy-agent",
        tool="deploy-service",
        operation="restart_service",
        condition={"field": "environment", "op": "==", "value": "production"},
        approval_role="SRE On-Call",
    ),
]


def restart_service_tool(service: str, environment: str) -> dict:
    return {"service": service, "environment": environment, "restarted": True}


def main() -> None:
    for db in (APPROVALS_DB, CLARIFY_DB):
        Path(db).unlink(missing_ok=True)
        for suffix in ("-wal", "-shm"):
            Path(db + suffix).unlink(missing_ok=True)

    clarifications = ClarificationStore(CLARIFY_DB)
    approvals = ApprovalStore(APPROVALS_DB)
    evaluator = PolicyEvaluator(DEPLOY_POLICIES)

    print("=== ask_human: basic ask/answer round trip ===")
    cid = clarifications.ask(
        agent="deploy-agent",
        question="Does 'the payments service' mean staging or production?",
        options=["staging", "production"],
        context={"service": "payments-api"},
    )
    pending = clarifications.get(cid)
    check("a fresh clarification is pending", pending.status == "pending")
    check("the question text round-trips", pending.question.startswith("Does 'the payments service'"))
    check("the offered options round-trip", pending.options == ["staging", "production"])

    answered = clarifications.answer(cid, "production")
    check("answering marks it answered", answered.status == "answered")
    check("the answer round-trips", answered.answer == "production")

    print("\n=== ask_human: validation ===")
    try:
        clarifications.answer(cid, "doesn't matter")
        check("answering an already-answered clarification is rejected", False, detail="it succeeded again")
    except ValueError as exc:
        check("answering an already-answered clarification is rejected", "already" in str(exc), detail=str(exc))

    cid2 = clarifications.ask(agent="deploy-agent", question="Which region?", options=["us-east", "eu-west"])
    try:
        clarifications.answer(cid2, "ap-south")  # not an offered option
        check("an answer outside the offered options is rejected", False, detail="it succeeded")
    except ValueError as exc:
        check("an answer outside the offered options is rejected", "is not one of" in str(exc), detail=str(exc))

    print("\n=== ask_human and governed_call's approval gate never cross-contaminate ===")
    # Create a pending approval for a production restart, and a pending
    # clarification about the SAME service, at the same time.
    call_count = {"n": 0}

    def counting_tool(**kwargs) -> dict:
        call_count["n"] += 1
        return restart_service_tool(**kwargs)

    pending_approval = governed_call(
        evaluator, approvals, agent="deploy-agent", tool="deploy-service", operation="restart_service",
        payload={"service": "payments-api", "environment": "production"}, fn=counting_tool,
    )
    check("a production restart is gated as pending_approval, not executed",
          pending_approval["status"] == "pending_approval" and call_count["n"] == 0, detail=str(pending_approval))

    cid3 = clarifications.ask(agent="deploy-agent", question="Is this restart urgent?", options=["yes", "no"])

    # Answering the UNRELATED clarification must not touch the approval at all.
    clarifications.answer(cid3, "no")
    approval_record = approvals.get(pending_approval["approval_id"])
    check("answering a clarification leaves the pending approval's status untouched",
          approval_record.status == "pending", detail=f"status={approval_record.status}")
    check("the real tool still was never called just because an unrelated clarification got answered",
          call_count["n"] == 0)

    # And approving the approval must not touch the clarification's status.
    approvals.decide(pending_approval["approval_id"], approved=True, approver="SRE On-Call")
    clarification_record = clarifications.get(cid3)
    check("deciding an approval leaves an unrelated clarification's status untouched",
          clarification_record.status == "answered" and clarification_record.answer == "no")

    print("\n=== the worked scenario: resolving ambiguity changes what policy later sees ===")
    # "whether 'the payments service' means staging or production" -- ask_human
    # resolves this BEFORE the agent can even construct a sensible payload for
    # governed_call, since the policy condition is keyed on `environment`.
    cid4 = clarifications.ask(
        agent="deploy-agent",
        question="Does 'the payments service' mean staging or production?",
        options=["staging", "production"],
    )
    clarifications.answer(cid4, "staging")
    resolved_env = clarifications.get(cid4).answer

    staging_call_count = {"n": 0}

    def staging_counting_tool(**kwargs) -> dict:
        staging_call_count["n"] += 1
        return restart_service_tool(**kwargs)

    staging_result = governed_call(
        evaluator, approvals, agent="deploy-agent", tool="deploy-service", operation="restart_service",
        payload={"service": "payments-api", "environment": resolved_env}, fn=staging_counting_tool,
    )
    check("resolving to 'staging' via ask_human lets the restart execute immediately (ALLOW)",
          staging_result["status"] == "executed" and staging_call_count["n"] == 1, detail=str(staging_result))

    print("\n=== approval enforcement never depends on the model having asked for clarification at all ===")
    # The model skips ask_human entirely and just hands governed_call a
    # production payload directly. The approval gate must fire anyway --
    # it is a property of the PAYLOAD and the POLICY, never of whether a
    # clarification round-trip happened first.
    skip_call_count = {"n": 0}

    def skip_counting_tool(**kwargs) -> dict:
        skip_call_count["n"] += 1
        return restart_service_tool(**kwargs)

    skip_result = governed_call(
        evaluator, approvals, agent="deploy-agent", tool="deploy-service", operation="restart_service",
        payload={"service": "checkout-api", "environment": "production"}, fn=skip_counting_tool,
    )
    check("a production restart is STILL gated even with zero ask_human calls beforehand",
          skip_result["status"] == "pending_approval" and skip_call_count["n"] == 0, detail=str(skip_result))

    clarifications.close()
    approvals.close()
    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
