# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-03-24

### Added

- Initial project structure with modular `src/oura_alarm/` package
- CSV data loading from Oura sleepmodel exports (semicolon-separated)
- Oura API v2 integration (`/v2/usercollection/sleep`) with pagination
- 30-second `sleep_phase_30_sec` timeline decoding
- Consecutive-sample confirmation algorithm for alarm trigger decisions
- Tkinter GUI with source selection (CSV / API), date picker, and wake window configuration
- Matplotlib visualisation of sleep stages within the wake window
- Text summary panel with stage distribution, segment analysis, and alarm reasoning
- Unit tests for core analysis logic and data loading
- Project documentation (README, design notes, changelog)
