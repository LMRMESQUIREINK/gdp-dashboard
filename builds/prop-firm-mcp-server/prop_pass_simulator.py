"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: prop_pass_simulator.py                        ║
║      Role:      Monte Carlo pass probability for prop evals    ║
║      The gap:   TPT playbook gives rules, never shows pass-    ║
║                  rate math. This closes that gap.              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

USAGE
    from prop_firm_sizing import PropFirmAccount
    from prop_pass_simulator import PassSimulator

    acct = PropFirmAccount("50K", "ES")
    sim = PassSimulator(
        account=acct,
        current_balance=50_800,        # up $800 on the eval so far
        high_water_mark=51_200,        # peaked at +$1,200 today
        days_remaining=8,              # 11-day eval, 3 done
        avg_daily_pnl=250.0,           # trader's recent average
        daily_pnl_std=600.0,           # trader's recent daily std dev
    )
    sim.run()
    print(sim.report())
"""

import numpy as np
from dataclasses import dataclass, field
from prop_firm_sizing import PropFirmAccount, TPT_TIERS


@dataclass
class PassSimulator:
    """
    Monte Carlo simulator for prop firm evaluation outcomes.

    Models the evaluation as a random walk with daily P&L drawn from
    a normal distribution, tracking two termination conditions:
      1. Profit target hit → PASS
      2. EOD trailing drawdown floor breached → FAIL
      (Daily loss limit is modeled as a hard stop within each simulated day)

    avg_daily_pnl and daily_pnl_std should come from the trader's own
    journal or paper trading history — they are NOT estimated here.
    """
    account: PropFirmAccount
    current_balance: float          # balance right now
    high_water_mark: float          # HWM since eval started (or last reset)
    days_remaining: int             # trading days left in the eval
    avg_daily_pnl: float            # trader's recent mean daily P&L ($)
    daily_pnl_std: float            # trader's recent daily P&L std dev ($)
    simulations: int = 50_000
    min_trading_days: int = 3       # TPT rule: minimum 3 trading days

    # Results (populated by run())
    pass_probability: float = field(default=0.0, init=False)
    fail_dd_probability: float = field(default=0.0, init=False)
    fail_time_probability: float = field(default=0.0, init=False)
    median_days_to_pass: float = field(default=float("nan"), init=False)
    pct5_final_balance: float = field(default=0.0, init=False)
    pct95_final_balance: float = field(default=0.0, init=False)
    _ran: bool = field(default=False, init=False)

    def run(self) -> None:
        """Run the Monte Carlo simulation."""
        rng = np.random.default_rng(seed=42)
        profit_target   = self.account.starting_balance + self.account.profit_target
        daily_loss_cap  = self.account.daily_loss_limit  # max loss any one day
        eod_dd          = self.account.eod_trailing_dd

        outcomes = {"pass": 0, "fail_dd": 0, "fail_time": 0}
        days_to_pass_list = []
        final_balances = []

        for _ in range(self.simulations):
            balance = self.current_balance
            hwm     = self.high_water_mark
            passed  = False
            failed  = False
            day_num = 0
            days_traded = 0

            for day in range(self.days_remaining):
                day_num += 1
                # Daily P&L, capped at the daily loss limit
                raw_pnl = rng.normal(self.avg_daily_pnl, self.daily_pnl_std)
                daily_pnl = max(raw_pnl, -daily_loss_cap)  # daily loss limit kicks in

                balance += daily_pnl
                days_traded += 1

                # Update high-water mark
                if balance > hwm:
                    hwm = balance

                # Check trailing DD floor AFTER the day closes
                dd_floor = hwm - eod_dd
                if balance <= dd_floor:
                    outcomes["fail_dd"] += 1
                    failed = True
                    break

                # Check profit target (respecting min trading days)
                if balance >= profit_target and days_traded >= self.min_trading_days:
                    outcomes["pass"] += 1
                    days_to_pass_list.append(day_num)
                    passed = True
                    break

            if not passed and not failed:
                outcomes["fail_time"] += 1

            final_balances.append(balance)

        n = self.simulations
        self.pass_probability      = outcomes["pass"] / n
        self.fail_dd_probability   = outcomes["fail_dd"] / n
        self.fail_time_probability = outcomes["fail_time"] / n

        if days_to_pass_list:
            self.median_days_to_pass = float(np.median(days_to_pass_list))

        fb = np.array(final_balances)
        self.pct5_final_balance  = float(np.percentile(fb, 5))
        self.pct95_final_balance = float(np.percentile(fb, 95))
        self._ran = True

    def report(self) -> str:
        if not self._ran:
            self.run()

        tier       = self.account.tier
        sym        = self.account.symbol
        profit_tgt = self.account.starting_balance + self.account.profit_target
        dd_floor   = self.high_water_mark - self.account.eod_trailing_dd

        pass_icon = "🟢" if self.pass_probability >= 0.60 else ("🟡" if self.pass_probability >= 0.35 else "🔴")

        lines = [
            f"\n♛ PROP EVAL PASS PROBABILITY — {tier} ({sym})  {pass_icon}",
            f"{'─' * 60}",
            f"  Current balance:       ${self.current_balance:>10,.2f}",
            f"  High-water mark:       ${self.high_water_mark:>10,.2f}",
            f"  Current DD floor:      ${dd_floor:>10,.2f}",
            f"  Profit target:         ${profit_tgt:>10,.2f}",
            f"  Days remaining:        {self.days_remaining:>11}",
            f"  Input: avg daily P&L   ${self.avg_daily_pnl:>+10.2f} ± ${self.daily_pnl_std:.0f}",
            f"  Simulations:           {self.simulations:>11,}",
            f"{'─' * 60}",
            f"  ♛ PASS probability:    {self.pass_probability:>10.1%}",
            f"  Fail (DD breach):      {self.fail_dd_probability:>10.1%}",
            f"  Fail (time expired):   {self.fail_time_probability:>10.1%}",
            f"{'─' * 60}",
            f"  Median days to pass:   {self.median_days_to_pass:>10.1f}  (if passing)",
            f"  5th pct final balance: ${self.pct5_final_balance:>10,.2f}",
            f"  95th pct final bal:    ${self.pct95_final_balance:>10,.2f}",
            f"{'─' * 60}",
        ]

        # Plain-English interpretation
        if self.pass_probability >= 0.70:
            lines.append("  ✔  Strong position — maintain sizing discipline.")
        elif self.pass_probability >= 0.45:
            lines.append("  ⚠  Moderate. Consider reducing size to protect the floor.")
        else:
            lines.append("  ⛔  Low pass probability. The trailing DD floor is the primary threat.")
            lines.append("      Reduce to 1 contract, focus on not losing, let time work for you.")

        return "\n".join(lines)


def compare_sizing_strategies(account: PropFirmAccount, current_balance: float,
                                high_water_mark: float, days_remaining: int,
                                avg_daily_pnl_by_size: dict) -> None:
    """
    Compare pass probability at different contract sizes.
    avg_daily_pnl_by_size: {n_contracts: (avg_pnl, std_pnl)} for each sizing choice.
    """
    print(f"\n♛ SIZING STRATEGY COMPARISON — {account.tier} ({account.symbol})")
    print(f"{'─' * 65}")
    print(f"  {'Contracts':>10} | {'Avg P&L':>8} | {'Std Dev':>8} | {'Pass %':>8} | {'DD Fail %':>10}")
    print(f"{'─' * 65}")

    for n_contracts, (avg_pnl, std_pnl) in sorted(avg_daily_pnl_by_size.items()):
        sim = PassSimulator(
            account=account,
            current_balance=current_balance,
            high_water_mark=high_water_mark,
            days_remaining=days_remaining,
            avg_daily_pnl=avg_pnl,
            daily_pnl_std=std_pnl,
            simulations=20_000,
        )
        sim.run()
        marker = " ← 25% rule" if n_contracts == account.safe_contracts else ""
        print(f"  {n_contracts:>10} | ${avg_pnl:>7.0f} | ${std_pnl:>7.0f} | "
              f"{sim.pass_probability:>7.1%} | {sim.fail_dd_probability:>9.1%}{marker}")
    print(f"{'─' * 65}")


if __name__ == "__main__":
    from prop_firm_sizing import PropFirmAccount

    acct = PropFirmAccount("50K", "ES")

    # Baseline: trader up $800, peaked at $1,200, 8 days left
    sim = PassSimulator(
        account=acct,
        current_balance=50_800,
        high_water_mark=51_200,
        days_remaining=8,
        avg_daily_pnl=180.0,
        daily_pnl_std=550.0,
        simulations=50_000,
    )
    sim.run()
    print(sim.report())

    # Compare 1 vs 3 vs 6 contracts (fictional P&L scaling)
    print()
    compare_sizing_strategies(
        account=acct,
        current_balance=50_000,
        high_water_mark=50_000,
        days_remaining=11,
        avg_daily_pnl_by_size={
            1: (90,  275),   # 1 contract: modest edge, low vol
            2: (165, 490),   # 2 contracts
            3: (230, 700),   # 3 contracts
            6: (400, 1400),  # 6 contracts: max — bigger wins but huge variance
        }
    )
