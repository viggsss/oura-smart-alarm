"""Unit tests for the core analysis and alarm-trigger logic."""

from __future__ import annotations

import pandas as pd
import pytest

from src.oura_alarm.analysis import (
    choose_alarm_time,
    decode_sleep_timeline,
    find_first_confirmed_run,
    longest_run,
)
from src.oura_alarm.config import AWAKE_CONFIRM_SAMPLES, LIGHT_CONFIRM_SAMPLES


# ---------------------------------------------------------------------------
# Helpers — build minimal dataframes for testing
# ---------------------------------------------------------------------------
def _make_window_df(stage_names: list[str]) -> pd.DataFrame:
    """Create a minimal window dataframe from a list of stage names."""
    base = pd.Timestamp("2026-03-23 08:00:00", tz="UTC")
    return pd.DataFrame({
        "timestamp": [base + pd.Timedelta(seconds=30 * i) for i in range(len(stage_names))],
        "stage_code": [
            {"deep": "1", "light": "2", "rem": "3", "awake": "4"}[s] for s in stage_names
        ],
        "stage_name": stage_names,
    })


def _make_sleep_row(phase_string: str, bedtime_start: str, bedtime_end: str, day: str) -> pd.Series:
    """Create a minimal row resembling a sleep record."""
    return pd.Series({
        "day": day,
        "bedtime_start": bedtime_start,
        "bedtime_end": bedtime_end,
        "sleep_phase_30_sec": phase_string,
    })


# ---------------------------------------------------------------------------
# Tests — find_first_confirmed_run
# ---------------------------------------------------------------------------
class TestFindFirstConfirmedRun:
    def test_finds_awake_run(self):
        stages = ["light"] * 3 + ["awake"] * 6 + ["light"] * 2
        df = _make_window_df(stages)
        result = find_first_confirmed_run(df, "awake", AWAKE_CONFIRM_SAMPLES)
        assert result is not None
        _, code, length = result
        assert code == "4"
        assert length >= AWAKE_CONFIRM_SAMPLES

    def test_returns_none_when_run_too_short(self):
        stages = ["light"] * 3 + ["awake"] * 2 + ["light"] * 5
        df = _make_window_df(stages)
        result = find_first_confirmed_run(df, "awake", AWAKE_CONFIRM_SAMPLES)
        assert result is None

    def test_finds_light_run(self):
        stages = ["deep"] * 2 + ["light"] * 7
        df = _make_window_df(stages)
        result = find_first_confirmed_run(df, "light", LIGHT_CONFIRM_SAMPLES)
        assert result is not None


# ---------------------------------------------------------------------------
# Tests — longest_run
# ---------------------------------------------------------------------------
class TestLongestRun:
    def test_single_stage(self):
        df = _make_window_df(["light"] * 10)
        assert longest_run(df, "light") == 10
        assert longest_run(df, "deep") == 0

    def test_mixed_stages(self):
        stages = ["light"] * 3 + ["deep"] * 2 + ["light"] * 5 + ["awake"] * 1
        df = _make_window_df(stages)
        assert longest_run(df, "light") == 5
        assert longest_run(df, "deep") == 2
        assert longest_run(df, "awake") == 1


# ---------------------------------------------------------------------------
# Tests — choose_alarm_time
# ---------------------------------------------------------------------------
class TestChooseAlarmTime:
    def _make_timeline(self, stage_names: list[str], start: str = "2026-03-23 07:50:00") -> pd.DataFrame:
        base = pd.Timestamp(start, tz="UTC")
        return pd.DataFrame({
            "timestamp": [base + pd.Timedelta(seconds=30 * i) for i in range(len(stage_names))],
            "stage_code": [
                {"deep": "1", "light": "2", "rem": "3", "awake": "4"}[s] for s in stage_names
            ],
            "stage_name": stage_names,
        })

    def test_prefers_awake_over_light(self):
        # Window covers indices 20..40 (08:00 to 08:10)
        stages = ["deep"] * 20 + ["awake"] * 6 + ["light"] * 20
        timeline = self._make_timeline(stages)
        ws = pd.Timestamp("2026-03-23 08:00:00", tz="UTC")
        we = pd.Timestamp("2026-03-23 08:10:00", tz="UTC")
        decision = choose_alarm_time(timeline, ws, we)
        assert decision.trigger_mode == "confirmed_awake"

    def test_falls_back_to_light(self):
        stages = ["deep"] * 20 + ["light"] * 10 + ["deep"] * 10
        timeline = self._make_timeline(stages)
        ws = pd.Timestamp("2026-03-23 08:00:00", tz="UTC")
        we = pd.Timestamp("2026-03-23 08:10:00", tz="UTC")
        decision = choose_alarm_time(timeline, ws, we)
        assert decision.trigger_mode == "confirmed_light"

    def test_forces_window_end_when_no_run(self):
        # Alternate stages so no consecutive run reaches the threshold
        stages = ["deep"] * 20 + (["light", "deep"] * 10)
        timeline = self._make_timeline(stages)
        ws = pd.Timestamp("2026-03-23 08:00:00", tz="UTC")
        we = pd.Timestamp("2026-03-23 08:10:00", tz="UTC")
        decision = choose_alarm_time(timeline, ws, we)
        assert decision.trigger_mode == "forced_window_end"

    def test_empty_window(self):
        stages = ["deep"] * 10
        timeline = self._make_timeline(stages, start="2026-03-23 06:00:00")
        ws = pd.Timestamp("2026-03-23 08:00:00", tz="UTC")
        we = pd.Timestamp("2026-03-23 08:30:00", tz="UTC")
        decision = choose_alarm_time(timeline, ws, we)
        assert decision.trigger_mode == "forced_window_end"
        assert decision.trigger_time == we


# ---------------------------------------------------------------------------
# Tests — decode_sleep_timeline
# ---------------------------------------------------------------------------
class TestDecodeSleepTimeline:
    def test_basic_decode(self):
        row = _make_sleep_row(
            phase_string="1234",
            bedtime_start="2026-03-23 02:00:00+00:00",
            bedtime_end="2026-03-23 02:02:00+00:00",
            day="2026-03-23",
        )
        timeline = decode_sleep_timeline(row)
        assert len(timeline) == 4
        assert list(timeline["stage_name"]) == ["deep", "light", "rem", "awake"]

    def test_raises_on_empty_phase(self):
        row = _make_sleep_row(
            phase_string="",
            bedtime_start="2026-03-23 02:00:00+00:00",
            bedtime_end="2026-03-23 02:02:00+00:00",
            day="2026-03-23",
        )
        with pytest.raises(ValueError, match="empty"):
            decode_sleep_timeline(row)
