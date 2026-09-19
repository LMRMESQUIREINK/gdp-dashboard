# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Orchestrator entry point — runs data -> signal -> risk -> Jarvis query
#  Data Layer: EODHD+FMP
#  Generated: 2026-07-18 | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Strategy:  Trading Jarvis — RSI-cross + volume confirm    ║
║      Symbol(s): configurable via CLI arg                       ║
║      Timeframe: daily                                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python run_strategy.py AAPL.US
    python run_strategy.py AAPL.US --monitor      (starts the live monitor)
    python run_strategy.py --ask "Check MSFT for a signal"   (Jarvis NL mode)

Renamed from run_strategy1.py to match README.md's documented entry point.
Now uses the real OHLCV frame (data_pipeline.get_recent_ohlcv) instead of
a synthetic high/low/volume band built from closes alone.
"""

import argparse

from data_pipeline import get_recent_ohlcv
from signal_generator import generate_signals, latest_signal
from risk_manager import evaluate_trade


def run_once(symbol: str, equity: float = 50_000, risk_pct: float = 1.0) -> None:
    print(f"♛ RUTHLESS TRADING GOLD — checking {symbol}\n")

    frame = get_recent_ohlcv(symbol, lookback_days=120)
    signaled = generate_signals(frame)
    sig = latest_signal(signaled)
    print(f"  Latest close : ${frame['adjusted_close'].iloc[-1]:.2f}")
    print(f"  Latest RSI   : {signaled['rsi'].iloc[-1]:.1f}")
    print(f"  Signal       : {sig}")

    if sig == "BUY":
        risk = evaluate_trade(frame, equity=equity, risk_pct=risk_pct)
        print(f"\n  ♛ Risk check (review before acting on this — no order is placed):")
        print(f"    Suggested shares : {risk['sizing']['shares']}")
        print(f"    Stop             : ${risk['sizing']['stop']}")
        print(f"    Dollar risk      : ${risk['sizing']['dollar_risk']}")
        print(f"    Trade heat       : {risk['portfolio_heat']['heat_pct']}%"
              f"{'  ⚠ WARNING' if risk['portfolio_heat']['warning'] else ''}")
        print(f"    ({risk['portfolio_heat']['reason']})")
    else:
        print("\n  No actionable BUY signal — risk check skipped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RUTHLESS Trading Jarvis — run once or monitor.")
    parser.add_argument("symbol", nargs="?", default="AAPL.US", help="EODHD symbol, e.g. AAPL.US")
    parser.add_argument("--monitor", action="store_true", help="Start the live polling monitor")
    parser.add_argument("--ask", type=str, default=None, help="Send a natural-language query to Jarvis (Claude API)")
    args = parser.parse_args()

    if args.ask:
        from jarvis_orchestrator import ask_jarvis
        print(f"> {args.ask}\n")
        print(ask_jarvis(args.ask))
    elif args.monitor:
        from live_monitor import monitor_signal
        monitor_signal(args.symbol, poll_sec=60)
    else:
        run_once(args.symbol)
