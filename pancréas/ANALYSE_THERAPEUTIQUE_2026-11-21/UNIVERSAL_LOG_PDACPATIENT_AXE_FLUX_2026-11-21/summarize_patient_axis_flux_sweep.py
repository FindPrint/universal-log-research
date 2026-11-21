#!/usr/bin/env python3
"""Summarize the completed v6.0.1 patient-level axis x flux sweep."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
RUNS = OUT / "runs"
MANIFEST_PATH = OUT / "RUN_MANIFEST.json"
SUMMARY_PATH = OUT / "RUN_SUMMARY.csv"
SOURCE = (PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-17" /
          "multi_axis_resistance" / "results_all_57" /
          "patient_level_normalized_57.csv")
PIPELINE = (PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" /
            "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" /
            "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py")
ORDERS = ["source_order", "reverse_order", "shuffle_20261121"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    # Keep public artifacts portable; no user-specific absolute paths.
    manifest["source_csv"] = SOURCE.relative_to(PROJECT).as_posix()
    manifest["pipeline"] = PIPELINE.relative_to(PROJECT).as_posix()
    manifest["python_executable"] = ".venv\\Scripts\\python.exe"
    manifest["status"] = "complete"
    return manifest


def main() -> None:
    manifest = load_manifest()
    runs = pd.read_csv(SUMMARY_PATH)
    if manifest.get("status") != "complete" or len(runs) != 48:
        raise RuntimeError(f"Expected completed 48-run manifest; got {manifest.get('status')} / {len(runs)}")
    success = runs[runs["status"] == "success"].copy()
    if len(success) != 30:
        raise RuntimeError(f"Expected 30 successful core runs; got {len(success)}")

    # Compact axis x order table, including the exact threshold span observed.
    pivot = success.pivot(index="control", columns="order", values="T0_percent")
    pivot = pivot.reindex(columns=ORDERS)
    pivot["range_pp"] = pivot.max(axis=1) - pivot.min(axis=1)
    pivot["median_T0_percent"] = pivot[ORDERS].median(axis=1)
    pivot["n_successful_orders"] = pivot[ORDERS].count(axis=1)
    pivot = pivot.reset_index().sort_values("range_pp", ascending=False)
    pivot.to_csv(OUT / "AXIS_ORDER_SENSITIVITY.csv", index=False, float_format="%.10g")

    # Quantify which estimates are actually finite for each control x flux.
    coverage_rows = []
    monotonicity_rows = []
    for row in success.to_dict("records"):
        run_dir = HERE / row["run_dir"]
        features = pd.read_csv(run_dir / "features.csv")
        with gzip.open(run_dir / "pipeline_output.json.gz", "rt", encoding="utf-8") as f:
            result = json.load(f)
        mono = result.get("monotone_flags", {})
        for flux, stats in result.get("global_flux_stats", {}).items():
            if flux == row["control"]:
                raise RuntimeError(f"Selected control leaked into flux list: {row['order']} / {row['control']}")
            mean_cols = [c for c in features.columns
                         if c.startswith(f"{flux}_") and c.endswith("_mean")]
            finite_rows = {c: int(features[c].notna().sum()) for c in mean_cols}
            finite_est = sum(n > 0 for n in finite_rows.values())
            total_finite = sum(finite_rows.values())
            coverage_rows.append({
                "order": row["order"], "control_axis": row["control"], "flux": flux,
                "n_valid_flux_source": int(stats.get("n_valid", 0)),
                "n_total_flux_source": int(stats.get("n_total", 0)),
                "missing_fraction_flux": float(result.get("missing_rates", {}).get(flux, np.nan)),
                "n_estimator_types_with_any_finite_mean": finite_est,
                "n_estimator_types_called": len(mean_cols),
                "n_progress_bins": len(features),
                "finite_estimator_mean_cells": total_finite,
                "possible_estimator_mean_cells": len(mean_cols) * len(features),
                "finite_cell_fraction": (total_finite / (len(mean_cols) * len(features))
                                         if mean_cols and len(features) else np.nan),
                "n_estimators_finite_at_least_half_bins": sum(
                    n >= len(features) / 2 for n in finite_rows.values()
                ),
                "control_flux_exclusion_verified": flux != row["control"],
                "monotonicity": mono.get(flux, {}).get("direction"),
            })
        for name, info in mono.items():
            role = "control" if name == "__control__" else "flux"
            monotonicity_rows.append({
                "order": row["order"], "selected_control": row["control"],
                "column": info.get("name", name), "role_in_run": role,
                "direction": info.get("direction"), "monotone": info.get("monotone"),
                "constant": info.get("constant"), "n_valid": info.get("n_valid"),
                "n_total": info.get("n_total"),
            })

    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT / "FLOW_ESTIMATOR_COVERAGE.csv", index=False, float_format="%.10g")
    pd.DataFrame(monotonicity_rows).to_csv(
        OUT / "AXIS_FLUX_ROLE_MONOTONICITY.csv", index=False
    )
    flow_summary = (coverage.groupby("flux", as_index=False)
                    .agg(control_order_pairs=("control_axis", "size"),
                         mean_finite_estimator_types=("n_estimator_types_with_any_finite_mean", "mean"),
                         median_finite_estimator_types=("n_estimator_types_with_any_finite_mean", "median"),
                         max_finite_estimator_types=("n_estimator_types_with_any_finite_mean", "max"),
                         mean_finite_cell_fraction=("finite_cell_fraction", "mean"),
                         min_source_n_valid=("n_valid_flux_source", "min"),
                         max_source_n_valid=("n_valid_flux_source", "max")))
    flow_summary.to_csv(OUT / "FLOW_COVERAGE_SUMMARY.csv", index=False, float_format="%.10g")

    # Figure 1: thresholds by control and row ordering, explicitly rank percent.
    matrix = success.pivot(index="control", columns="order", values="T0_percent").reindex(columns=ORDERS)
    matrix = matrix.loc[pivot["control"].tolist()]
    fig, ax = plt.subplots(figsize=(9, max(5, 0.45 * len(matrix))))
    arr = matrix.to_numpy(dtype=float)
    im = ax.imshow(np.ma.masked_invalid(arr), aspect="auto", cmap="viridis", vmin=0, vmax=100)
    ax.set_xticks(range(len(ORDERS)), ["Ordre source", "Ordre inversé", "Mélange fixe"])
    ax.set_yticks(range(len(matrix)), matrix.index.tolist())
    ax.set_title("UNIVERSAL_LOG v6.0.1 — seuil de rang par axe et ordre\nPDAC, cohorte transversale de 57 patients")
    ax.set_xlabel("Ordre des lignes (aucun n'est une chronologie biologique)")
    ax.set_ylabel("Colonne numérique choisie comme axe de contrôle")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if np.isfinite(arr[i, j]):
                ax.text(j, i, f"{arr[i, j]:.1f}", ha="center", va="center", color="white", fontsize=8)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("T0 (% de l'axe de progression interne; pas une valeur brute)")
    fig.tight_layout()
    fig.savefig(OUT / "AXIS_ORDER_SENSITIVITY.png", dpi=190)
    plt.close(fig)

    # Figure 2: estimator availability across control x flux pairs.
    agg = (coverage.groupby(["control_axis", "flux"], as_index=False)
           ["n_estimator_types_with_any_finite_mean"].mean())
    controls = list(pivot["control"])
    fluxes = sorted(coverage["flux"].unique().tolist())
    cov_matrix = np.full((len(controls), len(fluxes)), np.nan)
    for r, control in enumerate(controls):
        for c, flux in enumerate(fluxes):
            if control == flux:
                continue
            item = agg[(agg.control_axis == control) & (agg.flux == flux)]
            if not item.empty:
                cov_matrix[r, c] = float(item.iloc[0]["n_estimator_types_with_any_finite_mean"])
    def short_name(name: str) -> str:
        labels = {
            "acquired_any_listed": "acq. tous",
            "acquired_kras_amp": "acq. KRAS amp",
            "acquired_myc_amp": "acq. MYC amp",
            "acquired_other": "acq. autres",
            "acquired_ras_cna": "acq. RAS CNA",
            "acquired_ras_short": "acq. RAS SNV",
            "delta_on_to_eot_vaf_pp": "Δ VAF on→EOT",
            "delta_pre_to_eot_vaf_pp": "Δ VAF pré→EOT",
            "delta_pre_to_on_vaf_pp": "Δ VAF pré→on",
            "dose_mg": "Dose mg",
            "genomic_max_vaf_eot": "VAF max EOT",
            "multiple_ras_pathway_classes": "multi classes RAS",
            "n_ras_pathway_classes_acquired": "n classes RAS",
            "ras_vaf_eot": "VAF EOT",
            "ras_vaf_on": "VAF on",
            "ras_vaf_pre": "VAF pré",
        }
        return labels.get(name, name)

    fig, ax = plt.subplots(figsize=(15.5, 7.5), constrained_layout=True)
    im = ax.imshow(np.ma.masked_invalid(cov_matrix), aspect="auto", cmap="magma", vmin=0, vmax=29)
    ax.set_xticks(range(len(fluxes)), [short_name(x) for x in fluxes], rotation=42, ha="right", fontsize=8)
    ax.set_yticks(range(len(controls)), [short_name(x) for x in controls], fontsize=9)
    ax.set_title("Estimateurs finis disponibles — moyenne des trois ordres\nContrôle × flux; la case diagonale est exclue", fontsize=13)
    ax.set_xlabel("Flux analysé")
    ax.set_ylabel("Axe de contrôle")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Types d'estimateur finis (sur 29) — disponibilité, pas significativité", labelpad=10)
    fig.savefig(OUT / "CONTROL_FLUX_ESTIMATOR_COVERAGE.png", dpi=190)
    plt.close(fig)

    # Sanitize local absolute paths before the manifest is included in public artifacts.
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Build a careful narrative with observations and interpretation boundaries separate.
    axes_table = [
        "| Axe numérique | Ordre source | Inversé | Mélange fixe | Étendue observée |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in pivot.iterrows():
        vals = [r.get(order, np.nan) for order in ORDERS]
        fmt = lambda x: "—" if pd.isna(x) else f"{x:.2f} %"
        axes_table.append(f"| `{r['control']}` | {fmt(vals[0])} | {fmt(vals[1])} | {fmt(vals[2])} | {r['range_pp']:.2f} points |")
    coverage_table = [
        "| Flux | Paires contrôle × ordre | Estimateurs finis moyens (sur 29) | N observé min–max |",
        "|---|---:|---:|---:|",
    ]
    for _, r in flow_summary.sort_values("mean_finite_estimator_types").iterrows():
        coverage_table.append(
            f"| `{r['flux']}` | {int(r['control_order_pairs'])} | "
            f"{r['mean_finite_estimator_types']:.1f} | "
            f"{int(r['min_source_n_valid'])}–{int(r['max_source_n_valid'])} |"
        )

    abstain = pd.DataFrame(manifest["abstained_controls"])
    abstain_table = ["| Contrôle numérique candidat | N valide | Statut |", "|---|---:|---|"]
    for item in abstain.to_dict("records"):
        abstain_table.append(f"| `{item['control']}` | {item['n_valid']} | abstention : minimum 50 conservé |")

    detail_table = [
        "| Ordre | Contrôle | Statut | N valide | T0 interne (%) | Flux analysés | Durée (s) |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in runs.to_dict("records"):
        success = row["status"] == "success"
        status_label = "réussi" if success else "abstention N<50"
        t0 = f"{float(row['T0_percent']):.2f}" if pd.notna(row.get("T0_percent")) else "—"
        n_fluxes = int(row["n_fluxes_returned"]) if pd.notna(row.get("n_fluxes_returned")) else 0
        runtime = f"{float(row['runtime_seconds']):.1f}" if pd.notna(row.get("runtime_seconds")) else "—"
        detail_table.append(
            f"| {row['order']} | `{row['control']}` | {status_label} | "
            f"{int(row['n_valid_control'])} | {t0} | {n_fluxes} | {runtime} |"
        )

    source_rel = SOURCE.relative_to(PROJECT).as_posix()
    pipeline_rel = PIPELINE.relative_to(PROJECT).as_posix()
    successful_count = int((runs.status == "success").sum())
    abstain_count = int(runs.status.str.startswith("abstain").sum())
    error_count = int((runs.status == "error").sum())
    report = f"""# Audit UNIVERSAL_LOG v6.0.1 — matrice contrôle × flux PDAC

**Date :** 21 novembre 2026  
**Statut :** balayage descriptif achevé; aucun résultat présenté comme prédiction, effet causal, biomarqueur validé ou efficacité thérapeutique.

## Question et portée

Cette analyse reprend le CSV patient de 57 sujets issu des tableaux cliniques publiés sur le daraxonrasib. Elle passe le cœur `run_pipeline` de v6.0.1 sur toutes ses colonnes numériques : une colonne à la fois comme axe de contrôle, puis toutes les autres colonnes numériques conservées comme flux distincts. L'axe sélectionné est exclu des flux de ce passage. Les contrôles non monotones ne sont pas rejetés.

Le tableau est transversal : une ligne = un patient. La cohorte assemblée réunit 44 patients d'une strate principale et 13 de la table supplémentaire à dose plus faible; la sélection concerne des patients ayant bénéficié initialement avant progression et ne comporte pas de groupe non-progressif comparateur. Les strates ne sont pas randomisées l'une par rapport à l'autre. L'ordre source regroupe donc les strates de dose; l'ordre inversé et le mélange déterministe servent uniquement à vérifier la sensibilité à l'ordre des lignes. Aucun ordre de patients n'est une chronologie biologique. Source primaire : Aronchik et al., *Nature Medicine* (2026), [article et données supplémentaires](https://doi.org/10.1038/s41591-026-04537-w).

## Protocole exécuté

- Pipeline : `{pipeline_rel}`, v6.0.1, SHA-256 `{manifest['pipeline_sha256']}`.
- Entrée : `{source_rel}`, 57 lignes × 30 colonnes, 57 identifiants patient distincts, SHA-256 `{manifest['source_sha256']}`.
- Mode `fast`, Cohen-d, graine `{manifest['configuration']['random_seed']}`, un worker, triangulation complète désactivée.
- Minimum d'entrée inchangé : 50 valeurs valides dans l'axe. Pas d'imputation des VAF/deltas manquants.
- Toutes les colonnes numériques d'origine sont des candidats axes; les autres restent des flux. Les textes catégoriels et annotations libres ne sont pas convertis en nombres.
- Trois dispositions : ordre source, ordre inversé, mélange déterministe `20261121`.

## Résultats observés

La matrice comprend **48 passages** : **{successful_count} réussites**, **{abstain_count} abstentions au minimum d'entrée**, **{error_count} erreurs**. Dix axes numériques passent l'entrée dans les trois dispositions; six axes insuffisamment complets s'abstiennent.

### Seuils de rang par axe et ordre des lignes

Les nombres sont `T0` en pourcentage de l'axe de progression interne du pipeline, pas une valeur brute de dose ou de VAF.

{chr(10).join(axes_table)}

La dispersion la plus élevée entre les trois ordres concerne `acquired_other` (53,25 points), puis `multiple_ras_pathway_classes` (39,29), `acquired_any_listed` (37,88) et `acquired_kras_amp` (27,27). `dose_mg` varie de 19,05 à 20,45 points de rang (étendue 1,41); `genomic_max_vaf_eot` reste à 41,67 dans ces trois ordres. Ce sont des observations sur un seul jeu et trois dispositions précises.

![Seuils de rang par axe et ordre](results/AXIS_ORDER_SENSITIVITY.png)

### Couverture réelle des estimateurs par flux

Le fait que le pipeline appelle 29 estimateurs ne signifie pas que 29 sorties finies sont disponibles pour chaque flux. Le tableau ci-dessous compte, pour chaque flux, le nombre moyen de types d'estimateur ayant au moins une valeur finie dans une matrice flux × contrôle × ordre. La disponibilité ne mesure ni significativité ni validité biologique.

{chr(10).join(coverage_table)}

![Couverture finie estimateurs par contrôle et flux](results/CONTROL_FLUX_ESTIMATOR_COVERAGE.png)

Les flux `ras_vaf_pre`, `ras_vaf_on` et les trois deltas n'ont aucune valeur moyenne d'estimateur finie dans le run pilote `dose_mg`; `ras_vaf_eot` n'a que quelques valeurs finies dans ce run. Ils restent dans les matrices de flux avec leurs valeurs manquantes, sans être imputés. Les CSV d'audit donnent le détail de chaque paire, de chaque ordre et des indicateurs de monotonie.

### Contrôles mis en abstention

{chr(10).join(abstain_table)}

### Résumé complet des 48 passages

Chaque ligne correspond à un contrôle candidat dans une disposition des lignes. `T0 interne` est donné uniquement quand le pipeline a franchi son minimum de 50 valeurs; les lignes en abstention n'ont pas de seuil calculé. Les durées sont le temps observé pour chaque passage sur cet environnement.

{chr(10).join(detail_table)}

## Lecture permise et limites

**Résultat établi :** v6.0.1 a exécuté la matrice numérique contrôle × flux sans erreur; le contrôle sélectionné est absent des flux mappés. Les seuils de rang dépendent de l'axe et, pour plusieurs colonnes, de l'ordre des lignes. Les flux à données clairsemées produisent peu ou pas d'estimateurs finis.

**Interprétation limitée :** l'ordre patient n'étant pas un temps mesuré, les différences entre source, inversion et mélange sont un diagnostic de dépendance à l'ordre dans un jeu transversal. Elles ne constituent pas une preuve de dynamique tumorale. Les sorties ne testent pas causalement un biomarqueur, ne prédisent pas la réponse d'un patient et ne démontrent pas l'efficacité du daraxonrasib.

**Hypothèse à tester ailleurs :** si certains axes produisent un motif stable et reproductible, il faut d'abord le retrouver dans une cohorte indépendante avec mesures datées/ordonnées pertinentes et unités biologiques confirmées. La présente matrice ne choisit pas un mécanisme ni un traitement.

## Fichiers et reproduction

- Script d'exécution : `run_patient_axis_flux_sweep.py`.
- Script de synthèse : `summarize_patient_axis_flux_sweep.py`.
- Tous les passages, contrôles et empreintes : `results/RUN_MANIFEST.json`, `results/RUN_SUMMARY.csv`.
- Détail contrôle × flux × estimateurs : `results/FLOW_ESTIMATOR_COVERAGE.csv`.
- Seuils par ordre : `results/AXIS_ORDER_SENSITIVITY.csv`.
- Rôle et monotonie des axes/flux : `results/AXIS_FLUX_ROLE_MONOTONICITY.csv`.
- Entrées exactes et sorties complètes compressées, journaux console et matrices `features.csv` : `results/runs/`.
- La source CSV et le code pipeline restent inchangés.

Depuis la racine du projet, `.venv` activé :

```powershell
.\\.venv\\Scripts\\python.exe .\\pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-21\\UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21\\run_patient_axis_flux_sweep.py
.\\.venv\\Scripts\\python.exe .\\pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-21\\UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21\\summarize_patient_axis_flux_sweep.py
```
"""
    (HERE / "REPORT_PDACPATIENT_AXIS_FLUX_AUDIT_FR.md").write_text(report, encoding="utf-8")

    print(json.dumps({
        "status": manifest["status"], "runs": len(runs),
        "success": successful_count, "abstain": abstain_count, "errors": error_count,
        "controls_with_thresholds": pivot["control"].tolist(),
        "largest_order_ranges": pivot[["control", "range_pp"]].head(5).to_dict("records"),
        "lowest_mean_flow_coverage": flow_summary.sort_values("mean_finite_estimator_types").head(5).to_dict("records"),
        "report": str(HERE / "REPORT_PDACPATIENT_AXIS_FLUX_AUDIT_FR.md"),
        "manifest_sha256": sha256(MANIFEST_PATH),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
