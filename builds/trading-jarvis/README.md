# ♛ Trading Jarvis — Pro build

A Claude-powered trading assistant: reasoning core (Claude API) + tool-calling
over live market data + signal generation + risk sizing.

Built and corrected across two upload rounds. Round 1 (`data_pipeline.py`,
`jarvis_orchestrator.py`, `live_monitor.py`, `README3.md`, `run_strategy1.py`)
was missing `signal_generator.py` and `risk_manager.py` entirely — nothing
could import. Round 2 supplied the **actual** `risk_manager.py`, which turned
out to have a different, more capable design than the from-spec version this
build originally wrote in its place (genuine multi-position portfolio heat
via `existing_positions`, an `r_multiple_target` field, EWM-based ATR). This
build now uses the real file, fixes the one real bug in it, writes
`signal_generator.py` to match its conventions, and wires up the
`existing_positions` capability that was built but never fed real data.

Full writeup: `/notes/trading-jarvis-analysis.md`.

## Files

| File | Role |
|---|---|
| `data_pipeline.py` | EODHD/FMP fetch + local cache; exposes real OHLCV, not just closes |
| `signal_generator.py` | **Written for this build.** RSI-cross + volume-confirmation signal |
| `risk_manager.py` | **The actual uploaded file**, with one schema-consistency fix (see below) |
| `positions_store.py` | **New.** Local open-positions ledger — the missing wire into `existing_positions` |
| `live_monitor.py` | Polling loop → signal → alert. **Never places an order.** |
| `jarvis_orchestrator.py` | Claude API tool-calling front end over the above |
| `run_strategy.py` | CLI entry point — one-shot check, live monitor, NL query, or position tracking |

## What changed, across both rounds

| Problem found | Fix |
|---|---|
| `signal_generator.py` / `risk_manager.py` referenced everywhere, uploaded nowhere in round 1 — the system couldn't import | Both written; round 2 then supplied the real `risk_manager.py`, which replaced the from-spec version |
| `get_recent_closes()` returned only prices; every caller fabricated high/low/volume (`high = close*1.01`, `volume = 1_500_000` constant) — breaking ATR stops and volume confirmation | New `get_recent_ohlcv()` returns the real frame `fetch_eod()` already had |
| `jarvis_orchestrator.py` hardcoded `MODEL = "claude-sonnet-4-6"`, no override | Defaults to `claude-opus-5`, overridable via `JARVIS_MODEL` env var |
| A placeholder API key (`"YOUR_EODHD_KEY"`) went straight to the network, failing as a confusing remote 401/403 | Fails locally and immediately with a clear message before any request |
| `pip install ... --break-system-packages`, no `requirements.txt` | Isolated `.venv` + exact pinned `requirements.txt` |
| `live_monitor.py` could fail every poll forever on a persistent error (e.g. bad key), printing the same error indefinitely | Stops after `max_consecutive_errors` (default 5) with a clear message |
| `run_strategy1.py` filename didn't match the README's documented `run_strategy.py` | Renamed |
| **(round 2)** `risk_manager.size_position()`'s zero-risk-distance branch returned a different key set than the normal branch (no `r_multiple_target`, a `warning` key meaning something else than `portfolio_heat`'s) | Both branches now return the same keys; the zero-risk message moved to `error` |
| **(round 2)** `live_monitor.py` referenced `risk_check['portfolio_heat']['reason']` — a key that doesn't exist in the real `risk_manager.py`; would have crashed with `KeyError` the first time a signal got risk-gated | Fixed to read the real keys (`heat_pct`/`warning`/`sizing.error`) |
| **(round 2)** `evaluate_trade()`'s `existing_positions` parameter is genuinely multi-position-capable, but no caller ever passed anything — heat was single-trade-only in practice despite the capability existing | Added `positions_store.py` + `run_strategy.py --add-position/--positions/--remove-position`; `check_risk` and `live_monitor` now pass real recorded positions |

Everything that was already good is untouched: no `execute_order` tool
anywhere in this codebase, text-first (no voice), every signal framed as
"review required" not an instruction, and the Claude system prompt refuses
to treat a BUY signal as a trade order. Recording a position is always an
explicit, human-typed command — never inferred from a signal or an
"approved" risk check (see `positions_store.py`'s docstring).

## What's deliberately out of scope, and why

**Voice input.** A misheard ticker, size, or direction is a real failure
mode the moment the next step touches money. Add a transcription layer on
top of `jarvis_orchestrator.py`'s text interface once you trust the
pipeline underneath it — don't let voice be the first untested layer
between a user and their capital.

**Live trade execution.** No `execute_order` tool exists anywhere in this
codebase, by design. Every "BUY" the system produces is a suggestion with a
computed size, stop, and 2R target attached — a human decision, not an
automated one. If you build a broker integration on top of this, put a
mandatory confirmation step between Jarvis's suggestion and the API call,
and don't let that step get automated away later for convenience.

## Setup

**macOS / Linux:**
```bash
chmod +x setup_venv.sh run_jarvis.sh   # once
./setup_venv.sh
export EODHD_API_KEY="your_key_here"
export FMP_API_KEY="your_key_here"
export ANTHROPIC_API_KEY="your_key_here"
```

**Windows:**
```
setup_venv.bat
setx EODHD_API_KEY "your_key_here"
setx FMP_API_KEY "your_key_here"
setx ANTHROPIC_API_KEY "your_key_here"
```
(restart your terminal after `setx` so the new values are picked up)

Optional: `JARVIS_MODEL` to pin a specific Claude model (defaults to
`claude-opus-5`).

## Run it

```bash
./run_jarvis.sh AAPL.US                       # one-shot signal + risk check
./run_jarvis.sh AAPL.US --monitor             # live polling monitor (signal-only)
./run_jarvis.sh --ask "Check MSFT for a buy signal at 1% risk"   # Jarvis NL mode

# Track positions you already took elsewhere, so portfolio heat is real:
./run_jarvis.sh --add-position AAPL.US 100 150.25 145.00
./run_jarvis.sh --positions
./run_jarvis.sh --remove-position AAPL.US
```
(Windows: `run_jarvis.bat` with the same arguments.)

## Hard rules baked into this build

1. `signal_generator.py` only signals off completed bars — feed it EOD/
   completed-bar data, not an in-progress live tick.
2. `check_risk` / `evaluate_trade` never fires for a symbol without a live
   BUY signal (enforced in the Jarvis system prompt).
3. Portfolio heat over 5% is always flagged, never silently allowed —
   and now actually reflects recorded open positions, not just the trade
   being checked.
4. No component in this repo can place an order, and no component ever
   records a position on its own — `--add-position` is always a human,
   typed, after-the-fact command.

## Verification status

Proven in this build environment, without live EODHD/FMP/Anthropic keys
(this sandbox's network policy blocks those domains — see
`/notes/trading-jarvis-analysis.md`):

- Fresh pinned-venv install of `requirements.txt` imports cleanly.
- `signal_generator.generate_signals()` / `latest_signal()` produce
  correct BUY/SELL/HOLD on synthetic OHLCV, including a volume-confirmed
  RSI breakout.
- The real `risk_manager.evaluate_trade()` returns a consistent schema on
  both the normal and zero-ATR edge-case branches, correctly gates on the
  5% heat limit, and — with `positions_store.py` wired in — genuinely
  raises heat when another recorded position is factored in (verified:
  adding a second position pushed heat from 0.99% to 5.99% and flipped
  the warning).
- `run_strategy.py --add-position/--positions/--remove-position` proven
  end-to-end (add two, list, remove one, list again) with real file
  persistence.
- `run_strategy.run_once()`'s full BUY-signal print path (signal, RSI,
  shares, stop, 2R target, multi-position heat) exercised against
  synthetic data engineered to land a BUY on the latest bar.
- `jarvis_orchestrator._run_tool()` dispatch, `ask_jarvis()`'s tool-call
  loop, and `check_risk`'s positions wiring, proven against a mocked
  Anthropic client and mocked data fetch (no real network/API key
  involved).
- `data_pipeline.fetch_eod()` fails fast and locally on a missing/
  placeholder API key, before any request goes out.

**Not yet run against live EODHD/FMP/Anthropic APIs from this
environment** — that needs a real API key and a network path this sandbox
doesn't have. Run it on your own machine and it'll have normal internet
access.
