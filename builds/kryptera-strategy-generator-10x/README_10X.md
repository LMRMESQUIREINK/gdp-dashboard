# ♛ RUTHLESS TRADING GOLD — Strategy Generator 10X

A structural upgrade of the Kryptera "Simple Indicators Strategy Generator
(Lite)" — same core idea (randomly combine boolean indicator conditions,
backtest, keep what survives), rebuilt around the five gaps identified in
the DEEP/DEEPER/DEEPEST/DEEPEST-EST analysis of the original
(`/notes/kryptera-strategy-lab-analysis.md`, Addendum 1).

## What "10X" means here

Not a literal 10x condition count. `conditions.py`'s factory builds
**144 conditions across 12 conceptual indicator families** (BB, HMA, KAMA,
ER, RSI, MACD, ADX, ATR, Donchian, Stochastic, OBV/VWAP, Z-score/ROC —
verified at runtime, nothing here is hardcoded), close to the original
estimate of ~145 and, per Addendum 1's reconciliation, roughly 1.5x the
original Lite script's actual 93-condition/4-family library. Note:
`run_10x.py`'s own printed family count uses each condition NAME's prefix,
which comes out to 14 rather than 12 — `OBV_*`/`VWAP_*` are one family in
this table but two prefixes, and so are `Zscore_*`/`ROC_*`. Both numbers
are real and verified; 12 is the conceptual grouping used above, 14 is
what a naive `split("_")[0]` over the column names actually counts. The
condition count was never the real problem, either way. The 10X is in
**structure**:

| # | Gap in the original | Fix in this build |
|---|---|---|
| 1 | No attempt-count disclosure | Every result reports how many candidates were tried and rejected |
| 2 | Pass bar = "return > 0" only | Requires minimum Sharpe **and** a max-drawdown ceiling |
| 3 | Single symbol only (NVDA) | Must pass on **every** symbol in a basket, not one |
| 4 | One static 3-way split | Multiple rolling walk-forward folds |
| 5 | No cost sensitivity check | Must survive a stressed fee/slippage scenario, not just base costs |

Where the original's lookahead-bias handling was already correct
(decide-at-close, execute-at-next-open, then shift again before the
backtest touches it), this build keeps that pattern unchanged.

## Files

| File | Role |
|---|---|
| `indicators.py` | Vectorized indicator math (BB, HMA, KAMA, ER, RSI, MACD, ADX, ATR, Donchian, Stochastic, OBV/VWAP, Z-score/ROC) |
| `conditions.py` | Condition factory — builds the full 144-condition/12-family searchable library from `indicators.py` |
| `strategy_generator_10x.py` | `Generator10X` — the multi-symbol, walk-forward, risk-adjusted, attempt-tracked, cost-stressed search |
| `data_pipeline_10x.py` | Multi-symbol yfinance fetch (kept on yfinance to match the original product) |
| `run_10x.py` | CLI entry point for the system above |
| `ruthless_strategy_lab_10x.py` | **Alternative engine** — see "Two engines" below |

## Two engines, on purpose

This folder ships two different 10X search engines rather than merging
them into one, because they make a genuinely different design choice:

- **`strategy_generator_10x.py` (the system above)** draws entry/exit
  conditions **by name** from a large, fixed library of pre-built
  (indicator, parameter preset, comparison) columns — breadth of the
  searchable rule space, multi-symbol, walk-forward, cost-stressed.
  Requires `vectorbt`.
- **`ruthless_strategy_lab_10x.py`** draws each condition's underlying
  **parameters** fresh on every trial — a real search over parameter
  space, not just rule space — across a smaller 23-condition/10-family
  registry. Single-symbol by default, no `vectorbt` dependency (the
  backtest loop is hand-rolled), so it still runs even if
  `vectorbt`/`numba` fail to install on a given platform. Run it
  directly: `python ruthless_strategy_lab_10x.py`.

Both independently fix the same five gaps above; they just trade off
breadth-of-rules (official system) against depth-of-parameter-search
(alternative engine). Try the official system first; fall back to the
alternative if you want per-trial parameter randomization or hit a
`vectorbt`/`numba` install problem.

## Setup

```bash
pip install vectorbt==0.28.5 yfinance "pandas>=2.0.0,<3.0.0" numpy --break-system-packages
```

Or, for a pinned, isolated install (recommended — see `requirements.txt`
for why exact pins matter here):

```bash
./setup_venv.sh      # macOS/Linux
setup_venv.bat        # Windows
```

Same pandas-version constraint as the original product: vectorbt 0.28.5
does not support pandas 3.0+.

## Run it

```bash
python run_10x.py
# or customize the basket / strictness:
python run_10x.py --symbols NVDA AAPL KO --size 2 --min-sharpe 0.7

# or the vectorbt-free alternative engine, single symbol:
python ruthless_strategy_lab_10x.py
```

Default basket is deliberately mixed-regime (`NVDA`, `AAPL`, `KO`) — two
growth mega-caps and one defensive staple — because a strategy that only
survives on correlated growth names hasn't proven much.

## What this still doesn't fix

This build does not turn a random search into a validated trading edge —
no amount of structure does that. What it does is make the search honest:
if nothing passes, `Generator10X.search()` raises after `max_attempts`
with a message saying so plainly, rather than looping silently forever.
A "no result" run is real information; treat it as such rather than as a
bug to work around by loosening filters until something passes.

The disclaimer on the original product still applies in full here: this
is a research prototype, not trading advice, and any output — pass or
fail — needs further stress testing before real capital ever touches it.
