"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: prop_firm_position_sizing.py                   ║
║      Role:      Pre-trade sizing check for funded/eval         ║
║                  futures accounts                              ║
║      Source:    Operationalized from "The Secrets of Trading   ║
║                  Funded Accounts" (Take Profit Trader) — see    ║
║                  tpt_funded_accounts_analysis.html for what     ║
║                  was kept vs left out, and why                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

WHAT THIS DOES AND DOESN'T DO
    Kept (generalizable, math-checkable):
      - Point-risk-from-daily-loss-limit calculation
      - The 25%-of-max-contracts sizing check (flagged as the
        source's own stated personal preference, not a universal
        rule — exposed here as a configurable parameter, default 25%)
      - Risk-as-fraction-of-ADR check (the volatility-adjusted
        sizing idea the source document gestures at informally)

    Left out (not generalizable — see DEEPER/DEEPEST in the
    analysis dashboard for why):
      - The specific $50k/$150k account tier numbers are one firm's
        product parameters, not a market constant — this script
        takes YOUR account's actual daily loss limit, trailing
        drawdown and max-contract numbers as inputs, not TPT's table
      - Any claim about "millions of data points" — this script
        makes no probability-of-success claim, only a mechanical
        risk-consumption calculation
      - Commissions/fees are now included (the source's math omitted
        them) — see `commission_per_contract`

    NOTE — this file is superseded by prop_firm_sizing.py for
    day-to-day use: that file adds the EOD trailing-drawdown floor
    (the parameter this simpler file's docstring above doesn't even
    model) and a Monte Carlo pass-probability layer
    (prop_pass_simulator.py). Kept here as the simpler, standalone
    "point risk at this size" calculator — still correct and
    independently useful for a quick pre-trade sanity check that
    doesn't need the fuller account/session state.

SETUP
    pip install requests --break-system-packages   # only if using fetch_recent_adr
"""

import os
from dataclasses import dataclass


@dataclass
class AccountRules:
    """The account's own actual rules — read these off your prop firm's
    evaluation page, not off any generic table."""
    account_equity: float
    daily_loss_limit: float          # dollar amount that ends the day/test
    eod_trailing_drawdown: float     # dollar amount, separate constraint
    max_contracts: int               # firm's stated max position size
    point_value: float               # $ per point for the instrument (e.g. ES = 50)
    commission_per_contract: float = 4.50   # round-trip, adjust to your broker/firm


def point_risk_at_size(rules: AccountRules, contracts: int) -> dict:
    """
    How many points of adverse move, at `contracts` size, consumes the
    daily loss limit — the core calculation from the source's "Fault #1"
    section, with commissions netted in (the source's version didn't).
    """
    if contracts <= 0:
        return {"error": "contracts must be > 0"}

    total_commission = rules.commission_per_contract * contracts
    risk_budget_after_fees = rules.daily_loss_limit - total_commission
    if risk_budget_after_fees <= 0:
        return {"error": "commission alone exceeds the daily loss limit at this size"}

    points_of_risk = risk_budget_after_fees / (rules.point_value * contracts)

    return {
        "contracts": contracts,
        "points_of_risk": round(points_of_risk, 3),
        "commission_consumed": round(total_commission, 2),
        "dollar_risk_after_fees": round(risk_budget_after_fees, 2),
    }


def check_25pct_rule(rules: AccountRules, contracts: int, max_size_fraction: float = 0.25) -> dict:
    """
    The source's "Secret #2" — flagged explicitly as the author's stated
    personal preference (25%), not a derived or universal threshold.
    Exposed here as a configurable parameter so it's used as a starting
    point, not gospel.
    """
    allowed = max(1, int(rules.max_contracts * max_size_fraction))
    return {
        "contracts": contracts,
        "max_contracts": rules.max_contracts,
        "size_fraction_rule": max_size_fraction,
        "allowed_under_rule": allowed,
        "within_rule": contracts <= allowed,
        "pct_of_max_used": round((contracts / rules.max_contracts) * 100, 1),
    }


def check_adr_consumption(rules: AccountRules, contracts: int, average_daily_range_points: float) -> dict:
    """
    The volatility-adjusted idea the source gestures at informally
    (22 points of risk vs. a 78-point ADR). average_daily_range_points
    should be a CURRENT measurement — see the regime-dependency warning
    in the analysis dashboard before reusing an old ADR figure.
    """
    result = point_risk_at_size(rules, contracts)
    if "error" in result:
        return result

    pct_of_adr = (result["points_of_risk"] / average_daily_range_points) * 100 if average_daily_range_points > 0 else None
    return {
        **result,
        "average_daily_range_points": average_daily_range_points,
        "pct_of_adr_as_stop_room": round(pct_of_adr, 1) if pct_of_adr is not None else None,
        "warning": (pct_of_adr is not None and pct_of_adr < 25),
    }


def evaluate_size(rules: AccountRules, contracts: int, average_daily_range_points: float = None,
                   max_size_fraction: float = 0.25) -> dict:
    """One-call check combining all three: point risk, the 25%-style rule,
    and (if ADR supplied) the volatility-consumption check."""
    out = {
        "point_risk": point_risk_at_size(rules, contracts),
        "size_rule": check_25pct_rule(rules, contracts, max_size_fraction),
    }
    if average_daily_range_points is not None:
        out["adr_check"] = check_adr_consumption(rules, contracts, average_daily_range_points)

    out["summary_flags"] = []
    if not out["size_rule"]["within_rule"]:
        out["summary_flags"].append(
            f"Exceeds the {max_size_fraction*100:.0f}% max-size rule "
            f"({contracts} contracts vs {out['size_rule']['allowed_under_rule']} allowed)."
        )
    if "adr_check" in out and out["adr_check"].get("warning"):
        out["summary_flags"].append(
            f"Stop room is under 25% of current ADR "
            f"({out['adr_check']['pct_of_adr_as_stop_room']}%) — thin relative to typical daily movement."
        )
    if not out["summary_flags"]:
        out["summary_flags"].append("No flags — within the configured size and volatility checks.")

    return out


# ───────────────────────────────────────────────────────────────
# Optional: pull a real current ADR instead of hand-typing one
# ───────────────────────────────────────────────────────────────

def fetch_recent_adr(symbol: str, lookback_days: int = 14) -> float:
    """Fetch recent daily bars from EODHD and compute average daily range
    (High - Low) in points, so the ADR check uses CURRENT volatility
    rather than a stale figure copied from someone else's chart."""
    import requests
    import pandas as pd

    eodhd_key = os.getenv("EODHD_API_KEY", "YOUR_EODHD_KEY")
    end = pd.Timestamp.today().strftime("%Y-%m-%d")
    start = (pd.Timestamp.today() - pd.Timedelta(days=lookback_days * 3)).strftime("%Y-%m-%d")

    r = requests.get(
        f"https://eodhd.com/api/eod/{symbol}",
        params={"api_token": eodhd_key, "from": start, "to": end, "period": "d", "fmt": "json"},
        timeout=20,
    )
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df["range"] = df["high"] - df["low"]
    return round(float(df["range"].tail(lookback_days).mean()), 2)


if __name__ == "__main__":
    # Example: replicate the source's $50k/ES scenario, but with commissions
    # netted in and the ADR check parameterized rather than hardcoded.
    my_account = AccountRules(
        account_equity=50_000,
        daily_loss_limit=1100,
        eod_trailing_drawdown=2000,
        max_contracts=6,
        point_value=50,          # ES
        commission_per_contract=4.50,
    )

    print("♛ RUTHLESS PROP-FIRM SIZING CHECK\n")
    for contracts in (1, 3, 6):
        result = evaluate_size(my_account, contracts, average_daily_range_points=78.0)
        print(f"--- {contracts} contract(s) ---")
        print(f"  Points of risk (after commission): {result['point_risk'].get('points_of_risk')}")
        print(f"  Within {int(0.25*100)}% max-size rule: {result['size_rule']['within_rule']} "
              f"({result['size_rule']['pct_of_max_used']}% of max used)")
        if "adr_check" in result:
            print(f"  Stop room as % of ADR: {result['adr_check']['pct_of_adr_as_stop_room']}%")
        for flag in result["summary_flags"]:
            print(f"  ⚠ {flag}" if "No flags" not in flag else f"  ✓ {flag}")
        print()
