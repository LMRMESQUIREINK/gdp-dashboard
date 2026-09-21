# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛  ×  SWAMP INTELLIGENCE
#  ───────────────────────────────────────────────────────────
#  Orchestrator entry point — runs data -> signal -> risk -> Jarvis query
#  PATCHED: uses real OHLCV (get_recent_ohlcv) instead of fabricated
#  high/low/volume — see data_pipeline.py's fix note for why that mattered.
#  Data Layer: EODHD+FMP
#  Generated: 2026-07-18 | Patched: 2026-08-03 | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Strategy:  Trading Jarvis — RSI(65) + volume confirm      ║
║      Symbol(s): configurable via CLI arg                       ║
║      Timeframe: daily                                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python run_strategy.py AAPL.US
    python run_strategy.py AAPL.US --monitor      (starts the live monitor)
    python run_strategy.py --ask "Check MSFT for a signal"   (Jarvis NL mode)
    python run_strategy.py AAPL.US --swamp        (Swamp Intelligence reasoning layer)
    python run_strategy.py --add-position AAPL.US 100 150.25 145.00
    python run_strategy.py --positions
    python run_strategy.py --remove-position AAPL.US

    Prop-firm account tools (TPT) — a separate flow, no EODHD/FMP data touched:
    python run_strategy.py --prop-size-check --prop-tier 50K --prop-contracts 1 --prop-adr 78
    python run_strategy.py --prop-session --prop-tier 50K --prop-pnl 200 --prop-hwm 51500
    python run_strategy.py --prop-pass-prob --prop-tier 50K --prop-balance 50800 \
        --prop-hwm 51200 --prop-days 8 --prop-avg-pnl 180 --prop-pnl-std 550
    python run_strategy.py --prop-compare --prop-tier 50K --prop-balance 50000 --prop-hwm 50000 \
        --prop-days 11 --prop-compare-size 1:90:275 2:165:490 3:230:700 6:400:1400

WHAT CHANGED IN THIS BUILD
    Added --add-position/--positions/--remove-position (positions_store.py)
    so evaluate_trade()'s existing_positions parameter — always
    architecturally supported, never fed real data by any entry point —
    actually reflects other open positions. Recording a position is
    always an explicit, human-typed command, never inferred from a
    signal or an approved risk check.

    Added --prop-size-check/--prop-session/--prop-pass-prob, giving CLI
    access to the same three prop-firm tools jarvis_orchestrator.py
    exposes to Claude (see /notes/prop-firm-sizing-analysis.md) without
    needing an Anthropic key or NL mode. Reuses SessionState.report()
    and PassSimulator.report()'s existing formatting rather than
    re-implementing it here.

    Added --prop-compare, wiring prop_pass_simulator.compare_sizing_
    strategies() — not exposed as a Claude tool (it takes a dict of
    {contracts: (avg_pnl, pnl_std)}, awkward as a single-turn NL ask;
    the CLI's --prop-compare-size CONTRACTS:AVG_PNL:PNL_STD [...] list
    fits it more naturally). Parses and validates each entry itself
    with a plain-English error on a malformed one, rather than letting
    a bad split()/int() surface as a raw traceback.
"""

import argparse

from data_pipeline import get_recent_ohlcv
from signal_generator import generate_signals, latest_signal
from risk_manager import evaluate_trade
import positions_store as positions
from prop_firm_sizing import PropFirmAccount, SessionState, TPT_TIERS, CONTRACT_SPECS
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_pass_simulator import PassSimulator, compare_sizing_strategies


def run_once(symbol: str, equity: float = 50_000, risk_pct: float = 1.0) -> None:
    print(f"♛ RUTHLESS TRADING GOLD — checking {symbol}\n")

    ohlcv = get_recent_ohlcv(symbol, lookback_days=120)

    signaled = generate_signals(ohlcv)
    sig = latest_signal(signaled)
    print(f"  Latest close : ${ohlcv['adjusted_close'].iloc[-1]:.2f}")
    print(f"  Latest RSI   : {signaled['rsi'].iloc[-1]:.1f}")
    print(f"  Vol confirm  : {signaled['vol_confirm'].iloc[-1]}")
    print(f"  Signal       : {sig}")

    if sig == "BUY":
        # ohlcv already has real close/high/low — risk_manager.atr() needs
        # exactly those columns, no fabrication required anymore.
        existing = positions.positions_for_heat_check(exclude_symbol=symbol)
        risk = evaluate_trade(ohlcv, equity=equity, risk_pct=risk_pct, existing_positions=existing)
        s, heat = risk["sizing"], risk["portfolio_heat"]
        print(f"\n  ♛ Risk check (review before acting on this — no order is placed):")
        if s["error"]:
            print(f"    {s['error']}")
        else:
            print(f"    Suggested shares : {s['shares']}")
            print(f"    Stop             : ${s['stop']}")
            print(f"    Dollar risk      : ${s['dollar_risk']}")
            print(f"    2R target        : ${s['r_multiple_target']}")
        print(f"    Portfolio heat   : {heat['heat_pct']}% (${heat['total_risk']} across "
              f"{len(existing) + 1} position(s)){'  ⚠ WARNING' if heat['warning'] else ''}")
        print(f"    Approved         : {risk['approved']}")
        if existing:
            print(f"    (heat includes {len(existing)} other open position(s) — see --positions)")
    else:
        print("\n  No actionable BUY signal — risk check skipped.")


def prop_size_check(tier: str, symbol: str, contracts: int, adr: float = None) -> None:
    account = PropFirmAccount(tier=tier, symbol=symbol)
    rules = AccountRules(
        account_equity=account.starting_balance,
        daily_loss_limit=account.daily_loss_limit,
        eod_trailing_drawdown=account.eod_trailing_dd,
        max_contracts=account.max_contracts,
        point_value=account.point_value,
    )
    result = evaluate_size(rules, contracts, average_daily_range_points=adr)
    print(f"♛ PROP-FIRM SIZE CHECK — {tier} ({symbol}), {contracts} contract(s)\n")
    point_risk = result["point_risk"]
    if "error" in point_risk:
        print(f"  {point_risk['error']}")
        return
    print(f"  Points of risk (after commission): {point_risk['points_of_risk']}")
    print(f"  Within {int(result['size_rule']['size_fraction_rule']*100)}% max-size rule: "
          f"{result['size_rule']['within_rule']} ({result['size_rule']['pct_of_max_used']}% of max used)")
    if "adr_check" in result:
        print(f"  Stop room as % of ADR: {result['adr_check']['pct_of_adr_as_stop_room']}%")
    for flag in result["summary_flags"]:
        print(f"  ⚠ {flag}" if "No flags" not in flag else f"  ✓ {flag}")


def prop_session_report(tier: str, symbol: str, intraday_pnl: float,
                         high_water_mark: float = None, session_start_balance: float = None) -> None:
    account = PropFirmAccount(tier=tier, symbol=symbol)
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
    print(state.report())


def prop_pass_probability(tier: str, symbol: str, current_balance: float, high_water_mark: float,
                           days_remaining: int, avg_daily_pnl: float, daily_pnl_std: float) -> None:
    account = PropFirmAccount(tier=tier, symbol=symbol)
    sim = PassSimulator(
        account=account,
        current_balance=current_balance,
        high_water_mark=high_water_mark,
        days_remaining=days_remaining,
        avg_daily_pnl=avg_daily_pnl,
        daily_pnl_std=daily_pnl_std,
    )
    print(sim.report())


def _parse_compare_sizes(specs: list) -> dict:
    """Parse ["1:90:275", "2:165:490", ...] into {contracts: (avg_pnl, std_pnl)}."""
    avg_daily_pnl_by_size = {}
    for spec in specs:
        parts = spec.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"--prop-compare-size '{spec}' isn't in CONTRACTS:AVG_PNL:PNL_STD "
                f"format (e.g. '2:165:490') — 3 colon-separated numbers, got {len(parts)}."
            )
        try:
            contracts = int(parts[0])
            avg_pnl = float(parts[1])
            pnl_std = float(parts[2])
        except ValueError:
            raise ValueError(
                f"--prop-compare-size '{spec}': CONTRACTS must be a whole number, "
                f"AVG_PNL/PNL_STD must be numbers (e.g. '2:165:490')."
            )
        avg_daily_pnl_by_size[contracts] = (avg_pnl, pnl_std)
    return avg_daily_pnl_by_size


def prop_compare(tier: str, symbol: str, current_balance: float, high_water_mark: float,
                  days_remaining: int, size_specs: list) -> None:
    account = PropFirmAccount(tier=tier, symbol=symbol)
    avg_daily_pnl_by_size = _parse_compare_sizes(size_specs)
    compare_sizing_strategies(account, current_balance, high_water_mark,
                               days_remaining, avg_daily_pnl_by_size)


def print_positions() -> None:
    open_positions = positions.load_positions()
    if not open_positions:
        print("♛ No open positions recorded.")
        return
    print(f"♛ Open positions ({positions.POSITIONS_FILE}):")
    for p in open_positions:
        print(f"  {p['symbol']:10s} shares={p['shares']:<8} entry=${p['entry']:<10} stop=${p['stop']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RUTHLESS Trading Jarvis — run once or monitor.")
    parser.add_argument("symbol", nargs="?", default="AAPL.US", help="EODHD symbol, e.g. AAPL.US")
    parser.add_argument("--monitor", action="store_true", help="Start the live polling monitor")
    parser.add_argument("--ask", type=str, default=None, help="Send a natural-language query to Jarvis (Claude API)")
    parser.add_argument("--swamp", action="store_true",
                         help="Route the check through the Swamp Intelligence reasoning layer "
                              "(Task Tree + Event Packets) before running the same data->signal->risk sequence")
    parser.add_argument("--equity", type=float, default=50_000, help="Account equity for sizing (default 50000)")
    parser.add_argument("--risk-pct", type=float, default=1.0, help="Risk percent per trade (default 1.0)")
    parser.add_argument("--positions", action="store_true", help="List recorded open positions")
    parser.add_argument("--add-position", nargs=4, metavar=("SYMBOL", "SHARES", "ENTRY", "STOP"),
                         help="Record a position you already took elsewhere (never automatic)")
    parser.add_argument("--remove-position", metavar="SYMBOL", help="Remove a recorded position")

    prop = parser.add_argument_group(
        "prop-firm account tools (TPT)",
        "A separate flow from everything above — no EODHD/FMP data touched. "
        "Pick exactly one of --prop-size-check/--prop-session/--prop-pass-prob.",
    )
    prop.add_argument("--prop-size-check", action="store_true",
                       help="Static point-risk + 25%%-rule + optional ADR check. Needs --prop-tier, --prop-contracts.")
    prop.add_argument("--prop-session", action="store_true",
                       help="Live trailing-DD-floor-aware session report. Needs --prop-tier, --prop-pnl.")
    prop.add_argument("--prop-pass-prob", action="store_true",
                       help="Monte Carlo eval pass probability. Needs --prop-tier, --prop-balance, --prop-hwm, "
                            "--prop-days, --prop-avg-pnl, --prop-pnl-std.")
    prop.add_argument("--prop-compare", action="store_true",
                       help="Compare pass probability across contract sizes. Needs --prop-tier, --prop-balance, "
                            "--prop-hwm, --prop-days, --prop-compare-size (one or more).")
    prop.add_argument("--prop-tier", type=str, default=None,
                       help=f"TPT account tier: one of {list(TPT_TIERS.keys())}")
    prop.add_argument("--prop-symbol", type=str, default="ES",
                       help="Futures contract: ES, NQ, MES, MNQ, RTY, or YM (default ES)")
    prop.add_argument("--prop-contracts", type=int, default=None, help="Contract count, for --prop-size-check")
    prop.add_argument("--prop-adr", type=float, default=None,
                       help="Optional current average daily range in points, for --prop-size-check")
    prop.add_argument("--prop-pnl", type=float, default=0.0,
                       help="Today's intraday P&L (negative if down), for --prop-session")
    prop.add_argument("--prop-hwm", type=float, default=None,
                       help="High-water mark, for --prop-session (optional) / --prop-pass-prob (required)")
    prop.add_argument("--prop-start-balance", type=float, default=None,
                       help="Session start balance override, for --prop-session")
    prop.add_argument("--prop-balance", type=float, default=None, help="Current balance, for --prop-pass-prob")
    prop.add_argument("--prop-days", type=int, default=None, help="Days remaining in eval, for --prop-pass-prob")
    prop.add_argument("--prop-avg-pnl", type=float, default=None,
                       help="Trader's OWN recent average daily P&L — never estimated, for --prop-pass-prob")
    prop.add_argument("--prop-pnl-std", type=float, default=None,
                       help="Trader's OWN recent daily P&L std dev — never estimated, for --prop-pass-prob")
    prop.add_argument("--prop-compare-size", nargs="+", metavar="CONTRACTS:AVG_PNL:PNL_STD", default=None,
                       help="One entry per contract size to compare, e.g. "
                            "1:90:275 2:165:490 3:230:700 — for --prop-compare")

    args = parser.parse_args()

    if args.prop_size_check or args.prop_session or args.prop_pass_prob or args.prop_compare:
        if args.prop_size_check and args.prop_contracts is None:
            parser.error("--prop-size-check needs --prop-tier and --prop-contracts")
        if args.prop_pass_prob:
            missing = [flag for flag, val in (
                ("--prop-balance", args.prop_balance), ("--prop-hwm", args.prop_hwm),
                ("--prop-days", args.prop_days), ("--prop-avg-pnl", args.prop_avg_pnl),
                ("--prop-pnl-std", args.prop_pnl_std),
            ) if val is None]
            if missing:
                parser.error(f"--prop-pass-prob needs {', '.join(missing)}")
        if args.prop_compare:
            missing = [flag for flag, val in (
                ("--prop-balance", args.prop_balance), ("--prop-hwm", args.prop_hwm),
                ("--prop-days", args.prop_days), ("--prop-compare-size", args.prop_compare_size),
            ) if val is None]
            if missing:
                parser.error(f"--prop-compare needs {', '.join(missing)}")
        if not args.prop_tier:
            parser.error("Prop-firm tools need --prop-tier")

        try:
            if args.prop_size_check:
                prop_size_check(args.prop_tier, args.prop_symbol, args.prop_contracts, args.prop_adr)
            elif args.prop_session:
                prop_session_report(args.prop_tier, args.prop_symbol, args.prop_pnl,
                                     args.prop_hwm, args.prop_start_balance)
            elif args.prop_pass_prob:
                prop_pass_probability(args.prop_tier, args.prop_symbol, args.prop_balance, args.prop_hwm,
                                       args.prop_days, args.prop_avg_pnl, args.prop_pnl_std)
            else:
                prop_compare(args.prop_tier, args.prop_symbol, args.prop_balance, args.prop_hwm,
                             args.prop_days, args.prop_compare_size)
        except ValueError as exc:
            # PropFirmAccount's own ValueError already names the valid tiers;
            # _parse_compare_sizes' own ValueError already explains the format.
            print(f"♛ Prop-firm input error: {exc}")
        except KeyError:
            # CONTRACT_SPECS[symbol] raising is a bare KeyError with just the
            # bad key as its message — give a real sentence instead.
            print(f"♛ Prop-firm input error: unknown --prop-symbol "
                  f"'{args.prop_symbol}'. Valid: {list(CONTRACT_SPECS.keys())}")
    elif args.add_position:
        sym, shares, entry, stop = args.add_position
        positions.add_position(sym, int(shares), float(entry), float(stop))
        print(f"♛ Recorded: {sym} {shares} shares @ ${entry}, stop ${stop}")
        print_positions()
    elif args.remove_position:
        positions.remove_position(args.remove_position)
        print(f"♛ Removed {args.remove_position}")
        print_positions()
    elif args.positions:
        print_positions()
    elif args.ask:
        from jarvis_orchestrator import ask_jarvis
        print(f"> {args.ask}\n")
        print(ask_jarvis(args.ask))
    elif args.monitor:
        from live_monitor import monitor_signal
        monitor_signal(args.symbol, poll_sec=60)
    elif args.swamp:
        from jarvis_swamp_bridge import route_through_bus
        route_through_bus(args.symbol, equity=args.equity, risk_pct=args.risk_pct)
    else:
        run_once(args.symbol, equity=args.equity, risk_pct=args.risk_pct)
