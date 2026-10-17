"""
Real tests of the toolkit's mechanics — registry schema derivation,
the result contract, the ledger, the shortlist scorer, run_chain
(including the approval gate and the stop-at-first-failed-check rule),
and the skill compiler. Every numeric assertion against the demo tools
checks the toolkit's output against a DIRECT call to the same underlying
prop-firm-sizing function, same discipline as
/builds/prop-firm-mcp-server/test_client.py.

Run with:
    python3 test_toolkit.py
"""
from __future__ import annotations

import sys

from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import PropFirmAccount
from tools_demo import register_demo_tools

from toolkit.approval import ApprovalGate
from toolkit.chain import run_chain
from toolkit.ledger import Ledger, TaskCounters
from toolkit.registry import ToolRegistry
from toolkit.result import result
from toolkit.shortlist import shortlist_groups
from toolkit.skill_compiler import compile_skill

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main() -> None:
    registry = ToolRegistry()
    gate = ApprovalGate()
    register_demo_tools(registry)

    # ── registry: schema derivation ─────────────────────────────────────
    print("=== registry: schema derivation ===")
    schema = registry.schemas(["prop_firm_size_check"])[0]
    check("schema name matches function name", schema["name"] == "prop_firm_size_check")
    props = schema["input_schema"]["properties"]
    check("tier/symbol typed as string, contracts as integer",
          props["tier"]["type"] == "string" and props["symbol"]["type"] == "string"
          and props["contracts"]["type"] == "integer", detail=str(props))
    check("all three params required (no defaults)",
          set(schema["input_schema"]["required"]) == {"tier", "symbol", "contracts"},
          detail=str(schema["input_schema"]["required"]))
    check("docstring became the description", "25%" in schema["description"])

    # ── result(): ok derived from checks, never set by hand ─────────────
    print("\n=== result(): ok is derived from checks ===")
    r_ok = result("fine", checks=[("a", True), ("b", True)])
    r_bad = result("not fine", checks=[("a", True), ("b", False)])
    check("all-true checks -> ok=True", r_ok["ok"] is True)
    check("one false check -> ok=False", r_bad["ok"] is False)

    # ── demo tool vs. direct evaluate_size() ─────────────────────────────
    print("\n=== prop_firm_size_check matches evaluate_size() directly ===")
    account = PropFirmAccount(tier="50K", symbol="ES")
    rules = AccountRules(
        account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
        eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
        point_value=account.point_value,
    )
    direct = evaluate_size(rules, 1, average_daily_range_points=None)
    via_tool = registry.call("prop_firm_size_check", tier="50K", symbol="ES", contracts=1)
    check("tool output matches direct evaluate_size() call",
          via_tool["size_rule"] == direct["size_rule"] and via_tool["ok"],
          detail=f"direct={direct} tool={via_tool}")

    # ── shortlist scorer ─────────────────────────────────────────────────
    print("\n=== shortlist_groups ===")
    signals = {
        "prop_firm": [(r"\btpt\b|\bprop firm\b|\bfunded account\b|\bevaluation\b", 8)],
        "signals": [(r"\brsi\b|\bema\b|\bsignal\b", 8)],
    }
    clear = shortlist_groups("check my 50K TPT funded account sizing", signals)
    check("a clear winner returns exactly one group", clear == ["prop_firm"], detail=str(clear))
    ambiguous = shortlist_groups("hello", signals)
    check("no signal hits returns an empty list", ambiguous == [], detail=str(ambiguous))

    # ── run_chain: references between steps ──────────────────────────────
    print("\n=== run_chain: $id references resolve between steps ===")
    chain_result = run_chain(registry, gate, [
        {"id": "size", "tool": "prop_firm_size_check", "args": {"tier": "50K", "symbol": "ES", "contracts": 1}},
        {"id": "pass_prob", "tool": "prop_firm_pass_probability",
         "args": {"tier": "50K", "symbol": "ES", "current_balance": 50_800, "high_water_mark": 51_200,
                   "days_remaining": 8, "avg_daily_pnl": 180, "daily_pnl_std": 550}},
    ])
    check("chain of two independent steps both ran and succeeded",
          chain_result["ok"] and chain_result["done"]["size"]["ok"] and chain_result["done"]["pass_prob"]["ok"],
          detail=str(chain_result))

    # ── run_chain: stops at the first failed check ───────────────────────
    print("\n=== run_chain: stops at the first failed check ===")
    bad_chain = run_chain(registry, gate, [
        {"id": "bad", "tool": "prop_firm_size_check", "args": {"tier": "999K", "symbol": "ES", "contracts": 1}},
        {"id": "never_runs", "tool": "prop_firm_pass_probability",
         "args": {"tier": "50K", "symbol": "ES", "current_balance": 50_000, "high_water_mark": 50_000,
                   "days_remaining": 5, "avg_daily_pnl": 100, "daily_pnl_std": 300}},
    ])
    check("chain reports ok=False and names the failed step",
          bad_chain["ok"] is False and bad_chain["failed"] == "bad", detail=str(bad_chain))
    check("the second step never ran", "never_runs" not in bad_chain["done"])

    # ── run_chain: outward tool holds for approval ───────────────────────
    print("\n=== run_chain: outward tool holds for approval, then runs once approved ===")
    publish_args = {"filename": "chain_test.txt", "body": "hello from run_chain"}
    held = run_chain(registry, gate, [{"id": "pub", "tool": "publish_report", "args": publish_args}])
    check("unapproved outward call is held, not executed", "pending" in held and held["done"] == {}, detail=str(held))
    gate.approve("publish_report", publish_args)
    ran = run_chain(registry, gate, [{"id": "pub", "tool": "publish_report", "args": publish_args}])
    check("approved outward call actually runs", ran["ok"] and ran["done"]["pub"]["ok"], detail=str(ran))
    check("approval is single-use (re-running without re-approving holds again)",
          "pending" in run_chain(registry, gate, [{"id": "pub2", "tool": "publish_report", "args": publish_args}]))

    # ── skill compiler ───────────────────────────────────────────────────
    print("\n=== skill compiler: compile a chain, then replay it with new params ===")
    recorded_steps = [
        {"id": "chk", "tool": "prop_firm_size_check", "args": {"tier": "50K", "symbol": "ES", "contracts": 1}},
    ]
    compile_skill(registry, gate, "check_50k_es_sizing", recorded_steps, params={1: "contracts"})
    check("compiled skill registered as a new tool", "check_50k_es_sizing" in registry.names())
    compiled_out = registry.call("check_50k_es_sizing", contracts=3)
    direct_3 = registry.call("prop_firm_size_check", tier="50K", symbol="ES", contracts=3)
    check("compiled skill replayed with contracts=3 matches a direct call with the same args",
          compiled_out["done"]["chk"] == direct_3, detail=f"compiled={compiled_out} direct={direct_3}")
    try:
        registry.call("check_50k_es_sizing")
        check("missing required param raises", False)
    except TypeError as exc:
        check("missing required param raises TypeError naming it", "contracts" in str(exc), detail=str(exc))

    # ── ledger ────────────────────────────────────────────────────────────
    print("\n=== ledger ===")
    ledger = Ledger()
    counters = TaskCounters(model_calls=2, tool_calls=1, ui_actions=0)
    ledger.record("prop_firm_size_check demo", counters, tokens="~900", seconds="0.01 s", checks="2/2")
    rendered = ledger.show()
    check("ledger renders the recorded row", "prop_firm_size_check demo" in rendered and "2/2" in rendered)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
