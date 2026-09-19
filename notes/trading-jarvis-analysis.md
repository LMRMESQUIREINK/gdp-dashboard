# Trading Jarvis (RUTHLESS TRADING GOLD build) — Deep Analysis

Analysis of five uploaded files: `data_pipeline.py`, `jarvis_orchestrator.py`,
`live_monitor.py`, `README3.md`, and `run_strategy1.py`. **No PDF was actually
attached this time** despite the request phrasing — these are Python source
files plus a markdown README, analyzed as-is.

Per `README3.md`, this codebase is the "safe, shippable core" of a
"How to Build a Trading Jarvis AI System in 2026" article's architecture:
Claude-API tool-calling front end + live market data + signal generation +
risk sizing, deliberately without voice input or order execution.

---

## DEEP — what's actually here

Six files are named in `README3.md`'s own file table; **only four were
uploaded**:

| File | Role (per README3.md) | Uploaded? |
|---|---|---|
| `data_pipeline.py` | EODHD/FMP fetch + cache | Yes |
| `signal_generator.py` | RSI(65) + volume-confirmation trigger | **No** |
| `risk_manager.py` | ATR stop, fixed-fractional sizing, portfolio heat | **No** |
| `live_monitor.py` | Polling loop → signal → alert | Yes |
| `jarvis_orchestrator.py` | Claude API tool-calling front end | Yes |
| `run_strategy.py` | CLI entry point | Yes (as `run_strategy1.py`) |

`signal_generator.py` and `risk_manager.py` are imported, unconditionally, by
every one of the other three files (`from signal_generator import
generate_signals, latest_signal`; `from risk_manager import evaluate_trade`).
**As uploaded, none of the three entry points can even be imported** — this
is a 6-file system with 2 load-bearing files missing, not a complete system
with a couple of rough edges.

The safety design that *is* present is genuinely consistent across every
file and the README: no `execute_order` tool exists anywhere; the system
prompt in `jarvis_orchestrator.py` explicitly tells Claude to say so if
asked to trade for real; `live_monitor.py`'s docstring and every alert
message frame a signal as "review required," never an instruction. That's a
real, repeated design commitment, not just a README claim — there's no code
path anywhere in these four files that could place an order even by
accident.

---

## DEEPER — what breaks once you look past the README's claims

1. **High, low, and volume are fabricated, not fetched — in the two files
   that most need real ones.** `data_pipeline.get_recent_closes()` returns
   only a `Series` of adjusted closes. Every downstream consumer
   (`jarvis_orchestrator.py`, `live_monitor.py`) then builds a synthetic
   OHLCV frame from that single series:
   ```python
   high = closes * 1.01
   low  = closes * 0.99
   volume = pd.Series(1_500_000, index=closes.index)  # constant
   ```
   This directly undermines two of the three headline features:
   - An **ATR-based stop** (`risk_manager.py`, per the README) needs real
     high/low/close ranges. A flat, arbitrary ±1% band produces a
     constant, symbol-independent "volatility" reading no matter how
     calm or violent the actual stock is — position sizing built on it
     would be systematically wrong in both directions.
   - A **"volume-confirmation" signal** (`signal_generator.py`, per the
     README) checked against a hardcoded constant volume can never
     confirm or reject anything — it's a no-op dressed up as a feature.

   The frustrating part: `data_pipeline.fetch_eod()` already returns real
   `open`/`high`/`low`/`close`/`volume` columns from EODHD. The bug isn't
   missing data access, it's that the one convenience wrapper every
   consumer calls (`get_recent_closes`) throws that real data away before
   it reaches them.

2. **`jarvis_orchestrator.py` hardcodes `MODEL = "claude-sonnet-4-6"`**
   with no override path. That string is a real, still-served model — not
   garbage — but it's the previous generation, and there's no environment
   variable or fallback, so every future model transition means editing
   source instead of config.

3. **API keys default to visibly-fake placeholder strings**
   (`os.getenv("EODHD_API_KEY", "YOUR_EODHD_KEY")`) with no check before
   use. If a user forgets to set the env var, every function fires a real
   HTTP request with the literal string `"YOUR_EODHD_KEY"` as the token,
   surfacing as a confusing 401/403 from EODHD's servers instead of an
   immediate, local, actionable error.

4. **No isolation, no pinned versions.** `README3.md`'s setup is
   `pip install anthropic requests pandas --break-system-packages` — no
   virtual environment, and `--break-system-packages` deliberately
   overrides pip's protection and installs into the system Python
   directly. There's no `requirements.txt`, so two installs a month apart
   can silently get different library versions.

5. **`evaluate_trade()`'s "portfolio heat" can't actually know the
   portfolio.** Every call site is a single, stateless check for one
   symbol — nothing in these four files persists what other positions are
   currently open. A genuine portfolio-heat check (total risk across all
   open positions) needs state this architecture doesn't have. Calling it
   "portfolio heat" implies more awareness than a stateless per-symbol
   call can honestly provide.

---

## DEEPEST — root causes

- The missing-files problem is almost certainly an **upload omission, not
  a design gap** — every file assumes the other two exist unconditionally
  (no `try/except ImportError`), and the "Generated: 2026-07-18" banner is
  identical across all five, meaning they were produced together as one
  set.
- The fabricated-OHLC/volume bug traces to a **single convenience function
  with too narrow a return type** (`get_recent_closes` → `Series`, not a
  frame). Three independent call sites each had to compensate locally,
  and each compensated the same lossy way — a strong sign the fix belongs
  in `data_pipeline.py` once, not patched three times downstream.
- The hardcoded model ID and the placeholder-key-goes-straight-to-the-wire
  behavior are the same underlying pattern from the Kryptera build's
  unpinned dependencies: **a value that's *supposed* to be
  environment/config-driven is instead baked in with no validation**,
  so it fails at the worst possible moment (a deprecated model, a typo'd
  env var) instead of at startup with a clear message.

---

## DEEPEST-EST — what the completed system should do

1. **Write `signal_generator.py` and `risk_manager.py` for real**, matching
   the exact call signatures every other file already expects
   (`generate_signals(frame, rsi_threshold=65)`, `latest_signal(signaled)`,
   `evaluate_trade(frame, equity=, risk_pct=)` → `{"sizing": {...},
   "portfolio_heat": {...}, "approved": bool}`), so the system can
   actually import and run end to end.
2. **Add a real-OHLCV accessor to `data_pipeline.py`** (`get_recent_ohlcv`)
   and switch every consumer to it instead of reconstructing a synthetic
   band from closes alone.
3. **Fix the model ID**, make it env-var-overridable with a current model
   as the default.
4. **Fail fast and locally** on an unset/placeholder API key instead of
   letting a doomed request go out over the network.
5. **Isolate and pin**: a `.venv` + exact `requirements.txt`, consistent
   with this project's own isolate/build software-factory steps and the
   Kryptera Pro build.
6. **Document the portfolio-heat limitation honestly** — it's single-trade
   risk framed as "heat," not a multi-position portfolio view, unless
   position state is added later.
7. **Every existing safety guarantee stays untouched**: no
   `execute_order` tool, text-first, human-confirmation framing, no
   silent voice layer. None of the above requires touching that design.

Full build: `/builds/trading-jarvis/`.

---

## ADDENDUM — the real `risk_manager.py` was uploaded (round 2)

A second upload provided the **actual** `risk_manager.py` — the file this
analysis originally had to reconstruct from the other files' call
signatures alone. It's different from, and better than, the guess:

- `atr()` uses EWM (exponential) smoothing (`tr.ewm(span=n,
  adjust=False).mean()`) — closer to true Wilder ATR than the simple
  rolling-mean approximation this build originally substituted.
- `size_position()` also computes an `r_multiple_target` (a 2R profit
  target above entry) — a real feature the earlier reconstruction didn't
  include at all.
- **`evaluate_trade()` takes an `existing_positions` parameter, and
  `portfolio_heat()` genuinely sums risk across a list of positions.**

That last point directly contradicts finding #6 above and the
"deepest-est" recommendation to just *document* single-trade risk as a
limitation. The correct finding: **the capability for real portfolio-wide
heat was already built into this file** — what was actually missing was
anything upstream ever populating `existing_positions` with real open
positions. Every call site (`jarvis_orchestrator.py`, `live_monitor.py`)
always left it at the default `None`, so in *practice* heat was
single-trade-only, but not because the architecture couldn't do
otherwise — because nothing fed it. That's a narrower, more precise gap
than "add position tracking later"; the fix is a positions ledger plus
wiring, not a redesign. See `positions_store.py` in the build.

One genuine bug did survive in the real file:
`size_position()`'s zero-risk-distance branch (`entry == stop`) returned
a different key set than its normal branch — no `r_multiple_target`, and
a `"warning"` key that meant something different from
`portfolio_heat()`'s own boolean `"warning"` one level up. A caller
reading `result["sizing"]["r_multiple_target"]` unconditionally would
`KeyError` on that edge case. Fixed by normalizing both branches to the
same key set (the zero-risk message moved to `"error"`).

A second, sharper bug this correction surfaced: `live_monitor.py`'s
risk-gated alert path referenced `risk_check['portfolio_heat']['reason']`
— a key that has never existed in the real schema (only
`total_risk`/`heat_pct`/`warning`). That line would have thrown
`KeyError` the first time a signal actually got risk-gated in
production. It went unnoticed earlier because the swapped-in
reconstruction had a `"reason"` key by coincidence of a different design
choice — a reminder that testing against a plausible stand-in isn't the
same as testing against the real contract, however carefully the
stand-in is built.
