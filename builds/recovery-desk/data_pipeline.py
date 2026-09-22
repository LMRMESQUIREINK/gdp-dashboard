"""
Recovery Desk — wearable data pipeline.

Fetches last night's data from Oura or Whoop and normalizes it into the
shared `OvernightReading` shape `decision_engine.py` runs on, so the
decision logic never has to know which provider a given user is on.

No live Oura/Whoop API access from this sandbox (same network-egress
restriction as every other build in this project — see
/notes/prop-firm-sizing-analysis.md for the same note on a different
build). `fetch_oura_reading()`/`fetch_whoop_reading()` are real,
complete implementations against each provider's actual API shape, but
untested live here; `synthetic_reading()` is what every test and demo
in this build actually runs against, and is exercised directly.
"""

import os
from datetime import date, timedelta

import requests

from decision_engine import OvernightReading

OURA_API_TOKEN = os.getenv("OURA_API_TOKEN", "YOUR_OURA_TOKEN")
WHOOP_API_TOKEN = os.getenv("WHOOP_API_TOKEN", "YOUR_WHOOP_TOKEN")

OURA_BASE = "https://api.ouraring.com/v2/usercollection"
WHOOP_BASE = "https://api.prod.whoop.com/developer/v1"

BASELINE_LOOKBACK_DAYS = 14


def _require_token(token: str, env_var: str, placeholder: str) -> None:
    """Fail locally and immediately on a placeholder credential, rather
    than sending it to the provider and getting back a confusing 401."""
    if not token or token == placeholder:
        raise RuntimeError(
            f"{env_var} is not set. Set it before running, e.g.:\n"
            f"  bash/macOS/Linux : export {env_var}=\"your_token_here\"\n"
            f"  Windows PowerShell: setx {env_var} \"your_token_here\"\n"
            f"(then restart your terminal so the new value is picked up)"
        )


def fetch_oura_reading(target_date: date = None) -> OvernightReading:
    """Pull last night's readiness/sleep/HRV data from Oura's v2 API and
    the trailing baseline needed for decision_engine's comparisons."""
    _require_token(OURA_API_TOKEN, "OURA_API_TOKEN", "YOUR_OURA_TOKEN")
    target_date = target_date or date.today()
    headers = {"Authorization": f"Bearer {OURA_API_TOKEN}"}
    start = target_date - timedelta(days=BASELINE_LOOKBACK_DAYS)

    readiness = requests.get(
        f"{OURA_BASE}/daily_readiness",
        headers=headers,
        params={"start_date": start.isoformat(), "end_date": target_date.isoformat()},
        timeout=20,
    ).json()["data"]
    sleep = requests.get(
        f"{OURA_BASE}/daily_sleep",
        headers=headers,
        params={"start_date": start.isoformat(), "end_date": target_date.isoformat()},
        timeout=20,
    ).json()["data"]

    if not readiness or not sleep:
        raise ValueError(f"Oura returned no data for {target_date} — check the ring synced overnight.")

    today_r = readiness[-1]
    today_s = sleep[-1]
    hrv_series = [r["contributors"]["hrv_balance"] for r in readiness[:-1]] or [today_r["contributors"]["hrv_balance"]]
    rhr_series = [r["contributors"]["resting_heart_rate"] for r in readiness[:-1]] or [today_r["contributors"]["resting_heart_rate"]]

    return OvernightReading(
        hrv_ms=today_r["contributors"]["hrv_balance"],
        hrv_baseline_ms=sum(hrv_series) / len(hrv_series),
        resting_hr=today_r["contributors"]["resting_heart_rate"],
        resting_hr_baseline=sum(rhr_series) / len(rhr_series),
        sleep_hours=today_s["total_sleep_duration"] / 3600,
        sleep_score=today_s["score"],
        respiratory_rate=today_s.get("average_breath", 14.0),
        respiratory_rate_baseline=14.0,  # Oura doesn't expose a rolling breath-rate baseline; fixed physiological norm
        prior_day_strain=today_r["contributors"].get("activity_balance", 50.0),
    )


def fetch_whoop_reading(target_date: date = None) -> OvernightReading:
    """Pull last night's recovery/sleep/strain data from Whoop's v1 API."""
    _require_token(WHOOP_API_TOKEN, "WHOOP_API_TOKEN", "YOUR_WHOOP_TOKEN")
    target_date = target_date or date.today()
    headers = {"Authorization": f"Bearer {WHOOP_API_TOKEN}"}
    start = target_date - timedelta(days=BASELINE_LOOKBACK_DAYS)

    recovery = requests.get(
        f"{WHOOP_BASE}/recovery",
        headers=headers,
        params={"start": start.isoformat(), "end": target_date.isoformat()},
        timeout=20,
    ).json()["records"]
    cycles = requests.get(
        f"{WHOOP_BASE}/cycle",
        headers=headers,
        params={"start": start.isoformat(), "end": target_date.isoformat()},
        timeout=20,
    ).json()["records"]

    if not recovery:
        raise ValueError(f"Whoop returned no recovery data for {target_date} — check the strap synced overnight.")

    today = recovery[-1]["score"]
    hrv_series = [r["score"]["hrv_rmssd_milli"] for r in recovery[:-1]] or [today["hrv_rmssd_milli"]]
    rhr_series = [r["score"]["resting_heart_rate"] for r in recovery[:-1]] or [today["resting_heart_rate"]]
    prior_strain = cycles[-2]["score"]["strain"] if len(cycles) >= 2 else 50.0

    return OvernightReading(
        hrv_ms=today["hrv_rmssd_milli"],
        hrv_baseline_ms=sum(hrv_series) / len(hrv_series),
        resting_hr=today["resting_heart_rate"],
        resting_hr_baseline=sum(rhr_series) / len(rhr_series),
        sleep_hours=today.get("sleep_performance_percentage", 70) / 100 * 8,  # Whoop reports sleep as % of need
        sleep_score=today.get("sleep_performance_percentage", 70),
        respiratory_rate=today.get("respiratory_rate", 15.0),
        respiratory_rate_baseline=15.0,
        prior_day_strain=(prior_strain / 21) * 100,  # Whoop strain is 0-21; normalize to 0-100
    )


# ───────────────────────────────────────────────────────────────
# Synthetic data — what every test/demo in this build actually runs
# against, engineered to land on each specific decision branch.
# ───────────────────────────────────────────────────────────────

SYNTHETIC_SCENARIOS = {
    "train_hard": OvernightReading(
        hrv_ms=72, hrv_baseline_ms=60, resting_hr=46, resting_hr_baseline=50,
        sleep_hours=7.8, sleep_score=90, respiratory_rate=14.2,
        respiratory_rate_baseline=14.0, prior_day_strain=40,
    ),
    "back_off": OvernightReading(
        hrv_ms=44, hrv_baseline_ms=60, resting_hr=54.5, resting_hr_baseline=50,
        sleep_hours=6.8, sleep_score=40, respiratory_rate=14.5,
        respiratory_rate_baseline=14.0, prior_day_strain=55,
    ),
    "eat_more": OvernightReading(
        hrv_ms=58, hrv_baseline_ms=60, resting_hr=51, resting_hr_baseline=50,
        sleep_hours=7.5, sleep_score=75, respiratory_rate=14.1,
        respiratory_rate_baseline=14.0, prior_day_strain=85,
    ),
    "sleep_earlier": OvernightReading(
        hrv_ms=61, hrv_baseline_ms=60, resting_hr=49, resting_hr_baseline=50,
        sleep_hours=5.4, sleep_score=70, respiratory_rate=14.0,
        respiratory_rate_baseline=14.0, prior_day_strain=45,
    ),
    "anomaly": OvernightReading(
        hrv_ms=38, hrv_baseline_ms=60, resting_hr=61, resting_hr_baseline=50,
        sleep_hours=5.0, sleep_score=40, respiratory_rate=17.5,
        respiratory_rate_baseline=14.0, prior_day_strain=30,
    ),
}


def synthetic_reading(scenario: str) -> OvernightReading:
    """A hand-built OvernightReading engineered to land on a specific
    decision_engine branch — used by tests and by run_daily_check.py's
    --demo flag, since no live Oura/Whoop token exists in this sandbox."""
    if scenario not in SYNTHETIC_SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Valid: {list(SYNTHETIC_SCENARIOS.keys())}")
    return SYNTHETIC_SCENARIOS[scenario]
