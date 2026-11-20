#!/usr/bin/env python
"""Score the frozen synthetic pilot only after pipeline runs have completed."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


HERE = Path(__file__).resolve().parent
INPUT = HERE / "input"
SPEC = json.loads((HERE / "pilot_spec.json").read_text(encoding="utf-8"))
TRUTH = json.loads((HERE / "truth_private" / "truth.json").read_text(encoding="utf-8"))["cases"]
STATE = json.loads((HERE / "run_state.json").read_text(encoding="utf-8"))["cases"]


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


rows = []
for case in SPEC["cases"]:
    case_id = case["case_id"]
    run = STATE.get(case_id, {})
    truth = TRUTH[case_id]
    t0 = run.get("t0_rank_pct")
    boundary = truth.get("boundary_rank_fraction")
    loc_error = abs(float(t0) / 100.0 - float(boundary)) if finite(t0) and boundary is not None else None
    rows.append({
        **run,
        "case_id": case_id,
        "event_family": truth.get("family"),
        "event_present": truth.get("event_present"),
        "truth_description": truth.get("description", truth.get("event_definition")),
        "change_index_zero_based": truth.get("change_index_zero_based"),
        "boundary_rank_fraction": boundary,
        "location_error_normalized": loc_error,
        "no_event_t0_is_false_positive": False,
    })

case01 = pd.read_csv(INPUT / "case_01.csv")
case02 = pd.read_csv(INPUT / "case_02.csv")
paired_same_target_axis = case01[["control_index", "target"]].equals(case02[["control_index", "target"]])
row_by_id = {r["case_id"]: r for r in rows}
geo01 = ((row_by_id.get("case_01", {}).get("tlog") or {}).get("class_median") or {})
geo02 = ((row_by_id.get("case_02", {}).get("tlog") or {}).get("class_median") or {})
tlog_pair_delta = {k: float(geo01[k]) - float(geo02[k]) for k in geo01 if k in geo02
                   if finite(geo01.get(k)) and finite(geo02.get(k))}

scored = {
    "pilot": SPEC["protocol"],
    "spec_sha256": __import__("hashlib").sha256((HERE / "pilot_spec.json").read_bytes()).hexdigest(),
    "truth_sha256": __import__("hashlib").sha256((HERE / "truth_private" / "truth.json").read_bytes()).hexdigest(),
    "pipeline_sha256": SPEC["pipeline_sha256"],
    "runner_sha256": SPEC["runner_sha256"],
    "scorer_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest(),
    "all_cases_recorded_terminal": all(STATE.get(c["case_id"], {}).get("status") in {"complete", "error"} for c in SPEC["cases"]),
    "completed_pipeline_runs": sum(STATE.get(c["case_id"], {}).get("status") == "complete" for c in SPEC["cases"]),
    "recorded_pipeline_errors": {k: v.get("error") for k, v in STATE.items() if v.get("status") == "error"},
    "paired_case01_case02_same_axis_and_target": paired_same_target_axis,
    "case01_case02_t0_abs_difference_percentage_points": (
        abs(float(STATE["case_01"]["t0_rank_pct"]) - float(STATE["case_02"]["t0_rank_pct"]))
        if finite(STATE.get("case_01", {}).get("t0_rank_pct")) and finite(STATE.get("case_02", {}).get("t0_rank_pct")) else None
    ),
    "case01_minus_case02_tlog_class_median_delta": tlog_pair_delta,
    "interpretation_guard": "No-event T0 values are reported as selected locations only; no alert rule was frozen, so no false-positive label or rate is computed.",
    "case_results": rows,
}
(HERE / "scored_pilot_results.json").write_text(json.dumps(scored, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
pd.DataFrame([{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()}
              for row in rows]).to_csv(HERE / "scored_pilot_summary.csv", index=False, encoding="utf-8")

# Figure uses only outputs and truth disclosed after execution.
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)
event_rows = [r for r in rows if r.get("event_present") is True]
sizes = sorted({int(r["n_rows"]) for r in event_rows})
truth_by_n = {}
for r in event_rows:
    truth_by_n[int(r["n_rows"])] = 100.0 * float(r["boundary_rank_fraction"])
if sizes:
    ax1.plot(sizes, [truth_by_n[n] for n in sizes], color="#238b45", marker="o", linestyle="--", label="Frontière vraie")
for r in rows:
    if not finite(r.get("t0_rank_pct")):
        continue
    n = int(r["n_rows"])
    is_event = r.get("event_present") is True
    offset = -1.4 if r["case_id"] == "case_01" else (1.4 if r["case_id"] == "case_02" else 0.0)
    if is_event:
        ax1.scatter([n + offset], [r["t0_rank_pct"]], color="#0072B2", marker="s", s=60,
                    label="T0, cas avec marche" if r["case_id"] == next(x["case_id"] for x in rows if x.get("event_present") is True and finite(x.get("t0_rank_pct"))) else None, zorder=3)
        label_offsets = {"case_01": (-48, 9), "case_02": (8, 9), "case_03": (-42, -16), "case_04": (8, 9)}
        ax1.annotate(r["case_id"], (n + offset, r["t0_rank_pct"]), xytext=label_offsets.get(r["case_id"], (4, 5)), textcoords="offset points", fontsize=8)
    else:
        ax1.scatter([n], [r["t0_rank_pct"]], color="#D55E00", marker="^", s=65,
                    label="T0 sélectionné, aucun événement défini" if r["case_id"] == next((x["case_id"] for x in rows if x.get("event_present") is False), None) else None, zorder=3)
        ax1.annotate(r["case_id"], (n, r["t0_rank_pct"]), xytext=(4, 5), textcoords="offset points", fontsize=8)
ax1.set(title="Position T0 et frontière connue — lecture descriptive du pilote", xlabel="Nombre de lignes N", ylabel="Position sur l'axe (%)")
ax1.set_ylim(-5, 105)
ax1.grid(alpha=.25)
ax1.legend(loc="best", fontsize=8)

for r in rows:
    if r.get("status") != "complete":
        continue
    statuses = r.get("estimator_status_counts", {}) or {}
    success = statuses.get("success", 0)
    n = int(r["n_rows"])
    offset = {"case_01": -1.8, "case_02": 1.8, "case_03": -0.7, "case_04": 0.7}.get(r["case_id"], 0.0)
    ax2.scatter([n + offset], [success], color="#6A51A3" if r.get("event_present") else "#D55E00", s=55,
                label="estimateurs calculés" if r["case_id"] == next(x["case_id"] for x in rows if x.get("status") == "complete") else None)
    label_offsets = {"case_01": (-48, 8), "case_02": (12, 8), "case_03": (-48, -18), "case_04": (12, -18)}
    ax2.annotate(r["case_id"], (n + offset, success), xytext=label_offsets.get(r["case_id"], (4, 4)), textcoords="offset points", fontsize=8)
for r in rows:
    if r.get("status") == "error":
        n = int(r["n_rows"])
        ax1.annotate(f"{r['case_id']} refusé", (n, 5), ha="center", va="bottom", fontsize=8, color="#B2182B")
        ax2.scatter([n], [0], marker="x", color="#B2182B", s=65, zorder=4,
                    label="run rejeté avant calcul des estimateurs" if r["case_id"] == next(x["case_id"] for x in rows if x.get("status") == "error") else None)
        ax2.annotate(r["case_id"], (n, 0), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8, color="#B2182B")
ax2.axhline(29, color="#555555", linestyle=":", linewidth=1, label="29 estimators configurés")
ax2.set(title="Estimateurs avec statut `success` pour la cible `Tous`", xlabel="Nombre de lignes N", ylabel="Nombre d'estimateurs (sur 29)")
ax2.set_ylim(bottom=0)
ax1.set_xlim(0, max(sizes) + 4 if sizes else 80)
ax2.set_xlim(0, max(int(r["n_rows"]) for r in rows) + 4)
ax2.set_yticks(range(0, 30, 5))
ax2.grid(alpha=.25)
ax2.legend(loc="best", fontsize=8)
fig.savefig(HERE / "pilot_overview.png", dpi=170)
plt.close(fig)

report_lines = [
    "# Résultats du pilote synthétique v1",
    "",
    f"**Runs pipeline terminés :** {sum(r.get('status') == 'complete' for r in rows)}/{len(rows)}; **erreurs explicitement enregistrées :** {sum(r.get('status') == 'error' for r in rows)}. **Axe et cible identiques dans la paire case_01/case_02 :** {paired_same_target_axis}.",
    "",
    "Ce pilote comporte une réalisation déterministe par cas. Les chiffres ci-dessous décrivent ces exécutions; ils ne donnent pas de taux de détection ou de faux positifs.",
    "",
    "![Position T0 et couverture des estimateurs](pilot_overview.png)",
    "",
    "## Résumé par cas",
    "",
    "| Cas | N | Vérité | Statut | T0 rang % | Erreur normalisée | Estimateurs success / 29 | L7b | TLog classe |",
    "|---|---:|---|---|---:|---:|---:|---|---|",
]
for r in rows:
    truth_label = "marche" if r.get("event_present") is True else "aucun événement" if r.get("event_present") is False else "inconnu"
    counts = r.get("estimator_status_counts", {}) or {}
    err = f"{r['location_error_normalized']:.4f}" if finite(r.get("location_error_normalized")) else "—"
    t0s = f"{r['t0_rank_pct']:.2f}" if finite(r.get("t0_rank_pct")) else "—"
    report_lines.append(f"| {r['case_id']} | {r.get('n_rows','—')} | {truth_label} | {r.get('status','—')} | {t0s} | {err} | {counts.get('success',0)} / {r.get('estimator_count','—')} | {(r.get('l7b') or {}).get('verdict','—')} | {json.dumps((r.get('tlog') or {}).get('class_median'), ensure_ascii=False)} |")
q_keys = ["Q1_Calme_vs_Chaos", "Q2_Tension_Seuil", "Q3_Agressivite", "Q4_Persistence", "Q5_Actif_Receptif", "Q6_Actif_Receptif_Echelle"]
report_lines += [
    "",
    "## Disponibilité des six questions Q1–Q6",
    "",
    "Chaque cellule indique les valeurs numériques finies / le nombre de valeurs numériques observées dans la sortie de la question. Ce sont des comptages de sorties, pas des scores de performance.",
    "",
    "| Cas | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 |",
    "|---|---:|---:|---:|---:|---:|---:|",
]
for r in rows:
    q = r.get("q_finite_counts") or {}
    cells = [f"{(q.get(k) or {}).get('finite')}/{(q.get(k) or {}).get('numeric')}" if r.get("status") == "complete" else "—" for k in q_keys]
    report_lines.append("| " + r["case_id"] + " | " + " | ".join(cells) + " |")
report_lines += [
    "",
    "## Cascade et dérivées F1/F2 rapportées par le pipeline",
    "",
    "| Cas | F1 avant (T−1) | T0 | F1 après (T+1) | max F1 velocity | max F2 curvature | Statut |",
    "|---|---:|---:|---:|---:|---:|---|",
]
for r in rows:
    f = r.get("f1_f2") or {}
    if r.get("status") != "complete":
        report_lines.append(f"| {r['case_id']} | — | — | — | — | — | non calculé (entrée refusée) |")
    else:
        vals = [f.get("T_-1_F1_pre_inflection"), f.get("T_0_Monte_Carlo_Central"), f.get("T_+1_F1_post_deceleration"), f.get("max_F1_velocity"), f.get("max_F2_curvature")]
        report_lines.append("| " + r["case_id"] + " | " + " | ".join(f"{float(v):.4f}" if finite(v) else "—" for v in vals) + f" | {f.get('status','—')} |")
report_lines += [
    "",
    "Ces F1/F2 sont les lectures numériques du code aux positions de la cascade; elles ne portent pas d'intervalle d'incertitude dans ce pilote.",
    "",
    "## TLog et voies",
    "",
    "| Cas | TLog saturation | TLog criticality | TLog divergence | TLog null | Higuchi Voie 1 | Voie 2 |",
    "|---|---:|---:|---:|---:|---:|---|",
]
for r in rows:
    if r.get("status") != "complete":
        report_lines.append(f"| {r['case_id']} | — | — | — | — | — | non calculé |")
        continue
    t = (r.get("tlog") or {}).get("class_median") or {}
    v1 = (r.get("voie1") or {}).get("higuchi")
    v2 = (r.get("voie2") or {}).get("proof_status")
    tvals = [t.get(k) for k in ("saturation", "criticality", "divergence", "null_reference")]
    v1_text = f"{float(v1):.3f}" if finite(v1) else "—"
    v2_text = "heuristique, pas preuve" if v2 else "—"
    report_lines.append("| " + r["case_id"] + " | " + " | ".join(f"{float(v):.3f}" if finite(v) else "—" for v in tvals) + f" | {v1_text} | {v2_text} |")
report_lines += [
    "",
    "Portée indiquée par v6.0 : `(d−4)·log(n)` sur la couche géométrique; les estimateurs bruts et les sorties par classe restent nécessaires à l'interprétation. La Voie 1 correspond ici à Higuchi; la Voie 2 reste une triangulation heuristique, pas une preuve.",
]
report_lines += [
    "",
    "## Interprétation et limites",
    "",
    f"- L'ablation des flux case_01/case_02 conserve exactement le même axe et la même cible : `{paired_same_target_axis}`. L'écart absolu de T0 est {scored['case01_case02_t0_abs_difference_percentage_points'] if scored['case01_case02_t0_abs_difference_percentage_points'] is not None else 'non calculable'} points de pourcentage. Une seule paire donne une observation descriptive, sans incertitude estimable.",
    f"- Les comptes de valeurs Q suivent le nombre de flux disponibles : case_01 contient {json.dumps((row_by_id['case_01'].get('q_finite_counts') or {}).get('Q1_Calme_vs_Chaos'), ensure_ascii=False)} pour Q1 contre {json.dumps((row_by_id['case_02'].get('q_finite_counts') or {}).get('Q1_Calme_vs_Chaos'), ensure_ascii=False)} en cible seule. Les médianes de classe TLog changent aussi; deltas case_01 moins case_02 : `{json.dumps(tlog_pair_delta, ensure_ascii=False)}`. Cela montre des sorties de couche différentes dans cette paire malgré un T0 égal; ce n'est pas une mesure d'effet générale.",
    "- Les cas AR(1) stationnaire et dérive lisse n'ont pas de frontière vraie. Si un T0 apparaît, il s'agit d'une position sélectionnée par le balayage; sans règle d'alerte gelée, ce résultat n'est pas noté faux positif.",
    "- Rejets enregistrés : " + ("; ".join(f"{r['case_id']} (N={r.get('n_rows')}): {r.get('error')}" for r in rows if r.get("status") == "error") or "aucun"),
    "- Les compteurs `success` comptent les statuts de la cible `Tous` pour les estimateurs configurés. Ils ne signifient pas que chaque estimateur est valide ou fiable pour N court.",
    "- Les sorties complètes, graphiques, journaux, manifestes, scores Q, dérivées F1/F2, Voie 1/2, TLog et L7a/L7b restent dans les sous-dossiers `runs/case_XX/`.",
    "- Une exécution par cas ne permet ni intervalle de confiance ni généralisation. Aucune conclusion clinique, biologique ou universelle ne découle de ce pilote.",
    "",
    "## Hypothèses et résultats observés",
    "",
    "Les hypothèses génératrices sont dans `truth_private/truth.json`, séparées des CSV vus par le pipeline. Les résultats calculés sont dans `scored_pilot_results.json` et les données maîtres de chaque exécution dans `runs/case_XX/master_results.json`.",
]
(HERE / "PILOT_REPORT_FR.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
print(f"Scored {len(rows)} cases; report={HERE / 'PILOT_REPORT_FR.md'}")
