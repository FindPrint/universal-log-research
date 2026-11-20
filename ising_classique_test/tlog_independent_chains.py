"""Direct T_log comparison across three independent Ising chain records.

Input consists of the archived 80-Wolff-update block means, not raw per-update
spin trajectories. This is a chain-level robustness study for the estimators
on block-averaged observables, not a replacement for raw-time-series analysis.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
FINITE_SIZE = PROJECT / "ising_classique_test" / "finite_size"
OUT = PROJECT / "ising_classique_test" / "finite_size" / "tlog_chain_comparison"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5_3.py"

spec = importlib.util.spec_from_file_location("universal_log", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


def run_variant(label, frame, n_bootstrap, seed):
    csv_path = OUT / f"{label}.csv"
    frame.to_csv(csv_path, index=False)
    run_result, features, fluxes, fluxes_ui = ul.run_pipeline(
        data_source="custom",
        custom_file_path=str(csv_path),
        mapping={
            "control_col": "Temperature",
            "flux_mapping": {"Energy_per_spin": "Energy_per_spin",
                             "Magnetization": "Magnetization"},
            "flux_columns_explicit": True,
        },
        mode="fast",
        opt_cfg={"random_seed": seed, "harmonic_prob": ul.HARMONIC_PROB,
                 "max_workers": 1},
    )
    state = ul.compute_holographic_tension_state(
        features, run_result.get("scores"), n_samples=len(frame),
        control_col="Temperature"
    )
    window = ul.resolve_tlog_window_size(run_result)
    uncertainty = ul.estimate_tlog_d_uncertainty(
        features, n_input_rows=len(frame), window_size=window,
        n_bootstrap=n_bootstrap, seed=seed + 20261109,
    )
    scales = [
        {"kind": "block_measurements", "value": len(frame)},
        {"kind": "lattice_sites", "value": 16 * 16},
    ]
    profiles = ul.build_tlog_profiles(state, scales, d_uncertainty=uncertainty)
    (OUT / f"{label}_df_feat.csv").write_text(features.to_csv(index=False), encoding="utf-8")
    return {
        "label": label,
        "n_rows": int(len(frame)),
        "window_size_input_rows": window,
        "n_progress_positions": int(len(features)),
        "n_dimension_estimators_finite": int(sum(
            1 for value in state.get("per_estimator", {}).values()
            if value.get("enters_geometric_D")
        )),
        "D_vector": state.get("D_vector"),
        "uncertainty_status": uncertainty.get("status"),
        "uncertainty_method": uncertainty.get("method"),
        "bootstrap_replicates": uncertainty.get("n_bootstrap"),
        "block_length_positions": uncertainty.get("block_length_positions"),
        "profiles": profiles,
    }


def main(n_bootstrap=100, blocks_per_temperature=4):
    OUT.mkdir(parents=True, exist_ok=True)
    archive = np.load(FINITE_SIZE / "finite_size_block_moments.npz")
    moments = archive["moments"]
    sizes = archive["sizes"].astype(int)
    temperatures = archive["temperatures"].astype(float)
    meta = json.loads((FINITE_SIZE / "finite_size_summary.json").read_text(encoding="utf-8"))
    chain_count = int(meta["independent_chains"])
    blocks_per_chain = int(meta["measurement_cluster_updates_per_chain_and_T"] // meta["block_size"])
    L = 16
    li = int(np.flatnonzero(sizes == L)[0])
    if moments.shape[2] != chain_count * blocks_per_chain:
        raise ValueError("The stored block array does not match the chain metadata.")

    if blocks_per_temperature < 2 or blocks_per_temperature > blocks_per_chain:
        raise ValueError("blocks_per_temperature must be between 2 and the archived block count.")
    # Preserve every temperature while reducing the full 50-block record to
    # a deterministic, evenly spaced subset for this exploratory comparison.
    selected_offsets = np.unique(np.rint(np.linspace(
        0, blocks_per_chain - 1, blocks_per_temperature
    )).astype(int))
    frames = []
    for chain in range(chain_count):
        rows = []
        start = chain * blocks_per_chain
        for ti, temperature in enumerate(temperatures):
            for offset in selected_offsets:
                block = start + int(offset)
                moment = moments[li, ti, block]
                rows.append({"Temperature": float(temperature),
                             "Energy_per_spin": float(moment[0]),
                             "Magnetization": float(moment[2]),
                             "Abs_magnetization": float(moment[5])})
        frames.append(pd.DataFrame(rows))

    variants = []
    for chain, frame in enumerate(frames):
        print(f"Running independent chain {chain + 1}/{chain_count} ({len(frame)} selected block observations)", flush=True)
        variants.append(run_variant(f"chain_{chain}", frame, n_bootstrap, 4200 + chain))
    pooled = pd.concat(frames, ignore_index=True)
    print(f"Running pooled chains ({len(pooled)} selected block observations)", flush=True)
    variants.append(run_variant("pooled", pooled, n_bootstrap, 4299))

    anchor_names = ("saturation", "criticality", "divergence", "null_reference")
    cross_chain = {}
    chain_variants = variants[:chain_count]
    for anchor in anchor_names:
        values = [v["D_vector"].get({"saturation": "d_sat", "criticality": "d_crit",
                                     "divergence": "d_div", "null_reference": "d_null"}[anchor])
                  for v in chain_variants]
        finite = np.asarray([x for x in values if x is not None], dtype=float)
        cross_chain[anchor] = {
            "per_chain_d": values,
            "n_finite_chains": int(len(finite)),
            "mean_d": float(np.mean(finite)) if len(finite) else None,
            "sd_between_chains": float(np.std(finite, ddof=1)) if len(finite) > 1 else None,
            "min_d": float(np.min(finite)) if len(finite) else None,
            "max_d": float(np.max(finite)) if len(finite) else None,
            "range_d": float(np.ptp(finite)) if len(finite) else None,
        }

    result = {
        "purpose": "Compare T_log dimension anchors across independent chain records and their pooled block observations.",
        "simulation": {
            "model": meta["model"], "L": L, "temperatures": [float(temperatures[0]), float(temperatures[-1])],
            "chains": chain_count,
            "blocks_archived_per_chain_per_temperature": blocks_per_chain,
            "blocks_selected_per_chain_per_temperature": int(len(selected_offsets)),
            "selected_block_offsets_zero_based": selected_offsets.tolist(),
            "selection_method": "deterministic evenly spaced subset within each temperature",
            "block_updates": int(meta["block_size"]),
            "block_observation_count_per_chain": int(len(frames[0])),
            "bootstrap_replicates_per_variant": int(n_bootstrap),
        },
        "data_limitations": [
            "The archive stores block means of e, m and |m|, not the raw spin trajectory or per-update values.",
            "Each independent chain record archives 50 consecutive block means per temperature; this run uses 4 deterministically and evenly spaced blocks at each temperature to keep the four pipeline runs tractable.",
            "Temperature settings are simulated independently and then ordered as a sweep. The chain comparison therefore tests estimator stability on a thinned, block-averaged response sweep, not full trajectory-level dynamics.",
            "Three chains are too few for a calibrated between-chain confidence interval; mean, standard deviation and range are descriptive.",
        ],
        "cross_chain_anchor_summary": cross_chain,
        "variants": variants,
    }
    path = OUT / "tlog_chain_comparison.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    rows = []
    for variant in variants:
        for profile in variant["profiles"]:
            for name, entry in profile["anchor_readings"].items():
                uncertainty = entry.get("uncertainty") or {}
                rows.append({
                    "variant": variant["label"], "n_rows": variant["n_rows"],
                    "n_kind": profile["n_scale"]["kind"], "n_value": profile["n_scale"]["value"],
                    "anchor": name, "d": entry.get("d"), "T_log": entry.get("T_log"),
                    "d_se": uncertainty.get("d_se"),
                    "d_ci95_low": (uncertainty.get("d_ci95") or [None, None])[0],
                    "d_ci95_high": (uncertainty.get("d_ci95") or [None, None])[1],
                    "T_log_se": uncertainty.get("T_log_se"),
                    "T_log_ci95_low": (uncertainty.get("T_log_ci95") or [None, None])[0],
                    "T_log_ci95_high": (uncertainty.get("T_log_ci95") or [None, None])[1],
                    "uncertainty_status": uncertainty.get("status"),
                    "bootstrap_method": uncertainty.get("method"),
                })
    pd.DataFrame(rows).to_csv(OUT / "tlog_chain_comparison.csv", index=False)
    print(f"Wrote {path} and tlog_chain_comparison.csv")


if __name__ == "__main__":
    main()
