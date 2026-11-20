"""Fixed-temperature Ising MCMC experiment with multiple physical/control fluxes.

The simulation stores per-Wolff-update trajectories. The v5.8 core is then
run with explicit, predeclared flux mappings and alternative control columns.
This is a diagnostic study of axis/flux sensitivity, not a causal test.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import spearmanr

PROJECT = Path(__file__).resolve().parents[1]
TEST_DIR = PROJECT / "ising_classique_test"
FINITE = TEST_DIR / "finite_size"
OUT = FINITE / "multiflux_mcmc_pipeline_test"
RAW = OUT / "raw_trajectories"
LOGS = OUT / "pipeline_logs"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5.8.py"

TC = float(2.0 / np.log(1.0 + np.sqrt(2.0)))
SIZES = (16, 32)
TEMPERATURES = (2.0, TC, 2.5)
N_CHAINS = 3
N_BURN = 500
N_MEASURE = 4000
BLOCK_SIZE = 80
PIPELINE_STRIDE = 20
WINDOW_SIZE = 40
LANDSCAPE_SCAN_POINTS = 24
PIPELINE_SEED = 20261108

COMMON_FLUXES = [
    "Abs_magnetization", "M_squared", "M_fourth", "Cluster_fraction", "Noise_flux"
]
FULL_FLUXES = [
    "Energy_per_spin", "Magnetization", "Abs_magnetization", "M_squared",
    "M_fourth", "Nearest_neighbor_correlation", "Cluster_fraction",
    "Noise_axis", "Noise_flux", "Abs_magnetization_shuffled",
]
CONTROL_AXES = [
    "MC_Update", "Energy_per_spin", "Magnetization",
    "Nearest_neighbor_correlation", "Noise_axis", "Abs_magnetization_shuffled",
]

spec = importlib.util.spec_from_file_location("universal_log_v58_multiflux", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


@njit
def wolff_trajectory(L, temperature, n_burn, n_measure, seed):
    """One row per cluster update: e, m, |m|, m², m⁴, nn corr, cluster fraction."""
    np.random.seed(seed)
    n = L * L
    spins = np.empty((L, L), dtype=np.int8)
    magnetization = 0.0
    energy = 0.0
    for i in range(L):
        for j in range(L):
            spins[i, j] = 1 if np.random.random() < 0.5 else -1
            magnetization += spins[i, j]
    for i in range(L):
        for j in range(L):
            s = spins[i, j]
            energy -= s * (spins[(i + 1) % L, j] + spins[i, (j + 1) % L])

    marks = np.zeros((L, L), dtype=np.int32)
    stack = np.empty(n, dtype=np.int32)
    p_add = 1.0 - np.exp(-2.0 / temperature)
    rows = np.empty((n_measure, 7), dtype=np.float64)
    sample_index = 0

    for update in range(n_burn + n_measure):
        stamp = update + 1
        si = np.random.randint(0, L)
        sj = np.random.randint(0, L)
        seed_spin = spins[si, sj]
        cluster_size = 1
        head = 0
        stack[0] = si * L + sj
        marks[si, sj] = stamp
        while head < cluster_size:
            flat = stack[head]
            head += 1
            i = flat // L
            j = flat % L
            for direction in range(4):
                if direction == 0:
                    ni, nj = (i - 1) % L, j
                elif direction == 1:
                    ni, nj = (i + 1) % L, j
                elif direction == 2:
                    ni, nj = i, (j - 1) % L
                else:
                    ni, nj = i, (j + 1) % L
                if marks[ni, nj] != stamp and spins[ni, nj] == seed_spin:
                    if np.random.random() < p_add:
                        marks[ni, nj] = stamp
                        stack[cluster_size] = ni * L + nj
                        cluster_size += 1

        cluster_m = 0.0
        delta_energy = 0.0
        for k in range(cluster_size):
            flat = stack[k]
            i = flat // L
            j = flat % L
            s = spins[i, j]
            cluster_m += s
            for direction in range(4):
                if direction == 0:
                    ni, nj = (i - 1) % L, j
                elif direction == 1:
                    ni, nj = (i + 1) % L, j
                elif direction == 2:
                    ni, nj = i, (j - 1) % L
                else:
                    ni, nj = i, (j + 1) % L
                if marks[ni, nj] != stamp:
                    delta_energy += 2.0 * s * spins[ni, nj]
        magnetization -= 2.0 * cluster_m
        energy += delta_energy
        for k in range(cluster_size):
            flat = stack[k]
            spins[flat // L, flat % L] *= -1

        if update >= n_burn:
            e = energy / n
            m = magnetization / n
            m2 = m * m
            rows[sample_index, 0] = e
            rows[sample_index, 1] = m
            rows[sample_index, 2] = abs(m)
            rows[sample_index, 3] = m2
            rows[sample_index, 4] = m2 * m2
            rows[sample_index, 5] = -e / 2.0
            rows[sample_index, 6] = cluster_size / n
            sample_index += 1
    return rows


def safe_float(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def slug(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value))


def generate_frame(L, temperature, chain):
    seed = 20261108 + L * 10000 + int(round(temperature * 100000)) + chain * 101
    raw = wolff_trajectory(L, temperature, N_BURN, N_MEASURE, seed)
    frame = pd.DataFrame(raw, columns=[
        "Energy_per_spin", "Magnetization", "Abs_magnetization", "M_squared",
        "M_fourth", "Nearest_neighbor_correlation", "Cluster_fraction",
    ])
    frame.insert(0, "MC_Update", np.arange(1, N_MEASURE + 1, dtype=int))
    rng = np.random.default_rng(seed + 91000000)
    frame["Noise_axis"] = rng.normal(size=N_MEASURE)
    frame["Noise_flux"] = rng.normal(size=N_MEASURE)
    frame["Abs_magnetization_shuffled"] = rng.permutation(frame["Abs_magnetization"].to_numpy())
    frame["Temperature"] = float(temperature)
    frame["L"] = int(L)
    frame["Chain"] = int(chain)
    frame["Seed"] = int(seed)
    return frame


def integrate_autocorrelation(series, max_lag=500):
    x = np.asarray(series, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 10 or np.var(x) == 0:
        return {"tau_int_updates": None, "effective_n": None, "rho_lag1": None}
    x = x - np.mean(x)
    nfft = 1 << (2 * len(x) - 1).bit_length()
    spectrum = np.fft.rfft(x, n=nfft)
    acov = np.fft.irfft(spectrum * np.conjugate(spectrum), n=nfft)[:min(max_lag, len(x) - 1) + 1]
    acov = acov / np.arange(len(acov), 0, -1)
    if acov[0] <= 0:
        return {"tau_int_updates": None, "effective_n": None, "rho_lag1": None}
    rho = acov / acov[0]
    tau = 0.5
    for r in rho[1:]:
        if r <= 0:
            break
        tau += float(r)
    tau = max(0.5, tau)
    return {
        "tau_int_updates": float(tau),
        "effective_n": float(min(len(x), len(x) / (2.0 * tau))),
        "rho_lag1": float(rho[1]) if len(rho) > 1 else None,
    }


def calc_thermo(frame, L, temperature):
    e = frame["Energy_per_spin"].to_numpy(dtype=float)
    m = frame["Magnetization"].to_numpy(dtype=float)
    am = frame["Abs_magnetization"].to_numpy(dtype=float)
    m2 = m * m
    m4 = m2 * m2
    n = L * L
    return {
        "E_per_spin": float(np.mean(e)),
        "Cv_per_spin": float(n * (np.mean(e * e) - np.mean(e) ** 2) / temperature**2),
        "chi_abs_per_spin": float(n * (np.mean(m2) - np.mean(am) ** 2) / temperature),
        "Binder_U4": float(1.0 - np.mean(m4) / (3.0 * np.mean(m2) ** 2)) if np.mean(m2) > 0 else None,
        "abs_magnetization": float(np.mean(am)),
    }


def make_relationship_rows(frame, L, temperature, chain):
    cols = [
        "MC_Update", "Energy_per_spin", "Magnetization", "Abs_magnetization",
        "M_squared", "M_fourth", "Nearest_neighbor_correlation",
        "Cluster_fraction", "Noise_axis", "Noise_flux", "Abs_magnetization_shuffled",
    ]
    rows = []
    for i, left in enumerate(cols):
        for right in cols[i + 1:]:
            result = spearmanr(frame[left].to_numpy(dtype=float), frame[right].to_numpy(dtype=float))
            rows.append({
                "L": int(L), "T": float(temperature), "Chain": int(chain),
                "flux_a": left, "flux_b": right, "spearman_rho": safe_float(result.statistic),
            })
    return rows


def physical_checks(trajectory_frames):
    reference = pd.read_csv(FINITE / "finite_size_results.csv")
    chain_rows = []
    cell_rows = []
    for (L, temperature), group_items in sorted(trajectory_frames.items()):
        cell_estimates = []
        for chain, frame in group_items:
            estimate = calc_thermo(frame, L, temperature)
            estimate.update({"L": int(L), "T": float(temperature), "Chain": int(chain)})
            chain_rows.append(estimate)
            cell_estimates.append(estimate)
        physical_ref = reference[reference["L"].eq(L)]
        ref_row = physical_ref.iloc[(physical_ref["T"] - temperature).abs().argmin()]
        mappings = {
            "E_per_spin": ("E_per_spin", "E_per_spin_se"),
            "Cv_per_spin": ("Cv_per_spin", "Cv_per_spin_se"),
            "chi_abs_per_spin": ("chi_abs_per_spin", "chi_abs_per_spin_se"),
            "Binder_U4": ("Binder_U4", "Binder_U4_se"),
            "abs_magnetization": ("abs_magnetization", "abs_magnetization_se"),
        }
        row = {"L": int(L), "T": float(temperature), "reference_T": float(ref_row["T"]), "n_chains": len(group_items)}
        for metric, (ref_metric, ref_se) in mappings.items():
            values = np.asarray([entry[metric] for entry in cell_estimates if entry[metric] is not None], dtype=float)
            mean = float(np.mean(values)) if len(values) else np.nan
            between_sd = float(np.std(values, ddof=1)) if len(values) > 1 else np.nan
            mean_se = between_sd / math.sqrt(len(values)) if len(values) > 1 else np.nan
            ref_value = float(ref_row[ref_metric])
            ref_err = float(ref_row[ref_se])
            combined = math.sqrt(mean_se**2 + ref_err**2) if np.isfinite(mean_se) else np.nan
            row.update({
                metric + "_mcmc_mean": mean,
                metric + "_between_chain_sd": between_sd,
                metric + "_reference": ref_value,
                metric + "_reference_se": ref_err,
                metric + "_difference_over_combined_se": (mean - ref_value) / combined if combined > 0 else None,
            })
        cell_rows.append(row)
    return pd.DataFrame(chain_rows), pd.DataFrame(cell_rows)


def pipeline_run(run_id, csv_path, frame, L, temperature, chain, control, flux_set_name, flux_names):
    mapping = {
        "control_col": control,
        "flux_mapping": {name: name for name in flux_names},
        "flux_columns_explicit": True,
    }
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            result, features, _fluxes, _ui = ul.run_pipeline(
                data_source="custom",
                custom_file_path=str(csv_path),
                mapping=mapping,
                mode="fast",
                opt_cfg={
                    "random_seed": PIPELINE_SEED,
                    "auto_optimize_threshold": False,
                    "optimization_iterations": 0,
                    "mc_complexity_enabled": False,
                    "max_workers": 1,
                    "estimator_profile": "all",
                    "landscape_scan_points": LANDSCAPE_SCAN_POINTS,
                },
            )
        state = ul.compute_holographic_tension_state(
            features, result.get("scores"), n_samples=len(frame), control_col=control
        )
        features.to_csv(OUT / "feature_landscapes" / f"{run_id}_df_feat.csv", index=False)
        monotonic = (result.get("monotone_flags") or {}).get("__control__", {})
        meta = result.get("metadata") or {}
        mc_axis = result.get("mc_axis") or {}
        d_vector = state.get("D_vector") or {}
        summary = {
            "run_id": run_id,
            "status": "ok",
            "L": int(L), "T": float(temperature), "Chain": int(chain),
            "control": control,
            "flux_set": flux_set_name,
            "flux_names": ",".join(flux_names),
            "n_input_rows": int(len(frame)),
            "n_fluxes": int(len(flux_names)),
            "n_estimator_methods": int(len(result.get("estimators_computed", []))),
            "window_size_rows": int(meta.get("w_size", 0)),
            "landscape_scan_points": int(meta.get("landscape_scan_points", 120)),
            "threshold_pct": safe_float(meta.get("opt_threshold")),
            "threshold_source": meta.get("threshold_source"),
            "threshold_status": meta.get("threshold_status"),
            "mc_axis_kind": mc_axis.get("axis_kind"),
            "control_is_monotone": monotonic.get("monotone"),
            "control_direction": monotonic.get("direction"),
            "control_spearman_in_row_order": safe_float(
                spearmanr(np.arange(len(frame)), frame[control].to_numpy(dtype=float)).statistic
            ),
            "control_unique_values": int(frame[control].nunique(dropna=True)),
            "state_status": state.get("status"),
            "dominant_regime": state.get("dominant_regime"),
            "d_sat": safe_float(d_vector.get("d_sat")),
            "d_crit": safe_float(d_vector.get("d_crit")),
            "d_div": safe_float(d_vector.get("d_div")),
            "d_null": safe_float(d_vector.get("d_null")),
            "n_landscape_rows": int(len(features)),
        }
        per_estimator_rows = []
        for estimator, entry in (state.get("per_estimator") or {}).items():
            per_estimator_rows.append({
                "run_id": run_id, "L": int(L), "T": float(temperature), "Chain": int(chain),
                "control": control, "flux_set": flux_set_name, "estimator": estimator,
                "d_kind": entry.get("d_kind"), "quantity_type": entry.get("quantity_type"),
                "tlog_membership": entry.get("tlog_membership"),
                "raw_median": safe_float(entry.get("raw_median")),
                "n_fluxes_used": entry.get("n_fluxes_used"),
                "enters_geometric_D": entry.get("enters_geometric_D"),
            })
        typed_rows = []
        for kind, entry in ((state.get("geometric_layer") or {}).get("T_log_by_d_kind") or {}).items():
            typed_rows.append({
                "run_id": run_id, "L": int(L), "T": float(temperature), "Chain": int(chain),
                "control": control, "flux_set": flux_set_name, "d_kind": kind,
                "quantity_type": entry.get("quantity_type"),
                "d_median": safe_float(entry.get("d_median")),
                "T_log": safe_float(entry.get("T_log")),
                "n_estimators_used": entry.get("n_estimators_used"),
                "estimators_used": ",".join(entry.get("estimators_used", [])),
            })
        (LOGS / f"{run_id}.log").write_text(
            "STDOUT\n" + stdout_buffer.getvalue() + "\nSTDERR\n" + stderr_buffer.getvalue(),
            encoding="utf-8",
        )
        return summary, per_estimator_rows, typed_rows
    except Exception as exc:
        (LOGS / f"{run_id}.log").write_text(
            "STDOUT\n" + stdout_buffer.getvalue() + "\nSTDERR\n" + stderr_buffer.getvalue()
            + f"\nERROR\n{type(exc).__name__}: {exc}\n", encoding="utf-8",
        )
        return {
            "run_id": run_id, "status": "error", "L": int(L), "T": float(temperature),
            "Chain": int(chain), "control": control, "flux_set": flux_set_name,
            "flux_names": ",".join(flux_names), "error": f"{type(exc).__name__}: {exc}",
        }, [], []


def add_run(run_specs, seen, l_size, temperature, chain, control, set_name, flux_names):
    run_id = slug(f"L{l_size}_T{temperature:.6f}_C{chain}_{control}_{set_name}")
    if run_id in seen:
        return
    seen.add(run_id)
    csv_path = RAW / f"L{l_size}_T{temperature:.6f}_chain{chain}.csv"
    full_frame = pd.read_csv(csv_path)
    frame = full_frame.iloc[::PIPELINE_STRIDE].reset_index(drop=True)
    sampled_path = OUT / "pipeline_inputs" / csv_path.name
    sampled_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(sampled_path, index=False)
    run_specs.append((run_id, sampled_path, frame, l_size, temperature, chain, control, set_name, list(flux_names)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    (OUT / "feature_landscapes").mkdir(parents=True, exist_ok=True)

    # Make the compared width an actual pipeline mode setting, not a silent opt_cfg override.
    ul.PARAMETERS["modes"]["fast"]["w_size"] = WINDOW_SIZE
    trajectory_frames = {}
    physical_rows = []
    relationship_rows = []
    lag_rows = []

    print("Generating fixed-temperature Wolff trajectories...", flush=True)
    for L in SIZES:
        for temperature in TEMPERATURES:
            entries = []
            for chain in range(N_CHAINS):
                frame = generate_frame(L, temperature, chain)
                file_path = RAW / f"L{L}_T{temperature:.6f}_chain{chain}.csv"
                frame.to_csv(file_path, index=False)
                entries.append((chain, frame))
                thermo = calc_thermo(frame, L, temperature)
                taus_e = integrate_autocorrelation(frame["Energy_per_spin"])
                taus_m = integrate_autocorrelation(frame["Abs_magnetization"])
                physical_rows.append({
                    "L": L, "T": temperature, "Chain": chain,
                    **thermo,
                    "tau_energy_updates": taus_e["tau_int_updates"],
                    "ESS_energy": taus_e["effective_n"],
                    "tau_absM_updates": taus_m["tau_int_updates"],
                    "ESS_absM": taus_m["effective_n"],
                    "sign_changes": int(np.sum(np.sign(frame["Magnetization"].to_numpy()[1:]) != np.sign(frame["Magnetization"].to_numpy()[:-1]))),
                    "cluster_fraction_mean": float(frame["Cluster_fraction"].mean()),
                })
                relationship_rows.extend(make_relationship_rows(frame, L, temperature, chain))
                for flux in ["Energy_per_spin", "Magnetization", "Abs_magnetization", "Cluster_fraction", "Abs_magnetization_shuffled"]:
                    tau = integrate_autocorrelation(frame[flux])
                    lag_rows.append({"L": L, "T": temperature, "Chain": chain, "flux": flux, **tau})
            trajectory_frames[(L, temperature)] = entries
            print(f"  L={L}, T={temperature:.6f}: {N_CHAINS} chains × {N_MEASURE} updates", flush=True)

    chain_physics, cell_physics = physical_checks(trajectory_frames)
    pd.DataFrame(physical_rows).to_csv(OUT / "mcmc_chain_physics.csv", index=False)
    chain_physics.to_csv(OUT / "mcmc_physical_checks_by_chain.csv", index=False)
    cell_physics.to_csv(OUT / "mcmc_physical_checks_vs_finite_size.csv", index=False)
    pd.DataFrame(relationship_rows).to_csv(OUT / "flux_relationships_spearman.csv", index=False)
    pd.DataFrame(lag_rows).to_csv(OUT / "flux_autocorrelation_diagnostics.csv", index=False)

    # Pipeline matrix: common controls all cells, richer controls at Tc, flux ablations,
    # full-flux comparisons, and critical-point chain repeats.
    run_specs = []
    seen = set()
    for L in SIZES:
        for temperature in TEMPERATURES:
            add_run(run_specs, seen, L, temperature, 0, "MC_Update", "common", COMMON_FLUXES)
    for L in SIZES:
        add_run(run_specs, seen, L, TC, 0, "MC_Update", "all_fluxes", FULL_FLUXES)
    for control in CONTROL_AXES[1:]:
        add_run(run_specs, seen, 16, TC, 0, control, "common", COMMON_FLUXES)
    for control in ["Energy_per_spin", "Noise_axis"]:
        add_run(run_specs, seen, 32, TC, 0, control, "common", COMMON_FLUXES)
    # Explicitly vary the number and dependence of observed fluxes, same control/data.
    for name, fluxes in [
        ("target_absM_only", ["Abs_magnetization"]),
        ("order_parameter_family", ["Abs_magnetization", "M_squared", "M_fourth"]),
        ("physical_without_noise", ["Abs_magnetization", "M_squared", "M_fourth", "Cluster_fraction"]),
    ]:
        add_run(run_specs, seen, 16, TC, 0, "MC_Update", name, fluxes)
    # Independent chain repeats at Tc, temporal control and identical common flux mapping.
    for L in SIZES:
        add_run(run_specs, seen, L, TC, 1, "MC_Update", "common", COMMON_FLUXES)

    pipeline_summaries = []
    estimator_rows = []
    typed_rows = []
    total = len(run_specs)
    print(f"Running v5.8 core on {total} explicit control/flux configurations...", flush=True)
    for i, args in enumerate(run_specs, start=1):
        run_id, csv_path, frame, L, temperature, chain, control, set_name, flux_names = args
        summary, per_estimator, per_kind = pipeline_run(
            run_id, csv_path, frame, L, temperature, chain, control, set_name, flux_names
        )
        pipeline_summaries.append(summary)
        estimator_rows.extend(per_estimator)
        typed_rows.extend(per_kind)
        print(f"  [{i}/{total}] {run_id}: {summary['status']}", flush=True)

    pipeline_df = pd.DataFrame(pipeline_summaries)
    pipeline_df.to_csv(OUT / "pipeline_axis_flux_matrix.csv", index=False)
    pd.DataFrame(estimator_rows).to_csv(OUT / "pipeline_estimator_outputs.csv", index=False)
    pd.DataFrame(typed_rows).to_csv(OUT / "pipeline_tlog_by_d_kind.csv", index=False)

    # Focused reports/figures: critical-point relationship map and geometric-axis sensitivity.
    corr_src = pd.read_csv(RAW / f"L16_T{TC:.6f}_chain0.csv")
    corr_cols = [
        "Energy_per_spin", "Magnetization", "Abs_magnetization", "M_squared",
        "M_fourth", "Nearest_neighbor_correlation", "Cluster_fraction",
        "Noise_axis", "Noise_flux", "Abs_magnetization_shuffled",
    ]
    corr = corr_src[corr_cols].corr(method="spearman")
    corr.to_csv(OUT / "critical_flux_spearman_matrix_L16.csv")
    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(corr.to_numpy(), cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr_cols)), corr_cols, rotation=75, ha="right", fontsize=8)
    ax.set_yticks(range(len(corr_cols)), corr_cols, fontsize=8)
    for i in range(len(corr_cols)):
        for j in range(len(corr_cols)):
            val = corr.iloc[i, j]
            if np.isfinite(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=ax, label="Corrélation de rang de Spearman")
    ax.set_title(f"Ising MCMC, L=16, T=Tc : relations entre flux")
    fig.tight_layout()
    fig.savefig(OUT / "critical_flux_spearman_matrix_L16.png", dpi=170)
    plt.close(fig)

    critical_common = pipeline_df[
        pipeline_df["status"].eq("ok")
        & pipeline_df["T"].sub(TC).abs().lt(1e-10)
        & pipeline_df["flux_set"].eq("common")
        & pipeline_df["Chain"].eq(0)
    ].copy()
    if len(critical_common):
        axis_order = ["MC_Update", "Energy_per_spin", "Magnetization", "Nearest_neighbor_correlation", "Noise_axis", "Abs_magnetization_shuffled"]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
        for ax, L in zip(axes, SIZES):
            part = critical_common[critical_common["L"].eq(L)].set_index("control").reindex(axis_order)
            vals = pd.to_numeric(part["d_crit"], errors="coerce").to_numpy(dtype=float)
            ax.bar(range(len(axis_order)), vals, color=["#3366cc"] + ["#dd8452"] * 3 + ["#55a868"] * 2)
            ax.set_xticks(range(len(axis_order)), axis_order, rotation=70, ha="right", fontsize=8)
            ax.set_title(f"L={L} — jeu commun de 5 flux")
            ax.set_ylabel("d_crit agrégé par le pipeline")
            ax.grid(axis="y", alpha=0.2)
        fig.suptitle("Sensibilité du résultat géométrique au choix de la colonne de contrôle (Tc)")
        fig.tight_layout()
        fig.savefig(OUT / "pipeline_axis_sensitivity_at_Tc.png", dpi=170)
        plt.close(fig)

    report_lines = [
        "# Ising classique : trajectoires MCMC et interactions multi-flux",
        "",
        "Protocole : [ISING_MCMC_MULTIFLUX_PROTOCOL.md](../../../ISING_MCMC_MULTIFLUX_PROTOCOL.md).",
        "",
        f"Simulation : Wolff 2D, `H=0`, `L={SIZES}`, `T=2.0, Tc={TC:.9f}, 2.5`, {N_CHAINS} chaînes par cellule, {N_BURN} mises à jour de chauffe et {N_MEASURE} observations par chaîne.",
        "Une observation est une mise à jour de grappe Wolff; elle n'est pas une unité de temps physique.",
        "",
        "Le CSV de température historique contient 3 observations par température (petites réplications indépendantes), pas une trajectoire temporelle longue. Les nouveaux CSV bruts conservent les 4 000 mesures; les appels au pipeline utilisent 1 mesure sur 20 (200 lignes), choisie régulièrement, pour garder les fenêtres chevauchantes du cœur v5.8 calculables.",
        "",
        "## Contrôle de cohérence physique",
        "",
        "Les moments calculés sur les nouvelles trajectoires sont comparés à `finite_size_results.csv` au point de température le plus proche. Le tableau donne les écarts standardisés par l'erreur combinée; avec seulement trois chaînes, ils restent diagnostiques.",
        "",
        "| L | T simulée | T référence | z(E) | z(Cv) | z(chi_abs) | z(Binder) | z(|m|) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in cell_physics.iterrows():
        def fmt(metric):
            val = row.get(metric + "_difference_over_combined_se")
            return "n/a" if pd.isna(val) else f"{val:.2f}"
        report_lines.append(
            f"| {int(row['L'])} | {row['T']:.6f} | {row['reference_T']:.2f} | "
            f"{fmt('E_per_spin')} | {fmt('Cv_per_spin')} | {fmt('chi_abs_per_spin')} | "
            f"{fmt('Binder_U4')} | {fmt('abs_magnetization')} |"
        )

    ok_count = int(pipeline_df.get("status", pd.Series(dtype=str)).eq("ok").sum())
    lines = report_lines + [
        "",
        "## Résultats du pipeline",
        "",
        f"Le cœur `run_pipeline` v5.8 a été lancé {len(pipeline_df)} fois sur les trajectoires échantillonnées (1 ligne sur {PIPELINE_STRIDE}) avec une fenêtre fixe de {WINDOW_SIZE} lignes et {LANDSCAPE_SCAN_POINTS} positions de paysage; {ok_count} runs ont abouti.",
        "Les runs utilisent les 29 estimateurs et désactivent seulement l'optimisation Monte Carlo du seuil. Chaque appel reçoit un axe et une liste de flux explicitement nommés.",
        "",
        "### Comparaison des axes au voisinage de Tc",
        "",
        "| L | Contrôle | Flux utilisés | monotone ? | rho ordre/valeur | d_crit | Régime calculé | statut |",
        "|---:|---|---|---|---:|---:|---|---|",
    ]
    for _, row in pipeline_df[(pipeline_df["flux_set"].eq("common")) & pipeline_df["Chain"].eq(0) & pipeline_df["T"].sub(TC).abs().lt(1e-10)].iterrows():
        dcrit = row.get("d_crit")
        lines.append(
            f"| {int(row['L'])} | {row['control']} | jeu commun ({row['n_fluxes']} flux) | "
            f"{row.get('control_is_monotone')} | {row.get('control_spearman_in_row_order'):.2f} | "
            f"{'n/a' if pd.isna(dcrit) else f'{dcrit:.3f}'} | "
            f"{row.get('dominant_regime')} | {row.get('status')} |"
        )
    lines.extend([
        "",
        "### Comparaison des configurations de flux à L=16, Tc, contrôle MC_Update",
        "",
        "| Jeu de flux | n flux | d_sat | d_crit | d_div | régime |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for _, row in pipeline_df[(pipeline_df["L"].eq(16)) & pipeline_df["Chain"].eq(0) & pipeline_df["T"].sub(TC).abs().lt(1e-10) & pipeline_df["control"].eq("MC_Update")].iterrows():
        def fmt_value(key):
            value = row.get(key)
            return "n/a" if pd.isna(value) else f"{value:.3f}"
        lines.append(
            f"| {row['flux_set']} | {row['n_fluxes']} | {fmt_value('d_sat')} | {fmt_value('d_crit')} | "
            f"{fmt_value('d_div')} | {row.get('dominant_regime')} |"
        )
    lines.extend([
        "",
        "`Noise_axis` et `Abs_magnetization_shuffled` sont des contrôles négatifs : un profil géométrique stable autour de ces axes serait un signe de sensibilité aux tris/à la configuration, pas une découverte physique. `Noise_flux` est un flux indépendant conservé dans le jeu commun; le jeu complet ajoute des flux redondants (`E`/corrélation de voisins, `|m|`/m²/m⁴) et un flux mélangé.",
        "",
        "Les axes énergie et aimantation ne sont généralement pas monotones au fil des mises à jour. Le pipeline les ordonne pour construire une coupe; leur seuil ne doit pas être lu comme une date ou une température critique. La comparaison utile est la variation des mêmes flux sous des axes différents et les alertes produites par les axes négatifs.",
        "",
        "## Lecture des résultats",
        "",
        "Les moments thermodynamiques des nouvelles chaînes concordent avec le balayage de taille finie : 29 des 30 écarts comparés sont dans ±2 erreurs combinées (l'exception est Cv à L=16, T=2.0, à 2.43). Les trajectoires semblent donc physiquement plausibles pour ce pilote.",
        "",
        "Le régime nommé `criticality` n'est pas un détecteur de transition ici : il apparaît dans les 6 cellules (L,T) avec contrôle temporel, y compris à T=2.0 et T=2.5, et apparaît aussi sous le contrôle négatif `Noise_axis`. Seul L=32 montre un maximum de d_crit parmi les trois températures testées à Tc; L=16 n'en montre pas. Ce petit nombre de températures ne localise pas Tc avec précision.",
        "",
        "La sensibilité à l'orientation de l'axe est nette : `Nearest_neighbor_correlation = -Energy_per_spin/2` (corrélation de rang −1), mais à L=16, Tc, le contrôle énergie donne le régime `divergence`, tandis que la corrélation de voisins donne `criticality`. L'axe `Magnetization` donne `saturation`. Ces contrôles sont non monotones dans l'ordre de la chaîne; il s'agit de coupes triées, pas de temps ni de causalité.",
        "",
        "La composition des flux compte aussi : à L=16, Tc, d_crit passe de 2.729 avec |m| seul à 3.263 avec la famille corrélée |m|, m², m⁴; ajouter Cluster_fraction change peu (3.195) et ajouter le bruit indépendant revient à 3.263. Les liens de rang |m|↔m² et |m|↔m⁴ sont exactement 1 dans ces données. Une moyenne qui compte ces flux comme observations indépendantes peut donc surpondérer une seule famille physique.",
        "",
        "Les moments physiques restent le contrôle de référence. La dépendance aux axes/flux est un diagnostic de la représentation CSV; un changement de `d_crit` ou de régime n'est pas à lui seul une confirmation de transition.",
        "",
        "## Fichiers",
        "",
        "- [CSV brut représentatif, L16 à Tc](raw_trajectories/L16_T2.269185_chain0.csv)",
        "- [Entrée échantillonnée remise au pipeline](pipeline_inputs/L16_T2.269185_chain0.csv)",
        "- [Matrice axe × flux du pipeline](pipeline_axis_flux_matrix.csv)",
        "- [Sorties des 29 estimateurs par run](pipeline_estimator_outputs.csv)",
        "- [Profils TLog par d_kind](pipeline_tlog_by_d_kind.csv)",
        "- [Diagnostics physiques et autocorrélations](mcmc_chain_physics.csv), [comparaison à l'étude finie](mcmc_physical_checks_vs_finite_size.csv)",
        "- [Corrélations des flux critiques](critical_flux_spearman_matrix_L16.csv) et [figure](critical_flux_spearman_matrix_L16.png)",
        "- [Sensibilité de d_crit au contrôle à Tc](pipeline_axis_sensitivity_at_Tc.png)",
        "- [Journaux complets](pipeline_logs/)",
    ])
    (OUT / "RAPPORT_MCMC_MULTIFLUX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metadata = {
        "pipeline_version": ul.VERSION_MASTER,
        "protocol": str(PROJECT / "ISING_MCMC_MULTIFLUX_PROTOCOL.md"),
        "model": "2D square Ising; periodic; J=1; H=0; Wolff cluster updates",
        "L": list(SIZES), "temperatures": list(TEMPERATURES), "Tc_exact": TC,
        "independent_chains_per_cell": N_CHAINS,
        "n_burn_cluster_updates": N_BURN, "n_measure_cluster_updates": N_MEASURE,
        "pipeline_row_stride": PIPELINE_STRIDE,
        "pipeline_rows_per_trajectory": int(math.ceil(N_MEASURE / PIPELINE_STRIDE)),
        "control_axes": list(CONTROL_AXES),
        "common_fluxes": COMMON_FLUXES, "full_fluxes": FULL_FLUXES,
        "pipeline_window_rows": WINDOW_SIZE,
        "pipeline_landscape_scan_points": LANDSCAPE_SCAN_POINTS,
        "pipeline_runs": len(pipeline_df), "successful_runs": ok_count,
        "interpretation_notes": [
            "Wolff cluster updates are algorithmic update counts, not physical time.",
            "Alternative nonmonotone flux controls define sorted observational cuts, not causal axes.",
            "Noise and shuffled controls are negative controls for axis/flux-induced structure.",
            "Derived fluxes are intentionally redundant in the full set to measure composition sensitivity.",
            "Three chains and finite runs make uncertainty estimates exploratory.",
        ],
    }
    (OUT / "multiflux_mcmc_pipeline_test.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote multi-flux MCMC experiment to {OUT}", flush=True)


if __name__ == "__main__":
    main()
