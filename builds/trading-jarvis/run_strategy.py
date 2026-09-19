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

WHAT CHANGED IN THIS BUILD
    Added --add-position/--positions/--remove-position (positions_store.py)
    so evaluate_trade()'s existing_positions parameter — always
    architecturally supported, never fed real data by any entry point —
    actually reflects other open positions. Recording a position is
    always an explicit, human-typed command, never inferred from a
    signal or an approved risk check.
"""

import argparse

from data_pipeline import get_recent_ohlcv
from signal_generator import generate_signals, latest_signal
from risk_manager import evaluate_trade
import positions_store as positions


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
    args = parser.parse_args()

    if args.add_position:
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
