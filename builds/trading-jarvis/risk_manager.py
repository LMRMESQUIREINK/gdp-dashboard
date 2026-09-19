# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Risk manager — ATR stop, fixed-fractional sizing, heat check
#  Data Layer: none (pure function of an OHLCV frame)
#  Generated: 2026-09-19 (completes the Trading Jarvis build)
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component:  risk_manager.py                              ║
║      Role:       ATR stop + fixed-fractional position sizing   ║
║      Guarantee:  Never places an order — sizing suggestion     ║
║                  for a human to review, exactly like every     ║
║                  other component in this system.               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

HONEST LIMITATION — "portfolio heat" here is single-trade risk, not
whole-portfolio risk. Every call to evaluate_trade() is a stateless
check for one symbol; nothing in this codebase tracks what other
positions are currently open elsewhere. heat_pct below is this trade's
dollar risk as a percentage of equity — a real and useful number, but
not the multi-position "total portfolio heat" the name might suggest.
If you add position tracking later, extend evaluate_trade() to accept
existing open risk and sum it in, rather than silently relabeling this
as portfolio-wide.

INPUT CONTRACT
    evaluate_trade() expects a DataFrame with at least
    ["high", "low", "close"] columns, one row per completed bar, most
    recent last (e.g. from data_pipeline.get_recent_ohlcv()).
"""

from __future__ import annotations

import math

import pandas as pd

HEAT_WARNING_PCT = 5.0  # matches README3.md's "portfolio heat over 5%" rule


def compute_atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range, vectorized (simple rolling mean of true
    range — the standard simplified ATR variant; Wilder's exact
    smoothing differs slightly but this is deterministic and needs no
    warm-up loop)."""
    high, low, close = frame["high"], frame["low"], frame["close"]
    prev_close = close.shift(1)
    true_range = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return true_range.rolling(period, min_periods=1).mean()


def evaluate_trade(
    frame: pd.DataFrame,
    equity: float,
    risk_pct: float = 1.0,
    atr_period: int = 14,
    atr_multiplier: float = 2.0,
) -> dict:
    """ATR-based stop + fixed-fractional position size for a long entry
    at the latest close.

    Returns:
        {
          "sizing": {"shares": int, "stop": float, "entry": float, "dollar_risk": float},
          "portfolio_heat": {"heat_pct": float, "warning": bool, "reason": str},
          "approved": bool,
        }
    """
    if frame.empty:
        raise ValueError("evaluate_trade requires a non-empty OHLC frame")
    for col in ("high", "low", "close"):
        if col not in frame.columns:
            raise ValueError(f"evaluate_trade requires a '{col}' column")
    if equity <= 0:
        raise ValueError("equity must be positive")

    atr = compute_atr(frame, period=atr_period)
    entry = float(frame["close"].iloc[-1])
    latest_atr = float(atr.iloc[-1])
    stop = round(entry - atr_multiplier * latest_atr, 2)
    risk_per_share = entry - stop

    dollar_risk = round(equity * (risk_pct / 100), 2)
    shares = math.floor(dollar_risk / risk_per_share) if risk_per_share > 0 else 0
    # heat_pct is this trade's ACTUAL dollar risk (using the rounded-down
    # share count, not the target dollar_risk above) as a % of equity.
    actual_dollar_risk = round(shares * risk_per_share, 2)
    heat_pct = round((actual_dollar_risk / equity) * 100, 2) if equity else 0.0

    warning = heat_pct > HEAT_WARNING_PCT
    approved = shares > 0 and risk_per_share > 0 and not warning

    if shares <= 0 or risk_per_share <= 0:
        reason = "ATR stop distance is zero or negative — cannot size a position."
    elif warning:
        reason = f"Trade risk ({heat_pct}% of equity) exceeds the {HEAT_WARNING_PCT}% heat limit."
    else:
        reason = "Within risk limits."

    return {
        "sizing": {
            "shares": shares,
            "stop": stop,
            "entry": entry,
            "dollar_risk": actual_dollar_risk,
        },
        "portfolio_heat": {
            "heat_pct": heat_pct,
            "warning": warning,
            "reason": reason,
        },
        "approved": approved,
    }


if __name__ == "__main__":
    import numpy as np

    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    rng = np.random.default_rng(1)
    close = pd.Series(150 + np.cumsum(rng.normal(0, 1.5, 60)), index=idx)
    frame = pd.DataFrame({
        "close": close,
        "high": close + rng.uniform(0.5, 2.5, 60),
        "low": close - rng.uniform(0.5, 2.5, 60),
    })

    result = evaluate_trade(frame, equity=50_000, risk_pct=1.0)
    print(f"♛ {result}")
