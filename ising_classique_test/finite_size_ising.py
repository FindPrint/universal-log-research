"""Finite-size 2D square-lattice Ising study using Wolff cluster updates.

All energies are per spin. J = k_B = H = 1 (H=0 for this study).
The simulation is independent of UNIVERSAL_LOG; it generates physical
observables needed to compare finite-size behavior with the exact Tc.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from numba import njit

HERE = Path(__file__).resolve().parent
OUT = HERE / "finite_size"
OUT.mkdir(parents=True, exist_ok=True)
SIZES = [8, 12, 16, 24, 32, 48, 64]
TEMPERATURES = np.round(np.arange(1.90, 2.651, 0.01), 3)
N_BURN = 500
N_SAMPLES = 4000
N_CHAINS = 3
BLOCK_SIZE = 80
N_BOOTSTRAP = 500
TC_EXACT = float(2.0 / np.log(1.0 + np.sqrt(2.0)))

@njit
def wolff_block_moments(L, temperature, n_burn, n_samples, block_size, seed):
    """Return block means of e, e^2, m, m^2, m^4 and |m|."""
    np.random.seed(seed)
    n = L * L
    spins = np.empty((L, L), dtype=np.int8)
    for i in range(L):
        for j in range(L):
            spins[i, j] = 1 if np.random.random() < 0.5 else -1
    marks = np.zeros((L, L), dtype=np.int32)
    stack = np.empty(n, dtype=np.int32)
    magnetization = 0.0
    energy = 0.0
    for i in range(L):
        for j in range(L):
            s = spins[i, j]
            magnetization += s
            energy -= s * (spins[(i + 1) % L, j] + spins[i, (j + 1) % L])
    p_add = 1.0 - np.exp(-2.0 / temperature)
    n_blocks = n_samples // block_size
    blocks = np.zeros((n_blocks, 6), dtype=np.float64)
    sample_index = 0
    for update in range(n_burn + n_samples):
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
            b = sample_index // block_size
            blocks[b, 0] += e
            blocks[b, 1] += e * e
            blocks[b, 2] += m
            blocks[b, 3] += m * m
            blocks[b, 4] += m * m * m * m
            blocks[b, 5] += abs(m)
            sample_index += 1
    return blocks / block_size

def observables(moment_means, L, temperature):
    e, e2, m, m2, m4, abs_m = moment_means
    n = L * L
    cv = n * max(0.0, e2 - e * e) / (temperature * temperature)
    chi = n * max(0.0, m2 - m * m) / temperature
    # At H=0, finite-size chains tunnel between +M and -M. The connected
    # |M|-susceptibility removes that global sign-switching contribution.
    chi_abs = n * max(0.0, m2 - abs_m * abs_m) / temperature
    binder = 1.0 - e4_ratio(m4, m2)
    return {"E_per_spin": e, "Cv_per_spin": cv, "chi_per_spin": chi,
            "chi_abs_per_spin": chi_abs,
            "Binder_U4": binder, "abs_magnetization": abs_m}

def e4_ratio(m4, m2):
    return m4 / (3.0 * m2 * m2) if m2 > 0.0 else np.nan

def estimate_with_block_error(blocks, L, temperature):
    means = blocks.mean(axis=0)
    estimate = observables(means, L, temperature)
    keys = list(estimate)
    jack = {key: [] for key in keys}
    n_blocks = len(blocks)
    if n_blocks > 1:
        total = blocks.sum(axis=0)
        for b in range(n_blocks):
            leave_one_out = (total - blocks[b]) / (n_blocks - 1)
            vals = observables(leave_one_out, L, temperature)
            for key in keys:
                jack[key].append(vals[key])
    for key in keys:
        values = np.asarray(jack[key], dtype=float)
        estimate[key + "_se"] = (float(np.sqrt((n_blocks - 1) / n_blocks *
                                                np.sum((values - values.mean()) ** 2)))
                                  if len(values) > 1 else np.nan)
    estimate["n_blocks"] = int(n_blocks)
    return estimate

def crossing_for_pair(left, right, temperatures, tc):
    diff = left - right
    candidates = []
    for i in range(len(temperatures) - 1):
        if diff[i] == 0.0:
            candidates.append((float(temperatures[i]), float(left[i])))
        elif diff[i] * diff[i + 1] < 0.0:
            frac = -diff[i] / (diff[i + 1] - diff[i])
            t_cross = temperatures[i] + frac * (temperatures[i + 1] - temperatures[i])
            u_cross = left[i] + frac * (left[i + 1] - left[i])
            candidates.append((float(t_cross), float(u_cross)))
    near = [x for x in candidates if abs(x[0] - tc) <= 0.20]
    return min(near, key=lambda x: abs(x[0] - tc)) if near else None

def curve_metrics(block_means, L, temperatures):
    e, e2 = block_means[:, 0], block_means[:, 1]
    m, m2, m4, abs_m = (block_means[:, 2], block_means[:, 3],
                         block_means[:, 4], block_means[:, 5])
    n = L * L
    cv = n * np.maximum(0.0, e2 - e * e) / (temperatures * temperatures)
    chi_abs = n * np.maximum(0.0, m2 - abs_m * abs_m) / temperatures
    binder = 1.0 - m4 / (3.0 * np.maximum(m2 * m2, 1e-30))
    return {"Cv_per_spin": cv, "chi_abs_per_spin": chi_abs,
            "Binder_U4": binder, "abs_magnetization": abs_m}

def percentile_interval(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {"n_valid": 0, "se": None, "ci95_low": None, "ci95_high": None}
    return {"n_valid": int(len(values)), "se": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            "ci95_low": float(np.percentile(values, 2.5)),
            "ci95_high": float(np.percentile(values, 97.5))}

def bootstrap_fss(block_moments, sizes, temperatures, tc, n_bootstrap=500, seed=861107):
    """Resample independent measurement blocks within each (L,T) cell."""
    rng = np.random.default_rng(seed)
    n_sizes, n_t, n_blocks, _ = block_moments.shape
    crossing_samples = {(a, b): {"t": [], "u": []} for a, b in zip(sizes[:-1], sizes[1:])}
    peak_samples = {L: {k: [] for k in ("T_Cv_peak", "Cv_peak", "T_chi_abs_peak", "chi_abs_peak")}
                    for L in sizes}
    gamma_samples, beta_samples, tc_chi_intercepts, cv_log_slopes = [], [], [], []
    t_grid = np.asarray(temperatures, dtype=float)
    for _ in range(n_bootstrap):
        curves = {}
        chi_peaks, cv_peaks, abs_m_tc = [], [], []
        t_chi_peaks = []
        for li, L in enumerate(sizes):
            means = np.empty((n_t, 6), dtype=float)
            for ti in range(n_t):
                selected = rng.integers(0, n_blocks, size=n_blocks)
                means[ti] = block_moments[li, ti, selected, :].mean(axis=0)
            curve = curve_metrics(means, L, t_grid)
            curves[L] = curve
            cv_i = int(np.argmax(curve["Cv_per_spin"]))
            chi_i = int(np.argmax(curve["chi_abs_per_spin"]))
            peak_samples[L]["T_Cv_peak"].append(float(t_grid[cv_i]))
            peak_samples[L]["Cv_peak"].append(float(curve["Cv_per_spin"][cv_i]))
            peak_samples[L]["T_chi_abs_peak"].append(float(t_grid[chi_i]))
            peak_samples[L]["chi_abs_peak"].append(float(curve["chi_abs_per_spin"][chi_i]))
            t_chi_peaks.append(float(t_grid[chi_i]))
            chi_peaks.append(float(curve["chi_abs_per_spin"][chi_i]))
            cv_peaks.append(float(curve["Cv_per_spin"][cv_i]))
            abs_m_tc.append(float(np.interp(tc, t_grid, curve["abs_magnetization"])))
        sizes_arr = np.asarray(sizes, dtype=float)
        gamma_samples.append(float(np.polyfit(np.log(sizes_arr), np.log(chi_peaks), 1)[0]))
        cv_log_slopes.append(float(np.polyfit(np.log(sizes_arr), cv_peaks, 1)[0]))
        beta_samples.append(float(-np.polyfit(np.log(sizes_arr), np.log(abs_m_tc), 1)[0]))
        tc_chi_intercepts.append(float(np.polyfit(1.0 / sizes_arr, t_chi_peaks, 1)[1]))
        for (a, b), samples in crossing_samples.items():
            result = crossing_for_pair(curves[a]["Binder_U4"], curves[b]["Binder_U4"], t_grid, tc)
            if result is not None:
                samples["t"].append(result[0])
                samples["u"].append(result[1])
    crossing_ci = {}
    for pair, samples in crossing_samples.items():
        crossing_ci[pair] = {"T_cross_bootstrap": percentile_interval(samples["t"]),
                             "Binder_at_cross_bootstrap": percentile_interval(samples["u"])}
    peak_ci = {L: {k: percentile_interval(v) for k, v in values.items()}
               for L, values in peak_samples.items()}
    return {
        "replicates": int(n_bootstrap),
        "binder_crossings": crossing_ci,
        "peak_intervals": peak_ci,
        "gamma_over_nu": percentile_interval(gamma_samples),
        "beta_over_nu": percentile_interval(beta_samples),
        "cv_peak_vs_lnL_slope": percentile_interval(cv_log_slopes),
        "chi_peak_linear_1_over_L_intercept": percentile_interval(tc_chi_intercepts),
    }

def main():
    records = []
    n_blocks_total = N_CHAINS * (N_SAMPLES // BLOCK_SIZE)
    block_moments = np.empty((len(SIZES), len(TEMPERATURES), n_blocks_total, 6), dtype=np.float64)
    for li, L in enumerate(SIZES):
        for ti, temperature in enumerate(TEMPERATURES):
            chain_blocks = []
            for chain in range(N_CHAINS):
                seed = 20261107 + li * 100000 + ti * 1000 + chain
                chain_blocks.append(wolff_block_moments(
                    L, float(temperature), N_BURN, N_SAMPLES, BLOCK_SIZE, seed
                ))
            blocks = np.vstack(chain_blocks)
            block_moments[li, ti] = blocks
            stats = estimate_with_block_error(blocks, L, float(temperature))
            records.append({"L": L, "T": float(temperature), **stats})
        print(f"Finished L={L}: {len(TEMPERATURES)} temperatures, "
              f"{N_CHAINS} chains, {N_SAMPLES} samples/chain.", flush=True)
    results = pd.DataFrame(records).sort_values(["L", "T"]).reset_index(drop=True)
    results.to_csv(OUT / "finite_size_results.csv", index=False)
    np.savez_compressed(OUT / "finite_size_block_moments.npz",
                        moments=block_moments, sizes=np.asarray(SIZES),
                        temperatures=np.asarray(TEMPERATURES))
    peak_rows = []
    for L, group in results.groupby("L"):
        cv_row = group.loc[group["Cv_per_spin"].idxmax()]
        chi_row = group.loc[group["chi_abs_per_spin"].idxmax()]
        abs_m_tc = float(np.interp(TC_EXACT, group["T"], group["abs_magnetization"]))
        peak_rows.append({"L": int(L), "T_Cv_peak": float(cv_row["T"]),
                          "Cv_peak": float(cv_row["Cv_per_spin"]),
                          "Cv_peak_se": float(cv_row["Cv_per_spin_se"]),
                          "T_chi_abs_peak": float(chi_row["T"]),
                          "chi_abs_peak": float(chi_row["chi_abs_per_spin"]),
                          "chi_abs_peak_se": float(chi_row["chi_abs_per_spin_se"]),
                          "abs_magnetization_at_Tc": abs_m_tc,
                          "Binder_at_Tc": float(np.interp(TC_EXACT, group["T"], group["Binder_U4"]))})
    peaks = pd.DataFrame(peak_rows).sort_values("L")
    binder = {int(L): group["Binder_U4"].to_numpy() for L, group in results.groupby("L")}
    boot = bootstrap_fss(block_moments, SIZES, TEMPERATURES, TC_EXACT,
                         n_bootstrap=N_BOOTSTRAP, seed=861107)
    crossings = []
    for a, b in zip(SIZES[:-1], SIZES[1:]):
        result = crossing_for_pair(binder[a], binder[b], TEMPERATURES, TC_EXACT)
        ci = boot["binder_crossings"][(a, b)]
        t_ci, u_ci = ci["T_cross_bootstrap"], ci["Binder_at_cross_bootstrap"]
        crossings.append({"L1": a, "L2": b,
                          "T_cross": result[0] if result else None,
                          "Binder_at_cross": result[1] if result else None,
                          "delta_Tc": result[0] - TC_EXACT if result else None,
                          "T_cross_bootstrap_se": t_ci["se"],
                          "T_cross_ci95_low": t_ci["ci95_low"],
                          "T_cross_ci95_high": t_ci["ci95_high"],
                          "Binder_cross_ci95_low": u_ci["ci95_low"],
                          "Binder_cross_ci95_high": u_ci["ci95_high"],
                          "bootstrap_n_valid": t_ci["n_valid"]})
    crossings_df = pd.DataFrame(crossings)
    crossings_df.to_csv(OUT / "binder_crossings.csv", index=False)
    for row in peak_rows:
        ci = boot["peak_intervals"][row["L"]]
        for key, suffix in (("T_Cv_peak", "ci95"), ("Cv_peak", "ci95"),
                            ("T_chi_abs_peak", "ci95"), ("chi_abs_peak", "ci95")):
            row[key + "_boot_low"] = ci[key]["ci95_low"]
            row[key + "_boot_high"] = ci[key]["ci95_high"]
    peaks = pd.DataFrame(peak_rows).sort_values("L")
    peaks.to_csv(OUT / "finite_size_peaks.csv", index=False)
    chi_scaling_fit = np.polyfit(np.log(peaks["L"].to_numpy(float)),
                                 np.log(peaks["chi_abs_peak"].to_numpy(float)), 1)
    mag_scaling_fit = np.polyfit(np.log(peaks["L"].to_numpy(float)),
                                 np.log(peaks["abs_magnetization_at_Tc"].to_numpy(float)), 1)
    log_l = np.log(peaks["L"].to_numpy(float))
    chi_log = np.log(peaks["chi_abs_peak"].to_numpy(float))
    mag_log = np.log(peaks["abs_magnetization_at_Tc"].to_numpy(float))
    cv_logl_fit = np.polyfit(log_l, peaks["Cv_peak"].to_numpy(float), 1)
    def fit_r_squared(y, coeff):
        predicted = np.polyval(coeff, log_l)
        return float(1.0 - np.sum((y - predicted) ** 2) / np.sum((y - np.mean(y)) ** 2))
    tc_chi_naive = float(np.polyfit(1.0 / peaks["L"].to_numpy(float),
                                    peaks["T_chi_abs_peak"].to_numpy(float), 1)[1])
    summary = {
        "model": "2D square-lattice ferromagnetic Ising, periodic boundary, H=0",
        "algorithm": "Wolff single-cluster updates",
        "units": {"J": 1.0, "k_B": 1.0, "field": 0.0},
        "sizes": SIZES,
        "temperature_range": [float(TEMPERATURES[0]), float(TEMPERATURES[-1])],
        "temperature_step": float(TEMPERATURES[1] - TEMPERATURES[0]),
        "thermalization_cluster_updates_per_chain_and_T": N_BURN,
        "measurement_cluster_updates_per_chain_and_T": N_SAMPLES,
        "independent_chains": N_CHAINS,
        "block_size": BLOCK_SIZE,
        "exact_Tc_infinite_lattice": TC_EXACT,
        "susceptibility_peak_1_over_L_linear_extrapolation": tc_chi_naive,
        "susceptibility_peak_extrapolation_delta_Tc": tc_chi_naive - TC_EXACT,
        "gamma_over_nu_from_chi_peak_loglog": float(chi_scaling_fit[0]),
        "gamma_over_nu_fit_r_squared": fit_r_squared(chi_log, chi_scaling_fit),
        "gamma_over_nu_bootstrap_95": boot["gamma_over_nu"],
        "Cv_peak_vs_lnL_slope": float(cv_logl_fit[0]),
        "Cv_peak_vs_lnL_bootstrap_95": boot["cv_peak_vs_lnL_slope"],
        "beta_over_nu_from_abs_magnetization_at_Tc_loglog": float(-mag_scaling_fit[0]),
        "beta_over_nu_fit_r_squared": fit_r_squared(mag_log, mag_scaling_fit),
        "beta_over_nu_bootstrap_95": boot["beta_over_nu"],
        "chi_peak_linear_1_over_L_bootstrap_95": boot["chi_peak_linear_1_over_L_intercept"],
        "binder_crossings_adjacent_sizes": crossings,
        "block_bootstrap": {"replicates": N_BOOTSTRAP,
                            "method": "resample measurement blocks within each (L,T) cell"},
        "notes": [
            "Cv/N = L^2 Var(e)/T^2; conventional chi/N = L^2 Var(m)/T.",
            "For zero-field pseudocritical peaks, chi_abs/N = L^2(<m^2>-<|m|>^2)/T suppresses whole-lattice +/- tunneling.",
            "Binder U4 = 1 - <m^4>/(3 <m^2>^2); periodic-square reference near Tc is about 0.6107.",
            "Block-jackknife errors estimate pointwise Monte Carlo uncertainty; block-bootstrap intervals quantify peak/crossing/scaling uncertainty.",
            "Power-law fits over finite sizes are descriptive consistency checks, not precision exponent estimates.",
            "This is a physics validation harness; UNIVERSAL_LOG itself does not perform finite-size scaling."
        ]
    }
    (OUT / "finite_size_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    fig, axes = plt.subplots(1, 3, figsize=(19, 5.4))
    colors = plt.cm.viridis(np.linspace(0.06, 0.94, len(SIZES)))
    for color, L in zip(colors, SIZES):
        g = results[results["L"] == L]
        axes[0].plot(g["T"], g["Cv_per_spin"], color=color, label=f"L={L}")
        axes[1].plot(g["T"], g["chi_abs_per_spin"], color=color, label=f"L={L}")
        axes[2].plot(g["T"], g["Binder_U4"], color=color, label=f"L={L}")
    for ax in axes:
        ax.axvline(TC_EXACT, color="black", linestyle="--", linewidth=1.2,
                   label=r"$T_c$ exact" if ax is axes[0] else None)
        ax.set_xlabel("Temperature T (J/kB units)")
        ax.set_xlim(2.05, 2.50)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel(r"$C_V/N$")
    axes[0].set_title("Specific heat")
    axes[1].set_ylabel(r"$\chi_{|m|}/N$")
    axes[1].set_title("Connected susceptibility (absolute-magnetization definition)")
    axes[2].set_ylabel(r"$U_4=1-\langle m^4\rangle/(3\langle m^2\rangle^2)$")
    axes[2].set_title("Binder cumulant")
    for ax in axes:
        ax.legend(fontsize=8, ncol=2)
    fig.suptitle("Finite-size 2D Ising study (Wolff, periodic boundaries)")
    fig.tight_layout()
    fig.savefig(OUT / "finite_size_ising.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("\nPeaks by size:")
    print(peaks[["L", "T_Cv_peak", "Cv_peak", "T_chi_abs_peak", "chi_abs_peak", "Binder_at_Tc"]].to_string(index=False, float_format=lambda x: f"{x:.5f}"))
    print("\nBinder crossings with block-bootstrap 95% intervals:")
    print(crossings_df.to_string(index=False, float_format=lambda x: f"{x:.5f}"))
    print(f"\nExact Tc={TC_EXACT:.8f}; gamma/nu={chi_scaling_fit[0]:.5f}; beta/nu={-mag_scaling_fit[0]:.5f}")
    print(f"Outputs: {OUT}")

if __name__ == "__main__":
    main()
