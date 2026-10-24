#!/usr/bin/env python3
"""
outage_alert.py - silent-failure detector for the RUTHLESS trading runners.

THE PROBLEM this solves:
An OpenAI API outage (credit_balance_exhausted / insufficient_quota) makes EVERY
research agent fail on EVERY ticker, so every signal comes back UNKNOWN and gets
skipped. But the run still LOOKS normal - equity snapshot generates, positions get
monitored - so a whole day of zero signals passes silently. You only notice when
you go looking. This fires one alert the moment that pattern appears.

THE KEY DISTINCTION (avoids false alarms):
  - Zero signals because the API is DEAD  -> errors/UNKNOWNs  -> ALERT
  - Zero signals because it's a HOLD day   -> valid HOLD calls -> STAY SILENT
A quiet market where every ticker legitimately holds is NOT an outage. The detector
counts HOW tickers failed, not just that no trades opened.

HOW TO WIRE IT IN (minimal, no changes to agent logic):
  As each ticker is processed, record its outcome:
      tracker.record("AAPL", "signal")     # a real BUY/SELL/signal produced
      tracker.record("MSFT", "hold")        # a clean, valid HOLD/NO_TRADE
      tracker.record("NVDA", "error", "credit_balance_exhausted")  # agent failed
      tracker.record("TSLA", "unknown")     # signal came back UNKNOWN/None
  At end of run:
      tracker.check_and_alert(run_name="stock")   # fires alert if outage detected

Alerts print to stdout AND (optionally) send to a channel you configure. It NEVER
places or changes a trade - it only warns. Signal-only, same as live_monitor.
"""
import os
import json
import datetime
from collections import Counter


# outcomes that mean "the agent could not produce a real decision" (outage signature)
FAILED_OUTCOMES = {"error", "unknown"}
# outcomes that mean "the agent worked and made a real call" (healthy, incl. quiet days)
HEALTHY_OUTCOMES = {"signal", "hold"}

# error strings that specifically indicate an API/billing outage (vs. a one-off ticker error)
OUTAGE_ERROR_MARKERS = (
    "credit_balance_exhausted", "insufficient_quota", "no credits remaining",
    "rate_limit", "quota", "exceeded your current quota", "billing",
)


class RunTracker:
    """Records per-ticker outcomes for one run and decides if it was an outage."""

    def __init__(self, fail_threshold_pct: float = 80.0):
        # if >= this % of tickers failed (error/unknown), treat as an outage
        self.fail_threshold_pct = fail_threshold_pct
        self.results = []   # list of (ticker, outcome, detail)

    def record(self, ticker: str, outcome: str, detail: str = "") -> None:
        outcome = outcome.strip().lower()
        self.results.append((ticker, outcome, detail))

    def summary(self) -> dict:
        total = len(self.results)
        outcomes = Counter(o for _, o, _ in self.results)
        failed = sum(outcomes[o] for o in FAILED_OUTCOMES)
        healthy = sum(outcomes[o] for o in HEALTHY_OUTCOMES)
        fail_pct = (failed / total * 100) if total else 0.0

        # does any failure detail match a known outage marker?
        details = " ".join(d.lower() for _, _, d in self.results if d)
        outage_marker = next((m for m in OUTAGE_ERROR_MARKERS if m in details), None)

        return {
            "total_tickers": total,
            "signals": outcomes.get("signal", 0),
            "holds": outcomes.get("hold", 0),
            "errors": outcomes.get("error", 0),
            "unknowns": outcomes.get("unknown", 0),
            "failed": failed,
            "healthy": healthy,
            "fail_pct": round(fail_pct, 1),
            "outage_marker": outage_marker,
        }

    def is_outage(self) -> bool:
        """
        Outage = a broad, correlated failure, NOT a quiet HOLD day.
        Two ways to trip it:
          1. failure rate >= threshold (e.g. 80%+ of tickers errored/unknown), OR
          2. a known billing/quota error marker appears AND failures aren't isolated
             (more than one ticker failed - a single-ticker blip isn't an outage).
        A run where every ticker cleanly HELD has fail_pct 0 -> never an outage.
        """
        s = self.summary()
        if s["total_tickers"] == 0:
            return False
        if s["fail_pct"] >= self.fail_threshold_pct:
            return True
        if s["outage_marker"] and s["failed"] >= 2:
            return True
        return False

    def check_and_alert(self, run_name: str = "run", equity: float = None) -> bool:
        """Check the run; if it's an outage, fire the alert. Returns True if alerted."""
        s = self.summary()
        if not self.is_outage():
            # healthy run (including a legitimately quiet HOLD day) - say nothing loud
            print(f"[outage-check] {run_name}: OK - {s['signals']} signals, {s['holds']} holds, "
                  f"{s['failed']}/{s['total_tickers']} failed ({s['fail_pct']}%). No outage.")
            return False

        msg = self._format_alert(run_name, s, equity)
        print(msg)                 # always to stdout / log
        _send_external(msg)        # optional channel (Telegram/email/file), if configured
        return True

    def _format_alert(self, run_name, s, equity) -> str:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cause = s["outage_marker"] or "broad agent failure"
        lines = [
            "",
            "!!! TRADING SYSTEM OUTAGE ALERT !!!",
            f"  Run:     {run_name}   ({ts})",
            f"  Signal:  {s['failed']}/{s['total_tickers']} tickers FAILED ({s['fail_pct']}%) "
            f"- {s['errors']} errors, {s['unknowns']} unknown",
            f"  Likely cause: {cause}",
            f"  Real signals produced: {s['signals']}   (a whole run's signals may be lost)",
        ]
        if equity is not None:
            lines.append(f"  Equity snapshot still ran (${equity:,.2f}) - the run LOOKS normal, but isn't.")
        lines += [
            "  ACTION:",
            "   1. Check API billing at platform.openai.com/settings/organization/billing/overview",
            "      (the API PLATFORM balance - NOT chatgpt.com wallet; they are separate accounts).",
            "   2. Confirm with a direct test call before trusting the dashboard (it can lag).",
            "   3. After fixing, run with --check-only before the next scheduled run opens positions,",
            "      since no real signals fired for these tickers during the gap.",
            "!!!" + "-" * 40,
            "",
        ]
        return "\n".join(lines)


# -- optional external notification (configure via env; no-op if unset) --
def _send_external(message: str) -> None:
    """
    Sends the alert somewhere you'll actually see it. All optional - if no env
    vars are set, it just writes a local flag file so a dashboard can pick it up.
    Never raises; a broken alert channel must not crash the trading run.
    """
    # 1. always drop a local flag file the dashboard/next run can read
    try:
        flag = os.getenv("OUTAGE_FLAG_FILE", "outage_alert.flag")
        with open(flag, "w", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass

    # 2. Telegram, if configured (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat:
        try:
            import urllib.request, urllib.parse
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat, "text": message}).encode()
            urllib.request.urlopen(url, data=data, timeout=10)
        except Exception:
            pass  # never let a failed alert break the run


# -- helper: classify a raw agent result string into an outcome --
def classify(result_text: str) -> str:
    """
    Map a raw agent output/error into one of: signal / hold / error / unknown.
    Use this if your runner has raw text rather than clean outcomes.
    """
    t = (result_text or "").lower()
    if any(m in t for m in OUTAGE_ERROR_MARKERS) or "error" in t or "exception" in t:
        return "error"
    if "unknown" in t or t.strip() in ("", "none"):
        return "unknown"
    if any(k in t for k in ("buy", "sell", "long_call", "long_put", "signal")):
        return "signal"
    if any(k in t for k in ("hold", "no_trade", "skip", "wait")):
        return "hold"
    return "unknown"


if __name__ == "__main__":
    # -- DEMO: the two cases that must behave oppositely --
    print("=== CASE 1: real outage (every ticker hit credit_balance_exhausted) ===")
    t1 = RunTracker()
    for tk in ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META"]:
        t1.record(tk, "error", "credit_balance_exhausted")
    t1.check_and_alert(run_name="stock", equity=104_947.00)

    print("\n=== CASE 2: quiet HOLD day (API fine, everyone legitimately held) ===")
    t2 = RunTracker()
    for tk in ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META"]:
        t2.record(tk, "hold")
    t2.check_and_alert(run_name="stock", equity=104_947.00)

    print("\n=== CASE 3: healthy run with a real trade + one isolated ticker error ===")
    t3 = RunTracker()
    t3.record("AAPL", "signal")
    t3.record("MSFT", "hold"); t3.record("NVDA", "hold"); t3.record("TSLA", "hold")
    t3.record("GOOGL", "error", "timeout")   # one blip, not an outage
    t3.record("AMZN", "hold"); t3.record("META", "hold")
    t3.check_and_alert(run_name="stock", equity=105_299.74)
