"""Tests for policy/mandate_store.py -- the Mandate-revalidation-on-resume
mode this build was missing, per /builds/dsh-thread-mandate/'s own README
(itself read from deepseek-ai/dsh-superagent-prototype's domain model).

Run with: python3 test_mandate_store.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from demo_policies import POLICIES, size_check_tool
from policy.evaluator import PolicyEvaluator
from policy.mandate_store import MandateRevoked, MandateStore
from policy.model import Effect, Policy

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "mandates.sqlite3"
    store = MandateStore(db_path)

    baseline_evaluator = PolicyEvaluator(POLICIES)  # ALLOW up to 5 contracts

    # --- grant() creates a real, active Mandate -----------------------------
    print("=== grant() records an active Mandate with the exact selector and context ===")
    context = {"tier": "50k", "symbol": "MNQ", "contracts": 5}
    mandate_id = store.grant(
        agent="trading-jarvis", tool="prop-firm-mcp-server", operation="prop_firm_size_check",
        context=context, policy_id="allow-trading-jarvis-routine-size", policy_version=1,
    )
    record = store.get(mandate_id)
    check("the Mandate is active", record.status == "active")
    check("the Mandate's context round-trips exactly", record.context == context)
    check("the Mandate records which policy granted it", record.granted_policy_id == "allow-trading-jarvis-routine-size")

    # --- end_unit_of_work() is a pure no-op on standing ---------------------
    print("\n=== end_unit_of_work() never touches status, never consults the evaluator ===")
    store.end_unit_of_work(mandate_id)
    after_end = store.get(mandate_id)
    check("the Mandate is STILL active after its unit of work ends", after_end.status == "active")

    # --- a resume under an UNCHANGED policy set succeeds --------------------
    print("\n=== resume_unit_of_work() under an unchanged policy set succeeds ===")
    resumed = store.resume_unit_of_work(mandate_id, baseline_evaluator)
    check("resuming keeps the Mandate active", resumed.status == "active")

    # --- a Policy change while the work is still (conceptually) running
    # never gets checked until an actual resume is called -------------------
    print("\n=== A policy change is never checked except at an explicit resume ===")
    stricter_policies = [
        Policy(
            id="require-approval-small-size", name="Now requires approval above 3 contracts",
            effect=Effect.REQUIRES_APPROVAL, priority=50,
            agent="trading-jarvis", tool="prop-firm-mcp-server", operation="prop_firm_size_check",
            condition={"field": "contracts", "op": ">", "value": 3}, approval_role="Risk Desk",
        ),
        POLICIES[0],  # the original baseline ALLOW is still present too
    ]
    stricter_evaluator = PolicyEvaluator(stricter_policies)
    # Merely constructing a stricter evaluator, and not calling resume with
    # it, must leave the Mandate completely untouched -- there is no
    # background check anywhere in this module.
    untouched = store.get(mandate_id)
    check(
        "building a stricter evaluator object, without ever calling resume_unit_of_work() with it, "
        "leaves the Mandate's status exactly as it was",
        untouched.status == "active",
    )

    # --- resuming under the NOW-stricter policy set revokes the Mandate ----
    print("\n=== resume_unit_of_work() under a now-stricter policy set revokes the Mandate ===")
    raised_revoked = False
    try:
        store.resume_unit_of_work(mandate_id, stricter_evaluator)
    except MandateRevoked as exc:
        raised_revoked = True
        check(
            "the revocation reason names the real new effect (REQUIRES_APPROVAL), not a bare exception",
            "requires_approval" in str(exc).lower(),
        )
    check("resume_unit_of_work() raised MandateRevoked under the stricter policy set", raised_revoked)
    revoked_record = store.get(mandate_id)
    check("the Mandate's own stored status is now 'revoked'", revoked_record.status == "revoked")
    check("the revocation reason is persisted, not just raised and lost", bool(revoked_record.revoked_reason))

    # --- the SAME mandate, once revoked, can never resume again, even
    # back under the original permissive policy set -------------------------
    print("\n=== A revoked Mandate cannot resume again, even under the original permissive policies ===")
    raised_again = False
    try:
        store.resume_unit_of_work(mandate_id, baseline_evaluator)
    except MandateRevoked:
        raised_again = True
    check(
        "resuming the already-revoked Mandate against the ORIGINAL, still-permissive evaluator still fails -- "
        "revocation is a real, final state transition, not re-evaluated fresh every time",
        raised_again,
    )

    # --- withdraw() is unconditional and distinct from policy-driven
    # revocation --------------------------------------------------------------
    print("\n=== withdraw() revokes unconditionally, never consulting the evaluator ===")
    second_mandate_id = store.grant(
        agent="trading-jarvis", tool="prop-firm-mcp-server", operation="prop_firm_size_check",
        context={"tier": "50k", "symbol": "MNQ", "contracts": 2}, policy_id="allow-trading-jarvis-routine-size",
        policy_version=1,
    )
    store.withdraw(second_mandate_id, reason="trader asked to stop")
    withdrawn_record = store.get(second_mandate_id)
    check("withdraw() sets status to 'withdrawn'", withdrawn_record.status == "withdrawn")
    check("withdraw()'s reason is stored verbatim", withdrawn_record.revoked_reason == "trader asked to stop")

    raised_on_withdrawn_resume = False
    try:
        store.resume_unit_of_work(second_mandate_id, baseline_evaluator)
    except MandateRevoked as exc:
        raised_on_withdrawn_resume = True
        check(
            "resuming a withdrawn Mandate fails on the withdrawal check BEFORE the evaluator "
            "is even consulted -- the baseline evaluator would still say ALLOW for 2 contracts, "
            "proving the withdrawal, not a policy result, is what blocks this",
            "withdrawn" in str(exc).lower(),
        )
    check("resuming a withdrawn Mandate raises MandateRevoked", raised_on_withdrawn_resume)

    # --- end-to-end against the real prop-firm tool, matching the real
    # computation used everywhere else in this build -------------------------
    print("\n=== End-to-end: the real size_check_tool() behind a Mandate that later gets revoked ===")
    e2e_context = {"tier": "50k", "symbol": "MNQ", "contracts": 5}
    e2e_mandate = store.grant(
        agent="trading-jarvis", tool="prop-firm-mcp-server", operation="prop_firm_size_check",
        context=e2e_context, policy_id="allow-trading-jarvis-routine-size", policy_version=1,
    )
    real_result_while_valid = size_check_tool(**e2e_context)
    check(
        "the real evaluate_size() computation runs and returns a real result while the Mandate is still valid",
        isinstance(real_result_while_valid, dict) and len(real_result_while_valid) > 0,
    )
    store.end_unit_of_work(e2e_mandate)
    raised_e2e = False
    try:
        store.resume_unit_of_work(e2e_mandate, stricter_evaluator)
    except MandateRevoked:
        raised_e2e = True
    check(
        "the exact same 5-contract context that passed under the baseline policy set is correctly "
        "revoked on resume once the policy set tightened to REQUIRES_APPROVAL above 3 contracts",
        raised_e2e,
    )

    # --- a real cross-process-style persistence check: a FRESH MandateStore
    # against the same db file sees the same durable state -------------------
    print("\n=== A fresh MandateStore against the same file sees the same durable state ===")
    store.close()
    reopened = MandateStore(db_path)
    reopened_revoked = reopened.get(mandate_id)
    reopened_withdrawn = reopened.get(second_mandate_id)
    check("the revoked Mandate's status survived a store close/reopen", reopened_revoked.status == "revoked")
    check("the withdrawn Mandate's status survived a store close/reopen", reopened_withdrawn.status == "withdrawn")
    reopened.close()

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
