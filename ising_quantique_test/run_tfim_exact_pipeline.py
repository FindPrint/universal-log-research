"""Exact-diagonalization test of UNIVERSAL_LOG on the quantum Ising chain.

Model: H/J = -sum_i Z_i Z_(i+1) - g sum_i X_i, periodic boundary,
zero temperature. Small chains are solved by sparse exact diagonalization.
The pipeline analyzes ground-state response curves versus g; it does not
analyze a time trajectory or establish universality from this single model.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import eigsh

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "ising_quantique_test"
DATA = OUT / "data"
RESULTS = OUT / "results"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5_3.py"
SIZES = (8, 10, 12)
G_VALUES = np.linspace(0.60, 1.40, 81)
FIXED_WINDOW = 16
BOOTSTRAP_REPLICATES = 300
SEED = 20261107
G_CRITICAL_THERMODYNAMIC = 1.0

spec = importlib.util.spec_from_file_location("universal_log", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


def make_operators(n: int):
    dim = 1 << n
    states = np.arange(dim, dtype=np.uint32)
    z = np.empty((n, dim), dtype=np.float64)
    for i in range(n):
        z[i] = 1.0 - 2.0 * ((states >> i) & 1)
    zz_sum = np.sum(z * np.roll(z, -1, axis=0), axis=0)
    diag_interaction = -zz_sum

    rows = np.tile(states.astype(np.int64), n)
    cols = np.concatenate([(states ^ (1 << i)).astype(np.int64) for i in range(n)])
    values = np.ones(len(rows), dtype=np.float64)
    x_sum = csr_matrix((values, (rows, cols)), shape=(dim, dim))
    return diag_interaction, x_sum, zz_sum, states


def ground_state_curve(n: int, g_values: np.ndarray) -> pd.DataFrame:
    diag_interaction, x_sum, zz_sum, states = make_operators(n)
    dim = 1 << n
    parity_partner = states ^ (dim - 1)
    observations = []
    for index, g in enumerate(g_values):
        hamiltonian = diags(diag_interaction, format="csr") - float(g) * x_sum
        rng = np.random.default_rng(SEED + 1000 * n + index)
        v0 = rng.normal(size=dim)
        energies, vectors = eigsh(
            hamiltonian, k=6, which="SA", v0=v0,
            tol=1e-10, maxiter=50000,
        )
        order = np.argsort(energies)
        energies = energies[order]
        vectors = vectors[:, order]
        psi = vectors[:, 0]
        parity_expectations = np.sum(vectors * vectors[parity_partner, :], axis=0)
        parities = np.where(parity_expectations >= 0.0, 1, -1)
        same_parity = np.flatnonzero(parities[1:] == parities[0]) + 1
        opposite_parity = np.flatnonzero(parities[1:] != parities[0]) + 1
        same_parity_gap = float(energies[same_parity[0]] - energies[0]) if len(same_parity) else np.nan
        opposite_parity_gap = float(energies[opposite_parity[0]] - energies[0]) if len(opposite_parity) else np.nan
        prob = psi * psi
        mx = float(np.vdot(psi, x_sum @ psi).real / n)
        zz = float(np.dot(prob, zz_sum) / n)
        energy_per_site = float(energies[0] / n)
        lowest_spectral_gap = float(max(0.0, energies[1] - energies[0]))
        observations.append({
            "g": float(g),
            "energy_per_site": energy_per_site,
            "transverse_magnetization": mx,
            "longitudinal_nn_correlation": zz,
            "lowest_spectral_gap": lowest_spectral_gap,
            "same_parity_gap": float(max(0.0, same_parity_gap)) if np.isfinite(same_parity_gap) else np.nan,
            "opposite_parity_gap": float(max(0.0, opposite_parity_gap)) if np.isfinite(opposite_parity_gap) else np.nan,
            "ground_state_parity": int(parities[0]),
        })
        if (index + 1) % 20 == 0 or index == len(g_values) - 1:
            print(f"N={n}: exact diagonalization {index + 1}/{len(g_values)} fields", flush=True)

    frame = pd.DataFrame(observations)
    frame["transverse_response_abs_derivative"] = np.abs(
        np.gradient(frame["transverse_magnetization"].to_numpy(), g_values, edge_order=2)
    )
    return frame


def run_pipeline_for_size(n: int, frame: pd.DataFrame) -> dict:
    size_dir = RESULTS / f"N{n}"
    size_dir.mkdir(parents=True, exist_ok=True)
    input_path = DATA / f"tfim_ground_state_N{n}.csv"
    frame.to_csv(input_path, index=False)
    run_result, features, _fluxes, _ui = ul.run_pipeline(
        data_source="custom",
        custom_file_path=str(input_path),
        mapping={
            "control_col": "g",
            "flux_mapping": {
                "energy_per_site": "energy_per_site",
                "transverse_magnetization": "transverse_magnetization",
                "longitudinal_nn_correlation": "longitudinal_nn_correlation",
                "same_parity_gap": "same_parity_gap",
                "transverse_response_abs_derivative": "transverse_response_abs_derivative",
            },
            "flux_columns_explicit": True,
        },
        mode="fast",
        opt_cfg={
            "random_seed": SEED,
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
        features, run_result.get("scores"), n_samples=len(frame), control_col="g"
    )
    uncertainty = ul.estimate_tlog_d_uncertainty(
        features, n_input_rows=len(frame), window_size=used_window,
        n_bootstrap=BOOTSTRAP_REPLICATES, seed=SEED + n,
    )
    scales = [
        {"kind": "field_observations", "value": len(frame)},
        {"kind": "lattice_sites", "value": n},
    ]
    profiles = ul.build_tlog_profiles(state, scales, d_uncertainty=uncertainty)
    features.to_csv(size_dir / "df_feat.csv", index=False)
    run_meta = {
        "success": bool(run_result.get("success")),
        "control": "g",
        "target": "transverse_magnetization",
        "fluxes": [
            "energy_per_site", "transverse_magnetization",
            "longitudinal_nn_correlation", "same_parity_gap",
            "transverse_response_abs_derivative",
        ],
        "window_size_input_rows": used_window,
        "mode_overrides_applied": run_result.get("mode_overrides_applied"),
        "estimator_profile": run_result.get("estimator_profile"),
        "n_estimators_requested": len(run_result.get("estimators_computed", [])),
        "n_feature_positions": int(len(features)),
        "D_vector": state.get("D_vector"),
        "uncertainty_status": uncertainty.get("status"),
        "bootstrap_replicates": uncertainty.get("n_bootstrap"),
        "bootstrap_block_length_positions": uncertainty.get("block_length_positions"),
        "profiles": profiles,
    }
    (size_dir / "tlog_result.json").write_text(
        json.dumps(run_meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    peak_index = int(np.argmax(frame["transverse_response_abs_derivative"].to_numpy()))
    gap_min_index = int(np.nanargmin(frame["same_parity_gap"].to_numpy()))
    lowest_gap_min_index = int(np.argmin(frame["lowest_spectral_gap"].to_numpy()))
    return {
        "N": n,
        "n_field_observations": int(len(frame)),
        "fixed_window_input_rows": used_window,
        "critical_field_reference_g_infinite_chain": G_CRITICAL_THERMODYNAMIC,
        "finite_grid_transverse_response_peak_g": float(frame.iloc[peak_index]["g"]),
        "peak_abs_error_from_g_c": float(abs(frame.iloc[peak_index]["g"] - G_CRITICAL_THERMODYNAMIC)),
        "finite_grid_gap_minimum_g": float(frame.iloc[gap_min_index]["g"]),
        "finite_grid_same_parity_gap_minimum": float(frame.iloc[gap_min_index]["same_parity_gap"]),
        "finite_grid_lowest_spectral_gap_minimum_g": float(frame.iloc[lowest_gap_min_index]["g"]),
        "finite_grid_lowest_spectral_gap_minimum": float(frame.iloc[lowest_gap_min_index]["lowest_spectral_gap"]),
        "pipeline_D_vector": state.get("D_vector"),
        "tlog_profiles": profiles,
        "n_finite_dimension_estimators": int(sum(
            1 for e in (state.get("per_estimator") or {}).values()
            if e.get("enters_geometric_D") and e.get("raw_median") is not None
        )),
    }


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    frames = {}
    physical = []
    for n in SIZES:
        frame = ground_state_curve(n, G_VALUES)
        frames[n] = frame
        peak_index = int(np.argmax(frame["transverse_response_abs_derivative"].to_numpy()))
        gap_index = int(np.nanargmin(frame["same_parity_gap"].to_numpy()))
        lowest_gap_index = int(np.argmin(frame["lowest_spectral_gap"].to_numpy()))
        physical.append({
            "N": n,
            "n_field_observations": int(len(frame)),
            "g_c_infinite_chain": G_CRITICAL_THERMODYNAMIC,
            "transverse_response_peak_g": float(frame.iloc[peak_index]["g"]),
            "peak_absolute_error": float(abs(frame.iloc[peak_index]["g"] - G_CRITICAL_THERMODYNAMIC)),
            "minimum_same_parity_gap_g": float(frame.iloc[gap_index]["g"]),
            "minimum_same_parity_gap": float(frame.iloc[gap_index]["same_parity_gap"]),
            "lowest_spectral_gap_g": float(frame.iloc[lowest_gap_index]["g"]),
            "lowest_spectral_gap": float(frame.iloc[lowest_gap_index]["lowest_spectral_gap"]),
        })
    pd.DataFrame(physical).to_csv(OUT / "physical_finite_size_summary.csv", index=False)

    # Physical diagnostic plot: locate the finite-size response peak, not a T_log claim.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for n, frame in frames.items():
        axes[0].plot(frame["g"], frame["transverse_response_abs_derivative"], label=f"N={n}")
        axes[1].plot(frame["g"], frame["same_parity_gap"], label=f"N={n}")
    for ax in axes:
        ax.axvline(G_CRITICAL_THERMODYNAMIC, color="black", linestyle="--", linewidth=1,
                   label="g_c = 1" if ax is axes[0] else None)
        ax.set_xlabel("Champ transverse réduit g = h/J")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("|d <X>/dg|")
    axes[0].set_title("Réponse transverse")
    axes[0].legend(fontsize=8)
    axes[1].set_ylabel("Gap vers l’état de même parité (unités J)")
    axes[1].set_title("Gap de même parité")
    axes[1].legend(fontsize=8)
    fig.suptitle("Chaîne d’Ising quantique transverse — diagonalisation exacte")
    fig.tight_layout()
    fig.savefig(OUT / "tfim_physical_diagnostics.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

    pipeline_results = []
    for n, frame in frames.items():
        print(f"Running UNIVERSAL_LOG on quantum Ising N={n} ({len(frame)} g values).", flush=True)
        pipeline_results.append(run_pipeline_for_size(n, frame))

    result = {
        "purpose": "Second-domain integration test on the 1D transverse-field quantum Ising chain.",
        "model": {
            "hamiltonian": "H/J = -sum_i Z_i Z_(i+1) - g sum_i X_i",
            "boundary": "periodic",
            "temperature": "ground state (T=0)",
            "field_definition": "g = h/J",
            "sizes": list(SIZES),
            "g_grid": [float(G_VALUES[0]), float(G_VALUES[-1]), int(len(G_VALUES))],
            "thermodynamic_critical_field": G_CRITICAL_THERMODYNAMIC,
            "reference": "P. Pfeuty, Annals of Physics 57, 79–90 (1970), DOI:10.1016/0003-4916(70)90270-8",
        },
        "protocol": {
        "solver": "SciPy sparse eigsh for six lowest eigenpairs; global spin-flip parity resolves the low-energy doublet",
            "pipeline_window_fixed_input_rows": FIXED_WINDOW,
            "threshold_monte_carlo_optimization": False,
            "same_pipeline_seed_for_all_sizes": SEED,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "control_axis": "g",
            "target": "transverse_magnetization",
            "fluxes": [
                "energy_per_site", "transverse_magnetization",
                "longitudinal_nn_correlation", "same_parity_gap",
                "transverse_response_abs_derivative",
            ],
            "T_log_n_scales": ["number of g points", "number of lattice sites N"],
        },
        "interpretation_limits": [
            "The input is a ground-state response curve as g varies, not a time series or Monte Carlo trajectory.",
            "Finite chains have a smooth crossover. In the ordered phase the lowest two states form a near-degenerate parity doublet, so the raw lowest spectral gap is not the bulk critical gap; the reported critical diagnostic is the gap to the first state of the ground-state parity.",
            "The pipeline regime labels and T_log dimensions are heuristic outputs and are not used as estimates of g_c.",
            "This tests domain transfer and file/API integration, not universality of the theory.",
        ],
        "physical_finite_size_results": physical,
        "pipeline_results": pipeline_results,
    }
    result_path = OUT / "quantum_ising_pipeline_summary.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame([{
        "N": x["N"],
        "n_field_observations": x["n_field_observations"],
        "g_c_reference": x["critical_field_reference_g_infinite_chain"],
        "response_peak_g": x["finite_grid_transverse_response_peak_g"],
        "same_parity_gap_minimum_g": x["finite_grid_gap_minimum_g"],
        "same_parity_gap_minimum": x["finite_grid_same_parity_gap_minimum"],
        "lowest_spectral_gap_minimum_g": x["finite_grid_lowest_spectral_gap_minimum_g"],
        "lowest_spectral_gap_minimum": x["finite_grid_lowest_spectral_gap_minimum"],
        **{f"{k}_d": (x["pipeline_D_vector"] or {}).get(k) for k in ("d_sat", "d_crit", "d_div", "d_null")},
    } for x in pipeline_results]).to_csv(OUT / "quantum_ising_pipeline_summary.csv", index=False)
    print(f"Wrote {result_path}")


if __name__ == "__main__":
    main()
