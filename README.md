# Oura Smart Alarm Analyser

A Python tool that analyses Oura Ring sleep-stage data to identify the optimal wake-up time within a user-defined wake window. Built as part of the University of Bath EE22005 Engineering Practice and Design (EPD) synthesis portfolio.

## Overview

The Oura Smart Alarm Analyser decodes the 30-second resolution `sleep_phase_30_sec` data from Oura sleep records and applies a consecutive-sample confirmation algorithm to determine when a sleeper is genuinely in a light or awake stage — rather than experiencing brief stage jitter. The tool then recommends the best alarm trigger point inside a configurable wake window.

**Key capabilities:**

- Decode Oura `sleep_phase_30_sec` into a timestamped sleep-stage timeline
- Identify the optimal alarm time using confirmed consecutive-sample logic
- Support both **CSV export** and **Oura API** (`/v2/usercollection/sleep`) data sources
- Interactive Tkinter GUI with date/record selection and configurable wake windows
- Matplotlib visualisation of sleep stages and alarm trigger within the wake window
- Detailed text summary including stage distribution, segment analysis, and decision reasoning

> **Note on real-time capability:** The current system analyses sleep data that has already been recorded and synced. The Oura API exposes detailed session data after sync/availability, not as a guaranteed continuous stream during sleep. True live overnight alarm triggering is listed as future work pending investigation of Oura's near-real-time sync behaviour and potential webhook support.

## Project Structure

```
oura-smart-alarm/
├── README.md
├── LICENSE                      # MIT
├── CHANGELOG.md
├── requirements.txt
├── run.py                       # Convenience launcher
├── .gitignore
│
├── src/
│   └── oura_alarm/
│       ├── __init__.py          # Package version
│       ├── __main__.py          # python -m oura_alarm entry point
│       ├── config.py            # Constants, thresholds, API settings
│       ├── models.py            # WakeDecision and WindowAnalysis dataclasses
│       ├── data_loader.py       # CSV and API data loading
│       ├── analysis.py          # Stage decoding, alarm logic, pipelines
│       ├── formatting.py        # Text summary builders
│       ├── plotting.py          # Matplotlib wake-window chart
│       └── gui.py               # Tkinter application
│
├── tests/
│   ├── __init__.py
│   ├── test_analysis.py         # Unit tests for alarm logic
│   └── test_data_loader.py      # Unit tests for data loading
│
├── scripts/
│   └── api_test.py              # Standalone API connectivity test
│
├── data/                        # Local CSV data (git-ignored)
│   └── .gitkeep
│
├── figures/                     # Screenshots and generated plots (git-ignored)
│   └── .gitkeep
│
└── docs/
    └── design_notes.md          # Architecture, decisions, future work
```

## Installation

### Prerequisites

- Python 3.10 or later
- `tkinter` (included with most Python installations; on Ubuntu: `sudo apt install python3-tk`)

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/oura-smart-alarm.git
cd oura-smart-alarm

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Oura API access (optional)

To use API mode, you need an Oura personal access token:

1. Go to [https://cloud.ouraring.com/personal-access-tokens](https://cloud.ouraring.com/personal-access-tokens)
2. Generate a new token with sleep data permissions
3. Export it as an environment variable:

```bash
export OURA_ACCESS_TOKEN="your_token_here"
```

> Never commit your token. The `.gitignore` already excludes `.env` files.

### CSV data

Place your Oura sleep data export (`sleepmodel.csv`, semicolon-separated) in the `data/` directory:

```
data/sleepmodel.csv
```

## Usage

### GUI mode (recommended)

```bash
python run.py
```

Or using the package entry point:

```bash
python -m src.oura_alarm
```

The GUI allows you to:
- Switch between CSV and API data sources
- Select a specific sleep date/record
- Set custom wake window start and end times (HH:MM)
- View the alarm decision, stage distribution, and segment analysis
- See a matplotlib chart of sleep stages within the wake window

### API connectivity test

```bash
python scripts/api_test.py
```

## How the Alarm Logic Works

The algorithm operates on 30-second sleep-stage samples within a user-defined wake window:

1. **Priority 1 — Confirmed awake:** If at least 5 consecutive samples are classified as "awake" (stage code 4), trigger the alarm at that point.
2. **Priority 2 — Confirmed light sleep:** If at least 5 consecutive "light" samples (stage code 2) are found, trigger there.
3. **Fallback:** If neither threshold is met anywhere in the window, the alarm is forced at the window end.

The consecutive-sample requirement (configurable in `config.py`) prevents false triggers from brief single-sample stage jitter that is common in Oura data.

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Current Status and Future Work

### Implemented (v0.1.0)

- CSV-based sleep data loading and validation
- Oura API v2 integration with pagination and token management
- 30-second sleep-phase timeline decoding
- Confirmed consecutive-sample alarm trigger logic
- Tkinter GUI with dual-source support
- Matplotlib wake-window visualisation
- Stage segment and distribution summaries

### Future Work

- **Near-real-time triggering:** Investigate Oura's sync latency and potential webhook/push support to determine feasibility of live overnight alarm triggering
- **Timezone handling:** Improve timezone awareness beyond the current UTC-based approach
- **Configurable thresholds:** Expose confirmation sample counts in the GUI
- **Historical trend analysis:** Aggregate alarm decisions across multiple nights
- **Audio/notification integration:** Connect alarm decisions to system notifications or sound output
- **Packaging:** Add `pyproject.toml` for proper distribution

## Module Reference

| Module | Responsibility |
|---|---|
| `config.py` | All constants, thresholds, paths, and API settings |
| `models.py` | `WakeDecision` and `WindowAnalysis` dataclasses |
| `data_loader.py` | CSV parsing, API fetching, source selection |
| `analysis.py` | Timeline decoding, window construction, alarm logic |
| `formatting.py` | Text summary generation for the GUI |
| `plotting.py` | Matplotlib chart rendering |
| `gui.py` | Tkinter application and event wiring |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

Viggo Gustafson — University of Bath, EE22005 EPD
