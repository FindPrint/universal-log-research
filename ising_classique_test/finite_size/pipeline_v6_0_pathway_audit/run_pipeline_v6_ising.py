#!/usr/bin/env python
"""Reproducible complete-pipeline v6 Ising pathway audit.

Uses the frozen protocol beside this file. All execution is through the
archived UNIVERSAL_LOG v6.0 Cohen-d implementation; no pipeline source is
modified. Runs are resumable: a run with status=complete is skipped unless
--force is supplied.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
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
FINITE = PROJECT / "ising_classique_test" / "finite_size"
SOURCE_CSV = FINITE / "finite_size_results.csv"
PEAK_CSV = FINITE / "finite_size_peaks.csv"
PIPELINE_SOURCE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
PROTOCOL = HERE / "PROTOCOL_PIPELINE_COMPLET_V6.md"
DATA_DIR = HERE / "inputs"
RUNS_DIR = HERE / "runs"
STATE_PATH = HERE / "run_state.json"
SUMMARY_PATH = HERE / "pipeline_v6_ising_summary.csv"
MANIFEST_PATH = HERE / "pipeline_v6_ising_manifest.json"
RUN_SEED = 20261115
NOISE_SEED = 20261116
TARGET = "Energy_per_spin"
PHYSICAL_COLUMNS = [
    "Temperature", "Energy_per_spin", "abs_magnetization",
    "chi_abs_per_spin", "Cv_per_spin", "Binder_U4",
]
MULTI_CONTROLS = [
    "Temperature", "abs_magnetization", "chi_abs_per_spin",
    "Cv_per_spin", "Binder_U4",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v6_cohen_audit", PIPELINE_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load pipeline source: {PIPELINE_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_inputs(force: bool = False) -> dict[str, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(SOURCE_CSV)
    required = {"L", "T", "E_per_spin", "abs_magnetization", "chi_abs_per_spin", "Cv_per_spin", "Binder_U4"}
    missing = sorted(required - set(source.columns))
    if missing:
        raise ValueError(f"Ising source lacks columns: {missing}")
    prepared: dict[str, Path] = {}

    def write_variant(name: str, frame: pd.DataFrame) -> Path:
        path = DATA_DIR / f"{name}.csv"
        if path.exists() and not force:
            prepared[name] = path
            return path
        frame.to_csv(path, index=False, float_format="%.12g", encoding="utf-8")
        prepared[name] = path
        return path

    per_l = {}
    for l_size, group in source.groupby("L", sort=True):
        group = group.sort_values("T", kind="stable")
        frame = group[["T", "E_per_spin", "abs_magnetization", "chi_abs_per_spin", "Cv_per_spin", "Binder_U4"]].copy()
        frame.columns = PHYSICAL_COLUMNS
        name = f"ising_L{int(l_size)}_physical"
        per_l[int(l_size)] = write_variant(name, frame)

    l16 = source[source["L"].eq(16)].sort_values("T", kind="stable")
    base = l16[["T", "E_per_spin", "abs_magnetization", "chi_abs_per_spin", "Cv_per_spin", "Binder_U4"]].copy()
    base.columns = PHYSICAL_COLUMNS
    write_variant("ising_L16_physical", base)

    rng = np.random.default_rng(NOISE_SEED)
    noisy = base.copy()
    noisy["Noise_independent"] = rng.normal(0.0, 1.0, size=len(noisy))
    write_variant("ising_L16_plus_independent_noise", noisy)

    redundant = base.copy()
    redundant["Energy_redundant"] = 2.0 * redundant["Energy_per_spin"] + 3.0
    write_variant("ising_L16_plus_affine_duplicate_energy", redundant)

    reversed_rows = base.iloc[::-1].reset_index(drop=True)
    write_variant("ising_L16_reversed_row_order", reversed_rows)
    return prepared


def control_payload(result: dict) -> list[dict]:
    if isinstance(result.get("controls_summary"), list):
        return result["controls_summary"]
    meta = result.get("metadata", {}) or {}
    cascade = result.get("five_threshold_cascade", {}) or {}
    prediction = result.get("prediction_levels", {}) or {}
    l7 = prediction.get("L7_consensus") or prediction.get("L7a_coherence") or {}
    l7b = prediction.get("L7b_robustesse") or {}
    holo = result.get("holographic_tension") or result.get("holographic_tension_state") or {}
    geometric = holo.get("geometric_layer") or {}
    return [{
        "control": result.get("control_col") or meta.get("control_col"),
        "status": "ok",
        "target": meta.get("target"),
        "target_requested": meta.get("target_requested"),
        "target_used": meta.get("target_used"),
        "t0_pct": cascade.get("T_0_Monte_Carlo_Central"),
        "t0_control_value_raw": ((cascade.get("thresholds_in_control_units") or {}).get("T_0_Monte_Carlo_Central") or {}).get("control_value_raw"),
        "t_minus_2": cascade.get("T_-2_F2_pre_onset"),
        "t_minus_1": cascade.get("T_-1_F1_pre_inflection"),
        "t_plus_1": cascade.get("T_+1_F1_post_deceleration"),
        "t_plus_2": cascade.get("T_+2_F2_post_attractor"),
        "cascade_status": cascade.get("status"),
        "control_monotone": ((cascade.get("control_monotonicity") or {}).get("monotone")),
        "control_monotonicity_warning": ((cascade.get("control_monotonicity") or {}).get("warning_issued")),
        "consensus": l7.get("consensus_direction"),
        "l7b_verdict": l7b.get("verdict"),
        "dominant_regime_relative": holo.get("dominant_regime_relative"),
        "d_vector": holo.get("D_vector"),
        "voie1_higuchi": ((holo.get("tension_gap_diagnostics") or {}).get("voie1_higuchi")),
        "voie1_blind_risk": ((holo.get("tension_gap_diagnostics") or {}).get("voie1_blind_risk")),
        "triangulation": ((holo.get("tension_gap_diagnostics") or {}).get("triangulation")),
        # v6 stores class medians under geometric_layer; keep the full object
        # so that the summary never silently drops the TLog readout.
        "tlog_class_median": geometric.get("T_log_class_median"),
    }]


def run_specs() -> list[dict]:
    specs = []
    for l_size in (8, 12, 24, 32, 48, 64):
        specs.append({
            "run_id": f"primary_L{l_size}_temperature",
            "input": f"ising_L{l_size}_physical",
            "L": l_size,
            "variant": "physical_reference",
            "control_mode": "single",
            "control_col": "Temperature",
            "controls": None,
            "seed": RUN_SEED,
        })
    specs.append({
        "run_id": "sensitivity_L16_multiple_physical_controls",
        "input": "ising_L16_physical",
        "L": 16,
        "variant": "physical_reference",
        "control_mode": "multi",
        "control_col": None,
        "controls": MULTI_CONTROLS,
        "seed": RUN_SEED,
    })
    specs.extend([
        {"run_id": "sensitivity_L16_seed_42", "input": "ising_L16_physical", "L": 16,
         "variant": "physical_reference", "control_mode": "single", "control_col": "Temperature", "controls": None, "seed": 42},
        {"run_id": "sensitivity_L16_seed_123", "input": "ising_L16_physical", "L": 16,
         "variant": "physical_reference", "control_mode": "single", "control_col": "Temperature", "controls": None, "seed": 123},
        {"run_id": "negative_L16_reverse_row_order", "input": "ising_L16_reversed_row_order", "L": 16,
         "variant": "reversed_row_order", "control_mode": "single", "control_col": "Temperature", "controls": None, "seed": RUN_SEED},
        {"run_id": "negative_L16_independent_noise_flow", "input": "ising_L16_plus_independent_noise", "L": 16,
         "variant": "independent_noise_added", "control_mode": "single", "control_col": "Temperature", "controls": None, "seed": RUN_SEED},
        {"run_id": "sensitivity_L16_redundant_energy_flow", "input": "ising_L16_plus_affine_duplicate_energy", "L": 16,
         "variant": "affine_redundant_flow_added", "control_mode": "single", "control_col": "Temperature", "controls": None, "seed": RUN_SEED},
    ])
    return specs


def summarize_result(run_spec: dict, result: dict, output_path: Path, input_path: Path, elapsed: float, pipeline_version: str) -> dict:
    payload = control_payload(result)
    keys = ("t0_pct", "t0_control_value_raw", "t_minus_2", "t_minus_1", "t_plus_1", "t_plus_2",
            "cascade_status", "control_monotone", "control_monotonicity_warning", "consensus", "l7b_verdict",
            "dominant_regime_relative", "voie1_higuchi", "voie1_blind_risk", "tlog_class_median", "d_vector", "triangulation")
    first = payload[0] if len(payload) == 1 else None
    row = {
        **run_spec,
        "status": "complete",
        "pipeline_version": result.get("version") or pipeline_version,
        "input_path": str(input_path.resolve()),
        "input_sha256": sha256(input_path),
        "output_path": str(output_path.resolve()),
        "elapsed_seconds": elapsed,
        "controls_summary": payload,
    }
    if first:
        row.update({k: first.get(k) for k in keys})
    elif isinstance(result.get("controls"), dict):
        # Preserve the exact per-control rows; the concise CSV uses the JSON
        # and the resulting master_results folders as its lossless source.
        row["control_results"] = result.get("controls")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="rerun completed rows")
    parser.add_argument("--only", default=None, help="run one exact run_id")
    args = parser.parse_args()

    if not SOURCE_CSV.exists() or not PEAK_CSV.exists() or not PIPELINE_SOURCE.exists():
        raise FileNotFoundError("Required pipeline/Ising input files are missing")
    pipeline = load_pipeline()
    inputs = prepare_inputs(force=args.force)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"runs": {}}
    state.setdefault("runs", {})
    specs = run_specs()
    if args.only:
        specs = [spec for spec in specs if spec["run_id"] == args.only]
        if not specs:
            raise ValueError(f"Unknown run_id: {args.only}")

    for spec in specs:
        run_id = spec["run_id"]
        previous = state["runs"].get(run_id, {})
        if previous.get("status") == "complete" and not args.force:
            print(f"SKIP {run_id}: already complete", flush=True)
            continue
        input_path = inputs[spec["input"]]
        output_path = RUNS_DIR / run_id
        log_path = RUNS_DIR / f"{run_id}.log"
        started = datetime.now(timezone.utc).isoformat()
        print(f"START {run_id} | {spec['control_mode']} | L={spec['L']} | seed={spec['seed']}", flush=True)
        start = time.perf_counter()
        state["runs"][run_id] = {
            **spec, "status": "running", "started_utc": started,
            "input_sha256": sha256(input_path), "output_path": str(output_path.resolve()),
            "pipeline_version": getattr(pipeline, "VERSION_MASTER", None),
            "requested_settings": {
                "mode": "fast", "fast_mode_parameters": pipeline.PARAMETERS["modes"]["fast"],
                "target": TARGET, "target_policy": "fixed", "domain": "physics",
                "seed": int(spec["seed"]), "max_workers": 1,
                "triangulation": "default", "l7b": "light",
                "harmonic_validation_argument": None,
            },
        }
        STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            kwargs = {
                "csv_path": str(input_path),
                "target_col": TARGET,
                "control_col": spec["control_col"],
                "control_columns": spec["controls"],
                "control_mode": spec["control_mode"],
                "target_policy": "fixed",
                "domain": "physics",
                "mode": "fast",
                "seed": int(spec["seed"]),
                "output_dir": str(output_path),
                "max_workers": 1,
                "triangulation_estimators": "default",
                "l7b_mode": "light",
            }
            with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                result = pipeline.run_full_unified_pipeline(**kwargs)
            elapsed = time.perf_counter() - start
            row = summarize_result(spec, result, output_path, input_path, elapsed, getattr(pipeline, "VERSION_MASTER", None))
            row["status"] = "complete"
            row["started_utc"] = started
            row["finished_utc"] = datetime.now(timezone.utc).isoformat()
            row["log_path"] = str(log_path.resolve())
            state["runs"][run_id] = row
            print(f"DONE {run_id} | {elapsed:.1f}s", flush=True)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            state["runs"][run_id] = {
                **spec, "status": "error", "started_utc": started,
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": elapsed, "input_path": str(input_path.resolve()),
                "input_sha256": sha256(input_path), "output_path": str(output_path.resolve()),
                "log_path": str(log_path.resolve()), "error": repr(exc),
                "traceback": traceback.format_exc(),
            }
            print(f"ERROR {run_id}: {exc}", flush=True)
        STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        flat = []
        for item in state["runs"].values():
            summary = {k: v for k, v in item.items() if k not in ("controls_summary", "control_results", "traceback")}
            flat.append(summary)
        if flat:
            pd.DataFrame(flat).to_csv(SUMMARY_PATH, index=False, encoding="utf-8")

    environment = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script_path": str(Path(__file__).resolve()),
        "script_sha256": sha256(Path(__file__).resolve()),
        "protocol_path": str(PROTOCOL.resolve()),
        "protocol_sha256": sha256(PROTOCOL),
        "pipeline_path": str(PIPELINE_SOURCE.resolve()),
        "pipeline_sha256": sha256(PIPELINE_SOURCE),
        "source_csv_path": str(SOURCE_CSV.resolve()),
        "source_csv_sha256": sha256(SOURCE_CSV),
        "peaks_csv_path": str(PEAK_CSV.resolve()),
        "peaks_csv_sha256": sha256(PEAK_CSV),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "pipeline_version": getattr(pipeline, "VERSION_MASTER", None),
        "run_state_path": str(STATE_PATH.resolve()),
        "summary_path": str(SUMMARY_PATH.resolve()),
        "protocol_commit": "480f402",
        "primary_reference": {
            "Tc_exact": 2.269185314213022,
            "peak_table": str(PEAK_CSV.resolve()),
            "peak_table_sha256": sha256(PEAK_CSV),
        },
        "prepared_inputs": {name: {"path": str(path.resolve()), "sha256": sha256(path)} for name, path in inputs.items()},
    }
    MANIFEST_PATH.write_text(json.dumps(environment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"SUMMARY {SUMMARY_PATH}", flush=True)


if __name__ == "__main__":
    main()
