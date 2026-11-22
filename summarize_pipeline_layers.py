#!/usr/bin/env python
"""Summarize the major v6.0.1 outputs beyond T0, without interpreting them as truth."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


Q_KEYS = [
    "Q1_Calme_vs_Chaos", "Q2_Tension_Seuil", "Q3_Agressivite", "Q4_Persistence",
    "Q5_Actif_Receptif", "Q6_Actif_Receptif_Echelle",
]
Q_LABELS = ["Q1 calme/chaos", "Q2 tension/seuil", "Q3 agressivité", "Q4 persistance", "Q5 actif/réceptif", "Q6 échelle Q5"]
Q_DEFINITIONS = [
    "Taille d’effet entre progression basse et haute, pour une cellule flux × estimateur; le nom ne constitue pas un test du chaos.",
    "Même type de taille d’effet dans une marge avant le seuil contre une marge après.",
    "Comparaison Q1 restreinte aux flux dits agressifs; la sortie peut recopier Q1 si la couverture est faible.",
    "Séparation intra-fenêtre du flux brut, recopiée sur les colonnes d’estimateurs; ce n’est pas l’estimateur Hurst.",
    "Séparation actifs/réceptifs sur les moyennes brutes; la sortie peut être nulle si les étiquettes sont absentes.",
    "Q5 après division par l’écart-type sans centrage; cette version mise à l’échelle ne remplace pas Q5.",
]
T_KEYS = ["T_-2_F2_pre_onset", "T_-1_F1_pre_inflection", "T_0_Monte_Carlo_Central", "T_+1_F1_post_deceleration", "T_+2_F2_post_attractor"]
T_LABELS = ["T-2 F2", "T-1 F1", "T0 MC", "T+1 F1", "T+2 F2"]


def finite_values(value) -> list[float]:
    if not isinstance(value, dict):
        return []
    out = []
    for raw in value.values():
        try:
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            out.append(number)
    return out


def extract(run_key: str, state_row: dict, result_path: Path) -> dict:
    raw = json.loads(result_path.read_text(encoding="utf-8"))
    result = raw.get("result", {})
    metadata = result.get("metadata", {}) or {}
    core = result.get("run_pipeline", {}) or {}
    cascade = result.get("five_threshold_cascade", {}) or {}
    holo = result.get("holographic_tension_state", {}) or {}
    geometry = holo.get("geometric_layer", {}) or {}
    pred = result.get("prediction_levels", {}) or {}
    l1 = pred.get("L1_L2_target", {}) or {}
    l7a = pred.get("L7a_coherence", {}) or {}
    l7b = pred.get("L7b_robustesse", {}) or {}
    checks = l7b.get("checks", {}) or {}
    noise = core.get("noise_diagnostic", {}) or {}
    tools = result.get("instrumental_tool_footprint", {}) or {}
    q_scores = core.get("scores", {}) or {}
    class_medians = geometry.get("T_log_class_median", {}) or {}
    class_medians = class_medians if isinstance(class_medians, dict) else {}
    flux_stats = metadata.get("global_flux_stats", {}) or {}
    estimator_classes = metadata.get("estimator_classes", {}) or {}
    estimator_names = {name for group in estimator_classes.values() for name in (group or [])}
    row = {
        "run_key": run_key,
        "control": metadata.get("control"),
        "target_requested": metadata.get("target_requested"),
        "target_used": metadata.get("target_used"),
        "target_fallback_used": metadata.get("target_fallback_used"),
        "target_fallback_reason": metadata.get("target_fallback_reason"),
        "target_matches_request": metadata.get("target_requested") == metadata.get("target_used"),
        "n_samples": metadata.get("n_samples"),
        "analysis_flux_count": len(flux_stats),
        "control_excluded_from_analysis_fluxes": metadata.get("control") not in flux_stats,
        "estimator_count": len(estimator_names),
        "cascade_status": cascade.get("status"),
        "F1_max_velocity": cascade.get("max_F1_velocity"),
        "F2_max_curvature": cascade.get("max_F2_curvature"),
        "T_log_formula": geometry.get("T_log_formula"),
        "T_log_scope": geometry.get("T_log_scope"),
        "Delta_tension": holo.get("Delta_tension"),
        "regime_label": holo.get("dominant_regime"),
        "regime_status": holo.get("status"),
        "Q3_identical_to_Q1": holo.get("q3_identical_to_q1"),
        "L1_status": l1.get("status"),
        "L1_direction": l1.get("direction"),
        "L1_confidence": l1.get("confidence"),
        "internal_walkforward_rmse": (l1.get("walk_forward", {}) or {}).get("mean_rmse"),
        "internal_walkforward_mae": (l1.get("walk_forward", {}) or {}).get("mean_mae"),
        "internal_walkforward_directional_accuracy_pct": (l1.get("walk_forward", {}) or {}).get("directional_accuracy_pct"),
        "L7a_status": l7a.get("status"),
        "L7a_direction": l7a.get("consensus_direction"),
        "L7a_confidence": l7a.get("global_confidence"),
        "L7b_status": l7b.get("status"),
        "L7b_verdict": l7b.get("verdict"),
        "early_warning_status": (result.get("early_warning_alert", {}) or {}).get("status"),
        "noise_diagnostic_label": noise.get("diagnostic_label"),
        "noise_verdict_level": noise.get("verdict_level"),
        "tool_footprint_detected": tools.get("has_tool_footprint"),
        "tool_footprint_zero_difference_rate_pct": tools.get("zero_difference_rate_pct"),
        "tool_footprint_discrete_levels_count": tools.get("discrete_levels_count"),
        "elapsed_seconds": state_row.get("elapsed_seconds"),
    }
    threshold_meta = core.get("threshold_metadata", {}) or {}
    t0 = (metadata.get("thresholds_in_control_units", {}) or {}).get("T_0_Monte_Carlo_Central", {}) or {}
    row["threshold_status"] = threshold_meta.get("threshold_status")
    row["T0_pct"] = t0.get("threshold_pct")
    row["T0_raw"] = t0.get("control_value_raw")
    row["T0_raw_ambiguous"] = t0.get("ambiguous")
    for key in T_KEYS:
        row[key + "_pct"] = cascade.get(key)
    for question in Q_KEYS:
        vals = finite_values(q_scores.get(question, {}))
        row[question + "_median"] = float(np.median(vals)) if vals else None
        row[question + "_n_finite"] = len(vals)
    for class_name in ["saturation", "criticality", "divergence", "null_reference"]:
        row["T_log_" + class_name + "_class_median"] = class_medians.get(class_name)
    for check_name in ["stabilite_horizon", "stabilite_walkforward", "coherence_interne"]:
        check = checks.get(check_name, {}) or {}
        row["L7b_" + check_name + "_status"] = check.get("statut")
        row["L7b_" + check_name + "_detail"] = check.get("detail")
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_dir", type=Path)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    campaign = args.campaign_dir.resolve()
    state_path = campaign / "run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    rows = []
    for run_key, state_row in state.get("runs", {}).items():
        path = campaign / "runs" / run_key / "pipeline_result.json"
        if path.is_file() and state_row.get("status") == "complete":
            rows.append(extract(run_key, state_row, path))
    if not rows:
        raise RuntimeError("No completed pipeline_result.json files were found.")
    frame = pd.DataFrame(rows)
    stem = f"PIPELINE_LAYERS_{args.label}"
    csv_path = campaign / f"{stem}_SUMMARY.csv"
    report_path = campaign / f"{stem}_REPORT_FR.md"
    heatmap_path = campaign / f"{stem}_QUESTIONS_HEATMAP.png"
    cascade_path = campaign / f"{stem}_CASCADE_THRESHOLDS.png"
    tlog_path = campaign / f"{stem}_TLOG_CLASSES.png"
    frame.to_csv(csv_path, index=False, float_format="%.10g")

    qcols = [key + "_median" for key in Q_KEYS]
    qmatrix = frame[qcols].apply(pd.to_numeric, errors="coerce")
    qz = qmatrix.copy()
    for col in qcols:
        sd = qmatrix[col].std(ddof=0)
        qz[col] = 0.0 if not sd or not math.isfinite(sd) else (qmatrix[col] - qmatrix[col].mean()) / sd
    fig, ax = plt.subplots(figsize=(11, max(4.5, 0.42 * len(frame))))
    im = ax.imshow(qz.to_numpy(dtype=float), aspect="auto", cmap="coolwarm", vmin=-2, vmax=2)
    ax.set_yticks(range(len(frame)), frame["control"].astype(str))
    ax.set_xticks(range(len(Q_LABELS)), Q_LABELS, rotation=30, ha="right")
    ax.set_title("Médianes Q1-Q6 par contrôle (z-score séparé par question; descriptif)")
    fig.colorbar(im, ax=ax, label="z-score dans une question, entre axes")
    fig.tight_layout()
    fig.savefig(heatmap_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, max(4.5, 0.42 * len(frame))))
    x = np.arange(len(frame))
    for key, label in zip(T_KEYS, T_LABELS):
        ax.plot(x, pd.to_numeric(frame[key + "_pct"], errors="coerce"), marker="o", label=label)
    ax.set_xticks(x, frame["control"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("Progression (%)")
    ax.set_title("Cascade des cinq seuils par axe de contrôle")
    ax.grid(alpha=0.22)
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(cascade_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    class_names = ["saturation", "criticality", "divergence", "null_reference"]
    for class_name in class_names:
        ax.plot(x, pd.to_numeric(frame["T_log_" + class_name + "_class_median"], errors="coerce"), marker="o", label=class_name)
    ax.set_xticks(x, frame["control"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("Médiane de T_log géométrique (valeur brute du pipeline)")
    ax.set_title("T_log par classe du pipeline et axe de contrôle")
    ax.grid(alpha=0.22)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(tlog_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    lines = [
        f"# UNIVERSAL_LOG — sorties multi-couches ({args.label})", "",
        f"**Exécutions complètes incluses :** {len(frame)}. Ce document résume des sorties logicielles; il ne les transforme pas en faits sur le domaine.", "",
        "## Sorties des six questions", "",
        "Pour chaque exécution, chaque médiane ci-dessous est calculée sur les cellules finies flux × estimateur de la matrice correspondante; le compte exact est dans le CSV. Les Q ont des définitions et échelles différentes : leurs valeurs ne sont pas comparées entre questions. La figure standardise séparément chaque Q entre axes pour visualiser la sensibilité de configuration; un z-score de figure n’est ni p-value ni significativité.", "",
        "| Contrôle | Cible utilisée | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q3=Q1 signalé |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in frame.iterrows():
        qvalues = ["NA" if pd.isna(row[key + "_median"]) else f"{row[key + '_median']:.5g}" for key in Q_KEYS]
        lines.append(f"| {row['control']} | {row['target_used']} | " + " | ".join(qvalues) + f" | {row['Q3_identical_to_Q1']} |")
    lines.extend(["", "## Définitions des six sorties Q inscrites dans le code", ""])
    for label, definition in zip(Q_LABELS, Q_DEFINITIONS):
        lines.append(f"- **{label} :** {definition}")
    lines.extend(["", "## Cascade et dérivées F1/F2", "", "| Contrôle | T-2 F2 (%) | T-1 F1 (%) | T0 MC (%) | T+1 F1 (%) | T+2 F2 (%) | max F1 velocity | max F2 curvature |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for _, row in frame.iterrows():
        values = [row[key + "_pct"] for key in T_KEYS]
        fmt = ["NA" if pd.isna(v) else f"{v:.3f}" for v in values]
        f1 = "NA" if pd.isna(row["F1_max_velocity"]) else f"{row['F1_max_velocity']:.6g}"
        f2 = "NA" if pd.isna(row["F2_max_curvature"]) else f"{row['F2_max_curvature']:.6g}"
        lines.append(f"| {row['control']} | " + " | ".join(fmt) + f" | {f1} | {f2} |")
    lines.extend(["", "## TLog et états calculés", "", "La formule inscrite par v6.0.1 dans ces sorties est `(d-4)*log(n)`; l’échelle `n` est le nombre d’échantillons. Le code lui-même précise qu’il s’agit d’un indicateur de coupe sur les dimensions géométriques, pas de l’hologramme entier. Les médianes de classe ci-dessous restent des sorties du modèle et ne valident aucune transition dans le domaine.", "", "| Contrôle | T_log saturation | T_log criticality | T_log divergence | T_log null | Delta tension | étiquette de régime | état L7a / sens / confiance | L7b verdict |", "|---|---:|---:|---:|---:|---:|---|---|---|"])
    for _, row in frame.iterrows():
        classvals = [row[f"T_log_{name}_class_median"] for name in ["saturation", "criticality", "divergence", "null_reference"]]
        classfmt = ["NA" if pd.isna(v) else f"{v:.5g}" for v in classvals]
        delta = "NA" if pd.isna(row["Delta_tension"]) else f"{row['Delta_tension']:.5g}"
        lines.append(f"| {row['control']} | " + " | ".join(classfmt) + f" | {delta} | {row['regime_label']} | {row['L7a_status']} / {row['L7a_direction']} / {row['L7a_confidence']} | {row['L7b_verdict']} |")
    lines.extend(["", "## États prédictifs internes, bruit et robustesse", "", "Les niveaux `L1_L2_target` et `L7a/L7b` sont les diagnostics internes du pipeline. Ils sont publiés comme tels, sans être mélangés au benchmark prédictif indépendant. Pour cet axe `L1`, le CSV conserve aussi MAE/RMSE, exactitude directionnelle et stabilité T0 du walk-forward interne; le test conventionnel hors-échantillon est un autre objet.", "", "| Contrôle | L1 statut/sens | RMSE interne | exactitude directionnelle | stabilité T0 | alerte | bruit | empreinte outil | L7b horizon / walk-forward / cohérence |", "|---|---|---:|---:|---:|---|---|---|---|"])
    for _, row in frame.iterrows():
        internal = "NA" if pd.isna(row["internal_walkforward_rmse"]) else f"{row['internal_walkforward_rmse']:.5g}"
        directional = "NA" if pd.isna(row["internal_walkforward_directional_accuracy_pct"]) else f"{row['internal_walkforward_directional_accuracy_pct']:.4g}%"
        stab = "NA" if pd.isna(row["L7b_stabilite_walkforward_status"]) else str(row["L7b_stabilite_walkforward_status"])
        checks = "/".join(str(row["L7b_" + name + "_status"]) for name in ["stabilite_horizon", "stabilite_walkforward", "coherence_interne"])
        lines.append(f"| {row['control']} | {row['L1_status']} / {row['L1_direction']} | {internal} | {directional} | {stab} | {row['early_warning_status']} | {row['noise_verdict_level']} | {row['tool_footprint_detected']} | {checks} |")
    lines.extend(["", "## Portée des images et des sorties", "", "- Cascade : affiche les positions de T-2 à T+2; les axes ont des unités et ordres différents.", "- Heatmap Q : z-score descriptif séparé par question entre les contrôles; aucun seuil de significativité n’est appliqué.", "- TLog par classe : reproduit les médianes enregistrées, sans conclure que la classe est une propriété physique du système.", "- Les sorties complètes par axe contiennent les 29 estimateurs, matrices des six questions, diagnostics de bruit/CSD, analyse instrumentale, seuils, états L1-L7 et journaux. Elles sont conservées dans `runs/` et reproduites dans l’archive complète.", "- Quand `target_requested` et `target_used` diffèrent, le repli est un changement effectif de configuration. Ne pas comparer ce run comme si la cible restait constante.", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "complete", "runs": len(frame), "csv": csv_path.name, "report": report_path.name, "plots": [heatmap_path.name, cascade_path.name, tlog_path.name]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
