#!/usr/bin/env python
"""Prepare and run every source/diagnostic control on UCI Air Quality."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import platform
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
CAMPAIGN = HERE / "pipeline_control_rotation_v1"
SOURCE = HERE / "source" / "AirQualityUCI.csv"
INPUT = CAMPAIGN / "inputs" / "air_quality_100_time_bins.csv"
PIPELINE = PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
PROTOCOL = HERE / "PROTOCOLE_AIR_QUALITY_INSTRUMENTATION_V1_FR.md"
AUDIT = HERE / "source_quality_audit_v1.json"
PLAN = CAMPAIGN / "campaign_plan.json"
STATE = CAMPAIGN / "run_state.json"
SUMMARY = CAMPAIGN / "control_rotation_summary.csv"
TARGET = "CO(GT)"
N_BINS = 100
SCENARIOS = 8
SEED_BASE = 20261124
MIN_CONTROL_POINTS = 50
SENTINEL = -200


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    temp.replace(path)


def prepare() -> tuple[list[str], dict[str, int], dict[str, int]]:
    frame = pd.read_csv(SOURCE, sep=";", decimal=",", encoding="latin-1")
    frame = frame.loc[:, [c for c in frame.columns if not str(c).startswith("Unnamed:") and frame[c].notna().any()]]
    frame = frame.loc[~frame.isna().all(axis=1)].reset_index(drop=True)
    timestamp = pd.to_datetime(
        frame["Date"].astype(str).str.strip() + " " + frame["Time"].astype(str).str.strip(),
        format="%d/%m/%Y %H.%M.%S",
        errors="raise",
    )
    timestamp_ns = timestamp.astype("datetime64[ns]").astype("int64")
    first_timestamp_ns = int(timestamp_ns.iloc[0])
    numeric_names = [name for name in frame.columns if name not in {"Date", "Time"}]
    numeric = frame[numeric_names].apply(pd.to_numeric, errors="raise").replace(SENTINEL, np.nan)
    groups = np.array_split(np.arange(len(frame)), N_BINS)
    binned_rows = []
    for positions in groups:
        row = numeric.iloc[positions].mean(axis=0, skipna=True).to_dict()
        times = timestamp_ns.iloc[positions].to_numpy(dtype=np.int64)
        row["time_index_hours"] = float(((times - first_timestamp_ns) / 3_600_000_000_000).mean())
        raw_block = frame.iloc[positions][numeric_names].apply(pd.to_numeric, errors="coerce")
        row["missing_fraction_numeric"] = float(raw_block.eq(SENTINEL).sum().sum() / raw_block.size)
        binned_rows.append(row)
    binned = pd.DataFrame(binned_rows)
    controls = numeric_names + ["time_index_hours", "missing_fraction_numeric"]
    if TARGET not in controls:
        raise ValueError(f"Missing requested target/control: {TARGET}")
    INPUT.parent.mkdir(parents=True, exist_ok=True)
    binned.to_csv(INPUT, index=False, na_rep="", float_format="%.12g")
    control_counts = {col: int(binned[col].notna().sum()) for col in controls}
    missing_pct = {col: float(binned[col].isna().mean()) for col in numeric_names}
    return controls, control_counts, missing_pct


def load_pipeline(no_plots: bool):
    spec = importlib.util.spec_from_file_location("universal_log_v6_0_1_air_quality", PIPELINE)
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
    threshold = (core.get("threshold_metadata", {}) or {})
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
        "n_samples": metadata.get("n_samples"), "control_valid_bins": int(metadata.get("n_samples", 0) or 0),
        "control_monotone": mono.get("monotone"), "control_direction": mono.get("direction"),
        "t0_status": threshold.get("threshold_status"), "t0_pct": t0.get("threshold_pct"),
        "t0_raw_control_value": t0.get("control_value_raw"), "t0_raw_control_ambiguous": t0.get("ambiguous"),
        "analysis_flux_count": len(global_stats), "control_excluded_from_analysis_fluxes": control not in global_stats,
        "analysis_flux_missing_rates": {
            k: (1.0 - float(v["n_valid"]) / float(v["n_total"])) if isinstance(v, dict) and v.get("n_total") else None
            for k, v in global_stats.items()
        },
        "estimator_count": len(estimator_names), "estimator_names": estimator_names,
        "pipeline_elapsed_seconds": elapsed, "pipeline_version": result.get("version"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--with-plots", action="store_true")
    parser.add_argument("--max-runs", type=int)
    args = parser.parse_args()
    controls, control_counts, missing_pct = prepare()
    source_audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    input_sha = sha256(INPUT)
    plan = {
        "title": "UCI Air Quality: measurement/analysis flow controls V1",
        "status": "plan_frozen_before_pipeline_calls",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": source_audit["source_csv_sha256"],
        "input_csv_sha256": input_sha,
        "input_csv": "inputs/air_quality_100_time_bins.csv",
        "input_rows": N_BINS,
        "source_nonempty_rows": source_audit["nonempty_dated_source_records"],
        "target_requested": TARGET,
        "numeric_controls_all": controls,
        "per_control_valid_bins": control_counts,
        "source_flow_missing_rates_after_binning": missing_pct,
        "derived_controls": {
            "time_index_hours": "mean elapsed hour in each consecutive source block; ordering variable derived from Date/Time",
            "missing_fraction_numeric": "fraction of source numeric cells coded -200 within each block; process-of-measurement diagnostic, not a source sensor channel",
        },
        "sentinel_policy": "Convert documented -200 missing sentinel to NaN before block means; no imputation. Empty flow bins remain blank/NaN.",
        "aggregation": "100 consecutive, near-equal groups in original, timestamp-verified row order; per-column means ignore NaN; no rows are reordered.",
        "planned_runs": [
            {
                "run_key": f"control_{i+1:02d}_{name.replace(' ', '_').replace('/', '_')}",
                "control": name,
                "seed": SEED_BASE + i * 100,
                "valid_bins_before_call": control_counts[name],
                "expected_minimum_valid_control_points": MIN_CONTROL_POINTS,
                "diagonal_control_requested": name == TARGET,
            }
            for i, name in enumerate(controls)
        ],
        "planned_run_count": len(controls),
        "pipeline_source_sha256": sha256(PIPELINE),
        "protocol_sha256": sha256(PROTOCOL),
        "configuration": {
            "target_policy": "fixed",
            "mode": "fast",
            "n_scenarios": SCENARIOS,
            "max_workers": 1,
            "harmonic_validation": False,
            "l7b_mode": "light",
            "plots": bool(args.with_plots),
            "plot_suppression_method": "runtime monkeypatch of rendering functions only" if not args.with_plots else "none",
            "minimum_control_points_from_v6_mode": MIN_CONTROL_POINTS,
        },
        "claim_limits": [
            "Results describe software outputs; they are not causal or predictive conclusions about pollution.",
            "Different controls may have different valid-bin counts; do not compare them as identical support.",
            "The NMHC(GT) full-span control is expected to be rejected as too short if it has fewer than 50 valid bins; this is a support limitation, not a successful threshold estimate.",
            "Control equal to requested target is reported separately if v6.0.1 substitutes the target.",
            "Raw dataset is retained locally pending resolution of the UCI research-only/noncommercial wording versus its displayed CC BY 4.0 license.",
        ],
    }
    if PLAN.exists():
        old = json.loads(PLAN.read_text(encoding="utf-8"))
        frozen = ("source_sha256", "input_csv_sha256", "numeric_controls_all", "planned_runs", "pipeline_source_sha256", "protocol_sha256", "configuration")
        for key in frozen:
            if old.get(key) != plan.get(key):
                raise RuntimeError(f"Frozen plan mismatch at {key}; refusing overwrite.")
        plan["created_utc"] = old.get("created_utc", plan["created_utc"])
    else:
        write_json(PLAN, plan)
    if args.prepare_only:
        print(json.dumps({"status": "prepared", "controls": controls, "valid_bins": control_counts, "input_sha256": input_sha, "runs": len(controls)}, indent=2, ensure_ascii=False))
        return
    if args.max_runs is not None and args.max_runs < 1:
        raise ValueError("--max-runs must be positive")
    module, plot_functions = load_pipeline(no_plots=not args.with_plots)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {"runs": {}}
    state.setdefault("runs", {})
    for item in plan["planned_runs"][:args.max_runs]:
        key, control, seed = item["run_key"], item["control"], item["seed"]
        result_dir = CAMPAIGN / "runs" / key
        output_dir = result_dir / "pipeline_output"
        result_path, log_path = result_dir / "pipeline_result.json", result_dir / "pipeline.log"
        old = state["runs"].get(key, {})
        if old.get("status") in {"complete", "blocked_insufficient_support"} and old.get("input_sha256") == input_sha:
            continue
        result_dir.mkdir(parents=True, exist_ok=True)
        state["runs"][key] = {
            "status": "running", "control": control, "seed": seed, "input_sha256": input_sha,
            "pipeline_sha256": plan["pipeline_source_sha256"], "started_utc": datetime.now(timezone.utc).isoformat(),
        }
        write_json(STATE, state)
        config = {
            "csv_path": str(INPUT), "target_col": TARGET, "control_col": control,
            "control_mode": "single", "target_policy": "fixed", "domain": "generic", "mode": "fast",
            "n_scenarios": SCENARIOS, "seed": seed, "output_dir": str(output_dir),
            "max_workers": 1, "harmonic_validation": False, "l7b_mode": "light",
        }
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
        except ValueError as exc:
            elapsed = time.perf_counter() - started
            blocked = "Série trop courte" in str(exc)
            state["runs"][key] = {
                **state["runs"][key],
                "status": "blocked_insufficient_support" if blocked else "error",
                "finished_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": elapsed,
                "valid_bins_before_call": item["valid_bins_before_call"],
                "error_type": type(exc).__name__, "error": str(exc),
                "log_path": log_path.relative_to(CAMPAIGN).as_posix(),
            }
            result_path.write_text(json.dumps(state["runs"][key], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            write_json(STATE, state)
            label = "BLOCKED" if blocked else "ERROR"
            print(f"{label} {key} {elapsed:.1f}s: {exc}", flush=True)
        except BaseException as exc:
            elapsed = time.perf_counter() - started
            state["runs"][key] = {**state["runs"][key], "status": "error", "finished_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": elapsed, "error_type": type(exc).__name__, "error": str(exc), "log_path": log_path.relative_to(CAMPAIGN).as_posix()}
            write_json(STATE, state)
            print(f"ERROR {key} {type(exc).__name__}: {exc}", flush=True)
    rows = [state["runs"].get(item["run_key"], {"status": "pending", "control": item["control"]}) for item in plan["planned_runs"]]
    pd.DataFrame([{**row, **row.get("summary", {})} for row in rows]).to_csv(SUMMARY, index=False, float_format="%.10g")
    statuses = [row.get("status") for row in rows]
    manifest = {
        "status": "complete" if all(s in {"complete", "blocked_insufficient_support"} for s in statuses) else "partial_or_errors",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "completed_count": sum(s == "complete" for s in statuses),
        "blocked_insufficient_support_count": sum(s == "blocked_insufficient_support" for s in statuses),
        "error_count": sum(s == "error" for s in statuses), "planned_count": len(rows),
        "input_sha256": input_sha, "pipeline_sha256": plan["pipeline_source_sha256"],
        "runner_script_sha256": sha256(Path(__file__).resolve()),
        "summary_csv_sha256": sha256(SUMMARY),
        "plot_functions_skipped": plot_functions if not args.with_plots else [],
        "environment": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__},
    }
    write_json(CAMPAIGN / "campaign_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
