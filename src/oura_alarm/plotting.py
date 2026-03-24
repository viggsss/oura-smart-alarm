"""Matplotlib plotting for wake-window visualisation."""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from .models import WindowAnalysis

STAGE_LABELS = {1: "Deep", 2: "Light", 3: "REM", 4: "Awake"}


def plot_window(ax: plt.Axes, analysis: WindowAnalysis) -> None:
    """Plot sleep stages inside the selected wake window with the trigger line."""
    ax.clear()
    window_data = analysis.window_data.copy()

    if window_data.empty:
        ax.set_title("No samples in selected wake window")
        ax.set_xlabel("Time")
        ax.set_ylabel("Sleep stage")
        return

    y_values = window_data["stage_code"].astype(int)
    x_values = pd.to_datetime(window_data["timestamp"])

    ax.step(x_values, y_values, where="post", linewidth=2)
    ax.axvspan(analysis.window_start, analysis.window_end, alpha=0.15)
    ax.axvline(analysis.decision.trigger_time, linestyle="--", linewidth=2)

    ax.set_title("Sleep stages in selected wake window")
    ax.set_xlabel("Time")
    ax.set_ylabel("Stage")
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels([STAGE_LABELS[i] for i in [1, 2, 3, 4]])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(True, alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
