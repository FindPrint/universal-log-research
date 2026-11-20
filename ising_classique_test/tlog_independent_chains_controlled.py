"""Controlled full-record T_log comparison for the three L=16 Ising chains.

Uses all archived 80-Wolff-update block means (not raw spin trajectories), a
shared fixed analysis window, identical pipeline seed and no threshold-window
Monte Carlo optimization. Between-chain summaries are descriptive (three chains).
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
FINITE_SIZE = PROJECT / "ising_classique_test" / "finite_size"
OUT = FINITE_SIZE / "tlog_chain_comparison_controlled"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5_3.py"
L = 16
FIXED_WINDOW = 12
PIPELINE_SEED = 4200
N_BOOTSTRAP = 300

spec = importlib.util.spec_from_file_location("universal_log", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


def run_chain(label: str, frame: pd.DataFrame, chain_index: int) -> dict:
    csv_path = OUT / f"{label}.csv"
    frame.to_csv(csv_path, index=False)
    run_result, features, _fluxes, _ui = ul.run_pipeline(
        data_source="custom",
        custom_file_path=str(csv_path),
        mapping={
            "control_col": "Temperature",
            "flux_mapping": {
                "Energy_per_spin": "Energy_per_spin",
                "Magnetization": "Magnetization",
            },
            "flux_columns_explicit": True,
        },
        mode="fast",
        opt_cfg={
            "random_seed": PIPELINE_SEED,
            "auto_optimize_threshold": False,
            "optimization_iterations": 0,
            "mc_complexity_enabled": False,
            "max_workers": 1,
            "mode_overrides": {"w_size": FIXED_WINDOW},
        },
    )
    used_window = ul.resolve_tlog_window_size(run_result)
    if used_window != FIXED_WINDOW:
        raise RuntimeError(f"Requested window {FIXED_WINDOW}, pipeline used {used_window}.")
    state = ul.compute_holographic_tension_state(
        features, run_result.get("scores"), n_samples=len(frame), control_col="Temperature"
    )
    uncertainty = ul.estimate_tlog_d_uncertainty(
        features,
        n_input_rows=len(frame),
        window_size=used_window,
        n_bootstrap=N_BOOTSTRAP,
        seed=PIPELINE_SEED + 1000 + chain_index,
    )
    scales = [
        {"kind": "temperature_points", "value": len(frame)},
        {"kind": "block_observations_aggregated", "value": len(frame) * int(frame["blocks_averaged"].iloc[0])},
        {"kind": "lattice_sites", "value": L * L},
    ]
    profiles = ul.build_tlog_profiles(state, scales, d_uncertainty=uncertainty)
    features.to_csv(OUT / f"{label}_df_feat.csv", index=False)
    return {
        "label": label,
        "chain_index_zero_based": chain_index,
        "n_control_points": int(len(frame)),
        "n_temperatures": int(frame["Temperature"].nunique()),
        "blocks_per_temperature_averaged": int(frame["blocks_averaged"].iloc[0]),
        "block_observations_contributing": int(len(frame) * frame["blocks_averaged"].iloc[0]),
        "window_size_input_rows": int(used_window),
        "window_fraction_of_chain": float(used_window / len(frame)),
        "n_progress_positions": int(len(features)),
        "mode_overrides_applied": run_result.get("mode_overrides_applied"),
        "auto_threshold_optimization": False,
        "estimator_profile": run_result.get("estimator_profile"),
        "estimators_requested": len(run_result.get("estimators_computed", [])),
        "D_vector": state.get("D_vector"),
        "uncertainty_status": uncertainty.get("status"),
        "bootstrap_method": uncertainty.get("method"),
        "bootstrap_replicates": uncertainty.get("n_bootstrap"),
        "block_length_positions": uncertainty.get("block_length_positions"),
        "profiles": profiles,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    archive = np.load(FINITE_SIZE / "finite_size_block_moments.npz")
    moments = archive["moments"]
    sizes = archive["sizes"].astype(int)
    temperatures = archive["temperatures"].astype(float)
    meta = json.loads((FINITE_SIZE / "finite_size_summary.json").read_text(encoding="utf-8"))
    n_chains = int(meta["independent_chains"])
    block_size = int(meta["block_size"])
    blocks_per_chain = int(meta["measurement_cluster_updates_per_chain_and_T"] // block_size)
    if moments.shape[2] != n_chains * blocks_per_chain:
        raise ValueError("Archived moments and chain metadata are inconsistent.")
    li = int(np.flatnonzero(sizes == L)[0])

    variants = []
    for chain in range(n_chains):
        start = chain * blocks_per_chain
        stop = start + blocks_per_chain
        rows = []
        for ti, temperature in enumerate(temperatures):
            # The 50 repeated measurements estimate each response at one
            # control value. Average them so rows remain distinct temperatures.
            moment = moments[li, ti, start:stop, :].mean(axis=0)
            rows.append({
                "Temperature": float(temperature),
                "Energy_per_spin": float(moment[0]),
                "Magnetization": float(moment[2]),
                "Abs_magnetization": float(moment[5]),
                "blocks_averaged": int(blocks_per_chain),
            })
        frame = pd.DataFrame(rows)
        print(f"Chain {chain + 1}/{n_chains}: {len(frame)} measurements; fixed window {FIXED_WINDOW}.", flush=True)
        variants.append(run_chain(f"chain_{chain}", frame, chain))

    keys = {
        "saturation": "d_sat",
        "criticality": "d_crit",
        "divergence": "d_div",
        "null_reference": "d_null",
    }
    between_chain = {}
    for anchor, key in keys.items():
        values = [v["D_vector"].get(key) for v in variants]
        finite = np.asarray([v for v in values if v is not None], dtype=float)
        between_chain[anchor] = {
            "per_chain_d": values,
            "n_finite_chains": int(len(finite)),
            "mean_d": float(np.mean(finite)) if len(finite) else None,
            "sample_sd_between_chains": float(np.std(finite, ddof=1)) if len(finite) > 1 else None,
            "min_d": float(np.min(finite)) if len(finite) else None,
            "max_d": float(np.max(finite)) if len(finite) else None,
            "range_d": float(np.ptp(finite)) if len(finite) else None,
            "interval_status": "descriptive_only_three_chains",
        }

    result = {
        "purpose": "Isolate chain-record variation with a common fixed pipeline window on complete archived block records.",
        "model": meta["model"],
        "L": L,
        "temperature_range": [float(temperatures[0]), float(temperatures[-1])],
        "n_temperatures": int(len(temperatures)),
        "independent_chains": n_chains,
        "block_updates": block_size,
        "blocks_averaged_per_chain_and_temperature": blocks_per_chain,
        "control_points_per_chain": int(len(temperatures)),
        "block_observations_contributing_per_chain": int(blocks_per_chain * len(temperatures)),
        "window_protocol": {
            "fixed_w_size_input_rows": FIXED_WINDOW,
            "selection_basis": "12 of 76 distinct control points (about 16%); chosen before comparing chains",
            "same_window_for_every_chain": True,
            "threshold_monte_carlo_optimization": False,
            "pipeline_random_seed_same_for_all_chains": PIPELINE_SEED,
        },
        "bootstrap": {
            "replicates_per_chain": N_BOOTSTRAP,
            "seed_rule": "shared fixed pipeline seed + 1000 + chain index for uncertainty bootstrap",
            "block_length_mapping": "pipeline window projected from 76 distinct control points to the 120-position estimator landscape",
        },
        "data_limitations": [
            "Inputs are the complete archived means of 80 Wolff cluster updates per block, not per-update spin trajectories.",
            "All 50 blocks at each of the 76 independently simulated temperatures are averaged to one response point per temperature; this is a response sweep, not a trajectory across temperature.",
            "The moving-block bootstrap covers the ordered estimator landscape; it does not propagate the within-temperature uncertainty of the 50-block means.",
            "Three independent chains are too few to calibrate a between-chain confidence interval; standard deviations and ranges are descriptive.",
        ],
        "between_chain_anchor_summary": between_chain,
        "variants": variants,
    }
    json_path = OUT / "tlog_chain_comparison_controlled.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    rows = []
    for variant in variants:
        for profile in variant["profiles"]:
            for name, entry in profile["anchor_readings"].items():
                unc = entry.get("uncertainty") or {}
                ci = unc.get("d_ci95") or [None, None]
                tci = unc.get("T_log_ci95") or [None, None]
                rows.append({
                    "chain": variant["label"],
                    "n_kind": profile["n_scale"]["kind"],
                    "n_value": profile["n_scale"]["value"],
                    "anchor": name,
                    "d": entry.get("d"),
                    "d_ci95_low": ci[0],
                    "d_ci95_high": ci[1],
                    "T_log": entry.get("T_log"),
                    "T_log_ci95_low": tci[0],
                    "T_log_ci95_high": tci[1],
                    "window_size_input_rows": variant["window_size_input_rows"],
                    "bootstrap_block_length_positions": variant["block_length_positions"],
                })
    csv_path = OUT / "tlog_chain_comparison_controlled.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"Wrote {json_path} and {csv_path}")


if __name__ == "__main__":
    main()
