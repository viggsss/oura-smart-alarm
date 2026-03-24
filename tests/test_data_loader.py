"""Unit tests for data loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.oura_alarm.data_loader import (
    get_api_date_range,
    load_sleep_data_csv,
    require_oura_access_token,
)


class TestRequireOuraAccessToken:
    def test_raises_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="OURA_ACCESS_TOKEN"):
                require_oura_access_token()

    def test_returns_token_when_set(self):
        with patch.dict(os.environ, {"OURA_ACCESS_TOKEN": "test_token_abc"}):
            assert require_oura_access_token() == "test_token_abc"


class TestGetApiDateRange:
    def test_returns_two_date_strings(self):
        start, end = get_api_date_range(lookback_days=7)
        assert len(start) == 10  # YYYY-MM-DD
        assert len(end) == 10


class TestLoadSleepDataCsv:
    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_sleep_data_csv(Path("/nonexistent/path/sleep.csv"))
