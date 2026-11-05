# outage_alert.py — silent-failure guard for the RUTHLESS trading runners

Belongs to a separate local project (`C:\trading_system\` — a multi-agent
LangGraph stock/options paper-trading system), not the RUTHLESS TRADING GOLD
portfolio the rest of `/builds/` tracks. Added here at the user's explicit
request ("commit and push, give me the merge link") since that's the only
git-backed home this session has access to — see the Decisions note at the
bottom before assuming this sets a pattern for future unrelated uploads.

## What it does

Catches the exact failure the user hit: an OpenAI API outage
(`credit_balance_exhausted` / `insufficient_quota`) makes every research agent
fail on every ticker, so every signal comes back UNKNOWN and gets skipped —
but the run still LOOKS normal (equity snapshot generates, positions get
monitored). A whole day of zero signals passes silently. This fires one alert
the moment that pattern appears, and **stays silent on a normal quiet day**
where every ticker legitimately holds.

It never touches a trade — detect-and-warn only.

## Install (30 seconds)

1. Drop `outage_alert.py` into `C:\trading_system\` (next to your runners).
2. Wire the three touch points below into BOTH `papertrade_run.py` and
   `options_papertrade_run.py`.

## The three touch points

### (1) Top of the run — create the tracker

```python
from outage_alert import RunTracker
tracker = RunTracker()          # default: alerts if >=80% of tickers fail
```

### (2) Inside your per-ticker loop — record each outcome

Map whatever your loop produces to one of: `signal` / `hold` / `error` / `unknown`.

```python
tracker.record(ticker, "signal")                          # a real BUY/SELL/LONG_CALL etc.
tracker.record(ticker, "hold")                             # a clean, valid HOLD / NO_TRADE
tracker.record(ticker, "error", str(err))                  # the agent threw / API errored
tracker.record(ticker, "unknown")                          # signal came back UNKNOWN / None
```

If your loop only has raw result text, use the built-in classifier instead:

```python
from outage_alert import classify
tracker.record(ticker, classify(raw_result_text))
```

### (3) End of the run — after the equity snapshot — check and alert

```python
tracker.check_and_alert(run_name="stock", equity=total_equity)     # in papertrade_run.py
tracker.check_and_alert(run_name="options", equity=total_equity)   # in options_papertrade_run.py
```

Optional Telegram alerts: set `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` env
vars. Unset = silently skipped; the flag file (`outage_alert.flag`) always
gets written on an alert regardless.

## Review of the actual wiring (this round's task)

The user manually wired `outage_alert.py` into `papertrade_run.py` and
`options_papertrade_run.py` and asked for a check against the three touch
points above, confirmation that the `record()` mapping matched each runner's
real variables (`parsed['signal']` for stocks, `strategy` for options), a
`--report-only` smoke test on both, and a fix for anything wrong.

**What was checked and how**, stated plainly since the two runners depend on
this local project's own `agent_state`, `agents.*`, `papertrade.*`,
`options_agents.*`, and `options_papertrade.*` modules — none of which exist
in this sandbox, so nothing here could actually *execute* the pipelines:

- **Touch points 1 and 3**: correct in both files as pasted. `RunTracker()`
  is created once per run (module-level, before any ticker processing) and
  `check_and_alert()` fires after the Step 3 equity snapshot, before the
  final report — in both `--report-only` and `--check-only` modes the
  function returns before ever touching the tracker, which is correct (no
  new outcomes were recorded, so there's nothing to check).
- **Touch point 2 / outcome mapping**: correct in both files.
  - Stock runner: `parsed.get("signal")` — `"BUY"/"SELL"` → `"signal"`,
    `"HOLD"` → `"hold"`, anything else (including a broken pipeline that
    never set `final_trade_decision`) falls through to `classify()` on the
    raw decision text, which correctly resolves an empty/missing decision to
    `"unknown"`.
  - Options runner: `state.get("options_strategy", "UNKNOWN")` —
    `"UNKNOWN"` → `"unknown"`, `"NO_TRADE"` → `"hold"`, any real strategy
    name → `"signal"`. A failed Layer 7 (`strategy_selector_node` raises)
    correctly falls back to `"UNKNOWN"` since the key is never set on that
    path, matching how a failed agent should register.
- **A real bug found and fixed, not by running the code (couldn't) but by
  tracing the control flow and then proving the failure mode standalone**:
  in both files, `tracker.record(...)` fires early in `process_ticker()`,
  but the *unguarded* calls after it — `log_trade(...)` and
  `open_position_from_decision(...)` in the stock runner;
  `get_underlying_price(...)` and `open_position_from_proposal(...)` in the
  options runner — sit inside the same function that `main()` wraps in a
  blanket `try/except`. If either call raised for a reason that has nothing
  to do with the trading pipeline (a CSV write failing, a storage-layer
  429), `main()`'s except block would record a **second** outcome for that
  same ticker as `"error"`, inflating the failure count that
  `is_outage()` uses. Reproduced standalone against the real
  `outage_alert.py` (no runner dependencies needed for this part): a
  perfectly healthy 5-ticker HOLD day, with 2 tickers' `log_trade()` hitting
  an unrelated `"storage backend: rate_limit exceeded"` exception, false-
  triggered a full outage alert — because `"rate_limit"` matches
  `OUTAGE_ERROR_MARKERS` and 2 duplicate error records clears the
  `outage_marker AND failed >= 2` condition, even though 0 actual signals
  failed. This directly undermines the tool's own stated design goal ("so
  you can trust the alert when it fires").

  **Fix applied** (both files): wrapped the log/open-position calls in their
  own `try/except` that prints a `[WARN]` and does *not* re-raise, so a
  bookkeeping failure downstream of the outage-relevant outcome can never
  reach `main()`'s per-ticker except and double-record. The options runner's
  `log_trade` call was already guarded this way in the original; only its
  `get_underlying_price`/`open_position_from_proposal` block needed the same
  treatment. Verified two ways:
  1. `python3 -m py_compile` on all three files — clean, both before and
     after the fix (the diff is exactly the two `try/except` wraps, nothing
     else touched).
  2. A standalone integration-style test replicating the fixed
     `process_ticker()` control flow (stubbed `parse_pm_decision`/
     `log_trade`/`open_position_from_decision`, real `outage_alert.py`)
     against the exact scenario above — after the fix, all 5 tickers record
     exactly once, the storage errors surface as `[WARN]` lines, and
     `check_and_alert()` correctly stays silent. Asserted directly, not
     eyeballed.
  3. `outage_alert.py` itself was run for real (it has zero external
     dependencies — stdlib only) via its own `__main__` demo block: outage
     case alerts, quiet-HOLD-day case stays silent, isolated-single-error
     case stays silent. All three matched the file's own stated design.

- **Real run against the actual runners — confirmed by the user**: this
  sandbox has none of `agent_state.py`, `agents/`, `papertrade/`,
  `options_agents/`, `options_papertrade/`, or `tickers.txt` — the real
  trading-system codebase lives only on the user's machine at
  `C:\trading_system\` — so `--report-only` couldn't be run here, and this
  README said so plainly rather than faking it. The user then ran both
  fixed runners for real (a full 13-ticker run, stronger evidence than
  `--report-only` would have been, since it exercises the whole pipeline
  including `record()` and `check_and_alert()`) and pasted the output:
  - Stock runner: 11 signals + 2 holds (HYG, GLD) = 13 tickers exactly,
    `[outage-check] stock: OK - 11 signals, 2 holds, 0/13 failed (0.0%).
    No outage.` — the count matches the ticker list exactly, confirming no
    double-record occurred.
  - Options runner: 7 signals + 6 holds (NO_TRADE) = 13 tickers exactly,
    `[outage-check] options: OK - 7 signals, 6 holds, 0/13 failed (0.0%).
    No outage.` — same exact-match confirmation.
  - No `[WARN] Trade log failed` / `[WARN] Position open failed` lines
    appeared in either run, meaning the double-record guard added by the
    fix wasn't exercised by an actual downstream failure this time — the
    real-world proof that a genuine bookkeeping failure gets caught by the
    guard instead of double-counting is still only the standalone test
    above, not this live run. Worth a deliberate real-failure test later
    (e.g. temporarily pointing `trades.csv` at a read-only path) if that
    guard needs to be trusted under fire rather than just in theory.

## Files

| File | Role |
|---|---|
| `outage_alert.py` | The detector itself — unmodified from what the user provided, run for real in this sandbox (see above) |
| `papertrade_run.py` | Stock paper-trading runner, as provided, with the double-record fix applied |
| `options_papertrade_run.py` | Options paper-trading runner, as provided, with the same fix applied |

## Decisions log

- 2026-09-25 — Added to `/builds/` at the user's explicit request despite
  belonging to an entirely separate local project (`C:\trading_system\`),
  since this is the only git-backed environment available to act on
  "commit and push, give me the merge link." This is a genuinely different
  kind of build from everything else in this portfolio (a multi-agent
  LangGraph stock/options trading system vs. this project's own
  self-contained RUTHLESS TRADING GOLD scripts) and depends on modules this
  sandbox has never seen — flagged explicitly rather than treated as a new
  standing pattern for this repo.
