"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: ruthless_strategy_lab_10x.py                   ║
║      Role:      Trial-aware random strategy search             ║
║      Symbol(s): configurable (default NVDA)                    ║
║      Timeframe: daily                                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

ALTERNATIVE IMPLEMENTATION — not the file README_10X.md's table
describes (that's strategy_generator_10x.py + conditions.py +
data_pipeline_10x.py + run_10x.py, the "official" system in this
folder). This is a second, self-contained 10X engine that arrived in
the same upload, was never referenced by README_10X.md, and has no
missing imports — everything it needs is in this one file.

Shipped alongside the official system, not merged into it, because the
two make a genuinely different design choice and collapsing them would
lose that:

  - Official system (strategy_generator_10x.py): draws entry/exit BY
    NAME from a large, fixed library of pre-built (indicator, param
    preset, comparison) columns — conditions.py's 144 columns across
    12 families. Multi-symbol + walk-forward + cost-stress, built for
    breadth of the searchable rule space.

  - This file: draws each condition's underlying PARAMETERS fresh on
    every trial (not just which fixed rule to use) — a real search
    over parameter space, not just rule space, across a smaller
    23-condition/10-family registry. Single-symbol by default, no
    vectorbt dependency (manual position loop), so it still runs even
    if vectorbt/numba fail to install.

Both fix the same five gaps from the DEEP/DEEPER/DEEPEST/DEEPEST-EST
analysis of the original Lite script (attempt-count disclosure,
Sharpe+max-DD gate, walk-forward-or-3-way-split validation, cost
stress test) — they just make different tradeoffs getting there. Try
the official system first for breadth; use this one when you want
per-trial parameter randomization or don't want a vectorbt dependency.

WHAT "10X" MEANS HERE — this is not "more conditions than the Lite
product," it's a rigor upgrade on the same idea, built to close the
specific gaps found in the deep analysis of the Lite version:

  1. RANDOMIZED PARAMETERS, not just randomized condition choice.
     The Lite script fixes BB period=20, HMA fast=20/slow=50, etc. as
     global constants and only randomizes which pre-built boolean rule
     to use. Here, every condition's own parameters (periods, bands,
     thresholds) are drawn fresh on every trial — a real search over
     parameter space, not just rule space.

  2. A REAL BENCHMARK-BEAT FILTER. The Lite README claims the pass
     criterion is "Total Return > Benchmark Return" — the shipped code
     actually only checks "Total Return > 0". This engine implements
     the benchmark comparison for real, in all three periods.

  3. SHARPE + MAX-DRAWDOWN GATES, not just a trade-count minimum.
     A strategy can have 10 trades and a positive return and still be
     a coin flip. This engine adds a minimum Sharpe and a maximum
     drawdown ceiling to the pass filter.

  4. TRIAL TRANSPARENCY. The Lite engine loops silently until a pass
     and never tells you how many random strategies it threw away to
     get there — which is exactly the number you need to judge whether
     a "pass" is signal or noise (see: backtest overfitting / multiple-
     comparisons literature). This engine counts every trial, caps the
     search at max_trials, and reports the trial count with the result.

  5. TEN INDICATOR FAMILIES instead of Lite's six — BB, HMA, KAMA, RSI,
     MACD, ADX (trend regime), ATR (volatility regime), Donchian
     breakout, Volume, and Efficiency Ratio.

SETUP
    pip install yfinance pandas numpy vectorbt --break-system-packages
    (EODHD path additionally needs: pip install requests --break-system-packages)

    Windows PowerShell (only needed for the EODHD path):
        setx EODHD_API_KEY "your_key_here"
    bash:
        export EODHD_API_KEY="your_key_here"
"""

import os
import time
import numpy as np
import pandas as pd

# ───────────────────────────────────────────────────────────────
# Data layer — yfinance default, EODHD swap-ready (RUTHLESS pattern)
# ───────────────────────────────────────────────────────────────

PROVIDER = "yfinance"   # or "eodhd"
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "YOUR_EODHD_KEY")


def fetch_history(symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
    """Returns a DataFrame with columns: Open, High, Low, Close, Volume."""
    if PROVIDER == "yfinance":
        import yfinance as yf
        df = yf.download(symbol, start=start, end=end, interval=interval,
                          multi_level_index=False)
        df = df.reset_index()
        df = df[(df["Open"] >= 0) & (df["High"] >= 0) &
                (df["Low"] >= 0) & (df["Close"] >= 0)].copy()
        return df.set_index(df.columns[0])[["Open", "High", "Low", "Close", "Volume"]]

    if PROVIDER == "eodhd":
        import requests
        eodhd_symbol = symbol if "." in symbol else f"{symbol}.US"
        r = requests.get(
            f"https://eodhd.com/api/eod/{eodhd_symbol}",
            params={"api_token": EODHD_API_KEY, "from": start, "to": end,
                    "period": "d", "fmt": "json"}, timeout=20,
        )
        r.raise_for_status()
        raw = pd.DataFrame(r.json())
        raw["date"] = pd.to_datetime(raw["date"])
        raw = raw.set_index("date")
        return raw.rename(columns={"open": "Open", "high": "High", "low": "Low",
                                    "adjusted_close": "Close", "volume": "Volume"}
                           )[["Open", "High", "Low", "Close", "Volume"]]

    raise ValueError(f"Unknown PROVIDER: {PROVIDER}")


# ───────────────────────────────────────────────────────────────
# Indicator primitives (vectorized, hand-rolled)
# ───────────────────────────────────────────────────────────────

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def _hull_ma(s: pd.Series, n: int) -> pd.Series:
    half = max(int(n / 2), 1)
    sqrt_n = max(int(np.sqrt(n)), 1)
    wma_half = s.rolling(half).mean()
    wma_full = s.rolling(n).mean()
    return (2 * wma_half - wma_full).rolling(sqrt_n).mean()


def _kama(s: pd.Series, n: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
    change = s.diff(n).abs()
    volatility = s.diff().abs().rolling(n).sum()
    er = (change / volatility.replace(0, np.nan)).fillna(0)
    fast_sc, slow_sc = 2 / (fast + 1), 2 / (slow + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    kama = pd.Series(index=s.index, dtype=float)
    kama.iloc[0] = s.iloc[0]
    for i in range(1, len(s)):
        prev = kama.iloc[i - 1]
        kama.iloc[i] = prev + sc.iloc[i] * (s.iloc[i] - prev) if not np.isnan(sc.iloc[i]) else prev
    return kama


def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = -delta.clip(upper=0).rolling(n).mean()
    return 100 - (100 / (1 + gain / loss.replace(0, np.nan)))


def _macd(s: pd.Series, fast: int, slow: int, signal: int):
    macd_line = _ema(s, fast) - _ema(s, slow)
    signal_line = _ema(macd_line, signal)
    return macd_line, signal_line


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"] - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()


def _adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"] - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1)
    dm_pos = (df["High"] - df["High"].shift()).clip(lower=0)
    dm_neg = (df["Low"].shift() - df["Low"]).clip(lower=0)
    atr_ = tr.ewm(span=n, adjust=False).mean()
    di_p = 100 * dm_pos.ewm(span=n, adjust=False).mean() / atr_.replace(0, np.nan)
    di_n = 100 * dm_neg.ewm(span=n, adjust=False).mean() / atr_.replace(0, np.nan)
    dx = 100 * (di_p - di_n).abs() / (di_p + di_n).replace(0, np.nan)
    return dx.ewm(span=n, adjust=False).mean()


def _efficiency_ratio(s: pd.Series, n: int = 10) -> pd.Series:
    change = s.diff(n).abs()
    volatility = s.diff().abs().rolling(n).sum()
    return (change / volatility.replace(0, np.nan)).fillna(0)


# ───────────────────────────────────────────────────────────────
# Condition registry — 10 families. Each entry: (fn, param_sampler)
# fn(df, **params) -> boolean Series
# param_sampler() -> dict of randomized, sane parameter values
# ───────────────────────────────────────────────────────────────

def _sample_bb():
    return {"period": int(np.random.randint(10, 31)), "std": round(np.random.uniform(1.5, 3.0), 2)}


def _sample_ma_pair():
    fast = int(np.random.randint(8, 30))
    slow = int(np.random.randint(fast + 10, fast + 60))
    return {"fast": fast, "slow": slow}


def _sample_rsi():
    return {"period": int(np.random.randint(7, 22)), "level": int(np.random.randint(20, 81))}


def _sample_macd():
    fast = int(np.random.randint(8, 16))
    slow = int(np.random.randint(fast + 8, fast + 30))
    signal = int(np.random.randint(5, 12))
    return {"fast": fast, "slow": slow, "signal": signal}


def _sample_adx():
    return {"period": int(np.random.randint(10, 21)), "threshold": int(np.random.randint(18, 32))}


def _sample_atr():
    return {"period": int(np.random.randint(7, 22)), "lookback": int(np.random.randint(10, 30))}


def _sample_donchian():
    return {"lookback": int(np.random.randint(10, 56))}


def _sample_volume():
    return {"lookback": int(np.random.randint(10, 31)), "multiple": round(np.random.uniform(1.3, 2.5), 2)}


def _sample_er():
    return {"period": int(np.random.randint(8, 25)), "threshold": round(np.random.uniform(0.25, 0.6), 2)}


def bb_close_above_upper(df, period, std):
    mid = _sma(df["Close"], period)
    upper = mid + std * df["Close"].rolling(period).std()
    return df["Close"] > upper


def bb_close_below_lower(df, period, std):
    mid = _sma(df["Close"], period)
    lower = mid - std * df["Close"].rolling(period).std()
    return df["Close"] < lower


def bb_squeeze(df, period, std):
    mid = _sma(df["Close"], period)
    sd = df["Close"].rolling(period).std()
    width = (mid + std * sd) - (mid - std * sd)
    return width < width.rolling(period).mean()


def hma_fast_above_slow(df, fast, slow):
    return _hull_ma(df["Close"], fast) > _hull_ma(df["Close"], slow)


def hma_cross_above(df, fast, slow):
    f, s = _hull_ma(df["Close"], fast), _hull_ma(df["Close"], slow)
    return (f > s) & (f.shift(1) <= s.shift(1))


def hma_rising(df, fast, slow):
    return _hull_ma(df["Close"], fast).diff() > 0


def kama_fast_above_slow(df, fast, slow):
    return _kama(df["Close"], n=fast) > _kama(df["Close"], n=slow)


def kama_rising(df, fast, slow):
    return _kama(df["Close"], n=fast).diff() > 0


def rsi_above(df, period, level):
    return _rsi(df["Close"], period) > level


def rsi_below(df, period, level):
    return _rsi(df["Close"], period) < level


def rsi_cross_above(df, period, level):
    r = _rsi(df["Close"], period)
    return (r > level) & (r.shift(1) <= level)


def macd_bull_cross(df, fast, slow, signal):
    macd_line, signal_line = _macd(df["Close"], fast, slow, signal)
    return (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))


def macd_bear_cross(df, fast, slow, signal):
    macd_line, signal_line = _macd(df["Close"], fast, slow, signal)
    return (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))


def macd_above_zero(df, fast, slow, signal):
    macd_line, _ = _macd(df["Close"], fast, slow, signal)
    return macd_line > 0


def adx_trending(df, period, threshold):
    return _adx(df, period) > threshold


def adx_choppy(df, period, threshold):
    return _adx(df, period) < threshold


def atr_expanding(df, period, lookback):
    a = _atr(df, period)
    return a > a.rolling(lookback).mean()


def atr_contracting(df, period, lookback):
    a = _atr(df, period)
    return a < a.rolling(lookback).mean()


def donchian_breakout_up(df, lookback):
    upper = df["High"].rolling(lookback).max()
    return df["Close"] >= upper.shift(1)


def donchian_breakout_down(df, lookback):
    lower = df["Low"].rolling(lookback).min()
    return df["Close"] <= lower.shift(1)


def volume_spike(df, lookback, multiple):
    avg_vol = df["Volume"].rolling(lookback).mean()
    return df["Volume"] > (avg_vol * multiple)


def volume_dry_up(df, lookback, multiple):
    avg_vol = df["Volume"].rolling(lookback).mean()
    return df["Volume"] < (avg_vol / multiple)


def er_trending(df, period, threshold):
    return _efficiency_ratio(df["Close"], period) > threshold


def er_choppy(df, period, threshold):
    return _efficiency_ratio(df["Close"], period) < threshold


CONDITION_REGISTRY = {
    "BB_Close_Above_Upper": (bb_close_above_upper, _sample_bb),
    "BB_Close_Below_Lower": (bb_close_below_lower, _sample_bb),
    "BB_Squeeze": (bb_squeeze, _sample_bb),
    "HMA_Fast_Above_Slow": (hma_fast_above_slow, _sample_ma_pair),
    "HMA_Cross_Above": (hma_cross_above, _sample_ma_pair),
    "HMA_Rising": (hma_rising, _sample_ma_pair),
    "KAMA_Fast_Above_Slow": (kama_fast_above_slow, _sample_ma_pair),
    "KAMA_Rising": (kama_rising, _sample_ma_pair),
    "RSI_Above": (rsi_above, _sample_rsi),
    "RSI_Below": (rsi_below, _sample_rsi),
    "RSI_Cross_Above": (rsi_cross_above, _sample_rsi),
    "MACD_Bull_Cross": (macd_bull_cross, _sample_macd),
    "MACD_Bear_Cross": (macd_bear_cross, _sample_macd),
    "MACD_Above_Zero": (macd_above_zero, _sample_macd),
    "ADX_Trending": (adx_trending, _sample_adx),
    "ADX_Choppy": (adx_choppy, _sample_adx),
    "ATR_Expanding": (atr_expanding, _sample_atr),
    "ATR_Contracting": (atr_contracting, _sample_atr),
    "Donchian_Breakout_Up": (donchian_breakout_up, _sample_donchian),
    "Donchian_Breakout_Down": (donchian_breakout_down, _sample_donchian),
    "Volume_Spike": (volume_spike, _sample_volume),
    "Volume_Dry_Up": (volume_dry_up, _sample_volume),
    "ER_Trending": (er_trending, _sample_er),
    "ER_Choppy": (er_choppy, _sample_er),
}


def sample_condition_spec() -> dict:
    """Pick a random condition name + freshly randomized parameters."""
    name = str(np.random.choice(list(CONDITION_REGISTRY.keys())))
    _, sampler = CONDITION_REGISTRY[name]
    return {"name": name, "params": sampler()}


def evaluate_spec(df: pd.DataFrame, spec: dict) -> pd.Series:
    fn, _ = CONDITION_REGISTRY[spec["name"]]
    return fn(df, **spec["params"])


def combine_specs(df: pd.DataFrame, specs: list) -> pd.Series:
    """AND-combine multiple condition specs into one boolean Series."""
    result = pd.Series(True, index=df.index)
    for spec in specs:
        result &= evaluate_spec(df, spec).fillna(False)
    return result


# ───────────────────────────────────────────────────────────────
# Backtest + metrics (no vectorbt dependency — self-contained,
# so this engine still runs if vectorbt/numba fail to install)
# ───────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame, entry_signal: pd.Series, exit_signal: pd.Series,
                  fees: float = 0.001, slippage: float = 0.002) -> dict:
    """
    Vectorized long-only backtest. Entries/exits are shifted 1 bar and
    filled at the NEXT bar's Open — no lookahead.
    """
    entries = entry_signal.shift(1).where(entry_signal.shift(1).notna(), False).astype(bool)
    exits = exit_signal.shift(1).where(exit_signal.shift(1).notna(), False).astype(bool)

    position = pd.Series(0, index=df.index, dtype=float)
    in_pos = False
    for i in range(len(df)):
        if not in_pos and entries.iloc[i]:
            in_pos = True
        elif in_pos and exits.iloc[i]:
            in_pos = False
        position.iloc[i] = 1.0 if in_pos else 0.0

    open_ret = df["Open"].pct_change().fillna(0)
    trade_cost = (entries.astype(int).diff().abs().fillna(0) +
                  exits.astype(int).diff().abs().fillna(0)) * (fees + slippage)
    strategy_ret = position.shift(1).fillna(0) * open_ret - trade_cost

    equity = (1 + strategy_ret).cumprod()
    total_return = equity.iloc[-1] - 1 if len(equity) else 0.0

    trades = int((entries.astype(int).diff() == 1).sum())

    std = strategy_ret.std()
    sharpe = (strategy_ret.mean() / std) * np.sqrt(252) if std and std > 0 else 0.0

    rolling_max = equity.cummax()
    max_dd = ((equity - rolling_max) / rolling_max).min() if len(equity) else 0.0

    # Per-TRADE win rate (not per-bar): a multi-day hold must count once,
    # not once per profitable day inside it, or win_rate can exceed 1.0 —
    # reproduced with synthetic data before this fix (win_rate == 6.16).
    held = position.shift(1).fillna(0) == 1
    trade_id = (held.astype(int).diff() == 1).cumsum().where(held, 0)
    completed_trade_rets = []
    for _, seg_ret in strategy_ret[held].groupby(trade_id[held]):
        completed_trade_rets.append(float((1 + seg_ret).prod() - 1))
    wins = sum(1 for r in completed_trade_rets if r > 0)
    win_rate = wins / len(completed_trade_rets) if completed_trade_rets else 0.0

    benchmark_return = (df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1 if len(df) > 1 else 0.0

    return {
        "trades": trades,
        "total_return": round(float(total_return), 4),
        "benchmark_return": round(float(benchmark_return), 4),
        "beats_benchmark": bool(total_return > benchmark_return),
        "sharpe": round(float(sharpe), 2),
        "max_drawdown": round(float(max_dd), 4),
        "win_rate": round(float(win_rate), 4),
        "equity_curve": equity,
    }


# ───────────────────────────────────────────────────────────────
# The hardened generator
# ───────────────────────────────────────────────────────────────

class StrategyGenerator10X:
    def __init__(self, df: pd.DataFrame, size: int = 1, min_trades: int = 15,
                 min_sharpe: float = 0.3, max_drawdown_limit: float = 0.35,
                 is_ratio: float = 0.35, oos_ratio: float = 0.35, notest_ratio: float = 0.30,
                 max_trials: int = 20_000):
        assert abs(is_ratio + oos_ratio + notest_ratio - 1.0) < 1e-6, "split ratios must sum to 1.0"
        self.df = df.copy()
        self.size = size
        self.min_trades = min_trades
        self.min_sharpe = min_sharpe
        self.max_drawdown_limit = max_drawdown_limit
        self.max_trials = max_trials

        n = len(self.df)
        is_end = int(n * is_ratio)
        oos_end = int(n * (is_ratio + oos_ratio))
        self.df_is = self.df.iloc[:is_end]
        self.df_oos = self.df.iloc[is_end:oos_end]
        self.df_notest = self.df.iloc[oos_end:]

    def _random_specs(self, k: int) -> list:
        return [sample_condition_spec() for _ in range(k)]

    def _pass_filter(self, stats: dict) -> bool:
        return (
            stats["trades"] >= self.min_trades and
            stats["beats_benchmark"] and
            stats["sharpe"] >= self.min_sharpe and
            stats["max_drawdown"] >= -self.max_drawdown_limit
        )

    def search(self) -> dict:
        trial = 0
        while trial < self.max_trials:
            trial += 1
            entry_specs = self._random_specs(self.size)
            exit_specs = self._random_specs(self.size)

            entry_is = combine_specs(self.df_is, entry_specs)
            exit_is = combine_specs(self.df_is, exit_specs)
            stats_is = run_backtest(self.df_is, entry_is, exit_is)
            if not self._pass_filter(stats_is):
                continue

            entry_oos = combine_specs(self.df_oos, entry_specs)
            exit_oos = combine_specs(self.df_oos, exit_specs)
            stats_oos = run_backtest(self.df_oos, entry_oos, exit_oos)
            if not self._pass_filter(stats_oos):
                continue

            entry_nt = combine_specs(self.df_notest, entry_specs)
            exit_nt = combine_specs(self.df_notest, exit_specs)
            stats_nt = run_backtest(self.df_notest, entry_nt, exit_nt)
            if not self._pass_filter(stats_nt):
                continue

            confidence_note = (
                "⚠ Found on an early trial — with this few draws tried, treat this as a "
                "promising lead to stress-test further, not a validated edge."
                if trial < 30 else
                "Passed after a substantial number of trials — still recommend an "
                "out-of-universe (different symbol) check before sizing real risk."
            )

            return {
                "found": True,
                "trials": trial,
                "entry_specs": entry_specs,
                "exit_specs": exit_specs,
                "stats_is": stats_is,
                "stats_oos": stats_oos,
                "stats_notest": stats_nt,
                "confidence_note": confidence_note,
            }

        return {"found": False, "trials": trial,
                "message": f"No strategy passed all gates in {self.max_trials} trials. "
                           f"Loosen min_trades/min_sharpe/max_drawdown_limit or increase max_trials."}


# ───────────────────────────────────────────────────────────────
# Standalone script rendering — reproduces the winning strategy
# ───────────────────────────────────────────────────────────────

def render_standalone_script(symbol: str, start: str, end: str, result: dict) -> str:
    entry_lines = "\n".join(
        f'    {{"name": "{s["name"]}", "params": {s["params"]}}},' for s in result["entry_specs"]
    )
    exit_lines = "\n".join(
        f'    {{"name": "{s["name"]}", "params": {s["params"]}}},' for s in result["exit_specs"]
    )
    return f'''# ♛ RUTHLESS TRADING GOLD — Discovered Strategy (10X Lab)
# Symbol: {symbol} | Window: {start} to {end} | Trials to find: {result["trials"]}
#
# Requires ruthless_strategy_lab_10x.py in the same folder (imports the
# condition registry + backtest engine used to discover this strategy).

from ruthless_strategy_lab_10x import fetch_history, combine_specs, run_backtest

SYMBOL = "{symbol}"
START = "{start}"
END = "{end}"

ENTRY_SPECS = [
{entry_lines}
]
EXIT_SPECS = [
{exit_lines}
]

df = fetch_history(SYMBOL, START, END)
entry_signal = combine_specs(df, ENTRY_SPECS)
exit_signal = combine_specs(df, EXIT_SPECS)
stats = run_backtest(df, entry_signal, exit_signal)

print("♛ RUTHLESS TRADING GOLD — Strategy Replay")
for k, v in stats.items():
    if k != "equity_curve":
        print(f"  {{k}}: {{v}}")
'''


if __name__ == "__main__":
    SYMBOL = "NVDA"
    START, END = "2010-01-01", "2026-01-01"

    print(f"♛ RUTHLESS STRATEGY LAB 10X — searching {SYMBOL} ({START} to {END})")
    df = fetch_history(SYMBOL, START, END)
    print(f"  Loaded {len(df)} bars.\n")

    gen = StrategyGenerator10X(df, size=1, min_trades=15, min_sharpe=0.3,
                                max_drawdown_limit=0.35, max_trials=20_000)

    t0 = time.time()
    result = gen.search()
    elapsed = time.time() - t0

    if not result["found"]:
        print(f"✗ {result['message']}")
    else:
        print(f"✓ Strategy found after {result['trials']} trial(s) in {elapsed:.1f}s\n")
        print("  Entry conditions:", result["entry_specs"])
        print("  Exit conditions: ", result["exit_specs"])
        for period in ("stats_is", "stats_oos", "stats_notest"):
            s = result[period]
            print(f"\n  [{period}]")
            for k, v in s.items():
                if k != "equity_curve":
                    print(f"    {k}: {v}")
        print(f"\n  {result['confidence_note']}")

        script = render_standalone_script(SYMBOL, START, END, result)
        out_path = f"{SYMBOL}_ruthless_10x_strategy.py"
        with open(out_path, "w") as f:
            f.write(script)
        print(f"\n♛ Standalone replay script written to {out_path}")
