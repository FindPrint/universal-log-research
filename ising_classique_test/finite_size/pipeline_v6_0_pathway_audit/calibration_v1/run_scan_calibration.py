#!/usr/bin/env python
"""Independent synthetic calibration of v6's Cohen-d threshold scan.

This is deliberately a low-level calibration of scan_critical_threshold,
not a full run of UNIVERSAL_LOG. It does not modify the pipeline source.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import platform
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
PIPELINE_PATH = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
SEED = 20261116
REPS = 200
LENGTHS = [76, 150, 300, 600]
PROFILES = ["target_only", "target_plus_2_linked", "target_plus_2_linked_3_unrelated"]
NULLS = ["stationary_ar1", "linear_drift_no_break"]
ALTERNATIVES = [
    ("abrupt_step", 0.5),
    ("abrupt_step", 1.0),
    ("sigmoid_transition", 0.5),
    ("sigmoid_transition", 1.0),
]
RHO = 0.6
DRIFT_RANGE_SD = 1.0
SIGMOID_WIDTH_FRACTION = 0.05


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v6_calibration", PIPELINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load pipeline source: {PIPELINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ar1(rng: np.random.Generator, n: int, rho: float = RHO) -> np.ndarray:
    eps = rng.normal(0.0, math.sqrt(1.0 - rho * rho), n)
    x = np.empty(n, dtype=float)
    x[0] = rng.normal()
    for i in range(1, n):
        x[i] = rho * x[i - 1] + eps[i]
    return x


def make_target(rng: np.random.Generator, n: int, kind: str, amplitude: float = 0.0) -> np.ndarray:
    p = np.linspace(0.0, 1.0, n)
    noise = ar1(rng, n)
    if kind == "stationary_ar1":
        signal = np.zeros(n)
    elif kind == "linear_drift_no_break":
        signal = DRIFT_RANGE_SD * (p - 0.5)
    elif kind == "abrupt_step":
        signal = amplitude * (p >= 0.5)
    elif kind == "sigmoid_transition":
        width = max(SIGMOID_WIDTH_FRACTION, 1.0 / n)
        curve = 1.0 / (1.0 + np.exp(-(p - 0.5) / width))
        signal = amplitude * (curve - curve.mean())
    else:
        raise ValueError(kind)
    return noise + signal


def make_flux_profile(rng: np.random.Generator, target: np.ndarray, profile: str) -> dict[str, np.ndarray]:
    fluxes = {"target": target}
    if profile == "target_only":
        return fluxes
    if profile not in PROFILES:
        raise ValueError(profile)
    fluxes["linked_1"] = 0.8 * target + 0.5 * ar1(rng, len(target))
    fluxes["linked_2"] = 0.6 * target + 0.7 * ar1(rng, len(target))
    if profile == "target_plus_2_linked_3_unrelated":
        for i in range(1, 4):
            fluxes[f"unrelated_{i}"] = ar1(rng, len(target))
    return fluxes


def scan_once(pipeline, rng, n: int, kind: str, amplitude: float, profile: str):
    control = np.linspace(0.0, 100.0, n)
    target = make_target(rng, n, kind, amplitude)
    fluxes = make_flux_profile(rng, target, profile)
    mode_cfg = {"w_size": 80, "min_grp": 2, "test": "cohen_d"}
    t0, curve = pipeline.scan_critical_threshold(fluxes, control, mode_cfg)
    scores = [float(x["score"]) for x in curve if x.get("score") is not None and np.isfinite(x["score"])]
    if not scores:
        return {"status": "no_valid_scan", "t0_candidate_pct": None, "max_abs_cohen_d": None}
    return {"status": "ok", "t0_candidate_pct": float(t0), "max_abs_cohen_d": max(scores)}


def wilson(success: int, total: int, z: float = 1.959963984540054):
    if total <= 0:
        return None, None
    phat = success / total
    denom = 1.0 + z * z / total
    center = (phat + z * z / (2.0 * total)) / denom
    half = z * math.sqrt(phat * (1.0 - phat) / total + z * z / (4.0 * total * total)) / denom
    return center - half, center + half


def q95_higher(values):
    return float(np.quantile(np.asarray(values, dtype=float), 0.95, method="higher"))


def main():
    if not PIPELINE_PATH.is_file():
        raise FileNotFoundError(PIPELINE_PATH)
    pipeline = load_pipeline()
    rng = np.random.default_rng(SEED)
    rows: list[dict] = []
    summaries: list[dict] = []
    total_runs = len(LENGTHS) * len(PROFILES) * (len(NULLS) * REPS * 2 + len(ALTERNATIVES) * REPS)
    completed = 0

    for n in LENGTHS:
        for profile in PROFILES:
            train_scores: dict[str, list[float]] = defaultdict(list)
            validation: dict[str, list[dict]] = defaultdict(list)
            for null_kind in NULLS:
                for split, destination in (("train", train_scores), ("validation", validation)):
                    for rep in range(REPS):
                        result = scan_once(pipeline, rng, n, null_kind, 0.0, profile)
                        completed += 1
                        if completed % 100 == 0:
                            print(f"progress {completed}/{total_runs}", flush=True)
                        row = {
                            "n": n, "profile": profile, "split": split,
                            "scenario": null_kind, "amplitude_sd": 0.0,
                            "replicate": rep, **result,
                        }
                        rows.append(row)
                        if result["status"] == "ok":
                            if split == "train":
                                destination[null_kind].append(result["max_abs_cohen_d"])
                            else:
                                destination[null_kind].append(result)
            if any(len(train_scores[k]) != REPS for k in NULLS):
                raise RuntimeError(f"Unexpected training scan failures at N={n}, profile={profile}")
            thresholds = {k: q95_higher(train_scores[k]) for k in NULLS}
            calibrated_threshold = max(thresholds.values())

            for null_kind in NULLS:
                vals = validation[null_kind]
                hits = sum(x["max_abs_cohen_d"] > calibrated_threshold for x in vals)
                lo, hi = wilson(hits, len(vals))
                summaries.append({
                    "n": n, "profile": profile, "validation_scenario": null_kind,
                    "calibrated_score_threshold": calibrated_threshold,
                    "calibration_q95_stationary": thresholds["stationary_ar1"],
                    "calibration_q95_drift": thresholds["linear_drift_no_break"],
                    "n_validation": len(vals), "alerts": hits,
                    "alert_rate": hits / len(vals), "alert_rate_wilson95_low": lo,
                    "alert_rate_wilson95_high": hi,
                    "median_max_abs_cohen_d": float(np.median([x["max_abs_cohen_d"] for x in vals])),
                    "median_t0_candidate_pct": float(np.median([x["t0_candidate_pct"] for x in vals if x["t0_candidate_pct"] is not None])),
                    "status": "validation",
                })

            for scenario, amplitude in ALTERNATIVES:
                vals = []
                for rep in range(REPS):
                    result = scan_once(pipeline, rng, n, scenario, amplitude, profile)
                    completed += 1
                    if completed % 100 == 0:
                        print(f"progress {completed}/{total_runs}", flush=True)
                    row = {
                        "n": n, "profile": profile, "split": "validation",
                        "scenario": scenario, "amplitude_sd": amplitude,
                        "replicate": rep, **result,
                    }
                    rows.append(row)
                    if result["status"] == "ok":
                        vals.append(result)
                hits = sum(x["max_abs_cohen_d"] > calibrated_threshold for x in vals)
                lo, hi = wilson(hits, len(vals))
                errors = [abs(x["t0_candidate_pct"] / 100.0 - 0.5) for x in vals]
                summaries.append({
                    "n": n, "profile": profile, "validation_scenario": scenario,
                    "amplitude_sd": amplitude,
                    "calibrated_score_threshold": calibrated_threshold,
                    "calibration_q95_stationary": thresholds["stationary_ar1"],
                    "calibration_q95_drift": thresholds["linear_drift_no_break"],
                    "n_validation": len(vals), "alerts": hits,
                    "alert_rate": hits / len(vals) if vals else None,
                    "alert_rate_wilson95_low": lo, "alert_rate_wilson95_high": hi,
                    "median_max_abs_cohen_d": float(np.median([x["max_abs_cohen_d"] for x in vals])) if vals else None,
                    "median_t0_candidate_pct": float(np.median([x["t0_candidate_pct"] for x in vals])) if vals else None,
                    "median_abs_location_error_fraction": float(np.median(errors)) if errors else None,
                    "location_within_5pct_fraction": float(np.mean(np.asarray(errors) <= 0.05)) if errors else None,
                    "status": "validation",
                })
            print(
                f"N={n} profile={profile} threshold={calibrated_threshold:.4f} "
                f"q95_nulls={thresholds}", flush=True
            )

    raw_path = HERE / "scan_calibration_raw.csv"
    summary_path = HERE / "scan_calibration_summary.csv"
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(dict.fromkeys(key for row in summaries for key in row))
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed_exploratory_synthetic_calibration",
        "pipeline_path": str(PIPELINE_PATH),
        "pipeline_sha256": sha256(PIPELINE_PATH),
        "script_sha256": sha256(Path(__file__).resolve()),
        "protocol_path": str(HERE / "PROTOCOL_SCAN_ABSTENTION_V1.md"),
        "protocol_sha256": sha256(HERE / "PROTOCOL_SCAN_ABSTENTION_V1.md"),
        "python": platform.python_version(), "numpy": np.__version__,
        "seed": SEED, "replicates_per_scenario": REPS,
        "lengths": LENGTHS, "flux_profiles": PROFILES,
        "null_scenarios": NULLS,
        "alternatives": [{"scenario": s, "amplitude_sd": a} for s, a in ALTERNATIVES],
        "alert_rule": "For each N and flux profile, score threshold=max(training q95 of stationary AR(1), training q95 of linear drift); alert iff validation maximum scan Cohen-d is strictly greater.",
        "limitations": [
            "low-level Cohen-d scan only; not full UNIVERSAL_LOG pipeline",
            "fixed monotone rank control; does not test data-adaptive Monte Carlo axis",
            "only the declared AR(1) and linear-drift null families are calibrated",
            "simulation threshold is an exploratory 5% design target, not a universal cut-off or p-value",
            "L7b adaptive walk-forward full-pipeline distribution is not estimated here",
        ],
        "raw_csv_sha256": sha256(raw_path), "summary_csv_sha256": sha256(summary_path),
        "raw_rows": len(rows), "summary_rows": len(summaries),
    }
    (HERE / "scan_calibration_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Saved {len(rows)} scan records and {len(summaries)} summary records to {HERE}")


if __name__ == "__main__":
    main()
