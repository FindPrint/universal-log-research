"""Exploratory individual-estimator audit for the v5.8 TLog Ising pilot.

This is an extension of the pre-registered d_kind analysis. The 21 outputs
declared dimension-valued by DIMENSION_FOR_TLOG are tested individually using
the current d=4 convention. The 8 non-dimensional signatures are analyzed
descriptively and are never assigned T_log or compared with 4.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
FINITE = PROJECT / "ising_classique_test" / "finite_size"
OUT = FINITE / "tlog_individual_estimator_audit"
BASE_SCRIPT = PROJECT / "ising_classique_test" / "typed_tlog_transition_validation.py"
WINDOWS = (31, 41)
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
ELIGIBLE_SIZES = [12, 16, 24, 32, 48, 64]

spec = importlib.util.spec_from_file_location("typed_tlog_pilot_base", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
ul = base.ul

DIMENSIONAL = sorted({
    estimator for members in ul.DIMENSION_FOR_TLOG.values() for estimator in members
})
SIGNATURES = [name for name in ul.ESTIMATOR_NAMES if name not in DIMENSIONAL]
TC_EXACT = float(2.0 / np.log(1.0 + np.sqrt(2.0)))


def as_finite(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def scan(temperatures, signal, window_size, centers=None):
    temperatures = np.asarray(temperatures, dtype=float)
    signal = np.asarray(signal, dtype=float)
    half = window_size // 2
    if centers is None:
        centers = np.arange(half, len(signal) - half)
    rows = []
    for center in np.asarray(centers, dtype=int):
        start = int(center - half)
        stop = start + int(window_size)
        if start < 0 or stop > len(signal):
            continue
        values = ul.apply_complexity(
            signal[start:stop],
            flux_name="Energy_per_spin",
            mode_cfg={"min_len": int(window_size), "estimator_profile": "all"},
        )
        for estimator in ul.ESTIMATOR_NAMES:
            value = as_finite(values.get(estimator))
            dimensional = estimator in DIMENSIONAL
            rows.append({
                "estimator": estimator,
                "d_kind": ul.ESTIMATOR_D_KIND[estimator],
                "quantity_type": ul.D_KIND_REGISTRY[ul.ESTIMATOR_D_KIND[estimator]]["quantity_type"],
                "tlog_eligible": dimensional,
                "window_size": int(window_size),
                "center_index": int(center),
                "center_T": float(temperatures[center]),
                "value": value,
                "d": value if dimensional else None,
                "T_log": float((value - 4.0) * np.log(window_size)) if dimensional and value is not None else None,
            })
    return pd.DataFrame(rows)


def sampled_centers(n, window_size):
    half = window_size // 2
    return np.unique(np.round(np.linspace(half, n - half - 1, NULL_CENTERS)).astype(int))


def signature_slope_detection(group, ci_low, ci_high):
    group = group.sort_values("center_T")
    valid = group[np.isfinite(pd.to_numeric(group["value"], errors="coerce"))]
    if len(valid) < 2:
        return {"slope_peak_T": None, "max_abs_slope": None, "localized": False, "coverage": len(valid) / len(group) if len(group) else 0.0}
    t = valid["center_T"].to_numpy(dtype=float)
    y = valid["value"].to_numpy(dtype=float)
    slopes = np.abs(np.diff(y) / np.diff(t))
    if not len(slopes) or not np.isfinite(slopes).any():
        return {"slope_peak_T": None, "max_abs_slope": None, "localized": False, "coverage": len(valid) / len(group)}
    idx = int(np.nanargmax(slopes))
    peak_t = float((t[idx] + t[idx + 1]) / 2.0)
    localized = bool(ci_low - LOCALIZATION_PADDING <= peak_t <= ci_high + LOCALIZATION_PADDING)
    return {
        "slope_peak_T": peak_t,
        "max_abs_slope": float(slopes[idx]),
        "localized": localized,
        "coverage": float(len(valid) / len(group)),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    physical = pd.read_csv(FINITE / "finite_size_results.csv")
    peaks = pd.read_csv(FINITE / "finite_size_peaks.csv").set_index("L")
    positive_parts = []
    for l_size, frame in physical.groupby("L", sort=True):
        frame = frame.sort_values("T").reset_index(drop=True)
        temperatures = frame["T"].to_numpy(dtype=float)
        energy = frame["E_per_spin"].to_numpy(dtype=float)
        for window in WINDOWS:
            profile = scan(temperatures, energy, window)
            profile.insert(0, "L", int(l_size))
            positive_parts.append(profile)
    positive = pd.concat(positive_parts, ignore_index=True)
    positive.to_csv(OUT / "individual_local_profiles.csv", index=False)

    # Dimension-valued estimators: apply the existing T_log convention one by one.
    dimensional_profiles = positive[positive["tlog_eligible"]].copy()
    peak_rows = []
    for (estimator, l_size, window), group in dimensional_profiles.groupby(["estimator", "L", "window_size"]):
        peak = peaks.loc[int(l_size)]
        values = pd.to_numeric(group["d"], errors="coerce")
        finite = group.loc[np.isfinite(values)].copy()
        coverage = float(len(finite) / len(group)) if len(group) else 0.0
        if finite.empty:
            minimum, prediction, candidate, localized = None, None, False, False
        else:
            dist = np.abs(finite["d"].to_numpy(dtype=float) - 4.0)
            idx = int(np.argmin(dist))
            minimum = float(dist[idx])
            prediction = float(finite.iloc[idx]["center_T"]) if minimum <= BAND_HALF_WIDTH else None
            candidate = bool(prediction is not None)
            localized = bool(candidate and peak["T_chi_abs_peak_boot_low"] - LOCALIZATION_PADDING <= prediction <= peak["T_chi_abs_peak_boot_high"] + LOCALIZATION_PADDING)
        peak_rows.append({
            "estimator": estimator,
            "d_kind": ul.ESTIMATOR_D_KIND[estimator],
            "L": int(l_size),
            "window_size": int(window),
            "coverage": coverage,
            "min_abs_d_minus_4": minimum,
            "candidate": candidate,
            "T_pred": prediction,
            "peak_T": float(peak["T_chi_abs_peak"]),
            "peak_ci_low": float(peak["T_chi_abs_peak_boot_low"]),
            "peak_ci_high": float(peak["T_chi_abs_peak_boot_high"]),
            "localized": localized,
            "abs_error_from_peak": abs(prediction - float(peak["T_chi_abs_peak"])) if candidate else None,
            "abs_error_from_Tc_exact": abs(prediction - TC_EXACT) if candidate else None,
        })
    dimension_detection = pd.DataFrame(peak_rows)
    dimension_detection.to_csv(OUT / "individual_dimension_detection.csv", index=False)

    # Eight signatures have no d=4/T_log. Their steepest local change is descriptive only.
    signature_rows = []
    for (estimator, l_size, window), group in positive[positive["estimator"].isin(SIGNATURES)].groupby(["estimator", "L", "window_size"]):
        temps = physical[physical["L"].eq(int(l_size))].sort_values("T")["T"].to_numpy(dtype=float)
        centers = sampled_centers(len(temps), int(window))
        sampled = group[group["center_index"].isin(centers)]
        peak = peaks.loc[int(l_size)]
        det = signature_slope_detection(sampled, float(peak["T_chi_abs_peak_boot_low"]), float(peak["T_chi_abs_peak_boot_high"]))
        signature_rows.append({
            "estimator": estimator,
            "d_kind": ul.ESTIMATOR_D_KIND[estimator],
            "L": int(l_size),
            "window_size": int(window),
            **det,
            "peak_T": float(peak["T_chi_abs_peak"]),
            "peak_ci_low": float(peak["T_chi_abs_peak_boot_low"]),
            "peak_ci_high": float(peak["T_chi_abs_peak_boot_high"]),
        })
    signature_detection = pd.DataFrame(signature_rows)
    signature_detection.to_csv(OUT / "signature_shape_localization.csv", index=False)

    # Smooth nulls use the same 9 centers as the signature shape diagnostic.
    null_rows = []
    rng = np.random.default_rng(NULL_SEED)
    for l_size in NULL_SIZES:
        frame = physical[physical["L"].eq(l_size)].sort_values("T").reset_index(drop=True)
        temps = frame["T"].to_numpy(dtype=float)
        energy = frame["E_per_spin"].to_numpy(dtype=float)
        energy_se = frame["E_per_spin_se"].to_numpy(dtype=float)
        marker = peaks.loc[int(l_size)]
        for replicate in range(NULL_REPLICATES):
            null_signal = base.make_null_signal(temps, energy, energy_se, rng)
            for window in WINDOWS:
                centers = sampled_centers(len(temps), window)
                null_profile = scan(temps, null_signal, window, centers=centers)
                for estimator in ul.ESTIMATOR_NAMES:
                    group = null_profile[null_profile["estimator"].eq(estimator)]
                    row = {
                        "L_noise_reference": int(l_size),
                        "replicate": int(replicate),
                        "window_size": int(window),
                        "estimator": estimator,
                        "d_kind": ul.ESTIMATOR_D_KIND[estimator],
                        "tlog_eligible": estimator in DIMENSIONAL,
                    }
                    if estimator in DIMENSIONAL:
                        values = pd.to_numeric(group["d"], errors="coerce").to_numpy(dtype=float)
                        values = values[np.isfinite(values)]
                        row.update({
                            "candidate_any_center": bool(len(values) and np.min(np.abs(values - 4.0)) <= BAND_HALF_WIDTH),
                            "min_abs_d_minus_4": float(np.min(np.abs(values - 4.0))) if len(values) else None,
                            "finite_centers": int(len(values)),
                            "sampled_centers": int(len(group)),
                            "signature_max_slope_T": None,
                            "signature_localized": False,
                        })
                    else:
                        det = signature_slope_detection(group, float(marker["T_chi_abs_peak_boot_low"]), float(marker["T_chi_abs_peak_boot_high"]))
                        row.update({
                            "candidate_any_center": False,
                            "min_abs_d_minus_4": None,
                            "finite_centers": int(group["value"].notna().sum()),
                            "sampled_centers": int(len(group)),
                            "signature_max_slope_T": det["slope_peak_T"],
                            "signature_localized": det["localized"],
                        })
                    null_rows.append(row)
    null = pd.DataFrame(null_rows)
    null.to_csv(OUT / "individual_smooth_null_results.csv", index=False)

    null_scans = null.groupby(["L_noise_reference", "replicate", "window_size"], as_index=False).agg(
        any_dimension_candidate=("candidate_any_center", "any"),
        any_signature_localized=("signature_localized", "any"),
    )
    dimensional_fwer = float(null_scans["any_dimension_candidate"].mean())
    signature_fwer = float(null_scans["any_signature_localized"].mean())
    dim_false = null[null["tlog_eligible"]].groupby(["estimator", "window_size"])["candidate_any_center"].mean()
    sig_false = null[~null["tlog_eligible"]].groupby(["estimator", "window_size"])["signature_localized"].mean()

    dimension_summary = []
    for estimator in DIMENSIONAL:
        by_window = {}
        for window in WINDOWS:
            eligible = dimension_detection[
                dimension_detection["estimator"].eq(estimator)
                & dimension_detection["window_size"].eq(window)
                & dimension_detection["L"].isin(ELIGIBLE_SIZES)
            ]
            by_window[window] = {
                "localized_sizes": int(eligible["localized"].sum()),
                "candidate_sizes": int(eligible["candidate"].sum()),
                "eligible_sizes": int(len(eligible)),
                "coverage_min": float(eligible["coverage"].min()) if len(eligible) else 0.0,
                "coverage_ge_80pct_all_sizes": bool(len(eligible) == len(ELIGIBLE_SIZES) and (eligible["coverage"] >= MIN_COVERAGE).all()),
                "false_alarm_rate": float(dim_false.loc[(estimator, window)]),
            }
        paired = dimension_detection[
            dimension_detection["estimator"].eq(estimator)
            & dimension_detection["L"].isin(ELIGIBLE_SIZES)
        ].pivot(index="L", columns="window_size", values="T_pred")
        paired = paired.dropna() if set(WINDOWS).issubset(paired.columns) else pd.DataFrame()
        drift = float(np.median(np.abs(paired[WINDOWS[0]] - paired[WINDOWS[1]]))) if len(paired) else None
        eligible_all = dimension_detection[
            dimension_detection["estimator"].eq(estimator)
            & dimension_detection["L"].isin(ELIGIBLE_SIZES)
        ]
        best_distance = pd.to_numeric(eligible_all["min_abs_d_minus_4"], errors="coerce").min()
        minimum_coverage = float(eligible_all["coverage"].min()) if len(eligible_all) else 0.0
        localized_ok = all(by_window[w]["localized_sizes"] >= MIN_LOCALIZED_SIZES and by_window[w]["coverage_ge_80pct_all_sizes"] for w in WINDOWS)
        stability_ok = drift is not None and drift <= MAX_WINDOW_LOCATION_DRIFT
        false_ok = dimensional_fwer <= MAX_FAMILYWISE_FALSE_ALARM
        dimension_summary.append({
            "estimator": estimator,
            "d_kind": ul.ESTIMATOR_D_KIND[estimator],
            "window_results": {str(k): v for k, v in by_window.items()},
            "median_prediction_drift": drift,
            "best_abs_d_minus_4": float(best_distance) if np.isfinite(best_distance) else None,
            "minimum_coverage_all_eligible_sizes": minimum_coverage,
            "familywise_false_alarm_rate_21_estimators": dimensional_fwer,
            "meets_localization_coverage": localized_ok,
            "meets_familywise_false_alarm": false_ok,
            "meets_window_stability": stability_ok,
            "pilot_candidate": bool(localized_ok and false_ok and stability_ok),
        })

    signature_summary = []
    for estimator in SIGNATURES:
        by_window = {}
        for window in WINDOWS:
            eligible = signature_detection[
                signature_detection["estimator"].eq(estimator)
                & signature_detection["window_size"].eq(window)
                & signature_detection["L"].isin(ELIGIBLE_SIZES)
            ]
            false_rate = float(sig_false.loc[(estimator, window)])
            by_window[window] = {
                "localized_sizes": int(eligible["localized"].sum()),
                "eligible_sizes": int(len(eligible)),
                "coverage_min": float(eligible["coverage"].min()) if len(eligible) else 0.0,
                "false_alignment_rate": false_rate,
            }
        paired = signature_detection[
            signature_detection["estimator"].eq(estimator)
            & signature_detection["L"].isin(ELIGIBLE_SIZES)
        ].pivot(index="L", columns="window_size", values="slope_peak_T")
        paired = paired.dropna() if set(WINDOWS).issubset(paired.columns) else pd.DataFrame()
        drift = float(np.median(np.abs(paired[WINDOWS[0]] - paired[WINDOWS[1]]))) if len(paired) else None
        signature_summary.append({
            "estimator": estimator,
            "d_kind": ul.ESTIMATOR_D_KIND[estimator],
            "window_results": {str(k): v for k, v in by_window.items()},
            "median_max_slope_location_drift": drift,
            "familywise_false_alignment_rate_8_signatures": signature_fwer,
            "tlog_candidate": False,
            "interpretation": "descriptive_signature_only_no_d4_or_T_log",
        })

    json_result = {
        "analysis_status": "exploratory_extension_after_d_kind_pilot",
        "pipeline_version": ul.VERSION_MASTER,
        "input": "E_per_spin only; same physical data and markers as d_kind pilot",
        "estimators_total": len(ul.ESTIMATOR_NAMES),
        "dimension_estimators_tested_individually": DIMENSIONAL,
        "signature_estimators_descriptive_only": SIGNATURES,
        "windows": list(WINDOWS),
        "eligible_sizes": ELIGIBLE_SIZES,
        "d4_band": [4.0 - BAND_HALF_WIDTH, 4.0 + BAND_HALF_WIDTH],
        "null_design": {"sizes": list(NULL_SIZES), "replicates_per_size": NULL_REPLICATES, "sampled_centers": NULL_CENTERS, "seed": NULL_SEED, "n_scans": int(len(null_scans))},
        "familywise_false_alarm_rate_dimensions": dimensional_fwer,
        "familywise_false_alignment_rate_signatures": signature_fwer,
        "dimension_results": dimension_summary,
        "signature_results": signature_summary,
        "limitations": [
            "The individual analysis was planned after the d_kind pilot and is exploratory.",
            "The reference d=4 remains a domain-dependent hypothesis for the 21 dimensional outputs; the v5.8 taxonomy does not justify it universally.",
            "The 8 signature estimators are not dimensions in v5.8 and are never assigned T_log or compared with 4.",
            "Only 40 smooth null scans are used, so false-alarm rates are coarse.",
            "Uncertainty in physical curves is not propagated through estimator values.",
            "apply_complexity z-scores each local window, removing absolute amplitude and variance scale before estimating shape.",
            "This tests scalar local energy-versus-temperature profiles, not raw spin configurations or dynamic trajectories.",
        ],
    }
    (OUT / "individual_estimator_transition_audit.json").write_text(json.dumps(json_result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Audit exploratoire des 29 estimateurs individuels",
        "",
        "Extension exploratoire du pilote `d_kind`; plan d'analyse : [INDIVIDUAL_ESTIMATOR_EXTENSION_PLAN.md](../../../INDIVIDUAL_ESTIMATOR_EXTENSION_PLAN.md).",
        "",
        f"Valeurs calculées séparément pour {len(DIMENSIONAL)} dimensions TLog admissibles et {len(SIGNATURES)} signatures non dimensionnelles, sans agrégation par `d_kind`.",
        "",
        "## Sorties dimensionnelles : convention `d=4` actuelle",
        "",
        f"Taux familial de fausses alertes parmi les 21 sorties dimensionnelles : **{dimensional_fwer:.1%}** sur {len(null_scans)} balayages nuls.",
        "",
        "| Estimateur | d_kind | Localisés / 6 (w=31) | Localisés / 6 (w=41) | Couverture min. | Meilleur écart à 4 | Faux alertes individuelles (31 / 41) | Dérive médiane T | Candidat pilote |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in dimension_summary:
        a, b = row["window_results"][str(WINDOWS[0])], row["window_results"][str(WINDOWS[1])]
        dr = row["median_prediction_drift"]
        best_dist = row["best_abs_d_minus_4"]
        lines.append(f"| {row['estimator']} | {row['d_kind']} | {a['localized_sizes']} / 6 | {b['localized_sizes']} / 6 | {row['minimum_coverage_all_eligible_sizes']:.0%} | {'n/a' if best_dist is None else f'{best_dist:.3f}'} | {a['false_alarm_rate']:.1%} / {b['false_alarm_rate']:.1%} | {'n/a' if dr is None else f'{dr:.3f}'} | {'oui' if row['pilot_candidate'] else 'non'} |")
    lines.extend([
        "",
        "Le statut candidat conserve les critères de répétabilité, couverture, stabilité et taux familial du pilote. Le seuil `d=4` est la convention TLog actuelle, pas une référence universelle garantie pour chaque algorithme.",
        "",
        "Parmi les résultats finis, `PersistentHomology` est le seul estimateur régulièrement proche de 4 (13 combinaisons taille-fenêtre sur 14), mais il ne localise le pic physique que pour 1 taille sur 6 et déclenche 25 % de fausses alertes individuelles. `TwoNN` n'a aucune valeur finie sur ces courbes; la couverture minimale signale aussi les limites de `VisibilityGraph`, `SpectralDimension` et `LevinaBickel` dans ce régime.",
        "",
        "## Signatures non dimensionnelles : localisation descriptive",
        "",
        f"Taux familial de fausse localisation de la pente maximale parmi les huit signatures : **{signature_fwer:.1%}** sur les contrôles nuls.",
        "",
        "| Estimateur | Localisés / 6 (w=31) | Localisés / 6 (w=41) | Faux alignements (31 / 41) | Dérive médiane du centre de pente | Interprétation TLog |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for row in signature_summary:
        a, b = row["window_results"][str(WINDOWS[0])], row["window_results"][str(WINDOWS[1])]
        dr = row["median_max_slope_location_drift"]
        lines.append(f"| {row['estimator']} | {a['localized_sizes']} / 6 | {b['localized_sizes']} / 6 | {a['false_alignment_rate']:.1%} / {b['false_alignment_rate']:.1%} | {'n/a' if dr is None else f'{dr:.3f}'} | hors couche TLog |")
    lines.extend([
        "",
        "Ces huit valeurs n'ont pas été comparées à 4 et aucun `T_log` n'a été calculé pour elles : ce sont des signatures, conformément à la taxonomie v5.8. La localisation de la pente maximale est descriptive et n'établit pas à elle seule une transition.",
        "",
        "## Conclusion",
        "",
        f"Candidats dimensionnels satisfaisant l'ensemble des seuils : **{sum(r['pilot_candidate'] for r in dimension_summary)} / {len(dimension_summary)}**. Les signatures sont conservées comme diagnostics séparés et ne peuvent pas devenir des candidats TLog sans définition dimensionnelle et justification théorique.",
        "",
        "L'analyse porte uniquement sur les courbes d'énergie d'équilibre, avec 40 contrôles nuls. Elle est exploratoire, les taux de fausses alertes sont grossiers, et l'incertitude Monte Carlo des dimensions n'est pas propagée.",
        "",
        "`apply_complexity` z-score chaque fenêtre locale avant de calculer les estimateurs : cette analyse suit donc la forme locale, pas l'amplitude absolue ni la variance des fluctuations thermodynamiques.",
        "",
        "## Fichiers",
        "",
        "- [Plan de cette extension](../../../INDIVIDUAL_ESTIMATOR_EXTENSION_PLAN.md)",
        "- [Résultats JSON](individual_estimator_transition_audit.json)",
        "- [Profils individuels des 29 estimateurs](individual_local_profiles.csv)",
        "- [Détections individuelles dimensionnelles](individual_dimension_detection.csv)",
        "- [Localisation descriptive des signatures](signature_shape_localization.csv)",
        "- [Contrôles nuls individuels](individual_smooth_null_results.csv)",
    ])
    (OUT / "RAPPORT_AUDIT_29_ESTIMATEURS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote individual estimator audit to {OUT}")


if __name__ == "__main__":
    main()
