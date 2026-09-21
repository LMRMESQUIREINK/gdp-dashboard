# ♛ Trading Jarvis × Swamp Intelligence — Pro build

A Claude-powered trading assistant: reasoning core (Claude API) + tool-calling
over live market data + signal generation + risk sizing, now with a Swamp
Intelligence reasoning/governance layer that decomposes every objective into
an explicit Task Tree with a hard-enforced human-approval gate before any
risk-bearing step.

Built and corrected across three upload rounds:

- **Round 1**: `data_pipeline.py`, `jarvis_orchestrator.py`, `live_monitor.py`,
  a README, `run_strategy1.py`. `signal_generator.py` and `risk_manager.py`
  were missing entirely — nothing could import.
- **Round 2**: supplied the **actual** `risk_manager.py`, more capable than
  the from-spec version this build had written in its place (genuine
  multi-position portfolio heat, an `r_multiple_target` field, EWM-based ATR).
- **Round 3**: added a new `jarvis_swamp_bridge.py` (governance/routing layer)
  and patched `jarvis_orchestrator.py`/`live_monitor.py`/`data_pipeline.py` —
  but the `swamp_intelligence` module it imports, plus the real
  `signal_generator.py` and `risk_manager.py`, weren't in that first upload.
  A second, mid-turn upload supplied all three directly, plus an HTML
  analysis dashboard from an earlier pass that predates them.

Full writeup, all three rounds: `/notes/trading-jarvis-analysis.md`.

## Files

| File | Role |
|---|---|
| `data_pipeline.py` | EODHD/FMP fetch + local cache; exposes real OHLCV, not just closes |
| `signal_generator.py` | **The actual uploaded file.** RSI-cross + volume-confirmation, single threshold for both entry and exit |
| `risk_manager.py` | **The actual uploaded file**, with one schema-consistency fix (see below) |
| `swamp_intelligence.py` | **The actual uploaded file.** Domain-agnostic Task Tree / Event Packet / governance-guard engine |
| `jarvis_swamp_bridge.py` | **The actual uploaded file**, hardened. Routes a Jarvis objective through Swamp Intelligence, then hands off to the real modules above |
| `positions_store.py` | Local open-positions ledger — the missing wire into `existing_positions` |
| `live_monitor.py` | Polling loop → signal → alert. **Never places an order.** |
| `jarvis_orchestrator.py` | Claude API tool-calling front end — now includes a `swamp_decompose` tool plus the three prop-firm tools below |
| `run_strategy.py` | CLI entry point — one-shot check, `--swamp` reasoning mode, live monitor, NL query, or position tracking |
| `prop_firm_sizing.py`, `prop_firm_position_sizing.py`, `prop_pass_simulator.py` | Copied in from `/builds/prop-firm-sizing/` (same files, unmodified) — TPT funded-account sizing, wired into `jarvis_orchestrator.py` as three separate tools, see below |

## What changed, across all three rounds

| Problem found | Fix |
|---|---|
| `signal_generator.py` / `risk_manager.py` referenced everywhere, uploaded nowhere in round 1 — the system couldn't import | Both written; later rounds supplied the real files, which replaced the from-spec versions |
| `get_recent_closes()` returned only prices; every caller fabricated high/low/volume — breaking ATR stops and volume confirmation | `get_recent_ohlcv()` returns the real frame `fetch_eod()` already had |
| `jarvis_orchestrator.py` hardcoded a stale `MODEL`, no override — reverted in a fresh round-3 upload that didn't carry this fix forward | Re-applied: defaults to `claude-opus-5`, overridable via `JARVIS_MODEL` |
| A placeholder API key went straight to the network, failing as a confusing remote 401/403 | Fails locally and immediately, before any request |
| `pip install ... --break-system-packages`, no `requirements.txt` | Isolated `.venv` + exact pinned `requirements.txt` |
| `live_monitor.py` could fail every poll forever on a persistent error | Stops after `max_consecutive_errors` (default 5) with a clear message |
| `risk_manager.size_position()`'s zero-risk-distance branch returned a different key set than the normal branch — reappeared unfixed in the round-3 upload of the same file | Both branches normalized to the same keys; the zero-risk message lives in `error` |
| `evaluate_trade()`'s `existing_positions` parameter is genuinely multi-position-capable, but no caller ever passed anything | `positions_store.py` + `run_strategy.py --add-position/--positions/--remove-position`; `check_risk`, `live_monitor`, and the swamp bridge all now pass real recorded positions |
| **(round 3)** `jarvis_swamp_bridge.py`'s self-test of `guard("bypass_approval")` swallowed the result either way — a future regression in the guard would have stayed silent | Now asserts the raise actually happened, matching the file's own pattern for the `step3.approval_required` check |
| **(round 3)** An HTML analysis dashboard flagged "RSI(65) — period or threshold, ambiguous" before `signal_generator.py` was available | Resolved by the real file: `rsi_period=14` and `rsi_threshold=65.0` are separate, unambiguous parameters |

Everything that was already good is untouched: no `execute_order` tool
anywhere in this codebase, text-first (no voice), every signal framed as
"review required" not an instruction, and both the Claude system prompt and
the Swamp Intelligence governance guard refuse to treat a BUY signal as a
trade order. Recording a position is always an explicit, human-typed
command — never inferred from a signal or an "approved" risk check.

## What Swamp Intelligence adds

`swamp_intelligence.py` is a small, domain-agnostic coordination engine:
given an objective, it builds a `TaskTree` of `Task` nodes (step, assigned
agent, priority, risk score, `approval_required`), and can emit each as an
`EventPacket`. `SwampIntelligence.guard()` raises for a fixed table of
prohibited actions (`execute_trade`, `place_order`, `execute_task`,
`bypass_approval`, `bypass_bus`) — the layer's core directive is that it
**thinks, structures, and routes; it never executes.**

`jarvis_swamp_bridge.py` is the trading-specific tenant: it decomposes
"check `<symbol>` for a signal at `<risk_pct>`% risk" into a 4-step tree
(Fetch → Signal → Risk → Human Approval), with `approval_required=True`
hard-coded on both the risk-sizing and approval steps, then hands off to the
real `data_pipeline`/`signal_generator`/`risk_manager` modules — Swamp
Intelligence itself never touches them directly.

Reach it via `run_strategy.py --swamp`, or inside a natural-language
`--ask` query — `jarvis_orchestrator.py`'s system prompt now calls
`swamp_decompose` first, before `check_signal`/`check_risk`, so the same
Task Tree and Event Packets show up in NL answers too.

One honest note, not a bug: `swamp_intelligence.py`'s `ActivationGate`
(meant to decide whether a task is complex enough to warrant this layer at
all) needs a tree's step count as input — so it can only ever be used
*after* a tree already exists, not to decide *whether* to build one.
Nothing currently calls it; `jarvis_orchestrator.py` routes every symbol
check through Swamp Intelligence unconditionally instead.

**Checked against the actual Brain Spec (`01_brain/swamp_intelligence_core.md`)
once its full text became available** — see `/notes/trading-jarvis-analysis.md`,
Addendum 3, for the section-by-section comparison. Headline finding:
`EventPacket`'s fields and `Priority`'s values match the spec exactly, and
one real violation was caught and fixed — step 4's `risk_score` was `0`,
one below the spec's stated `1-100` floor; `Task` now validates that range
instead of just documenting it. `ActivationGate`'s dormancy turns out to be
expected, not a gap: Trading Jarvis only ever decomposes one objective
shape, so there's no complexity variance for it to gate. Several other spec
sections (dynamic approval-from-risk-threshold, dependency enforcement,
agent reassignment, revenue-ranked decision logic) have no corresponding
code — true of the uploaded file already, not a regression here, and
building them out for a single-objective-shape domain would be scope
expansion beyond what's needed, not a bug fix.

## Prop-firm account tools

Three tools from `/builds/prop-firm-sizing/` are wired into
`jarvis_orchestrator.py` as a fully separate flow from the EODHD/FMP
symbol-trading tools above — the system prompt tells Claude not to mix
the two: no `swamp_decompose`/`check_signal`/`check_risk` for a funded-
account sizing question, and no prop-firm tool for an ordinary symbol
question. Reachable two ways — through Claude (`--ask`) or directly via
CLI flags on `run_strategy.py`, no Anthropic key required for the latter:

- **`prop_firm_size_check`** / **`--prop-size-check`** — static,
  start-of-day check: point-risk at a given contract count, the
  25%-of-max-contracts rule, and an optional stop-room-vs-ADR check.
- **`prop_firm_session_report`** / **`--prop-session`** — the
  trailing-drawdown-aware live session state: the floor follows the
  high-water mark, not the starting balance (a good morning shrinks
  room, it doesn't grow it), plus a SAFE/WARNING/CRITICAL/BREACHED
  status. Use this over the static check whenever the user has given
  today's P&L.
- **`prop_firm_pass_probability`** / **`--prop-pass-prob`** — Monte
  Carlo eval pass probability, requiring the trader's own
  `avg_daily_pnl`/`daily_pnl_std` as input (never estimated by the tool,
  by Claude, or by the CLI).
- **`--prop-compare`** (CLI only — not a Claude tool) — wraps
  `compare_sizing_strategies()`, comparing pass probability across
  several contract sizes at once via one or more
  `--prop-compare-size CONTRACTS:AVG_PNL:PNL_STD` entries. Not exposed
  to Claude: its input is a `{contracts: (avg_pnl, pnl_std)}` dict,
  which fits a CLI's repeated-flag list better than a single-turn NL
  tool call.

The CLI flags reuse `SessionState.report()` and `PassSimulator.report()`
(including `compare_sizing_strategies()`) directly for output — same
formatting, same code path, as the tool functions Claude calls. A bad
`--prop-tier`/`--prop-symbol`/`--prop-compare-size` prints a one-line
plain-English error (valid tiers/symbols listed, or the expected
`CONTRACTS:AVG_PNL:PNL_STD` format) instead of a raw Python traceback.

Full source-document analysis these were built and cross-checked
against: `/notes/prop-firm-sizing-analysis.md`.

## What's deliberately out of scope, and why

**Voice input.** A misheard ticker, size, or direction is a real failure
mode the moment the next step touches money. Add a transcription layer on
top of `jarvis_orchestrator.py`'s text interface once you trust the
pipeline underneath it.

**Live trade execution.** No `execute_order` tool exists anywhere in this
codebase, by design — and Swamp Intelligence's own governance guard would
refuse `execute_trade`/`place_order`/`execute_task` even if one existed.
Every "BUY" the system produces is a suggestion with a computed size, stop,
and 2R target attached — a human decision, not an automated one.

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
./run_jarvis.sh AAPL.US --swamp               # route through Swamp Intelligence first
./run_jarvis.sh AAPL.US --monitor             # live polling monitor (signal-only)
./run_jarvis.sh --ask "Check MSFT for a buy signal at 1% risk"   # Jarvis NL mode (now Swamp-aware)

# Track positions you already took elsewhere, so portfolio heat is real:
./run_jarvis.sh --add-position AAPL.US 100 150.25 145.00
./run_jarvis.sh --positions
./run_jarvis.sh --remove-position AAPL.US

# Prop-firm account tools (TPT) — CLI access to the same three tools
# jarvis_orchestrator.py exposes to Claude, no Anthropic key needed:
./run_jarvis.sh --prop-size-check --prop-tier 50K --prop-contracts 1 --prop-adr 78
./run_jarvis.sh --prop-session --prop-tier 50K --prop-pnl 200 --prop-hwm 51500
./run_jarvis.sh --prop-pass-prob --prop-tier 50K --prop-balance 50800 \
    --prop-hwm 51200 --prop-days 8 --prop-avg-pnl 180 --prop-pnl-std 550
./run_jarvis.sh --prop-compare --prop-tier 50K --prop-balance 50000 --prop-hwm 50000 \
    --prop-days 11 --prop-compare-size 1:90:275 2:165:490 3:230:700 6:400:1400
```
(Windows: `run_jarvis.bat` with the same arguments.)

## Hard rules baked into this build

1. `signal_generator.py` only signals off completed bars — feed it EOD/
   completed-bar data, not an in-progress live tick.
2. `check_risk` / `evaluate_trade` never fires for a symbol without a live
   BUY signal — enforced in code (re-derived independently, not trusted
   from an earlier tool call), and structurally mirrored by
   `approval_required=True` on the risk-sizing step of every Swamp
   Intelligence Task Tree.
3. Portfolio heat over 5% is always flagged, never silently allowed — and
   reflects recorded open positions, not just the trade being checked.
4. No component in this repo can place an order, Swamp Intelligence's own
   governance guard refuses `execute_trade`/`place_order`/`execute_task`
   outright, and no component ever records a position on its own —
   `--add-position` is always a human, typed, after-the-fact command.

## Verification status

Proven in this build environment, without live EODHD/FMP/Anthropic keys
(this sandbox's network policy blocks those domains — see
`/notes/trading-jarvis-analysis.md`):

- Fresh pinned-venv install of `requirements.txt` imports cleanly.
- `swamp_intelligence`'s `TaskTree`/`EventPacket`/`guard()` proven directly
  — correctly raises `GovernanceError` for a prohibited action, correctly
  allows an unlisted one.
- The hardened self-test in `jarvis_swamp_bridge.route_through_bus()`
  proven to actually catch a simulated broken guard, not just demonstrate
  a working one.
- `signal_generator.generate_signals()` produces the real `vol_confirm`
  column and correct BUY/SELL/HOLD via the single-threshold RSI-cross
  design, on synthetic OHLCV.
- The real `risk_manager.evaluate_trade()` returns a consistent schema on
  both the normal and zero-ATR edge-case branches.
- **Full end-to-end run of `jarvis_swamp_bridge.route_through_bus()`**
  against synthetic data engineered to land a real BUY on the latest bar:
  Task Tree rendered, all 4 Event Packets emitted, real signal computed
  with volume confirmation True, real ATR-sized suggestion (shares, stop,
  2R target, portfolio heat) printed, human-approval step reached.
- `jarvis_orchestrator._run_tool()` proven for all four tools including
  the new `swamp_decompose`, and `check_risk`'s code-level gate proven to
  correctly refuse a non-BUY signal rather than trusting the caller.
- The three prop-firm tools proven directly via `_run_tool()` — including
  the exact "peaked at $51,500 then gave back to $50,200" trailing-DD
  scenario (floor correctly at $49,500, `WARNING` status) and a Monte
  Carlo pass-probability call, both matching the standalone
  `/builds/prop-firm-sizing/` toolkit's own verified output — then proven
  again through the **full `ask_jarvis()` tool-dispatch loop** with a
  mocked Anthropic client: Claude "calls" `prop_firm_session_report`,
  the real computation runs, the JSON result round-trips back through
  `messages`, and the mocked second turn asserts the correct numbers
  arrived before producing a final answer.
- `run_strategy.py --add-position/--positions/--remove-position` and
  `--help` (now showing `--swamp`/`--equity`/`--risk-pct` too) proven
  end-to-end.
- `run_strategy.py --prop-size-check/--prop-session/--prop-pass-prob`
  proven as real subprocess CLI calls (not just direct function calls):
  all three reproduce the standalone `/builds/prop-firm-sizing/`
  toolkit's exact previously-verified numbers, `--help` renders all the
  new flags correctly, missing-required-flag calls produce a clean
  `argparse` error naming exactly what's missing, and an invalid
  `--prop-tier`/`--prop-symbol` — which initially surfaced as a raw
  Python traceback — was caught and fixed to print a one-line
  plain-English error listing the valid values instead.
- `run_strategy.py --prop-compare` proven the same way, including
  reproducing `prop_pass_simulator.py`'s own `__main__` example numbers
  exactly (1.7%/27.1%/49.7%/70.8% pass probability across 1/2/3/6
  contracts) — plus a missing-`--prop-compare-size` `argparse` error and
  two malformed-spec cases (wrong field count, non-numeric field), both
  producing a plain-English message naming the expected
  `CONTRACTS:AVG_PNL:PNL_STD` format rather than a raw parse exception.
- `data_pipeline.fetch_eod()` fails fast and locally on a missing/
  placeholder API key, before any request goes out.

**Not yet run against live EODHD/FMP/Anthropic APIs from this
environment** — that needs a real API key and a network path this sandbox
doesn't have. Run it on your own machine and it'll have normal internet
access.
