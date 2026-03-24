"""Data loading — CSV and Oura API sources."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pandas as pd
import requests

from .config import (
    API_LOOKBACK_DAYS,
    DEFAULT_CSV_PATH,
    OURA_ACCESS_TOKEN_ENV,
    OURA_SLEEP_ENDPOINT,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
_REQUIRED_COLUMNS = [
    "day",
    "bedtime_start",
    "bedtime_end",
    "sleep_phase_30_sec",
    "sleep_phase_5_min",
    "deep_sleep_duration",
    "light_sleep_duration",
    "rem_sleep_duration",
    "awake_time",
    "total_sleep_duration",
]


def _check_required_columns(df: pd.DataFrame, label: str) -> None:
    missing = [col for col in _REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{label} is missing expected columns: {missing}")


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------
def load_sleep_data_csv(csv_path: Path | None = None) -> pd.DataFrame:
    """Load an Oura sleepmodel CSV export (semicolon-separated)."""
    path = csv_path or DEFAULT_CSV_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path.resolve()}. "
            "Place sleepmodel.csv in the data/ folder or pass the path explicitly."
        )
    df = pd.read_csv(path, sep=";")
    _check_required_columns(df, "CSV file")
    return df


# ---------------------------------------------------------------------------
# Oura API loading
# ---------------------------------------------------------------------------
def require_oura_access_token() -> str:
    """Read the Oura access token from the environment."""
    token = os.getenv(OURA_ACCESS_TOKEN_ENV, "").strip()
    if not token:
        raise RuntimeError(
            f"{OURA_ACCESS_TOKEN_ENV} is not set. "
            "Export a valid Oura personal access token before using API mode."
        )
    return token


def get_api_date_range(lookback_days: int = API_LOOKBACK_DAYS) -> tuple[str, str]:
    """Build a recent date range string pair for API fetches."""
    end_date = pd.Timestamp.now(tz="UTC").normalize().date()
    start_date = end_date - timedelta(days=lookback_days)
    return str(start_date), str(end_date)


def load_sleep_data_api(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch sleep records from the Oura v2 API and return a normalised dataframe."""
    access_token = require_oura_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    records: list[dict] = []
    params: dict[str, str] = {"start_date": start_date, "end_date": end_date}

    while True:
        response = requests.get(
            OURA_SLEEP_ENDPOINT, headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        payload = response.json()
        records.extend(payload.get("data", []))
        next_token = payload.get("next_token")
        if not next_token:
            break
        params = {"next_token": next_token}

    if not records:
        raise ValueError(
            "No sleep records were returned by the Oura API for the requested date range."
        )

    df = pd.DataFrame(records)
    _check_required_columns(df, "API response")
    return df


# ---------------------------------------------------------------------------
# Unified source selector (used by the GUI)
# ---------------------------------------------------------------------------
def load_selected_source_data(
    source_name: str,
    csv_cache: pd.DataFrame,
    api_cache: dict[str, pd.DataFrame | None],
    *,
    force_api_refresh: bool = False,
) -> pd.DataFrame:
    """Return the dataframe for the chosen source, with lazy caching for API mode."""
    if source_name == "CSV":
        return csv_cache

    if source_name == "API":
        if force_api_refresh:
            api_cache["df"] = None
        if api_cache["df"] is None:
            start_date, end_date = get_api_date_range()
            api_cache["df"] = load_sleep_data_api(start_date, end_date)
        return api_cache["df"]

    raise ValueError(f"Unsupported source: {source_name}")
