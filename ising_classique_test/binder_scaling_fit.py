"""Joint Binder-cumulant finite-size scaling fits and block bootstrap."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent / "finite_size"
FIT_WINDOW = (2.22, 2.32)
OMEGA = 2.0
N_BOOTSTRAP = 500
BOOTSTRAP_SEED = 20261108
TC_EXACT = float(2.0 / np.log(1.0 + np.sqrt(2.0)))
NU_EXACT = 1.0

def scaling_prediction(params, L, T, corrected):
    tc, nu, u_star, a1, a2, a3 = params[:6]
    x = (T - tc) * L ** (1.0 / nu)
    f = u_star + a1 * x + a2 * x**2 + a3 * x**3
    if corrected:
        c0, c1 = params[6:8]
        f = f + L ** (-OMEGA) * (c0 + c1 * x)
    return f

def fit_model(L, T, U, sigma, corrected, start=None):
    n_poly = 8 if corrected else 6
    if start is None:
        start = [2.269, 1.0, 0.61, -0.05, -0.01, -0.001]
        if corrected:
            start += [0.1, -0.25]
    lower = [2.20, 0.5, 0.4, -10.0, -10.0, -10.0]
    upper = [2.34, 1.8, 0.8, 10.0, 10.0, 10.0]
    if corrected:
        lower += [-10.0, -10.0]
        upper += [10.0, 10.0]
    start = np.asarray(start[:n_poly], dtype=float)
    result = least_squares(
        lambda q: (scaling_prediction(q, L, T, corrected) - U) / sigma,
        start, bounds=(lower, upper), x_scale="jac", max_nfev=5000,
    )
    chi2 = float(np.sum(result.fun**2))
    n_obs, k = len(U), len(result.x)
    dof = n_obs - k
    return {
        "params": result.x,
        "success": bool(result.success),
        "message": str(result.message),
        "n_observations": int(n_obs),
        "n_parameters": int(k),
        "degrees_of_freedom": int(dof),
        "chi2": chi2,
        "reduced_chi2": chi2 / dof,
        "AIC": chi2 + 2.0 * k,
        "BIC": chi2 + k * np.log(n_obs),
    }

def interval(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {"n_valid": 0, "se": None, "ci95_low": None, "ci95_high": None}
    return {"n_valid": int(len(values)),
            "se": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            "ci95_low": float(np.percentile(values, 2.5)),
            "ci95_high": float(np.percentile(values, 97.5))}

def main():
    sizes = [8, 12, 16, 24, 32, 48, 64]
    results = pd.read_csv(ROOT / "finite_size_results.csv")
    raw = np.load(ROOT / "finite_size_block_moments.npz")
    block_moments = raw["moments"]
    stored_sizes = raw["sizes"].astype(int).tolist()
    temperatures = raw["temperatures"].astype(float)
    if stored_sizes != sizes:
        raise ValueError(f"Unexpected size list in block moments: {stored_sizes}")
    t_mask = (temperatures >= FIT_WINDOW[0]) & (temperatures <= FIT_WINDOW[1])
    t_fit = temperatures[t_mask]
    li_indices = np.arange(len(sizes))
    ti_indices = np.flatnonzero(t_mask)
    rows = []
    for li, L in enumerate(sizes):
        for ti, T in zip(ti_indices, t_fit):
            row = results[(results["L"] == L) & np.isclose(results["T"], T)].iloc[0]
            rows.append({"L": float(L), "T": float(T), "U": float(row["Binder_U4"]),
                         "sigma": float(row["Binder_U4_se"])})
    fit_data = pd.DataFrame(rows)
    Ld, Td, Ud = (fit_data[k].to_numpy(float) for k in ("L", "T", "U"))
    sigma = np.maximum(fit_data["sigma"].to_numpy(float), 1e-4)
    uncorrected = fit_model(Ld, Td, Ud, sigma, False)
    corrected = fit_model(Ld, Td, Ud, sigma, True)

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    boot_params = {"uncorrected": [], "corrected": []}
    fit_success = {"uncorrected": 0, "corrected": 0}
    for replicate in range(N_BOOTSTRAP):
        bU = []
        for li, L in enumerate(sizes):
            for ti in ti_indices:
                blocks = block_moments[li, ti]
                selected = rng.integers(0, len(blocks), size=len(blocks))
                moments = blocks[selected].mean(axis=0)
                m2, m4 = moments[3], moments[4]
                bU.append(1.0 - m4 / (3.0 * m2 * m2) if m2 > 0 else np.nan)
        bU = np.asarray(bU, dtype=float)
        for name, base_fit, is_corrected in (
            ("uncorrected", uncorrected, False), ("corrected", corrected, True)
        ):
            try:
                boot_fit = fit_model(Ld, Td, bU, sigma, is_corrected,
                                     start=base_fit["params"])
                if boot_fit["success"] and np.all(np.isfinite(boot_fit["params"])):
                    boot_params[name].append(boot_fit["params"])
                    fit_success[name] += 1
            except (ValueError, FloatingPointError, np.linalg.LinAlgError):
                continue
        if (replicate + 1) % 100 == 0:
            print(f"Bootstrap fit {replicate + 1}/{N_BOOTSTRAP}", flush=True)

    parameter_names = ["Tc", "nu", "U_star", "a1", "a2", "a3"]
    corrected_names = parameter_names + ["c0_Lminus2", "c1_Lminus2_x"]
    fits = {}
    for name, fit, labels in (("uncorrected", uncorrected, parameter_names),
                              ("corrected", corrected, corrected_names)):
        samples = np.asarray(boot_params[name], dtype=float)
        intervals = {}
        for i, label in enumerate(labels):
            intervals[label] = interval(samples[:, i]) if samples.size else interval([])
        fits[name] = {
            "parameters": {label: float(fit["params"][i]) for i, label in enumerate(labels)},
            "bootstrap_95": intervals,
            "bootstrap_successes": int(fit_success[name]),
            "n_bootstrap": N_BOOTSTRAP,
            "fit_statistics": {k: fit[k] for k in ("n_observations", "n_parameters",
                                                    "degrees_of_freedom", "chi2",
                                                    "reduced_chi2", "AIC", "BIC")},
            "optimizer_success": fit["success"],
        }
    comparison = {
        "delta_AIC_corrected_minus_uncorrected": corrected["AIC"] - uncorrected["AIC"],
        "delta_BIC_corrected_minus_uncorrected": corrected["BIC"] - uncorrected["BIC"],
        "interpretation": "Negative favors the corrected model; positive favors the uncorrected model.",
    }
    document = {
        "model": "Binder scaling U4=F((T-Tc)L^(1/nu))",
        "fit_window_T": list(FIT_WINDOW),
        "correction": {"form": "L^-omega * (c0 + c1*x)", "omega_fixed": OMEGA},
        "scaling_function": "cubic polynomial in x",
        "exact_reference": {"Tc": TC_EXACT, "nu": NU_EXACT},
        "uncorrected": fits["uncorrected"],
        "corrected": fits["corrected"],
        "model_comparison": comparison,
        "bootstrap": {"replicates": N_BOOTSTRAP,
                       "method": "resample the Wolff measurement blocks independently at each (L,T); refit both models"},
        "limitations": [
            "The correction exponent omega is fixed at 2; uncertainty in omega is not included.",
            "The cubic scaling function and chosen temperature window are modeling choices.",
            "Bootstrap intervals describe Monte Carlo sampling uncertainty, not all finite-size/model-form uncertainty.",
        ],
    }
    out_json = ROOT / "binder_joint_scaling.json"
    out_json.write_text(json.dumps(document, indent=2), encoding="utf-8")
    sample_rows = []
    for name, values in boot_params.items():
        labels = parameter_names if name == "uncorrected" else corrected_names
        for j, row in enumerate(values):
            sample_rows.append({"replicate": j + 1, "model": name,
                                **{label: float(row[i]) for i, label in enumerate(labels)}})
    pd.DataFrame(sample_rows).to_csv(ROOT / "binder_joint_scaling_bootstrap.csv", index=False)
    pd.DataFrame([
        {"model": "uncorrected", **fits["uncorrected"]["parameters"],
         **{f"{k}_ci95_low": v["ci95_low"] for k,v in fits["uncorrected"]["bootstrap_95"].items()},
         **{f"{k}_ci95_high": v["ci95_high"] for k,v in fits["uncorrected"]["bootstrap_95"].items()},
         **fits["uncorrected"]["fit_statistics"]},
        {"model": "corrected_Lminus2", **fits["corrected"]["parameters"],
         **{f"{k}_ci95_low": v["ci95_low"] for k,v in fits["corrected"]["bootstrap_95"].items()},
         **{f"{k}_ci95_high": v["ci95_high"] for k,v in fits["corrected"]["bootstrap_95"].items()},
         **fits["corrected"]["fit_statistics"]},
    ]).to_csv(ROOT / "binder_joint_scaling_fits.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
    colors = plt.cm.viridis(np.linspace(0.06, 0.94, len(sizes)))
    x_grid = np.linspace(-3.4, 3.4, 300)
    for ax, fit, is_corrected, title in (
        (axes[0], uncorrected, False, "Without correction"),
        (axes[1], corrected, True, r"With $L^{-2}$ correction"),
    ):
        for color, L in zip(colors, sizes):
            g = fit_data[fit_data["L"] == L]
            params = fit["params"]
            x = (g["T"].to_numpy() - params[0]) * L ** (1.0 / params[1])
            y_plot = g["U"].to_numpy().copy()
            if is_corrected:
                y_plot -= L**(-OMEGA) * (params[6] + params[7] * x)
            ax.scatter(x, y_plot, s=22, alpha=0.8, color=color, label=f"L={L}")
        params = fit["params"]
        curve = params[2] + params[3]*x_grid + params[4]*x_grid**2 + params[5]*x_grid**3
        ax.plot(x_grid, curve, color="black", linewidth=2, label="F(x)")
        ax.set_title(title)
        ax.set_xlabel(r"$x=(T-T_c)L^{1/\nu}$")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, ncol=2)
    axes[0].set_ylabel(r"Corrected Binder cumulant $U_4$")
    fig.suptitle("Joint Binder finite-size scaling collapse")
    fig.tight_layout()
    fig.savefig(ROOT / "binder_joint_scaling_collapse.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps({"uncorrected": fits["uncorrected"],
                      "corrected": fits["corrected"],
                      "model_comparison": comparison}, indent=2))
    print(f"Wrote joint scaling results to {ROOT}")

if __name__ == "__main__":
    main()
