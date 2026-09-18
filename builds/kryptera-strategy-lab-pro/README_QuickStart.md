# Kryptera Strategy Lab — Strategy Generator (PRO)
## Quick Start Guide (Windows, macOS, Linux)

---

### No Python conflicts — runs in its own isolated environment

This build installs all dependencies into a private `.venv` folder inside
this directory. It will **not** touch, modify, or break any Python
packages already installed on your system.

---

## What's Included

| File | Purpose |
|------|---------|
| `strategy_generator_pro.py` | Main strategy generator script (single file, self-contained) |
| `requirements.txt` | Exact pinned library versions (tested working set) |
| `setup_venv.bat` / `setup_venv.sh` | One-click installer — **run this once** (Windows / macOS+Linux) |
| `run_strategy.bat` / `run_strategy.sh` | Launcher — run this every time you use it |

---

## What Changed From the Lite Version — and Why

The Lite bundle's two READMEs disagreed with each other on the actual
spec (4 vs. 6 indicator families, 93 vs. 63 conditions, a "positive
return" bar vs. a "beat the benchmark" bar, a 60/20/20 vs. 35/35/30 data
split). This Pro build resolves that by adopting the stricter, more
recently-documented spec as the single source of truth:

- **6 indicator families, 63 conditions**: Bollinger Bands (18), Hull
  Moving Average (21), KAMA (2), FastKAMA (2), Efficiency Ratio (18),
  Bar-based (2).
- **35% / 35% / 30%** chronological, non-overlapping In-Sample /
  Out-of-Sample / Final-Holdout split.
- **Pass bar: beat the buy-and-hold benchmark**, not just post a positive
  return, in *all three* phases, with at least `min_trades` trades in
  each.

It also fixes two real packaging bugs found in the Lite bundle and adds
several reliability/usability upgrades:

| Issue in the Lite bundle | Fix in this build |
|---|---|
| Setup script tells you to run `launch.bat`, which doesn't exist | Points to the actual launcher, `run_strategy.bat` |
| `requirements.txt` only floors/ceilings `pandas` and floors `plotly` with no upper bound — confirmed in testing to let pip install `pandas 3.0.6` and a `plotly` 6.x release, both of which break `vectorbt==0.28.5` | Every dependency is pinned to an exact, tested-working version |
| `numba` listed as required in the docs but commented out in `requirements.txt` | Included and pinned — it's what keeps the search loop fast |
| Search loop has no defined behavior if nothing can pass | Configurable `--max-attempts` cap with a clear message on exhaustion |
| Only a prose claim that execution avoids look-ahead bias | An explicit, asserted one-bar signal shift in code (`shift_to_next_bar_open`) |
| Discovered strategy has to be copied by hand from the console | Auto-saved to its own runnable `discovered_strategy_<SYMBOL>_<timestamp>.py` file |
| Equity curve requires a blocking `pf.plot().show()` GUI call | Saved as a standalone `equity_curve_*.html` file instead — safe for headless/scheduled runs |
| Windows-only setup/launch | `setup_venv.sh` / `run_strategy.sh` added for macOS/Linux |
| Reported metric was total return only | Sharpe ratio, max drawdown, win rate, and profit factor reported for all 3 phases, alongside the benchmark return each is measured against |

Full analysis behind these changes: see `/notes/kryptera-strategy-lab-analysis.md`
in the project this was built in.

---

## System Requirements

- **OS:** Windows 10/11, macOS, or Linux
- **Python:** 3.10 or 3.11 (3.12+ not recommended — matches `vectorbt`/`numba` compatibility)
- **Internet connection** required during setup (package download) and runtime (yfinance data)
- **Disk space:** ~1.5 GB free for the `.venv` folder

---

## First-Time Setup

**Windows:**
1. Put all files in the same folder, e.g. `C:\KrypteraStrategyLabPro\`
2. Double-click **`setup_venv.bat`**
3. Wait for **"Setup complete!"**

**macOS / Linux:**
1. Put all files in the same folder
2. In a terminal in that folder: `chmod +x setup_venv.sh run_strategy.sh` (once)
3. Run `./setup_venv.sh`
4. Wait for **"Setup complete!"**

You only need to do this once per copy of the folder.

---

## Running the Strategy Generator

**Windows:** double-click `run_strategy.bat`
**macOS/Linux:** run `./run_strategy.sh`

The simplest way to change settings is still editing the `CONFIG` block at
the top of `strategy_generator_pro.py` (no coding needed — it's just
values between quotes):

```python
SYMBOL     = "NVDA"          # any yfinance-supported ticker
START_DATE = "1960-01-01"
END_DATE   = "2030-01-01"
INTERVAL   = "1d"

MIN_TRADES = 10   # minimum trades required in each phase to pass
SIZE       = 1    # number of conditions combined per entry/exit signal
```

Power users can instead pass flags without editing the file, e.g.:

```
run_strategy.bat --symbol AAPL --min-trades 15 --size 2 --seed 42
```

Run with `--help` to see every available flag.

---

## What You Get When a Strategy Passes

- **A phase-by-phase stats table** printed to the console: trades,
  return, benchmark return, Sharpe ratio, max drawdown, win rate, and
  profit factor for the In-Sample, Out-of-Sample, and Holdout phases.
- **A saved, runnable strategy file** — `discovered_strategy_<SYMBOL>_<timestamp>.py`
  — a frozen copy of the generator pinned to the winning conditions and
  parameters, with the stats recorded in its header comment.
- **A saved equity curve** — `equity_curve_<SYMBOL>_<timestamp>.html` —
  open it in any browser.

If no combination passes within `--max-attempts` (default 20,000), the
script says so explicitly and suggests what to adjust — it will not hang
forever silently.

---

## Tips & Notes

- Increasing `SIZE` (e.g. `2`) creates more complex multi-condition
  strategies but makes passing all 3 phases harder and slower.
- Lowering `MIN_TRADES` increases the chance of passing but may produce
  strategies with too few trades to be statistically meaningful.
- The generator executes at the *next bar's open* after a signal is
  generated from the *current bar's close* — the look-ahead-bias guard
  this depends on is implemented explicitly in code, not just assumed.
- If the combined In-Sample + Out-of-Sample + Holdout window covers
  under ~2 years of data, the script prints an overfitting-risk warning.
  Treat a pass on a short window as a starting point, not proof.
- The generated strategy is a research prototype — stress-test, walk
  forward, and manually review before considering any live use.
- For intraday intervals (`'1h'`, `'15m'`), yfinance limits historical
  depth; daily bars (`'1d'`) give the most history.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Python not found` during setup | Install Python 3.10/3.11 and (on Windows) check "Add Python to PATH" |
| Setup fails or times out | Check your internet connection, then re-run the setup script — it skips steps already done |
| `[ERROR] Strategy script not found` | All files must be in the same folder |
| Generator exhausts `--max-attempts` | Widen the date range, lower `--min-trades`, use `--size 1`, or try a more volatile symbol |
| Import errors after setup | Don't hand-edit `requirements.txt` versions — they're pinned deliberately; delete `.venv` and re-run setup instead |
| Windows launcher window closes immediately | Right-click `run_strategy.bat` → "Run as administrator" |

---

## Library Versions (Pinned — see `requirements.txt` for why every one is exact)

| Library | Version | Purpose |
|---------|---------|---------|
| vectorbt | 0.28.5 | Backtesting engine |
| yfinance | 0.2.66 | Market data download |
| pandas | 2.2.3 | Data manipulation |
| numpy | 1.26.4 | Numerical computing |
| numba | 0.60.0 | JIT compilation for KAMA/FastKAMA (required, not optional) |
| plotly | 5.24.1 | Equity curve export |
| scipy | 1.17.1 | Statistics (vectorbt dependency) |
| tqdm | 4.70.1 | Progress reporting (vectorbt dependency) |
| pytz | 2026.3.post1 | Timezone handling (vectorbt dependency) |

---

## Disclaimer

This product is provided for educational and research purposes only. Past
backtest performance does not guarantee future results. Backtested
strategies are subject to look-ahead bias, regime changes, and market
structure shifts. Nothing in this product constitutes financial,
investment, or trading advice. Always conduct your own due diligence
before committing real capital to any strategy. The author assumes no
liability for financial losses arising from the use of this software.

Simple Indicator Strategy Generator — PRO Build | Kryptera
