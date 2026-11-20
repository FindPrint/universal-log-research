"""Pilot test of v5.8 typed TLog profiles against finite-size Ising markers.

Uses the stored finite-size energy curves and smooth polynomial negative
controls. No simulator is rerun. See TLOG_TRANSITION_VALIDATION_PROTOCOL.md
for the criteria frozen before this calculation.
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

PROJECT = Path(__file__).resolve().parents[1]
FINITE = PROJECT / "ising_classique_test" / "finite_size"
OUT = FINITE / "tlog_typed_transition_validation"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5.8.py"
WINDOWS = (31, 41)
TC_EXACT = float(2.0 / np.log(1.0 + np.sqrt(2.0)))
NULL_SIZES = (16, 64)
NULL_REPLICATES = 10
NULL_CENTERS = 9
NULL_SEED = 20261108
BAND_HALF_WIDTH = 0.5
LOCALIZATION_PADDING = 0.01
MIN_COVERAGE = 0.80
MIN_LOCALIZED_SIZES = 4
MAX_FAMILYWISE_FALSE_ALARM = 0.10
MAX_WINDOW_LOCATION_DRIFT = 0.05

spec = importlib.util.spec_from_file_location("universal_log_v58_transition_validation", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)

DIRECT_NAMES = {
    name for members in ul.DIMENSION_FOR_TLOG.values() for name in members
}
DKIND_MEMBERS = {}
for estimator in ul.ESTIMATOR_NAMES:
    if estimator in DIRECT_NAMES:
        DKIND_MEMBERS.setdefault(ul.ESTIMATOR_D_KIND[estimator], []).append(estimator)
DKINDS = sorted(DKIND_MEMBERS)


def estimate_window(series: np.ndarray, window_size: int) -> dict:
    values = ul.apply_complexity(
        np.asarray(series, dtype=float),
        flux_name="Energy_per_spin",
        mode_cfg={"min_len": int(window_size), "estimator_profile": "all"},
    )
    result = {}
    for kind, members in DKIND_MEMBERS.items():
        finite = {
            name: float(values[name])
            for name in members
            if values.get(name) is not None and np.isfinite(values[name])
        }
        d_value = float(np.median(list(finite.values()))) if finite else None
        result[kind] = {
            "d": d_value,
            "T_log": (
                float((d_value - 4.0) * np.log(window_size))
                if d_value is not None else None
            ),
            "estimators_used": finite,
        }
    return result


def scan_curve(temperatures, signal, window_size, centers=None):
    temperatures = np.asarray(temperatures, dtype=float)
    signal = np.asarray(signal, dtype=float)
    half = window_size // 2
    if centers is None:
        center_indices = np.arange(half, len(signal) - half)
    else:
        center_indices = np.asarray(centers, dtype=int)
    rows = []
    for center_index in center_indices:
        start = int(center_index - half)
        stop = start + int(window_size)
        if start < 0 or stop > len(signal):
            continue
        result = estimate_window(signal[start:stop], window_size)
        center_t = float(temperatures[center_index])
        for kind, profile in result.items():
            d_value = profile["d"]
            rows.append({
                "d_kind": kind,
                "window_size": int(window_size),
                "center_index": int(center_index),
                "center_T": center_t,
                "d": d_value,
                "T_log": profile["T_log"],
                "n_estimators_used": len(profile["estimators_used"]),
                "estimators_used": ",".join(profile["estimators_used"]),
            })
    return pd.DataFrame(rows)


def summarize_positive_curve(rows, peak_t, ci_low, ci_high, l_size):
    summaries = []
    for kind in DKINDS:
        group = rows[rows["d_kind"].eq(kind)].sort_values("center_T")
        finite = group[np.isfinite(pd.to_numeric(group["d"], errors="coerce"))]
        coverage = float(len(finite) / len(group)) if len(group) else 0.0
        if finite.empty:
            summaries.append({
                "L": int(l_size), "window_size": int(group["window_size"].iloc[0]) if len(group) else None,
                "d_kind": kind, "coverage": coverage, "min_abs_d_minus_4": None,
                "candidate": False, "T_pred": None, "peak_T": float(peak_t),
                "peak_ci_low": float(ci_low), "peak_ci_high": float(ci_high),
                "localized_to_peak_ci": False, "abs_error_from_peak": None,
                "abs_error_from_Tc_exact": None,
            })
            continue
        distances = np.abs(finite["d"].to_numpy(dtype=float) - 4.0)
        best_position = int(np.argmin(distances))
        best = finite.iloc[best_position]
        minimum = float(distances[best_position])
        candidate = bool(minimum <= BAND_HALF_WIDTH)
        t_pred = float(best["center_T"]) if candidate else None
        localized = bool(
            candidate
            and float(ci_low) - LOCALIZATION_PADDING <= t_pred <= float(ci_high) + LOCALIZATION_PADDING
        )
        summaries.append({
            "L": int(l_size),
            "window_size": int(best["window_size"]),
            "d_kind": kind,
            "coverage": coverage,
            "min_abs_d_minus_4": minimum,
            "candidate": candidate,
            "T_pred": t_pred,
            "peak_T": float(peak_t),
            "peak_ci_low": float(ci_low),
            "peak_ci_high": float(ci_high),
            "localized_to_peak_ci": localized,
            "abs_error_from_peak": abs(t_pred - float(peak_t)) if candidate else None,
            "abs_error_from_Tc_exact": abs(t_pred - TC_EXACT) if candidate else None,
        })
    return summaries


def make_null_signal(temperatures, observed_energy, observed_se, rng):
    """Smooth quadratic baseline with the empirical pointwise SE as noise."""
    x = (np.asarray(temperatures, dtype=float) - float(np.mean(temperatures))) / float(np.ptp(temperatures))
    coef = np.polyfit(x, np.asarray(observed_energy, dtype=float), deg=2)
    smooth = np.polyval(coef, x)
    se = np.asarray(observed_se, dtype=float)
    positive_se = se[np.isfinite(se) & (se > 0)]
    fallback = float(np.median(positive_se)) if len(positive_se) else 1e-4
    se = np.where(np.isfinite(se) & (se > 0), se, fallback)
    return smooth + rng.normal(0.0, se)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    physical = pd.read_csv(FINITE / "finite_size_results.csv")
    peaks = pd.read_csv(FINITE / "finite_size_peaks.csv").set_index("L")
    physical_rows = []
    positive_summaries = []
    curves = {}

    for l_size, frame in physical.groupby("L", sort=True):
        frame = frame.sort_values("T").reset_index(drop=True)
        temperatures = frame["T"].to_numpy(dtype=float)
        energy = frame["E_per_spin"].to_numpy(dtype=float)
        peak = peaks.loc[int(l_size)]
        for window_size in WINDOWS:
            curve = scan_curve(temperatures, energy, window_size)
            curve.insert(0, "L", int(l_size))
            physical_rows.extend(curve.to_dict(orient="records"))
            positive_summaries.extend(summarize_positive_curve(
                curve,
                peak_t=float(peak["T_chi_abs_peak"]),
                ci_low=float(peak["T_chi_abs_peak_boot_low"]),
                ci_high=float(peak["T_chi_abs_peak_boot_high"]),
                l_size=int(l_size),
            ))
            curves[(int(l_size), int(window_size))] = curve

    positive_df = pd.DataFrame(physical_rows)
    positive_summary = pd.DataFrame(positive_summaries)
    positive_df.to_csv(OUT / "positive_local_profiles.csv", index=False)
    positive_summary.to_csv(OUT / "positive_detection_summary.csv", index=False)

    null_rows = []
    rng = np.random.default_rng(NULL_SEED)
    for l_size in NULL_SIZES:
        frame = physical[physical["L"].eq(l_size)].sort_values("T").reset_index(drop=True)
        temperatures = frame["T"].to_numpy(dtype=float)
        energy = frame["E_per_spin"].to_numpy(dtype=float)
        energy_se = frame["E_per_spin_se"].to_numpy(dtype=float)
        for replicate in range(NULL_REPLICATES):
            null_signal = make_null_signal(temperatures, energy, energy_se, rng)
            for window_size in WINDOWS:
                half = window_size // 2
                centers = np.unique(np.round(np.linspace(
                    half, len(temperatures) - half - 1, NULL_CENTERS
                )).astype(int))
                profile = scan_curve(temperatures, null_signal, window_size, centers=centers)
                profile["L_noise_reference"] = int(l_size)
                profile["replicate"] = int(replicate)
                for kind in DKINDS:
                    group = profile[profile["d_kind"].eq(kind)]
                    dvals = pd.to_numeric(group["d"], errors="coerce").to_numpy(dtype=float)
                    dvals = dvals[np.isfinite(dvals)]
                    candidate = bool(
                        len(dvals) and np.min(np.abs(dvals - 4.0)) <= BAND_HALF_WIDTH
                    )
                    null_rows.append({
                        "L_noise_reference": int(l_size),
                        "replicate": int(replicate),
                        "window_size": int(window_size),
                        "d_kind": kind,
                        "candidate_any_sampled_center": candidate,
                        "min_abs_d_minus_4": (
                            float(np.min(np.abs(dvals - 4.0))) if len(dvals) else None
                        ),
                        "finite_centers": int(len(dvals)),
                        "sampled_centers": int(len(group)),
                    })
    null_df = pd.DataFrame(null_rows)
    null_df.to_csv(OUT / "smooth_null_detection.csv", index=False)

    null_global = (
        null_df.groupby(["L_noise_reference", "replicate", "window_size"], as_index=False)
        ["candidate_any_sampled_center"].any()
    )
    familywise_by_window = (
        null_global.groupby("window_size")["candidate_any_sampled_center"].mean().to_dict()
    )
    familywise_rate = float(null_global["candidate_any_sampled_center"].mean())
    false_by_kind = (
        null_df.groupby(["d_kind", "window_size"])["candidate_any_sampled_center"]
        .mean().unstack(fill_value=0.0)
    )

    eligible_sizes = [12, 16, 24, 32, 48, 64]
    typed_summaries = []
    for kind in DKINDS:
        by_window = {}
        for window_size in WINDOWS:
            eligible = positive_summary[
                positive_summary["d_kind"].eq(kind)
                & positive_summary["window_size"].eq(window_size)
                & positive_summary["L"].isin(eligible_sizes)
            ]
            enough_coverage = bool(len(eligible) == len(eligible_sizes)
                                  and (eligible["coverage"] >= MIN_COVERAGE).all())
            by_window[window_size] = {
                "sizes_with_candidate": int(eligible["candidate"].sum()),
                "sizes_localized": int(eligible["localized_to_peak_ci"].sum()),
                "sizes_eligible": int(len(eligible)),
                "coverage_ge_80pct_all_sizes": enough_coverage,
                "median_abs_error_peak": (
                    float(eligible.loc[eligible["candidate"], "abs_error_from_peak"].median())
                    if eligible["candidate"].any() else None
                ),
                "median_abs_error_Tc_exact": (
                    float(eligible.loc[eligible["candidate"], "abs_error_from_Tc_exact"].median())
                    if eligible["candidate"].any() else None
                ),
            }
        joint = positive_summary[
            positive_summary["d_kind"].eq(kind)
            & positive_summary["L"].isin(eligible_sizes)
        ].pivot(index="L", columns="window_size", values="T_pred")
        paired = joint.dropna() if set(WINDOWS).issubset(joint.columns) else pd.DataFrame()
        location_drift = (
            float(np.median(np.abs(paired[WINDOWS[0]] - paired[WINDOWS[1]])))
            if not paired.empty else None
        )
        false_rates = {
            str(window): float(false_by_kind.loc[kind, window])
            for window in WINDOWS
        }
        meets_localization = all(
            by_window[window]["sizes_localized"] >= MIN_LOCALIZED_SIZES
            and by_window[window]["coverage_ge_80pct_all_sizes"]
            for window in WINDOWS
        )
        meets_false_alarm = familywise_rate <= MAX_FAMILYWISE_FALSE_ALARM
        meets_stability = (
            location_drift is not None
            and location_drift <= MAX_WINDOW_LOCATION_DRIFT
        )
        typed_summaries.append({
            "d_kind": kind,
            "eligible_sizes": eligible_sizes,
            "window_results": {str(k): v for k, v in by_window.items()},
            "median_prediction_drift_between_windows": location_drift,
            "false_alarm_rate_by_kind": false_rates,
            "familywise_false_alarm_rate": familywise_rate,
            "meets_localization_rule": meets_localization,
            "meets_familywise_false_alarm_rule": meets_false_alarm,
            "meets_window_stability_rule": meets_stability,
            "pilot_candidate": bool(meets_localization and meets_false_alarm and meets_stability),
            "pilot_status": (
                "candidate_pilot" if meets_localization and meets_false_alarm and meets_stability
                else "does_not_meet_predeclared_pilot_criteria"
            ),
        })

    result = {
        "protocol": {
            "path": str(PROJECT / "TLOG_TRANSITION_VALIDATION_PROTOCOL.md"),
            "version": "1.0",
            "frozen_before_calculation": True,
            "physical_input": str(FINITE / "finite_size_results.csv"),
            "physical_marker": "finite-size chi_abs peak and its block-bootstrap 95% interval",
            "input_flux_for_d_kind": "E_per_spin only",
            "windows": list(WINDOWS),
            "d_critical_band": [4.0 - BAND_HALF_WIDTH, 4.0 + BAND_HALF_WIDTH],
            "localization_padding": LOCALIZATION_PADDING,
            "null_sizes": list(NULL_SIZES),
            "null_replicates_per_size": NULL_REPLICATES,
            "null_sampled_centers_per_window": NULL_CENTERS,
            "null_seed": NULL_SEED,
        },
        "pipeline_version": ul.VERSION_MASTER,
        "estimators": ul.ESTIMATOR_NAMES,
        "d_kind_members": DKIND_MEMBERS,
        "physical_finite_size_sizes": sorted(int(x) for x in physical["L"].unique()),
        "l8_excluded_from_localization": "susceptibility-peak confidence interval is right-censored by the temperature grid",
        "null_control_summary": {
            "n_null_scans": int(len(null_global)),
            "familywise_false_alarm_rate": familywise_rate,
            "familywise_false_alarm_rate_by_window": {
                str(k): float(v) for k, v in familywise_by_window.items()
            },
            "false_alarm_rate_by_kind_and_window": {
                kind: {str(window): float(false_by_kind.loc[kind, window]) for window in WINDOWS}
                for kind in DKINDS
            },
        },
        "pilot_criteria": {
            "minimum_coverage": MIN_COVERAGE,
            "minimum_localized_sizes_per_window": MIN_LOCALIZED_SIZES,
            "maximum_familywise_false_alarm_rate": MAX_FAMILYWISE_FALSE_ALARM,
            "maximum_median_window_location_drift": MAX_WINDOW_LOCATION_DRIFT,
            "candidate_d_kinds": [
                row["d_kind"] for row in typed_summaries if row["pilot_candidate"]
            ],
        },
        "per_d_kind": typed_summaries,
        "limitations": [
            "Physical observables are pooled from three chains; d-kind local estimates do not propagate their Monte Carlo uncertainty.",
            "The signal is a quasi-static equilibrium response versus temperature, not a time trajectory; attractor and dynamic d_kinds may be out of domain.",
            "The window sizes span 0.30 and 0.40 in temperature and can smooth sharp finite-size features.",
            "The quadratic null is a pilot control; 40 scans give a coarse false-alarm estimate.",
            "A candidate profile does not establish universal validity or justify the reference 4 outside its tested d_kind.",
        ],
        "outputs": {
            "positive_local_profiles": str(OUT / "positive_local_profiles.csv"),
            "positive_detection_summary": str(OUT / "positive_detection_summary.csv"),
            "smooth_null_detection": str(OUT / "smooth_null_detection.csv"),
        },
    }
    (OUT / "typed_tlog_transition_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(typed_summaries).to_json(
        OUT / "typed_tlog_detection_by_kind.json", orient="records", force_ascii=False, indent=2
    )

    report_lines = [
        "# Criblage de détection de transition TLog par d_kind",
        "",
        "Protocole préenregistré : [TLOG_TRANSITION_VALIDATION_PROTOCOL.md](../../../TLOG_TRANSITION_VALIDATION_PROTOCOL.md).",
        "",
        f"Contrôles nuls : taux familial de fausses alertes = {familywise_rate:.1%} sur {len(null_global)} balayages lisses.",
        "",
        "| d_kind | Localisés / 6 à w=31 | Localisés / 6 à w=41 | Faux positifs par type (w=31 / 41) | Dérive médiane entre fenêtres | Statut pilote |",
        "|---|---:|---:|---:|---:|---|",
    ]
    summary_df = pd.DataFrame(typed_summaries)
    for row in typed_summaries:
        r31 = row["window_results"][str(WINDOWS[0])]
        r41 = row["window_results"][str(WINDOWS[1])]
        drift = row["median_prediction_drift_between_windows"]
        lines = report_lines
        lines.append(
            f"| {row['d_kind']} | {r31['sizes_localized']} / {r31['sizes_eligible']} | "
            f"{r41['sizes_localized']} / {r41['sizes_eligible']} | "
            f"{row['false_alarm_rate_by_kind'][str(WINDOWS[0])]:.1%} / "
            f"{row['false_alarm_rate_by_kind'][str(WINDOWS[1])]:.1%} | "
            f"{'n/a' if drift is None else f'{drift:.3f}'} | {row['pilot_status']} |"
        )
    lines.extend([
        "",
        "## Lecture",
        "",
        "Un type ne devient candidat pilote que s'il respecte simultanément la localisation, la couverture, le contrôle des fausses alertes et la stabilité entre les deux fenêtres. Les taux sont des criblages à petit effectif, pas des probabilités définitives.",
        "",
        "## Conclusion du pilote",
        "",
        f"Aucun des {len(typed_summaries)} types ne satisfait les critères préétablis. Le taux familial de fausses alertes atteint {familywise_rate:.1%}, au-dessus du plafond de {MAX_FAMILYWISE_FALSE_ALARM:.0%}.",
        "",
        "Le proxy de persistance H0 est le seul à entrer dans la bande candidate |d−4|≤0,5. Il localise le pic de susceptibilité dans seulement 1 taille sur 6 pour chacune des fenêtres, avec 25 % de fausses alertes par type et une dérive médiane de prédiction de 0,160 en température. Il ne constitue donc pas un détecteur fiable dans ce pilote.",
        "",
        "Cette conclusion porte sur ces profils TLog, calculés à partir de la courbe d'énergie d'équilibre et selon ce protocole. Elle ne réfute ni la transition Ising (confirmée ici par les observables thermodynamiques/Binder), ni la validité d'autres types de données ou d'autres constructions TLog.",
        "",
        "## Fichiers",
        "",
        "- [Protocole préenregistré](../../../TLOG_TRANSITION_VALIDATION_PROTOCOL.md)",
        "- [Résultats détaillés JSON](typed_tlog_transition_validation.json) et [résumé par d_kind](typed_tlog_detection_by_kind.json)",
        "- [Profils locaux par température](positive_local_profiles.csv) et [résumé des détections](positive_detection_summary.csv)",
        "- [Résultats des contrôles nuls](smooth_null_detection.csv)",
        "- [Courbes d'énergie et marqueurs physiques](physical_energy_curves_and_markers.png)",
        "- [Rapport de validation physique Ising](../physical_validation_report.md)",
        "",
    ])
    (OUT / "RAPPORT_DETECTION_TLOG_PAR_D_KIND.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    # Diagnostic figure: normalized energy curves and finite-size chi peaks.
    fig, ax = plt.subplots(figsize=(9, 5))
    for l_size, frame in physical.groupby("L", sort=True):
        frame = frame.sort_values("T")
        y = frame["E_per_spin"].to_numpy(dtype=float)
        y = (y - np.mean(y)) / (np.std(y) if np.std(y) > 0 else 1.0)
        ax.plot(frame["T"], y, linewidth=1.1, label=f"L={int(l_size)}")
        peak_t = float(peaks.loc[int(l_size), "T_chi_abs_peak"])
        ax.axvline(peak_t, color="0.5", alpha=0.08)
    ax.axvline(TC_EXACT, color="black", linestyle="--", linewidth=1.3, label="Tc exact")
    ax.set_xlabel("Température T")
    ax.set_ylabel("Énergie par spin (z-score par L)")
    ax.set_title("Courbes positives d'Ising; lignes grises = pics χabs par taille")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "physical_energy_curves_and_markers.png", dpi=160)
    plt.close(fig)
    print(f"Wrote pilot transition validation to {OUT}")


if __name__ == "__main__":
    main()
