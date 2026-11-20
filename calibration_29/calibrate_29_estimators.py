"""Controlled synthetic calibration screen for the 29 v5.3 estimators.

It tests the estimator layer on known graph dimensions (fractional Brownian
paths), known Hurst/spectral exponents (fractional Gaussian noise), and known
intrinsic dimensions (quasiperiodic k-tori reconstructed from one scalar trace).
This is a screening benchmark, not a universal validation or a test of T_log
as a phase-transition detector.
"""
from __future__ import annotations
import importlib.util
import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
_out_setting = Path(os.environ.get("UNIVERSAL_LOG_CALIBRATION_OUT", "calibration_29"))
OUT = _out_setting if _out_setting.is_absolute() else PROJECT / _out_setting
_pipeline_setting = Path(os.environ.get("UNIVERSAL_LOG_PIPELINE", "UNIVERSAL_LOG_v5_3.py"))
PIPELINE = _pipeline_setting if _pipeline_setting.is_absolute() else PROJECT / _pipeline_setting
N = 1024
REPLICATES_STOCHASTIC = 8
REPLICATES_TORUS = 5
SEED = 20261108

spec = importlib.util.spec_from_file_location("universal_log", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)

GRAPH_ESTIMATORS = [
    "Higuchi", "Katz", "Petrosian", "Sevcik", "BoxCounting", "VisibilityGraph",
]
INTRINSIC_ESTIMATORS = [
    "CorrelationD2", "GrassbergerProcaccia", "InformationD1", "TwoNN", "DANCo",
    "LevinaBickel", "LocalPCA", "GraphDimension", "PersistentHomology", "MFA",
]
LINEAR_EFFECTIVE_ESTIMATORS = ["PCAIntrinsic", "Fisher"]
NON_DIMENSION = sorted(ul.NON_DIMENSION_REASON)


def fgn_circulant(n: int, hurst: float, rng: np.random.Generator) -> np.ndarray:
    """Fractional Gaussian noise from a nonnegative circulant covariance embedding."""
    lags = np.arange(n, dtype=float)
    gamma = np.empty(n, dtype=float)
    gamma[0] = 1.0
    k = lags[1:]
    gamma[1:] = 0.5 * (np.abs(k - 1.0) ** (2 * hurst)
                       - 2.0 * k ** (2 * hurst)
                       + (k + 1.0) ** (2 * hurst))
    circulant_row = np.concatenate([gamma, [0.0], gamma[:0:-1]])
    eigenvalues = np.fft.fft(circulant_row).real
    min_eigenvalue = float(eigenvalues.min())
    if min_eigenvalue < -1e-8:
        raise ValueError(f"Circulant covariance is not positive semidefinite: {min_eigenvalue}.")
    noise = rng.normal(size=2 * n)
    sample = np.fft.ifft(np.sqrt(np.maximum(eigenvalues, 0.0)) * np.fft.fft(noise)).real
    return sample[:n]


def quasiperiodic_torus(n: int, dimension: int, rng: np.random.Generator) -> np.ndarray:
    """A generic scalar observation of a k-torus with rationally independent rates."""
    primes = (2, 3, 5, 7)
    t = np.arange(n, dtype=float)
    signal = np.zeros(n, dtype=float)
    for j, prime in enumerate(primes[:dimension]):
        omega = 2.0 * np.pi * np.sqrt(prime) / 13.0
        phase = float(rng.uniform(0.0, 2.0 * np.pi))
        signal += np.cos(omega * t + phase)
    return signal / math.sqrt(dimension)


def make_cases():
    cases = []
    for hurst in (0.50, 0.75):
        for rep in range(REPLICATES_STOCHASTIC):
            rng = np.random.default_rng(SEED + int(hurst * 1000) * 10 + rep)
            increments = fgn_circulant(N, hurst, rng)
            cases.append({
                "benchmark": f"fGn_H{hurst:.2f}", "replicate": rep,
                "signal": increments,
                "process": "fractional Gaussian noise (stationary increments)",
                "known_hurst": hurst,
                "known_spectral_beta": 2.0 * hurst - 1.0,
                "known_graph_dimension": None,
                "known_intrinsic_dimension": None,
                "embedding_stress": False,
            })
            cases.append({
                "benchmark": f"fBm_graph_H{hurst:.2f}", "replicate": rep,
                "signal": np.cumsum(increments),
                "process": "fractional Brownian sample path (integrated fGn)",
                "known_hurst": hurst,
                "known_spectral_beta": None,
                "known_graph_dimension": 2.0 - hurst,
                "known_intrinsic_dimension": None,
                "embedding_stress": False,
            })
    for dimension in (1, 2, 3, 4):
        for rep in range(REPLICATES_TORUS):
            rng = np.random.default_rng(SEED + 10000 + dimension * 100 + rep)
            cases.append({
                "benchmark": f"torus_k{dimension}", "replicate": rep,
                "signal": quasiperiodic_torus(N, dimension, rng),
                "process": f"smooth quasiperiodic scalar observation of a {dimension}-torus",
                "known_hurst": None,
                "known_spectral_beta": None,
                "known_graph_dimension": 1.0,
                "known_intrinsic_dimension": float(dimension),
                "embedding_stress": dimension == 4,
            })
    return cases


def targets_for_case(case: dict) -> dict[str, tuple[str, float, float]]:
    """Return target kind, truth and screening tolerance for applicable outputs."""
    targets: dict[str, tuple[str, float, float]] = {}
    benchmark = case["benchmark"]
    if benchmark.startswith("fBm_graph"):
        truth = float(case["known_graph_dimension"])
        for name in ["Higuchi", "Katz", "Petrosian", "Sevcik", "BoxCounting", "VisibilityGraph"]:
            targets[name] = ("graph_dimension", truth, 0.15)
    elif benchmark.startswith("fGn_"):
        h = float(case["known_hurst"])
        targets["Hurst"] = ("hurst_exponent", h, 0.10)
        targets["DFA"] = ("code_transform_2_minus_DFA_alpha", 2.0 - h, 0.15)
        targets["Hurst2mH"] = ("code_transform_2_minus_H", 2.0 - h, 0.15)
        targets["SpectralBeta"] = ("power_spectral_beta", float(case["known_spectral_beta"]), 0.20)
    elif benchmark.startswith("torus_"):
        k = float(case["known_intrinsic_dimension"])
        for name in INTRINSIC_ESTIMATORS:
            targets[name] = ("intrinsic_attractor_dimension", k, 0.50)
        # PCAIntrinsic and Fisher are participation ratios, not ranks. 2*k is
        # the maximum linear rank of this delay signal, but it is not the
        # expected participation ratio unless the covariance eigenvalues are
        # equal. Keep these outputs in the raw file; do not score them against
        # an invalid 2*k reference.
        for name in ["Higuchi", "Katz", "Petrosian", "Sevcik", "BoxCounting", "Hurst2mH"]:
            targets[name] = ("smooth_scalar_graph_dimension", 1.0, 0.15)
        # A smooth quasiperiodic flow has zero maximal Lyapunov exponent.
        targets["Lyapunov"] = ("maximal_lyapunov_exponent", 0.0, 0.20)
    return targets


def screening_status(target_kind: str, finite_fraction: float, median_error: float | None,
                     embedding_stress: bool) -> str:
    if embedding_stress and target_kind == "intrinsic_attractor_dimension":
        return "stress_only_embedding_dimension_limit"
    if finite_fraction < 0.80 or median_error is None:
        return "not_calibrated_insufficient_finite_outputs"
    tolerance = {
        "graph_dimension": 0.15,
        "smooth_scalar_graph_dimension": 0.15,
        "intrinsic_attractor_dimension": 0.50,
        "linear_effective_dimension_not_manifold_dimension": 0.75,
        "hurst_exponent": 0.10,
        "code_transform_2_minus_DFA_alpha": 0.15,
        "code_transform_2_minus_H": 0.15,
        "power_spectral_beta": 0.20,
        "maximal_lyapunov_exponent": 0.20,
    }.get(target_kind)
    if tolerance is None:
        return "descriptive_only_no_dimension_truth"
    return "passes_pilot_tolerance" if median_error <= tolerance else "fails_pilot_tolerance"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_records = []
    target_records = []
    cases = make_cases()
    mode_cfg = {"min_len": 50, "estimator_profile": "all"}
    for index, case in enumerate(cases, start=1):
        signal = np.asarray(case["signal"], dtype=float)
        values = ul.apply_complexity(signal, flux_name=case["benchmark"], mode_cfg=mode_cfg)
        targets = targets_for_case(case)
        for name in ul.ESTIMATOR_NAMES:
            value = values.get(name)
            finite = value is not None and np.isfinite(value)
            raw_records.append({
                "benchmark": case["benchmark"],
                "replicate": int(case["replicate"]),
                "process": case["process"],
                "embedding_stress": bool(case["embedding_stress"]),
                "estimator": name,
                "class_v53": ul.estimator_class(name),
                "enters_tlog_geometric_layer": name in {
                    method for methods in ul.DIMENSION_FOR_TLOG.values() for method in methods
                },
                "value": float(value) if finite else None,
                "finite": bool(finite),
            })
        for name, (target_kind, truth, tolerance) in targets.items():
            value = values.get(name)
            finite = value is not None and np.isfinite(value)
            target_records.append({
                "benchmark": case["benchmark"],
                "replicate": int(case["replicate"]),
                "estimator": name,
                "target_kind": target_kind,
                "reference_value": float(truth),
                "value": float(value) if finite else None,
                "absolute_error": abs(float(value) - truth) if finite else None,
                "relative_error": abs(float(value) - truth) / max(abs(truth), 1e-9) if finite else None,
                "finite": bool(finite),
                "embedding_stress": bool(case["embedding_stress"]),
                "screening_tolerance": float(tolerance),
            })
        if index % 5 == 0 or index == len(cases):
            print(f"Calibrated {index}/{len(cases)} synthetic signals", flush=True)

    raw = pd.DataFrame(raw_records)
    targets = pd.DataFrame(target_records)
    summary = []
    for (benchmark, estimator, target_kind), group in targets.groupby(
        ["benchmark", "estimator", "target_kind"], sort=False
    ):
        values = group.loc[group["finite"], "value"].to_numpy(dtype=float)
        errors = group.loc[group["finite"], "absolute_error"].to_numpy(dtype=float)
        truth = float(group["reference_value"].iloc[0])
        finite_fraction = float(len(values) / len(group))
        median_error = float(np.median(errors)) if len(errors) else None
        stress = bool(group["embedding_stress"].any())
        summary.append({
            "benchmark": benchmark,
            "estimator": estimator,
            "target_kind": target_kind,
            "reference_value": truth,
            "replicates": int(len(group)),
            "finite_replicates": int(len(values)),
            "finite_fraction": finite_fraction,
            "mean_estimate": float(np.mean(values)) if len(values) else None,
            "median_estimate": float(np.median(values)) if len(values) else None,
            "sd_estimate": float(np.std(values, ddof=1)) if len(values) > 1 else None,
            "median_absolute_error": median_error,
            "median_relative_error": float(np.median(group.loc[group["finite"], "relative_error"])) if len(values) else None,
            "screening_tolerance": float(group["screening_tolerance"].iloc[0]),
            "status": screening_status(target_kind, finite_fraction, median_error, stress),
            "scope_note": "pilot_screen_not_validation",
        })
    summary_df = pd.DataFrame(summary)
    raw_path = OUT / "estimator_outputs.csv"
    target_path = OUT / "targeted_calibration.csv"
    summary_path = OUT / "targeted_calibration_summary.csv"
    json_path = OUT / "calibration_29_results.json"
    raw.to_csv(raw_path, index=False)
    targets.to_csv(target_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    config = {
        "purpose": "Screen code outputs against known targets of distinct geometric/statistical kinds.",
        "pipeline_file": str(PIPELINE),
        "pipeline_version": ul.VERSION_MASTER,
        "sample_length": N,
        "stochastic_replicates": REPLICATES_STOCHASTIC,
        "torus_replicates": REPLICATES_TORUS,
        "seed_base": SEED,
        "estimator_count": len(ul.ESTIMATOR_NAMES),
        "estimator_names": ul.ESTIMATOR_NAMES,
        "dimension_for_tlog": ul.DIMENSION_FOR_TLOG,
        "non_dimension_signatures": ul.NON_DIMENSION_REASON,
        "benchmarks": [
            "fGn_H0.50 and fGn_H0.75: H and beta references, with the code's d transforms tested separately",
            "fBm_graph_H0.50 and fBm_graph_H0.75: known graph dimension 2-H",
            "torus_k1..k3: known manifold dimension k and smooth scalar graph dimension 1; PCA/Fisher outputs are descriptive because their participation ratios are not the rank 2k",
            "torus_k4: stress test because several code embeddings are capped below the generic 2k+1 Takens bound",
        ],
        "descriptive_only_estimators_on_torus": {
            name: "The code returns a covariance participation ratio; 2*k is only a possible linear rank, not a calibrated participation-ratio target."
            for name in LINEAR_EFFECTIVE_ESTIMATORS
        },
        "screening_rules": {
            "minimum_finite_fraction": 0.80,
            "graph_abs_error": 0.15,
            "intrinsic_abs_error": 0.50,
            "hurst_abs_error": 0.10,
            "spectral_beta_abs_error": 0.20,
            "linear_effective_dimension_abs_error": 0.75,
            "note": "Predeclared pilot tolerances are screening thresholds, not inferential pass/fail claims.",
        },
        "limitations": [
            "No noise or measurement irregularity is added; these are idealized data.",
            "Finite records and only 5-8 replicates give a screening result, not a full calibration study.",
            "The quasiperiodic signals are scalar delay observations; reconstruction quality depends on embedding dimension and delay.",
            "A linear covariance effective dimension and a manifold intrinsic dimension are different targets even when both are numerical dimensions.",
            "Non-dimensional signatures are retained and checked for finite outputs, but they are not forced to have a geometric dimension reference.",
            "Passing one synthetic family does not establish domain universality or validate the universal d_crit=4 reference.",
        ],
        "results": summary,
        "files": {
            "raw_estimator_outputs": str(raw_path),
            "targeted_calibration_long": str(target_path),
            "targeted_calibration_summary": str(summary_path),
        },
    }
    json_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Visualize only benchmark/estimator cells with an explicit target.
    if not summary_df.empty:
        pivot = summary_df.pivot(index="estimator", columns="benchmark", values="median_absolute_error")
        fig, ax = plt.subplots(figsize=(12, max(6, 0.28 * len(pivot))))
        image = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="magma", interpolation="nearest")
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=8)
        ax.set_title("Erreur médiane absolue par cible contrôlée (cellules non applicables laissées vides)")
        fig.colorbar(image, ax=ax, label="Erreur absolue médiane")
        fig.tight_layout()
        fig.savefig(OUT / "calibration_error_heatmap.png", dpi=170, bbox_inches="tight")
        plt.close(fig)
    print(f"Wrote {json_path}, {raw_path}, {target_path}, {summary_path}")


if __name__ == "__main__":
    main()
