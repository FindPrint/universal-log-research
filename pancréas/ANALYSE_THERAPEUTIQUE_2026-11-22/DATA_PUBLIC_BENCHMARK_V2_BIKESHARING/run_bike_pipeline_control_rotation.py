#!/usr/bin/env python
"""Resumable v6.0.1 rotation over every numeric Bike Sharing flow."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
CAMPAIGN = HERE / "pipeline_control_rotation_v1"
SOURCE = HERE / "source" / "hour.csv"
AGGREGATED = CAMPAIGN / "inputs" / "bike_hour_100_bins.csv"
PIPELINE = PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
PROTOCOL = HERE / "PROTOCOLE_BIKESHARING_V1_FR.md"
PLAN = CAMPAIGN / "campaign_plan.json"
STATE = CAMPAIGN / "run_state.json"
SUMMARY = CAMPAIGN / "control_rotation_summary.csv"
TARGET = "cnt"
N_BINS = 100
SCENARIOS = 8
SEED_BASE = 20261123


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def prepare() -> list[str]:
    frame = pd.read_csv(SOURCE)
    if len(frame) != 17379 or not frame["instant"].is_monotonic_increasing:
        raise ValueError("Unexpected Bike Sharing source rows or order.")
    numeric = frame.select_dtypes(include="number").columns.tolist()
    groups = np.array_split(np.arange(len(frame)), N_BINS)
    binned = pd.DataFrame([frame.iloc[index][numeric].mean(axis=0) for index in groups])
    AGGREGATED.parent.mkdir(parents=True, exist_ok=True)
    binned.to_csv(AGGREGATED, index=False, float_format="%.12g")
    return numeric


def load_pipeline(no_plots: bool):
    spec = importlib.util.spec_from_file_location("universal_log_v6_0_1_bike_rotation", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load pipeline source: {PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plot_functions = sorted(name for name, value in vars(module).items() if name.startswith("plot_") and callable(value))
    if no_plots:
        for name in plot_functions:
            setattr(module, name, lambda *args, **kwargs: None)
    return module, plot_functions


def extract_summary(result: dict, control: str, seed: int, elapsed: float) -> dict:
    metadata = result.get("metadata", {}) or {}
    core = result.get("run_pipeline", {}) or {}
    threshold = core.get("threshold_metadata", {}) or {}
    t0 = (metadata.get("thresholds_in_control_units", {}) or {}).get("T_0_Monte_Carlo_Central", {}) or {}
    global_stats = metadata.get("global_flux_stats", {}) or {}
    mono = metadata.get("control_monotonicity", {}) or {}
    if not isinstance(mono, dict):
        mono = {}
    estimator_classes = metadata.get("estimator_classes", {}) or {}
    estimator_names = sorted({name for group in estimator_classes.values() for name in (group or [])})
    return {
        "status": "complete", "control": control, "seed": seed,
        "target_requested": metadata.get("target_requested"), "target_used": metadata.get("target_used"),
        "target_fallback_used": metadata.get("target_fallback_used"),
        "target_fallback_reason": metadata.get("target_fallback_reason"),
        "diagonal_control_requested": control == TARGET,
        "n_samples": metadata.get("n_samples"), "control_monotone": mono.get("monotone"),
        "control_direction": mono.get("direction"), "t0_status": threshold.get("threshold_status"),
        "t0_pct": t0.get("threshold_pct"), "t0_raw_control_value": t0.get("control_value_raw"),
        "t0_raw_control_ambiguous": t0.get("ambiguous"),
        "analysis_flux_count": len(global_stats), "control_excluded_from_analysis_fluxes": control not in global_stats,
        "estimator_count": len(estimator_names), "estimator_names": estimator_names,
        "pipeline_elapsed_seconds": elapsed, "pipeline_version": result.get("version"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--with-plots", action="store_true")
    parser.add_argument("--max-runs", type=int)
    args = parser.parse_args()
    numeric = prepare()
    if TARGET not in numeric:
        raise ValueError(f"Missing target: {TARGET}")
    input_sha = sha256(AGGREGATED)
    dataset = json.loads((HERE / "dataset_manifest.json").read_text(encoding="utf-8"))
    plan = {
        "title": "UCI Bike Sharing: all numeric controls V1", "status": "plan_frozen_before_pipeline_calls",
        "created_utc": datetime.now(timezone.utc).isoformat(), "source_csv_sha256": dataset["extracted_files"]["hour.csv"]["sha256"],
        "input_csv_sha256": input_sha, "input_csv": "inputs/bike_hour_100_bins.csv", "target": TARGET,
        "numeric_controls_all": numeric, "source_rows": 17379, "bin_count": N_BINS,
        "aggregation": "mean of all numeric columns over 100 consecutive, near-equal blocks in original hour/instant order",
        "linked_target_fluxes": {"casual": "component of cnt", "registered": "component of cnt"},
        "planned_runs": [{"run_key": f"control_{i+1:02d}_{name.replace(' ', '_').replace('/', '_')}", "control": name, "seed": SEED_BASE + i * 100, "diagonal_control_requested": name == TARGET} for i, name in enumerate(numeric)],
        "planned_run_count": len(numeric), "pipeline_source_sha256": sha256(PIPELINE), "protocol_sha256": sha256(PROTOCOL),
        "configuration": {"target_policy": "fixed", "mode": "fast", "n_scenarios": SCENARIOS, "max_workers": 1, "harmonic_validation": False, "l7b_mode": "light", "plots": not args.with_plots,
                           "plot_suppression_method": "runtime monkeypatch of render functions only" if not args.with_plots else "none"},
        "claim_limits": ["Behavioral pipeline study, not a forecast benchmark, causality test, operational guarantee, or universality proof."],
    }
    if PLAN.exists():
        old = json.loads(PLAN.read_text(encoding="utf-8"))
        for key in ("source_csv_sha256", "input_csv_sha256", "numeric_controls_all", "planned_runs", "pipeline_source_sha256", "protocol_sha256", "configuration"):
            if old.get(key) != plan.get(key):
                raise RuntimeError(f"Frozen plan mismatch at {key}; refusing overwrite.")
        plan["created_utc"] = old.get("created_utc", plan["created_utc"])
    else:
        write_json(PLAN, plan)
    if args.prepare_only:
        print(json.dumps({"status": "prepared", "numeric_controls": numeric, "input_sha256": input_sha, "runs": len(numeric)}, indent=2, ensure_ascii=False))
        return
    if args.max_runs is not None and args.max_runs < 1:
        raise ValueError("--max-runs must be positive")
    module, plot_functions = load_pipeline(no_plots=not args.with_plots)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {"runs": {}}
    state.setdefault("runs", {})
    for item in plan["planned_runs"][:args.max_runs]:
        key, control, seed = item["run_key"], item["control"], item["seed"]
        run_dir = CAMPAIGN / "runs" / key
        output_dir = run_dir / "pipeline_output"
        result_path, log_path = run_dir / "pipeline_result.json", run_dir / "pipeline.log"
        old = state["runs"].get(key, {})
        if old.get("status") == "complete" and old.get("input_sha256") == input_sha and result_path.is_file():
            continue
        run_dir.mkdir(parents=True, exist_ok=True)
        state["runs"][key] = {"status": "running", "control": control, "seed": seed, "input_sha256": input_sha, "pipeline_sha256": plan["pipeline_source_sha256"], "started_utc": datetime.now(timezone.utc).isoformat()}
        write_json(STATE, state)
        config = {"csv_path": str(AGGREGATED), "target_col": TARGET, "control_col": control, "control_mode": "single", "target_policy": "fixed", "domain": "generic", "mode": "fast", "n_scenarios": SCENARIOS, "seed": seed, "output_dir": str(output_dir), "max_workers": 1, "harmonic_validation": False, "l7b_mode": "light"}
        started = time.perf_counter()
        try:
            with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                result = module.run_full_unified_pipeline(**config)
            elapsed = time.perf_counter() - started
            summary = extract_summary(result, control, seed, elapsed)
            result_path.write_text(json.dumps({"summary": summary, "result": result, "configuration": {k: v for k, v in config.items() if k not in {"csv_path", "output_dir"}}}, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
            state["runs"][key] = {**state["runs"][key], "status": "complete", "finished_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": elapsed, "result_path": result_path.relative_to(CAMPAIGN).as_posix(), "log_path": log_path.relative_to(CAMPAIGN).as_posix(), "summary": summary}
            write_json(STATE, state)
            print(f"DONE {key} {elapsed:.1f}s target_used={summary['target_used']} T0={summary['t0_pct']}", flush=True)
        except BaseException as exc:
            elapsed = time.perf_counter() - started
            state["runs"][key] = {**state["runs"][key], "status": "error", "finished_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": elapsed, "error_type": type(exc).__name__, "error": str(exc), "log_path": log_path.relative_to(CAMPAIGN).as_posix()}
            write_json(STATE, state)
            print(f"ERROR {key} {type(exc).__name__}: {exc}", flush=True)
    rows = [state["runs"].get(item["run_key"], {"status": "pending", "control": item["control"]}) for item in plan["planned_runs"]]
    pd.DataFrame([row.get("summary", {k: v for k, v in row.items() if k != "summary"}) for row in rows]).to_csv(SUMMARY, index=False, float_format="%.10g")
    manifest = {"status": "complete" if all(row.get("status") == "complete" for row in rows) else "partial_or_errors", "created_utc": datetime.now(timezone.utc).isoformat(), "completed_count": sum(row.get("status") == "complete" for row in rows), "error_count": sum(row.get("status") == "error" for row in rows), "planned_count": len(rows), "input_sha256": input_sha, "pipeline_sha256": plan["pipeline_source_sha256"], "summary_csv_sha256": sha256(SUMMARY), "plot_functions_skipped": plot_functions if not args.with_plots else [], "environment": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__}}
    write_json(CAMPAIGN / "campaign_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
