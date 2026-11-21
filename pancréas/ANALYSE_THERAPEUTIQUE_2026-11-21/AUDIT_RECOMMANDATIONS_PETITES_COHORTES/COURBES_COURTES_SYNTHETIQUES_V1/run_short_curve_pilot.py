#!/usr/bin/env python3
"""Descriptive synthetic pilot for short monotone dose-response curves.

This calls the unchanged v6.0.0 apply_complexity function directly with a
local min_len override. It does not run the pipeline orchestration, infer T0,
or calculate TLog. The override is only a diagnostic probe of estimator
finiteness on 7-10 observations, not a proposed production mode.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.machinery
import importlib.util
import json
import platform
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import OptimizeWarning, curve_fit

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
PIPELINE = PROJECT / "pancréas" / "universal_v6.0.0_cohen - Copie.py.txt"
OUT = HERE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261121
REPEATS = 50
LENGTHS = (7, 8, 9, 10)
DOSE_LOW_M = 1e-9
DOSE_HIGH_M = 1e-4

SCENARIOS = {
    "sigmoid_strong": {"top": 100.0, "bottom": 20.0, "hill": 1.5, "noise_sd": 3.0, "has_ic50": True},
    "sigmoid_weak": {"top": 100.0, "bottom": 70.0, "hill": 0.8, "noise_sd": 10.0, "has_ic50": True},
    "flat_no_effect": {"top": 100.0, "bottom": 100.0, "hill": 1.0, "noise_sd": 5.0, "has_ic50": False},
    "noise_no_trend": {"top": 50.0, "bottom": 50.0, "hill": 1.0, "noise_sd": 20.0, "has_ic50": False},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_pipeline():
    loader = importlib.machinery.SourceFileLoader("universal_log_shortcurve_pilot", str(PIPELINE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def hill4(log_dose: np.ndarray, bottom: float, top: float, log_ic50: float, slope: float) -> np.ndarray:
    # Downward, four-parameter logistic curve; dose is in log10(M).
    exponent = np.clip((log_dose - log_ic50) * slope, -100.0, 100.0)
    return bottom + (top - bottom) / (1.0 + 10.0 ** exponent)


def fit_hill4(log_dose: np.ndarray, response: np.ndarray) -> dict[str, object]:
    lo, hi = float(log_dose.min()), float(log_dose.max())
    y_min, y_max = float(response.min()), float(response.max())
    p0 = [min(y_min, 95.0), max(y_max, 100.0), float(np.median(log_dose)), 1.0]
    bounds = ([-100.0, -100.0, lo - 2.0, 0.1], [200.0, 200.0, hi + 2.0, 5.0])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", OptimizeWarning)
        try:
            params, covariance = curve_fit(
                hill4, log_dose, response, p0=p0, bounds=bounds,
                maxfev=20000, method="trf",
            )
            cov_finite = bool(np.all(np.isfinite(covariance)))
            return {
                "fit_status": "converged",
                "fit_bottom": float(params[0]),
                "fit_top": float(params[1]),
                "fit_log10_ic50_M": float(params[2]),
                "fit_hill_slope": float(params[3]),
                "fit_covariance_finite": cov_finite,
                "fit_ic50_inside_tested_range": bool(lo <= params[2] <= hi),
                "fit_warning_count": len(caught),
                "fit_rmse": float(np.sqrt(np.mean((hill4(log_dose, *params) - response) ** 2))),
            }
        except (RuntimeError, ValueError, FloatingPointError) as exc:
            return {
                "fit_status": f"failed:{type(exc).__name__}",
                "fit_bottom": None, "fit_top": None, "fit_log10_ic50_M": None,
                "fit_hill_slope": None, "fit_covariance_finite": False,
                "fit_ic50_inside_tested_range": False,
                "fit_warning_count": len(caught), "fit_rmse": None,
            }


def main() -> int:
    started = time.perf_counter()
    if not PIPELINE.is_file():
        raise FileNotFoundError(PIPELINE)
    pipeline = load_pipeline()
    rng = np.random.default_rng(SEED)
    base_cfg = dict(pipeline.PARAMETERS["modes"]["stable"])
    base_cfg["estimator_profile"] = "all"

    curve_rows: list[dict[str, object]] = []
    curve_records: list[dict[str, object]] = []
    estimator_rows: list[dict[str, object]] = []
    curve_id = 0
    for n in LENGTHS:
        doses_m = np.logspace(np.log10(DOSE_LOW_M), np.log10(DOSE_HIGH_M), n)
        log_dose = np.log10(doses_m)
        true_log_ic50 = float(np.median(log_dose))
        for scenario, params in SCENARIOS.items():
            for rep in range(REPEATS):
                curve_id += 1
                mean_response = hill4(
                    log_dose,
                    float(params["bottom"]),
                    float(params["top"]),
                    true_log_ic50,
                    float(params["hill"]),
                )
                if scenario == "noise_no_trend":
                    mean_response = np.full(n, float(params["top"]))
                response = mean_response + rng.normal(0.0, float(params["noise_sd"]), size=n)

                probe_estimators = rep == 0
                estimates = {}
                estimator_elapsed = None
                finite_count = None
                if probe_estimators:
                    cfg = dict(base_cfg)
                    cfg["min_len"] = n
                    cfg["estimator_profile"] = "all"
                    estimate_started = time.perf_counter()
                    estimates = pipeline.apply_complexity(response, flux_name="viability_pct", mode_cfg=cfg)
                    estimator_elapsed = time.perf_counter() - estimate_started
                    finite_count = int(sum(np.isfinite(estimates.get(name, np.nan)) for name in pipeline.ESTIMATOR_NAMES))
                fit = fit_hill4(log_dose, response)
                has_ic50 = bool(params["has_ic50"])
                fitted_log_ic50 = fit["fit_log10_ic50_M"]
                fit_error = (
                    abs(float(fitted_log_ic50) - true_log_ic50)
                    if has_ic50 and fitted_log_ic50 is not None else None
                )
                curve_label = f"sc_{curve_id:04d}"
                curve_common = {
                    "curve_id": curve_label,
                    "n_doses": n,
                    "scenario": scenario,
                    "replicate": rep + 1,
                    "true_log10_ic50_M": true_log_ic50 if has_ic50 else None,
                    "true_hill_slope": float(params["hill"]) if has_ic50 else None,
                    "noise_sd_percentage_points": float(params["noise_sd"]),
                    "has_defined_ic50": has_ic50,
                    "fit_abs_log10_ic50_error": fit_error,
                    "estimator_probe_included": probe_estimators,
                    "estimator_seconds": estimator_elapsed,
                }
                for j, (dose, ldose, y) in enumerate(zip(doses_m, log_dose, response), 1):
                    curve_rows.append({
                        **curve_common,
                        "point_index": j,
                        "dose_M": float(dose),
                        "log10_dose_M": float(ldose),
                        "response_viability_pct": float(y),
                    })
                curve_common["finite_estimators_of_29"] = finite_count
                curve_common.update(fit)
                curve_records.append(curve_common)
                if probe_estimators:
                    for name in pipeline.ESTIMATOR_NAMES:
                        value = estimates.get(name, np.nan)
                        finite = bool(np.isfinite(value))
                        estimator_rows.append({
                            "curve_id": curve_label,
                            "n_doses": n,
                            "scenario": scenario,
                            "replicate": rep + 1,
                            "estimator": name,
                            "value": float(value) if finite else None,
                            "finite": finite,
                            "estimator_seconds_for_curve": estimator_elapsed,
                        })

    def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            raise RuntimeError(f"No rows to write: {path}")
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    curves_path = OUT / "SYNTHETIC_DOSE_CURVES.csv"
    fits_path = OUT / "HILL4_FIT_PER_CURVE.csv"
    write_csv(curves_path, curve_rows)
    write_csv(fits_path, curve_records)

    probes_path = OUT / "ESTIMATOR_PROBES.csv"
    write_csv(probes_path, estimator_rows)

    fit_summary = []
    for n in LENGTHS:
        for scenario in SCENARIOS:
            rows = [r for r in curve_records if r["n_doses"] == n and r["scenario"] == scenario]
            errors = np.asarray([r["fit_abs_log10_ic50_error"] for r in rows if r["fit_abs_log10_ic50_error"] is not None], dtype=float)
            fit_summary.append({
                "n_doses": n,
                "scenario": scenario,
                "curves": len(rows),
                "hill_fit_converged": sum(r["fit_status"] == "converged" for r in rows),
                "covariance_finite": sum(bool(r["fit_covariance_finite"]) for r in rows),
                "ic50_inside_tested_range": sum(bool(r["fit_ic50_inside_tested_range"]) for r in rows),
                "curves_with_defined_ic50": len(errors),
                "median_abs_log10_ic50_error": float(np.median(errors)) if errors.size else None,
                "p90_abs_log10_ic50_error": float(np.quantile(errors, 0.90)) if errors.size else None,
            })
    fit_summary_path = OUT / "HILL4_FIT_SUMMARY.csv"
    write_csv(fit_summary_path, fit_summary)

    manifest = {
        "protocol": "short_dose_response_synthetic_pilot_v1.1",
        "status": "descriptive_monte_carlo_pilot_not_confirmatory",
        "seed": SEED,
        "replicates_per_length_scenario": REPEATS,
        "lengths": list(LENGTHS),
        "concentrations_M": [DOSE_LOW_M, DOSE_HIGH_M],
        "scenarios": SCENARIOS,
        "pipeline": str(PIPELINE),
        "pipeline_version": getattr(pipeline, "VERSION", "not exposed"),
        "pipeline_sha256": sha256(PIPELINE),
        "pipeline_api": "apply_complexity only; unchanged source; local min_len=N; estimator_profile=all",
        "full_pipeline_run": False,
        "t0_tlog_computed": False,
        "bootstrap": False,
        "interpretation": "Describes one-call estimator finiteness/values per condition and conventional 4PL fit behavior on synthetic vectors only. Monte Carlo repetitions are not experimental replicates. Does not validate estimator stability, a small-series production mode, or T0=IC50.",
        "outputs": {},
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    for path in (curves_path, fits_path, probes_path, fit_summary_path):
        manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest["protocol_sha256"] = sha256(HERE / "PROTOCOLE_FR.md")
    manifest["runner_sha256"] = sha256(Path(__file__))
    manifest["estimator_probe_policy"] = "one first RNG draw per length x scenario (16 curves); no estimator stability inference"
    manifest_path = OUT / "PILOT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "curves": len(curve_records),
        "estimator_probe_rows": len(estimator_rows),
        "pipeline_sha256": manifest["pipeline_sha256"],
        "runtime_seconds": manifest["runtime_seconds"],
        "outputs": manifest["outputs"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
