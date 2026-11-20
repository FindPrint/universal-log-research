#!/usr/bin/env python
"""Deterministic synthetic pilot for UNIVERSAL_LOG v6; pipeline source is read-only."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import math
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
PIPELINE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
INPUT = HERE / "input"
PRIVATE = HERE / "truth_private"
RUNS = HERE / "runs"
SPEC_PATH = HERE / "pilot_spec.json"
TRUTH_PATH = PRIVATE / "truth.json"
STATE_PATH = HERE / "run_state.json"
SUMMARY_JSON = HERE / "pilot_summary.json"
SUMMARY_CSV = HERE / "pilot_summary.csv"
PIPELINE_SEEDS = {
    "case_01": 730101,
    "case_02": 730101,
    "case_03": 730103,
    "case_04": 730104,
    "case_05": 730105,
    "case_06": 730106,
    "case_07": 730107,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    x = np.empty(n, dtype=float)
    x[0] = rng.normal(0.0, sigma / math.sqrt(max(1e-9, 1 - phi * phi)))
    for i in range(1, n):
        x[i] = phi * x[i - 1] + rng.normal(0.0, sigma)
    return x


def abrupt(n: int, seed: int, rich: bool) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(seed)
    i = np.arange(n)
    change = n // 2
    target = (i >= change).astype(float) + rng.normal(0, 0.10, n)
    data = {"control_index": i, "target": target}
    if rich:
        data["flow_correlated"] = 0.8 * target + rng.normal(0, 0.15, n)
        data["flow_affine_copy"] = 2.0 * target + 3.0
        data["flow_independent"] = rng.normal(0, 1, n)
    frame = pd.DataFrame(data)
    truth = {
        "family": "abrupt_step",
        "event_present": True,
        "event_definition": "first row at or after which the generated target has a level shift",
        "change_index_zero_based": change,
        "boundary_control_midpoint": change - 0.5,
        "boundary_rank_fraction": (change - 0.5) / max(1, n - 1),
        "data_seed": seed,
        "flow_relations": ("correlated proxy", "exact affine copy", "independent noise") if rich else (),
    }
    return frame, truth


def build_cases() -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
    frames: dict[str, pd.DataFrame] = {}
    truth: dict[str, dict] = {}
    base, base_truth = abrupt(76, 202611151, rich=True)
    frames["case_01"] = base
    truth["case_01"] = {**base_truth, "description": "abrupt event with related, affine-copy, and independent flows"}
    # Paired ablation uses the identical target and axis bytes, only target is supplied.
    frames["case_02"] = base[["control_index", "target"]].copy()
    truth["case_02"] = {**base_truth, "description": "paired same event and target; additional flows removed"}

    rng = np.random.default_rng(202611153)
    target = ar1(rng, 76, phi=0.55, sigma=0.45)
    frames["case_03"] = pd.DataFrame({
        "control_index": np.arange(76), "target": target,
        "flow_correlated": 0.75 * target + rng.normal(0, 0.25, 76),
        "flow_independent": ar1(rng, 76, phi=0.30, sigma=0.45),
    })
    truth["case_03"] = {
        "family": "stationary_ar1_null", "event_present": False,
        "event_definition": "none; stationary AR(1) target with fixed phi=0.55 and fixed innovation scale",
        "target_phi": 0.55, "target_innovation_sigma": 0.45, "data_seed": 202611153,
    }

    rng = np.random.default_rng(202611154)
    drift = np.linspace(0, 1, 76) + rng.normal(0, 0.10, 76)
    frames["case_04"] = pd.DataFrame({
        "control_index": np.arange(76), "target": drift,
        "flow_correlated": 0.80 * drift + rng.normal(0, 0.15, 76),
        "flow_independent": rng.normal(0, 1, 76),
    })
    truth["case_04"] = {
        "family": "smooth_drift_null", "event_present": False,
        "event_definition": "no discrete transition; linear trend plus stationary measurement noise",
        "data_seed": 202611154,
    }

    for case_id, n, seed in (("case_05", 7, 202611157), ("case_06", 15, 202611158), ("case_07", 30, 202611159)):
        frame, labels = abrupt(n, seed, rich=True)
        frames[case_id] = frame
        truth[case_id] = {**labels, "description": f"short-series stress case N={n}"}
    return frames, truth


def prepare() -> None:
    INPUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    frames, truth = build_cases()
    cases = []
    for case_id, frame in frames.items():
        path = INPUT / f"{case_id}.csv"
        if path.exists():
            raise FileExistsError(f"Refusing to replace frozen pilot input: {path}")
        frame.to_csv(path, index=False, float_format="%.12g", encoding="utf-8")
        cases.append({
            "case_id": case_id,
            "input_file": f"input/{case_id}.csv",
            "input_sha256": sha256(path),
            "n_rows": int(len(frame)),
            "pipeline_seed": PIPELINE_SEEDS[case_id],
            "target_column": "target",
            "control_column": "control_index",
            "mode": "fast",
            "l7b_mode": "light",
            "domain": "generic",
            "control_mode": "single",
        })
    write_json(TRUTH_PATH, {
        "title": "Separate synthetic ground truth; not passed to the pipeline",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cases": truth,
    })
    write_json(SPEC_PATH, {
        "protocol": "synthetic_pilot_v1",
        "status": "frozen_pre_execution_pilot",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_path": str(PIPELINE.resolve()),
        "pipeline_sha256": sha256(PIPELINE),
        "pipeline_version_expected": "v6.0.0-L7aL7b-CohenD",
        "runner_path": str(Path(__file__).resolve()),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "python": sys.version,
        "cases": cases,
        "predeclared_readouts": [
            "run completion or recorded error and elapsed time",
            "T0 rank-percent; for abrupt cases, absolute normalized distance to the known boundary midpoint",
            "exact location error = abs(T0_rank_pct / 100 - boundary_rank_fraction); no pass/fail cutoff is imposed in this pilot",
            "for no-event cases, report T0 availability only; do not label a selected T0 a false positive",
            "per-estimator Tous status for the 29 configured estimators",
            "Q1-Q6 finite-value counts; F1/F2 cascade outputs; Voie 1/2 fields; TLog components; L7a/L7b statuses",
            "paired case_01 versus case_02 output differences are descriptive and isolate added-flow configuration only",
        ],
        "limitations_predeclared": [
            "one deterministic draw per case; no inferential confidence intervals",
            "this is a development pilot, not a confirmatory benchmark",
            "no-event cases cannot yield false-positive rates without a separately frozen alert/abstention rule",
            "no result from synthetic inputs validates a biological, clinical, or universal claim",
        ],
    })
    print(f"Prepared {len(cases)} CSV cases; truth is separate; pipeline SHA-256={sha256(PIPELINE)}")


def load_pipeline():
    spec = importlib.util.spec_from_file_location("pilot_universal_log_v6", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load pipeline source: {PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sanitize(value):
    if isinstance(value, dict):
        return {str(k): sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def finite_count(obj) -> tuple[int, int]:
    if isinstance(obj, dict):
        vals = [v for v in obj.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        return sum(math.isfinite(float(v)) for v in vals), len(vals)
    return 0, 0


def summarize(case: dict, result: dict, elapsed: float) -> dict:
    master = result
    cascade = master.get("five_threshold_cascade", {}) or {}
    predictions = master.get("prediction_levels", {}) or {}
    l7a = predictions.get("L7a_coherence", {}) or {}
    l7b = predictions.get("L7b_robustesse", {}) or {}
    pipeline_run = master.get("run_pipeline", {}) or {}
    transition = pipeline_run.get("transition_analysis", {}) or {}
    estimator_status = {}
    for name, detail in transition.items():
        if isinstance(detail, dict):
            row = detail.get("Tous", {}) or {}
            estimator_status[name] = row.get("status", "status_absent")
    scores = pipeline_run.get("scores", {}) or {}
    q_counts = {q: {"finite": finite_count(scores.get(q, {}))[0], "numeric": finite_count(scores.get(q, {}))[1]}
                for q in ("Q1_Calme_vs_Chaos", "Q2_Tension_Seuil", "Q3_Agressivite", "Q4_Persistence",
                          "Q5_Actif_Receptif", "Q6_Actif_Receptif_Echelle")}
    holo = master.get("holographic_tension_state", {}) or master.get("holographic_tension", {}) or {}
    geo = holo.get("geometric_layer", {}) or {}
    tension = holo.get("tension_gap_diagnostics", {}) or {}
    t0 = cascade.get("T_0_Monte_Carlo_Central")
    n = int(case["n_rows"])
    event_boundary = case.get("boundary_rank_fraction")
    error = abs(float(t0) / 100.0 - float(event_boundary)) if t0 is not None and event_boundary is not None else None
    status_counts: dict[str, int] = {}
    for status in estimator_status.values():
        status_counts[status] = status_counts.get(status, 0) + 1
    return sanitize({
        "case_id": case["case_id"],
        "n_rows": n,
        "status": "complete",
        "elapsed_seconds": elapsed,
        "pipeline_version": master.get("version"),
        "target_used": (master.get("metadata", {}) or {}).get("target_used"),
        "t0_rank_pct": t0,
        "t0_raw_control_units": ((cascade.get("thresholds_in_control_units", {}) or {}).get("T_0_Monte_Carlo_Central")),
        "known_boundary_rank_fraction": event_boundary,
        "absolute_normalized_t0_error": error,
        "estimator_count": len(estimator_status),
        "estimator_status_counts": status_counts,
        "estimator_statuses": estimator_status,
        "q_finite_counts": q_counts,
        "f1_f2": {k: cascade.get(k) for k in ("T_-1_F1_pre_inflection", "T_0_Monte_Carlo_Central", "T_+1_F1_post_deceleration", "max_F1_velocity", "max_F2_curvature", "status")},
        "l7a": {"status": l7a.get("status"), "direction": l7a.get("consensus_direction")},
        "l7b": {"status": l7b.get("status"), "verdict": l7b.get("verdict"), "checks": l7b.get("checks")},
        "tlog": {"class_median": geo.get("T_log_class_median"), "formula": geo.get("T_log_formula"), "scope": geo.get("T_log_scope")},
        "voie1": {"higuchi": tension.get("voie1_higuchi"), "blind_risk": tension.get("voie1_blind_risk")},
        "voie2": {"triangulation": tension.get("triangulation"), "proof_status": tension.get("proof_status")},
        "input_sha256": case["input_sha256"],
        "output_dir": str((RUNS / case["case_id"]).resolve()),
    })


def run() -> None:
    if not SPEC_PATH.exists():
        raise FileNotFoundError("Run `prepare` first to freeze inputs and protocol.")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if sha256(PIPELINE) != spec["pipeline_sha256"]:
        raise RuntimeError("Pipeline source hash changed since pilot freeze; create a new pilot version.")
    pipeline = load_pipeline()
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"cases": {}}
    state.setdefault("cases", {})
    for case in spec["cases"]:
        case_id = case["case_id"]
        previous = state["cases"].get(case_id, {})
        if previous.get("status") == "complete":
            print(f"SKIP {case_id}: already complete", flush=True)
            continue
        csv_path = HERE / case["input_file"]
        if sha256(csv_path) != case["input_sha256"]:
            raise RuntimeError(f"Frozen input hash mismatch: {case_id}")
        output_dir = RUNS / case_id
        log_path = RUNS / f"{case_id}.log"
        if output_dir.exists():
            raise FileExistsError(f"Output already exists for incomplete case {case_id}; preserve it and start a new pilot version.")
        RUNS.mkdir(parents=True, exist_ok=True)
        started = datetime.now(timezone.utc).isoformat()
        print(f"START {case_id} | N={case['n_rows']} | mode=fast | seed={case['pipeline_seed']}", flush=True)
        state["cases"][case_id] = {
            "status": "running", "started_utc": started, "input_sha256": case["input_sha256"],
            "pipeline_seed": case["pipeline_seed"], "output_dir": str(output_dir.resolve()),
        }
        write_json(STATE_PATH, state)
        start = time.perf_counter()
        try:
            kwargs = {
                "csv_path": str(csv_path),
                "target_col": case["target_column"],
                "control_col": case["control_column"],
                "control_mode": case["control_mode"],
                "target_policy": "fixed",
                "domain": case["domain"],
                "mode": case["mode"],
                "seed": int(case["pipeline_seed"]),
                "output_dir": str(output_dir),
                "max_workers": 1,
                "triangulation_estimators": "default",
                "l7b_mode": case["l7b_mode"],
            }
            with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                returned = pipeline.run_full_unified_pipeline(**kwargs)
            elapsed = time.perf_counter() - start
            master_path = output_dir / "master_results.json"
            master = json.loads(master_path.read_text(encoding="utf-8")) if master_path.exists() else returned
            row = summarize(case, master, elapsed)
            row["log_path"] = str(log_path.resolve())
            row["status"] = "complete"
            state["cases"][case_id] = {**row, "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat()}
            print(f"DONE {case_id} | {elapsed:.1f}s | T0={row.get('t0_rank_pct')}", flush=True)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            state["cases"][case_id] = {
                "case_id": case_id, "n_rows": case["n_rows"], "status": "error",
                "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": elapsed, "input_sha256": case["input_sha256"],
                "output_dir": str(output_dir.resolve()), "log_path": str(log_path.resolve()),
                "error": repr(exc), "traceback": traceback.format_exc(),
            }
            print(f"ERROR {case_id} | {exc}", flush=True)
        write_json(STATE_PATH, state)
        rows = [v for v in state["cases"].values()]
        write_json(SUMMARY_JSON, {"protocol": spec["protocol"], "case_results": rows})
        pd.DataFrame([{k: json.dumps(sanitize(v), ensure_ascii=False) if isinstance(v, (dict, list)) else v
                       for k, v in row.items() if k != "traceback"} for row in rows]).to_csv(SUMMARY_CSV, index=False, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "run"}:
        raise SystemExit("Usage: python run_synthetic_pilot.py prepare|run")
    prepare() if sys.argv[1] == "prepare" else run()
