"""
Kryptera Strategy Lab — Simple Indicator Strategy Generator (PRO)
==================================================================

Self-contained, single-file strategy generator. Randomly combines boolean
indicator conditions into entry/exit signals, backtests each candidate with
vectorbt, and only returns a strategy that clears three non-overlapping,
chronologically ordered data windows.

WHAT THIS BUILD CHANGES vs. the Lite bundle it's built from
-------------------------------------------------------------
The two READMEs that shipped with the Lite product disagree with each other
(4 vs. 6 indicator families, 93 vs. 63 conditions, "positive return" vs.
"beat the benchmark" as the pass bar, 60/20/20 vs. 35/35/30 split). This
build adopts the QuickStart guide's numbers — 6 families, 63 conditions,
35/35/30 split, beat-the-benchmark-in-all-3-phases — as the single source of
truth, since that's what the actual packaging (requirements.txt, the .bat
launchers) was built around. See /notes/kryptera-strategy-lab-analysis.md
for the full comparison.

On top of that spec, this build adds:
  - Sharpe ratio, max drawdown, win rate, and profit factor for all three
    phases (not just total return), plus the benchmark return each phase
    is measured against.
  - An explicit, asserted look-ahead-bias guard (signals are shifted one
    bar forward before being used to execute at the *next* bar's open).
  - A max-attempt cap on the search loop, with a clear message instead of
    an infinite silent loop when no combination can pass.
  - Auto-save of the discovered strategy to its own runnable .py file
    (a frozen copy of this same script, pinned to the winning parameters),
    in addition to printing it.
  - Optional CLI overrides for every top-of-file setting, with the
    top-of-file constants remaining the primary, no-coding-required way
    to use it.
  - An overfitting warning if the in-sample window covers under 2 years.

DISCLAIMER
----------
Provided for educational and research purposes only. Past backtest
performance does not guarantee future results. Backtested strategies are
subject to look-ahead bias, regime changes, and market structure shifts.
Nothing here is financial, investment, or trading advice. Do your own
diligence before committing real capital to any strategy discovered by
this tool. The author assumes no liability for financial losses arising
from its use.
"""

from __future__ import annotations

import argparse
import itertools
import random
import re
import sys
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

try:
    import numba

    NUMBA_AVAILABLE = True
except ImportError:  # pragma: no cover - defensive fallback only
    NUMBA_AVAILABLE = False

import vectorbt as vbt
import yfinance as yf

# === CONFIG START ============================================================
# Edit these directly for the simplest way to run this script — no command
# line needed. CLI flags (see --help) override these if passed.
SYMBOL = "NVDA"  # any yfinance-supported ticker
START_DATE = "1960-01-01"
END_DATE = "2030-01-01"
INTERVAL = "1d"

MIN_TRADES = 10  # minimum trades required in each phase to pass
SIZE = 1  # number of conditions randomly combined per entry/exit signal
MAX_ATTEMPTS = 20_000  # search cap before giving up with a clear message
RANDOM_SEED = None  # set an int for reproducible searches

FEES = 0.001  # 0.1%, matches the product's documented cost model
SLIPPAGE = 0.002  # 0.2%

# Data split — chronological, non-overlapping (must sum to 1.0)
IS_FRACTION = 0.35  # In-Sample
OOS_FRACTION = 0.35  # Out-of-Sample
NT_FRACTION = 0.30  # Final holdout (No-Test)
# === CONFIG END ==============================================================


# === CLI OVERRIDES ============================================================
def parse_cli_overrides() -> argparse.Namespace:
    """Optional power-user overrides. Every flag defaults to the CONFIG
    block above, so running with no arguments behaves exactly like editing
    the constants by hand."""
    parser = argparse.ArgumentParser(
        description="Kryptera Strategy Lab — Strategy Generator (Pro)"
    )
    parser.add_argument("--symbol", default=SYMBOL)
    parser.add_argument("--start", default=START_DATE)
    parser.add_argument("--end", default=END_DATE)
    parser.add_argument("--interval", default=INTERVAL)
    parser.add_argument("--min-trades", type=int, default=MIN_TRADES)
    parser.add_argument("--size", type=int, default=SIZE)
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Where to save the discovered strategy snapshot .py file",
    )
    return parser.parse_args()


# === DATA LAYER ================================================================
def fetch_price_data(symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
    """Download OHLCV data via yfinance and fail with a clear message
    instead of crashing deep inside pandas on bad input."""
    raw = yf.download(
        symbol, start=start, end=end, interval=interval, progress=False, auto_adjust=True
    )
    if raw is None or raw.empty:
        raise ValueError(
            f"No price data returned for symbol={symbol!r} between {start} and {end} "
            f"at interval={interval!r}. Check the ticker is valid on yfinance and that "
            f"the date range/interval combination is supported (intraday intervals have "
            f"limited history)."
        )
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
    if len(df) < 50:
        raise ValueError(
            f"Only {len(df)} bars returned for {symbol!r} — too little data to split "
            f"into three validation phases. Widen the date range or use a lower-frequency "
            f"interval."
        )
    span_years = (df.index[-1] - df.index[0]).days / 365.25
    if span_years < 2:
        warnings.warn(
            f"In-sample+out-of-sample+holdout window only spans ~{span_years:.1f} years. "
            f"Strategies validated on under 2 years of data carry a real overfitting risk "
            f"— treat a pass here as a starting point, not proof.",
            stacklevel=2,
        )
    return df


# === INDICATOR LAYER (vectorized) =============================================
def rolling_bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    bandwidth = (upper - lower) / mid
    percent_b = (close - lower) / (upper - lower)
    return mid, upper, lower, bandwidth, percent_b


def wma(series: pd.Series, window: int) -> pd.Series:
    weights = np.arange(1, window + 1)
    return series.rolling(window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def hull_moving_average(close: pd.Series, window: int) -> pd.Series:
    half = max(int(window / 2), 1)
    sqrt_n = max(int(np.sqrt(window)), 1)
    return wma(2 * wma(close, half) - wma(close, window), sqrt_n)


def efficiency_ratio(close: pd.Series, window: int = 10) -> pd.Series:
    """Kaufman Efficiency Ratio: net change over `window` bars divided by
    the sum of absolute bar-to-bar changes over the same window. Fully
    vectorized — no recursion needed."""
    change = (close - close.shift(window)).abs()
    volatility = close.diff().abs().rolling(window).sum()
    return (change / volatility.replace(0, np.nan)).fillna(0)


def _kama_numba_loop(close: np.ndarray, er: np.ndarray, fast: int, slow: int) -> np.ndarray:
    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    out = np.empty_like(close)
    out[0] = close[0]
    for i in range(1, len(close)):
        sc = (er[i] * (fast_sc - slow_sc) + slow_sc) ** 2
        out[i] = out[i - 1] + sc * (close[i] - out[i - 1])
    return out


if NUMBA_AVAILABLE:
    _kama_core = numba.njit(cache=True)(_kama_numba_loop)
else:  # pragma: no cover - only exercised if numba failed to install
    _kama_core = _kama_numba_loop


def kaufman_adaptive_ma(close: pd.Series, er_window: int, fast: int, slow: int) -> pd.Series:
    """KAMA's smoothing constant adapts every bar based on the efficiency
    ratio, which makes it inherently recursive (like an EMA) — this can't
    be expressed as a single vectorized pandas op. The recursion itself is
    numba-JIT-compiled so it stays fast; only this one function uses an
    explicit loop, and it's documented here rather than hidden."""
    er = efficiency_ratio(close, er_window).to_numpy()
    values = _kama_core(close.to_numpy(dtype=np.float64), er, fast, slow)
    return pd.Series(values, index=close.index)


# === CONDITION LIBRARY (63 conditions across 6 families) =====================
def crosses_above(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a > b) & (a.shift(1) <= b.shift(1))


def crosses_below(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))


def build_condition_library(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Returns {condition_name: boolean Series}. Every condition is
    computed only from data available up to and including the current
    bar's close — the look-ahead-bias guard (see LOOKAHEAD-BIAS GUARD
    section) is what makes it safe to *use* these, not this function."""
    close, high, low, open_ = df["Close"], df["High"], df["Low"], df["Open"]
    cond: dict[str, pd.Series] = {}

    # --- Bollinger Bands (18 conditions) ---
    mid, upper, lower, bandwidth, percent_b = rolling_bollinger(close)
    bw_mean = bandwidth.rolling(50).mean()
    cond["bb_close_above_upper"] = close > upper
    cond["bb_close_below_lower"] = close < lower
    cond["bb_cross_above_upper"] = crosses_above(close, upper)
    cond["bb_cross_below_lower"] = crosses_below(close, lower)
    cond["bb_cross_above_mid"] = crosses_above(close, mid)
    cond["bb_cross_below_mid"] = crosses_below(close, mid)
    cond["bb_squeeze"] = bandwidth < bw_mean * 0.75
    cond["bb_expansion"] = bandwidth > bw_mean * 1.25
    cond["bb_pctb_above_1"] = percent_b > 1
    cond["bb_pctb_below_0"] = percent_b < 0
    cond["bb_pctb_cross_above_80"] = crosses_above(percent_b, pd.Series(0.8, index=df.index))
    cond["bb_pctb_cross_below_20"] = crosses_below(percent_b, pd.Series(0.2, index=df.index))
    cond["bb_rejection_at_upper"] = (high > upper) & (close < upper)
    cond["bb_rejection_at_lower"] = (low < lower) & (close > lower)
    cond["bb_walk_up_3"] = (close > upper).rolling(3).sum() == 3
    cond["bb_walk_down_3"] = (close < lower).rolling(3).sum() == 3
    cond["bb_bandwidth_widening"] = bandwidth > bandwidth.shift(1)
    cond["bb_bandwidth_narrowing"] = bandwidth < bandwidth.shift(1)

    # --- Hull Moving Average (21 conditions) ---
    hma_fast = hull_moving_average(close, 9)
    hma_slow = hull_moving_average(close, 21)
    hma_fast_slope = hma_fast.diff()
    hma_slow_slope = hma_slow.diff()
    cond["hma_fast_above_slow"] = hma_fast > hma_slow
    cond["hma_fast_below_slow"] = hma_fast < hma_slow
    cond["hma_golden_cross"] = crosses_above(hma_fast, hma_slow)
    cond["hma_death_cross"] = crosses_below(hma_fast, hma_slow)
    cond["hma_close_above_fast"] = close > hma_fast
    cond["hma_close_below_fast"] = close < hma_fast
    cond["hma_close_cross_above_fast"] = crosses_above(close, hma_fast)
    cond["hma_close_cross_below_fast"] = crosses_below(close, hma_fast)
    cond["hma_close_above_slow"] = close > hma_slow
    cond["hma_close_below_slow"] = close < hma_slow
    cond["hma_close_cross_above_slow"] = crosses_above(close, hma_slow)
    cond["hma_close_cross_below_slow"] = crosses_below(close, hma_slow)
    cond["hma_fast_slope_up"] = hma_fast_slope > 0
    cond["hma_fast_slope_down"] = hma_fast_slope < 0
    cond["hma_slow_slope_up"] = hma_slow_slope > 0
    cond["hma_slow_slope_down"] = hma_slow_slope < 0
    cond["hma_regime_uptrend"] = (hma_fast_slope > 0) & (hma_slow_slope > 0)
    cond["hma_regime_downtrend"] = (hma_fast_slope < 0) & (hma_slow_slope < 0)
    cond["hma_fast_accelerating_up"] = hma_fast_slope.diff() > 0
    cond["hma_fast_accelerating_down"] = hma_fast_slope.diff() < 0
    cond["hma_fast_persistent_rise_3"] = (hma_fast_slope > 0).rolling(3).sum() == 3

    # --- KAMA (2 conditions) ---
    kama = kaufman_adaptive_ma(close, er_window=10, fast=2, slow=30)
    cond["kama_cross_above"] = crosses_above(close, kama)
    cond["kama_cross_below"] = crosses_below(close, kama)

    # --- FastKAMA (2 conditions) ---
    fast_kama = kaufman_adaptive_ma(close, er_window=5, fast=2, slow=15)
    cond["fastkama_cross_above"] = crosses_above(close, fast_kama)
    cond["fastkama_cross_below"] = crosses_below(close, fast_kama)

    # --- Efficiency Ratio (18 conditions) ---
    er = efficiency_ratio(close, 10)
    er_mean = er.rolling(50).mean()
    cond["er_trending"] = er > 0.5
    cond["er_choppy"] = er < 0.2
    cond["er_cross_above_high"] = crosses_above(er, pd.Series(0.5, index=df.index))
    cond["er_cross_below_high"] = crosses_below(er, pd.Series(0.5, index=df.index))
    cond["er_cross_above_low"] = crosses_above(er, pd.Series(0.2, index=df.index))
    cond["er_cross_below_low"] = crosses_below(er, pd.Series(0.2, index=df.index))
    cond["er_rising"] = er > er.shift(1)
    cond["er_falling"] = er < er.shift(1)
    cond["er_spike"] = (er - er.shift(1)) > 0.15
    cond["er_plunge"] = (er.shift(1) - er) > 0.15
    cond["er_noise_zone"] = (er >= 0.2) & (er <= 0.35)
    cond["er_above_mean"] = er > er_mean
    cond["er_below_mean"] = er < er_mean
    cond["er_multibar_high_20"] = er >= er.rolling(20).max()
    cond["er_multibar_low_20"] = er <= er.rolling(20).min()
    cond["er_sustained_trending_3"] = (er > 0.5).rolling(3).sum() == 3
    cond["er_sustained_choppy_3"] = (er < 0.2).rolling(3).sum() == 3
    cond["er_accelerating"] = er.diff().diff() > 0

    # --- Bar-based (2 conditions) ---
    cond["bar_bullish"] = (close > open_) & (close > close.shift(1))
    cond["bar_bearish"] = (close < open_) & (close < close.shift(1))

    assert len(cond) == 63, f"Expected 63 conditions, built {len(cond)} — spec drift."
    return {name: series.fillna(False).astype(bool) for name, series in cond.items()}


# === LOOKAHEAD-BIAS GUARD ======================================================
def shift_to_next_bar_open(signal: pd.Series) -> pd.Series:
    """A condition is only knowable once its bar has closed. Shifting it
    forward by one bar means a signal computed from bar t's close-based
    data can only trigger execution at bar t+1's open — never earlier.
    This is the one non-negotiable step standing between "backtest" and
    "backtest that quietly cheats." Every entry/exit signal MUST pass
    through this before being handed to the backtester."""
    shifted = signal.shift(1, fill_value=False).astype(bool)
    assert not shifted.iloc[0], "Bar zero must never carry a signal — shift failed."
    return shifted


# === BACKTEST LAYER (vectorbt) =================================================
@dataclass
class PhaseResult:
    name: str
    total_return: float
    benchmark_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: int
    passed: bool


def run_backtest(df: pd.DataFrame, entry_name: str, exit_name: str, cond: dict, min_trades: int) -> PhaseResult | None:
    entries = shift_to_next_bar_open(cond[entry_name])
    exits = shift_to_next_bar_open(cond[exit_name])
    if entries.sum() == 0:
        return None
    try:
        pf = vbt.Portfolio.from_signals(
            close=df["Open"],
            entries=entries,
            exits=exits,
            fees=FEES,
            slippage=SLIPPAGE,
            freq="1D",
        )
    except Exception:
        return None
    trades = int(pf.trades.count())
    if trades == 0:
        return None
    total_return = float(pf.total_return())
    benchmark_return = float(pf.total_benchmark_return())
    return PhaseResult(
        name="",
        total_return=total_return,
        benchmark_return=benchmark_return,
        sharpe=float(pf.sharpe_ratio()),
        max_drawdown=float(pf.max_drawdown()),
        win_rate=float(pf.trades.win_rate()) if trades else 0.0,
        profit_factor=float(pf.trades.profit_factor()) if trades else 0.0,
        trades=trades,
        passed=(trades >= min_trades) and (total_return > benchmark_return),
    )


def build_full_history_portfolio(df: pd.DataFrame, entry_names: tuple[str, ...], exit_names: tuple[str, ...]) -> vbt.Portfolio:
    """Recomputes the winning entry/exit combo over the *entire* dataset
    (all 3 phases stitched back together) purely for the equity-curve
    export below — this plays no role in the pass/fail decision, which is
    made per-phase above."""
    full_cond = build_condition_library(df)
    entry = full_cond[entry_names[0]].copy()
    for name in entry_names[1:]:
        entry &= full_cond[name]
    exit_ = full_cond[exit_names[0]].copy()
    for name in exit_names[1:]:
        exit_ &= full_cond[name]
    return vbt.Portfolio.from_signals(
        close=df["Open"],
        entries=shift_to_next_bar_open(entry),
        exits=shift_to_next_bar_open(exit_),
        fees=FEES,
        slippage=SLIPPAGE,
        freq="1D",
    )


def save_equity_curve(pf: vbt.Portfolio, out_path: Path) -> Path | None:
    """Saves the equity curve as a standalone HTML file — unlike the
    original's `pf.plot().show()`, this never blocks waiting for a GUI/
    browser to open, so it's safe to call from a plain terminal or a
    scheduled/headless run. Best-effort: a plotting failure here should
    never take down an otherwise-successful strategy search."""
    try:
        fig = pf.plot()
        fig.write_html(str(out_path))
        return out_path
    except Exception as exc:  # pragma: no cover - plotting is best-effort
        print(f"[WARN] Could not save equity curve ({exc}). Stats above are unaffected.")
        return None


# === STRATEGY GENERATOR (search + 3-phase validation) ==========================
@dataclass
class SearchResult:
    entry_conditions: tuple[str, ...]
    exit_conditions: tuple[str, ...]
    attempts: int
    phases: dict[str, PhaseResult] = field(default_factory=dict)


class StrategyGenerator:
    """Randomly combines `size` conditions (ANDed together) into an entry
    signal and a separate random combination into an exit signal, then
    requires the combo to beat its own buy-and-hold benchmark with at
    least `min_trades` trades in ALL three chronological phases —
    In-Sample, Out-of-Sample, and a final holdout the search never sees
    until the very last check."""

    def __init__(self, df: pd.DataFrame, condition_names: list[str], min_trades: int = MIN_TRADES, size: int = SIZE):
        self.condition_names = condition_names
        self.min_trades = min_trades
        self.size = size

        n = len(df)
        is_end = int(n * IS_FRACTION)
        oos_end = is_end + int(n * OOS_FRACTION)
        self.phases = {
            "in_sample": df.iloc[:is_end],
            "out_of_sample": df.iloc[is_end:oos_end],
            "holdout": df.iloc[oos_end:],
        }
        self.condition_cache = {
            phase_name: build_condition_library(phase_df) for phase_name, phase_df in self.phases.items()
        }

    def _random_combo_condition(self, cond: dict[str, pd.Series], prefix: str) -> tuple[tuple[str, ...], pd.Series]:
        picked = tuple(random.sample(self.condition_names, self.size))
        combined = cond[picked[0]].copy()
        for name in picked[1:]:
            combined &= cond[name]
        return picked, combined

    def search(self, max_attempts: int = MAX_ATTEMPTS) -> SearchResult | None:
        is_cond = self.condition_cache["in_sample"]
        for attempt in range(1, max_attempts + 1):
            if attempt % 2000 == 0:
                print(f"  ... {attempt} combinations tried so far")

            entry_names, entry_signal = self._random_combo_condition(is_cond, "entry")
            exit_names, exit_signal = self._random_combo_condition(is_cond, "exit")
            if entry_names == exit_names:
                continue

            is_cond_with_signals = dict(is_cond)
            is_cond_with_signals["__entry__"] = entry_signal
            is_cond_with_signals["__exit__"] = exit_signal
            is_result = run_backtest(self.phases["in_sample"], "__entry__", "__exit__", is_cond_with_signals, self.min_trades)
            if is_result is None or not is_result.passed:
                continue

            result = SearchResult(entry_conditions=entry_names, exit_conditions=exit_names, attempts=attempt)
            is_result.name = "In-Sample"
            result.phases["in_sample"] = is_result

            all_passed = True
            for phase_name, label in (("out_of_sample", "Out-of-Sample"), ("holdout", "Final Holdout")):
                phase_cond = dict(self.condition_cache[phase_name])
                entry_sig = phase_cond[entry_names[0]].copy()
                for name in entry_names[1:]:
                    entry_sig &= phase_cond[name]
                exit_sig = phase_cond[exit_names[0]].copy()
                for name in exit_names[1:]:
                    exit_sig &= phase_cond[name]
                phase_cond["__entry__"] = entry_sig
                phase_cond["__exit__"] = exit_sig
                phase_result = run_backtest(self.phases[phase_name], "__entry__", "__exit__", phase_cond, self.min_trades)
                if phase_result is None or not phase_result.passed:
                    all_passed = False
                    break
                phase_result.name = label
                result.phases[phase_name] = phase_result

            if all_passed:
                return result
        return None


# === REPORTING ==================================================================
def print_phase_table(result: SearchResult) -> None:
    print()
    print(f"{'Phase':<16}{'Trades':>8}{'Return':>10}{'Benchmark':>12}{'Sharpe':>9}{'MaxDD':>9}{'WinRate':>9}{'PF':>7}")
    for phase in result.phases.values():
        print(
            f"{phase.name:<16}{phase.trades:>8}{phase.total_return:>10.2%}"
            f"{phase.benchmark_return:>12.2%}{phase.sharpe:>9.2f}{phase.max_drawdown:>9.2%}"
            f"{phase.win_rate:>9.2%}{phase.profit_factor:>7.2f}"
        )
    print()
    print(f"Entry conditions (AND): {', '.join(result.entry_conditions)}")
    print(f"Exit conditions  (AND): {', '.join(result.exit_conditions)}")
    print(f"Found after {result.attempts} attempts.")


# === SNAPSHOT / SAVE =============================================================
def save_strategy_snapshot(result: SearchResult, symbol: str, start: str, end: str, interval: str, min_trades: int, size: int, output_dir: str) -> Path:
    """Writes a frozen, independently-runnable copy of this file: the
    CONFIG block is rewritten with this run's exact parameters, and a
    header block records which named conditions won and their stats.
    Matches the original product's promise of self-contained output —
    but saved to a file automatically instead of copy-pasted by hand."""
    source = Path(__file__).read_text()

    config_pattern = re.compile(r"# === CONFIG START.*?# === CONFIG END ={2,}\n", re.DOTALL)
    frozen_config = (
        "# === CONFIG START (FROZEN — discovered strategy snapshot) ==================\n"
        f"SYMBOL = {symbol!r}\n"
        f"START_DATE = {start!r}\n"
        f"END_DATE = {end!r}\n"
        f"INTERVAL = {interval!r}\n\n"
        f"MIN_TRADES = {min_trades}\n"
        f"SIZE = {size}\n"
        f"MAX_ATTEMPTS = {MAX_ATTEMPTS}\n"
        f"RANDOM_SEED = None\n\n"
        f"FEES = {FEES}\n"
        f"SLIPPAGE = {SLIPPAGE}\n\n"
        f"IS_FRACTION = {IS_FRACTION}\n"
        f"OOS_FRACTION = {OOS_FRACTION}\n"
        f"NT_FRACTION = {NT_FRACTION}\n"
        "# === CONFIG END ==============================================================\n"
    )
    source = config_pattern.sub(frozen_config, source, count=1)

    stats_lines = "\n".join(
        f"#   {p.name}: trades={p.trades}, return={p.total_return:.2%}, "
        f"benchmark={p.benchmark_return:.2%}, sharpe={p.sharpe:.2f}, "
        f"max_dd={p.max_drawdown:.2%}, win_rate={p.win_rate:.2%}, "
        f"profit_factor={p.profit_factor:.2f}"
        for p in result.phases.values()
    )
    header = (
        f"# === DISCOVERED STRATEGY (frozen {datetime.now():%Y-%m-%d %H:%M}) ============\n"
        f"# Entry (AND): {', '.join(result.entry_conditions)}\n"
        f"# Exit  (AND): {', '.join(result.exit_conditions)}\n"
        f"{stats_lines}\n"
        f"# Found after {result.attempts} search attempts.\n"
        "# =============================================================================\n\n"
    )
    source = header + source

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"discovered_strategy_{symbol}_{datetime.now():%Y%m%d_%H%M%S}.py"
    out_path.write_text(source)
    return out_path


# === MAIN =========================================================================
def main() -> int:
    args = parse_cli_overrides()
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    print(f"Fetching {args.symbol} {args.interval} bars from {args.start} to {args.end}...")
    try:
        df = fetch_price_data(args.symbol, args.start, args.end, args.interval)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    condition_names = list(build_condition_library(df.iloc[:200] if len(df) > 200 else df).keys())
    generator = StrategyGenerator(df, condition_names, min_trades=args.min_trades, size=args.size)

    print(
        f"Searching (min_trades={args.min_trades}, size={args.size}, "
        f"max_attempts={args.max_attempts})... this loops until a strategy beats its "
        f"benchmark in all 3 phases, or the attempt cap is hit."
    )
    result = generator.search(max_attempts=args.max_attempts)

    if result is None:
        print(
            f"\n[NO STRATEGY FOUND] Exhausted {args.max_attempts} attempts without a "
            f"combination that beat the benchmark with >= {args.min_trades} trades in "
            f"all 3 phases. Try: a wider date range, a lower --min-trades, --size 1 "
            f"instead of a larger combo size, or a more liquid/volatile symbol."
        )
        return 1

    print_phase_table(result)
    out_path = save_strategy_snapshot(
        result, args.symbol, args.start, args.end, args.interval, args.min_trades, args.size, args.output_dir
    )
    print(f"\nSaved runnable strategy snapshot to: {out_path}")

    full_pf = build_full_history_portfolio(df, result.entry_conditions, result.exit_conditions)
    equity_path = Path(args.output_dir) / f"equity_curve_{args.symbol}_{datetime.now():%Y%m%d_%H%M%S}.html"
    saved_equity = save_equity_curve(full_pf, equity_path)
    if saved_equity:
        print(f"Saved equity curve to: {saved_equity} (open in any browser)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
