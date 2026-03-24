"""Data classes used across the analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class WakeDecision:
    """Encapsulates the alarm-trigger decision for a single wake window."""

    trigger_time: pd.Timestamp
    stage_code: str
    stage_name: str
    reason: str
    consecutive_samples: int
    trigger_mode: str


@dataclass
class WindowAnalysis:
    """Bundles a complete analysis result for one sleep record and wake window."""

    window_data: pd.DataFrame
    decision: WakeDecision
    row: pd.Series
    window_start: pd.Timestamp
    window_end: pd.Timestamp
