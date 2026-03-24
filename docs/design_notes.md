# Design Notes

## Architecture Rationale

The application is structured as a Python package (`src/oura_alarm/`) with a clear separation of concerns across seven modules. This separation was chosen for three reasons:

**Testability.** The alarm-trigger logic in `analysis.py` is pure computation — it takes a dataframe and timestamps as input and returns a `WakeDecision` dataclass. This makes it straightforward to test without a GUI, network access, or file system. The same applies to `data_loader.py`, which can be tested against mock data or fixture CSVs.

**Change management.** Isolating the GUI (`gui.py`) from the analysis logic means that modifications to the user interface, such as adding new controls or changing layout, do not risk breaking the alarm algorithm. Similarly, adding a new data source (for example, a webhook listener) only requires changes to `data_loader.py` and potentially `config.py` — the analysis pipeline remains untouched.

**Readability for portfolio review.** Each module file is short enough to read end-to-end and has a clear, single purpose. A reviewer can understand the alarm logic by reading `analysis.py` alone, without needing to parse GUI event handlers or API pagination.

## Module Responsibilities

| Module | Owns | Does not own |
|---|---|---|
| `config.py` | All magic numbers, thresholds, paths, API URLs | No logic |
| `models.py` | `WakeDecision`, `WindowAnalysis` dataclasses | No logic |
| `data_loader.py` | CSV/API I/O, column validation, caching | No analysis |
| `analysis.py` | Timeline decoding, window logic, alarm decisions | No I/O |
| `formatting.py` | Text summary generation | No decisions |
| `plotting.py` | Matplotlib rendering | No data loading |
| `gui.py` | Tkinter wiring and layout | Delegates all work |

## Key Design Decisions

### Consecutive-sample confirmation

Single-sample stage labels in Oura data often include brief "jitter" — one or two samples of a different stage embedded in an otherwise continuous run. The confirmation threshold (default: 5 consecutive samples = 150 seconds) filters out these artefacts so the alarm only triggers on stable stage transitions.

### UTC timestamps

All internal timestamps use UTC. The Oura API returns UTC-offset timestamps, and the CSV export includes timezone information. For a student project focused on algorithmic correctness, UTC simplifies comparison logic. Improved local-timezone handling is noted as future work.

### Forced window-end fallback

If no confirmed awake or light-sleep run is found inside the entire wake window, the alarm defaults to the window end. This guarantees the user always wakes up, at worst at their latest acceptable time.

## Data Flow

```
CSV file / Oura API
        │
        ▼
   data_loader.py  ──►  pd.DataFrame (normalised sleep records)
        │
        ▼
   analysis.py     ──►  decode timeline  ──►  build wake window  ──►  choose_alarm_time()
        │
        ▼
   WakeDecision + WindowAnalysis dataclasses
        │
        ├──►  formatting.py  ──►  Text summary panel
        └──►  plotting.py   ──►  Matplotlib chart
```

## Honest Scope Statement

This project analyses sleep-stage data **after it has been recorded and synced** from the Oura Ring. The Oura API exposes `sleep_phase_30_sec` data only once a sleep session is available (typically after the ring syncs in the morning or after opening the Oura app). The system does **not** currently perform live, real-time overnight monitoring.

True real-time alarm triggering would require either continuous polling of the API during sleep (with unknown sync latency) or a push/webhook mechanism that Oura does not currently document publicly. This is noted as future investigation work.

## Testing Strategy

Tests are organised into two categories:

- `test_analysis.py` — unit tests for the core alarm logic, including edge cases like empty windows, sub-threshold runs, and stage priority ordering.
- `test_data_loader.py` — tests for token handling, date-range generation, and error paths for missing files.

The GUI is not unit-tested directly (Tkinter testing is fragile and low-value for a project of this scope), but the functions it calls are all individually testable.

## Versioning and Branching Strategy

- **`main`** — stable, reviewed code only
- **`dev`** — active development branch
- **Feature branches** — `feature/xyz` off `dev` for individual changes
- Tags follow semantic versioning: `v0.1.0`, `v0.2.0`, etc.
- The `CHANGELOG.md` is updated with every tagged release
