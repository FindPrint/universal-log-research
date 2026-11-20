#!/usr/bin/env python
"""Create a reader-first, non-destructive view of the frozen v6 Ising audit.

The original pipeline outputs remain untouched. This report translates their
saved JSON/CSV into labeled figures and plain-language summaries, with links to
the complete raw artifacts for audit.
"""
from __future__ import annotations

import html
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
FINITE = PROJECT / "ising_classique_test" / "finite_size"
RUNS = HERE / "runs"
STATE = HERE / "run_state.json"
PEAKS = FINITE / "finite_size_peaks.csv"
BINDER_CROSSINGS = FINITE / "binder_crossings.csv"
DATA = FINITE / "finite_size_results.csv"
OUT = HERE / "LECTURE_GUIDEE_V6"
FIG = OUT / "figures"
TC_EXACT = 2.269185314213022
COLORS = {"blue": "#0072B2", "orange": "#D55E00", "green": "#009E73",
          "purple": "#CC79A7", "sky": "#56B4E9", "gray": "#666666"}

plt.rcParams.update({"font.size": 10, "axes.titlesize": 14, "axes.labelsize": 11,
                     "figure.titlesize": 16, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white"})


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_runs():
    state = read_json(STATE)
    return state.get("runs", {})


def master_for(run):
    path = Path(run.get("output_path", "")) / "master_results.json"
    return read_json(path) if path.exists() else {}


def t0_record(master):
    cascade = master.get("five_threshold_cascade") or {}
    units = cascade.get("thresholds_in_control_units") or {}
    t0 = units.get("T_0_Monte_Carlo_Central") or {}
    return {
        "percent": cascade.get("T_0_Monte_Carlo_Central"),
        "raw": t0.get("control_value_raw"),
        "low": t0.get("control_value_raw_min_near"),
        "high": t0.get("control_value_raw_max_near"),
        "ambiguous": t0.get("ambiguous"),
        "monotone": (cascade.get("control_monotonicity") or {}).get("monotone"),
    }


def masters_for_run(run_id, run):
    if run_id == "sensitivity_L16_multiple_physical_controls":
        controls = read_json(Path(run.get("output_path", "")) / "controls_summary.json").get("controls") or {}
        found = []
        for control, entry in controls.items():
            folder = Path(entry.get("output_dir", ""))
            master = read_json(folder / "master_results.json") if folder else {}
            found.append((control, entry, master))
        return found
    master = master_for(run)
    return [(run.get("control_col") or "Temperature", {}, master)] if master else []


def write_readable_summary(runs, peaks, blind_frame=None, diagonal_frame=None):
    peak_by_l = {int(row["L"]): row for _, row in peaks.iterrows()}
    rows = []
    for run_id, run in sorted(runs.items()):
        if run.get("status") != "complete":
            continue
        for control, control_entry, master in masters_for_run(run_id, run):
            if not master:
                continue
            cascade = master.get("five_threshold_cascade") or {}
            t0 = t0_record(master)
            holo = master.get("holographic_tension_state") or {}
            gap = holo.get("tension_gap_diagnostics") or {}
            trio = gap.get("triangulation") or {}
            trio_values = trio.get("trio_values") or {}
            geometric = holo.get("geometric_layer") or {}
            pred = master.get("prediction_levels") or {}
            l7a = pred.get("L7a_coherence") or pred.get("L7_consensus") or {}
            l7b = pred.get("L7b_robustesse") or {}
            rp = master.get("run_pipeline") or {}
            threshold_meta = rp.get("threshold_metadata") or {}
            optimization = (threshold_meta.get("threshold_optimization") or {})
            mc_diag = optimization.get("raw_optimization_diagnostics") or optimization.get("optimization_diagnostics") or {}
            transitions = rp.get("transition_analysis") or {}
            higuchi = transitions.get("Higuchi") or {}
            total = higuchi.get("Tous") or {}
            score_map = rp.get("scores") or {}
            q_keys = ["Q1_Calme_vs_Chaos", "Q2_Tension_Seuil", "Q3_Agressivite",
                      "Q4_Persistence", "Q5_Active_Reactive", "Q6_Active_Reactive_Scaled"]
            q_coverage = {}
            for q in q_keys:
                values = score_map.get(q) or {}
                valid = 0
                for key, value in values.items():
                    if key.startswith("Energy_per_spin_") and key.endswith("_mean"):
                        try:
                            valid += int(np.isfinite(float(value)))
                        except (TypeError, ValueError):
                            pass
                q_coverage[q.split("_")[0]] = f"{valid}/29"
            l_size = int(run.get("L", -1))
            peak = peak_by_l.get(l_size, {}) if control == "Temperature" else {}
            chi_peak = float(peak["T_chi_abs_peak"]) if peak is not None and "T_chi_abs_peak" in peak else None
            cv_peak = float(peak["T_Cv_peak"]) if peak is not None and "T_Cv_peak" in peak else None
            error = float(t0["raw"]) - chi_peak if isinstance(t0.get("raw"), (int, float)) and chi_peak is not None else None
            error_tc = float(t0["raw"]) - TC_EXACT if control == "Temperature" and isinstance(t0.get("raw"), (int, float)) else None
            rows.append({
                "run_id": run_id, "L": l_size, "n_lignes": master.get("metadata", {}).get("n_samples"),
                "controle": control, "cible_demandee": master.get("metadata", {}).get("target_requested"),
                "cible_utilisee": master.get("metadata", {}).get("target_used"),
                "statut": control_entry.get("status", master.get("status", "complete")),
                "T0_rang_pct": t0.get("percent"), "T0_axe_brut": t0.get("raw"),
                "T0_borne_min_locale": t0.get("low"), "T0_borne_max_locale": t0.get("high"),
                "T0_conversion_ambigue": t0.get("ambiguous"),
                "axe_monotone": t0.get("monotone"), "pic_Cv_T": cv_peak, "pic_chi_T": chi_peak,
                "T0_moins_Tc_exact": error_tc, "T0_moins_pic_chi": error,
                "L7a_vote": l7a.get("consensus_direction"), "L7b_robustesse": l7b.get("verdict"),
                "voie1_Higuchi": gap.get("voie1_higuchi"),
                "voie2_ancre_saturation": trio_values.get(trio.get("trio_sat_estimator", "")),
                "voie2_ancre_transition": trio_values.get(trio.get("trio_crit_estimator", "")),
                "voie2_ancre_divergence": trio_values.get(trio.get("trio_div_estimator", "")),
                "voie2_statut": "complet" if all(trio_values.get(name) is not None for name in trio.get("trio", [])) else "ancre manquante",
                "Tlog_classe_median": geometric.get("T_log_class_median"),
                "MC_iterations": mc_diag.get("n_iterations"), "MC_reussites": mc_diag.get("n_success"),
                "MC_echecs": mc_diag.get("n_failed"), "MC_seuil_scan": optimization.get("raw_mc_threshold"),
                **{f"{q}_couverture": v for q, v in q_coverage.items()},
                "F1_avant_Higuchi_Tous": total.get("first_derivative_pre"),
                "F1_apres_Higuchi_Tous": total.get("first_derivative"),
                "F2_avant_Higuchi_Tous": total.get("second_derivative_pre"),
                "F2_apres_Higuchi_Tous": total.get("second_derivative"),
                "d_sat": (holo.get("D_vector") or {}).get("d_sat"),
                "d_crit": (holo.get("D_vector") or {}).get("d_crit"),
                "d_div": (holo.get("D_vector") or {}).get("d_div"),
                "dominant_regime": holo.get("dominant_regime_relative"),
                "dossier_sortie": str(control_entry.get("output_dir") or run.get("output_path")),
            })
    if blind_frame is not None and not blind_frame.empty:
        blind_manifest = read_json(HERE / "blind_flux_sensitivity_manifest.json")
        blind_master = read_json(Path(blind_manifest.get("output_path", "")) / "master_results.json")
        rec = t0_record(blind_master)
        holo = blind_master.get("holographic_tension_state") or {}
        gap = holo.get("tension_gap_diagnostics") or {}
        trio = gap.get("triangulation") or {}
        trio_values = trio.get("trio_values") or {}
        pred = blind_master.get("prediction_levels") or {}
        cascade = blind_master.get("five_threshold_cascade") or {}
        optimization = (((blind_master.get("run_pipeline") or {}).get("threshold_metadata") or {})
                        .get("threshold_optimization") or {})
        mc_diag = optimization.get("raw_optimization_diagnostics") or {}
        peak = peak_by_l[64]
        raw = rec.get("raw")
        rows.append({
            "run_id": "blind_flux_L64_temperature_energy", "L": 64,
            "n_lignes": blind_master.get("metadata", {}).get("n_samples"), "controle": "Temperature",
            "cible_demandee": "Energy_per_spin", "cible_utilisee": "Energy_per_spin",
            "statut": blind_manifest.get("status"), "T0_rang_pct": rec.get("percent"),
            "T0_axe_brut": raw, "T0_borne_min_locale": rec.get("low"),
            "T0_borne_max_locale": rec.get("high"), "T0_conversion_ambigue": rec.get("ambiguous"),
            "axe_monotone": rec.get("monotone"), "pic_Cv_T": float(peak["T_Cv_peak"]),
            "pic_chi_T": float(peak["T_chi_abs_peak"]),
            "T0_moins_Tc_exact": (float(raw) - TC_EXACT if isinstance(raw, (int, float)) else None),
            "T0_moins_pic_chi": (float(raw) - float(peak["T_chi_abs_peak"]) if isinstance(raw, (int, float)) else None),
            "L7a_vote": ((pred.get("L7a_coherence") or {}).get("consensus_direction")),
            "L7b_robustesse": ((pred.get("L7b_robustesse") or {}).get("verdict")),
            "voie1_Higuchi": gap.get("voie1_higuchi"),
            "voie2_ancre_saturation": trio_values.get(trio.get("trio_sat_estimator", "")),
            "voie2_ancre_transition": trio_values.get(trio.get("trio_crit_estimator", "")),
            "voie2_ancre_divergence": trio_values.get(trio.get("trio_div_estimator", "")),
            "voie2_statut": "complet" if all(trio_values.get(name) is not None for name in trio.get("trio", [])) else "ancre manquante",
            "MC_iterations": mc_diag.get("n_iterations"), "MC_reussites": mc_diag.get("n_success"),
            "MC_echecs": mc_diag.get("n_failed"), "MC_seuil_scan": optimization.get("raw_mc_threshold"),
            "dominant_regime": holo.get("dominant_regime_relative"),
            "dossier_sortie": blind_manifest.get("output_path"),
        })
    if diagonal_frame is not None and not diagonal_frame.empty:
        row = diagonal_frame.iloc[0]
        rows.append({
            "run_id": "diagonal_L16_energy_as_target_and_control", "L": 16,
            "n_lignes": row.get("n_lignes"), "controle": "Energy_per_spin (diagonal)",
            "cible_demandee": "Energy_per_spin", "cible_utilisee": "Energy_per_spin",
            "statut": row.get("status"), "T0_rang_pct": row.get("T0_rang_pct"),
            "T0_axe_brut": row.get("T0_axe_brut"),
            "T0_borne_min_locale": row.get("T0_local_low_5_lignes"),
            "T0_borne_max_locale": row.get("T0_local_high_5_lignes"),
            "T0_conversion_ambigue": row.get("conversion_ambigue"),
            "axe_monotone": row.get("axe_monotone"), "L7a_vote": row.get("L7a"),
            "L7b_robustesse": row.get("L7b"), "voie2_statut": "cas diagonal; comparer avec réserve",
            "dossier_sortie": str(Path(read_json(HERE / "diagonal_sensitivity_manifest.json").get("output", ""))),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(OUT / "resultats_synthese_lisible.csv", index=False, encoding="utf-8")
    return df


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=170, bbox_inches="tight")
    plt.close(fig)


def fig_localization(runs):
    peaks = pd.read_csv(PEAKS).sort_values("L")
    points = {}
    for rid, item in runs.items():
        if item.get("status") != "complete":
            continue
        if rid.startswith("primary_L") and rid.endswith("_temperature"):
            master = master_for(item)
            points[int(item["L"])] = t0_record(master)
        elif rid == "sensitivity_L16_multiple_physical_controls":
            p = Path(item.get("output_path", "")) / "controls_summary.json"
            summary = read_json(p)
            control = (summary.get("controls") or {}).get("Temperature", {})
            points[16] = {"percent": control.get("t0_pct"), "raw": control.get("t0_control_value_raw"),
                          "low": control.get("t0_control_value_min_near"),
                          "high": control.get("t0_control_value_max_near"),
                          "ambiguous": control.get("t0_control_value_ambiguous"),
                          "monotone": control.get("control_monotone")}

    fig, (ax, err) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=(3, 1.25), sharex=True)
    x = peaks["L"].to_numpy(float)
    mid = peaks["T_chi_abs_peak"].to_numpy(float)
    low = peaks["T_chi_abs_peak_boot_low"].to_numpy(float)
    high = peaks["T_chi_abs_peak_boot_high"].to_numpy(float)
    ax.fill_between(x, low, high, color=COLORS["sky"], alpha=.24,
                    label="IC bootstrap à 95 % du pic χ (fichier de référence)")
    ax.plot(x, mid, "o-", color=COLORS["blue"], label="Pic de susceptibilité χ — référence")
    cv = peaks["T_Cv_peak"].to_numpy(float)
    cv_low = peaks["T_Cv_peak_boot_low"].to_numpy(float)
    cv_high = peaks["T_Cv_peak_boot_high"].to_numpy(float)
    ax.fill_between(x, cv_low, cv_high, color=COLORS["green"], alpha=.13,
                    label="IC bootstrap à 95 % du pic Cv")
    ax.plot(x, cv, "^--", color=COLORS["green"], markersize=5,
            label="Pic de capacité calorifique Cv")
    ax.axhline(TC_EXACT, color=COLORS["gray"], linestyle="--", linewidth=1.5,
               label=f"Tc exact, réseau infini = {TC_EXACT:.4f}")
    present = [(L, r) for L, r in sorted(points.items()) if isinstance(r.get("raw"), (float, int))]
    if present:
        px = np.array([L for L, _ in present], dtype=float)
        py = np.array([r["raw"] for _, r in present], dtype=float)
        ax.scatter(px, py, marker="D", s=65, color=COLORS["orange"], edgecolor="white", linewidth=.7,
                   zorder=5, label="T0 pipeline (température brute)")
        ax.plot([], [], color=COLORS["orange"], linewidth=2,
                label="Étendue locale de T0 (5 lignes proches)")
        for L, rec in present:
            if isinstance(rec.get("low"), (float, int)) and isinstance(rec.get("high"), (float, int)):
                ax.vlines(L, rec["low"], rec["high"], color=COLORS["orange"], linewidth=2, alpha=.75)
    ax.set(title="T0 se situe-t-il près des repères thermiques connus ?",
           ylabel="Température T", xlabel="Taille linéaire du réseau L")
    ax.grid(alpha=.2)
    ax.legend(loc="best", frameon=True, fontsize=9)

    errors_chi = []
    errors_tc = []
    for _, row in peaks.iterrows():
        rec = points.get(int(row["L"]))
        if rec and isinstance(rec.get("raw"), (float, int)):
            errors_chi.append(float(rec["raw"]) - float(row["T_chi_abs_peak"]))
            errors_tc.append(float(rec["raw"]) - TC_EXACT)
        else:
            errors_chi.append(np.nan)
            errors_tc.append(np.nan)
    err.axhline(0, color=COLORS["gray"], linewidth=1)
    err.scatter(x - .7, errors_chi, marker="o", color=COLORS["orange"], label="T0 − pic χ")
    err.scatter(x + .7, errors_tc, marker="s", color=COLORS["purple"], label="T0 − Tc exact")
    err.set(ylabel="Écart T (°T)", xlabel="Taille linéaire du réseau L")
    err.set_xticks(x, [str(int(i)) for i in x])
    err.grid(axis="y", alpha=.2)
    err.legend(frameon=False, ncol=2, loc="lower right", fontsize=8)
    fig.subplots_adjust(bottom=.16, hspace=.16, top=.9)
    fig.text(.5, .015, "IC physiques bootstrap à 95 % du CSV; Tc exact = limite L→∞. Le trait court de T0 montre l’étendue locale "
             "sur 5 lignes, pas un IC. T0 est une sortie unique; le pas de T est 0,01.", ha="center", fontsize=8.5, color="#444444")
    save(fig, "localisation_t0_et_reperes.png")
    markers = peaks[["L", "T_Cv_peak", "T_Cv_peak_boot_low", "T_Cv_peak_boot_high",
                     "T_chi_abs_peak", "T_chi_abs_peak_boot_low", "T_chi_abs_peak_boot_high"]].copy()
    markers["Tc_exact_infinite"] = TC_EXACT
    markers["T0_pipeline"] = markers["L"].map(lambda L: points.get(int(L), {}).get("raw"))
    markers["T0_minus_Tc_exact"] = markers["T0_pipeline"] - TC_EXACT
    markers["T0_minus_chi_peak"] = markers["T0_pipeline"] - markers["T_chi_abs_peak"]
    markers.to_csv(OUT / "reperes_physiques_et_T0.csv", index=False, encoding="utf-8")
    return points, peaks


def fig_binder_crossings():
    if not BINDER_CROSSINGS.exists():
        return pd.DataFrame()
    binder = pd.read_csv(BINDER_CROSSINGS).sort_values(["L1", "L2"])
    x = np.arange(len(binder))
    mid = binder["T_cross"].to_numpy(float)
    low = binder["T_cross_ci95_low"].to_numpy(float)
    high = binder["T_cross_ci95_high"].to_numpy(float)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.errorbar(x, mid, yerr=[mid - low, high - mid], fmt="o", color=COLORS["blue"],
                ecolor=COLORS["sky"], elinewidth=2, capsize=4,
                label="Croisement Binder U4 (IC bootstrap 95 %)")
    ax.axhline(TC_EXACT, color=COLORS["gray"], linestyle="--", label=f"Tc exact = {TC_EXACT:.4f}")
    labels = [f"{int(a)}–{int(b)}" for a, b in zip(binder["L1"], binder["L2"])]
    ax.set_xticks(x, labels)
    ax.set_xlabel("Paire de tailles L qui se croisent")
    ax.set_ylabel("Température de croisement T")
    ax.set_title("Les croisements du cumulant de Binder se rapprochent-ils de Tc ?")
    ax.grid(axis="y", alpha=.2)
    ax.legend(frameon=False, loc="best")
    fig.text(.5, .015, "Les croisements sont des repères physiques du jeu de référence; ils n’entrent pas dans la cible du pipeline.",
             ha="center", fontsize=9)
    fig.subplots_adjust(bottom=.17)
    save(fig, "croisements_binder_et_Tc.png")
    return binder


def fig_observables():
    data = pd.read_csv(DATA)
    l16 = data[data["L"].eq(16)].sort_values("T")
    cols = [("E_per_spin", "Énergie par spin", "blue"),
            ("abs_magnetization", "Aimantation absolue", "orange"),
            ("chi_abs_per_spin", "Susceptibilité χ", "green"),
            ("Cv_per_spin", "Capacité calorifique Cv", "purple"),
            ("Binder_U4", "Cumulant de Binder U4", "sky")]
    fig, axes = plt.subplots(5, 1, figsize=(10, 12), sharex=True)
    for ax, (col, label, color) in zip(axes, cols):
        ax.plot(l16["T"], l16[col], color=COLORS[color], linewidth=1.8)
        ax.axvline(TC_EXACT, color=COLORS["gray"], linestyle="--", linewidth=1.2,
                   label="Tc exact (limite infinie)")
        ax.set_ylabel(label)
        ax.grid(alpha=.2)
    axes[0].legend(loc="best", frameon=False)
    axes[-1].set_xlabel("Température T")
    fig.suptitle("Les cinq colonnes physiques du jeu Ising (L=16, 76 températures)", y=1.005)
    fig.text(.5, .003, "Ces courbes montrent le jeu fourni au pipeline. L’énergie est la cible fixe; "
             "les quatre autres observables servent ici de flux/axes de sensibilité.", ha="center", fontsize=9)
    save(fig, "observables_physiques_L16.png")


def fig_question_heatmap(runs):
    candidates = [(rid, item) for rid, item in runs.items()
                  if rid.startswith("primary_L") and item.get("status") == "complete"]
    chosen = next(((rid, item) for rid, item in candidates if rid.startswith("primary_L24_")), None)
    if not chosen:
        return None
    rid, item = chosen
    master = master_for(item)
    scores = ((master.get("run_pipeline") or {}).get("scores") or {})
    questions = [
        ("Q1 — Calme / chaos", "Q1_Calme_vs_Chaos"),
        ("Q2 — Tension seuil", "Q2_Tension_Seuil"),
        ("Q3 — Agressivité", "Q3_Agressivite"),
        ("Q4 — Persistance", "Q4_Persistence"),
        ("Q5 — Actif / réactif", "Q5_Active_Reactive"),
        ("Q6 — Contraste mis à l’échelle", "Q6_Active_Reactive_Scaled"),
    ]
    metric_names = list(scores.get(questions[0][1], {}))
    estimators = []
    for key in metric_names:
        prefix = "Energy_per_spin_"
        suffix = "_mean"
        if key.startswith(prefix) and key.endswith(suffix):
            estimators.append(key[len(prefix):-len(suffix)])
    if not estimators:
        return None
    values = np.full((len(questions), len(estimators)), np.nan)
    for qi, (_, skey) in enumerate(questions):
        for ei, estimator in enumerate(estimators):
            raw = (scores.get(skey) or {}).get(f"Energy_per_spin_{estimator}_mean")
            try:
                val = float(raw)
                values[qi, ei] = val if np.isfinite(val) else np.nan
            except (TypeError, ValueError):
                pass
    # Color is within-question rank for readability; exact scores remain in CSV.
    ranks = np.full_like(values, np.nan)
    for qi, row in enumerate(values):
        finite = np.isfinite(row)
        if finite.any():
            order = pd.Series(row[finite]).rank(method="average", pct=True).to_numpy()
            ranks[qi, finite] = order
    fig, ax = plt.subplots(figsize=(12.5, 9))
    masked = np.ma.masked_invalid(ranks.T)
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("#D9D9D9")
    image = ax.imshow(masked, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(questions)), [q[0].replace(" — ", "\n") for q in questions], rotation=0, ha="center", fontsize=9)
    ax.set_yticks(range(len(estimators)), estimators, fontsize=8)
    ax.set_title("Q1–Q6 : profil relatif des 29 estimateurs — L=24, cible énergie", pad=16)
    ax.set_ylabel("Estimateur")
    cbar = fig.colorbar(image, ax=ax, pad=.025, fraction=.035)
    cbar.set_label("Rang relatif dans la question (0–1)")
    fig.subplots_adjust(left=.2, right=.9, top=.92, bottom=.1)
    fig.text(.5, .015, "La couleur classe les estimateurs à l’intérieur d’une même question; elle ne compare pas "
             "les amplitudes entre Q. Les valeurs brutes sont dans scores_Q1_Q6_L24_long.csv.",
             ha="center", fontsize=9)
    save(fig, "questions_Q1_Q6_rangs_29_estimateurs.png")
    rows = []
    for qi, (qname, skey) in enumerate(questions):
        for ei, estimator in enumerate(estimators):
            rows.append({"question": qname, "estimateur": estimator,
                         "score_brut": values[qi, ei], "rang_interne_question": ranks[qi, ei],
                         "etat": "calculé" if np.isfinite(values[qi, ei]) else "indisponible"})
    pd.DataFrame(rows).to_csv(OUT / "scores_Q1_Q6_L24_long.csv", index=False, encoding="utf-8")
    return estimators, values


def fig_f1_f2():
    master = read_json(RUNS / "primary_L24_temperature" / "master_results.json")
    transitions = ((master.get("run_pipeline") or {}).get("transition_analysis") or {})
    h = transitions.get("Higuchi") or {}
    fluxes = ["Tous", "Energy_per_spin", "abs_magnetization", "chi_abs_per_spin", "Cv_per_spin", "Binder_U4"]
    labels = ["Tous", "Énergie", "|m|", "χ", "Cv", "Binder U4"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    for ax, before_key, after_key, title, ylab in [
        (axes[0], "first_derivative_pre", "first_derivative", "F1 — pente locale", "coefficient de pente"),
        (axes[1], "second_derivative_pre", "second_derivative", "F2 — courbure locale", "coefficient de courbure")]:
        y = np.arange(len(fluxes))
        pre, post = [], []
        for flux in fluxes:
            block = h.get(flux) or {}
            pre.append(block.get(before_key, np.nan))
            post.append(block.get(after_key, np.nan))
        ax.axvline(0, color=COLORS["gray"], linewidth=1)
        ax.scatter(pre, y + .12, color=COLORS["blue"], label="Avant T0", s=45)
        ax.scatter(post, y - .12, color=COLORS["orange"], label="Après T0", s=45)
        for i, (a, b) in enumerate(zip(pre, post)):
            if isinstance(a, (float, int)) and isinstance(b, (float, int)) and np.isfinite(a) and np.isfinite(b):
                ax.plot([a, b], [i + .12, i - .12], color="#AAAAAA", linewidth=1, zorder=0)
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel(ylab)
        ax.grid(axis="x", alpha=.2)
    axes[0].legend(frameon=False, loc="best")
    fig.suptitle("F1/F2 de Higuchi avant et après T0 — L=24", y=1.02)
    fig.text(.5, -.02, "Chaque paire avant/après se compare au sein du même flux. "
             "Unités propres aux flux; aucun intervalle d’incertitude n’est fourni pour ces points.", ha="center", fontsize=9)
    save(fig, "derivees_F1_F2_avant_apres_L24.png")


def fig_pathways_by_size(readable):
    selected = readable[readable["run_id"].str.startswith("primary_L") |
                        readable["run_id"].eq("sensitivity_L16_multiple_physical_controls")].copy()
    selected = selected[selected["controle"].eq("Temperature")].sort_values("L")
    if selected.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5.4))
    series = [
        ("voie1_Higuchi", "Higuchi · Voie 1 / ancre saturation Voie 2", "blue", "o"),
        ("voie2_ancre_transition", "InformationD1 · ancre transition", "orange", "s"),
        ("voie2_ancre_divergence", "LevinaBickel · ancre divergence", "green", "^"),
    ]
    for col, label, color, marker in series:
        values = pd.to_numeric(selected[col], errors="coerce")
        ax.plot(selected["L"], values, marker=marker, color=COLORS[color], label=label, linewidth=1.7)
    ax.set_xticks(selected["L"], [str(int(x)) for x in selected["L"]])
    ax.set_xlabel("Taille linéaire du réseau L")
    ax.set_ylabel("Valeur de l’estimateur (échelle propre à chacun)")
    ax.set_title("Voie 1 à côté des trois ancres de Voie 2 — contrôle Température")
    ax.grid(alpha=.2)
    ax.legend(frameon=False, loc="best", fontsize=8.5)
    fig.text(.5, .015, "Les estimateurs n’ont pas nécessairement une échelle commune. Les trous signalent une ancre indisponible; "
             "aucune valeur n’est imputée et les ancres ne sont pas moyennées.", ha="center", fontsize=9)
    fig.subplots_adjust(bottom=.19)
    save(fig, "voies_1_2_ancres_par_taille.png")
    selected[["run_id", "L", "voie1_Higuchi", "voie2_ancre_saturation", "voie2_ancre_transition",
              "voie2_ancre_divergence", "voie2_statut", "Tlog_classe_median", "d_sat", "d_crit", "d_div"]].to_csv(
                  OUT / "voies_1_2_par_taille.csv", index=False, encoding="utf-8")


def multi_controls(runs):
    item = runs.get("sensitivity_L16_multiple_physical_controls", {})
    path = Path(item.get("output_path", "")) / "controls_summary.json"
    data = read_json(path)
    return data.get("controls") or {}


def fig_multi_control(runs):
    controls = multi_controls(runs)
    entries = [(name, row) for name, row in controls.items() if row.get("status") == "ok"]
    if not entries:
        return controls
    fig, ax = plt.subplots(figsize=(10, 5.2))
    y = np.arange(len(entries))
    for yi, (name, row) in enumerate(entries):
        x = row.get("t0_pct")
        if isinstance(x, (int, float)) and np.isfinite(x):
            color = COLORS["blue"]
            marker = "x" if row.get("control_monotone") is False else "o"
            style = {"edgecolors": "white"} if marker != "x" else {}
            ax.scatter(x, yi, s=65, color=color, marker=marker, zorder=3, **style)
            raw = row.get("t0_control_value_raw")
            raw_text = "" if raw is None else f"  axe brut = {float(raw):.4g}" + (" (ambig.)" if row.get("t0_control_value_ambiguous") else "")
            ax.annotate(f"{float(x):.1f}%{raw_text}", (x, yi), xytext=(7, 0),
                        textcoords="offset points", va="center", fontsize=8.5)
    ax.set_yticks(y, [name for name, _ in entries])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Position de T0 dans l’axe propre au contrôle (%)")
    ax.set_title("Changer de contrôle déplace-t-il le seuil ? — L=16")
    ax.grid(axis="x", alpha=.25)
    ax.text(.01, -.22, "Les pourcentages sont des rangs sur des axes différents. Les valeurs brutes à droite ont des unités différentes; "
            "elles ne sont pas directement comparables ni des températures. Marqueur X = axe non monotone. La cible énergie reste fixe; elle n’est pas testée comme contrôle.",
            transform=ax.transAxes, fontsize=8.5, color="#444444", va="top", wrap=True)
    fig.subplots_adjust(bottom=.28, right=.86, left=.24)
    save(fig, "seuil_par_controle_L16.png")
    return controls


def fig_multi_axis_questions(runs):
    run = runs.get("sensitivity_L16_multiple_physical_controls", {})
    controls = read_json(Path(run.get("output_path", "")) / "controls_summary.json").get("controls") or {}
    question_defs = [
        ("Q1", "Q1_Calme_vs_Chaos"), ("Q2", "Q2_Tension_Seuil"),
        ("Q3", "Q3_Agressivite"), ("Q4", "Q4_Persistence"),
        ("Q5", "Q5_Active_Reactive"), ("Q6", "Q6_Active_Reactive_Scaled"),
    ]
    fluxes = ["Energy_per_spin", "abs_magnetization", "chi_abs_per_spin", "Cv_per_spin", "Binder_U4"]
    records = []
    f_records = []
    profiles = []
    coverage = []
    estimators = None
    for control, entry in controls.items():
        folder = Path(entry.get("output_dir", ""))
        master = read_json(folder / "master_results.json") if folder else {}
        rp = master.get("run_pipeline") or {}
        scores = rp.get("scores") or {}
        row_coverage = []
        for short, qkey in question_defs:
            q_scores = scores.get(qkey) or {}
            picked = {}
            for flux in fluxes:
                prefix = flux + "_"
                for key, value in q_scores.items():
                    if key.startswith(prefix) and key.endswith("_mean"):
                        estimator = key[len(prefix):-len("_mean")]
                        try:
                            score = float(value)
                            score = score if np.isfinite(score) else np.nan
                        except (TypeError, ValueError):
                            score = np.nan
                        records.append({"controle": control, "question": short, "flux": flux,
                                        "estimateur": estimator, "score_brut": score,
                                        "etat": "calculé" if np.isfinite(score) else "indisponible"})
                        if flux == "Energy_per_spin":
                            picked[estimator] = score
            n_finite = sum(np.isfinite(v) for v in picked.values())
            row_coverage.append(n_finite)
            if estimators is None and picked:
                estimators = list(picked)
            finite_vals = [v for v in picked.values() if np.isfinite(v)]
            rank_map = {}
            if finite_vals:
                rank_map = dict(zip([k for k, v in picked.items() if np.isfinite(v)],
                                    pd.Series(finite_vals).rank(method="average", pct=True).to_numpy()))
            for estimator in (estimators or list(picked)):
                profiles.append({"controle": control, "question": short, "estimateur": estimator,
                                 "rang_relatif": rank_map.get(estimator, np.nan)})
        coverage.append(row_coverage)
        for metric, by_flux in (rp.get("transition_analysis") or {}).items():
            for flux, data in by_flux.items():
                if not isinstance(data, dict):
                    continue
                f_records.append({
                    "controle": control, "estimateur": metric, "flux": flux,
                    "F1_avant": data.get("first_derivative_pre"), "F1_apres": data.get("first_derivative"),
                    "F2_avant": data.get("second_derivative_pre"), "F2_apres": data.get("second_derivative"),
                    "n_avant": data.get("points_count_pre"), "n_apres": data.get("points_count"),
                    "statut_avant": data.get("status_pre"), "statut_apres": data.get("status"),
                    "fenetre_avant": data.get("window_pre"), "fenetre_apres": data.get("window_post"),
                })
    if not coverage:
        return
    controls_order = list(controls)
    coverage_arr = np.array(coverage, dtype=float)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    image = ax.imshow(coverage_arr, aspect="auto", cmap="Blues", vmin=0, vmax=29)
    ax.set_xticks(range(len(question_defs)), [x[0] for x in question_defs])
    ax.set_yticks(range(len(controls_order)), controls_order)
    for i in range(len(controls_order)):
        for j in range(len(question_defs)):
            ax.text(j, i, f"{int(coverage_arr[i, j])}/29", ha="center", va="center",
                    color="white" if coverage_arr[i, j] >= 17 else "#17324d", fontsize=9)
    ax.set_title("Couverture des estimateurs selon contrôle et question — L=16")
    ax.set_xlabel("Question")
    ax.set_ylabel("Axe de contrôle")
    fig.colorbar(image, ax=ax, pad=.025, label="Nombre de scores finis (sur 29)")
    fig.tight_layout()
    save(fig, "couverture_Q1_Q6_par_controle_L16.png")

    score_df = pd.DataFrame(records)
    profile_df = pd.DataFrame(profiles)
    if not score_df.empty:
        score_df.to_csv(OUT / "scores_Q1_Q6_multi_controle_L16_long.csv", index=False, encoding="utf-8")
    if not profile_df.empty:
        pivot = profile_df.pivot_table(index="estimateur", columns=["controle", "question"],
                                       values="rang_relatif", aggfunc="first")
        pivot = pivot.reindex(columns=pd.MultiIndex.from_tuples(
            [(control, short) for control in controls_order for short, _ in question_defs]))
        fig, ax = plt.subplots(figsize=(17, 9.5))
        cmap = plt.get_cmap("viridis").copy()
        cmap.set_bad("#D9D9D9")
        image = ax.imshow(np.ma.masked_invalid(pivot.to_numpy(float)), aspect="auto", cmap=cmap,
                          interpolation="nearest", vmin=0, vmax=1)
        xlabels = [f"{control}\n{question}" for control, question in pivot.columns]
        ax.set_xticks(range(len(xlabels)), xlabels, rotation=55, ha="right", fontsize=7.5)
        ax.set_yticks(range(len(pivot.index)), list(pivot.index), fontsize=8)
        ax.set_title("Profil Q1–Q6 par contrôle — rangs relatifs dans chaque question", pad=18)
        ax.set_ylabel("Estimateur")
        fig.colorbar(image, ax=ax, pad=.015, fraction=.025, label="Rang relatif (0–1); pas une taille d’effet comparable")
        fig.subplots_adjust(left=.17, right=.91, top=.92, bottom=.24)
        fig.text(.5, .02, "Chaque colonne classe les estimateurs à l’intérieur d’un contrôle × question. Gris = non fini/absent. "
                 "Les valeurs brutes sont dans le CSV long.", ha="center", fontsize=9)
        save(fig, "profils_Q1_Q6_par_controle_L16.png")
    if f_records:
        pd.DataFrame(f_records).to_csv(OUT / "derivees_F1_F2_multi_controle_L16_long.csv", index=False, encoding="utf-8")


def fig_sensitivity(runs):
    base = multi_controls(runs).get("Temperature", {})
    entries = [("Référence · graine 20261115", base.get("t0_control_value_raw"), base.get("t0_pct"), "multi-control")]
    run_ids = [
        ("Graine 42", "sensitivity_L16_seed_42"),
        ("Graine 123", "sensitivity_L16_seed_123"),
        ("Ordre inversé", "negative_L16_reverse_row_order"),
        ("Bruit indépendant ajouté", "negative_L16_independent_noise_flow"),
        ("Flux énergie affine ajouté", "sensitivity_L16_redundant_energy_flow"),
    ]
    for label, rid in run_ids:
        item = runs.get(rid, {})
        if item.get("status") == "complete":
            rec = t0_record(master_for(item))
            entries.append((label, rec.get("raw"), rec.get("percent"), rid))
        else:
            entries.append((label, None, None, rid))
    visible = [(label, raw, pct, rid) for label, raw, pct, rid in entries if isinstance(raw, (float, int))]
    if not visible:
        return entries
    fig, ax = plt.subplots(figsize=(10, 5.6))
    y = np.arange(len(visible))
    ax.axvline(TC_EXACT, color=COLORS["gray"], linestyle="--", label=f"Tc exact = {TC_EXACT:.4f}")
    for yi, (label, raw, pct, rid) in enumerate(visible):
        color = COLORS["blue"] if yi == 0 else COLORS["orange"]
        ax.scatter(float(raw), yi, s=65, color=color, edgecolor="white", zorder=3)
        ax.annotate(f"{float(raw):.3f} (rang {float(pct):.1f}%)", (float(raw), yi),
                    xytext=(7, 0), textcoords="offset points", va="center", fontsize=8.5)
    ax.set_yticks(y, [row[0] for row in visible])
    ax.invert_yaxis()
    ax.set_xlabel("T0 ramené en température (T)")
    ax.set_title("Stabilité de T0 face aux graines et variantes — L=16, contrôle T")
    ax.grid(axis="x", alpha=.2)
    ax.legend(frameon=False, loc="best")
    ax.text(.01, -.2, "Le bruit blanc et la copie affine sont des flux synthétiques ajoutés. Le renversement concerne l’ordre des lignes, "
            "pas un algorithme Reverse Monte Carlo. Chaque point reste une exécution, sans inférence statistique entre variantes.",
            transform=ax.transAxes, fontsize=8.5, color="#444444", va="top", wrap=True)
    fig.subplots_adjust(bottom=.27, right=.86, left=.28)
    save(fig, "sensibilite_T0_graines_flux_L16.png")
    return entries


def fig_blind_flux_comparison(runs):
    manifest_path = HERE / "blind_flux_sensitivity_manifest.json"
    blind_manifest = read_json(manifest_path)
    blind_path = Path(blind_manifest.get("output_path", "")) / "master_results.json"
    blind = read_json(blind_path) if blind_path.exists() else {}
    full_run = runs.get("primary_L64_temperature", {})
    full = master_for(full_run) if full_run else {}
    if not full or not blind:
        return None
    peak = pd.read_csv(PEAKS).set_index("L").loc[64]
    records = []
    for label, master in [("Flux physiques complets", full), ("Deux colonnes (T + énergie)", blind)]:
        rec = t0_record(master)
        cascade = master.get("five_threshold_cascade") or {}
        holo = master.get("holographic_tension_state") or {}
        tri = (holo.get("tension_gap_diagnostics") or {}).get("triangulation") or {}
        pred = master.get("prediction_levels") or {}
        records.append({"configuration": label, "L": 64, "n_lignes": master.get("metadata", {}).get("n_samples"),
                        "T0_rang_pct": rec.get("percent"), "T0_temperature": rec.get("raw"),
                        "T0_local_low_5_lignes": rec.get("low"), "T0_local_high_5_lignes": rec.get("high"),
                        "axe_monotone": rec.get("monotone"), "conversion_ambigue": rec.get("ambiguous"),
                        "L7a": ((pred.get("L7a_coherence") or {}).get("consensus_direction")),
                        "L7b": ((pred.get("L7b_robustesse") or {}).get("verdict")),
                        "LevinaBickel": (tri.get("trio_values") or {}).get("LevinaBickel"),
                        "voie2_trio_mode": tri.get("trio_gap_mode")})
    frame = pd.DataFrame(records)
    frame["T_chi_peak_L64"] = float(peak["T_chi_abs_peak"])
    frame["T_chi_peak_ci95_low"] = float(peak["T_chi_abs_peak_boot_low"])
    frame["T_chi_peak_ci95_high"] = float(peak["T_chi_abs_peak_boot_high"])
    frame["Tc_exact_infinite"] = TC_EXACT
    frame.to_csv(OUT / "comparaison_flux_complets_vs_deux_colonnes_L64.csv", index=False, encoding="utf-8")
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.axhspan(float(peak["T_chi_abs_peak_boot_low"]), float(peak["T_chi_abs_peak_boot_high"]),
               color=COLORS["sky"], alpha=.22, label="IC bootstrap 95 % du pic χ (référence)")
    ax.axhline(TC_EXACT, color=COLORS["gray"], linestyle="--", label=f"Tc exact = {TC_EXACT:.4f}")
    colors = [COLORS["blue"], COLORS["orange"]]
    for i, row in frame.iterrows():
        t0 = row["T0_temperature"]
        if pd.notna(t0):
            ax.scatter(i, float(t0), s=90, color=colors[i], edgecolor="white", zorder=4)
            lo, hi = row["T0_local_low_5_lignes"], row["T0_local_high_5_lignes"]
            if pd.notna(lo) and pd.notna(hi):
                ax.vlines(i, float(lo), float(hi), color=colors[i], linewidth=2)
            ax.annotate(f"T0={float(t0):.3f}", (i, float(t0)), xytext=(8, 7), textcoords="offset points")
    ax.set_xticks(range(len(frame)), frame["configuration"])
    ax.set_ylabel("Température T")
    ax.set_title("Le T0 de L=64 change-t-il quand χ/Cv/Binder ne sont plus des flux ?")
    ax.grid(axis="y", alpha=.2)
    ax.legend(frameon=False, loc="best", fontsize=8.5)
    fig.text(.5, .015, "Contrôle secondaire exploratoire choisi après le résultat principal. Les petits traits verticaux autour de T0 "
             "sont l’étendue locale sur 5 lignes, pas un intervalle de confiance.", ha="center", fontsize=8.5)
    fig.subplots_adjust(bottom=.18)
    save(fig, "comparaison_flux_complets_deux_colonnes_L64.png")
    return frame


def diagonal_comparison(runs):
    manifest = read_json(HERE / "diagonal_sensitivity_manifest.json")
    output = Path(manifest.get("output", ""))
    master = read_json(output / "master_results.json") if output else {}
    if not master:
        return None
    rec = t0_record(master)
    pred = master.get("prediction_levels") or {}
    l7a = pred.get("L7a_coherence") or pred.get("L7_consensus") or {}
    l7b = pred.get("L7b_robustesse") or {}
    rows = [{"configuration": "Énergie cible + contrôle (diagonal)", "L": 16,
             "n_lignes": master.get("metadata", {}).get("n_samples"), "controle": "Energy_per_spin",
             "cible": "Energy_per_spin", "diagonal": True, "T0_rang_pct": rec.get("percent"),
             "T0_axe_brut": rec.get("raw"), "T0_local_low_5_lignes": rec.get("low"),
             "T0_local_high_5_lignes": rec.get("high"), "axe_monotone": rec.get("monotone"),
             "conversion_ambigue": rec.get("ambiguous"), "L7a": l7a.get("consensus_direction"),
             "L7b": l7b.get("verdict"), "status": manifest.get("status") }]
    controls = multi_controls(runs)
    temperature = controls.get("Temperature", {})
    temperature_master = read_json(Path(temperature.get("output_dir", "")) / "master_results.json") if temperature else {}
    temperature_pred = temperature_master.get("prediction_levels") or {}
    temperature_l7b = (temperature_pred.get("L7b_robustesse") or {}).get("verdict")
    rows.append({"configuration": "Température contrôle (cible énergie)", "L": 16,
                 "n_lignes": 76, "controle": "Temperature", "cible": "Energy_per_spin", "diagonal": False,
                 "T0_rang_pct": temperature.get("t0_pct"), "T0_axe_brut": temperature.get("t0_control_value_raw"),
                 "T0_local_low_5_lignes": temperature.get("t0_control_value_min_near"),
                 "T0_local_high_5_lignes": temperature.get("t0_control_value_max_near"),
                 "axe_monotone": temperature.get("control_monotone"),
                 "conversion_ambigue": temperature.get("t0_control_value_ambiguous"),
                 "L7a": temperature.get("consensus"), "L7b": temperature_l7b, "status": "complete"})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "comparaison_controle_diagonal_L16.csv", index=False, encoding="utf-8")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, row in frame.iterrows():
        value = row["T0_rang_pct"]
        if pd.notna(value):
            ax.scatter(float(value), i, marker="x" if row["diagonal"] else "o",
                       color=COLORS["orange"] if row["diagonal"] else COLORS["blue"], s=75, linewidth=2)
            ax.annotate(f"{float(value):.2f}%", (float(value), i), xytext=(7, 0), textcoords="offset points", va="center")
    ax.set_yticks(range(len(frame)), frame["configuration"])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Position T0 dans l’axe choisi (%)")
    ax.set_title("Le pipeline accepte-t-il le cas contrôle = cible ? — L=16")
    ax.grid(axis="x", alpha=.2)
    fig.text(.5, .02, "Les rangs sont sur deux axes différents et ne constituent pas une comparaison physique. Le contrôle diagonal "
             "est un cas d’usage, pas une détection de Tc.", ha="center", fontsize=8.5)
    fig.subplots_adjust(bottom=.18, left=.32)
    save(fig, "controle_diagonal_cible_L16.png")
    return frame


def fig_mc_scan():
    master = read_json(RUNS / "primary_L24_temperature" / "master_results.json")
    tm = (((master.get("run_pipeline") or {}).get("threshold_metadata") or {})
          .get("threshold_optimization") or {})
    curve = tm.get("raw_mc_scan_curve") or []
    if not curve:
        return
    frame = pd.DataFrame(curve)
    xkey = next((k for k in ("threshold", "threshold_pct", "candidate", "x") if k in frame), None)
    ykey = next((k for k in ("score", "mean_score", "separation", "b_score", "value") if k in frame), None)
    if xkey is None or ykey is None:
        # Preserve the saved scan as a readable table if the curve schema differs.
        pd.DataFrame(curve).to_csv(OUT / "scan_monte_carlo_L24.csv", index=False)
        return
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.plot(frame[xkey], frame[ykey], "o-", color=COLORS["purple"], markersize=3)
    opt = tm.get("raw_mc_threshold")
    if isinstance(opt, (int, float)):
        ax.axvline(opt, color=COLORS["orange"], linestyle="--", label=f"Seuil MC choisi = {opt:g}")
        ax.legend(frameon=False)
    ax.set(title="Scan Monte-Carlo interne du seuil — L=24", xlabel="Candidat du scan interne (échelle 0–100 du code)",
           ylabel=f"Score du scan ({ykey})")
    ax.grid(alpha=.2)
    fig.subplots_adjust(bottom=.2)
    fig.text(.5, .015, f"Optimisation pipeline : {tm.get('n_iterations', '—')} itérations; "
             f"source={tm.get('threshold_source', '—')}. L’axe x n’est pas une température.",
             ha="center", fontsize=9, color="#444444")
    save(fig, "scan_monte_carlo_interne_L24.png")


def html_report(runs, points, peaks, readable):
    complete = sum(1 for r in runs.values() if r.get("status") == "complete")
    total = len(runs)
    blind_status = read_json(HERE / "blind_flux_sensitivity_manifest.json").get("status", "en attente")
    diagonal_status = read_json(HERE / "diagonal_sensitivity_manifest.json").get("status", "en attente")
    rows = []
    for L in sorted(set(peaks["L"].astype(int))):
        peak = peaks[peaks["L"].eq(L)].iloc[0]
        rec = points.get(L, {})
        raw = rec.get("raw")
        status = "En attente" if raw is None else ("T0 converti en température" if rec.get("monotone") is True and not rec.get("ambiguous") else "conversion à interpréter avec prudence")
        err_chi = float(raw) - float(peak["T_chi_abs_peak"]) if isinstance(raw, (float, int)) else None
        err_tc = float(raw) - TC_EXACT if isinstance(raw, (float, int)) else None
        rows.append(f"<tr><th>L={L}</th><td>{float(peak['T_Cv_peak']):.3f}</td>"
                    f"<td>{float(peak['T_chi_abs_peak']):.3f} "
                    f"[{float(peak['T_chi_abs_peak_boot_low']):.3f}, {float(peak['T_chi_abs_peak_boot_high']):.3f}]</td>"
                    f"<td>{'—' if raw is None else f'{float(raw):.3f}'}</td>"
                    f"<td>{'—' if err_tc is None else f'{err_tc:+.3f}'}</td>"
                    f"<td>{'—' if err_chi is None else f'{err_chi:+.3f}'}</td><td>{html.escape(status)}</td></tr>")
    available = []
    for rid, row in sorted(runs.items()):
        if row.get("status") not in ("complete", "error"):
            continue
        artifact = "controls_summary.json" if rid == "sensitivity_L16_multiple_physical_controls" else "master_results.json"
        available.append(f"<li>{html.escape(rid)} — {html.escape(str(row.get('status')))} · "
                         f"<a href='../runs/{html.escape(rid)}/{artifact}'>sortie maîtresse</a> · "
                         f"<a href='../runs/{html.escape(rid)}.log'>journal</a></li>")
    blind_manifest = read_json(HERE / "blind_flux_sensitivity_manifest.json")
    if blind_manifest.get("status"):
        available.append("<li>blind_flux_L64_temperature_energy — " + html.escape(str(blind_manifest.get("status"))
                         ) + " · <a href='../runs/blind_flux_L64_temperature_energy/master_results.json'>sortie maîtresse</a> · "
                         "<a href='../runs/blind_flux_L64_temperature_energy.log'>journal</a></li>")
    diagonal_manifest = read_json(HERE / "diagonal_sensitivity_manifest.json")
    if diagonal_manifest.get("status"):
        available.append("<li>diagonal_L16_energy_as_target_and_control — " + html.escape(str(diagonal_manifest.get("status"))
                         ) + " · <a href='../runs/diagonal_L16_energy_as_target_and_control/master_results.json'>sortie maîtresse</a> · "
                         "<a href='../runs/diagonal_L16_energy_as_target_and_control.log'>journal</a></li>")
    blocks = []
    for name, title, desc in [
        ("localisation_t0_et_reperes.png", "T0 face aux repères Ising", "Le losange orange est le seuil du pipeline converti en température; les ronds bleus sont les pics de susceptibilité du CSV de référence, avec IC bootstrap à 95 %."),
        ("croisements_binder_et_Tc.png", "Croisements du cumulant de Binder", "Chaque point est le croisement U4 entre la paire de tailles indiquée; les barres sont les IC bootstrap à 95 %."),
        ("voies_1_2_ancres_par_taille.png", "Voie 1 et ancres de Voie 2", "Le graphique conserve les estimateurs séparés; les trous indiquent les ancrages non calculés."),
        ("observables_physiques_L16.png", "Ce que contiennent les colonnes physiques", "Les cinq courbes montrent les entrées à L=16 et la référence Tc du modèle infini."),
        ("questions_Q1_Q6_rangs_29_estimateurs.png", "Les six questions et les 29 estimateurs", "La couleur indique un rang à l’intérieur de chaque question; elle ne compare pas les tailles de score entre questions."),
        ("derivees_F1_F2_avant_apres_L24.png", "Pentes et courbures avant/après T0", "Points bleus : avant. Points orange : après. Les segments relient les coefficients descriptifs du même flux."),
        ("scan_monte_carlo_interne_L24.png", "Comment le scan interne choisit un seuil", "Ce scan est un calcul interne au pipeline; son axe de candidat n’est pas l’axe de température.")]:
        path = FIG / name
        if path.exists():
            blocks.append(f"<section><h2>{html.escape(title)}</h2><p>{html.escape(desc)}</p><img src='figures/{name}' alt='{html.escape(title)}'></section>")
    if (OUT / "voies_1_2_par_taille.csv").exists():
        blocks.append("<section><p>Valeurs exactes des trois ancrages, Voie 1 et médianes disponibles : <a href='voies_1_2_par_taille.csv'>tableau CSV Voie 1/2 par taille</a>.</p></section>")
    blind_image = FIG / "comparaison_flux_complets_deux_colonnes_L64.png"
    if blind_image.exists():
        blocks.append("<section><h2>Sensibilité aux flux physiques fournis — L=64</h2><p>Comparaison secondaire exploratoire, décidée après les runs principaux. Le premier run voit tous les observables; le second ne reçoit que Température et Énergie. Les pics et croisements sont des repères du même jeu simulé, pas un jeu externe.</p><img src='figures/comparaison_flux_complets_deux_colonnes_L64.png' alt='Comparaison de T0 avec tous les flux ou deux colonnes'><p><a href='comparaison_flux_complets_vs_deux_colonnes_L64.csv'>Télécharger les valeurs et statuts</a> · <a href='../ADDENDUM_CONTROLE_FLUX_AVEUGLE.md'>Addendum pré-run</a></p></section>")
    diagonal_image = FIG / "controle_diagonal_cible_L16.png"
    if diagonal_image.exists():
        blocks.append("<section><h2>Quand contrôle et cible sont la même colonne — L=16</h2><p>Le cas diagonal est un usage possible du pipeline et il est signalé. Ces rangs ne sont pas un test de Tc; les sorties peuvent être circulaires ou tautologiques dans cette configuration. Le graphique compare des rangs internes, pas les unités brutes des axes.</p><img src='figures/controle_diagonal_cible_L16.png' alt='Comparaison du cas diagonal et d’un contrôle température'><p><a href='comparaison_controle_diagonal_L16.csv'>Télécharger les valeurs et avertissements</a> · <a href='../ADDENDUM_AXE_CONTROLE_EGAL_CIBLE.md'>Addendum de configuration</a></p></section>")
    controls = multi_controls(runs)
    controls_rows = []
    for name, row in controls.items():
        raw = row.get("t0_control_value_raw")
        pct = row.get("t0_pct")
        raw_text = "—" if raw is None else f"{float(raw):.5g}"
        pct_text = "—" if pct is None else f"{float(pct):.2f}%"
        controls_rows.append(f"<tr><th>{html.escape(name)}</th><td>{pct_text}</td><td>{raw_text}</td>"
                             f"<td>{html.escape(str(row.get('t0_control_value_ambiguous')))}</td>"
                             f"<td>{html.escape(str(row.get('control_monotone')))}</td>"
                             f"<td>{html.escape(str(row.get('consensus')))}</td><td>{html.escape(str(row.get('status')))}</td></tr>")
    if controls_rows:
        blocks.append("<section><h2>Axes de contrôle (L=16)</h2><p>Chaque ligne réordonne le même jeu selon une colonne différente. Les T0 bruts ne partagent pas une unité; la cible énergie reste fixe. Les contrôles sont Température, aimantation, χ, Cv et Binder; énergie n’est pas utilisé comme contrôle dans ce plan.</p>"
                      "<img src='figures/seuil_par_controle_L16.png' alt='T0 selon les axes de contrôle'>"
                      "<table><thead><tr><th>Contrôle</th><th>T0 rang</th><th>T0 axe brut</th><th>Conversion ambiguë</th><th>Axe monotone</th><th>Vote L7a</th><th>Statut</th></tr></thead><tbody>"
                      + "".join(controls_rows) + "</tbody></table></section>")
    multi_coverage = FIG / "couverture_Q1_Q6_par_controle_L16.png"
    multi_profiles = FIG / "profils_Q1_Q6_par_controle_L16.png"
    if multi_coverage.exists():
        blocks.append("<section><h2>Interactions contrôle × flux × question (L=16)</h2><p>La première carte indique combien des 29 scores du flux cible énergie sont finis. La seconde compare les profils de rang par contrôle et question; elle conserve les flux observés en sortie dans le CSV, sans moyenner les tailles d’effet entre flux.</p>"
                      "<img src='figures/couverture_Q1_Q6_par_controle_L16.png' alt='Couverture Q1 à Q6 selon le contrôle'>"
                      + ("<img src='figures/profils_Q1_Q6_par_controle_L16.png' alt='Profils des 29 estimateurs selon contrôle et question'>" if multi_profiles.exists() else "")
                      + "<p><a href='scores_Q1_Q6_multi_controle_L16_long.csv'>Scores Q1–Q6 tous flux et contrôles en CSV</a> · "
                      "<a href='derivees_F1_F2_multi_controle_L16_long.csv'>F1/F2 tous estimateurs, flux et contrôles en CSV</a></p></section>")
    summary_rows = []
    for _, row in readable.iterrows():
        def cell(value):
            if pd.isna(value):
                return "—"
            if isinstance(value, (float, np.floating)):
                return f"{float(value):.3f}"
            return str(value)
        summary_rows.append("<tr>" + "".join(f"<td>{html.escape(cell(value))}</td>" for value in [
            row.get("run_id"), row.get("controle"), row.get("T0_rang_pct"), row.get("T0_axe_brut"),
            row.get("L7a_vote"), row.get("L7b_robustesse"), row.get("voie2_statut")]) + "</tr>")
    if summary_rows:
        blocks.insert(0, "<section><h2>Tableau court des sorties</h2><p>Une ligne par run et contrôle. L7a est le vote de cohérence interne; L7b évalue séparément la robustesse. Utilisez le CSV lisible pour les nombres non arrondis, couvertures Q1–Q6, F1/F2, Monte-Carlo et trois ancres.</p>"
                      "<div style='overflow-x:auto'><table><thead><tr><th>Run</th><th>Contrôle</th><th>T0 rang (%)</th><th>T0 axe brut</th><th>Vote L7a</th><th>Robustesse L7b</th><th>Voie 2</th></tr></thead><tbody>"
                      + "".join(summary_rows) + "</tbody></table></div><p><a href='resultats_synthese_lisible.csv'>Télécharger la synthèse lisible CSV</a></p></section>")
    l24 = read_json(RUNS / "primary_L24_temperature" / "master_results.json")
    score_map = ((l24.get("run_pipeline") or {}).get("scores") or {})
    q3_flag = (l24.get("holographic_tension_state") or {}).get("q3_identical_to_q1")
    q4 = [v for k, v in (score_map.get("Q4_Persistence") or {}).items()
          if k.startswith("Energy_per_spin_") and k.endswith("_mean") and isinstance(v, (int, float)) and np.isfinite(v)]
    q4_constant = bool(q4) and (max(q4) - min(q4) < 1e-12)
    q_notes = []
    if q3_flag:
        q_notes.append("Pour cet essai, le diagnostic du pipeline indique que Q3 recopie Q1.")
    if q4_constant:
        q_notes.append(f"Pour cet essai, les valeurs Q4 des estimateurs affichés sont identiques ({q4[0]:.4g}); la rangée uniforme ne signifie pas une différence nulle.")
    if q_notes:
        blocks.append("<section><h2>À surveiller dans les questions</h2><ul>" + "".join(f"<li>{html.escape(n)}</li>" for n in q_notes) + "</ul><p>Ce sont des constats de structure des sorties, pas une conclusion physique. Les comptes de valeurs manquantes restent dans la synthèse CSV.</p></section>")
    sensitivity_path = FIG / "sensibilite_T0_graines_flux_L16.png"
    if sensitivity_path.exists():
        blocks.append("<section><h2>Graines et flux ajoutés (L=16)</h2><p>Le protocole compare plusieurs graines, l’ordre inversé des lignes, un bruit blanc synthétique et une copie affine exacte de l’énergie. Ces variantes testent la sensibilité des sorties, pas la validité universelle.</p><img src='figures/sensibilite_T0_graines_flux_L16.png' alt='Sensibilité de T0 aux graines et flux'></section>")
    html_text = f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Guide visuel — audit Ising v6</title><style>
body{{font:16px/1.55 system-ui,Segoe UI,Arial,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1.2rem;color:#19212b;background:#fff}}
h1,h2{{line-height:1.2;color:#132b44}}h1{{font-size:2rem}}section,.card{{margin:1.5rem 0;padding:1.2rem;border:1px solid #d7e0e8;border-radius:10px;background:#fbfcfd}}
img{{width:100%;height:auto;border:1px solid #e3e7eb;border-radius:5px}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{text-align:left;border-bottom:1px solid #ccd5dd;padding:.55rem;vertical-align:top}}th{{background:#edf3f7}}
.note{{border-left:4px solid #0072B2;padding:.7rem 1rem;background:#eef7fb}}.warn{{border-left-color:#D55E00;background:#fff5ef}}small{{color:#4b5661}}
a{{color:#005a8d}}code{{background:#edf0f2;padding:.1rem .25rem;border-radius:3px}}
</style></head><body>
<h1>Guide visuel des résultats Ising — pipeline v6</h1>
<p><strong>État du calcul :</strong> {complete}/{total} configurations principales terminées (le run multi-contrôle contient cinq axes); contrôle flux réduit : {html.escape(str(blind_status))}; contrôle diagonal : {html.escape(str(diagonal_status))}. Ce document se met à jour en relançant <code>build_reader_report.py</code>.</p>
<div class='note warn'><strong>À retenir :</strong> ce benchmark vérifie comment le pipeline se comporte sur des données Ising connues. Il ne démontre pas l’universalité de la théorie. T0, Q1–Q6 et F1/F2 sont des sorties descriptives/heuristiques de cette version.</div>
<section><h2>Lire le tableau en une minute</h2><p><strong>Pic Cv</strong> et <strong>pic χ</strong> sont des repères physiques calculés séparément par taille. L’IC bootstrap à 95 % du pic χ provient du fichier de référence. <strong>T0</strong> est le seuil choisi par le pipeline, ramené en température si l’axe est monotone. Les deux écarts séparent proximité avec Tc exact et proximité avec le pic χ fini; T0 est une seule exécution, sans IC ici.</p>
<table><thead><tr><th>Taille</th><th>Pic Cv</th><th>Pic χ (IC bootstrap 95 %)</th><th>T0 brut</th><th>T0 − Tc exact</th><th>T0 − pic χ</th><th>Conversion</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p>Le petit trait vertical orange du graphique T0 montre l’étendue des 5 lignes de contrôle les plus proches; il ne s’agit pas d’un intervalle de confiance.</p><p><a href='reperes_physiques_et_T0.csv'>Télécharger les repères physiques et T0 en CSV</a></p></section>
<section><h2>Quelles données entrent dans le pipeline ?</h2><p>Pour chaque taille L, le pipeline reçoit un tableau résumé de 76 températures, pas une trajectoire brute de spins. Les observables viennent de la simulation 2D Ising par grappes de Wolff : 3 chaînes, 4 000 mesures et 500 mises à jour de chauffe par chaîne et température; les IC physiques sont issues de 500 réplications bootstrap en blocs de 80 mesures. Le n=76 des couches géométriques est le nombre de lignes analysées, pas le nombre de spins L². Les sources et scripts sont dans l’archive jointe.</p></section>
<section><h2>Ce qui est calculé et ce qui est interprété</h2><ul><li><strong>Voie 1 :</strong> Higuchi seul, affiché comme une mesure partielle.</li><li><strong>Voie 2 :</strong> plusieurs ancres restent séparées; si une ancre manque, la triangulation est signalée comme incomplète.</li><li><strong>Monte-Carlo :</strong> distinguer la simulation physique des spins, l’optimisation MC interne du seuil et les permutations/bootstrap d’audit.</li><li><strong>Q1–Q6 :</strong> six sorties distinctes; zéro, absent et non calculé ne doivent pas être confondus.</li><li><strong>F1/F2 :</strong> pente et courbure ajustées avant/après le seuil; descriptives, sans intervalle d’incertitude fourni ici.</li></ul></section>
<section><h2>Le TLog fait partie d’une théorie opérationnelle plus large</h2><p>Le benchmark conserve la chaîne entière : fichier et choix des flux/axes, scan du seuil et optimisation Monte-Carlo, 29 estimateurs, Q1–Q6, cascade T−2 à T+2, F1/F2 avant/après, Voie 1 et Voie 2, puis niveaux L1–L7a/L7b et lecture. La quantité TLog produite par le code est une couche de cette chaîne; elle n’est pas utilisée ici comme substitut à l’analyse complète. La formule exacte, les rôles et les réserves sont détaillés dans le guide de lecture.</p></section>
{''.join(blocks)}
<section><h2>Pilote synthétique à vérité connue — résultats v1</h2><p>Le pilote a terminé quatre calculs N=76; trois séries courtes (N=7, 15, 30) ont été refusées avant le calcul, car la configuration fast exige au moins 50 points. La marche N=76 donne T0=48,803 % avec ou sans flux additionnels; les valeurs Q et les médianes TLog changent toutefois avec la configuration des flux. Les cas AR(1) stationnaire et dérive lisse renvoient aussi une position T0, qui n'est pas qualifiée de faux positif faute de règle d'alerte pré-déclarée. Une réalisation par cas : résultat descriptif, non confirmatoire.</p><img src='../synthetic_pilot_v1/pilot_overview.png' alt='T0 et couverture des estimateurs dans le pilote synthétique'><p><a href='../synthetic_pilot_v1/PILOT_REPORT_FR.md'>Rapport détaillé</a> · <a href='../synthetic_pilot_v1/pilot_spec.json'>Configuration et empreintes gelées</a> · <a href='../synthetic_pilot_v1/scored_pilot_results.json'>Résultats notés JSON</a> · <a href='../synthetic_pilot_v1/scored_pilot_summary.csv'>Résumé CSV</a> · <a href='../synthetic_pilot_v1/PILOT_PROTOCOL_FR.md'>Protocole pré-déclaré</a> · <a href='../synthetic_pilot_v1/truth_private/truth.json'>Vérité génératrice (consultée après les runs)</a></p></section>
<section><h2>Traces et reproduction</h2><p>Les sorties brutes restent la source complète. Les liens ci-dessous ouvrent le JSON maître; chaque dossier de run contient aussi le CSV d’entrée, les figures d’origine et le journal texte.</p><ul>{''.join(available)}</ul>
<p><a href='../PROTOCOL_PIPELINE_COMPLET_V6.md'>Protocole gelé</a> · <a href='../CONTRAT_CONFIGURATION_UNIVERSEL_V1.md'>Contrat de configuration proposé</a> · <a href='../PROTOCOLE_BANC_ESSAI_SYNTHETIQUE_V1.md'>Banc synthétique proposé</a> · <a href='../REVUE_AVIS_AUTRE_IA_2026-11-15.md'>Revue de l’avis externe</a> · <a href='../REFERENCES/avis_autre_IA_texte_brut.txt'>Texte brut de l’avis</a> · <a href='../DIAGNOSTIC_LEVINA_SUPPORT.json'>Diagnostic Levina–Bickel (JSON)</a> · <a href='../ADDENDUM_CONTROLE_FLUX_AVEUGLE.md'>Addendum du contrôle à deux flux</a> · <a href='../ADDENDUM_AXE_CONTROLE_EGAL_CIBLE.md'>Addendum contrôle=cible</a> · <a href='../ERRATA_ET_JOURNAL.md'>Journal des choix et errata</a> · <a href='../GUIDE_LECTURE_PIPELINE_FR.md'>Guide des termes</a> · <a href='../REPRODUCTION_FR.md'>Reproduire les analyses</a> · <a href='../run_pipeline_v6_ising.py'>Script reproductible de lancement</a> · <a href='../pipeline_v6_ising_summary.csv'>Résumé CSV complet</a></p></section>
<p><small>Généré depuis les sorties enregistrées localement; aucune sortie brute du pipeline n’est modifiée. Tc exact du modèle carré 2D isotrope à champ nul, pour J=kB=1 : {TC_EXACT:.12f}; référence primaire : <a href='https://journals.aps.org/pr/abstract/10.1103/PhysRev.65.117'>Onsager, Physical Review 65 (1944)</a>.</small></p>
</body></html>"""
    (OUT / "index.html").write_text(html_text, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runs = load_runs()
    points, peaks = fig_localization(runs)
    blind_frame = fig_blind_flux_comparison(runs)
    diagonal_frame = diagonal_comparison(runs)
    readable = write_readable_summary(runs, peaks, blind_frame, diagonal_frame)
    fig_pathways_by_size(readable)
    fig_binder_crossings()
    fig_observables()
    fig_question_heatmap(runs)
    fig_f1_f2()
    fig_mc_scan()
    fig_multi_control(runs)
    fig_multi_axis_questions(runs)
    fig_sensitivity(runs)
    html_report(runs, points, peaks, readable)
    outputs = [OUT / "index.html", OUT / "resultats_synthese_lisible.csv", OUT / "reperes_physiques_et_T0.csv",
               OUT / "voies_1_2_par_taille.csv",
               OUT / "comparaison_flux_complets_vs_deux_colonnes_L64.csv", OUT / "comparaison_controle_diagonal_L16.csv",
               OUT / "scores_Q1_Q6_L24_long.csv", OUT / "scores_Q1_Q6_multi_controle_L16_long.csv",
               OUT / "derivees_F1_F2_multi_controle_L16_long.csv",
               *sorted(FIG.glob("*.png"))]
    outputs = [path for path in outputs if path.is_file()]
    manifest = {
        "report_script": str(Path(__file__).resolve()),
        "report_script_sha256": sha256(Path(__file__).resolve()),
        "source_state": str(STATE.resolve()),
        "source_state_sha256": sha256(STATE),
        "source_peak_table": str(PEAKS.resolve()),
        "source_peak_table_sha256": sha256(PEAKS),
        "source_binder_crossings": str(BINDER_CROSSINGS.resolve()),
        "source_binder_crossings_sha256": sha256(BINDER_CROSSINGS),
        "source_ising_data": str(DATA.resolve()),
        "source_ising_data_sha256": sha256(DATA),
        "pipeline_manifest_sha256": sha256(HERE / "pipeline_v6_ising_manifest.json"),
        "blind_flux_addendum_sha256": sha256(HERE / "ADDENDUM_CONTROLE_FLUX_AVEUGLE.md"),
        "diagonal_addendum_sha256": sha256(HERE / "ADDENDUM_AXE_CONTROLE_EGAL_CIBLE.md"),
        "configuration_contract_sha256": sha256(HERE / "CONTRAT_CONFIGURATION_UNIVERSEL_V1.md"),
        "synthetic_benchmark_protocol_sha256": sha256(HERE / "PROTOCOLE_BANC_ESSAI_SYNTHETIQUE_V1.md"),
        "external_ai_review_sha256": sha256(HERE / "REVUE_AVIS_AUTRE_IA_2026-11-15.md"),
        "external_ai_source_attachment_sha256": sha256(HERE / "REFERENCES" / "avis_autre_IA_texte_brut.txt"),
        "levina_diagnostic_script_sha256": sha256(HERE / "diagnose_levina_support.py"),
        "levina_diagnostic_result_sha256": sha256(HERE / "DIAGNOSTIC_LEVINA_SUPPORT.json"),
        "synthetic_pilot_spec_sha256": sha256(HERE / "synthetic_pilot_v1" / "pilot_spec.json"),
        "synthetic_pilot_runner_sha256": sha256(HERE / "synthetic_pilot_v1" / "run_synthetic_pilot.py"),
        "synthetic_pilot_scorer_sha256": sha256(HERE / "synthetic_pilot_v1" / "score_synthetic_pilot.py"),
        "synthetic_pilot_truth_sha256": sha256(HERE / "synthetic_pilot_v1" / "truth_private" / "truth.json"),
        "synthetic_pilot_results_sha256": sha256(HERE / "synthetic_pilot_v1" / "scored_pilot_results.json"),
        "synthetic_pilot_report_sha256": sha256(HERE / "synthetic_pilot_v1" / "PILOT_REPORT_FR.md"),
        "synthetic_pilot_figure_sha256": sha256(HERE / "synthetic_pilot_v1" / "pilot_overview.png"),
        "synthetic_pilot_completed_run_count": sum(r.get("status") == "complete" for r in json.loads((HERE / "synthetic_pilot_v1" / "run_state.json").read_text(encoding="utf-8")).get("cases", {}).values()),
        "blind_flux_manifest_sha256": sha256(HERE / "blind_flux_sensitivity_manifest.json") if (HERE / "blind_flux_sensitivity_manifest.json").exists() else None,
        "diagonal_manifest_sha256": sha256(HERE / "diagonal_sensitivity_manifest.json") if (HERE / "diagonal_sensitivity_manifest.json").exists() else None,
        "completed_run_count_at_generation": sum(r.get("status") == "complete" for r in runs.values()),
        "outputs": [{"path": str(p.resolve()), "sha256": sha256(p), "bytes": p.stat().st_size} for p in outputs],
    }
    (OUT / "reader_report_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Guide visuel : {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
