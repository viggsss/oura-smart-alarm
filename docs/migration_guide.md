# Migration Guide: From Flat Scripts to Repository Structure

This document explains how to move your existing files into the new repository structure and the first 10 git commits to make.

## File Mapping

| Original file | New location | Notes |
|---|---|---|
| `oura.py` | Refactored into `src/oura_alarm/` modules | Logic is split across `config.py`, `models.py`, `data_loader.py`, `analysis.py`, `formatting.py`, `plotting.py`, and `gui.py` |
| `oura_api_test.py` | `scripts/api_test.py` | Kept as a standalone diagnostic script |
| `sleepmodel.csv` | `data/sleepmodel.csv` | Git-ignored; keep locally but do not commit (contains personal health data) |

## Step-by-Step Migration

1. Create the repository on GitHub (empty, no README — you will push yours)
2. Clone it locally:
   ```bash
   git clone https://github.com/<username>/oura-smart-alarm.git
   cd oura-smart-alarm
   ```
3. Copy the entire contents of the output folder into the repo root
4. Place your `sleepmodel.csv` into `data/`
5. Optionally place any GUI screenshots into `figures/`
6. Follow the commit sequence below

## First 10 Git Commits (In Order)

These commits tell a clear story of project evolution for a portfolio reviewer.

### Commit 1 — Project scaffolding
```bash
git add .gitignore LICENSE requirements.txt
git commit -m "Initial project scaffolding with .gitignore, MIT license, and requirements"
```

### Commit 2 — Package structure
```bash
git add src/oura_alarm/__init__.py src/oura_alarm/__main__.py
git commit -m "Add oura_alarm package skeleton with version and entry point"
```

### Commit 3 — Configuration and data models
```bash
git add src/oura_alarm/config.py src/oura_alarm/models.py
git commit -m "Add centralised config constants and WakeDecision/WindowAnalysis models"
```

### Commit 4 — Data loading layer
```bash
git add src/oura_alarm/data_loader.py
git commit -m "Add CSV and Oura API data loading with column validation"
```

### Commit 5 — Core analysis logic
```bash
git add src/oura_alarm/analysis.py
git commit -m "Add sleep-stage decoding and consecutive-sample alarm trigger logic"
```

### Commit 6 — Formatting and plotting
```bash
git add src/oura_alarm/formatting.py src/oura_alarm/plotting.py
git commit -m "Add text summary formatting and matplotlib wake-window chart"
```

### Commit 7 — GUI
```bash
git add src/oura_alarm/gui.py run.py
git commit -m "Add Tkinter GUI with source selection, date picker, and wake window controls"
```

### Commit 8 — Unit tests
```bash
git add tests/
git commit -m "Add unit tests for alarm logic, run detection, and data loading"
```

### Commit 9 — Documentation
```bash
git add README.md CHANGELOG.md docs/ data/.gitkeep figures/.gitkeep
git commit -m "Add README, changelog, design notes, and directory placeholders"
```

### Commit 10 — API test script
```bash
git add scripts/api_test.py
git commit -m "Add standalone Oura API connectivity test script"
```

## Branch Strategy

After these 10 commits on `main`:

```bash
git checkout -b dev
```

All future development happens on `dev`. Create feature branches off `dev`:

```bash
git checkout -b feature/configurable-thresholds dev
# ... make changes ...
git checkout dev
git merge feature/configurable-thresholds
```

Merge `dev` into `main` only for tagged releases:

```bash
git checkout main
git merge dev
git tag v0.1.0
git push origin main --tags
```
