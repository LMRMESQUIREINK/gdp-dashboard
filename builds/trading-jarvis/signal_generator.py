# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Signal generator — RSI + volume confirmation trigger (vectorized)
#  Data Layer: EODHD
#  Generated: 2026-07-18
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: signal_generator.py                           ║
║      Strategy:  RSI threshold cross + volume confirmation      ║
║      Symbol(s): configurable                                   ║
║      Timeframe: daily (adaptable to intraday)                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

This implements the plain-English trigger from the "Trading Jarvis" article's
cold-open example: "alert me when RSI crosses 65 with volume confirmation."

Every indicator is shifted by 1 bar before it touches the signal decision —
this file NEVER compares an indicator to the same bar's forward return.

rsi_period (14, standard) and rsi_threshold (65) are separate parameters —
this resolves the "RSI(65) — period or threshold?" ambiguity flagged in an
earlier analysis pass that ran before this file was available: 65 is the
threshold level, not the lookback period.
"""

import numpy as np
import pandas as pd


# ───────────────────────────────────────────────────────────────
# Indicator library — vectorized, hand-rolled (no black-box TA-Lib)
# ───────────────────────────────────────────────────────────────

def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = -delta.clip(upper=0).rolling(n).mean()
    return 100 - (100 / (1 + gain / loss))


def volume_confirmation(volume: pd.Series, lookback: int = 20,
                         multiple: float = 1.5) -> pd.Series:
    """True where volume exceeds `multiple` x its trailing average."""
    avg_vol = volume.rolling(lookback).mean()
    return volume > (avg_vol * multiple)


# ───────────────────────────────────────────────────────────────
# Signal generation — the RSI-cross + volume-confirmation trigger
# ───────────────────────────────────────────────────────────────

def generate_signals(
    df: pd.DataFrame,
    rsi_period: int = 14,
    rsi_threshold: float = 65.0,
    volume_lookback: int = 20,
    volume_multiple: float = 1.5,
    price_col: str = "adjusted_close",
    volume_col: str = "volume",
) -> pd.DataFrame:
    """
    Entry: RSI crosses UP through `rsi_threshold` AND volume confirms.
    Exit:  RSI crosses back DOWN through `rsi_threshold`.

    Returns df with columns: [<price_col>, rsi, vol_confirm, signal, position]
    """
    out = df.copy()
    out["rsi"] = rsi(out[price_col], rsi_period)
    out["vol_confirm"] = volume_confirmation(out[volume_col], volume_lookback, volume_multiple)

    # ♛ Lookahead-bias check — every comparison below uses .shift(1)/.shift(2),
    #   i.e. only information available at the close of the PRIOR bar.
    rsi_prev1 = out["rsi"].shift(1)
    rsi_prev2 = out["rsi"].shift(2)
    vol_confirm_prev1 = out["vol_confirm"].shift(1)

    entry = (rsi_prev1 > rsi_threshold) & (rsi_prev2 <= rsi_threshold) & (vol_confirm_prev1 == True)  # noqa: E712
    exit_ = (rsi_prev1 < rsi_threshold) & (rsi_prev2 >= rsi_threshold)

    out["signal"] = 0
    out.loc[entry, "signal"] = 1
    out.loc[exit_, "signal"] = -1

    # Position = forward-fill of signal until an exit clears it
    out["position"] = out["signal"].replace(0, np.nan).ffill().fillna(0)
    out.loc[out["position"] == -1, "position"] = 0

    return out[[price_col, "rsi", "vol_confirm", "signal", "position"]]


def latest_signal(df_with_signals: pd.DataFrame) -> str:
    """Convert the most recent row's signal into a human-readable label."""
    if df_with_signals.empty:
        return "NO_DATA"
    row = df_with_signals.iloc[-1]
    if row["signal"] == 1:
        return "BUY"
    if row["signal"] == -1:
        return "SELL"
    return "HOLD"


if __name__ == "__main__":
    # Smoke test with synthetic data
    rng = pd.date_range("2024-01-01", periods=300, freq="B")
    price = pd.Series(100 + np.cumsum(np.random.normal(0.1, 1.2, len(rng))), index=rng)
    volume = pd.Series(np.random.randint(1_000_000, 3_000_000, len(rng)), index=rng)
    synthetic = pd.DataFrame({"adjusted_close": price, "volume": volume})

    result = generate_signals(synthetic)
    print(result.tail(10))
    print(f"♛ Latest signal: {latest_signal(result)}")
