#!/usr/bin/env python
"""Synthetic integration test for patient-grouped UNIVERSAL_LOG execution.

This harness does not change the archived pipeline. It creates a fully
synthetic longitudinal panel, splits it by patient, rotates every numeric
measurement as control, and calls the frozen v6.0.1 full entry point once per
patient/control pair. Outputs are exploratory software checks, not biology.
"""
from __future__ import annotations

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
INPUT_DIR = HERE / "inputs"
RUNS_DIR = HERE / "runs"
PANEL_PATH = INPUT_DIR / "synthetic_longitudinal_panel_v1.csv"
STATE_PATH = HERE / "run_state.json"
SUMMARY_PATH = HERE / "patient_control_summary.csv"
QA_PATH = HERE / "validation_results.json"
MANIFEST_PATH = HERE / "run_manifest.json"

SEED = 20261122
SHORT_SEED = 20261123
N_PATIENTS = 3
N_VISITS = 64
SHORT_VISITS = 32
MIN_POINTS = 50  # observed default fast-mode entry gate, recorded from v6.0.1
GROUP_COLUMN = "patient_key"
ORDER_COLUMN = "week_from_start"
FIXED_TARGET = "signal_primary"
MODE = "fast"
N_SCENARIOS = 8
CONTROLS = [
    "week_from_start",
    "signal_primary",
    "marker_correlated",
    "marker_oscillatory",
    "noise_independent",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v6_0_1_panel_test", PIPELINE_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load pipeline source: {PIPELINE_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_panel(n_visits: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frames = []
    t = np.arange(n_visits, dtype=float)
    for index in range(N_PATIENTS):
        patient = f"SYN-P{index + 1:02d}"
        shift = (-1.5, 0.0, 1.25)[index]
        phase = (0.0, 0.8, 1.6)[index]
        transition = 1.0 / (1.0 + np.exp(-(t - (n_visits * 0.58 + shift)) / max(2.0, n_visits * 0.045)))
        primary = transition + rng.normal(0.0, 0.045, n_visits)
        correlated = 0.78 * transition + 0.22 * (t / max(1, n_visits - 1)) + rng.normal(0.0, 0.055, n_visits)
        oscillatory = np.sin(2.0 * np.pi * t / 15.0 + phase) + 0.16 * transition + rng.normal(0.0, 0.07, n_visits)
        independent = rng.normal(0.0, 1.0, n_visits)
        frames.append(pd.DataFrame({
            GROUP_COLUMN: patient,
            "sample_key": [f"{patient}-V{j + 1:03d}" for j in range(n_visits)],
            ORDER_COLUMN: t,
            "signal_primary": primary,
            "marker_correlated": correlated,
            "marker_oscillatory": oscillatory,
            "noise_independent": independent,
            "synthetic_class": "generated_signal" if index != 2 else "generated_variant",
        }))
    return pd.concat(frames, ignore_index=True)


def normalize_panel(frame: pd.DataFrame) -> pd.DataFrame:
    required = {GROUP_COLUMN, "sample_key", ORDER_COLUMN, *CONTROLS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing panel columns: {missing}")
    if frame[GROUP_COLUMN].isna().any() or frame["sample_key"].isna().any():
        raise ValueError("Group and sample identifiers must be present.")
    if frame["sample_key"].duplicated().any():
        raise ValueError("Synthetic sample identifiers must be unique.")
    return frame.sort_values([GROUP_COLUMN, ORDER_COLUMN, "sample_key"], kind="stable").reset_index(drop=True)


def run_cases(frame: pd.DataFrame, engine, minimum: int, output_root: Path | None = None) -> list[dict]:
    """Split first, then admit/abstain per patient; never pool rows to pass N."""
    normalized = normalize_panel(frame)
    results = []
    for patient, group in normalized.groupby(GROUP_COLUMN, sort=True, observed=True):
        group = group.sort_values([ORDER_COLUMN, "sample_key"], kind="stable").reset_index(drop=True)
        n_valid_by_control = {
            control: int(pd.to_numeric(group[control], errors="coerce").notna().sum())
            for control in CONTROLS
        }
        for control in CONTROLS:
            n_valid = n_valid_by_control[control]
            record = {
                "patient_key": str(patient), "control": control,
                "n_rows_in_patient": int(len(group)), "n_valid_control": n_valid,
                "minimum_points": int(minimum), "status": None,
            }
            if n_valid < minimum:
                record["status"] = "abstained_short_series"
                results.append(record)
                continue
            out_dir = (output_root / str(patient) / control) if output_root else None
            payload = engine(group.copy(), control, str(patient), out_dir)
            record.update(payload)
            results.append(record)
    return results


def brief_result(result: dict, control: str) -> dict:
    metadata = result.get("metadata", {}) or {}
    core = result.get("run_pipeline", {}) or {}
    threshold_meta = core.get("threshold_metadata", {}) or {}
    stats = metadata.get("global_flux_stats", {}) or {}
    classes = metadata.get("estimator_classes", {}) or {}
    estimator_names = sorted({name for names in classes.values() for name in names})
    cascade = result.get("five_threshold_cascade", {}) or {}
    tension = result.get("holographic_tension_state", {}) or {}
    geometric = tension.get("geometric_layer", {}) or {}
    scores = core.get("scores", {}) or {}
    q_groups = sorted(str(key) for key in scores.keys())
    mono = metadata.get("control_monotonicity", {}) or {}
    return {
        "pipeline_version": result.get("version"),
        "n_samples_reported": metadata.get("n_samples"),
        "control_reported": metadata.get("control"),
        "target_requested": metadata.get("target_requested"),
        "target_used": metadata.get("target_used"),
        "target_fallback_used": metadata.get("target_fallback_used"),
        "control_monotone": mono.get("monotone"),
        "control_non_monotone": mono.get("is_non_monotone"),
        "analysis_flux_names": sorted(stats.keys()),
        "analysis_flux_count": len(stats),
        "control_present_as_analyzed_flux": control in stats,
        "n_estimator_names_in_class_map": len(estimator_names),
        "estimator_names_in_class_map": estimator_names,
        "q_score_groups": q_groups,
        "mc_axis_status": (metadata.get("mc_axis") or {}).get("status"),
        "threshold_status": (metadata.get("mc_axis") or {}).get("threshold_status"),
        "t0_pct": cascade.get("T_0_Monte_Carlo_Central"),
        "cascade_status": cascade.get("status"),
        "tlog_class_median": geometric.get("T_log_class_median", {}),
        "tlog_formula_metadata": geometric.get("T_log_formula"),
        "control_flux_exclusions": threshold_meta.get("control_flux_exclusions", []),
        "pipeline_success": bool(core.get("scores") is not None),
    }


def make_engine(pipeline, state: dict, logs_dir: Path):
    def execute(group: pd.DataFrame, control: str, patient: str, out_dir: Path | None) -> dict:
        assert group[GROUP_COLUMN].nunique() == 1
        assert str(group[GROUP_COLUMN].iloc[0]) == patient
        assert group[ORDER_COLUMN].is_monotonic_increasing
        if out_dir is None:
            raise ValueError("Actual engine requires a per-patient/per-control output directory.")
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = INPUT_DIR / f"{patient}.csv"
        if not csv_path.exists():
            group.to_csv(csv_path, index=False, float_format="%.12g", encoding="utf-8")
        run_id = f"{patient}__{control}"
        previous = state["runs"].get(run_id, {})
        if previous.get("status") == "complete" and previous.get("input_sha256") == sha256(csv_path):
            saved_json = out_dir / "panel_run_result.json"
            if saved_json.exists():
                saved = json.loads(saved_json.read_text(encoding="utf-8"))
                return {"status": "complete", "result_path": str(saved_json.resolve()), **saved.get("brief", {})}
        seed_offset = CONTROLS.index(control) * 100
        seed = SEED + (int(patient[-2:]) * 1000) + seed_offset
        log_path = logs_dir / f"{run_id}.log"
        started = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        state["runs"][run_id] = {
            "status": "running", "patient_key": patient, "control": control,
            "input_sha256": sha256(csv_path), "pipeline_sha256": sha256(PIPELINE_SOURCE),
            "started_utc": started, "seed": seed,
            "requested": {"mode": MODE, "target": FIXED_TARGET, "control_mode": "single",
                          "max_workers": 1, "n_scenarios": N_SCENARIOS,
                          "harmonic_validation": False, "l7b_mode": "light"},
            "output_dir": str(out_dir.resolve()), "log_path": str(log_path.resolve()),
        }
        STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                result = pipeline.run_full_unified_pipeline(
                    csv_path=str(csv_path), target_col=FIXED_TARGET, control_col=control,
                    control_mode="single", target_policy="fixed", domain="generic",
                    mode=MODE, n_scenarios=N_SCENARIOS, seed=seed,
                    output_dir=str(out_dir), max_workers=1,
                    harmonic_validation=False, l7b_mode="light",
                )
            brief = brief_result(result, control)
            payload = {"brief": brief, "result": result}
            result_path = out_dir / "panel_run_result.json"
            result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
            elapsed = time.perf_counter() - t0
            state["runs"][run_id] = {
                **state["runs"][run_id], "status": "complete", "finished_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": elapsed, "result_path": str(result_path.resolve()),
                "brief": brief,
            }
            print(f"DONE {run_id} | {elapsed:.1f}s | T0={brief['t0_pct']}", flush=True)
            return {"status": "complete", "elapsed_seconds": elapsed, "result_path": str(result_path.resolve()), **brief}
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            state["runs"][run_id] = {
                **state["runs"][run_id], "status": "error",
                "finished_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": elapsed,
                "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc(),
            }
            print(f"ERROR {run_id}: {type(exc).__name__}: {exc}", flush=True)
            return {"status": "error", "error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": elapsed}
        finally:
            STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return execute


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (HERE / "logs").mkdir(parents=True, exist_ok=True)
    if not PIPELINE_SOURCE.exists():
        raise FileNotFoundError(PIPELINE_SOURCE)

    panel = make_panel(N_VISITS, SEED)
    normalized = normalize_panel(panel)
    normalized.to_csv(PANEL_PATH, index=False, float_format="%.12g", encoding="utf-8")
    numeric_controls = normalized.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_controls != CONTROLS:
        raise AssertionError(f"Numeric control rotation mismatch: {numeric_controls} != {CONTROLS}")

    shuffled = normalized.sample(frac=1.0, random_state=SHORT_SEED).reset_index(drop=True)
    shuffle_invariant = normalize_panel(shuffled).equals(normalized)

    # Exercise the short-series rule with a fake engine. Three 32-row patients
    # pool to 96 rows (> 50), but each patient remains below the frozen gate.
    short_panel = make_panel(SHORT_VISITS, SHORT_SEED)
    fake_calls: list[str] = []
    short_records = run_cases(
        short_panel,
        engine=lambda g, c, p, o: fake_calls.append(f"{p}:{c}") or {"status": "unexpected_engine_call"},
        minimum=MIN_POINTS,
    )
    short_test = {
        "pooled_rows": int(len(short_panel)),
        "pooled_rows_meet_minimum": bool(len(short_panel) >= MIN_POINTS),
        "per_patient_rows": sorted(short_panel.groupby(GROUP_COLUMN).size().astype(int).tolist()),
        "per_patient_below_minimum": bool((short_panel.groupby(GROUP_COLUMN).size() < MIN_POINTS).all()),
        "case_count": len(short_records),
        "abstention_count": sum(r["status"] == "abstained_short_series" for r in short_records),
        "engine_call_count": len(fake_calls),
        "passed": len(short_panel) >= MIN_POINTS and all(len(g) < MIN_POINTS for _, g in short_panel.groupby(GROUP_COLUMN))
                  and not fake_calls and all(r["status"] == "abstained_short_series" for r in short_records),
    }

    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"runs": {}}
    state.setdefault("runs", {})
    pipeline = load_pipeline()
    actual = run_cases(panel, make_engine(pipeline, state, HERE / "logs"), MIN_POINTS, RUNS_DIR)
    summaries = []
    for record in actual:
        if record.get("status") == "complete":
            summaries.append({k: v for k, v in record.items() if k != "result_path"})
        elif record.get("status") != "error":
            summaries.append(record)
    pd.DataFrame(summaries).to_csv(SUMMARY_PATH, index=False, encoding="utf-8")

    complete = [row for row in actual if row.get("status") == "complete"]
    errors = [row for row in actual if row.get("status") == "error"]
    per_group_counts = {str(k): int(v) for k, v in normalized.groupby(GROUP_COLUMN).size().items()}
    expected_cases = N_PATIENTS * len(CONTROLS)
    exclusion_check = all(not row.get("control_present_as_analyzed_flux", True) for row in complete)
    control_coverage = sorted({row["control"] for row in complete})
    group_coverage = sorted({row["patient_key"] for row in complete})
    target_diagonal_rows = [row for row in complete if row["control"] == FIXED_TARGET]
    estimator_coverage = all(row.get("n_estimator_names_in_class_map") == 29 for row in complete)
    diagonal_explicit = all(row.get("target_fallback_used") is True for row in target_diagonal_rows)
    nonmonotone_rows = [row for row in complete if row["control"] == "marker_oscillatory"]
    nonmonotone_retained = len(nonmonotone_rows) == N_PATIENTS and all(
        row.get("control_reported") == "marker_oscillatory" for row in nonmonotone_rows
    )
    tests = {
        "panel_split_precedes_minimum_gate": short_test,
        "global_row_shuffle_normalizes_to_same_patient_time_order": {"passed": shuffle_invariant},
        "all_synthetic_numeric_columns_rotated_as_controls": {
            "expected_controls": CONTROLS, "observed_controls": control_coverage,
            "expected_patient_groups": N_PATIENTS, "observed_patient_groups": group_coverage,
            "expected_case_count": expected_cases, "completed_case_count": len(complete),
            "error_case_count": len(errors),
            "passed": control_coverage == sorted(CONTROLS) and len(group_coverage) == N_PATIENTS
                      and len(complete) == expected_cases and not errors,
        },
        "selected_control_excluded_from_analyzed_fluxes": {
            "checked_runs": len(complete), "passed": exclusion_check,
        },
        "all_29_estimator_names_remain_declared": {
            "checked_runs": len(complete), "counts": sorted({row.get("n_estimator_names_in_class_map") for row in complete}),
            "passed": estimator_coverage,
        },
        "fixed_target_diagonal_is_explicit": {
            "diagonal_runs": len(target_diagonal_rows), "passed": diagonal_explicit,
        },
        "nonmonotone_control_is_not_dropped": {
            "runs": len(nonmonotone_rows),
            "reported_monotonicity": [row.get("control_non_monotone") for row in nonmonotone_rows],
            "passed": nonmonotone_retained,
        },
    }
    required = [
        short_test["passed"], shuffle_invariant,
        tests["all_synthetic_numeric_columns_rotated_as_controls"]["passed"],
        exclusion_check, estimator_coverage, diagonal_explicit, nonmonotone_retained,
    ]
    result = {
        "title": "Synthetic grouped-panel integration validation",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Synthetic software/integration tests only; no clinical or biological data.",
        "pipeline_source": str(PIPELINE_SOURCE.resolve()),
        "pipeline_sha256": sha256(PIPELINE_SOURCE),
        "pipeline_version": getattr(pipeline, "VERSION_MASTER", None),
        "harness_sha256": sha256(Path(__file__).resolve()),
        "panel_sha256": sha256(PANEL_PATH),
        "configuration": {
            "seed": SEED, "n_patients": N_PATIENTS, "visits_per_patient": N_VISITS,
            "short_series_visits_per_patient": SHORT_VISITS,
            "minimum_per_patient": MIN_POINTS, "mode": MODE,
            "n_scenarios": N_SCENARIOS, "controls": CONTROLS,
            "fixed_numeric_target": FIXED_TARGET,
            "target_diagonal_policy": "v6.0.1 explicit fallback retained and flagged; diagonal result not comparable to other fixed-target controls",
            "group_summary": "Per-patient/per-control results only; no pooled visits and no patient-bootstrap inference in V1.",
        },
        "panel_structure": {"rows": int(len(normalized)), "patients": per_group_counts,
                            "numeric_columns_all_rotated": numeric_controls,
                            "categorical_metadata": [GROUP_COLUMN, "sample_key", "synthetic_class"]},
        "tests": tests,
        "completed_runs": len(complete),
        "failed_runs": [{"patient_key": row.get("patient_key"), "control": row.get("control"), "error": row.get("error")} for row in errors],
        "status": "passed" if all(required) else "incomplete_or_failed",
        "interpretation_boundary": "A pass supports only the tested group-splitting/dispatch and v6.0.1 execution behavior on generated data. It does not validate threshold accuracy, clinical utility, TLog theory, or PDAC biology.",
        "next_limitations": [
            "The frozen pipeline gate is per run/measurement length, not a minimum number of independent patients.",
            "No inferential confidence interval across patients is produced; implement only after group-level behavior is separately specified.",
            "The synthetic target is one numeric measurement and its diagonal control run is explicitly non-comparable.",
            "No clinical CSV or patient data were loaded.",
        ],
    }
    QA_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    state["validation_status"] = result["status"]
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    environment = {
        "generated_utc": result["generated_utc"],
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__,
        "pipeline_path": str(PIPELINE_SOURCE.resolve()),
        "pipeline_sha256": sha256(PIPELINE_SOURCE),
        "harness_path": str(Path(__file__).resolve()),
        "harness_sha256": sha256(Path(__file__).resolve()),
        "input_path": str(PANEL_PATH.resolve()), "input_sha256": sha256(PANEL_PATH),
        "results_path": str(QA_PATH.resolve()), "summary_path": str(SUMMARY_PATH.resolve()),
    }
    MANIFEST_PATH.write_text(json.dumps(environment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "completed_runs": len(complete),
                      "failed_runs": len(errors), "tests": tests,
                      "summary": str(SUMMARY_PATH), "qa": str(QA_PATH)}, indent=2, ensure_ascii=False), flush=True)
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
