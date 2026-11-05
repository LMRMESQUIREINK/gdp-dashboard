"""
Real tests of the condition evaluator, the policy evaluator's
precedence/tie-break rules, and governed_call's enforcement boundary —
most importantly, that DENY and REQUIRES_APPROVAL really prevent the
real tool from ever being called (proven with a call counter, not just
by checking the returned status string), and that payload-hash binding
really rejects a resume whose payload doesn't match what was approved.

Run with:
    python3 test_policy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from demo_policies import POLICIES, size_check_tool
from governed_call import governed_call, resume_governed_call
from policy.approval_store import ApprovalStore, canonical_hash
from policy.conditions import evaluate as evaluate_condition
from policy.evaluator import PolicyEvaluator
from policy.model import Effect, Policy
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import PropFirmAccount

FAILURES: list[str] = []
DB = "test_approvals.db"


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main() -> None:
    Path(DB).unlink(missing_ok=True)
    for suffix in ("-wal", "-shm"):
        Path(DB + suffix).unlink(missing_ok=True)

    print("=== condition evaluator: comparisons, AND/OR/NOT, nested ===")
    check("simple > comparison", evaluate_condition({"field": "amount", "op": ">", "value": 1000}, {"amount": 1500}))
    check("simple > comparison, false case",
          not evaluate_condition({"field": "amount", "op": ">", "value": 1000}, {"amount": 500}))
    check("'all' (AND) requires every clause",
          not evaluate_condition({"all": [{"field": "a", "op": "==", "value": 1}, {"field": "b", "op": "==", "value": 2}]},
                                  {"a": 1, "b": 99}))
    check("'any' (OR) needs only one clause",
          evaluate_condition({"any": [{"field": "a", "op": "==", "value": 1}, {"field": "b", "op": "==", "value": 2}]},
                              {"a": 99, "b": 2}))
    check("'not' inverts",
          not evaluate_condition({"not": {"field": "a", "op": "==", "value": 1}}, {"a": 1}))
    check("nested all/any", evaluate_condition(
        {"all": [{"field": "tier", "op": "==", "value": "50K"},
                 {"any": [{"field": "contracts", "op": ">", "value": 5}, {"field": "urgent", "op": "==", "value": True}]}]},
        {"tier": "50K", "contracts": 1, "urgent": True}))
    check("a condition field missing from context fails closed, doesn't crash",
          not evaluate_condition({"field": "nonexistent", "op": ">", "value": 1}, {}))
    check("None condition always matches", evaluate_condition(None, {}))

    print("\n=== policy evaluator: priority wins, then effect precedence on ties, then default DENY ===")
    evaluator = PolicyEvaluator(POLICIES)
    low = evaluator.evaluate(agent="trading-jarvis", tool="prop-firm-mcp-server",
                              operation="prop_firm_size_check", context={"contracts": 2})
    check("2 contracts (below threshold) -> ALLOW via the base policy", low.effect == Effect.ALLOW, detail=str(low))
    high = evaluator.evaluate(agent="trading-jarvis", tool="prop-firm-mcp-server",
                               operation="prop_firm_size_check", context={"contracts": 10})
    check("10 contracts (above threshold) -> REQUIRES_APPROVAL, the higher-priority policy wins",
          high.effect == Effect.REQUIRES_APPROVAL and high.policy_id == "require-approval-large-size", detail=str(high))
    unknown = evaluator.evaluate(agent="rogue-agent", tool="prop-firm-mcp-server",
                                  operation="prop_firm_size_check", context={"contracts": 1})
    check("unrecognized agent, no matching policy -> default DENY",
          unknown.effect == Effect.DENY and unknown.policy_id is None, detail=str(unknown))

    tie_policies = [
        Policy(id="p-allow", name="allow", effect=Effect.ALLOW, priority=5),
        Policy(id="p-deny", name="deny", effect=Effect.DENY, priority=5),
    ]
    tie_eval = PolicyEvaluator(tie_policies)
    tie_decision = tie_eval.evaluate(agent="x", tool="y", operation="z", context={})
    check("same-priority tie between ALLOW and DENY resolves to DENY (effect precedence)",
          tie_decision.effect == Effect.DENY, detail=str(tie_decision))

    print("\n=== governed_call: DENY and REQUIRES_APPROVAL never call the real tool ===")
    approvals = ApprovalStore(DB)
    call_count = {"n": 0}

    def counting_tool(**kwargs):
        call_count["n"] += 1
        return size_check_tool(**kwargs)

    denied = governed_call(evaluator, approvals, agent="rogue-agent", tool="prop-firm-mcp-server",
                            operation="prop_firm_size_check",
                            payload={"tier": "50K", "symbol": "ES", "contracts": 1}, fn=counting_tool)
    check("DENY response returned", denied["status"] == "denied", detail=str(denied))
    check("the real tool was NEVER called on a DENY", call_count["n"] == 0, detail=f"call_count={call_count['n']}")

    pending = governed_call(evaluator, approvals, agent="trading-jarvis", tool="prop-firm-mcp-server",
                             operation="prop_firm_size_check",
                             payload={"tier": "50K", "symbol": "ES", "contracts": 10}, fn=counting_tool)
    check("REQUIRES_APPROVAL response returned with an approval_id",
          pending["status"] == "pending_approval" and pending.get("approval_id"), detail=str(pending))
    check("the real tool was STILL never called while pending", call_count["n"] == 0, detail=f"call_count={call_count['n']}")
    check("approval carries the Risk Desk role from the policy", pending["approval_role"] == "Risk Desk")

    print("\n=== governed_call: ALLOW really executes and matches a direct call ===")
    allowed = governed_call(evaluator, approvals, agent="trading-jarvis", tool="prop-firm-mcp-server",
                             operation="prop_firm_size_check",
                             payload={"tier": "50K", "symbol": "ES", "contracts": 2}, fn=counting_tool)
    check("ALLOW executed and the tool WAS called exactly once", call_count["n"] == 1, detail=f"call_count={call_count['n']}")
    account = PropFirmAccount(tier="50K", symbol="ES")
    rules = AccountRules(account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
                          eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
                          point_value=account.point_value)
    direct = evaluate_size(rules, 2, average_daily_range_points=None)
    check("governed ALLOW result matches a direct evaluate_size() call",
          allowed["result"]["size_rule"] == direct["size_rule"],
          detail=f"governed={allowed['result']['size_rule']} direct={direct['size_rule']}")

    print("\n=== resume_governed_call: approve, then resume with the SAME payload executes for real ===")
    approval_id = pending["approval_id"]
    approvals.decide(approval_id, approved=True, approver="risk.desk@firm.example")
    resumed = resume_governed_call(approvals, approval_id,
                                    payload={"tier": "50K", "symbol": "ES", "contracts": 10}, fn=counting_tool)
    check("resume executed", resumed["status"] == "executed", detail=str(resumed))
    check("the real tool was called for the resume (now 2 total calls)",
          call_count["n"] == 2, detail=f"call_count={call_count['n']}")
    direct10 = evaluate_size(rules, 10, average_daily_range_points=None)
    check("resumed result matches a direct evaluate_size(10) call",
          resumed["result"]["size_rule"] == direct10["size_rule"],
          detail=f"resumed={resumed['result']['size_rule']} direct={direct10['size_rule']}")

    print("\n=== the single most important security property: payload-hash tamper detection ===")
    pending2 = governed_call(evaluator, approvals, agent="trading-jarvis", tool="prop-firm-mcp-server",
                              operation="prop_firm_size_check",
                              payload={"tier": "50K", "symbol": "ES", "contracts": 20}, fn=counting_tool)
    approvals.decide(pending2["approval_id"], approved=True, approver="risk.desk@firm.example")
    calls_before_tamper = call_count["n"]
    try:
        resume_governed_call(approvals, pending2["approval_id"],
                              payload={"tier": "50K", "symbol": "ES", "contracts": 999},  # DIFFERENT from what was approved
                              fn=counting_tool)
        check("a resume with a TAMPERED payload (different contracts) was rejected", False,
              detail="it executed instead of raising")
    except ValueError as exc:
        check("a resume with a TAMPERED payload (different contracts) was rejected",
              "payload hash mismatch" in str(exc), detail=str(exc))
    check("the real tool was NEVER called for the tampered payload",
          call_count["n"] == calls_before_tamper, detail=f"call_count={call_count['n']}")

    legit_resume = resume_governed_call(approvals, pending2["approval_id"],
                                         payload={"tier": "50K", "symbol": "ES", "contracts": 20},  # the ACTUAL approved payload
                                         fn=counting_tool)
    check("resuming with the ACTUAL approved payload (after the tamper attempt) succeeds",
          legit_resume["status"] == "executed", detail=str(legit_resume))

    print("\n=== an approval can't be replayed twice ===")
    try:
        resume_governed_call(approvals, pending2["approval_id"],
                              payload={"tier": "50K", "symbol": "ES", "contracts": 20}, fn=counting_tool)
        check("replaying an already-consumed approval is rejected", False, detail="it executed again")
    except ValueError as exc:
        check("replaying an already-consumed approval is rejected", "already consumed" in str(exc), detail=str(exc))

    print("\n=== canonical_hash is stable regardless of key order ===")
    h1 = canonical_hash({"tier": "50K", "symbol": "ES", "contracts": 2})
    h2 = canonical_hash({"contracts": 2, "tier": "50K", "symbol": "ES"})
    check("same payload, different key order, same hash", h1 == h2, detail=f"{h1} vs {h2}")
    h3 = canonical_hash({"tier": "50K", "symbol": "ES", "contracts": 3})
    check("a genuinely different payload hashes differently", h1 != h3)

    approvals.close()
    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
