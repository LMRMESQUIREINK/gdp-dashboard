"""
papertrade_run.py
=================
Daily paper-trading runner. The full lifecycle:

  1. Read watchlist from tickers.txt
  2. For each ticker:
     a. Run full 6-layer pipeline
     b. Log signal to trades.csv (audit trail)
     c. If BUY/SELL with valid params, open paper position (skip if held)
  3. Walk all open positions, check stop/target hits, close if triggered
  4. Snapshot equity to equity_curve.csv
  5. Print performance report

Usage:
    cd C:\\trading_system
    python papertrade_run.py                 (uses tickers.txt)
    python papertrade_run.py NVDA            (one-off ticker, no watchlist)
    python papertrade_run.py --report-only   (just print report, no new trades)
    python papertrade_run.py --check-only    (just close hit positions, no new entries)

Watchlist format (tickers.txt):
    NVDA
    MSFT
    AAPL
    # comments OK
    META

Cost: ~$0.15-$0.40 per ticker. With 5 tickers, ~$1-2 per daily run.
"""

import os
import sys
import re
from datetime import datetime
import atexit
import time
from outage_alert import RunTracker, classify

LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_run.lock")
STALE_LOCK_SECONDS = 2 * 60 * 60  # 2 hours

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid_str, ts_str = f.read().strip().split(",")
                existing_pid = int(pid_str)
                lock_age = time.time() - float(ts_str)
        except (ValueError, FileNotFoundError):
            existing_pid = None
            lock_age = STALE_LOCK_SECONDS + 1

        if lock_age < STALE_LOCK_SECONDS:
            still_running = False
            if existing_pid:
                try:
                    import ctypes
                    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                    handle = ctypes.windll.kernel32.OpenProcess(
                        PROCESS_QUERY_LIMITED_INFORMATION, False, existing_pid
                    )
                    if handle:
                        still_running = True
                        ctypes.windll.kernel32.CloseHandle(handle)
                except Exception:
                    still_running = True

            if still_running:
                print(f"[lock] Another stock run (PID {existing_pid}) is already active "
                      f"({lock_age/60:.1f} min old). Exiting cleanly - not a failure.")
                sys.exit(0)
            else:
                print(f"[lock] Stale lock found (PID {existing_pid} not running). Proceeding.")
        else:
            print(f"[lock] Lock file is {lock_age/60:.1f} min old - treating as stale. Proceeding.")

    with open(LOCK_FILE, "w") as f:
        f.write(f"{os.getpid()},{time.time()}")

    atexit.register(release_lock)

def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass

acquire_lock()

from agent_state import create_initial_state
from agents.market_analyst import build_market_analyst
from agents.social_analyst import build_social_analyst
from agents.news_analyst import build_news_analyst
from agents.fundamentals_analyst import build_fundamentals_analyst
from agents.insider_options_analyst import build_insider_options_analyst
from agents.research_team import build_research_team
from agents.risk_team import build_risk_team

from papertrade.storage import (
    log_trade, append_equity_snapshot, get_open_positions,
    get_current_cash,
)
from papertrade.positions import (
    open_position_from_decision, check_and_close_positions,
    parse_pm_decision, get_positions_market_value,
)
from papertrade.report import print_report


WATCHLIST_FILE = "tickers.txt"

# --- outage-alert: one tracker for the whole run ---
tracker = RunTracker()


def section(title: str):
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def read_watchlist() -> list:
    """Load tickers from tickers.txt (one per line, # comments OK)."""
    if not os.path.exists(WATCHLIST_FILE):
        print(f"  [WARN] {WATCHLIST_FILE} not found - using default ['NVDA']")
        return ["NVDA"]
    tickers = []
    with open(WATCHLIST_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tickers.append(line.upper())
    return tickers


def run_pipeline(ticker: str) -> dict:
    """Run the full 6-layer pipeline on one ticker, return final state."""
    trade_date = datetime.today().strftime("%Y-%m-%d")
    state = create_initial_state(ticker, trade_date)

    # Layer 1: Analysts
    for name, builder, field in [
        ("Market",        build_market_analyst,          "market_report"),
        ("Social",        build_social_analyst,          "sentiment_report"),
        ("News",          build_news_analyst,            "news_report"),
        ("Fundamentals",  build_fundamentals_analyst,    "fundamentals_report"),
        ("Insider/Options", build_insider_options_analyst, "insider_options_report"),
    ]:
        try:
            graph = builder()
            result = graph.invoke(state, {"recursion_limit": 25})
            if field in result:
                state[field] = result[field]
            print(f"    {name:18s} done")
        except Exception as e:
            print(f"    {name:18s} FAILED: {e}")

    # Layers 2-3: Research team
    try:
        state = build_research_team().invoke(state, {"recursion_limit": 50})
        print("    Research team       done")
    except Exception as e:
        print(f"    Research team       FAILED: {e}")
        return state

    # Layers 4-6: Risk team + PM
    try:
        state = build_risk_team().invoke(state, {"recursion_limit": 50})
        print("    Risk team + PM      done")
    except Exception as e:
        print(f"    Risk team + PM      FAILED: {e}")

    return state


def _extract_thesis_summary(plan: str) -> str:
    """Pull the THESIS section from the Research Manager's plan."""
    if not plan:
        return ""
    match = re.search(r"THESIS\s*:?\s*(.+?)(?:\n\n|KEY EVIDENCE|$)",
                      plan, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()[:300]
    return plan[:300]


def process_ticker(ticker: str):
    """Full run for one ticker: pipeline -> log -> maybe open position."""
    section(f"PROCESSING: {ticker}")
    state = run_pipeline(ticker)

    final_decision = state.get("final_trade_decision", "")
    parsed = parse_pm_decision(final_decision)

    # --- outage-alert: record this ticker's outcome ---
    # This is the single source of truth for this ticker's outcome. Everything
    # below this point is bookkeeping (CSV logging, opening a paper position) -
    # a failure in that bookkeeping is not a signal/agent failure and must not
    # reach main()'s per-ticker except, which would record a SECOND outcome for
    # the same ticker and corrupt the outage-rate math (see README's "A real bug
    # found and fixed" section for the false-positive-alert this caused).
    signal = parsed.get("signal")
    if signal in ("BUY", "SELL"):
        tracker.record(ticker, "signal")
    elif signal in ("HOLD",):
        tracker.record(ticker, "hold")
    else:
        tracker.record(ticker, classify(str(final_decision)))

    print(f"\n  Signal:    {parsed['signal']}")
    print(f"  Size:      {parsed['position_size_pct']}%")
    print(f"  Stop:      ${parsed['stop_loss']}")
    print(f"  Target:    ${parsed['take_profit']}")

    # Log to audit trail - guarded so a storage hiccup can't double-record this
    # ticker's outcome via main()'s outer except (see comment above).
    try:
        log_trade(
            ticker=ticker,
            trade_date=state["trade_date"],
            signal=parsed["signal"],
            action=parsed["signal"],
            position_size_pct=parsed["position_size_pct"] or 0,
            entry=None,  # filled at open time below
            stop_loss=parsed["stop_loss"],
            take_profit=parsed["take_profit"],
            time_horizon="weeks",
            judge_score=None,
            thesis_summary=_extract_thesis_summary(state.get("investment_plan", "")),
        )
    except Exception as e:
        print(f"  [WARN] Trade log failed: {e}")

    # Open position if signal is actionable - same guard, same reason.
    try:
        open_result = open_position_from_decision(ticker, final_decision)
        print(f"\n  Action: {open_result['action']}")
        if open_result["action"] == "opened":
            print(f"    {open_result['shares']:.2f} shares @ "
                  f"${open_result['entry_price']:.2f} "
                  f"(${open_result['dollar_size']:,.2f} position)")
        elif "reason" in open_result:
            print(f"    Reason: {open_result['reason']}")
    except Exception as e:
        print(f"  [WARN] Position open failed: {e}")


def main():
    args = sys.argv[1:]
    report_only = "--report-only" in args
    check_only = "--check-only" in args
    args = [a for a in args if not a.startswith("--")]

    section("PAPER TRADING DAILY RUNNER")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if report_only:
        print_report()
        return

    # Step 1 - close any positions that hit stop/target (run before opening new ones)
    section("STEP 1 - Checking open positions for stop/target hits")
    positions_before = get_open_positions()
    print(f"  Open positions: {len(positions_before)}")
    closure_summary = check_and_close_positions()
    print(f"  Checked {closure_summary['checked']}, "
          f"closed {closure_summary['closed']}, "
          f"realized P&L ${closure_summary['total_pnl']:+.2f}")
    for c in closure_summary["closures"]:
        print(f"    CLOSED {c['ticker']}: ${c['pnl_dollars']:+.2f} "
              f"({c['pnl_pct']:+.2f}%) [{c['close_reason']}]")

    if check_only:
        section("Skipping new trades (--check-only)")
        print_report()
        return

    # Step 2 - Process each ticker on the watchlist
    if args:
        tickers = [a.upper() for a in args]
        print(f"\n  One-off mode: {tickers}")
    else:
        tickers = read_watchlist()
        section(f"STEP 2 - Watchlist ({len(tickers)} tickers)")
        for t in tickers:
            print(f"    - {t}")

    for ticker in tickers:
        try:
            process_ticker(ticker)
        except Exception as e:
            print(f"  [ERROR] {ticker} failed: {e}")
            # --- outage-alert: a hard failure counts as an error for this ticker ---
            tracker.record(ticker, "error", str(e))

    # Step 3 - Snapshot equity
    section("STEP 3 - Equity Snapshot")
    cash = get_current_cash()
    positions_value = get_positions_market_value()
    open_count = len(get_open_positions())
    append_equity_snapshot(
        cash=cash,
        positions_value=positions_value,
        open_positions=open_count,
        closed_today=closure_summary["closed"],
        pnl_today=closure_summary["total_pnl"],
    )
    total_equity = cash + positions_value
    print(f"  Cash:            ${cash:,.2f}")
    print(f"  Positions value: ${positions_value:,.2f}")
    print(f"  Total equity:    ${total_equity:,.2f}")

    # --- outage-alert: check the run for a silent all-agent failure ---
    tracker.check_and_alert(run_name="stock", equity=total_equity)

    # Step 4 - Performance report
    print_report()


if __name__ == "__main__":
    main()
