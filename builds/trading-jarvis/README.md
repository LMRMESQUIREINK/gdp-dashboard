# ♛ Trading Jarvis — Pro build

A Claude-powered trading assistant: reasoning core (Claude API) + tool-calling
over live market data + signal generation + risk sizing. Built from an
uploaded 5-file bundle (`data_pipeline.py`, `jarvis_orchestrator.py`,
`live_monitor.py`, `README3.md`, `run_strategy1.py`) whose own README
documented **six** files — `signal_generator.py` and `risk_manager.py` were
missing, so nothing in the original upload could even import. This build
completes it and fixes what deep analysis found along the way.

Full writeup: `/notes/trading-jarvis-analysis.md`.

## Files

| File | Role |
|---|---|
| `data_pipeline.py` | EODHD/FMP fetch + local cache; now exposes real OHLCV, not just closes |
| `signal_generator.py` | **New.** RSI-cross + volume-confirmation signal, lookahead-safe |
| `risk_manager.py` | **New.** ATR stop, fixed-fractional sizing, single-trade heat check |
| `live_monitor.py` | Polling loop → signal → alert. **Never places an order.** |
| `jarvis_orchestrator.py` | Claude API tool-calling front end over the above |
| `run_strategy.py` | CLI entry point — one-shot check, live monitor, or NL query |

## What changed from the uploaded bundle

| Problem found | Fix |
|---|---|
| `signal_generator.py` / `risk_manager.py` referenced everywhere, uploaded nowhere — the system couldn't import | Both written from the call signatures every other file already expected |
| `get_recent_closes()` returned only prices; every caller fabricated high/low/volume (`high = close*1.01`, `volume = 1_500_000` constant) — breaking ATR stops and volume confirmation | New `get_recent_ohlcv()` returns the real frame `fetch_eod()` already had |
| `jarvis_orchestrator.py` hardcoded `MODEL = "claude-sonnet-4-6"`, no override | Defaults to `claude-opus-5`, overridable via `JARVIS_MODEL` env var |
| A placeholder API key (`"YOUR_EODHD_KEY"`) went straight to the network, failing as a confusing remote 401/403 | Fails locally and immediately with a clear message before any request |
| `pip install ... --break-system-packages`, no `requirements.txt` | Isolated `.venv` + exact pinned `requirements.txt` |
| `live_monitor.py` could fail every poll forever on a persistent error (e.g. bad key), printing the same error indefinitely | Stops after `max_consecutive_errors` (default 5) with a clear message |
| "Portfolio heat" implied multi-position awareness a stateless per-symbol call can't have | Documented honestly as single-trade risk; `reason` field explains every approve/reject |
| `run_strategy1.py` filename didn't match the README's documented `run_strategy.py` | Renamed |

Everything that was already good is untouched: no `execute_order` tool
anywhere in this codebase, text-first (no voice), every signal framed as
"review required" not an instruction, and the Claude system prompt refuses
to treat a BUY signal as a trade order.

## What's deliberately out of scope, and why

**Voice input.** A misheard ticker, size, or direction is a real failure
mode the moment the next step touches money. Add a transcription layer on
top of `jarvis_orchestrator.py`'s text interface once you trust the
pipeline underneath it — don't let voice be the first untested layer
between a user and their capital.

**Live trade execution.** No `execute_order` tool exists anywhere in this
codebase, by design. Every "BUY" the system produces is a suggestion with a
computed size and stop attached — a human decision, not an automated one.
If you build a broker integration on top of this, put a mandatory
confirmation step between Jarvis's suggestion and the API call, and don't
let that step get automated away later for convenience.

**Multi-position portfolio heat.** `risk_manager.evaluate_trade()` checks
one symbol at a time and has no memory of other open positions. The
`heat_pct` it reports is this trade's own risk as a % of equity — a real
and useful number, but not a whole-portfolio view. Add position tracking
before relying on it as one.

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
```
(Windows: `run_jarvis.bat` with the same arguments.)

## Hard rules baked into this build

1. `signal_generator.py` only signals off completed bars — feed it EOD/
   completed-bar data, not an in-progress live tick.
2. `check_risk` / `evaluate_trade` never fires for a symbol without a live
   BUY signal (enforced in the Jarvis system prompt).
3. Trade risk over 5% of equity is always flagged, never silently allowed.
4. No component in this repo can place an order. That is a feature, not a
   gap to close by default.

## Verification status

Proven in this build environment, without live EODHD/FMP/Anthropic keys
(this sandbox's network policy blocks those domains — see
`/notes/trading-jarvis-analysis.md` and the parent conversation for the
egress-policy details):

- Fresh pinned-venv install of `requirements.txt` imports cleanly.
- `signal_generator.generate_signals()` / `latest_signal()` produce
  correct BUY/SELL/HOLD on synthetic OHLCV data, including a
  volume-confirmed RSI breakout.
- `risk_manager.evaluate_trade()` returns the exact contract every caller
  expects, correctly gates on the heat limit, and fails safely (0 shares,
  not approved) on a zero-ATR edge case.
- `jarvis_orchestrator._run_tool()` dispatch and `ask_jarvis()`'s
  tool-call loop, proven against a mocked Anthropic client and mocked
  data fetch (no real network/API key involved).
- `data_pipeline.fetch_eod()` fails fast and locally on a missing/
  placeholder API key, before any request goes out.
- `run_strategy.py --help` and the CLI argument surface.

**Not yet run against live EODHD/FMP/Anthropic APIs from this
environment** — that needs a real API key and a network path this sandbox
doesn't have. Run it on your own machine and it'll have normal internet
access.
