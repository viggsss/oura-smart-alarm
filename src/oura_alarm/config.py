"""Centralised configuration constants for the Oura Smart Alarm Analyser."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "sleepmodel.csv"

# ---------------------------------------------------------------------------
# Wake-window defaults
# ---------------------------------------------------------------------------
WAKE_WINDOW_START = "08:00"
WAKE_WINDOW_END = "08:30"

# ---------------------------------------------------------------------------
# Alarm trigger thresholds (consecutive 30-second samples)
# ---------------------------------------------------------------------------
AWAKE_CONFIRM_SAMPLES = 5
LIGHT_CONFIRM_SAMPLES = 5

# ---------------------------------------------------------------------------
# Oura API
# ---------------------------------------------------------------------------
OURA_ACCESS_TOKEN_ENV = "OURA_ACCESS_TOKEN"
OURA_SLEEP_ENDPOINT = "https://api.ouraring.com/v2/usercollection/sleep"
API_LOOKBACK_DAYS = 120

# ---------------------------------------------------------------------------
# Stage mapping — maps single-character codes from sleep_phase_30_sec
# ---------------------------------------------------------------------------
STAGE_MAP = {
    "1": "deep",
    "2": "light",
    "3": "rem",
    "4": "awake",
}

PREFERRED_STAGES = {"light", "awake"}
AVOID_STAGES = {"deep"}
