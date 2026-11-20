"""Benchmark the existing Cliff-vs-Cohen scan paths on archived Ising inputs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CLIFF_SOURCE = ROOT / "audit_release" / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
COHEN_SOURCE = ROOT / "UNIVERSAL_LOG_v5.9.2.py"
INPUT_200 = ROOT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test" / "pipeline_inputs" / "L16_T2.269185_chain0.csv"
INPUT_80 = ROOT / "audit_release" / "2026-11-14_l7b_full_reduced" / "data" / "L16_T2.269185_chain0_first80.csv"
OUT = Path(__file__).resolve().parent / "cliff_vs_cohen_scan_benchmark.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def load_pipeline(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load archived v5.9.1 pipeline")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    cliff_pipeline = load_pipeline(CLIFF_SOURCE, "universal_log_v591_cliff_bench")
    cohen_pipeline = load_pipeline(COHEN_SOURCE, "universal_log_v592_cohen_bench")
    rows = []
    for label, csv_path in (("archived_80_row_slice", INPUT_80), ("archived_200_rows", INPUT_200)):
        if not csv_path.is_file():
            raise FileNotFoundError(csv_path)
        df = pd.read_csv(csv_path)
        flux_names = ["Abs_magnetization", "Energy_per_spin", "M_squared"]
        fluxes = {name: df[name].to_numpy(dtype=float) for name in flux_names if name in df.columns}
        control = df["MC_Update"].to_numpy(dtype=float)
        axis_cfg = dict(cohen_pipeline.PARAMETERS["modes"]["fast"], random_seed=20261108)
        progress_result = cohen_pipeline._build_mc_progress_axis(control, fluxes, axis_cfg)
        progress = np.asarray(progress_result["progress_pct"], dtype=float)

        for mode_name in ("robust", "full", "predict"):
            base_cfg = dict(cohen_pipeline.PARAMETERS["modes"][mode_name])
            w_size = min(int(base_cfg["w_size"]), max(2, len(progress) // 2))
            common = {
                "min_grp": int(base_cfg["min_grp"]),
                "w_size": w_size,
                "random_seed": 20261108,
                "harmonic_prob": float(cohen_pipeline.HARMONIC_PROB),
            }
            observed = {}
            for stat_test in ("cohen_d", "cliff_delta"):
                cfg = {**base_cfg, **common, "test": stat_test}
                metric_pipeline = cohen_pipeline if stat_test == "cohen_d" else cliff_pipeline
                # One warm-up is excluded from timing.
                first = metric_pipeline.scan_critical_threshold(
                    fluxes, progress, cfg, n_candidates=31, w_size=w_size, min_grp=common["min_grp"]
                )
                times = []
                final_threshold, final_curve = first
                for _ in range(5):
                    t0 = time.perf_counter()
                    final_threshold, final_curve = metric_pipeline.scan_critical_threshold(
                        fluxes, progress, cfg, n_candidates=31, w_size=w_size, min_grp=common["min_grp"]
                    )
                    times.append(time.perf_counter() - t0)
                observed[stat_test] = {
                    "threshold": float(final_threshold) if np.isfinite(final_threshold) else None,
                    "median_seconds_5_runs": statistics.median(times),
                    "all_seconds": times,
                    "score_curve": [item.get("score") for item in final_curve],
                    "score_curve_length": len(final_curve),
                }
            cohen_curve = np.asarray([np.nan if x is None else x for x in observed["cohen_d"]["score_curve"]], dtype=float)
            cliff_curve = np.asarray([np.nan if x is None else x for x in observed["cliff_delta"]["score_curve"]], dtype=float)
            valid = np.isfinite(cohen_curve) & np.isfinite(cliff_curve)
            rho = float(spearmanr(cohen_curve[valid], cliff_curve[valid]).statistic) if np.sum(valid) >= 3 else None
            cohen_threshold = observed["cohen_d"]["threshold"]
            cliff_threshold = observed["cliff_delta"]["threshold"]
            rows.append({
                "input": label,
                "input_path": str(csv_path.relative_to(ROOT)),
                "input_sha256": sha256(csv_path),
                "n_rows": len(df),
                "control": "MC_Update",
                "fluxes": list(fluxes),
                "mode_parameters_from_v5_9_1": mode_name,
                "n_candidates": 31,
                "window_size": w_size,
                "min_group_count": common["min_grp"],
                "cohen_threshold": cohen_threshold,
                "cliff_threshold": cliff_threshold,
                "threshold_equal": cohen_threshold == cliff_threshold,
                "spearman_score_curve_correlation": rho,
                "cohen_median_seconds": observed["cohen_d"]["median_seconds_5_runs"],
                "cliff_median_seconds": observed["cliff_delta"]["median_seconds_5_runs"],
                "cliff_over_cohen_speed_ratio": (
                    observed["cliff_delta"]["median_seconds_5_runs"]
                    / observed["cohen_d"]["median_seconds_5_runs"]
                    if observed["cohen_d"]["median_seconds_5_runs"] > 0 else None
                ),
                "cohen": observed["cohen_d"],
                "cliff": observed["cliff_delta"],
            })

    report = {
        "status": "completed",
        "purpose": "Compare current v5.9.1 Cohen-d fast scan and Cliff-delta legacy scan under identical archived Ising inputs and scan settings.",
        "cliff_source": CLIFF_SOURCE.name,
        "cliff_source_sha256": sha256(CLIFF_SOURCE),
        "cohen_source": COHEN_SOURCE.name,
        "cohen_source_sha256": sha256(COHEN_SOURCE),
        "cohen_definition": "degrees-of-freedom weighted pooled standard deviation, as implemented in the candidate version",
        "python": sys.version,
        "repeats_per_case": 5,
        "warmup_per_metric": 1,
        "results": rows,
        "limitations": [
            "This is a software performance/output comparison on archived Ising inputs at one control and selected fluxes.",
            "The scans are not a physical validation of Tc or universality.",
            "Cohen d and Cliff delta measure different effect-size quantities; identical raw values or selected thresholds are not guaranteed.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
