"""Build V2 descriptive figures, public summary, and French audit report."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STATE = HERE / "run_state.json"
QA = HERE / "validation_results.json"
PLAN = HERE / "campaign_plan.json"
REPORT = HERE / "AUDIT_RESULTATS_SENSIBILITE_V2_FR.md"
PUBLIC_JSON = HERE / "PUBLIC_VALIDATION_SUMMARY_V2.json"
T0_FIGURE = HERE / "V2_T0_BY_CONTROL.png"
TLOG_FIGURE = HERE / "V2_TLOG_BY_CONDITION_CONTROL.png"
SUMMARY_CSV = HERE / "patient_control_summary.csv"
GROUPED_CSV = HERE / "descriptive_summary.csv"
TIME_CSV = HERE / "time_axis_localization_summary.csv"
RUNTIME_CSV = HERE / "runtime_summary_v2.csv"

def number(value, digits=4):
    try:
        value = float(value)
        return f"{value:.{digits}f}" if np.isfinite(value) else "NA"
    except (TypeError, ValueError):
        return "NA"

def render_figures(rows, plan):
    controls = plan["controls"]
    datasets = plan["planned_datasets"]
    matrix = np.full((len(datasets), len(controls)), np.nan)
    labels = []
    lookup = {(r["case_key"], r["control"]): r for r in rows}
    for i, ds in enumerate(datasets):
        labels.append(ds["case_key"].replace("_seed", "\nseed"))
        for j, control in enumerate(controls):
            value = lookup.get((ds["case_key"], control), {}).get("t0_pct")
            try:
                matrix[i, j] = float(value)
            except (TypeError, ValueError):
                pass
    fig, ax = plt.subplots(figsize=(12.5, 7.5), constrained_layout=True)
    im = ax.imshow(matrix, aspect="auto", cmap="viridis")
    ax.set_title("T0 retourné selon l’entrée synthétique et le contrôle")
    ax.set_xticks(range(len(controls)), controls, rotation=16, ha="right")
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, f"{matrix[i, j]:.1f}", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im, ax=ax, label="T0 (%)")
    fig.savefig(T0_FIGURE, dpi=180, bbox_inches="tight")
    plt.close(fig)

    classes = ["saturation", "criticality", "divergence", "null_reference"]
    conditions = ["null", "weak", "strong"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5), constrained_layout=True, sharey=True)
    for ax, n in zip(axes, [64, 100]):
        values = np.full((len(controls), len(conditions) * len(classes)), np.nan)
        xlabels = []
        col = 0
        for condition in conditions:
            for cls in classes:
                xlabels.append(f"{condition}\n{cls}")
                for control_index, control in enumerate(controls):
                    cell_values = []
                    for row in rows:
                        if row["n_points"] == n and row["condition"] == condition and row["control"] == control:
                            val = (row.get("tlog_class_median") or {}).get(cls)
                            try:
                                val = float(val)
                                if np.isfinite(val):
                                    cell_values.append(val)
                            except (TypeError, ValueError):
                                pass
                    if cell_values:
                        values[control_index, col] = float(np.median(cell_values))
                col += 1
        im2 = ax.imshow(values, aspect="auto", cmap="coolwarm")
        ax.set_title(f"{n} observations")
        ax.set_xticks(range(len(xlabels)), xlabels, rotation=50, ha="right", fontsize=7)
        ax.set_yticks(range(len(controls)), controls, fontsize=8)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                if np.isfinite(values[i, j]):
                    ax.text(j, i, f"{values[i, j]:.1f}", ha="center", va="center", fontsize=6,
                            color="white" if abs(values[i, j]) > 8 else "black")
    fig.suptitle("Médianes descriptives des classes TLog par condition et contrôle")
    fig.colorbar(im2, ax=axes.ravel().tolist(), label="Sortie TLog")
    fig.savefig(TLOG_FIGURE, dpi=180, bbox_inches="tight")
    plt.close(fig)

def main():
    for path in (STATE, QA, PLAN, SUMMARY_CSV, GROUPED_CSV, TIME_CSV):
        if not path.is_file():
            raise FileNotFoundError(path)
    state = json.loads(STATE.read_text(encoding="utf-8"))
    qa = json.loads(QA.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if qa.get("status") != "passed" or qa.get("completed_runs") != 35:
        raise RuntimeError("Refusing to report an incomplete V2 campaign.")
    rows = []
    for item in plan["planned_runs"]:
        record = state.get("runs", {}).get(item["run_key"], {})
        if record.get("status") != "complete" or not isinstance(record.get("brief"), dict):
            raise RuntimeError(f"Missing completed record: {item['run_key']}")
        brief = dict(record["brief"])
        brief["elapsed_seconds"] = record.get("elapsed_seconds")
        rows.append(brief)
    render_figures(rows, plan)
    # "null" is a literal condition label in this experiment. Pandas' default
    # NA vocabulary treats it as missing, which blanks the category in tables.
    grouped = pd.read_csv(GROUPED_CSV, keep_default_na=False)
    time_summary = pd.read_csv(TIME_CSV, keep_default_na=False)
    runtime_frame = pd.DataFrame(rows)
    runtime_summary = (
        runtime_frame.groupby("control", as_index=False)["elapsed_seconds"]
        .agg(runs="count", median_seconds="median", p90_seconds=lambda values: values.quantile(0.9),
             min_seconds="min", max_seconds="max")
        .sort_values("control")
    )
    runtime_summary.to_csv(RUNTIME_CSV, index=False, encoding="utf-8")
    null_rows = [r for r in rows if r["condition"] == "null"]
    null_t0 = sum(r.get("t0_pct") is not None for r in null_rows)

    lines = [
        "# Rapport V2 — sensibilité synthétique aux transitions",
        "",
        f"**Date de génération :** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Statut technique :** {qa['status']}",
        f"**Appels complets :** {len(rows)} sur {qa['planned_runs']}",
        f"**Cœur :** {qa.get('pipeline_version')}",
        "**Données :** synthétiques uniquement; aucune donnée patient, clinique ou biologique.",
        "",
        "## Portée et lecture",
        "",
        "Le protocole gelé couvrait des signaux nuls, faibles et forts, deux longueurs, plusieurs graines et cinq axes numériques. Les sorties ci-dessous décrivent les conditions testées. Le statut passed concerne les critères d’intégrité technique, pas l’exactitude des seuils.",
        "",
        "## T0 et TLog par exécution",
        "",
        "| N | Condition | Graine | Contrôle | Monotone | T0 (%) | Statut seuil | TLog sat. | TLog crit. | TLog div. | TLog nul | Repli cible |",
        "|---:|---|---:|---|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        tlog = r.get("tlog_class_median") or {}
        lines.append(
            f"| {r['n_points']} | {r['condition']} | {r['input_seed']} | {r['control']} | "
            f"{r.get('control_monotone')} | {number(r.get('t0_pct'), 3)} | {r.get('threshold_status')} | "
            f"{number(tlog.get('saturation'))} | {number(tlog.get('criticality'))} | "
            f"{number(tlog.get('divergence'))} | {number(tlog.get('null_reference'))} | "
            f"{r.get('target_fallback_used')} |"
        )
    lines += [
        "",
        "## Résumés descriptifs par N, condition et contrôle",
        "",
        "| N | Condition | Contrôle | Runs | T0 disponibles | T0 médian (%) | T0 min–max (%) |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for _, r in grouped.iterrows():
        lines.append(
            f"| {int(r['n_points'])} | {r['condition']} | {r['control']} | {int(r['runs'])} | "
            f"{int(r['t0_available_count'])} | {number(r['t0_median_pct'], 3)} | "
            f"{number(r['t0_min_pct'], 3)}–{number(r['t0_max_pct'], 3)} |"
        )
    lines += [
        "",
        "## Localisation sur l’axe temporel",
        "",
        "L’erreur absolue par rapport au centre injecté de 58 % est calculée uniquement pour le contrôle time_index dans les cas avec transition. Le cas nul n’a pas de position vraie.",
        "",
        "| N | Condition | Runs | T0 dispo. | T0 médian (%) | Erreur absolue médiane (points %) | Étendue d’erreur (points %) |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for _, r in time_summary.iterrows():
        if r["condition"] == "null":
            error, error_range = "non définie", "non définie"
        else:
            error = number(r["absolute_t0_error_median_pct_points"], 3)
            error_range = f"{number(r['absolute_t0_error_min_pct_points'], 3)}–{number(r['absolute_t0_error_max_pct_points'], 3)}"
        lines.append(
            f"| {int(r['n_points'])} | {r['condition']} | {int(r['runs'])} | "
            f"{int(r['t0_available_count'])} | {number(r['t0_median_pct'], 3)} | {error} | {error_range} |"
        )
    lines += [
        "",
        f"Sur les {len(null_rows)} appels de condition nulle, T0 est disponible dans {null_t0} cas. Ce décompte n’est pas un taux de fausses alertes : aucune règle d’alarme n’a été préspécifiée.",
        "",
        "## Contrôles techniques",
        "",
        "| Assertion | Résultat |",
        "|---|---|",
    ]
    for name, value in qa.get("checks", {}).items():
        lines.append(f"| {name} | {'PASS' if value else 'FAIL'} |")
    lines += [
        "",
        "## Temps d’exécution observés",
        "",
        "Temps mural par appel du pipeline, rapporté par le harnais; les mesures comprennent le travail complet de l’appel dans la configuration gelée. Ce tableau n’est pas un profil par estimateur.",
        "",
        "| Contrôle | Appels | Médiane (s) | P90 (s) | Min–max (s) |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in runtime_summary.iterrows():
        lines.append(
            f"| {r['control']} | {int(r['runs'])} | {number(r['median_seconds'], 1)} | "
            f"{number(r['p90_seconds'], 1)} | {number(r['min_seconds'], 1)}–{number(r['max_seconds'], 1)} |"
        )
    longest = runtime_frame.sort_values("elapsed_seconds", ascending=False).head(5)
    lines += [
        "",
        "Cinq appels les plus longs (description de cette campagne uniquement) :",
        "",
        "| N | Condition | Graine | Contrôle | Temps (s) |",
        "|---:|---|---:|---|---:|",
    ]
    for _, r in longest.iterrows():
        lines.append(
            f"| {int(r['n_points'])} | {r['condition']} | {int(r['input_seed'])} | "
            f"{r['control']} | {number(r['elapsed_seconds'], 1)} |"
        )
    lines += [
        "",
        "## Limites et interprétation",
        "",
        "- Les niveaux d’amplitude, tailles, graines et formes de flux sont des paramètres synthétiques de conception.",
        "- Le nombre de réplicats reste faible; les tableaux sont descriptifs et aucun test statistique ni intervalle inférentiel n’est présenté.",
        "- Une vérité de transition n’est définie que sur l’axe temporel et pour les signaux non nuls.",
        "- Le contrôle diagonal avec la cible est signalé; le contrôle oscillatoire est conservé.",
        "- Les résultats ne valident ni TLog, ni la théorie générale, ni une application PDAC, ni un biomarqueur, ni un traitement.",
        "",
        "## Empreintes",
        "",
        f"- Protocole SHA-256 : {qa['protocol_sha256']}",
        f"- Harnais SHA-256 : {qa['harness_sha256']}",
        f"- Pipeline v6.0.1 SHA-256 : {qa['pipeline_sha256']}",
        f"- Plan SHA-256 : {qa['plan_sha256']}",
        "",
        "Les sorties natives par contrôle, leurs figures et journaux sont conservés dans le snapshot complet V11, à part du PDF.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    public = {
        "title": qa["title"], "status": qa["status"], "scope": qa["scope"],
        "pipeline_version": qa["pipeline_version"], "pipeline_sha256": qa["pipeline_sha256"],
        "protocol_sha256": qa["protocol_sha256"], "harness_sha256": qa["harness_sha256"],
        "plan_sha256": qa["plan_sha256"], "planned_runs": qa["planned_runs"],
        "completed_runs": qa["completed_runs"], "checks": qa["checks"],
        "null_condition_t0_available_count": null_t0, "null_condition_run_count": len(null_rows),
        "patient_control_results": rows,
        "runtime_summary_by_control": runtime_summary.to_dict(orient="records"),
        "interpretation_boundary": qa["interpretation_boundary"],
    }
    PUBLIC_JSON.write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "public_summary": str(PUBLIC_JSON),
                      "t0_figure": str(T0_FIGURE), "tlog_figure": str(TLOG_FIGURE),
                      "null_t0_available": null_t0, "null_runs": len(null_rows)},
                     indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
