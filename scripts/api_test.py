#!/usr/bin/env python3
"""Standalone Oura API connectivity test.

Usage:
    export OURA_ACCESS_TOKEN="your_token"
    python scripts/api_test.py

This script is intentionally kept simple and self-contained for quick
debugging of API access without importing the main application.
"""

import json
import os

import requests

access_token = os.getenv("OURA_ACCESS_TOKEN")
if not access_token:
    raise RuntimeError("OURA_ACCESS_TOKEN is not set.")

url = "https://api.ouraring.com/v2/usercollection/sleep"
params = {
    "start_date": "2026-03-01",
    "end_date": "2026-03-24",
}
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(url, headers=headers, params=params, timeout=30)
print("Status:", response.status_code)
print("Requested date range:", params["start_date"], "to", params["end_date"])

data = response.json()
print("Top-level keys:", list(data.keys()))

records = data.get("data", [])
print("Total records returned:", len(records))

if not records:
    print("No records returned by the API.")
else:
    days = [r.get("day") for r in records if r.get("day")]
    unique_days = sorted(set(days))
    print("Earliest day:", unique_days[0] if unique_days else "N/A")
    print("Latest day:", unique_days[-1] if unique_days else "N/A")

    first = records[0]
    print("\nFirst record keys:", sorted(first.keys()))
    print("\nSleep/phase/movement fields:")
    for key in sorted(first.keys()):
        if any(k in key.lower() for k in ("sleep", "phase", "movement")):
            print(f"  {key}: {type(first[key]).__name__}")
