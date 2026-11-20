"""Sensitivity check for finite-size Ising Binder inference.

The archived array stores blocks concatenated in chain order. This script
compares the legacy pooled-block bootstrap with chain-stratified and
hierarchical chain/block resampling, and estimates autocorrelation only on
stored block-level moments (not raw Wolff updates).
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE / "finite_size"
FIT_SCRIPT = HERE / "binder_scaling_fit.py"

spec = importlib.util.spec_from_file_location("binder_scaling_fit", FIT_SCRIPT)
fit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit_module)
fit_model = fit_module.fit_model


def binder_from_moments(moment_means):
    m2, m4 = float(moment_means[3]), float(moment_means[4])
    return 1.0 - m4 / (3.0 * m2 * m2) if m2 > 0 else np.nan


def crossing(t_grid, u_left, u_right, tc):
    diff = np.asarray(u_left) - np.asarray(u_right)
    found = []
    for i in range(len(t_grid) - 1):
        if diff[i] == 0:
            found.append((float(t_grid[i]), float(u_left[i])))
        elif diff[i] * diff[i + 1] < 0:
            f = -diff[i] / (diff[i + 1] - diff[i])
            found.append((float(t_grid[i] + f * (t_grid[i + 1] - t_grid[i])),
                          float(u_left[i] + f * (u_left[i + 1] - u_left[i]))))
    found = [p for p in found if abs(p[0] - tc) <= 0.2]
    return min(found, key=lambda p: abs(p[0] - tc)) if found else (np.nan, np.nan)


def block_autocorrelation(series):
    """Initial-positive-pair tau_int estimate, in stored-block units."""
    x = np.asarray(series, dtype=float)
    if len(x) < 8 or not np.all(np.isfinite(x)):
        return np.nan
    x = x - x.mean()
    var = np.dot(x, x) / len(x)
    if var <= 0:
        return np.nan
    max_lag = min(len(x) // 2, 20)
    rho = []
    for lag in range(1, max_lag + 1):
        rho.append(float(np.dot(x[:-lag], x[lag:]) / (len(x) - lag) / var))
    tau = 0.5
    for i in range(0, len(rho) - 1, 2):
        pair = rho[i] + rho[i + 1]
        if pair <= 0:
            break
        tau += pair
    return float(tau)


def draw_indices(rng, n_chains, blocks_per_chain, method):
    if method == "pooled_iid":
        return rng.integers(0, n_chains * blocks_per_chain,
                            size=n_chains * blocks_per_chain)
    if method == "chain_stratified":
        return np.concatenate([
            chain * blocks_per_chain + rng.integers(0, blocks_per_chain,
                                                     size=blocks_per_chain)
            for chain in range(n_chains)
        ])
    if method == "hierarchical_chain_block":
        selected_chains = rng.integers(0, n_chains, size=n_chains)
        return np.concatenate([
            chain * blocks_per_chain + rng.integers(0, blocks_per_chain,
                                                     size=blocks_per_chain)
            for chain in selected_chains
        ])
    raise ValueError(method)


def interval(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    return {
        "n_valid": int(len(x)),
        "mean": float(np.mean(x)) if len(x) else None,
        "se": float(np.std(x, ddof=1)) if len(x) > 1 else (0.0 if len(x) else None),
        "ci95_low": float(np.percentile(x, 2.5)) if len(x) else None,
        "ci95_high": float(np.percentile(x, 97.5)) if len(x) else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20261109)
    args = parser.parse_args()
    if args.replicates < 20:
        raise ValueError("Use at least 20 bootstrap replicates for this diagnostic.")

    meta = json.loads((ROOT / "finite_size_summary.json").read_text(encoding="utf-8"))
    archive = np.load(ROOT / "finite_size_block_moments.npz")
    moments = archive["moments"]
    sizes = archive["sizes"].astype(int).tolist()
    temperatures = archive["temperatures"].astype(float)
    n_chains = int(meta["independent_chains"])
    n_samples = int(meta["measurement_cluster_updates_per_chain_and_T"])
    block_size = int(meta["block_size"])
    blocks_per_chain = n_samples // block_size
    n_t, n_blocks = len(temperatures), moments.shape[2]
    if moments.shape != (len(sizes), n_t, n_chains * blocks_per_chain, 6):
        raise ValueError(f"Archive shape does not match chain metadata: {moments.shape}")
    if sizes != [8, 12, 16, 24, 32, 48, 64]:
        raise ValueError(f"Unexpected lattice sizes: {sizes}")

    tc_exact = float(meta["exact_Tc_infinite_lattice"])
    fit_window = (2.22, 2.32)
    ti_fit = np.flatnonzero((temperatures >= fit_window[0]) &
                            (temperatures <= fit_window[1]))
    t_fit = temperatures[ti_fit]
    results = pd.read_csv(ROOT / "finite_size_results.csv")
    # Recompute key observables from the archived block moments before fitting.
    reproduction_error = {k: 0.0 for k in
                          ("Cv_per_spin", "chi_abs_per_spin", "Binder_U4", "abs_magnetization")}
    for li, L in enumerate(sizes):
        for ti, temperature in enumerate(temperatures):
            e, e2, _m, m2, m4, abs_m = moments[li, ti].mean(axis=0)
            n = L * L
            checks = {
                "Cv_per_spin": n * max(0.0, e2 - e * e) / (temperature * temperature),
                "chi_abs_per_spin": n * max(0.0, m2 - abs_m * abs_m) / temperature,
                "Binder_U4": 1.0 - m4 / (3.0 * m2 * m2),
                "abs_magnetization": abs_m,
            }
            row = results[(results["L"] == L) &
                          np.isclose(results["T"], temperature)].iloc[0]
            for key, value in checks.items():
                reproduction_error[key] = max(reproduction_error[key],
                                               abs(float(row[key]) - float(value)))
    if max(reproduction_error.values()) > 1e-10:
        raise ValueError(f"Archived moments do not reproduce CSV observables: {reproduction_error}")
    fit_rows = []
    for li, L in enumerate(sizes):
        for ti in ti_fit:
            row = results[(results["L"] == L) &
                          np.isclose(results["T"], temperatures[ti])].iloc[0]
            fit_rows.append({"L": float(L), "T": float(temperatures[ti]),
                             "U": float(row["Binder_U4"]),
                             "sigma": float(row["Binder_U4_se"])})
    fit_data = pd.DataFrame(fit_rows)
    Ld, Td, Ud = (fit_data[k].to_numpy(float) for k in ("L", "T", "U"))
    sigma = np.maximum(fit_data["sigma"].to_numpy(float), 1e-4)
    base_uncorrected = fit_model(Ld, Td, Ud, sigma, False)
    base_corrected = fit_model(Ld, Td, Ud, sigma, True)
    base = {"uncorrected": base_uncorrected, "corrected_Lminus2": base_corrected}

    methods = ("pooled_iid", "chain_stratified", "hierarchical_chain_block")
    models = (("uncorrected", False), ("corrected_Lminus2", True))
    samples = {method: {name: [] for name, _ in models} for method in methods}
    crossing_samples = {method: [] for method in methods}
    rng = np.random.default_rng(args.seed)
    li48, li64 = sizes.index(48), sizes.index(64)
    for rep in range(args.replicates):
        for method in methods:
            bU = []
            u48, u64 = [], []
            for li, L in enumerate(sizes):
                for ti in ti_fit:
                    blocks = moments[li, ti]
                    idx = draw_indices(rng, n_chains, blocks_per_chain, method)
                    u = binder_from_moments(blocks[idx].mean(axis=0))
                    bU.append(u)
                    if L == 48:
                        u48.append(u)
                    elif L == 64:
                        u64.append(u)
            tc_cross, u_cross = crossing(t_fit, u48, u64, tc_exact)
            crossing_samples[method].append({"Tc": tc_cross, "U4": u_cross})
            bU = np.asarray(bU, dtype=float)
            for name, corrected in models:
                try:
                    fit = fit_model(Ld, Td, bU, sigma, corrected,
                                    start=base[name]["params"])
                    if fit["success"] and np.all(np.isfinite(fit["params"])):
                        samples[method][name].append(fit["params"][:3].copy())
                except (ValueError, FloatingPointError, np.linalg.LinAlgError):
                    pass
        if (rep + 1) % 50 == 0:
            print(f"Bootstrap sensitivity {rep + 1}/{args.replicates}", flush=True)

    summary = {
        "protocol": {
            "sizes": sizes, "Tc_reference": tc_exact, "temperature_fit_window": list(fit_window),
            "chains": n_chains, "samples_per_chain_cell": n_samples,
            "block_size_updates": block_size, "blocks_per_chain_cell": blocks_per_chain,
            "bootstrap_replicates": args.replicates, "seed": args.seed,
            "chain_order": "block array is the vstack of chain outputs in chain order",
            "models": "same cubic Binder scaling fits and fixed pointwise sigma as the original fit",
        },
        "point_fits": {}, "bootstrap_sensitivity": {}, "block_autocorrelation": {},
        "limitations": [
            "Archived data contain block averages, not raw per-update trajectories; autocorrelation is only estimated between block averages.",
            "Three chains provide a weak estimate of between-chain variability; hierarchical intervals should be read as a sensitivity analysis.",
            "Fits keep the original pointwise sigma fixed; these intervals isolate bootstrap resampling design, not all fit/model uncertainty.",
            "The chain boundaries are inferred from saved run settings and the documented chain concatenation order.",
        ],
    }
    summary["archive_reproduction"] = {
        "checks": "recomputed from archived block moments across all (L,T) cells",
        "maximum_absolute_error": reproduction_error,
        "pass_tolerance": 1e-10,
        "passed": True,
    }
    for name, fit in base.items():
        summary["point_fits"][name] = {
            "Tc": float(fit["params"][0]), "nu": float(fit["params"][1]),
            "U_star": float(fit["params"][2]), "AIC": fit["AIC"], "BIC": fit["BIC"],
        }
    csv_rows = []
    for method in methods:
        crossings = crossing_samples[method]
        summary["bootstrap_sensitivity"][method] = {
            "binder_crossing_48_64_Tc": interval([x["Tc"] for x in crossings]),
            "binder_crossing_48_64_U4": interval([x["U4"] for x in crossings]),
            "fits": {},
        }
        for name, _ in models:
            arr = np.asarray(samples[method][name], dtype=float)
            data = {"n_valid": int(len(arr))}
            labels = ("Tc", "nu", "U_star")
            for j, label in enumerate(labels):
                data[label] = interval(arr[:, j]) if len(arr) else interval([])
            summary["bootstrap_sensitivity"][method]["fits"][name] = data
            row = {"method": method, "model": name, "n_valid": int(len(arr))}
            for label in labels:
                vals = data[label]
                for key in ("mean", "se", "ci95_low", "ci95_high"):
                    row[f"{label}_{key}"] = vals[key]
            row["crossing_48_64_Tc_ci95_low"] = summary["bootstrap_sensitivity"][method]["binder_crossing_48_64_Tc"]["ci95_low"]
            row["crossing_48_64_Tc_ci95_high"] = summary["bootstrap_sensitivity"][method]["binder_crossing_48_64_Tc"]["ci95_high"]
            csv_rows.append(row)

    near_ti = int(np.argmin(np.abs(temperatures - tc_exact)))
    ac = {}
    for li, L in enumerate(sizes):
        ac[str(L)] = {"T": float(temperatures[near_ti]), "observables": {}}
        for col, label in ((0, "energy"), (3, "m2"), (5, "abs_m")):
            per_chain = [block_autocorrelation(
                moments[li, near_ti, c * blocks_per_chain:(c + 1) * blocks_per_chain, col]
            ) for c in range(n_chains)]
            finite = np.asarray(per_chain, dtype=float)
            ac[str(L)]["observables"][label] = {
                "tau_int_blocks_per_chain": [float(x) if np.isfinite(x) else None for x in finite],
                "median_tau_int_blocks": float(np.nanmedian(finite)) if np.any(np.isfinite(finite)) else None,
            }
    summary["block_autocorrelation"] = {
        "definition": "initial-positive-pair tau_int estimate on 50 consecutive block means per chain; iid baseline is 0.5 block",
        "temperature_nearest_Tc": float(temperatures[near_ti]), "by_size": ac,
    }

    out_json = ROOT / "chain_bootstrap_validation.json"
    out_csv = ROOT / "chain_bootstrap_validation.csv"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.DataFrame(csv_rows).to_csv(out_csv, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    colors = {"pooled_iid": "#777777", "chain_stratified": "#377eb8",
              "hierarchical_chain_block": "#e41a1c"}
    labels = {"pooled_iid": "Pooled blocks", "chain_stratified": "Within-chain",
              "hierarchical_chain_block": "Chains + blocks"}
    method_order = list(methods)
    for col, (model, title) in enumerate((("uncorrected", "Without correction"),
                                          ("corrected_Lminus2", r"With $L^{-2}$ correction"))):
        for row, (param_i, param_label, reference) in enumerate(
                ((0, r"$T_c$", tc_exact), (1, r"$\nu$", 1.0))):
            ax = axes[row, col]
            for j, method in enumerate(method_order):
                arr = np.asarray(samples[method][model], dtype=float)
                if not len(arr):
                    continue
                values = arr[:, param_i]
                median = float(np.percentile(values, 50))
                lo, hi = np.percentile(values, [2.5, 97.5])
                ax.errorbar(j, median, yerr=[[median - lo], [hi - median]], fmt="o",
                            color=colors[method], capsize=4, markersize=6)
            ax.axhline(reference, color="black", linestyle="--", linewidth=1,
                       label="Exact reference" if row == 0 and col == 0 else None)
            ax.set_xticks(range(len(method_order)), [labels[m] for m in method_order], rotation=15)
            ax.set_ylabel(param_label)
            ax.set_title(title if row == 0 else "")
            ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Sensitivity to chain-aware bootstrap resampling")
    fig.tight_layout()
    fig.savefig(ROOT / "chain_bootstrap_validation.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps({k: v["fits"] for k, v in summary["bootstrap_sensitivity"].items()}, indent=2))
    print(f"Wrote {out_json}, {out_csv}, and chain_bootstrap_validation.png")

if __name__ == "__main__":
    main()
