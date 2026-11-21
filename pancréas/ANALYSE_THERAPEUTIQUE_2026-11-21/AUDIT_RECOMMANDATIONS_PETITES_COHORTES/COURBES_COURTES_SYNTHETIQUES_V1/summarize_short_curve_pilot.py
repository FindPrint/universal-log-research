#!/usr/bin/env python3
"""Render tables, a compact figure, and a French audit note from pilot CSVs."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
fit = pd.read_csv(OUT / "HILL4_FIT_PER_CURVE.csv")
fits = pd.read_csv(OUT / "HILL4_FIT_SUMMARY.csv")
probes = pd.read_csv(OUT / "ESTIMATOR_PROBES.csv")


def fnum(x, digits=3):
    return "—" if pd.isna(x) else f"{float(x):.{digits}f}"


def pct(x, den):
    return f"{x}/{den} ({100*x/den:.0f} %)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
colors = {"sigmoid_strong": "#007C91", "sigmoid_weak": "#E07A27"}
labels = {"sigmoid_strong": "Sigmoïde forte", "sigmoid_weak": "Sigmoïde faible"}
for scenario in colors:
    rows = fits[fits.scenario == scenario].sort_values("n_doses")
    x = rows.n_doses.to_numpy()
    med = rows.median_abs_log10_ic50_error.to_numpy()
    p90 = rows.p90_abs_log10_ic50_error.to_numpy()
    axes[0].plot(x, med, marker="o", color=colors[scenario], label=f"{labels[scenario]} — médiane")
    axes[0].plot(x, p90, marker="s", linestyle="--", color=colors[scenario], alpha=0.7, label=f"{labels[scenario]} — P90")
axes[0].set_title("Ajustement Hill 4PL : erreur sur log₁₀(IC50)")
axes[0].set_xlabel("Nombre de doses")
axes[0].set_ylabel("Erreur absolue (décades log₁₀)")
axes[0].set_xticks([7, 8, 9, 10])
axes[0].grid(alpha=0.25)
axes[0].legend(fontsize=8)

scenario_order = ["sigmoid_strong", "sigmoid_weak", "flat_no_effect", "noise_no_trend"]
scenario_labels = ["Forte", "Faible", "Plate", "Bruit"]
matrix = np.zeros((len(scenario_order), 4), dtype=int)
for i, scenario in enumerate(scenario_order):
    for j, n in enumerate([7, 8, 9, 10]):
        rows = probes[(probes.scenario == scenario) & (probes.n_doses == n)]
        matrix[i, j] = int(rows.finite.sum())
im = axes[1].imshow(matrix, cmap="viridis", vmin=0, vmax=29, aspect="auto")
axes[1].set_title("Estimateurs finis sur un sondage (sur 29)")
axes[1].set_xlabel("Nombre de doses")
axes[1].set_xticks(range(4), [7, 8, 9, 10])
axes[1].set_yticks(range(4), scenario_labels)
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        axes[1].text(j, i, str(matrix[i, j]), ha="center", va="center", color="white" if matrix[i, j] < 18 else "black", fontweight="bold")
fig.colorbar(im, ax=axes[1], label="Estimateurs finis")
fig.suptitle("Pilote synthétique v1.1 — sorties exploratoires, non confirmatoires", fontsize=13, fontweight="bold")
figure_path = OUT / "PILOT_FIGURE.png"
fig.savefig(figure_path, dpi=180)
plt.close(fig)

lines = [
    "# Résultats — courbes dose-réponse courtes synthétiques v1.1",
    "",
    "**Statut :** pilote descriptif Monte-Carlo, non confirmatoire. Exécution avec le `.venv`; source v6.0.0 non modifiée. Voir `PROTOCOLE_FR.md`, `ATTEMPT_LOG.md` et `outputs/PILOT_MANIFEST.json`.",
    "",
    "![Erreurs Hill et disponibilité des estimateurs](outputs/PILOT_FIGURE.png)",
    "",
    "## Résultats observés",
    "",
    f"- {len(fit)} courbes synthétiques ont été générées (50 par longueur × scénario; N=7, 8, 9, 10).",
    f"- Les 29 estimateurs ont été sondés sur {probes.curve_id.nunique()} courbes représentatives (une par longueur × scénario), soit {len(probes)} lignes de sorties. Cela ne mesure pas leur stabilité entre répétitions.",
    f"- Le run a duré {json.loads((OUT / 'PILOT_MANIFEST.json').read_text(encoding='utf-8'))['runtime_seconds']:.1f} secondes sur cette machine, essentiellement dans les 800 ajustements Hill, notamment sur les scénarios nuls.",
    "- Chaque sondage donne seulement 4/29 estimateurs finis, sauf la sigmoïde forte à N=9 et N=10 (5/29). Les quatre constamment finis ici sont DFA, Katz, Petrosian et Sevcik; SampleEn apparaît en plus dans les deux sondages sigmoïdes fortes les plus longs.",
    "- Les 50/50 ajustements convergent dans chaque groupe et les matrices de covariance renvoyées sont finies dans ces exécutions. Cette convergence ne suffit pas à établir qu'une IC50 existe ou est identifiable.",
    "",
    "### Erreur IC50 du fit Hill 4PL",
    "",
    "| N doses | Sigmoïde forte : erreur médiane / P90 (décades) | IC50 dans la plage | Sigmoïde faible : erreur médiane / P90 (décades) | IC50 dans la plage | Nul plat : fit dans la plage (IC50 inexistante) |",
    "|---:|---:|---:|---:|---:|---:|",
]
for n in [7, 8, 9, 10]:
    strong = fits[(fits.n_doses == n) & (fits.scenario == "sigmoid_strong")].iloc[0]
    weak = fits[(fits.n_doses == n) & (fits.scenario == "sigmoid_weak")].iloc[0]
    flat = fits[(fits.n_doses == n) & (fits.scenario == "flat_no_effect")].iloc[0]
    lines.append(
        f"| {n} | {fnum(strong.median_abs_log10_ic50_error)} / {fnum(strong.p90_abs_log10_ic50_error)} | {int(strong.ic50_inside_tested_range)}/50 | "
        f"{fnum(weak.median_abs_log10_ic50_error)} / {fnum(weak.p90_abs_log10_ic50_error)} | {int(weak.ic50_inside_tested_range)}/50 | {int(flat.ic50_inside_tested_range)}/50 |"
    )
lines += [
    "",
    "## Lecture méthodologique",
    "",
    "Le scénario à réponse forte, avec IC50 au milieu de la gamme, grande amplitude et faible bruit, est favorable par construction : son erreur médiane reste entre 0,028 et 0,042 log10. Le scénario faible/bruité est nettement moins stable : son erreur médiane est de 0,57 à 0,63 log10 et son P90 atteint 1,97 à 4,50 log10. Ces valeurs caractérisent uniquement ces générateurs et cette grille de concentrations.",
    "",
    "Surtout, le fit Hill converge aussi dans les scénarios sans IC50 vraie. Dans le nul plat, son IC50 est située dans la gamme testée dans 35–40 cas sur 50; dans le bruit sans tendance, dans 34–43 cas sur 50. Ce comportement est un avertissement sur la permissivité d'un fit convergé, pas un taux de faux positifs de T0. Un futur mode dose-réponse doit pouvoir déclarer la réponse non identifiable ou s'abstenir.",
    "",
    "Les 29 estimateurs ne reçoivent ici que la série réponse, standardisée comme le fait `apply_complexity`; ils ne voient pas la concentration. Ce sont des estimateurs de séries, et leur valeur finie ne constitue pas une mesure validée d'IC50, d'inflexion ou d'entropie pharmacologique. Le fait que seulement 4–5 valeurs soient finies dans ces 16 sondages indique que le mode court requiert une étude méthode par méthode avant tout profil de production.",
    "",
    "## Ce qui n'a pas été établi",
    "",
    "- Aucun T0, TLog, Q1–Q6, F1/F2, Voie 1/2, L7a ou L7b n'a été calculé : le pipeline complet garde son seuil d'entrée de 50 points et les courbes courtes réelles sont refusées. Le seuil n'a pas été changé.",
    "- Le test précédent sur les données réelles Figure 6d de Yin et al. a transmis séparément 150 colonnes de 7 ou 8 doses à la porte d'entrée réelle de v6.0.0 : les 150 ont été rejetées. Il s'agit d'un contrôle de compatibilité d'entrée, sans T0 ni résultat d'effet biologique (voir `../PDO_FIG6D_PIPELINE_GATE_SUMMARY.json`).",
    "- Aucune équivalence T0=IC50, aucune corrélation entre ces quantités, aucune règle bootstrap à 95 % et aucune efficacité thérapeutique ne sont testées ou validées.",
    "- Les Monte-Carlo synthétiques ne remplacent pas les réplicats par puits, expériences indépendantes, modèles biologiques ou contrôles de plaque.",
    "",
    "## Fichiers de reproduction",
    "",
    "- `run_short_curve_pilot.py` — générateur, fit 4PL, appel aux estimateurs et sortie des CSV.",
    "- `outputs/SYNTHETIC_DOSE_CURVES.csv` — toutes les doses et réponses simulées.",
    "- `outputs/HILL4_FIT_PER_CURVE.csv` et `HILL4_FIT_SUMMARY.csv` — résultats de chaque fit et synthèse.",
    "- `outputs/ESTIMATOR_PROBES.csv` — sorties brutes des 29 estimateurs pour les 16 sondages.",
    "- `outputs/PILOT_MANIFEST.json` — empreintes, versions, paramètres et durée.",
    "",
    "**Décision :** ne pas activer un seuil de N=7–10 en production. Étape suivante : concevoir un module pharmacologique séparé qui exploite les coordonnées de dose, la réplication hiérarchique, la qualité d'ajustement/identifiabilité et une règle d'abstention pré-déclarée; ensuite seulement comparer à des courbes publiques réelles.",
]
report_path = HERE / "RESULTATS_FR.md"
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
manifest_path = OUT / "PILOT_MANIFEST.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
for path in (figure_path, report_path, Path(__file__)):
    manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
manifest["summarizer_sha256"] = sha256(Path(__file__))
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {report_path} and {figure_path}")
