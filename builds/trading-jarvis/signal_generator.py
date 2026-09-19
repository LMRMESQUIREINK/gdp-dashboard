# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Signal generator — RSI-cross + volume confirmation
#  Data Layer: none (pure function of an OHLCV frame)
#  Generated: 2026-09-19 (completes the Trading Jarvis build)
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: signal_generator.py                           ║
║      Role:      RSI(threshold) cross + volume confirmation     ║
║      Default:   threshold=65, no lookahead                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

This module never fires on data it couldn't have known about at the
time — every indicator is computed from bars up to and including the
one it signals on, and generate_signals() expects one row per
COMPLETED bar (feed it EOD or otherwise-closed data, e.g. from
data_pipeline.get_recent_ohlcv() or a live_monitor frame with the
final row's price overlaid onto an otherwise-real bar).

WHY RSI-CROSS, NOT RSI-REVERSION
    Classic RSI treats RSI > 70 as overbought (sell) and RSI < 30 as
    oversold (buy) — mean-reversion. The 65 default here doesn't fit
    that convention (65 is below the classic 70 line), so this build
    treats a cross ABOVE the threshold as bullish momentum breaking
    out (BUY, confirmed by above-average volume), and a cross below
    the symmetric lower threshold (100 - threshold) as momentum
    breaking down (SELL). If you actually want mean-reversion RSI
    instead, that's a different, equally valid strategy — the two
    comparisons below are what would flip.

INPUT CONTRACT
    generate_signals() expects a DataFrame with at least
    ["adjusted_close", "volume"] columns, one row per completed bar.
"""

import pandas as pd


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    """Wilder's RSI via EWM — vectorized, same smoothing style as
    risk_manager.atr()."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return (100 - (100 / (1 + rs))).fillna(50)  # neutral while warming up


def volume_confirms(volume: pd.Series, window: int = 20) -> pd.Series:
    """True where volume is above its own rolling average."""
    return volume > volume.rolling(window, min_periods=1).mean()


def _crosses_above(series: pd.Series, level: float) -> pd.Series:
    return (series > level) & (series.shift(1) <= level)


def _crosses_below(series: pd.Series, level: float) -> pd.Series:
    return (series < level) & (series.shift(1) >= level)


def generate_signals(frame: pd.DataFrame, rsi_threshold: float = 65,
                      rsi_period: int = 14, volume_window: int = 20) -> pd.DataFrame:
    """Returns a copy of `frame` with rsi/signal columns added.
    signal is one of "BUY", "SELL", "HOLD" per row.

    BUY : RSI crosses above rsi_threshold AND volume confirms.
    SELL: RSI crosses below (100 - rsi_threshold) — no volume gate on
          the way down; exits shouldn't wait on the same confirmation
          entries do.
    """
    out = frame.copy()
    out["rsi"] = rsi(out["adjusted_close"], n=rsi_period)

    lower_threshold = 100 - rsi_threshold
    buy = _crosses_above(out["rsi"], rsi_threshold) & volume_confirms(out["volume"], volume_window)
    sell = _crosses_below(out["rsi"], lower_threshold)

    out["signal"] = "HOLD"
    out.loc[buy, "signal"] = "BUY"
    out.loc[sell, "signal"] = "SELL"
    return out


def latest_signal(signaled: pd.DataFrame) -> str:
    """The most recent row's signal — what a live check reports."""
    if signaled.empty or "signal" not in signaled.columns:
        return "HOLD"
    return str(signaled["signal"].iloc[-1])


if __name__ == "__main__":
    import numpy as np

    idx = pd.date_range("2024-01-01", periods=200, freq="B")
    rng = np.random.default_rng(0)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1.2, 200)), index=idx)
    volume = pd.Series(rng.integers(800_000, 2_200_000, 200), index=idx)
    frame = pd.DataFrame({"adjusted_close": close, "volume": volume})

    result = generate_signals(frame)
    print(f"♛ Signal counts:\n{result['signal'].value_counts()}")
    print(f"♛ Latest signal: {latest_signal(result)}")
