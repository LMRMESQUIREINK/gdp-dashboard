# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Data pipeline — fetch + cache layer for the Jarvis system
#  Data Layer: EODHD (OHLCV/intraday/real-time) + FMP (fundamentals)
#  Generated: 2026-07-18 | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component:  data_pipeline.py                             ║
║      Role:       Market data fetch + normalize + cache        ║
║      Providers:  EODHD (price), FMP (fundamentals)             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

SETUP — set your API keys as environment variables before running.

Windows PowerShell:
    setx EODHD_API_KEY "your_key_here"
    setx FMP_API_KEY "your_key_here"
    setx ANTHROPIC_API_KEY "your_key_here"

bash / macOS / Linux:
    export EODHD_API_KEY="your_key_here"
    export FMP_API_KEY="your_key_here"
    export ANTHROPIC_API_KEY="your_key_here"

WHAT CHANGED IN THIS BUILD
    get_recent_closes() used to be the only accessor every downstream
    file called, and it only ever returned adjusted-close prices —
    forcing every caller to fabricate high/low/volume synthetically
    (a flat +/-1% band and a hardcoded volume constant). That broke
    ATR-based stops and volume-confirmation signals, which both need
    real data. get_recent_ohlcv() below returns the real frame
    fetch_eod() already has; get_recent_closes() is kept as a thin
    wrapper over it for backward compatibility.

    A placeholder API key ("YOUR_EODHD_KEY") used to be sent straight
    to the network, surfacing as a confusing remote 401/403. The
    _require_key() check below fails locally and immediately instead.
"""

import os
import time
import json
import hashlib
from pathlib import Path

import requests
import pandas as pd

EODHD_API_KEY = os.getenv("EODHD_API_KEY", "YOUR_EODHD_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY", "YOUR_FMP_KEY")
FMP_BASE = "https://financialmodelingprep.com/api/v3"

CACHE_DIR = Path(".ruthless_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_SECONDS = 300  # 5 minutes — safe default for EOD/fundamentals data


# ───────────────────────────────────────────────────────────────
# Key validation — fail locally and immediately, not with a
# confusing remote 401/403 after a wasted round trip.
# ───────────────────────────────────────────────────────────────

def _require_key(key: str, env_var: str, placeholder: str) -> None:
    if not key or key == placeholder:
        raise RuntimeError(
            f"{env_var} is not set. Set it before running, e.g.:\n"
            f"  bash/macOS/Linux : export {env_var}=\"your_key_here\"\n"
            f"  Windows PowerShell: setx {env_var} \"your_key_here\"\n"
            f"(then restart your terminal so the new value is picked up)"
        )


# ───────────────────────────────────────────────────────────────
# Cache layer — avoids hammering the API on repeated Jarvis queries
# ───────────────────────────────────────────────────────────────

def _cache_key(*parts: str) -> Path:
    digest = hashlib.md5("|".join(parts).encode()).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _cache_get(*parts: str):
    path = _cache_key(*parts)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_TTL_SECONDS:
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _cache_set(data, *parts: str) -> None:
    path = _cache_key(*parts)
    path.write_text(json.dumps(data, default=str))


# ───────────────────────────────────────────────────────────────
# EODHD — OHLCV / intraday / real-time
# ───────────────────────────────────────────────────────────────

def fetch_eod(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch end-of-day OHLCV with corporate-action-adjusted close.
    symbol format: 'AAPL.US', 'BMW.DE', 'BTC-USD.CC'
    """
    _require_key(EODHD_API_KEY, "EODHD_API_KEY", "YOUR_EODHD_KEY")

    cached = _cache_get("eod", symbol, start, end)
    if cached is not None:
        df = pd.DataFrame(cached)
    else:
        r = requests.get(
            f"https://eodhd.com/api/eod/{symbol}",
            params={"api_token": EODHD_API_KEY, "from": start, "to": end,
                    "period": "d", "fmt": "json"},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        _cache_set(data, "eod", symbol, start, end)
        df = pd.DataFrame(data)

    if df.empty:
        raise ValueError(f"No EOD data returned for {symbol} ({start} to {end})")

    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[["open", "high", "low", "close",
                                  "adjusted_close", "volume"]]


def fetch_intraday(symbol: str, interval: str = "1m") -> pd.DataFrame:
    """Fetch intraday bars. interval: '1m', '5m', '1h'."""
    _require_key(EODHD_API_KEY, "EODHD_API_KEY", "YOUR_EODHD_KEY")

    r = requests.get(
        f"https://eodhd.com/api/intraday/{symbol}",
        params={"api_token": EODHD_API_KEY, "interval": interval, "fmt": "json"},
        timeout=20,
    )
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if df.empty:
        raise ValueError(f"No intraday data returned for {symbol}")
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.set_index("datetime")[["open", "high", "low", "close", "volume"]]


def fetch_realtime(symbol: str) -> float:
    """Fetch latest real-time quote (polling, not websocket)."""
    _require_key(EODHD_API_KEY, "EODHD_API_KEY", "YOUR_EODHD_KEY")

    r = requests.get(
        f"https://eodhd.com/api/real-time/{symbol}",
        params={"api_token": EODHD_API_KEY, "fmt": "json"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("close")


# ───────────────────────────────────────────────────────────────
# FMP — fundamentals / ratios / insider / analyst
# ───────────────────────────────────────────────────────────────

def fetch_quote(symbol: str) -> dict:
    _require_key(FMP_API_KEY, "FMP_API_KEY", "YOUR_FMP_KEY")
    r = requests.get(f"{FMP_BASE}/quote/{symbol}",
                      params={"apikey": FMP_API_KEY}, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else {}


def fetch_ratios_ttm(symbol: str) -> dict:
    _require_key(FMP_API_KEY, "FMP_API_KEY", "YOUR_FMP_KEY")
    r = requests.get(f"{FMP_BASE}/ratios-ttm/{symbol}",
                      params={"apikey": FMP_API_KEY}, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else {}


def fetch_analyst_estimates(symbol: str) -> list:
    _require_key(FMP_API_KEY, "FMP_API_KEY", "YOUR_FMP_KEY")
    r = requests.get(f"{FMP_BASE}/analyst-estimates/{symbol}",
                      params={"apikey": FMP_API_KEY}, timeout=20)
    r.raise_for_status()
    return r.json()


# ───────────────────────────────────────────────────────────────
# Unified accessors used by the Jarvis orchestrator's tool layer
# ───────────────────────────────────────────────────────────────

def get_recent_ohlcv(symbol: str, lookback_days: int = 120) -> pd.DataFrame:
    """Real open/high/low/close/adjusted_close/volume for the last
    `lookback_days` bars — what signal_generator.py and risk_manager.py
    should actually be fed, instead of a synthetic band built from
    closes alone."""
    end = pd.Timestamp.today().strftime("%Y-%m-%d")
    start = (pd.Timestamp.today() - pd.Timedelta(days=lookback_days * 2)).strftime("%Y-%m-%d")
    df = fetch_eod(symbol, start, end)
    return df.tail(lookback_days)


def get_recent_closes(symbol: str, lookback_days: int = 120) -> pd.Series:
    """Convenience wrapper kept for backward compatibility: recent
    adjusted-close series only. Prefer get_recent_ohlcv() for anything
    that needs real high/low/volume (signals, ATR stops)."""
    return get_recent_ohlcv(symbol, lookback_days)["adjusted_close"]


if __name__ == "__main__":
    # Smoke test — replace symbol as needed
    try:
        frame = get_recent_ohlcv("AAPL.US", lookback_days=30)
        print(f"♛ Fetched {len(frame)} OHLCV bars for AAPL.US")
        print(frame.tail())
    except Exception as e:
        print(f"[error] {e}")
