#!/usr/bin/env python3
"""Run the v6.0.1 UNIVERSAL_LOG analysis core on all numeric PDAC patient axes.

This is a descriptive cross-sectional audit of a 57-patient table. Patients
are not a time series. Each native numeric column is tried as control in a
separate run; that axis is excluded from the mapped fluxes. All other numeric
columns remain distinct fluxes. No categorical text is silently encoded.
Three row orders are compared to expose order dependence on cross-sectional
data. The pipeline's fast-mode minimum of 50 valid control observations is
kept unchanged; axes below it are logged as abstentions.
"""
from __future__ import annotations

import contextlib
import gzip
import hashlib
import importlib.util
import json
import os
import platform
import random
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE_CSV = (PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-17" /
              "multi_axis_resistance" / "results_all_57" /
              "patient_level_normalized_57.csv")
PIPELINE = (PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" /
            "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" /
            "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py")
OUT = HERE / "results"
MIN_VALID = 50
SEED = 20261121
ORDERS = ("source_order", "reverse_order", "shuffle_20261121")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v601", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import pipeline: {PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def order_indices(n: int, label: str) -> np.ndarray:
    if label == "source_order":
        return np.arange(n)
    if label == "reverse_order":
        return np.arange(n - 1, -1, -1)
    if label == "shuffle_20261121":
        return np.random.default_rng(SEED).permutation(n)
    raise ValueError(label)


def persist_manifest(manifest: dict) -> None:
    (OUT / "RUN_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=json_default) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(manifest["runs"]).to_csv(OUT / "RUN_SUMMARY.csv", index=False)


def run_one(module, frame: pd.DataFrame, order_name: str, control: str) -> dict:
    numeric = frame.select_dtypes(include=[np.number]).columns.tolist()
    valid_n = int(pd.to_numeric(frame[control], errors="coerce").notna().sum())
    if valid_n < MIN_VALID:
        return {
            "order": order_name, "control": control, "status": "abstain_minimum_n",
            "n_rows": int(len(frame)), "n_valid_control": valid_n,
            "minimum_required": MIN_VALID, "n_numeric_fluxes_available": max(0, len(numeric) - 1),
            "reason": "v6.0.1 fast-mode gate kept unchanged; no N override",
        }
    if int(frame[control].nunique(dropna=True)) < 2:
        return {
            "order": order_name, "control": control, "status": "abstain_constant_axis",
            "n_rows": int(len(frame)), "n_valid_control": valid_n,
            "minimum_required": MIN_VALID, "n_unique": int(frame[control].nunique(dropna=True)),
            "reason": "constant control has no axis variation",
        }

    flux_map = {name: [name] for name in numeric if name != control}
    run_id = f"{order_name}__{control}"
    run_dir = OUT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    input_path = run_dir / "input.csv"
    frame.to_csv(input_path, index=False, float_format="%.12g")
    (run_dir / "flux_map.json").write_text(
        json.dumps({"control_axis": control, "fluxes": flux_map}, indent=2,
                   ensure_ascii=False) + "\n", encoding="utf-8"
    )
    stdout_path = run_dir / "console.log"
    started = time.perf_counter()
    np.random.seed(SEED)
    random.seed(SEED)
    try:
        with stdout_path.open("w", encoding="utf-8", errors="replace") as log, \
             contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            output, features, fluxes, fluxes_ui = module.run_pipeline(
                data_source="custom",
                custom_file_path=str(input_path),
                mapping={"control_col": control, "flux_mapping": flux_map},
                mode="fast",
                opt_cfg={"random_seed": SEED, "max_workers": 1},
            )
        runtime = time.perf_counter() - started
        if isinstance(features, pd.DataFrame):
            features.to_csv(run_dir / "features.csv", index=False)
        with gzip.open(run_dir / "pipeline_output.json.gz", "wt", encoding="utf-8") as stream:
            json.dump(output, stream, ensure_ascii=False, default=json_default)
        meta = output.get("metadata", {})
        control_flag = output.get("monotone_flags", {}).get("__control__", {})
        return {
            "order": order_name, "control": control, "status": "success",
            "n_rows": int(len(frame)), "n_valid_control": valid_n,
            "minimum_required": MIN_VALID, "n_fluxes_requested": len(flux_map),
            "n_fluxes_returned": len(fluxes),
            "fluxes": list(flux_map), "control_excluded_from_fluxes": control not in flux_map,
            "control_monotonicity": control_flag,
            "T0_percent": meta.get("opt_threshold"),
            "threshold_source": meta.get("threshold_source"),
            "threshold_status": meta.get("threshold_status"),
            "mc_axis_status": (output.get("mc_axis") or {}).get("status"),
            "n_estimators_computed": len(output.get("estimators_computed", [])),
            "feature_rows": int(len(features)) if isinstance(features, pd.DataFrame) else None,
            "input_sha256": sha256(input_path),
            "output_sha256": sha256(run_dir / "pipeline_output.json.gz"),
            "runtime_seconds": round(runtime, 3),
            "run_dir": run_dir.relative_to(HERE).as_posix(),
        }
    except Exception as exc:  # preserve a failed control run; continue the grid
        runtime = time.perf_counter() - started
        error = {
            "order": order_name, "control": control, "status": "error",
            "n_rows": int(len(frame)), "n_valid_control": valid_n,
            "minimum_required": MIN_VALID, "n_fluxes_requested": len(flux_map),
            "error_type": type(exc).__name__, "error": str(exc),
            "traceback": traceback.format_exc(),
            "runtime_seconds": round(runtime, 3),
            "run_dir": run_dir.relative_to(HERE).as_posix(),
        }
        (run_dir / "error.json").write_text(
            json.dumps(error, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return error


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not SOURCE_CSV.is_file() or not PIPELINE.is_file():
        raise FileNotFoundError(f"Source or pipeline missing: {SOURCE_CSV} / {PIPELINE}")
    source = pd.read_csv(SOURCE_CSV)
    if len(source) != 57 or source["patient_id"].nunique() != 57:
        raise ValueError("Expected 57 unique patient rows; refusing a changed cohort silently")
    numeric_cols = source.select_dtypes(include=[np.number]).columns.tolist()
    controls = []
    skipped = []
    for col in numeric_cols:
        n_valid = int(pd.to_numeric(source[col], errors="coerce").notna().sum())
        n_unique = int(source[col].nunique(dropna=True))
        if n_valid < MIN_VALID:
            skipped.append({"control": col, "status": "abstain_minimum_n",
                            "n_valid": n_valid, "minimum_required": MIN_VALID,
                            "reason": "unchanged fast-mode input gate"})
        elif n_unique < 2:
            skipped.append({"control": col, "status": "abstain_constant_axis",
                            "n_valid": n_valid, "n_unique": n_unique,
                            "reason": "constant control has no axis variation"})
        else:
            controls.append(col)

    manifest = {
        "analysis_id": "UNIVERSAL_LOG_v6.0.1_PDACPATIENT_all_numeric_axes_fluxes_order_sensitivity",
        "status": "running",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unit_of_analysis": "one patient row; cross-sectional, not longitudinal",
        "source_csv": SOURCE_CSV.relative_to(PROJECT).as_posix(), "source_sha256": sha256(SOURCE_CSV),
        "source_shape": list(source.shape), "source_rows_unique_patient_ids": 57,
        "pipeline": PIPELINE.relative_to(PROJECT).as_posix(), "pipeline_sha256": sha256(PIPELINE),
        "python": sys.version, "python_executable": ".venv\\Scripts\\python.exe",
        "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "configuration": {
            "pipeline_mode": "fast", "statistical_test": "Cohen-d",
            "minimum_valid_control_points": MIN_VALID, "random_seed": SEED,
            "max_workers": 1, "full_triangulation": False,
            "control_axis_policy": "each eligible numeric source column gets one separate run",
            "flux_policy": "all other numeric source columns are mapped as separate fluxes",
            "selected_axis_is_flux": False,
            "nonmonotone_controls": "retained; monotonicity recorded as a diagnostic",
            "categorical_columns": "not numerically recoded; separate categorical companion analysis remains unchanged",
            "row_order_sensitivity": "source, reverse, and one fixed seeded permutation; no row is a time point",
            "interpretation_boundary": "descriptive analysis only; no temporal, causal, predictive, diagnostic, or treatment-efficacy claim",
        },
        "numeric_columns": numeric_cols, "eligible_controls": controls,
        "abstained_controls": skipped, "row_orders": list(ORDERS), "runs": [],
        "preflight_pilot": {
            "run_dir": "results/runs/pilot_source_order__dose_mg",
            "status": "success", "control": "dose_mg", "n_valid": 57,
            "n_fluxes": 15, "cohen_d_estimators": 29,
            "T0_percent": 20.454545454545457,
            "runtime_seconds": 55.412,
            "output_sha256": "3aeeff4783447bb35fa6b8ebf90e6f00749068458286a11e30bea7167ff8dfbe",
            "interpretation": "pipeline output on cross-sectional patient order; not a dose threshold or treatment effect",
        },
    }
    persist_manifest(manifest)
    patient_ids = source["patient_id"].astype(str).to_numpy()
    module = load_pipeline()
    for order_name in ORDERS:
        idx = order_indices(len(source), order_name)
        ordered = source.iloc[idx].reset_index(drop=True)
        row_map = pd.DataFrame({"row_order_1_based": np.arange(1, len(idx) + 1),
                                "source_row_1_based": idx + 1,
                                "patient_id": patient_ids[idx]})
        order_dir = OUT / "row_orders"
        order_dir.mkdir(exist_ok=True)
        row_map.to_csv(order_dir / f"{order_name}.csv", index=False)
        for control in numeric_cols:
            item = run_one(module, ordered, order_name, control)
            manifest["runs"].append(item)
            persist_manifest(manifest)
            print(f"{order_name}\t{control}\t{item['status']}\t"
                  f"T0={item.get('T0_percent')}\t"
                  f"n={item.get('n_valid_control')}\t"
                  f"seconds={item.get('runtime_seconds')}", flush=True)
    manifest["status"] = "complete"
    manifest["completed_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    persist_manifest(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
