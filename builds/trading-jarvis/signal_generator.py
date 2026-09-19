# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Signal generator — RSI momentum-breakout + volume confirmation
#  Data Layer: none (pure function of an OHLCV frame)
#  Generated: 2026-09-19 (completes the Trading Jarvis build)
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component:  signal_generator.py                          ║
║      Role:       RSI(threshold) cross + volume confirmation    ║
║      Strategy:   Momentum breakout, not mean-reversion —       ║
║                  see "Why RSI-cross, not RSI-reversion" below  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

WHY RSI-CROSS, NOT RSI-REVERSION
    Classic RSI usage treats RSI > 70 as overbought (sell) and RSI < 30
    as oversold (buy) — mean-reversion. README3.md's default threshold
    of 65 and the name "RSI-cross" don't fit that convention (65 is well
    below the classic 70 overbought line). This build treats an RSI
    cross ABOVE the threshold as bullish momentum breaking out (BUY,
    confirmed by above-average volume), and a cross below the
    symmetric lower threshold (100 - threshold) as momentum breaking
    down (SELL). If you actually want classic mean-reversion RSI
    instead, that's a different, equally valid strategy — say so and
    this file's two comparisons flip.

INPUT CONTRACT
    generate_signals() expects a DataFrame with at least
    ["adjusted_close", "volume"] columns, one row per COMPLETED bar
    (this is not a live-tick signal — feed it EOD or completed-bar
    data, e.g. from data_pipeline.get_recent_ohlcv()).
"""

from __future__ import annotations

import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI, vectorized: no per-row Python loop."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # neutral while warming up / when avg_loss is 0


def _crosses_above(a: pd.Series, level: float) -> pd.Series:
    return (a > level) & (a.shift(1) <= level)


def _crosses_below(a: pd.Series, level: float) -> pd.Series:
    return (a < level) & (a.shift(1) >= level)


def generate_signals(frame: pd.DataFrame, rsi_threshold: float = 65, rsi_period: int = 14,
                      volume_window: int = 20) -> pd.DataFrame:
    """Returns a copy of `frame` with rsi/avg_volume/signal columns added.
    signal is one of "BUY", "SELL", "HOLD" per row.

    BUY : RSI crosses above rsi_threshold AND volume confirms (above its
          rolling average) — a momentum breakout with real participation,
          not a thin-volume spike.
    SELL: RSI crosses below (100 - rsi_threshold) — symmetric momentum
          breakdown. Volume confirmation isn't required on the way down;
          exits shouldn't be gated on the same confirmation entries are.
    """
    if "adjusted_close" not in frame.columns or "volume" not in frame.columns:
        raise ValueError("generate_signals requires 'adjusted_close' and 'volume' columns")

    out = frame.copy()
    out["rsi"] = compute_rsi(out["adjusted_close"], period=rsi_period)
    out["avg_volume"] = out["volume"].rolling(volume_window, min_periods=1).mean()

    lower_threshold = 100 - rsi_threshold
    buy_cross = _crosses_above(out["rsi"], rsi_threshold)
    volume_confirms = out["volume"] > out["avg_volume"]
    sell_cross = _crosses_below(out["rsi"], lower_threshold)

    out["signal"] = "HOLD"
    out.loc[buy_cross & volume_confirms, "signal"] = "BUY"
    out.loc[sell_cross, "signal"] = "SELL"
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
