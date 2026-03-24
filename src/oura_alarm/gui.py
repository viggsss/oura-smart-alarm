"""Tkinter GUI for the Oura Smart Alarm Analyser."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .analysis import (
    analyse_selected_row,
    build_record_options,
    list_available_days,
)
from .config import WAKE_WINDOW_END, WAKE_WINDOW_START
from .data_loader import load_selected_source_data, load_sleep_data_csv
from .formatting import populate_results_text
from .plotting import plot_window


def launch() -> None:
    """Build and run the Tkinter GUI."""
    csv_df = load_sleep_data_csv()
    available_days = list_available_days(csv_df)
    if not available_days:
        raise ValueError("No valid sleep dates found in the CSV dataset.")

    api_cache: dict[str, pd.DataFrame | None] = {"df": None}
    record_option_cache: dict[str, dict[str, int]] = {"CSV": {}, "API": {}}

    # --- Window setup ---
    root = tk.Tk()
    root.title("Oura Smart Alarm Analyser")
    root.geometry("1300x900")

    controls_frame = ttk.Frame(root, padding=10)
    controls_frame.pack(side=tk.TOP, fill=tk.X)

    # Source selector
    ttk.Label(controls_frame, text="Source:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    source_var = tk.StringVar(value="CSV")
    source_combo = ttk.Combobox(
        controls_frame, textvariable=source_var, values=["CSV", "API"], width=8, state="readonly"
    )
    source_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Date selector
    ttk.Label(controls_frame, text="Sleep date:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    date_var = tk.StringVar(value=available_days[-1])
    date_combo = ttk.Combobox(
        controls_frame, textvariable=date_var, values=available_days, width=15, state="readonly"
    )
    date_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    # Wake window entries
    ttk.Label(controls_frame, text="Wake window start:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
    start_var = tk.StringVar(value=WAKE_WINDOW_START)
    ttk.Entry(controls_frame, textvariable=start_var, width=10).grid(row=0, column=5, padx=5, pady=5, sticky="w")

    ttk.Label(controls_frame, text="Wake window end:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
    end_var = tk.StringVar(value=WAKE_WINDOW_END)
    ttk.Entry(controls_frame, textvariable=end_var, width=10).grid(row=0, column=7, padx=5, pady=5, sticky="w")

    # Status bar
    status_var = tk.StringVar(value="Ready.")
    ttk.Label(controls_frame, textvariable=status_var).grid(row=0, column=9, padx=20, pady=5, sticky="w")

    # --- Content area ---
    content_frame = ttk.Frame(root, padding=10)
    content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    text_frame = ttk.Frame(content_frame)
    text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    results_text = tk.Text(text_frame, wrap="none", width=80)
    results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    results_text.config(state="disabled")

    text_scroll_y = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
    text_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    results_text.configure(yscrollcommand=text_scroll_y.set)

    figure_frame = ttk.Frame(content_frame)
    figure_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    fig, ax = plt.subplots(figsize=(7, 5), tight_layout=True)
    canvas = FigureCanvasTkAgg(fig, master=figure_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # --- Callbacks ---
    def refresh_available_dates(*_args: object) -> None:
        try:
            selected_source = source_var.get().strip() or "CSV"
            df_for_source = load_selected_source_data(
                selected_source, csv_df, api_cache, force_api_refresh=(selected_source == "API")
            )
            record_labels, label_to_index = build_record_options(df_for_source)
            if not record_labels:
                raise ValueError(f"No valid sleep records found for source {selected_source}.")
            record_option_cache[selected_source] = label_to_index
            date_combo["values"] = record_labels
            if date_var.get() not in record_labels:
                date_var.set(record_labels[-1])
            latest_day = (
                pd.to_datetime(df_for_source["day"], errors="coerce")
                .dropna()
                .dt.strftime("%Y-%m-%d")
                .max()
            )
            status_var.set(
                f"Loaded {selected_source} data source | "
                f"{len(record_labels)} records | latest day: {latest_day}"
            )
        except Exception as exc:
            messagebox.showerror("Source error", str(exc))
            status_var.set(f"Failed to load {source_var.get()} data.")

    def run_analysis() -> None:
        try:
            selected_source = source_var.get().strip() or "CSV"
            df = load_selected_source_data(
                selected_source, csv_df, api_cache, force_api_refresh=(selected_source == "API")
            )
            selected_label = date_var.get().strip()
            if not selected_label:
                raise ValueError("No sleep record is selected.")

            label_to_index = record_option_cache.get(selected_source, {})
            if selected_label not in label_to_index:
                raise ValueError(
                    f"Selected record '{selected_label}' is not available for source {selected_source}."
                )

            selected_row = df.iloc[label_to_index[selected_label]]
            wake_start_str = start_var.get().strip() or WAKE_WINDOW_START
            wake_end_str = end_var.get().strip() or WAKE_WINDOW_END

            analysis = analyse_selected_row(selected_row, wake_start_str, wake_end_str)
            populate_results_text(results_text, analysis)
            plot_window(ax, analysis)
            canvas.draw()

            latest_day = (
                pd.to_datetime(df["day"], errors="coerce")
                .dropna()
                .dt.strftime("%Y-%m-%d")
                .max()
            )
            status_var.set(
                f"Source: {selected_source} | latest day: {latest_day} | "
                f"Record: {selected_label} | "
                f"Trigger: {analysis.decision.trigger_time.strftime('%H:%M:%S')} | "
                f"Mode: {analysis.decision.trigger_mode}"
            )
        except Exception as exc:
            messagebox.showerror("Analysis error", str(exc))
            status_var.set("Analysis failed.")

    def refresh_api_now() -> None:
        try:
            api_cache["df"] = None
            refresh_available_dates()
            if source_var.get().strip() == "API":
                run_analysis()
        except Exception as exc:
            messagebox.showerror("API refresh error", str(exc))
            status_var.set("API refresh failed.")

    # --- Wire up controls ---
    ttk.Button(controls_frame, text="Run analysis", command=run_analysis).grid(
        row=0, column=8, padx=10, pady=5, sticky="w"
    )
    ttk.Button(controls_frame, text="Refresh API", command=refresh_api_now).grid(
        row=0, column=10, padx=10, pady=5, sticky="w"
    )
    source_combo.bind("<<ComboboxSelected>>", refresh_available_dates)

    # Initial load
    refresh_available_dates()
    run_analysis()
    root.mainloop()
