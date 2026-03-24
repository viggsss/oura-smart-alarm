"""Core sleep-stage analysis and alarm-trigger logic."""

from __future__ import annotations

import pandas as pd

from .config import AWAKE_CONFIRM_SAMPLES, LIGHT_CONFIRM_SAMPLES, STAGE_MAP
from .models import WakeDecision, WindowAnalysis


# ---------------------------------------------------------------------------
# Night selection and timeline decoding
# ---------------------------------------------------------------------------
def list_available_days(df: pd.DataFrame) -> list[str]:
    """Return all valid sleep record days as sorted YYYY-MM-DD strings."""
    days = (
        pd.to_datetime(df["day"], errors="coerce")
        .dropna()
        .sort_values()
        .dt.strftime("%Y-%m-%d")
    )
    return days.tolist()


def build_record_options(df: pd.DataFrame) -> tuple[list[str], dict[str, int]]:
    """Build GUI dropdown labels and map each label to its row index.

    When a day has multiple records, bedtime times are included in the label
    so the user can distinguish between sessions.
    """
    temp = df.copy()
    temp["day_dt"] = pd.to_datetime(temp["day"], errors="coerce")
    temp["bedtime_start_dt"] = pd.to_datetime(temp["bedtime_start"], errors="coerce")
    temp["bedtime_end_dt"] = pd.to_datetime(temp["bedtime_end"], errors="coerce")
    temp = temp.reset_index().sort_values(["day_dt", "bedtime_start_dt", "bedtime_end_dt"])

    day_strings = temp["day_dt"].dt.strftime("%Y-%m-%d")
    day_counts = day_strings.value_counts().to_dict()

    labels: list[str] = []
    label_to_index: dict[str, int] = {}

    for _, row in temp.iterrows():
        day_str = row["day_dt"].strftime("%Y-%m-%d")
        start_dt = row["bedtime_start_dt"]
        end_dt = row["bedtime_end_dt"]

        if day_counts.get(day_str, 0) > 1 and pd.notna(start_dt) and pd.notna(end_dt):
            label = f"{day_str} | {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        else:
            label = day_str

        if label in label_to_index:
            n = 2
            candidate = f"{label} #{n}"
            while candidate in label_to_index:
                n += 1
                candidate = f"{label} #{n}"
            label = candidate

        labels.append(label)
        label_to_index[label] = int(row["index"])

    return labels, label_to_index


def select_night(df: pd.DataFrame, day: str | None = None) -> pd.Series:
    """Select a sleep record by day string, or default to the most recent."""
    temp = df.copy()
    temp["day"] = pd.to_datetime(temp["day"], errors="coerce")
    temp = temp.sort_values("day")

    if day is None:
        return temp.iloc[-1]

    matches = temp[temp["day"] == pd.to_datetime(day)]
    if matches.empty:
        raise ValueError(f"No sleep record found for day={day}")
    return matches.iloc[-1]


def decode_sleep_timeline(row: pd.Series) -> pd.DataFrame:
    """Expand the 30-second sleep_phase_30_sec string into a timestamped timeline."""
    bedtime_start = pd.to_datetime(row["bedtime_start"], errors="coerce")
    bedtime_end = pd.to_datetime(row["bedtime_end"], errors="coerce")
    phase_string = str(row["sleep_phase_30_sec"]).strip()

    if pd.isna(bedtime_start) or pd.isna(bedtime_end):
        raise ValueError("Could not parse bedtime_start or bedtime_end.")
    if not phase_string or phase_string.lower() == "nan":
        raise ValueError("sleep_phase_30_sec is empty for this row.")

    stage_codes = list(phase_string)
    timestamps = [bedtime_start + pd.Timedelta(seconds=30 * i) for i in range(len(stage_codes))]

    timeline = pd.DataFrame({"timestamp": timestamps, "stage_code": stage_codes})
    timeline["stage_name"] = timeline["stage_code"].map(STAGE_MAP).fillna("unknown")
    return timeline


# ---------------------------------------------------------------------------
# Wake-window construction
# ---------------------------------------------------------------------------
def build_window_for_night(
    reference_day: pd.Timestamp, start_hhmm: str, end_hhmm: str
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Build UTC wake-window timestamps for the morning of the sleep date."""
    wake_date = reference_day.normalize()
    window_start = pd.Timestamp(f"{wake_date.date()} {start_hhmm}", tz="UTC")
    window_end = pd.Timestamp(f"{wake_date.date()} {end_hhmm}", tz="UTC")

    if window_end <= window_start:
        raise ValueError("Wake window end must be later than wake window start.")
    return window_start, window_end


# ---------------------------------------------------------------------------
# Consecutive-run helpers
# ---------------------------------------------------------------------------
def find_first_confirmed_run(
    window_data: pd.DataFrame, stage_name: str, min_samples: int
) -> tuple[pd.Timestamp, str, int] | None:
    """Return (trigger_time, stage_code, run_length) for the first confirmed run."""
    consecutive = 0
    for _, row in window_data.iterrows():
        if row["stage_name"] == stage_name:
            consecutive += 1
            if consecutive >= min_samples:
                return row["timestamp"], str(row["stage_code"]), consecutive
        else:
            consecutive = 0
    return None


def longest_run(window_data: pd.DataFrame, stage_name: str) -> int:
    """Return the longest consecutive run length for a stage in the window."""
    best = 0
    current = 0
    for _, row in window_data.iterrows():
        if row["stage_name"] == stage_name:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


# ---------------------------------------------------------------------------
# Alarm decision
# ---------------------------------------------------------------------------
def choose_alarm_time(
    timeline: pd.DataFrame,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> WakeDecision:
    """Choose the optimal alarm time inside a wake window.

    Priority:
      1. First confirmed awake run  (>= AWAKE_CONFIRM_SAMPLES consecutive samples).
      2. First confirmed light run  (>= LIGHT_CONFIRM_SAMPLES consecutive samples).
      3. Force alarm at the window end if neither threshold is met.
    """
    window_data = timeline[
        (timeline["timestamp"] >= window_start) & (timeline["timestamp"] <= window_end)
    ].copy()
    window_data = window_data.sort_values("timestamp").reset_index(drop=True)

    if window_data.empty:
        return WakeDecision(
            trigger_time=window_end,
            stage_code="N/A",
            stage_name="forced",
            reason="No sleep-phase samples inside the wake window; alarm forced at window end.",
            consecutive_samples=0,
            trigger_mode="forced_window_end",
        )

    # Priority 1 — confirmed awake
    awake_match = find_first_confirmed_run(window_data, "awake", AWAKE_CONFIRM_SAMPLES)
    if awake_match is not None:
        trigger_time, stage_code, run_length = awake_match
        return WakeDecision(
            trigger_time=trigger_time,
            stage_code=stage_code,
            stage_name="awake",
            reason=(
                f"Triggered after {run_length} consecutive awake samples "
                f"({run_length * 30} seconds), because confirmed awake periods are prioritised."
            ),
            consecutive_samples=run_length,
            trigger_mode="confirmed_awake",
        )

    # Priority 2 — confirmed light
    light_match = find_first_confirmed_run(window_data, "light", LIGHT_CONFIRM_SAMPLES)
    if light_match is not None:
        trigger_time, stage_code, run_length = light_match
        return WakeDecision(
            trigger_time=trigger_time,
            stage_code=stage_code,
            stage_name="light",
            reason=(
                f"Triggered after {run_length} consecutive light-sleep samples "
                f"({run_length * 30} seconds), to avoid short jitter-like stage changes."
            ),
            consecutive_samples=run_length,
            trigger_mode="confirmed_light",
        )

    # Fallback — force at window end
    max_awake_run = longest_run(window_data, "awake")
    max_light_run = longest_run(window_data, "light")
    final_row = window_data.iloc[-1]

    return WakeDecision(
        trigger_time=window_end,
        stage_code=str(final_row["stage_code"]),
        stage_name=str(final_row["stage_name"]),
        reason=(
            "No confirmed awake or light-sleep run found; alarm forced at window end. "
            f"Longest awake run: {max_awake_run} samples; longest light run: {max_light_run} samples."
        ),
        consecutive_samples=max(max_awake_run, max_light_run),
        trigger_mode="forced_window_end",
    )


# ---------------------------------------------------------------------------
# High-level analysis pipelines
# ---------------------------------------------------------------------------
def analyse_selected_row(
    row: pd.Series, wake_start_str: str, wake_end_str: str
) -> WindowAnalysis:
    """Run the full analysis pipeline from an already-selected dataframe row."""
    timeline = decode_sleep_timeline(row)

    reference_day = pd.to_datetime(row["day"], errors="coerce", utc=True)
    if pd.isna(reference_day):
        raise ValueError("Could not parse the 'day' column for the selected row.")

    window_start, window_end = build_window_for_night(reference_day, wake_start_str, wake_end_str)
    window_data = timeline[
        (timeline["timestamp"] >= window_start) & (timeline["timestamp"] <= window_end)
    ].copy()
    window_data = window_data.sort_values("timestamp").reset_index(drop=True)
    decision = choose_alarm_time(timeline, window_start, window_end)

    return WindowAnalysis(
        window_data=window_data,
        decision=decision,
        row=row,
        window_start=window_start,
        window_end=window_end,
    )


def analyse_selected_window(
    df: pd.DataFrame,
    selected_day: str | None,
    wake_start_str: str,
    wake_end_str: str,
) -> WindowAnalysis:
    """Run the full analysis pipeline for one selected day and wake window."""
    row = select_night(df, selected_day)
    return analyse_selected_row(row, wake_start_str, wake_end_str)
