"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: conditions.py                                 ║
║      Role:      Condition factory — builds the full           ║
║                  searchable boolean library from indicators.py ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

This is the file README_10X.md describes as `conditions.py` and
`strategy_generator_10x.py` imports as `build_all_conditions` — it did
not exist in any upload (same "core file referenced, never uploaded"
pattern as every other round of this build). Written here from
indicators.py's function library plus README_10X.md's stated 12-family
scope (BB, HMA, KAMA, ER, RSI, MACD, ADX, ATR, Donchian, Stochastic,
OBV/VWAP, Z-score/ROC).

DESIGN NOTE — fixed parameter grid, not per-trial random params.
`Generator10X.random_strategy()` (strategy_generator_10x.py) treats each
key of `build_all_conditions()`'s output as one fixed, named column and
draws entry/exit conditions BY NAME — it does not re-sample parameters
per trial. So this factory's job is to pre-build a rich, fixed library
of (indicator, parameter-preset, comparison) combinations, not to
generate one parametric condition per family. That's a real design
difference from `ruthless_strategy_lab_10x.py`'s registry, which DOES
randomize parameters per trial (see that file's own docstring) — the
two are deliberately different search strategies, not the same thing
twice. Each family below uses 2-3 period/parameter presets crossed with
a handful of distinct boolean comparisons, landing at 12 conditions per
family (144 total) — close to, and in the same spirit as, README_10X.md's
stated "145 conditions across 12 families" (that number was never
hardcoded there either; it's whatever this factory actually produces,
verified at runtime by run_10x.py printing `len(gen.all_columns)`).

Every function returns a raw (unshifted) boolean pd.Series aligned to
the input df's index. Shifting by 1 bar before it touches a backtest
happens downstream, in strategy_generator_10x.py's `_run_backtest` —
consistent with the lookahead-bias pattern this whole build follows.
"""

import pandas as pd

from indicators import (
    bollinger_bands, hull_ma, kama, efficiency_ratio, rsi, macd,
    adx, atr, donchian, stochastic, obv, rolling_vwap, zscore, roc,
)


def _cross_above(a: pd.Series, b) -> pd.Series:
    b = b if isinstance(b, pd.Series) else pd.Series(b, index=a.index)
    return (a > b) & (a.shift(1) <= b.shift(1))


def _cross_below(a: pd.Series, b) -> pd.Series:
    b = b if isinstance(b, pd.Series) else pd.Series(b, index=a.index)
    return (a < b) & (a.shift(1) >= b.shift(1))


# ───────────────────────────────────────────────────────────────
# Bollinger Bands — 3 periods x 4 comparisons = 12
# ───────────────────────────────────────────────────────────────

def _bb_conditions(df: pd.DataFrame) -> dict:
    out = {}
    for period in (14, 20, 30):
        mid, upper, lower = bollinger_bands(df["Close"], period=period, std_mult=2.0)
        out[f"BB_CloseAboveUpper_{period}"] = df["Close"] > upper
        out[f"BB_CloseBelowLower_{period}"] = df["Close"] < lower
        out[f"BB_CloseAboveMid_{period}"] = df["Close"] > mid
        out[f"BB_CloseBelowMid_{period}"] = df["Close"] < mid
    return out


# ───────────────────────────────────────────────────────────────
# Hull Moving Average — 3 fast/slow pairs x (above/cross-up/cross-dn) + 3 rising = 12
# ───────────────────────────────────────────────────────────────

def _hma_conditions(df: pd.DataFrame) -> dict:
    out = {}
    pairs = ((9, 20), (20, 50), (9, 50))
    for fast, slow in pairs:
        hma_fast = hull_ma(df["Close"], fast)
        hma_slow = hull_ma(df["Close"], slow)
        out[f"HMA_FastAboveSlow_{fast}_{slow}"] = hma_fast > hma_slow
        out[f"HMA_CrossAbove_{fast}_{slow}"] = _cross_above(hma_fast, hma_slow)
        out[f"HMA_CrossBelow_{fast}_{slow}"] = _cross_below(hma_fast, hma_slow)
    for length in (9, 20, 50):
        out[f"HMA_Rising_{length}"] = hull_ma(df["Close"], length).diff() > 0
    return out


# ───────────────────────────────────────────────────────────────
# KAMA — 3 fast/slow length pairs x (above/cross-up/cross-dn) + 3 rising = 12
# ───────────────────────────────────────────────────────────────

def _kama_conditions(df: pd.DataFrame) -> dict:
    out = {}
    pairs = ((10, 30), (5, 20), (20, 50))
    for fast_len, slow_len in pairs:
        kama_fast = kama(df["Close"], length=fast_len)
        kama_slow = kama(df["Close"], length=slow_len)
        out[f"KAMA_FastAboveSlow_{fast_len}_{slow_len}"] = kama_fast > kama_slow
        out[f"KAMA_CrossAbove_{fast_len}_{slow_len}"] = _cross_above(kama_fast, kama_slow)
        out[f"KAMA_CrossBelow_{fast_len}_{slow_len}"] = _cross_below(kama_fast, kama_slow)
    for length in (10, 20, 30):
        out[f"KAMA_Rising_{length}"] = kama(df["Close"], length=length).diff() > 0
    return out


# ───────────────────────────────────────────────────────────────
# Efficiency Ratio — 3 periods x (trend-high/trend-low/choppy/rising) = 12
# ───────────────────────────────────────────────────────────────

def _er_conditions(df: pd.DataFrame) -> dict:
    out = {}
    for period in (10, 14, 20):
        er = efficiency_ratio(df["Close"], period=period)
        out[f"ER_TrendingHigh_{period}"] = er > 0.5
        out[f"ER_TrendingLow_{period}"] = er > 0.3
        out[f"ER_Choppy_{period}"] = er < 0.3
        out[f"ER_Rising_{period}"] = er.diff() > 0
    return out


# ───────────────────────────────────────────────────────────────
# RSI — 3 periods x (above70/below30/cross-up50/cross-dn50) = 12
# ───────────────────────────────────────────────────────────────

def _rsi_conditions(df: pd.DataFrame) -> dict:
    out = {}
    for period in (7, 14, 21):
        r = rsi(df["Close"], period=period)
        out[f"RSI_Above70_{period}"] = r > 70
        out[f"RSI_Below30_{period}"] = r < 30
        out[f"RSI_CrossAbove50_{period}"] = _cross_above(r, 50)
        out[f"RSI_CrossBelow50_{period}"] = _cross_below(r, 50)
    return out


# ───────────────────────────────────────────────────────────────
# MACD — 3 fast/slow/signal presets x (bull/bear/above0/below0) = 12
# ───────────────────────────────────────────────────────────────

def _macd_conditions(df: pd.DataFrame) -> dict:
    out = {}
    presets = ((12, 26, 9), (5, 35, 5), (8, 21, 5))
    for fast, slow, signal in presets:
        macd_line, signal_line, _hist = macd(df["Close"], fast=fast, slow=slow, signal=signal)
        tag = f"{fast}_{slow}_{signal}"
        out[f"MACD_BullCross_{tag}"] = _cross_above(macd_line, signal_line)
        out[f"MACD_BearCross_{tag}"] = _cross_below(macd_line, signal_line)
        out[f"MACD_AboveZero_{tag}"] = macd_line > 0
        out[f"MACD_BelowZero_{tag}"] = macd_line < 0
    return out


# ───────────────────────────────────────────────────────────────
# ADX/DMI — 3 periods x (trending/choppy/+DI>-DI/-DI>+DI) = 12
# ───────────────────────────────────────────────────────────────

def _adx_conditions(df: pd.DataFrame) -> dict:
    out = {}
    for period in (14, 20, 28):
        adx_, di_pos, di_neg = adx(df["High"], df["Low"], df["Close"], period=period)
        out[f"ADX_Trending_{period}"] = adx_ > 25
        out[f"ADX_Choppy_{period}"] = adx_ < 20
        out[f"ADX_DIPosAboveNeg_{period}"] = di_pos > di_neg
        out[f"ADX_DINegAbovePos_{period}"] = di_neg > di_pos
    return out


# ───────────────────────────────────────────────────────────────
# ATR — 3 periods x (expanding/contracting/high-vol/low-vol) = 12
# ───────────────────────────────────────────────────────────────

def _atr_conditions(df: pd.DataFrame) -> dict:
    out = {}
    for period in (7, 14, 21):
        a = atr(df["High"], df["Low"], df["Close"], period=period)
        a_ma = a.rolling(period).mean()
        out[f"ATR_Expanding_{period}"] = a > a_ma
        out[f"ATR_Contracting_{period}"] = a < a_ma
        out[f"ATR_HighVol_{period}"] = a > (a_ma * 1.5)
        out[f"ATR_LowVol_{period}"] = a < (a_ma * 0.7)
    return out


# ───────────────────────────────────────────────────────────────
# Donchian Channel — 3 lookbacks x (breakout-up/breakout-dn/above-mid/below-mid) = 12
# ───────────────────────────────────────────────────────────────

def _donchian_conditions(df: pd.DataFrame) -> dict:
    out = {}
    for period in (10, 20, 55):
        upper, mid, lower = donchian(df["High"], df["Low"], period=period)
        out[f"Donchian_BreakoutUp_{period}"] = df["Close"] >= upper.shift(1)
        out[f"Donchian_BreakoutDown_{period}"] = df["Close"] <= lower.shift(1)
        out[f"Donchian_AboveMid_{period}"] = df["Close"] > mid
        out[f"Donchian_BelowMid_{period}"] = df["Close"] < mid
    return out


# ───────────────────────────────────────────────────────────────
# Stochastic Oscillator — 3 (k,d) presets x (overbought/oversold/cross-up/cross-dn) = 12
# ───────────────────────────────────────────────────────────────

def _stochastic_conditions(df: pd.DataFrame) -> dict:
    out = {}
    presets = ((14, 3), (21, 5), (9, 3))
    for k_period, d_period in presets:
        pct_k, pct_d = stochastic(df["High"], df["Low"], df["Close"],
                                   k_period=k_period, d_period=d_period)
        tag = f"{k_period}_{d_period}"
        out[f"Stoch_Overbought_{tag}"] = pct_k > 80
        out[f"Stoch_Oversold_{tag}"] = pct_k < 20
        out[f"Stoch_CrossAboveD_{tag}"] = _cross_above(pct_k, pct_d)
        out[f"Stoch_CrossBelowD_{tag}"] = _cross_below(pct_k, pct_d)
    return out


# ───────────────────────────────────────────────────────────────
# OBV / VWAP — 3 lookbacks x (OBV rising/OBV above its MA/above VWAP/below VWAP) = 12
# ───────────────────────────────────────────────────────────────

def _obv_vwap_conditions(df: pd.DataFrame) -> dict:
    out = {}
    obv_ = obv(df["Close"], df["Volume"])
    for lookback in (10, 20, 30):
        out[f"OBV_Rising_{lookback}"] = obv_.diff(lookback) > 0
        out[f"OBV_AboveMA_{lookback}"] = obv_ > obv_.rolling(lookback).mean()
        vwap = rolling_vwap(df["Close"], df["Volume"], period=lookback)
        out[f"VWAP_CloseAbove_{lookback}"] = df["Close"] > vwap
        out[f"VWAP_CloseBelow_{lookback}"] = df["Close"] < vwap
    return out


# ───────────────────────────────────────────────────────────────
# Z-score / ROC — 3 lookback/period presets x (z-high/z-low/roc-up/roc-dn) = 12
# ───────────────────────────────────────────────────────────────

def _zscore_roc_conditions(df: pd.DataFrame) -> dict:
    out = {}
    presets = (20, 10, 30)
    for lookback in presets:
        z = zscore(df["Close"], lookback=lookback)
        out[f"Zscore_Above1_{lookback}"] = z > 1.0
        out[f"Zscore_BelowNeg1_{lookback}"] = z < -1.0
        r = roc(df["Close"], period=lookback)
        out[f"ROC_Positive_{lookback}"] = r > 0
        out[f"ROC_Negative_{lookback}"] = r < 0
    return out


_FAMILY_BUILDERS = (
    _bb_conditions,
    _hma_conditions,
    _kama_conditions,
    _er_conditions,
    _rsi_conditions,
    _macd_conditions,
    _adx_conditions,
    _atr_conditions,
    _donchian_conditions,
    _stochastic_conditions,
    _obv_vwap_conditions,
    _zscore_roc_conditions,
)


def build_all_conditions(df: pd.DataFrame) -> dict:
    """
    Build the full 12-family condition library for one OHLCV DataFrame.
    Returns {condition_name: boolean pd.Series}, all aligned to df.index,
    NaN-filled comparisons left as NaN/False (the generator's own
    `.fillna(False)` step, applied downstream, handles that).
    """
    conditions = {}
    for builder in _FAMILY_BUILDERS:
        conditions.update(builder(df))
    return conditions
