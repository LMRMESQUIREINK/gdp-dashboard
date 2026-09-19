# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Live monitor — polling loop, signal + alert only (NEVER executes orders)
#  PATCHED: uses real OHLCV (get_recent_ohlcv) instead of fabricated
#  high/low/volume. Real-time price still overlays the latest close.
#  Data Layer: EODHD
#  Generated: 2026-07-18 | Patched: 2026-08-03 | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: live_monitor.py                               ║
║      Role:      Poll live quotes, recompute signal, alert      ║
║      Guarantee: NEVER places an order — signal-only by design  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

This is the safe, productizable core of the "Trading Jarvis" article's
vision: voice/text query -> live data -> signal -> alert. The article's
"live trade execution" step is intentionally NOT implemented here.

If you want to wire this into a broker, that integration belongs in a
separate, explicitly human-reviewed module — never as an automatic next
step off of this monitor. Treat every BUY/SELL line below as a suggestion
for a human to evaluate, not an instruction the system carries out.

NOTE: fetch_realtime() gives an intraday price update, but not an
intraday volume update — EODHD's real-time endpoint used here doesn't
carry volume. The volume-confirmation check therefore still runs on the
most recent completed daily bar's volume until intraday volume is wired
in (see fetch_intraday() in data_pipeline.py for that upgrade path).

WHAT CHANGED IN THIS BUILD
    - A persistent failure (e.g. a missing API key) used to reprint the
      same error every poll_sec forever. Now backs off and stops after
      max_consecutive_errors, with a clear message, instead of running
      unattended and failing silently.
    - Now passes real existing_positions (via positions_store.py) into
      evaluate_trade(), and reports the actual portfolio_heat keys
      (heat_pct/warning/sizing.error) instead of dumping the whole dict
      into the alert message.
"""

import time
from datetime import datetime

from data_pipeline import get_recent_ohlcv, fetch_realtime
from signal_generator import generate_signals, latest_signal
from risk_manager import evaluate_trade
import positions_store as positions


def default_alert(message: str) -> None:
    """Default alert channel: stdout. Swap for Telegram/email/Slack as needed."""
    print(message)


def monitor_signal(
    symbol: str,
    equity: float = 50_000,
    risk_pct: float = 1.0,
    poll_sec: int = 60,
    alert_fn=default_alert,
    lookback_days: int = 120,
    max_iterations: int = None,
    max_consecutive_errors: int = 5,
) -> None:
    """
    Polling loop for one symbol. NEVER places orders — logs and alerts only.

    max_iterations: set to an int for testing (e.g. 3) to avoid an infinite loop.
                    Leave None for continuous monitoring.
    max_consecutive_errors: stop (rather than loop forever failing silently)
                    after this many consecutive fetch/compute errors.
    """
    print(f"♛ RUTHLESS LIVE MONITOR — watching {symbol} | "
          f"started {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("  (signal-only mode — no orders will ever be placed by this process)")

    iterations = 0
    consecutive_errors = 0
    while True:
        try:
            ohlcv = get_recent_ohlcv(symbol, lookback_days=lookback_days)
            live_price = fetch_realtime(symbol)
            if live_price:
                # Overlay the intraday price on the latest bar's close/
                # adjusted_close; high/low/volume stay as the last
                # completed daily bar's real values (see note above).
                ohlcv.iloc[-1, ohlcv.columns.get_loc("close")] = live_price
                ohlcv.iloc[-1, ohlcv.columns.get_loc("adjusted_close")] = live_price

            signaled = generate_signals(ohlcv)
            sig = latest_signal(signaled)
            ts = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
            line = (f"[{ts}] {symbol} | ${ohlcv['adjusted_close'].iloc[-1]:.2f} | "
                    f"signal={sig}")
            print(line)
            consecutive_errors = 0

            if sig == "BUY":
                existing = positions.positions_for_heat_check(exclude_symbol=symbol)
                risk_check = evaluate_trade(ohlcv, equity=equity, risk_pct=risk_pct,
                                             existing_positions=existing)
                heat = risk_check["portfolio_heat"]
                if risk_check["approved"]:
                    alert_fn(f"♛ ALERT (review required): {line} | "
                             f"suggested size={risk_check['sizing']['shares']} shares, "
                             f"stop=${risk_check['sizing']['stop']} | "
                             f"heat={heat['heat_pct']}%")
                else:
                    reason = (risk_check["sizing"]["error"] or
                              f"portfolio heat {heat['heat_pct']}% exceeds the 5% limit")
                    alert_fn(f"♛ SIGNAL FIRED BUT RISK-GATED: {line} | reason: {reason}")
            elif sig == "SELL":
                alert_fn(f"♛ ALERT (review required): {line}")

        except Exception as e:
            consecutive_errors += 1
            print(f"[error] {symbol}: {e} (consecutive failures: {consecutive_errors})")
            if consecutive_errors >= max_consecutive_errors:
                print(f"♛ Stopping after {consecutive_errors} consecutive errors — "
                      f"check API keys and connectivity, then restart.")
                break

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            print(f"♛ Monitor stopped after {iterations} iteration(s) (test mode).")
            break

        time.sleep(poll_sec)


if __name__ == "__main__":
    # Test mode — 2 iterations, 5-second interval, no real sleep-forever loop
    monitor_signal("AAPL.US", poll_sec=5, max_iterations=2)
