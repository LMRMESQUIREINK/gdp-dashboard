"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: strategy_generator_10x.py                     ║
║      Role:      Random-search strategy discovery, WITH the     ║
║                  five statistical fixes the analysis flagged   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

This is a structural upgrade of the Kryptera "Simple Indicators
Strategy Generator (Lite)" script. Same core idea — randomly combine
boolean indicator conditions, backtest, keep what survives — but
fixes the five gaps the DEEPER/DEEPEST/DEEPEST-EST analysis flagged:

  1. ATTEMPT-COUNT DISCLOSURE — every result reports how many
     candidates were tried and rejected before one passed. This
     number is the single most important piece of context a random
     search like this can report, and the original never surfaces it.

  2. RISK-ADJUSTED FILTER — pass bar requires a minimum Sharpe ratio
     and a maximum drawdown ceiling, not just "return > 0".

  3. MULTI-SYMBOL VALIDATION — a candidate must pass on EVERY symbol
     in the validation list, not just one. A strategy that only works
     on NVDA's specific historical run is exactly what a single-symbol
     search would surface, and exactly what this rejects.

  4. WALK-FORWARD FOLDS — multiple rolling IS/OOS windows instead of
     one static 3-way split, so passing isn't just "got lucky on the
     one holdout slice that happened to suit it."

  5. COST STRESS TEST — the candidate must still show a positive
     Sharpe under a stressed slippage/fee assumption, not just the
     base-case 0.1%/0.2% used during the search.

Every condition is causal (see conditions.py); the combined
entry/exit signal is additionally .shift(1)'d here before touching
vectorbt, exactly as the original script does — this part of the
original was already correct and is preserved unchanged.
"""

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import vectorbt as vbt

from conditions import build_all_conditions


# ───────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────

@dataclass
class SearchConfig:
    size: int = 1                      # conditions combined per entry/exit
    min_trades: int = 10
    min_sharpe: float = 0.5            # risk-adjusted filter (fix #2)
    max_drawdown_pct: float = -35.0    # reject anything worse than this (fix #2)
    is_ratio: float = 0.35
    oos_ratio: float = 0.35
    notest_ratio: float = 0.30
    n_walkforward_folds: int = 3       # fix #4
    stress_fee: float = 0.003          # 0.3% vs base 0.1% (fix #5)
    stress_slippage: float = 0.006     # 0.6% vs base 0.2% (fix #5)
    base_fee: float = 0.001
    base_slippage: float = 0.002
    init_cash: float = 100_000
    max_attempts: int = 20_000         # hard ceiling so this can't loop forever


@dataclass
class SearchResult:
    entry: list
    exit_: list
    attempts_tried: int
    symbols_validated: list
    fold_stats: list = field(default_factory=list)
    stress_test_passed: bool = False
    stress_sharpe: float = None


# ───────────────────────────────────────────────────────────────
# Backtest helper
# ───────────────────────────────────────────────────────────────

def _run_backtest(df: pd.DataFrame, entry_cols: list, exit_cols: list,
                   fee: float, slippage: float, init_cash: float):
    df = df.copy()
    df["entry_signal"] = df[entry_cols].all(axis=1)
    df["exit_signal"] = df[exit_cols].all(axis=1)

    entries = df["entry_signal"].shift(1).astype(bool).fillna(False).to_numpy()
    exits = df["exit_signal"].shift(1).astype(bool).fillna(False).to_numpy()

    pf = vbt.Portfolio.from_signals(
        close=df["Open"],
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        fees=fee,
        slippage=slippage,
        freq="1d",
    )
    return pf


def _passes_risk_filter(pf, cfg: SearchConfig) -> bool:
    stats = pf.stats()
    trades_ok = stats.get("Total Trades", 0) >= cfg.min_trades
    sharpe = stats.get("Sharpe Ratio", np.nan)
    sharpe_ok = (not np.isnan(sharpe)) and sharpe >= cfg.min_sharpe
    max_dd = stats.get("Max Drawdown [%]", -100.0)
    dd_ok = max_dd >= cfg.max_drawdown_pct
    return trades_ok and sharpe_ok and dd_ok


# ───────────────────────────────────────────────────────────────
# The generator
# ───────────────────────────────────────────────────────────────

class Generator10X:
    """
    Multi-symbol, walk-forward, risk-adjusted, attempt-tracked,
    cost-stress-tested strategy search.

    Usage:
        gen = Generator10X({"NVDA": df_nvda, "AAPL": df_aapl, "MSFT": df_msft},
                            config=SearchConfig())
        result = gen.search()
    """

    def __init__(self, symbol_frames: dict, config: SearchConfig = None):
        """symbol_frames: {symbol: OHLCV DataFrame} — must share a condition set shape."""
        self.symbol_frames = symbol_frames
        self.cfg = config or SearchConfig()
        self.symbol_conditions = {
            sym: build_all_conditions(df) for sym, df in symbol_frames.items()
        }
        self.all_columns = sorted(next(iter(self.symbol_conditions.values())).keys())
        # Build each symbol's full (OHLCV + conditions) frame once — reused every attempt.
        self._condition_frames = {}
        for sym, base in symbol_frames.items():
            cond_df = pd.DataFrame(self.symbol_conditions[sym], index=base.index)
            self._condition_frames[sym] = pd.concat([base, cond_df], axis=1)

    def _condition_frame(self, symbol: str) -> pd.DataFrame:
        return self._condition_frames[symbol]

    def _walkforward_folds(self, df: pd.DataFrame):
        """Yield (is_slice, oos_slice) pairs — rolling, non-overlapping, chronological."""
        n = len(df)
        n_folds = self.cfg.n_walkforward_folds
        fold_size = n // (n_folds + 1)
        for i in range(n_folds):
            is_start = i * fold_size
            is_end = is_start + fold_size
            oos_end = is_end + fold_size
            if oos_end > n:
                break
            yield df.iloc[is_start:is_end], df.iloc[is_end:oos_end]

    def random_strategy(self):
        entry = list(np.random.choice(self.all_columns, size=self.cfg.size, replace=False))
        remaining = [c for c in self.all_columns if c not in entry]
        exit_ = list(np.random.choice(remaining, size=self.cfg.size, replace=False))
        return entry, exit_

    def _passes_all_symbols_walkforward(self, entry: list, exit_: list) -> tuple:
        """Fixes #3 and #4: every symbol, every walk-forward fold must pass."""
        fold_stats = []
        for symbol in self.symbol_frames:
            frame = self._condition_frame(symbol)
            folds = list(self._walkforward_folds(frame))
            if not folds:
                return False, fold_stats
            for is_df, oos_df in folds:
                pf_is = _run_backtest(is_df, entry, exit_, self.cfg.base_fee,
                                       self.cfg.base_slippage, self.cfg.init_cash)
                if not _passes_risk_filter(pf_is, self.cfg):
                    return False, fold_stats
                pf_oos = _run_backtest(oos_df, entry, exit_, self.cfg.base_fee,
                                        self.cfg.base_slippage, self.cfg.init_cash)
                if not _passes_risk_filter(pf_oos, self.cfg):
                    return False, fold_stats
                fold_stats.append({
                    "symbol": symbol,
                    "is_sharpe": round(float(pf_is.stats().get("Sharpe Ratio", np.nan)), 2),
                    "oos_sharpe": round(float(pf_oos.stats().get("Sharpe Ratio", np.nan)), 2),
                })
        return True, fold_stats

    def _stress_test(self, entry: list, exit_: list) -> tuple:
        """Fix #5: does it still show a positive Sharpe under stressed costs, on every symbol?"""
        sharpes = []
        for symbol in self.symbol_frames:
            frame = self._condition_frame(symbol)
            pf = _run_backtest(frame, entry, exit_, self.cfg.stress_fee,
                                self.cfg.stress_slippage, self.cfg.init_cash)
            sharpe = pf.stats().get("Sharpe Ratio", np.nan)
            sharpes.append(sharpe)
        if any(np.isnan(s) for s in sharpes):
            return False, None
        min_sharpe = min(sharpes)
        return min_sharpe > 0, round(float(min_sharpe), 2)

    def search(self, verbose: bool = True) -> SearchResult:
        attempts = 0
        start = time.time()
        while attempts < self.cfg.max_attempts:
            attempts += 1
            entry, exit_ = self.random_strategy()

            passed, fold_stats = self._passes_all_symbols_walkforward(entry, exit_)
            if not passed:
                continue

            stress_passed, stress_sharpe = self._stress_test(entry, exit_)

            if verbose:
                elapsed = time.time() - start
                print(f"♛ Candidate found after {attempts} attempts ({elapsed:.1f}s)")
                print(f"  Entry: {entry}")
                print(f"  Exit:  {exit_}")
                print(f"  Cost-stress test: {'PASSED' if stress_passed else 'FAILED'} "
                      f"(min Sharpe under stress = {stress_sharpe})")

            if not stress_passed:
                # Passed the walk-forward gate but died under realistic costs — keep searching.
                continue

            return SearchResult(
                entry=entry, exit_=exit_, attempts_tried=attempts,
                symbols_validated=list(self.symbol_frames.keys()),
                fold_stats=fold_stats,
                stress_test_passed=stress_passed,
                stress_sharpe=stress_sharpe,
            )

        raise RuntimeError(
            f"♛ No strategy passed all gates in {self.cfg.max_attempts} attempts. "
            f"This is itself a meaningful result — it suggests this condition library, "
            f"at this size/filter combination, doesn't contain an easy multi-symbol edge. "
            f"Consider loosening min_sharpe, increasing size, or reviewing symbol_frames."
        )
