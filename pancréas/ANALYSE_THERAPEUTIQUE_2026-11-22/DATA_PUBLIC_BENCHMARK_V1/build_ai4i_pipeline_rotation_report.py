#!/usr/bin/env python
"""Build a path-redacted summary table, plot, and report from the rotation campaign."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE / "pipeline_control_rotation_v1"
STATE = CAMPAIGN / "run_state.json"
PLAN = CAMPAIGN / "campaign_plan.json"
SUMMARY = CAMPAIGN / "control_rotation_summary.csv"
REPORT = CAMPAIGN / "AI4I_PIPELINE_CONTROL_ROTATION_V1_REPORT_FR.md"
PLOT = CAMPAIGN / "t0_by_control_v1.png"
MANIFEST = CAMPAIGN / "public_summary_manifest.json"
SOURCE = HERE / "source" / "ai4i2020.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8"))
    rows = []
    for run in plan["planned_runs"]:
        record = state["runs"].get(run["run_key"], {"status": "pending"})
        summary = record.get("summary", {})
        result_file = CAMPAIGN / "runs" / run["run_key"] / "pipeline_result.json"
        raw_metadata = {}
        if result_file.is_file():
            raw_metadata = (json.loads(result_file.read_text(encoding="utf-8")).get("result", {}).get("metadata", {}) or {})
        rows.append({
            "run_key": run["run_key"],
            "control": run["control"],
            "status": record.get("status", "pending"),
            "diagonal_control_requested": run["diagonal_control_equals_target"],
            "target_requested": summary.get("target_requested"),
            "target_used": summary.get("target_used"),
            "target_fallback_used": raw_metadata.get("target_fallback_used"),
            "target_fallback_reason": raw_metadata.get("target_fallback_reason"),
            "n_samples": summary.get("n_samples"),
            "control_monotone": summary.get("control_monotone"),
            "control_direction": summary.get("control_direction"),
            "t0_status": summary.get("t0_status"),
            "t0_pct": summary.get("t0_pct"),
            "t0_raw_control_value": summary.get("t0_raw_control_value"),
            "t0_raw_control_ambiguous": summary.get("t0_raw_control_ambiguous"),
            "analysis_flux_count": summary.get("analysis_flux_count"),
            "control_excluded_from_analysis_fluxes": summary.get("control_excluded_from_analysis_fluxes"),
            "estimator_count": summary.get("estimator_count"),
            "pipeline_elapsed_seconds": summary.get("pipeline_elapsed_seconds"),
        })
    result = pd.DataFrame(rows)
    result.to_csv(SUMMARY, index=False, float_format="%.10g")
    observed = result[result["status"] == "complete"].copy()
    observed["t0_plot"] = pd.to_numeric(observed["t0_pct"], errors="coerce")
    observed = observed[observed["t0_plot"].notna()].copy().reset_index(drop=True)
    fig_height = max(6, 0.42 * max(len(observed), 1))
    fig, ax = plt.subplots(figsize=(11, fig_height))
    colors = ["#2a6f97" if pd.notna(value) and bool(value) else "#d97706" for value in observed["control_monotone"]]
    if len(observed):
        ax.barh(observed["control"], observed["t0_plot"], color=colors)
        for y, (_, row) in enumerate(observed.iterrows()):
            suffix = "  [T0 brut ambigu]" if pd.notna(row["t0_raw_control_ambiguous"]) and bool(row["t0_raw_control_ambiguous"]) else ""
            ax.text(row["t0_plot"] + 0.7, y, f"{row['t0_plot']:.1f}%{suffix}", va="center", fontsize=8)
    ax.set_xlabel("T0 (% progression/rang; valeur descriptive, pas unité physique commune)")
    ax.set_title("AI4I — sortie T0 selon la colonne de contrôle")
    ax.grid(axis="x", alpha=0.22)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(PLOT, dpi=180, bbox_inches="tight")
    plt.close(fig)

    complete = len(observed)
    total = len(plan["planned_runs"])
    lines = [
        "# AI4I — rotation des contrôles v1",
        "",
        f"**Statut au {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} :** {complete}/{total} contrôles avec T0 disponible; consultez le manifeste pour distinguer les erreurs, sorties sans seuil et appels en attente.",
        "",
        "## Question et portée",
        "",
        "Cette campagne mesure comment v6.0.1 réagit à une rotation de chaque colonne numérique comme axe de contrôle. Elle analyse 100 moyennes de blocs consécutifs de 100 lignes. La cible fixe est le taux `Machine failure` dans chaque bloc. Il s’agit d’une étude de comportement du pipeline sur un jeu synthétique; elle ne mesure pas la performance d’un classifieur ni l’efficacité d’une action industrielle.",
        "",
        "## Valeurs observées",
        "",
        "| Contrôle | Statut | Cible demandée → utilisée | Repli cible | Monotone | T0 (%) | T0 brut dans l’unité du contrôle | T0 ambigu | Flux | Contrôle exclu | Estimateurs | Durée (s) |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in result.iterrows():
        t0 = "NA" if pd.isna(row["t0_pct"]) else f"{row['t0_pct']:.3f}"
        raw = "NA" if pd.isna(row["t0_raw_control_value"]) else f"{row['t0_raw_control_value']:.6g}"
        duration = "NA" if pd.isna(row["pipeline_elapsed_seconds"]) else f"{row['pipeline_elapsed_seconds']:.1f}"
        lines.append(
            f"| {row['control']} | {row['status']} | {row['target_requested']} → {row['target_used']} | {row['target_fallback_used']} | {row['control_monotone']} | {t0} | {raw} | {row['t0_raw_control_ambiguous']} | {row['analysis_flux_count']} | {row['control_excluded_from_analysis_fluxes']} | {row['estimator_count']} | {duration} |"
        )
    lines.extend([
        "",
        "## Lecture des valeurs",
        "",
        "T0 (%) est une coordonnée de progression calculée pour chaque axe; les colonnes ont des unités et des distributions différentes. Un écart entre contrôles montre une sensibilité de configuration dans cet essai, pas que l’un des contrôles est biologiquement ou causalement correct. Pour un contrôle non monotone, la conversion en valeur brute peut être ambiguë; l’avertissement et l’intervalle sont conservés dans les sorties complètes.",
        "",
        "Le contrôle `Machine failure` a été demandé égal à la cible. Le code v6.0.1 applique alors son garde-fou diagonal et substitue la cible par `UDI` pour cet appel; ce run ne conserve donc pas la cible fixe des onze autres axes. Il est rapporté comme repli réellement observé, et ne doit pas être présenté comme une exécution diagonale à cible inchangée. Le contrôle sélectionné est retiré des flux analysés quand il est choisi. Les appels complets, journaux, paramètres, sorties JSON et graines sont conservés dans `runs/`.",
        "",
        "## Hypothèses et résultats",
        "",
        "**Hypothèses non confirmées ici :** les axes produiront-ils des T0 différents; l’agrégation en blocs lisse-t-elle ou déplace-t-elle les seuils; les drapeaux de panne révèlent-ils une propriété différente des mesures machine? Les résultats ci-dessus répondent uniquement pour cette version, cette transformation et ce jeu synthétique.",
        "",
        "Le jeu source est synthétique, UDI est un identifiant ordonné sans statut d’horloge physique, et le choix de 100 blocs est une résolution d’analyse. Une étude de sensibilité à d’autres tailles de blocs est nécessaire avant toute conclusion générale.",
        "",
        "## Reproduction",
        "",
        "Voir `PROTOCOLE_AI4I_PIPELINE_CONTROLS_V1_FR.md`, `campaign_plan.json` et `campaign_manifest.json`. La rotation peut être reprise en relançant `run_ai4i_pipeline_control_rotation.py`; les appels déjà terminés avec le même hash d’entrée sont ignorés.",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "status": "complete" if complete == total else "partial",
        "source_sha256": sha256(SOURCE),
        "plan_sha256": sha256(PLAN),
        "state_sha256": sha256(STATE),
        "summary_sha256": sha256(SUMMARY),
        "report_sha256": sha256(REPORT),
        "plot_sha256": sha256(PLOT),
        "available_t0_count": complete,
        "planned_control_count": total,
        "completed_run_count": int((result["status"] == "complete").sum()),
        "error_count": int((result["status"] == "error").sum()),
        "pending_count": int((result["status"] == "pending").sum()),
        "claim_limit": "Synthetic behavior/sensitivity only; no prediction or domain validation.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
