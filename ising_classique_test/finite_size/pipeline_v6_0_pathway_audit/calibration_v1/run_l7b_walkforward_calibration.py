#!/usr/bin/env python
"""Calibrate the v6 rolling T0-variability component over synthetic series."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
PIPELINE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
SEED = 20261117
REPS = 200
LENGTHS = [76, 150, 300, 600]
SCENARIOS = [
    ("stationary_ar1", 0.0, False),
    ("linear_drift_no_break", 0.0, False),
    ("abrupt_step", 0.5, True),
    ("abrupt_step", 1.0, True),
    ("sigmoid_transition", 0.5, True),
    ("sigmoid_transition", 1.0, True),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v6_l7b_calibration", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load pipeline source: {PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ar1(rng, n, rho=0.6):
    eps = rng.normal(0.0, np.sqrt(1.0 - rho * rho), n)
    x = np.empty(n, dtype=float)
    x[0] = rng.normal()
    for i in range(1, n):
        x[i] = rho * x[i - 1] + eps[i]
    return x


def series(rng, n, scenario, amplitude):
    p = np.linspace(0.0, 1.0, n)
    signal = np.zeros(n)
    if scenario == "linear_drift_no_break":
        signal = p - 0.5
    elif scenario == "abrupt_step":
        signal = amplitude * (p >= 0.5)
    elif scenario == "sigmoid_transition":
        width = max(0.05, 1.0 / n)
        curve = 1.0 / (1.0 + np.exp(-(p - 0.5) / width))
        signal = amplitude * (curve - curve.mean())
    return ar1(rng, n) + signal


def main():
    pipeline = load_pipeline()
    rng = np.random.default_rng(SEED)
    records = []
    total = len(LENGTHS) * len(SCENARIOS) * REPS
    done = 0
    for n in LENGTHS:
        control = np.linspace(0.0, 100.0, n)
        for scenario, amplitude, event_present in SCENARIOS:
            for rep in range(REPS):
                y = series(rng, n, scenario, amplitude)
                result = pipeline.adaptive_walk_forward_validation(
                    control, y, horizon=15, n_splits=5, window_frac=0.50, min_window=30
                )
                t0_std = result.get("t0_std")
                t0s = result.get("t0_reestimated", [])
                records.append({
                    "n": n, "scenario": scenario, "amplitude_sd": amplitude,
                    "event_present": event_present, "replicate": rep,
                    "status": result.get("status"), "n_folds": result.get("n_folds", len(result.get("folds", []))),
                    "t0_std_rank_percentage_points": t0_std,
                    "t0_std_div_n_exploratory": (float(t0_std) / n) if t0_std is not None else None,
                    "t0_stable_current_cutoff_10": (bool(t0_std <= 10.0) if t0_std is not None else None),
                    "t0_median_pct": float(np.median(t0s)) if t0s else None,
                })
                done += 1
                if done % 100 == 0:
                    print(f"progress {done}/{total}", flush=True)
        print(f"completed N={n}", flush=True)

    raw = HERE / "l7b_walkforward_raw.csv"
    summary = HERE / "l7b_walkforward_summary.csv"
    manifest = HERE / "l7b_walkforward_manifest.json"
    pd.DataFrame(records).to_csv(raw, index=False)
    d = pd.DataFrame(records)
    grouped = d.groupby(["n", "scenario", "amplitude_sd"], dropna=False)
    rows = []
    for (n, scenario, amplitude), g in grouped:
        vals = g.t0_std_rank_percentage_points.dropna().astype(float)
        stable = g.t0_stable_current_cutoff_10.dropna().astype(bool)
        rel = g.t0_std_div_n_exploratory.dropna().astype(float)
        t0med = g.t0_median_pct.dropna().astype(float)
        rows.append({
            "n": int(n), "scenario": scenario, "amplitude_sd": float(amplitude),
            "event_present": bool(g.event_present.iloc[0]), "n_runs": int(len(g)),
            "n_with_metric": int(len(vals)),
            "t0_std_median_percentage_points": float(vals.median()) if len(vals) else None,
            "t0_std_q10": float(vals.quantile(0.10)) if len(vals) else None,
            "t0_std_q90": float(vals.quantile(0.90)) if len(vals) else None,
            "pass_rate_current_t0_std_le_10": float(stable.mean()) if len(stable) else None,
            "t0_std_div_n_median_diagnostic_only": float(rel.median()) if len(rel) else None,
            "t0_median_pct": float(t0med.median()) if len(t0med) else None,
            "status_counts": json.dumps(g.status.value_counts().to_dict(), sort_keys=True),
        })
    pd.DataFrame(rows).to_csv(summary, index=False)
    manifest_data = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed_exploratory_l7b_walkforward_component_calibration",
        "pipeline_path": str(PIPELINE), "pipeline_sha256": sha256(PIPELINE),
        "script_path": str(Path(__file__).resolve()), "script_sha256": sha256(Path(__file__).resolve()),
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "seed": SEED, "replicates": REPS, "lengths": LENGTHS,
        "scenarios": [{"scenario": s, "amplitude_sd": a, "event_present": ev} for s, a, ev in SCENARIOS],
        "method": "Exact v6 adaptive_walk_forward_validation component; control is fixed monotone rank 0..100; horizon=15; n_splits=5; window_frac=0.5; min_window=30.",
        "interpretation_guard": "This estimates only the walk-forward T0 variability check, not the full L7b verdict and not end-to-end pipeline sensitivity.",
        "raw_sha256": sha256(raw), "summary_sha256": sha256(summary),
        "records": len(records), "summary_rows": len(rows),
    }
    manifest.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(records)} folds-based runs; {len(rows)} summary rows")


if __name__ == "__main__":
    main()
