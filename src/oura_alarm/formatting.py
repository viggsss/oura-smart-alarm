"""Text formatting and summary helpers."""

from __future__ import annotations

import tkinter as tk

import pandas as pd

from .analysis import longest_run
from .models import WindowAnalysis


def build_segment_summary(window_data: pd.DataFrame) -> str:
    """Build a compact summary of contiguous stage runs inside the wake window."""
    if window_data.empty:
        return "No samples found inside wake window."

    lines: list[str] = []
    current_stage = str(window_data.iloc[0]["stage_name"])
    segment_start = window_data.iloc[0]["timestamp"]
    previous_timestamp = window_data.iloc[0]["timestamp"]

    for _, row in window_data.iloc[1:].iterrows():
        stage = str(row["stage_name"])
        timestamp = row["timestamp"]
        if stage != current_stage:
            duration_seconds = int((previous_timestamp - segment_start).total_seconds()) + 30
            lines.append(
                f"{current_stage:<5} | "
                f"{segment_start.strftime('%H:%M:%S')} -> "
                f"{previous_timestamp.strftime('%H:%M:%S')} | "
                f"{duration_seconds:>4} s"
            )
            current_stage = stage
            segment_start = timestamp
        previous_timestamp = timestamp

    duration_seconds = int((previous_timestamp - segment_start).total_seconds()) + 30
    lines.append(
        f"{current_stage:<5} | "
        f"{segment_start.strftime('%H:%M:%S')} -> "
        f"{previous_timestamp.strftime('%H:%M:%S')} | "
        f"{duration_seconds:>4} s"
    )
    return "\n".join(lines)


def populate_results_text(text_widget: tk.Text, analysis: WindowAnalysis) -> None:
    """Fill a Tkinter Text widget with the analysis summary."""
    window_data = analysis.window_data
    decision = analysis.decision
    row = analysis.row

    counts = (
        window_data["stage_name"].value_counts(dropna=False)
        if not window_data.empty
        else pd.Series(dtype=int)
    )

    lines = [
        "=== Night summary ===",
        f"Day: {row['day']}",
        f"Bedtime start: {pd.to_datetime(row['bedtime_start'])}",
        f"Bedtime end:   {pd.to_datetime(row['bedtime_end'])}",
        "",
        "=== Wake window summary ===",
        f"Window start: {analysis.window_start}",
        f"Window end:   {analysis.window_end}",
        f"Samples in window: {len(window_data)}",
        "",
        "Stage distribution:",
    ]

    for stage in ["deep", "light", "rem", "awake"]:
        lines.append(f"  {stage}: {int(counts.get(stage, 0))}")

    lines.extend([
        "",
        "Longest consecutive runs:",
        f"  deep:  {longest_run(window_data, 'deep')} samples ({longest_run(window_data, 'deep') * 30} seconds)",
        f"  light: {longest_run(window_data, 'light')} samples ({longest_run(window_data, 'light') * 30} seconds)",
        f"  rem:   {longest_run(window_data, 'rem')} samples ({longest_run(window_data, 'rem') * 30} seconds)",
        f"  awake: {longest_run(window_data, 'awake')} samples ({longest_run(window_data, 'awake') * 30} seconds)",
        "",
        "=== Alarm decision ===",
        f"Trigger time:        {decision.trigger_time}",
        f"Stage code:          {decision.stage_code}",
        f"Stage name:          {decision.stage_name}",
        f"Trigger mode:        {decision.trigger_mode}",
        f"Consecutive samples: {decision.consecutive_samples}",
        f"Reason:              {decision.reason}",
        "",
        "=== Stage segments inside wake window ===",
        build_segment_summary(window_data),
        "",
        "=== Raw rows inside wake window ===",
        window_data.to_string(index=False) if not window_data.empty else "No rows in window.",
    ])

    text_widget.config(state="normal")
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", "\n".join(lines))
    text_widget.config(state="disabled")
