#!/usr/bin/env python
"""Rebuild the calibration summary from the immutable raw scan CSV."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
PIPELINE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
RAW = HERE / "scan_calibration_raw.csv"
SUMMARY = HERE / "scan_calibration_summary.csv"
REPORT = HERE / "scan_calibration_report.json"
MANIFEST = HERE / "scan_calibration_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def wilson(success: int, total: int, z: float = 1.959963984540054):
    if total <= 0:
        return None, None
    p = success / total
    d = 1 + z * z / total
    center = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return center - half, center + half


def q95_higher(values):
    return float(np.quantile(np.asarray(values, dtype=float), 0.95, method="higher"))


def main():
    if not RAW.is_file():
        raise FileNotFoundError(RAW)
    raw = pd.read_csv(RAW)
    expected_rows = 19_200
    if len(raw) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} raw scans; found {len(raw)}")
    failures = int((raw.status != "ok").sum())
    if failures:
        raise RuntimeError(f"Raw scan CSV contains {failures} failed scans")

    out = []
    calibration = {}
    for (n, profile), group in raw.groupby(["n", "profile"], sort=True):
        train = group[group.split == "train"]
        thresholds_by_null = {
            scenario: q95_higher(train.loc[train.scenario == scenario, "max_abs_cohen_d"])
            for scenario in ("stationary_ar1", "linear_drift_no_break")
        }
        if any(train.loc[train.scenario == k].shape[0] != 200 for k in thresholds_by_null):
            raise RuntimeError(f"Unexpected training sample size for N={n}, profile={profile}")
        threshold = max(thresholds_by_null.values())
        calibration[f"N{n}|{profile}"] = {
            "null_training_q95": thresholds_by_null,
            "conservative_threshold": threshold,
        }
        validation = group[group.split == "validation"]
        for (scenario, amplitude_value), sub in validation.groupby(["scenario", "amplitude_sd"], sort=True):
            is_null = scenario in thresholds_by_null
            if is_null:
                sub = sub[sub.amplitude_sd == 0]
                amplitude = None
            else:
                amplitude = float(amplitude_value)
            n_total = len(sub)
            if n_total != 200:
                raise RuntimeError(f"Unexpected validation count for {n}/{profile}/{scenario}/{amplitude}: {n_total}")
            hits = int((sub.max_abs_cohen_d > threshold).sum())
            detected = sub[sub.max_abs_cohen_d > threshold]
            lo, hi = wilson(hits, n_total)
            t0 = sub.t0_candidate_pct.to_numpy(dtype=float)
            row = {
                "n": int(n), "profile": profile, "scenario": scenario,
                "amplitude_sd": amplitude,
                "calibrated_score_threshold": threshold,
                "calibration_q95_stationary": thresholds_by_null["stationary_ar1"],
                "calibration_q95_drift": thresholds_by_null["linear_drift_no_break"],
                "n_validation": n_total, "alerts": hits,
                "alert_rate": hits / n_total,
                "alert_rate_wilson95_low": lo, "alert_rate_wilson95_high": hi,
                "median_max_abs_cohen_d": float(sub.max_abs_cohen_d.median()),
                "median_t0_candidate_pct": float(np.median(t0)),
                "status": "validation",
            }
            if not is_null:
                error = np.abs(t0 / 100.0 - 0.5)
                row["median_abs_location_error_fraction"] = float(np.median(error))
                row["location_within_5pct_fraction"] = float(np.mean(error <= 0.05))
                detected_error = np.abs(detected.t0_candidate_pct.to_numpy(dtype=float) / 100.0 - 0.5)
                row["n_alerted_with_location"] = len(detected_error)
                row["median_abs_location_error_fraction_when_alerted"] = (
                    float(np.median(detected_error)) if len(detected_error) else None
                )
                row["location_within_5pct_fraction_when_alerted"] = (
                    float(np.mean(detected_error <= 0.05)) if len(detected_error) else None
                )
            out.append(row)

    with SUMMARY.open("w", newline="", encoding="utf-8") as f:
        fields = list(dict.fromkeys(k for row in out for k in row))
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)

    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed_exploratory_synthetic_calibration",
        "raw_input": RAW.name,
        "raw_sha256": sha256(RAW),
        "raw_records": len(raw),
        "failed_scans": failures,
        "calibration": calibration,
        "validation_summary": out,
        "scope": "v6 low-level scan_critical_threshold only; no data-adaptive axis, MC optimization, TLog, estimators, Q/F or L7 used",
        "interpretation_guard": "The score threshold is fitted to two simulated null families. It is not an empirical p-value, clinical result, or universal threshold.",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "created_utc": report["created_utc"],
        "status": report["status"],
        "pipeline_path": str(PIPELINE),
        "pipeline_sha256": sha256(PIPELINE),
        "protocol_path": str(HERE / "PROTOCOL_SCAN_ABSTENTION_V1.md"),
        "protocol_sha256": sha256(HERE / "PROTOCOL_SCAN_ABSTENTION_V1.md"),
        "runner_path": str(HERE / "run_scan_calibration.py"),
        "runner_sha256": sha256(HERE / "run_scan_calibration.py"),
        "summarizer_path": str(Path(__file__).resolve()),
        "summarizer_sha256": sha256(Path(__file__).resolve()),
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "seed": 20261116, "replicates_per_scenario": 200,
        "lengths": [76, 150, 300, 600],
        "profiles": ["target_only", "target_plus_2_linked", "target_plus_2_linked_3_unrelated"],
        "scan_records": len(raw), "failed_scans": failures,
        "raw_csv_sha256": sha256(RAW), "summary_csv_sha256": sha256(SUMMARY),
        "report_json_sha256": sha256(REPORT),
        "run_note": "Initial run completed all 19,200 scans and wrote raw CSV; the mixed-schema summary export raised a DictWriter fieldnames error. Summary and manifest were reconstructed from the preserved raw CSV without rerunning scans. Runner now uses the union of summary fields.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Raw scans: {len(raw)}; failed: {failures}; summary rows: {len(out)}")
    print(f"Summary: {SUMMARY}")
    print(f"Report: {REPORT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
