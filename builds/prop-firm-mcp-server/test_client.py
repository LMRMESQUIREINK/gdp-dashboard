"""
Real end-to-end test: spawns prop_firm_mcp_server as a subprocess over
real stdio transport and drives it with a real `mcp` ClientSession —
not a unit test that imports the tool functions directly. Every assertion
compares the MCP response against the SAME underlying class/function
called directly in this script, so a pass here proves the MCP layer is a
faithful, non-lossy wrapper around the already-proven prop-firm-sizing
math, not just that the server doesn't crash.

Run with:
    python3 test_client.py
"""
from __future__ import annotations

import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from prop_firm_sizing import PropFirmAccount, SessionState
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_pass_simulator import PassSimulator

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def _text(result) -> str:
    return "".join(c.text for c in result.content if hasattr(c, "text"))


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "prop_firm_mcp_server.server"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            print("=== list_tools ===")
            check("all four tools registered",
                  names == {"prop_firm_size_check", "prop_firm_session_report",
                            "prop_firm_pass_probability", "prop_firm_compare_sizes"},
                  detail=str(names))

            # ── prop_firm_size_check vs. direct evaluate_size() ─────────
            print("\n=== prop_firm_size_check ===")
            account = PropFirmAccount(tier="50K", symbol="ES")
            rules = AccountRules(
                account_equity=account.starting_balance,
                daily_loss_limit=account.daily_loss_limit,
                eod_trailing_drawdown=account.eod_trailing_dd,
                max_contracts=account.max_contracts,
                point_value=account.point_value,
            )
            direct = evaluate_size(rules, 1, average_daily_range_points=None)

            mcp_result = await session.call_tool(
                "prop_firm_size_check", {"args": {"tier": "50K", "symbol": "ES", "contracts": 1}}
            )
            via_mcp = json.loads(_text(mcp_result))
            check("size_check not an error", not mcp_result.is_error)
            check("size_check matches direct evaluate_size() call",
                  via_mcp == direct, detail=f"direct={direct} mcp={via_mcp}")

            # ── prop_firm_session_report vs. direct SessionState ────────
            print("\n=== prop_firm_session_report ===")
            state = SessionState(
                account=account, session_start_balance=50_000,
                high_water_mark=50_000, intraday_pnl=-900,
            )
            direct_report = {
                "current_balance": round(state.current_balance, 2),
                "warning_level": state.warning_level(),
                "safe_contracts": state.safe_contracts,
            }
            mcp_result = await session.call_tool(
                "prop_firm_session_report",
                {"args": {"tier": "50K", "symbol": "ES",
                          "intraday_pnl": -900, "high_water_mark": 50_000,
                          "session_start_balance": 50_000}},
            )
            via_mcp = json.loads(_text(mcp_result))
            check("session_report not an error", not mcp_result.is_error)
            check("session_report current_balance matches",
                  via_mcp["current_balance"] == direct_report["current_balance"])
            check("session_report warning_level matches",
                  via_mcp["warning_level"] == direct_report["warning_level"],
                  detail=f"mcp={via_mcp['warning_level']} direct={direct_report['warning_level']}")
            check("session_report safe_contracts matches",
                  via_mcp["safe_contracts"] == direct_report["safe_contracts"])

            # ── prop_firm_pass_probability vs. direct PassSimulator ─────
            # Same inputs as this project's own previously-verified dashboard
            # run (seed=42 inside PassSimulator makes this deterministic).
            print("\n=== prop_firm_pass_probability ===")
            sim = PassSimulator(
                account=account, current_balance=50_800, high_water_mark=51_200,
                days_remaining=8, avg_daily_pnl=180, daily_pnl_std=550,
            )
            sim.run()
            mcp_result = await session.call_tool(
                "prop_firm_pass_probability",
                {"args": {"tier": "50K", "symbol": "ES", "current_balance": 50_800,
                          "high_water_mark": 51_200, "days_remaining": 8,
                          "avg_daily_pnl": 180, "daily_pnl_std": 550}},
            )
            via_mcp = json.loads(_text(mcp_result))
            check("pass_probability not an error", not mcp_result.is_error)
            check("pass_probability matches direct PassSimulator run (seed=42, deterministic)",
                  via_mcp["pass_probability"] == round(sim.pass_probability, 4),
                  detail=f"direct={sim.pass_probability:.4f} mcp={via_mcp['pass_probability']}")
            check("pass_probability matches this project's previously-verified figure (~36.7%)",
                  abs(via_mcp["pass_probability"] - 0.367) < 0.01,
                  detail=f"got {via_mcp['pass_probability']:.1%}")

            # ── prop_firm_compare_sizes vs. direct PassSimulator loop ───
            # Same scenario rows as this project's own previously-verified
            # Compare Sizes dashboard run.
            print("\n=== prop_firm_compare_sizes ===")
            scenarios = [
                {"contracts": 1, "avg_daily_pnl": 90, "daily_pnl_std": 275},
                {"contracts": 2, "avg_daily_pnl": 165, "daily_pnl_std": 490},
                {"contracts": 3, "avg_daily_pnl": 230, "daily_pnl_std": 700},
                {"contracts": 6, "avg_daily_pnl": 400, "daily_pnl_std": 1400},
            ]
            direct_rates = []
            for s in scenarios:
                sim = PassSimulator(
                    account=account, current_balance=50_000, high_water_mark=50_000,
                    days_remaining=11, avg_daily_pnl=s["avg_daily_pnl"],
                    daily_pnl_std=s["daily_pnl_std"], simulations=20_000,
                )
                sim.run()
                direct_rates.append(round(sim.pass_probability, 4))

            mcp_result = await session.call_tool(
                "prop_firm_compare_sizes",
                {"args": {"tier": "50K", "symbol": "ES", "current_balance": 50_000,
                          "high_water_mark": 50_000, "days_remaining": 11,
                          "scenarios": scenarios}},
            )
            via_mcp = json.loads(_text(mcp_result))
            mcp_rates = [row["pass_probability"] for row in via_mcp["comparison"]]
            check("compare_sizes not an error", not mcp_result.is_error)
            check("compare_sizes matches direct per-scenario PassSimulator runs",
                  mcp_rates == direct_rates, detail=f"direct={direct_rates} mcp={mcp_rates}")
            expected_pct = [1.7, 27.1, 49.7, 70.8]
            got_pct = [r * 100 for r in mcp_rates]
            check("compare_sizes matches this project's previously-verified figures (1.7/27.1/49.7/70.8%)",
                  all(abs(a - b) < 0.5 for a, b in zip(got_pct, expected_pct)),
                  detail=f"got {got_pct}")

            # ── SERF error: unknown tier ─────────────────────────────────
            print("\n=== SERF validation error (unknown tier) ===")
            mcp_result = await session.call_tool(
                "prop_firm_size_check", {"args": {"tier": "999K", "contracts": 1}}
            )
            text = _text(mcp_result)
            check("unknown tier returns is_error=True", mcp_result.is_error)
            check("error message carries SERF code", '"code": "unknown_tier"' in text, detail=text)
            check("error message carries retryable=false", '"retryable": false' in text, detail=text)

            # ── Rate limiting: trip prop_firm_compare_sizes's tight quota ─
            print("\n=== rate limiting (prop_firm_compare_sizes, capacity=5) ===")
            one_scenario = [{"contracts": 1, "avg_daily_pnl": 90, "daily_pnl_std": 275}]
            results = []
            for i in range(7):
                r = await session.call_tool(
                    "prop_firm_compare_sizes",
                    {"args": {"tier": "50K", "symbol": "ES", "current_balance": 50_000,
                              "high_water_mark": 50_000, "days_remaining": 11,
                              "scenarios": one_scenario}},
                )
                results.append(r)
            errored = [r for r in results if r.is_error]
            check("at least one of 7 rapid calls hit the rate limit (capacity=5)",
                  len(errored) >= 1, detail=f"{len(errored)}/7 errored")
            if errored:
                check("rate-limit error carries SERF code",
                      '"code": "rate_limited"' in _text(errored[0]), detail=_text(errored[0]))

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
