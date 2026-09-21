# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Risk manager — ATR stops, fixed-fractional sizing, portfolio heat
#  Data Layer: EODHD
#  Generated: 2026-07-18 | Pro fix applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: risk_manager.py                               ║
║      Role:      Position sizing + exposure control             ║
║      Default:   1% account risk per trade, 5% max portfolio    ║
║                  heat                                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

This module NEVER touches a broker. It computes what a trade WOULD
cost/size to be, so a human (or the Jarvis orchestrator's human-in-the-loop
gate) can review before anything is ever sent to an execution venue.

WHAT CHANGED IN THIS BUILD
    size_position()'s zero-risk-distance branch (entry == stop) used to
    return a different key set than the normal branch — no
    r_multiple_target key, and a "warning" key that meant something
    different from portfolio_heat's boolean "warning" one level up.
    Both branches now return the same keys, so a caller can read
    result["sizing"]["r_multiple_target"] unconditionally instead of
    needing a special case. The zero-risk message moved to an "error"
    key to avoid the name collision with portfolio_heat's "warning".
    (This exact fix has now been applied twice across two otherwise-
    identical uploads of this file — see /notes/trading-jarvis-analysis.md.)
"""

import pandas as pd


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Average True Range — vectorized."""
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()


def atr_stop(df: pd.DataFrame, multiplier: float = 2.0, period: int = 14) -> float:
    """ATR-based stop distance below the latest close (long-only convention)."""
    a = atr(df, period).iloc[-1]
    return df["close"].iloc[-1] - (multiplier * a)


def size_position(equity: float, risk_pct: float, entry: float, stop: float) -> dict:
    """Fixed-fractional position sizing.

    risk_pct: percent of account equity to risk on this trade (default convention: 1.0)
    """
    risk_per_share = abs(entry - stop)
    if risk_per_share == 0:
        return {"shares": 0, "dollar_risk": 0.0, "entry": round(entry, 2), "stop": round(stop, 2),
                "r_multiple_target": None, "error": "entry == stop, cannot size"}

    dollar_risk = equity * (risk_pct / 100)
    shares = int(dollar_risk / risk_per_share)
    return {
        "shares": shares,
        "dollar_risk": round(shares * risk_per_share, 2),
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "r_multiple_target": round(entry + 2 * (entry - stop), 2),
        "error": None,
    }


def portfolio_heat(positions: list, equity: float) -> dict:
    """Check total open-risk exposure across positions.

    positions: [{"shares": int, "entry": float, "stop": float}, ...]
    Flags if total risk exceeds 5% of equity.
    """
    total_risk = sum(p["shares"] * abs(p["entry"] - p["stop"]) for p in positions)
    heat_pct = (total_risk / equity) * 100 if equity else 0.0
    return {
        "total_risk": round(total_risk, 2),
        "heat_pct": round(heat_pct, 2),
        "warning": heat_pct > 5.0,
    }


def evaluate_trade(df: pd.DataFrame, equity: float, risk_pct: float = 1.0,
                    atr_multiplier: float = 2.0, existing_positions: list = None) -> dict:
    """
    One-call risk evaluation for a candidate trade, used by the Jarvis
    orchestrator's risk-check tool before any alert is surfaced as
    'actionable' to the user.

    existing_positions: pass currently-open positions here to get a real
    multi-position portfolio_heat reading. See positions_store.py.
    """
    existing_positions = existing_positions or []
    entry = df["close"].iloc[-1]
    stop = atr_stop(df, atr_multiplier)
    sizing = size_position(equity, risk_pct, entry, stop)

    hypothetical = existing_positions + [{
        "shares": sizing["shares"], "entry": entry, "stop": stop
    }]
    heat = portfolio_heat(hypothetical, equity)

    return {
        "sizing": sizing,
        "portfolio_heat": heat,
        "approved": (not heat["warning"]) and sizing["shares"] > 0,
    }


if __name__ == "__main__":
    import numpy as np
    rng = pd.date_range("2024-01-01", periods=60, freq="B")
    close = pd.Series(150 + np.cumsum(np.random.normal(0.2, 1.5, len(rng))), index=rng)
    high = close + np.random.uniform(0.5, 1.5, len(rng))
    low = close - np.random.uniform(0.5, 1.5, len(rng))
    synthetic = pd.DataFrame({"high": high, "low": low, "close": close})

    result = evaluate_trade(synthetic, equity=50_000, risk_pct=1.0)
    print("♛ Trade evaluation:")
    for k, v in result.items():
        print(f"  {k}: {v}")
