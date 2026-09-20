"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: indicators.py                                 ║
║      Role:      Core indicator math, all vectorized except     ║
║                  KAMA's inherently recursive smoothing step    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Every function here takes/returns pandas Series or DataFrames indexed
the same as the input OHLCV frame. Columns expected: Open, High, Low,
Close, Volume (matches yfinance's default column names, same as the
original Kryptera script).
"""

import numpy as np
import pandas as pd


# ───────────────────────────────────────────────────────────────
# Bollinger Bands
# ───────────────────────────────────────────────────────────────

def bollinger_bands(close: pd.Series, period: int = 20, std_mult: float = 2.0):
    ma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = ma + std_mult * std
    lower = ma - std_mult * std
    return ma, upper, lower


# ───────────────────────────────────────────────────────────────
# Hull Moving Average
# ───────────────────────────────────────────────────────────────

def hull_ma(series: pd.Series, length: int) -> pd.Series:
    half = max(int(length / 2), 1)
    sqrt_len = max(int(np.sqrt(length)), 1)
    wma_half = series.rolling(half).mean()
    wma_full = series.rolling(length).mean()
    diff = 2 * wma_half - wma_full
    return diff.rolling(sqrt_len).mean()


# ───────────────────────────────────────────────────────────────
# KAMA — inherently recursive (adaptive smoothing constant depends
# on its own prior output), so a single O(n) pass is unavoidable.
# We use raw numpy arrays instead of pandas .iloc for speed.
# ───────────────────────────────────────────────────────────────

def kama(series: pd.Series, length: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
    values = series.to_numpy(dtype=float)
    n = len(values)
    change = np.abs(np.diff(values, n=length, prepend=[np.nan] * length))
    abs_diff = np.abs(np.diff(values, prepend=[np.nan]))
    volatility = pd.Series(abs_diff).rolling(length).sum().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        er = np.where(volatility != 0, change / volatility, 0.0)
    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    er = np.clip(np.nan_to_num(er, nan=0.0), 0.0, 1.0)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    sc = np.clip(np.nan_to_num(sc, nan=slow_sc ** 2), slow_sc ** 2, fast_sc ** 2)

    out = np.empty(n)
    out[0] = values[0] if not np.isnan(values[0]) else 0.0
    for i in range(1, n):
        prev = out[i - 1]
        v = values[i]
        if np.isnan(v):
            out[i] = prev
        else:
            out[i] = prev + sc[i] * (v - prev)
    return pd.Series(out, index=series.index)


# ───────────────────────────────────────────────────────────────
# Kaufman Efficiency Ratio
# ───────────────────────────────────────────────────────────────

def efficiency_ratio(close: pd.Series, period: int = 14) -> pd.Series:
    change = close.diff(period).abs()
    volatility = close.diff().abs().rolling(period).sum()
    return change / volatility


# ───────────────────────────────────────────────────────────────
# RSI
# ───────────────────────────────────────────────────────────────

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = gain / loss
    return 100 - (100 / (1 + rs))


# ───────────────────────────────────────────────────────────────
# MACD
# ───────────────────────────────────────────────────────────────

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


# ───────────────────────────────────────────────────────────────
# ADX / DMI
# ───────────────────────────────────────────────────────────────

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    return pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    tr = true_range(high, low, close)
    atr_ = tr.ewm(span=period, adjust=False).mean()
    dm_pos = (high - high.shift()).clip(lower=0)
    dm_neg = (low.shift() - low).clip(lower=0)
    dm_pos = dm_pos.where(dm_pos > dm_neg, 0.0)
    dm_neg = dm_neg.where(dm_neg > dm_pos, 0.0)
    di_pos = 100 * dm_pos.ewm(span=period, adjust=False).mean() / atr_
    di_neg = 100 * dm_neg.ewm(span=period, adjust=False).mean() / atr_
    with np.errstate(divide="ignore", invalid="ignore"):
        dx = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg)
    adx_ = dx.ewm(span=period, adjust=False).mean()
    return adx_, di_pos, di_neg


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    return true_range(high, low, close).ewm(span=period, adjust=False).mean()


# ───────────────────────────────────────────────────────────────
# Donchian Channel
# ───────────────────────────────────────────────────────────────

def donchian(high: pd.Series, low: pd.Series, period: int = 20):
    upper = high.rolling(period).max()
    lower = low.rolling(period).min()
    mid = (upper + lower) / 2
    return upper, mid, lower


# ───────────────────────────────────────────────────────────────
# Stochastic Oscillator
# ───────────────────────────────────────────────────────────────

def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                k_period: int = 14, d_period: int = 3):
    lowest = low.rolling(k_period).min()
    highest = high.rolling(k_period).max()
    with np.errstate(divide="ignore", invalid="ignore"):
        pct_k = 100 * (close - lowest) / (highest - lowest)
    pct_d = pct_k.rolling(d_period).mean()
    return pct_k, pct_d


# ───────────────────────────────────────────────────────────────
# Volume: OBV, volume z-score, VWAP deviation
# ───────────────────────────────────────────────────────────────

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


def volume_zscore(volume: pd.Series, lookback: int = 20) -> pd.Series:
    mean = volume.rolling(lookback).mean()
    std = volume.rolling(lookback).std()
    with np.errstate(divide="ignore", invalid="ignore"):
        return (volume - mean) / std


def rolling_vwap(close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
    pv = (close * volume).rolling(period).sum()
    v = volume.rolling(period).sum()
    return pv / v


# ───────────────────────────────────────────────────────────────
# Z-score mean reversion + Rate of Change
# ───────────────────────────────────────────────────────────────

def zscore(close: pd.Series, lookback: int = 20) -> pd.Series:
    mean = close.rolling(lookback).mean()
    std = close.rolling(lookback).std()
    with np.errstate(divide="ignore", invalid="ignore"):
        return (close - mean) / std


def roc(close: pd.Series, period: int = 10) -> pd.Series:
    return close.pct_change(period) * 100
