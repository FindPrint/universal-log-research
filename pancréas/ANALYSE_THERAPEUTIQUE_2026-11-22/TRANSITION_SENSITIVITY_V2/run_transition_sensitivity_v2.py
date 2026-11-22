#!/usr/bin/env python
"""Frozen, resumable synthetic sensitivity campaign for UNIVERSAL_LOG v6.0.1."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PIPELINE_SOURCE = (
    PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20"
    / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source"
    / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
)
PROTOCOL = HERE / "PROTOCOLE_SENSIBILITE_TRANSITIONS_V2_FR.md"
INPUT_DIR = HERE / "inputs"
RUNS_DIR = HERE / "runs"
LOGS_DIR = HERE / "logs"
STATE_PATH = HERE / "run_state.json"
SUMMARY_PATH = HERE / "patient_control_summary.csv"
QA_PATH = HERE / "validation_results.json"
PLAN_PATH = HERE / "campaign_plan.json"
MANIFEST_PATH = HERE / "run_manifest.json"
DESCRIPTIVE_PATH = HERE / "descriptive_summary.csv"
TIME_AXIS_PATH = HERE / "time_axis_localization_summary.csv"

ORDER_COLUMN = "time_index"
TARGET_COLUMN = "signal_primary"
CONTROLS = [
    "time_index",
    "signal_primary",
    "marker_correlated",
    "marker_oscillatory",
    "noise_independent",
]
MODE = "fast"
N_SCENARIOS = 8
MINIMUM_POINTS_OBSERVED = 50
AMPLITUDES = {"null": 0.0, "weak": 0.5, "strong": 1.5}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_dataset_plan() -> list[dict]:
    design = [
        (64, "null", 20261123), (64, "null", 20261124),
        (64, "weak", 20261123),
        (64, "strong", 20261123), (64, "strong", 20261124),
        (100, "null", 20261125), (100, "strong", 20261125),
    ]
    records = []
    for n, condition, seed in design:
        amplitude = AMPLITUDES[condition]
        case_key = f"N{n:03d}_{condition}_seed{seed}"
        records.append({
            "case_key": case_key,
            "n_points": n,
            "condition": condition,
            "signal_amplitude_noise_sd": amplitude,
            "input_seed": seed,
            "true_transition_pct": 58.0 if amplitude > 0 else None,
            "true_transition_index": (n - 1) * 0.58 if amplitude > 0 else None,
            "controls": CONTROLS,
        })
    return records


def make_panel(n: int, condition: str, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    amplitude = AMPLITUDES[condition]
    center = (n - 1) * 0.58
    width = max(2.0, n * 0.045)
    latent = 1.0 / (1.0 + np.exp(-(t - center) / width))
    signal_noise = rng.normal(0.0, 1.0, n)
    signal = amplitude * latent + signal_noise
    residual = rng.normal(0.0, 1.0, n)
    correlated = 0.8 * signal + 0.6 * residual
    phase = (seed % 13) * 0.19
    oscillatory = (
        0.8 * np.sin(2.0 * np.pi * t / 15.0 + phase)
        + 0.15 * amplitude * latent
        + rng.normal(0.0, 0.3, n)
    )
    independent_noise = rng.normal(0.0, 1.0, n)
    key = f"N{n:03d}_{condition}_seed{seed}"
    return pd.DataFrame({
        "case_id": key,
        "sample_key": [f"{key}-V{i + 1:03d}" for i in range(n)],
        "condition_label": f"signal_{condition}",
        "time_index": t,
        "signal_primary": signal,
        "marker_correlated": correlated,
        "marker_oscillatory": oscillatory,
        "noise_independent": independent_noise,
    })


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v6_0_1_sensitivity_v2", PIPELINE_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen pipeline source: {PIPELINE_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def brief_result(result: dict, control: str, dataset: dict) -> dict:
    metadata = result.get("metadata", {}) or {}
    core = result.get("run_pipeline", {}) or {}
    threshold = core.get("threshold_metadata", {}) or {}
    stats = metadata.get("global_flux_stats", {}) or {}
    classes = metadata.get("estimator_classes", {}) or {}
    estimator_names = sorted({name for names in classes.values() for name in names})
    cascade = result.get("five_threshold_cascade", {}) or {}
    tension = result.get("holographic_tension_state", {}) or {}
    geometric = tension.get("geometric_layer", {}) or {}
    scores_value = core.get("scores")
    scores = scores_value or {}
    mono = metadata.get("control_monotonicity", {}) or {}
    t0 = cascade.get("T_0_Monte_Carlo_Central")
    truth = dataset["true_transition_pct"] if control == ORDER_COLUMN else None
    t0_error = None
    try:
        if truth is not None and t0 is not None and np.isfinite(float(t0)):
            t0_error = abs(float(t0) - float(truth))
    except (TypeError, ValueError):
        pass
    return {
        "case_key": dataset["case_key"],
        "n_points": int(dataset["n_points"]),
        "condition": dataset["condition"],
        "signal_amplitude_noise_sd": float(dataset["signal_amplitude_noise_sd"]),
        "input_seed": int(dataset["input_seed"]),
        "control": control,
        "status": "complete",
        "pipeline_version": result.get("version"),
        "n_samples_reported": metadata.get("n_samples"),
        "control_reported": metadata.get("control"),
        "control_monotone": mono.get("monotone"),
        "control_non_monotone": mono.get("is_non_monotone"),
        "target_used": metadata.get("target_used"),
        "target_fallback_used": metadata.get("target_fallback_used"),
        "analysis_flux_names": sorted(stats),
        "analysis_flux_count": len(stats),
        "control_present_as_analyzed_flux": control in stats,
        "estimator_count": len(estimator_names),
        "estimator_names": estimator_names,
        "q_score_groups": sorted(str(name) for name in scores),
        "mc_axis_status": (metadata.get("mc_axis") or {}).get("status"),
        "threshold_status": (metadata.get("mc_axis") or {}).get("threshold_status"),
        "t0_pct": t0,
        "true_transition_pct": truth,
        "absolute_t0_error_pct_points": t0_error,
        "cascade_status": cascade.get("status"),
        "tlog_class_median": geometric.get("T_log_class_median", {}),
        "tlog_formula_metadata": geometric.get("T_log_formula"),
        "control_flux_exclusions": threshold.get("control_flux_exclusions", []),
        "f1_max": cascade.get("max_F1_velocity"),
        "f2_max": cascade.get("max_F2_curvature"),
        "pipeline_success": scores_value is not None,
    }


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def write_summary(rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(SUMMARY_PATH, index=False, encoding="utf-8")


def generate_inputs() -> tuple[list[dict], dict[str, Path]]:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    datasets = make_dataset_plan()
    paths = {}
    for record in datasets:
        frame_a = make_panel(record["n_points"], record["condition"], record["input_seed"])
        frame_b = make_panel(record["n_points"], record["condition"], record["input_seed"])
        if not frame_a.equals(frame_b):
            raise AssertionError(f"Generator is not deterministic for {record['case_key']}")
        numeric = frame_a.select_dtypes(include=[np.number]).columns.tolist()
        if numeric != CONTROLS:
            raise AssertionError(f"Numeric control set mismatch: {numeric} != {CONTROLS}")
        if len(frame_a) != record["n_points"] or frame_a["sample_key"].duplicated().any():
            raise AssertionError(f"Invalid synthetic input structure: {record['case_key']}")
        path = INPUT_DIR / f"{record['case_key']}.csv"
        frame_a.to_csv(path, index=False, float_format="%.12g", encoding="utf-8")
        roundtrip = pd.read_csv(path)
        roundtrip_numeric = roundtrip.select_dtypes(include=[np.number]).columns.tolist()
        if roundtrip_numeric != CONTROLS or roundtrip["condition_label"].isna().any():
            raise AssertionError(
                f"CSV type round-trip changed the control set for {record['case_key']}: {roundtrip_numeric}"
            )
        paths[record["case_key"]] = path
        record["input_sha256"] = sha256(path)
        record["numeric_control_columns"] = numeric
    return datasets, paths


def make_descriptive_tables(rows: list[dict]) -> None:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return
    grouped = []
    for (n, condition, control), group in frame.groupby(["n_points", "condition", "control"], dropna=False):
        values = pd.to_numeric(group["t0_pct"], errors="coerce").dropna()
        tlogs = {name: [] for name in ("saturation", "criticality", "divergence", "null_reference")}
        for item in group["tlog_class_median"]:
            if isinstance(item, dict):
                for name in tlogs:
                    value = item.get(name)
                    if value is not None:
                        try:
                            v = float(value)
                            if np.isfinite(v):
                                tlogs[name].append(v)
                        except (TypeError, ValueError):
                            pass
        row = {
            "n_points": int(n), "condition": condition, "control": control,
            "runs": int(len(group)), "t0_available_count": int(values.size),
            "t0_median_pct": float(values.median()) if values.size else None,
            "t0_min_pct": float(values.min()) if values.size else None,
            "t0_max_pct": float(values.max()) if values.size else None,
        }
        for name, vals in tlogs.items():
            row[f"tlog_{name}_median_over_runs"] = float(np.median(vals)) if vals else None
        grouped.append(row)
    pd.DataFrame(grouped).to_csv(DESCRIPTIVE_PATH, index=False, encoding="utf-8")
    time_rows = frame.loc[frame["control"] == ORDER_COLUMN].copy()
    time_summary = []
    for (n, condition), group in time_rows.groupby(["n_points", "condition"], dropna=False):
        errors = pd.to_numeric(group["absolute_t0_error_pct_points"], errors="coerce").dropna()
        t0_values = pd.to_numeric(group["t0_pct"], errors="coerce").dropna()
        time_summary.append({
            "n_points": int(n), "condition": condition, "runs": int(len(group)),
            "t0_available_count": int(t0_values.size),
            "t0_median_pct": float(t0_values.median()) if t0_values.size else None,
            "absolute_t0_error_median_pct_points": float(errors.median()) if errors.size else None,
            "absolute_t0_error_min_pct_points": float(errors.min()) if errors.size else None,
            "absolute_t0_error_max_pct_points": float(errors.max()) if errors.size else None,
            "error_is_defined": condition != "null",
        })
    pd.DataFrame(time_summary).to_csv(TIME_AXIS_PATH, index=False, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="write deterministic inputs and plan without calling the pipeline")
    args = parser.parse_args()
    if not PIPELINE_SOURCE.is_file() or not PROTOCOL.is_file():
        raise FileNotFoundError("Pipeline source or frozen V2 protocol is missing.")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    datasets, input_paths = generate_inputs()
    controls = list(CONTROLS)
    planned_runs = [
        {
            "run_key": f"{dataset['case_key']}__{control}",
            "case_key": dataset["case_key"], "control": control,
            "n_points": dataset["n_points"], "condition": dataset["condition"],
            "input_seed": dataset["input_seed"],
        }
        for dataset in datasets for control in controls
    ]
    plan = {
        "title": "Synthetic transition sensitivity V2",
        "created_utc": utc_now(),
        "status": "frozen_before_pipeline_runs",
        "scope": "Synthetic software/analysis behavior only; no clinical or biological data.",
        "pipeline_source_sha256": sha256(PIPELINE_SOURCE),
        "protocol_sha256": sha256(PROTOCOL),
        "harness_sha256": sha256(Path(__file__).resolve()),
        "planned_datasets": datasets,
        "planned_run_count": len(planned_runs),
        "controls": controls,
        "configuration": {
            "mode": MODE, "n_scenarios": N_SCENARIOS, "target": TARGET_COLUMN,
            "control_mode": "single", "max_workers": 1,
            "harmonic_validation": False, "l7b_mode": "light",
            "minimum_points_observed": MINIMUM_POINTS_OBSERVED,
        },
        "planned_runs": planned_runs,
    }
    write_json(PLAN_PATH, plan)
    if args.prepare_only:
        print(json.dumps({"status": "inputs_prepared", "datasets": len(datasets),
                          "planned_pipeline_runs": len(planned_runs),
                          "plan": str(PLAN_PATH), "protocol_sha256": plan["protocol_sha256"]},
                         indent=2, ensure_ascii=False), flush=True)
        return

    pipeline = load_pipeline()
    pipeline_hash = sha256(PIPELINE_SOURCE)
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"runs": {}}
    state.setdefault("runs", {})
    complete_rows = []
    dataset_by_key = {x["case_key"]: x for x in datasets}
    errors = []
    for planned in planned_runs:
        run_key, case_key, control = planned["run_key"], planned["case_key"], planned["control"]
        record = dataset_by_key[case_key]
        input_path = input_paths[case_key]
        input_hash = sha256(input_path)
        out_dir = RUNS_DIR / case_key / control
        saved_path = out_dir / "sensitivity_run_result.json"
        previous = state["runs"].get(run_key, {})
        if (previous.get("status") == "complete" and previous.get("input_sha256") == input_hash
                and previous.get("pipeline_sha256") == pipeline_hash and saved_path.is_file()):
            saved = json.loads(saved_path.read_text(encoding="utf-8"))
            complete_rows.append(saved["brief"])
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        control_seed = int(record["input_seed"] + 100 * controls.index(control))
        log_path = LOGS_DIR / f"{run_key}.log"
        state["runs"][run_key] = {
            "status": "running", "case_key": case_key, "control": control,
            "input_sha256": input_hash, "pipeline_sha256": pipeline_hash,
            "pipeline_seed": control_seed, "started_utc": utc_now(),
            "n_points": record["n_points"], "condition": record["condition"],
            "input_seed": record["input_seed"], "log_path": str(log_path.resolve()),
            "output_dir": str(out_dir.resolve()),
        }
        write_json(STATE_PATH, state)
        started = time.perf_counter()
        try:
            with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                result = pipeline.run_full_unified_pipeline(
                    csv_path=str(input_path), target_col=TARGET_COLUMN, control_col=control,
                    control_mode="single", target_policy="fixed", domain="generic",
                    mode=MODE, n_scenarios=N_SCENARIOS, seed=control_seed,
                    output_dir=str(out_dir), max_workers=1,
                    harmonic_validation=False, l7b_mode="light",
                )
            brief = brief_result(result, control, record)
            saved_path.write_text(json.dumps({"brief": brief, "result": result}, indent=2,
                                             ensure_ascii=False, default=str) + "\n", encoding="utf-8")
            elapsed = time.perf_counter() - started
            state["runs"][run_key] = {
                **state["runs"][run_key], "status": "complete", "finished_utc": utc_now(),
                "elapsed_seconds": elapsed, "result_path": str(saved_path.resolve()), "brief": brief,
            }
            complete_rows.append(brief)
            print(f"DONE {len(complete_rows)}/{len(planned_runs)} {run_key} | {elapsed:.1f}s | T0={brief['t0_pct']}", flush=True)
        except Exception as exc:
            elapsed = time.perf_counter() - started
            error = {"run_key": run_key, "error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": elapsed}
            errors.append(error)
            state["runs"][run_key] = {
                **state["runs"][run_key], "status": "error", "finished_utc": utc_now(),
                **error, "traceback": traceback.format_exc(),
            }
            print(f"ERROR {len(complete_rows) + len(errors)}/{len(planned_runs)} {run_key}: {error['error']}", flush=True)
        finally:
            write_json(STATE_PATH, state)
            write_summary(complete_rows)

    expected_keys = {r["run_key"] for r in planned_runs}
    actual_keys = {f"{row['case_key']}__{row['control']}" for row in complete_rows}
    by_dataset = {}
    for row in complete_rows:
        by_dataset.setdefault(row["case_key"], []).append(row)
    checks = {
        "seven_deterministic_input_datasets": len(datasets) == 7 and all(
            sha256(input_paths[d["case_key"]]) == d["input_sha256"] for d in datasets),
        "all_35_pipeline_runs_complete": actual_keys == expected_keys and not errors,
        "every_input_rotated_over_all_five_numeric_controls": all(
            sorted(row["control"] for row in rows) == sorted(CONTROLS)
            for rows in by_dataset.values()
        ) and len(by_dataset) == len(datasets),
        "selected_control_excluded_from_analyzed_fluxes": all(
            row.get("control_present_as_analyzed_flux") is False for row in complete_rows
        ),
        "all_runs_declare_29_estimators": len(complete_rows) == 35 and all(
            row.get("estimator_count") == 29 for row in complete_rows
        ),
        "diagonal_target_control_fallback_explicit": all(
            row.get("target_fallback_used") is True for row in complete_rows
            if row.get("control") == TARGET_COLUMN
        ) and sum(row.get("control") == TARGET_COLUMN for row in complete_rows) == 7,
        "oscillatory_control_retained_for_every_dataset": sum(
            row.get("control") == "marker_oscillatory" for row in complete_rows
        ) == 7,
        "each_pipeline_input_individually_meets_minimum": all(
            row.get("n_samples_reported") in (64, 100) for row in complete_rows
        ),
    }
    make_descriptive_tables(complete_rows)
    status = "passed" if all(checks.values()) else "incomplete_or_failed"
    qa = {
        "title": "Synthetic transition sensitivity V2",
        "generated_utc": utc_now(), "status": status,
        "scope": "Generated data only; output-behavior study, not clinical or biological validation.",
        "pipeline_version": getattr(pipeline, "VERSION_MASTER", None),
        "pipeline_sha256": pipeline_hash,
        "protocol_sha256": sha256(PROTOCOL),
        "harness_sha256": sha256(Path(__file__).resolve()),
        "plan_sha256": sha256(PLAN_PATH),
        "dataset_count": len(datasets), "planned_runs": len(planned_runs),
        "completed_runs": len(complete_rows), "errors": errors,
        "checks": checks,
        "n_runs_with_t0_available": sum(row.get("t0_pct") is not None for row in complete_rows),
        "null_condition_t0_availability": [
            {"case_key": row["case_key"], "control": row["control"],
             "t0_available": row.get("t0_pct") is not None,
             "threshold_status": row.get("threshold_status")}
            for row in complete_rows if row.get("condition") == "null"
        ],
        "interpretation_boundary": (
            "All results are descriptive outputs of the stated synthetic construction. "
            "T0 localization error is computed only on the time_index control for non-null conditions. "
            "No false-alarm rate is estimated because no decision/abstention rule was specified. "
            "No clinical, biological, causal, or universality claim is tested."
        ),
    }
    write_json(QA_PATH, qa)
    state["validation_status"] = status
    state["finished_utc"] = utc_now()
    write_json(STATE_PATH, state)
    environment = {
        "generated_utc": utc_now(), "python": sys.version,
        "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "pipeline_source": str(PIPELINE_SOURCE.resolve()), "pipeline_sha256": pipeline_hash,
        "protocol_sha256": sha256(PROTOCOL), "harness_sha256": sha256(Path(__file__).resolve()),
        "plan_sha256": sha256(PLAN_PATH),
        "inputs": {key: sha256(path) for key, path in sorted(input_paths.items())},
        "summary_path": str(SUMMARY_PATH.resolve()),
    }
    write_json(MANIFEST_PATH, environment)
    print(json.dumps({"status": status, "planned_runs": len(planned_runs),
                      "completed_runs": len(complete_rows), "errors": errors,
                      "checks": checks, "qa": str(QA_PATH),
                      "summary": str(SUMMARY_PATH)}, indent=2, ensure_ascii=False), flush=True)
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
