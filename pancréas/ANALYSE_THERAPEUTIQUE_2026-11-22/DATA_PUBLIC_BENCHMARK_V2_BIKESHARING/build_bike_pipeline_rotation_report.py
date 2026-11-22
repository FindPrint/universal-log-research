#!/usr/bin/env python
"""Build a public, path-redacted report from the complete Bike Sharing rotation."""
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
PLAN = CAMPAIGN / "campaign_plan.json"
STATE = CAMPAIGN / "run_state.json"
SUMMARY = CAMPAIGN / "control_rotation_summary.csv"
REPORT = CAMPAIGN / "BIKESHARING_PIPELINE_CONTROL_ROTATION_V1_REPORT_FR.md"
PLOT = CAMPAIGN / "t0_by_control_bike_v1.png"
PUBLIC_MANIFEST = CAMPAIGN / "public_summary_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8"))
    rows = []
    for item in plan["planned_runs"]:
        run_key = item["run_key"]
        record = state.get("runs", {}).get(run_key, {"status": "pending"})
        summary = record.get("summary", {})
        result_path = CAMPAIGN / "runs" / run_key / "pipeline_result.json"
        metadata = {}
        if result_path.is_file():
            metadata = (json.loads(result_path.read_text(encoding="utf-8")).get("result", {}).get("metadata", {}) or {})
        flux_stats = metadata.get("global_flux_stats", {}) or {}
        classes = metadata.get("estimator_classes", {}) or {}
        estimator_names = sorted({name for group in classes.values() for name in (group or [])})
        rows.append({
            "run_key": run_key, "control": item["control"], "status": record.get("status", "pending"),
            "diagonal_control_requested": item["control"] == plan["target"],
            "target_requested": metadata.get("target_requested", summary.get("target_requested")),
            "target_used": metadata.get("target_used", summary.get("target_used")),
            "target_fallback_used": metadata.get("target_fallback_used"),
            "target_fallback_reason": metadata.get("target_fallback_reason"),
            "target_matches_request": metadata.get("target_used", summary.get("target_used")) == plan["target"],
            "n_samples": summary.get("n_samples"),
            "control_monotone": summary.get("control_monotone"), "control_direction": summary.get("control_direction"),
            "t0_status": summary.get("t0_status"), "t0_pct": summary.get("t0_pct"),
            "t0_raw_control_value": summary.get("t0_raw_control_value"),
            "t0_raw_control_ambiguous": summary.get("t0_raw_control_ambiguous"),
            "analysis_flux_count": len(flux_stats) if metadata else summary.get("analysis_flux_count"),
            "control_excluded_from_analysis_fluxes": item["control"] not in flux_stats if metadata else summary.get("control_excluded_from_analysis_fluxes"),
            "estimator_count": len(estimator_names) if metadata else summary.get("estimator_count"),
            "pipeline_elapsed_seconds": record.get("elapsed_seconds", summary.get("pipeline_elapsed_seconds")),
        })
    result = pd.DataFrame(rows)
    result.to_csv(SUMMARY, index=False, float_format="%.10g")
    observed = result[(result["status"] == "complete") & pd.to_numeric(result["t0_pct"], errors="coerce").notna()].copy()
    observed["t0_plot"] = pd.to_numeric(observed["t0_pct"], errors="coerce")
    fig, ax = plt.subplots(figsize=(11, max(6, 0.38 * max(len(observed), 1))))
    colors = ["#7c3aed" if bool(row["diagonal_control_requested"]) else ("#2a6f97" if pd.notna(row["control_monotone"]) and bool(row["control_monotone"]) else "#d97706") for _, row in observed.iterrows()]
    if len(observed):
        ax.barh(observed["control"], observed["t0_plot"], color=colors)
        for y, (_, row) in enumerate(observed.iterrows()):
            suffix = " [repli de cible]" if bool(row["target_fallback_used"]) else (" [T0 brut ambigu]" if bool(row["t0_raw_control_ambiguous"]) else "")
            ax.text(row["t0_plot"] + 0.8, y, f"{row['t0_plot']:.1f}%{suffix}", va="center", fontsize=7)
    ax.set_xlabel("T0 (% de progression sur l’axe de contrôle; pas une unité physique commune)")
    ax.set_title("Bike Sharing — sorties T0 selon le flux de contrôle")
    ax.grid(axis="x", alpha=0.22)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(PLOT, dpi=180, bbox_inches="tight")
    plt.close(fig)

    lines = [
        "# Bike Sharing — rotation v6.0.1 de tous les contrôles numériques", "",
        f"**État au {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} :** {int((result['status'] == 'complete').sum())}/{len(result)} axes terminés.", "",
        "## Plan et portée", "",
        "Les données horaires ont été conservées dans l’ordre de `instant`, puis réduites en 100 moyennes de blocs consécutifs quasi égaux. `cnt` est la cible demandée; 16 flux numériques ont été présentés comme contrôles. Le contrôle choisi est vérifié par rapport aux flux analysés. `casual` et `registered` restent dans l’analyse du pipeline comme flux liés, mais ont été exclus des variables explicatives du benchmark prédictif car `casual + registered = cnt`.", "",
        "## Sorties enregistrées", "",
        "| Contrôle | État | Cible demandée → utilisée | Repli | Monotone | T0 (%) | Valeur brute | Ambigu | Flux | Contrôle exclu | Estimateurs | Durée s |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in result.iterrows():
        t0 = "NA" if pd.isna(row["t0_pct"]) else f"{row['t0_pct']:.3f}"
        raw = "NA" if pd.isna(row["t0_raw_control_value"]) else f"{row['t0_raw_control_value']:.6g}"
        duration = "NA" if pd.isna(row["pipeline_elapsed_seconds"]) else f"{row['pipeline_elapsed_seconds']:.1f}"
        lines.append(f"| {row['control']} | {row['status']} | {row['target_requested']} → {row['target_used']} | {row['target_fallback_used']} | {row['control_monotone']} | {t0} | {raw} | {row['t0_raw_control_ambiguous']} | {row['analysis_flux_count']} | {row['control_excluded_from_analysis_fluxes']} | {row['estimator_count']} | {duration} |")
    lines.extend([
        "", "## Cas contrôle=cible demandé", "",
        "Pour `cnt` comme contrôle, le code v6.0.1 impose un repli de cible parce que contrôle et cible sont identiques. La cible effectivement utilisée et le motif exact sont conservés dans le tableau/manifeste. Ce résultat est un test du garde-fou de configuration, pas une diagonale exécutée à cible inchangée; ne pas le mélanger aux comparaisons où `cnt` est la cible réelle.", "",
        "## Lecture prudente", "",
        "Chaque T0 dépend de l’axe, de l’ordre et de l’agrégation prescrite. Les valeurs brutes n’ont pas d’unité commune; les axes non monotones peuvent rendre leur conversion ambiguë. Un écart indique une sensibilité de configuration observée, pas une cause, un effet sur la demande ou un seuil opérationnel. Ce jeu mesure un seul système de location sur deux ans et ne valide pas l’universalité.", "",
        "## Reproduction", "",
        "Consulter `PROTOCOLE_BIKESHARING_V1_FR.md`, `campaign_plan.json`, `campaign_manifest.json` et les sorties `runs/`. Le script reprend les axes déjà complets dont les empreintes d’entrée concordent.",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "status": "complete" if int((result["status"] == "complete").sum()) == len(result) else "partial",
        "plan_sha256": sha256(PLAN), "state_sha256": sha256(STATE), "summary_sha256": sha256(SUMMARY),
        "report_sha256": sha256(REPORT), "plot_sha256": sha256(PLOT),
        "completed_run_count": int((result["status"] == "complete").sum()),
        "error_count": int((result["status"] == "error").sum()), "pending_count": int((result["status"] == "pending").sum()),
        "requested_diagonal_fallback_count": int(result["target_fallback_used"].fillna(False).sum()),
        "claim_limit": "Pipeline behavior/sensitivity only; no forecast validation or universality claim.",
    }
    PUBLIC_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
