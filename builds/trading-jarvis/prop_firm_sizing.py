"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: prop_firm_sizing.py                           ║
║      Role:      TPT 25% rule calculator + trailing DD tracker  ║
║      Key fix:   Surfaces the EOD TRAILING DRAWDOWN floor —     ║
║                  the parameter the TPT playbook under-explains  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

SETUP
    pip install pandas numpy --break-system-packages

USAGE
    from prop_firm_sizing import PropFirmAccount, size_for_session

    acct = PropFirmAccount(tier="50K")
    print(acct.summary())
    print(size_for_session(acct, intraday_pnl=800, high_water_mark=800))
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


# ───────────────────────────────────────────────────────────────
# TPT account tier specs (as documented in the playbook)
# ───────────────────────────────────────────────────────────────

TPT_TIERS = {
    "25K":  {"starting_balance": 25_000, "max_contracts": 3,  "daily_loss": 1_000, "eod_trailing_dd": 1_500, "profit_target": 1_500, "fee": 150},
    "50K":  {"starting_balance": 50_000, "max_contracts": 6,  "daily_loss": 1_100, "eod_trailing_dd": 2_000, "profit_target": 3_000, "fee": 170},
    "75K":  {"starting_balance": 75_000, "max_contracts": 9,  "daily_loss": 2_250, "eod_trailing_dd": 2_750, "profit_target": 4_250, "fee": 245},
    "100K": {"starting_balance": 100_000,"max_contracts": 12, "daily_loss": 2_500, "eod_trailing_dd": 3_000, "profit_target": 6_000, "fee": 330},
    "150K": {"starting_balance": 150_000,"max_contracts": 15, "daily_loss": 3_300, "eod_trailing_dd": 4_500, "profit_target": 9_000, "fee": 360},
}

# Futures contract specs — extend as needed
CONTRACT_SPECS = {
    "ES":  {"name": "E-Mini S&P 500",     "point_value": 50.0,  "tick_size": 0.25},
    "NQ":  {"name": "E-Mini NASDAQ-100",   "point_value": 20.0,  "tick_size": 0.25},
    "MES": {"name": "Micro E-Mini S&P 500","point_value": 5.0,   "tick_size": 0.25},
    "MNQ": {"name": "Micro E-Mini NQ",     "point_value": 2.0,   "tick_size": 0.25},
    "RTY": {"name": "E-Mini Russell 2000", "point_value": 50.0,  "tick_size": 0.10},
    "YM":  {"name": "E-Mini Dow",          "point_value": 5.0,   "tick_size": 1.0},
}


@dataclass
class PropFirmAccount:
    """Represents a single TPT evaluation or PRO account at a given tier."""
    tier: str
    symbol: str = "ES"
    percent_rule: float = 0.25   # James's recommended 25% of max contracts

    # Populated from tier table on __post_init__
    starting_balance: float = field(init=False)
    max_contracts: int = field(init=False)
    daily_loss_limit: float = field(init=False)
    eod_trailing_dd: float = field(init=False)
    profit_target: float = field(init=False)
    fee: float = field(init=False)

    def __post_init__(self):
        tier_key = self.tier.upper().replace(" ", "")
        if tier_key not in TPT_TIERS:
            raise ValueError(f"Unknown tier '{tier_key}'. Valid: {list(TPT_TIERS.keys())}")
        spec = TPT_TIERS[tier_key]
        self.starting_balance   = spec["starting_balance"]
        self.max_contracts      = spec["max_contracts"]
        self.daily_loss_limit   = spec["daily_loss"]
        self.eod_trailing_dd    = spec["eod_trailing_dd"]
        self.profit_target      = spec["profit_target"]
        self.fee                = spec["fee"]

    @property
    def safe_contracts(self) -> int:
        """25% rule applied to max_contracts (minimum 1)."""
        raw = self.max_contracts * self.percent_rule
        return max(1, math.floor(raw))

    @property
    def point_value(self) -> float:
        return CONTRACT_SPECS[self.symbol.upper()]["point_value"]

    @property
    def daily_loss_in_points(self) -> float:
        """Daily loss limit expressed in points for this contract."""
        return self.daily_loss_limit / self.point_value

    def point_risk_per_contract(self, contracts: int) -> float:
        """How many points of risk each contract gets before the daily limit fires."""
        if contracts <= 0:
            return 0.0
        return self.daily_loss_in_points / contracts

    def summary(self) -> str:
        pts_safe = self.point_risk_per_contract(self.safe_contracts)
        pts_max  = self.point_risk_per_contract(self.max_contracts)
        sym_spec = CONTRACT_SPECS[self.symbol.upper()]
        lines = [
            f"\n♛ RUTHLESS PROP FIRM SIZING — {self.tier} Account ({self.symbol})",
            f"{'─' * 55}",
            f"  Starting balance:    ${self.starting_balance:>10,.0f}",
            f"  Profit target:       ${self.profit_target:>10,.0f}",
            f"  Daily loss limit:    ${self.daily_loss_limit:>10,.0f}  ({self.daily_loss_in_points:.1f} {self.symbol} pts)",
            f"  EOD trailing DD:     ${self.eod_trailing_dd:>10,.0f}  ({self.eod_trailing_dd / self.point_value:.1f} {self.symbol} pts)",
            f"  Max contracts:       {self.max_contracts:>11}",
            f"{'─' * 55}",
            f"  ♛ 25% RULE ({self.percent_rule*100:.0f}%):   {self.safe_contracts:>11} contract(s)",
            f"  Points/contract @25%: {pts_safe:>10.1f} pts",
            f"  Points/contract @max: {pts_max:>10.1f} pts  ← DANGER ZONE",
            f"{'─' * 55}",
            f"  Contract: {sym_spec['name']}",
            f"  Point value: ${sym_spec['point_value']:.0f} | Tick: {sym_spec['tick_size']}",
        ]
        return "\n".join(lines)


# ───────────────────────────────────────────────────────────────
# The critical fix: EOD trailing drawdown floor calculator
# This is what the playbook under-explains
# ───────────────────────────────────────────────────────────────

@dataclass
class SessionState:
    """Tracks intraday state against both daily limit AND trailing DD."""
    account: PropFirmAccount
    session_start_balance: float    # balance at start of today's session
    high_water_mark: float          # highest balance since last EOD reset
    intraday_pnl: float = 0.0       # current open + closed P&L for today

    @property
    def current_balance(self) -> float:
        return self.session_start_balance + self.intraday_pnl

    @property
    def trailing_dd_floor(self) -> float:
        """
        The actual trailing drawdown floor RIGHT NOW.
        This follows the HIGH WATER MARK, not the starting balance.
        KEY INSIGHT FROM DEEPEST-EST ANALYSIS: this can be ABOVE the starting
        balance if you had a good morning — giving you LESS room, not more.
        """
        return self.high_water_mark - self.account.eod_trailing_dd

    @property
    def remaining_daily_loss(self) -> float:
        """How much more loss is allowed by the daily limit."""
        return self.account.daily_loss_limit + self.intraday_pnl  # intraday_pnl is negative if losing

    @property
    def gap_to_trailing_floor(self) -> float:
        """How much room between current balance and the trailing DD floor."""
        return self.current_balance - self.trailing_dd_floor

    @property
    def binding_loss_limit(self) -> float:
        """
        The ACTUAL effective loss limit — the SMALLER of:
          a) Remaining daily loss
          b) Gap to trailing DD floor
        This is the number traders need to size against.
        """
        return min(self.remaining_daily_loss, self.gap_to_trailing_floor)

    @property
    def effective_points_per_contract(self) -> float:
        """Points of risk per contract based on EFFECTIVE (binding) limit."""
        n = self.safe_contracts
        pv = self.account.point_value
        if n <= 0 or pv <= 0:
            return 0.0
        return self.binding_loss_limit / pv / n

    @property
    def safe_contracts(self) -> int:
        """25% rule, but further constrained if binding limit is very tight."""
        base = self.account.safe_contracts
        pv = self.account.point_value
        min_point_risk = 3.0   # below this, even 1 contract is too risky to size
        if self.binding_loss_limit < (min_point_risk * pv):
            return 0   # Stop trading — too close to floor
        return base

    def warning_level(self) -> str:
        gap_pct = self.gap_to_trailing_floor / self.account.eod_trailing_dd
        if gap_pct <= 0:
            return "BREACHED"
        elif gap_pct <= 0.25:
            return "CRITICAL"
        elif gap_pct <= 0.50:
            return "WARNING"
        else:
            return "SAFE"

    def report(self) -> str:
        sym = self.account.symbol
        pv  = self.account.point_value
        wl  = self.warning_level()
        wl_icon = {"BREACHED": "🔴", "CRITICAL": "🔴", "WARNING": "🟡", "SAFE": "🟢"}.get(wl, "⚪")
        lines = [
            f"\n♛ SESSION STATE — {self.account.tier} ({sym})  {wl_icon} {wl}",
            f"{'─' * 58}",
            f"  Session start balance:   ${self.session_start_balance:>10,.2f}",
            f"  Intraday P&L:            ${self.intraday_pnl:>+10.2f}",
            f"  Current balance:         ${self.current_balance:>10,.2f}",
            f"  High-water mark:         ${self.high_water_mark:>10,.2f}",
            f"{'─' * 58}",
            f"  EOD Trailing DD floor:   ${self.trailing_dd_floor:>10,.2f}",
            f"  Gap to DD floor:         ${self.gap_to_trailing_floor:>10,.2f}  ({self.gap_to_trailing_floor/pv:.1f} {sym} pts)",
            f"  Remaining daily limit:   ${self.remaining_daily_loss:>10,.2f}",
            f"{'─' * 58}",
            f"  ♛ BINDING loss limit:    ${self.binding_loss_limit:>10,.2f}  ({self.binding_loss_limit/pv:.1f} {sym} pts)",
            f"  ♛ Safe contracts NOW:    {self.safe_contracts:>11}",
            f"  Points/contract NOW:     {self.effective_points_per_contract:>10.1f} pts",
        ]
        if wl in ("BREACHED", "CRITICAL"):
            lines.append(f"\n  ⛔ STOP TRADING — too close to DD floor to size safely.")
        elif wl == "WARNING":
            lines.append(f"\n  ⚠  Consider reducing to 1 contract or flat for the session.")
        return "\n".join(lines)


def size_for_session(account: PropFirmAccount, intraday_pnl: float = 0.0,
                      high_water_mark: Optional[float] = None,
                      session_start_balance: Optional[float] = None) -> str:
    """
    One-call convenience: get full session sizing report.

    intraday_pnl: today's P&L so far (negative if down)
    high_water_mark: highest balance today (or since last reset)
    session_start_balance: balance at open of today's session
    """
    if session_start_balance is None:
        session_start_balance = account.starting_balance
    if high_water_mark is None:
        high_water_mark = session_start_balance + max(0.0, intraday_pnl)

    state = SessionState(
        account=account,
        session_start_balance=session_start_balance,
        high_water_mark=high_water_mark,
        intraday_pnl=intraday_pnl,
    )
    return state.report()


# ───────────────────────────────────────────────────────────────
# Full comparison table across all tiers (CLI output)
# ───────────────────────────────────────────────────────────────

def print_full_tier_table(symbol: str = "ES") -> None:
    print(f"\n♛ RUTHLESS PROP FIRM SIZING TABLE — {symbol}")
    print(f"{'─' * 90}")
    hdr = f"{'Tier':>6} | {'Start':>8} | {'Max Cts':>7} | {'25% Cts':>7} | {'DLL $':>8} | {'DLL pts':>7} | {'EOD DD $':>9} | {'Pts/ct @25%':>11}"
    print(hdr)
    print(f"{'─' * 90}")
    pv = CONTRACT_SPECS[symbol.upper()]["point_value"]
    for tier, spec in TPT_TIERS.items():
        acct = PropFirmAccount(tier=tier, symbol=symbol)
        pts_dll = spec["daily_loss"] / pv
        pts_pc  = acct.point_risk_per_contract(acct.safe_contracts)
        row = (f"{tier:>6} | ${spec['starting_balance']:>7,.0f} | {spec['max_contracts']:>7} | "
               f"{acct.safe_contracts:>7} | ${spec['daily_loss']:>7,.0f} | {pts_dll:>7.1f} | "
               f"${spec['eod_trailing_dd']:>8,.0f} | {pts_pc:>11.1f}")
        print(row)
    print(f"{'─' * 90}")


if __name__ == "__main__":
    print_full_tier_table("ES")
    print()

    # Full account summary
    acct = PropFirmAccount(tier="50K", symbol="ES")
    print(acct.summary())

    # Session sizing — up $800 on the day, high-water = $800 profit
    print(size_for_session(acct, intraday_pnl=800, high_water_mark=50_800))

    print("\n--- Scenario: peaked at +$1,500, now back to +$200 ---")
    print(size_for_session(acct, intraday_pnl=200, high_water_mark=51_500))

    print("\n--- Scenario: down $900 on the day ---")
    print(size_for_session(acct, intraday_pnl=-900, high_water_mark=50_000))
