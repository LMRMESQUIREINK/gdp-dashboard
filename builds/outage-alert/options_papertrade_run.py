"""
options_papertrade_run.py
=========================
Daily options paper-trading runner. The full lifecycle:

  1. Read watchlist from tickers.txt (shares list with stock runner)
  2. Clear pricing cache (fresh start)
  3. For each open position: check stop/target/DTE close triggers
  4. For each ticker on watchlist:
     a. Run full 7-layer pipeline (stocks + options selector)
     b. Log signal to options_trades.csv
     c. If strategy != NO_TRADE, open paper options position
  5. Snapshot equity to options_equity.csv
  6. Print performance report

Usage:
    cd C:\\trading_system
    python options_papertrade_run.py                 (uses tickers.txt)
    python options_papertrade_run.py NVDA            (one-off ticker)
    python options_papertrade_run.py --report-only   (just print report)
    python options_papertrade_run.py --check-only    (just close hit positions)

Watchlist format: same tickers.txt as stock runner.
Cost: ~$0.30-$0.40 per ticker. Full watchlist ~$3-5 per daily run.
"""

import os
import sys
import re
from datetime import datetime
import atexit
import time
from outage_alert import RunTracker, classify

LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "options_run.lock")
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
                print(f"[lock] Another options run (PID {existing_pid}) is already active "
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

# NEW: options layer
from options_agents.strategy_selector import strategy_selector_node
from options.data_tools import get_underlying_price

from options_papertrade.storage import (
    log_trade, append_equity_snapshot, get_open_positions,
    get_current_cash,
)
from options_papertrade.positions import (
    open_position_from_proposal, check_and_close_positions,
    get_positions_market_value,
)
from options_papertrade.pricing import clear_cache
from options_papertrade.report import print_report


WATCHLIST_FILE = "tickers.txt"

# --- outage-alert: one tracker for the whole run ---
tracker = RunTracker()


def section(title: str):
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def read_watchlist() -> list:
    """Load tickers from tickers.txt."""
    if not os.path.exists(WATCHLIST_FILE):
        return ["NVDA"]
    tickers = []
    with open(WATCHLIST_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tickers.append(line.upper())
    return tickers


def run_full_pipeline(ticker: str) -> dict:
    """Run all 7 layers - stock side + options strategy selector."""
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

    # Layer 7: Options strategy selector
    try:
        result = strategy_selector_node(state)
        for k, v in result.items():
            state[k] = v
        print("    Options selector    done")
    except Exception as e:
        print(f"    Options selector    FAILED: {e}")

    return state


def _extract_thesis(plan: str) -> str:
    if not plan:
        return ""
    m = re.search(r"THESIS\s*:?\s*(.+?)(?:\n\n|KEY EVIDENCE|$)",
                  plan, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()[:300]
    return plan[:300]


def _parse_field(text: str, pattern: str, group: int = 1):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(group) if m else None


def process_ticker(ticker: str):
    """Full lifecycle for one ticker: pipeline -> log -> maybe open."""
    section(f"PROCESSING: {ticker}")
    state = run_full_pipeline(ticker)

    proposal = state.get("options_proposal", "")
    strategy = state.get("options_strategy", "UNKNOWN")
    iv_regime = state.get("options_iv_regime", "UNKNOWN")
    underlying_signal = state.get("options_underlying_signal", "UNKNOWN")

    # --- outage-alert: record this ticker's outcome ---
    # This is the single source of truth for this ticker's outcome. Everything
    # below this point is bookkeeping (CSV logging, opening a paper position) -
    # a failure in that bookkeeping is not a signal/agent failure and must not
    # reach main()'s per-ticker except, which would record a SECOND outcome for
    # the same ticker and corrupt the outage-rate math (see README's "A real bug
    # found and fixed" section for the false-positive-alert this caused).
    if strategy == "UNKNOWN":
        tracker.record(ticker, "unknown")
    elif strategy == "NO_TRADE":
        tracker.record(ticker, "hold")
    else:
        tracker.record(ticker, "signal")

    # Extract details for the audit log
    expiration = _parse_field(proposal, r"EXPIRATION\s*:?\s*(\d{4}-\d{2}-\d{2})") or ""
    dte_str = _parse_field(proposal, r"DAYS\s+TO\s+EXPIRATION\s*:?\s*(\d+)")
    dte = int(dte_str) if dte_str else 0
    net_dc = _parse_field(proposal, r"NET\s+(?:DEBIT|CREDIT|DEBIT/CREDIT)\s*:?\s*\$?([\d.]+)") or "0"
    max_loss_str = _parse_field(proposal, r"MAX\s+LOSS\s*:?\s*\$?([\d,.]+)") or "0"
    max_gain_str = _parse_field(proposal, r"MAX\s+GAIN\s*:?\s*\$?([\d,.]+)")
    breakeven_str = _parse_field(proposal, r"BREAKEVEN[\(s\)]*\s*:?\s*\$?([\d,.]+)") or "0"
    rr = _parse_field(proposal, r"RISK/REWARD\s*:?\s*(.+?)$") or ""

    print(f"\n  Strategy:    {strategy}")
    print(f"  IV regime:   {iv_regime}")
    print(f"  Underlying:  {underlying_signal}")
    if strategy not in ("NO_TRADE", "UNKNOWN"):
        print(f"  Expiration:  {expiration} ({dte} DTE)")
        print(f"  Max loss:    ${max_loss_str}")
        print(f"  Max gain:    ${max_gain_str if max_gain_str else 'Unlimited'}")

    # Log to audit trail - already guarded (unchanged from the original: a
    # storage hiccup here was never able to double-record via this path).
    try:
        log_trade(
            ticker=ticker,
            trade_date=state["trade_date"],
            strategy=strategy,
            underlying_signal=underlying_signal,
            iv_regime=iv_regime,
            expiration=expiration,
            dte=dte,
            net_debit_credit=float(net_dc.replace(",", "")) if net_dc else 0,
            max_loss=float(max_loss_str.replace(",", "")) if max_loss_str else 0,
            max_gain=float(max_gain_str.replace(",", "")) if max_gain_str else None,
            breakeven=float(breakeven_str.replace(",", "")) if breakeven_str else 0,
            rr_ratio=rr.strip()[:50],
            action_taken="",
            thesis_summary=_extract_thesis(state.get("investment_plan", "")),
        )
    except Exception as e:
        print(f"  [WARN] Trade log failed: {e}")

    # Open position if strategy is actionable
    if strategy in ("NO_TRADE", "UNKNOWN"):
        print(f"\n  Action: skipped (strategy is {strategy})")
        return

    # Guarded for the same reason as log_trade above: get_underlying_price()/
    # open_position_from_proposal() failing here is a pricing/storage problem,
    # not an agent-pipeline failure - it must not double-record this ticker's
    # outcome via main()'s outer except.
    try:
        spot = get_underlying_price(ticker) or 0
        open_result = open_position_from_proposal(
            ticker=ticker,
            proposal=proposal,
            iv_regime=iv_regime,
            underlying_at_entry=spot,
        )
        print(f"\n  Action: {open_result['action']}")
        if open_result["action"] == "opened":
            for i, leg in enumerate(open_result["legs"], 1):
                print(f"    Leg {i}: {leg['action']} {leg['qty']} {leg['type']} "
                      f"@ ${leg['strike']} for ${leg['entry_price']}")
            print(f"    Cost basis: ${open_result['cost_basis']:.2f}")
        elif "reason" in open_result:
            print(f"    Reason: {open_result['reason']}")
    except Exception as e:
        print(f"  [WARN] Position open failed: {e}")


def main():
    args = sys.argv[1:]
    report_only = "--report-only" in args
    check_only = "--check-only" in args
    args = [a for a in args if not a.startswith("--")]

    section("OPTIONS PAPER TRADING DAILY RUNNER")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if report_only:
        print_report()
        return

    # Clear pricing cache for fresh run
    clear_cache()

    # Step 1 - Close positions hitting triggers
    section("STEP 1 - Checking options positions for close triggers")
    positions_before = get_open_positions()
    print(f"  Open positions: {len(positions_before)}")
    closure_summary = check_and_close_positions()
    print(f"  Checked {closure_summary['checked']}, "
          f"closed {closure_summary['closed']}, "
          f"realized P&L ${closure_summary['total_pnl']:+.2f}")
    for c in closure_summary["closures"]:
        print(f"    CLOSED {c['ticker']} {c['strategy']}: "
              f"${c['pnl_dollars']:+.2f} ({c['pnl_pct']:+.2f}%) "
              f"[{c['close_reason']}]")

    if check_only:
        section("Skipping new trades (--check-only)")
        print_report()
        return

    # Step 2 - Process watchlist
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
    tracker.check_and_alert(run_name="options", equity=total_equity)

    # Step 4 - Report
    print_report()


if __name__ == "__main__":
    main()
