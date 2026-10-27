"""
Demo tools for the interface-lift toolkit. Not toy stand-ins: these wrap
the same already-proven PropFirmAccount/AccountRules/SessionState/
PassSimulator classes every other interface in this project uses
(prop_firm_sizing.py / prop_firm_position_sizing.py / prop_pass_simulator.py,
copied here unmodified, same convention as /builds/trading-jarvis/ and
/builds/prop-firm-mcp-server/).

Three tools, each demonstrating a different piece of the toolkit:
  - prop_firm_size_check       (local)   — ordinary computation, checked
                                            against evaluate_size() directly
  - prop_firm_pass_probability (local)   — same, against PassSimulator
  - publish_report             (outward) — writes a file another person
                                            could read; holds for approval
"""
from __future__ import annotations

from pathlib import Path

from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import CONTRACT_SPECS, PropFirmAccount, TPT_TIERS
from prop_pass_simulator import PassSimulator

from toolkit.registry import ToolRegistry
from toolkit.result import result

REPORTS_DIR = Path(__file__).resolve().parent / "outbox"
TIERS = list(TPT_TIERS.keys())
SYMBOLS = list(CONTRACT_SPECS.keys())


def register_demo_tools(registry: ToolRegistry) -> None:
    @registry.tool(effect="local")
    def prop_firm_size_check(tier: str, symbol: str, contracts: int) -> dict:
        """Check a TPT funded-account contract count against the
        25%-of-max-contracts rule. tier: one of 25K, 50K, 75K, 100K, 150K.
        symbol: a configured futures contract, e.g. ES."""
        if tier not in TPT_TIERS:
            return result(f"unknown tier {tier!r}, must be one of {TIERS}", checks=[("known tier", False)])
        if symbol not in CONTRACT_SPECS:
            return result(f"unknown symbol {symbol!r}, must be one of {SYMBOLS}", checks=[("known symbol", False)])
        account = PropFirmAccount(tier=tier, symbol=symbol)
        rules = AccountRules(
            account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
            eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
            point_value=account.point_value,
        )
        direct = evaluate_size(rules, contracts, average_daily_range_points=None)
        within_rule = direct["size_rule"]["within_rule"]
        return result(
            f"{contracts} contract(s) on {tier} {symbol}: {'within' if within_rule else 'over'} the 25% rule",
            checks=[("evaluate_size() returned a result", direct is not None)],
            **direct,
        )

    @registry.tool(effect="local")
    def prop_firm_pass_probability(tier: str, symbol: str, current_balance: float, high_water_mark: float,
                                    days_remaining: int, avg_daily_pnl: float, daily_pnl_std: float) -> dict:
        """Monte Carlo pass probability for a TPT evaluation, from the
        trader's own real average and standard deviation of daily P&L —
        never estimated by this tool."""
        if tier not in TPT_TIERS:
            return result(f"unknown tier {tier!r}, must be one of {TIERS}", checks=[("known tier", False)])
        account = PropFirmAccount(tier=tier, symbol=symbol)
        sim = PassSimulator(account=account, current_balance=current_balance, high_water_mark=high_water_mark,
                             days_remaining=days_remaining, avg_daily_pnl=avg_daily_pnl, daily_pnl_std=daily_pnl_std)
        sim.run()
        pass_probability = round(sim.pass_probability, 4)
        return result(
            f"{pass_probability:.1%} estimated pass probability over {days_remaining} days",
            checks=[("0 <= pass_probability <= 1", 0.0 <= pass_probability <= 1.0)],
            pass_probability=pass_probability, simulations=sim.simulations,
        )

    @registry.tool(effect="outward")
    def publish_report(filename: str, body: str) -> dict:
        """Write a plain-text report to the shared outbox — something
        another person could read, so it's an outward effect and holds
        for approval before it actually runs."""
        REPORTS_DIR.mkdir(exist_ok=True)
        path = REPORTS_DIR / filename
        path.write_text(body)
        written = path.read_text()
        return result(
            f"wrote {path.name} ({len(body)} bytes)", files={"report": path},
            checks=[("file on disk matches what was written", written == body)],
        )
