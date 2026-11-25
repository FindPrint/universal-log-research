#!/usr/bin/env python3
"""UNIVERSAL_LOG - Analyse exploratoire des courbes Yin et al. via Mode Courtes Courbes.

Les réponses de la feuille source sont en pourcentage de viabilité et sont converties
en fractions avant l'appel du module, dont le modèle 4PL attend des valeurs proches
de 1. Les deux colonnes source sont agrégées par dose sans imputation; leur statut
comme réplicats biologiques indépendants n'est pas établi par le classeur.
Cette analyse des données déjà consultées est exploratoire, pas une validation
indépendante ou confirmatoire.
"""

from __future__ import annotations

import json
import argparse
import hashlib
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
SOURCE_FILENAME = "41467_2025_57520_MOESM17_ESM.xlsx"
SOURCE_SHA256 = "917a1011426c5ee749343ccabf8126e35923a65c4719ec929f84aa29a511f7b1"
ARTICLE_DOI = "10.1038/s41467-025-57520-3"
ARTICLE_TITLE = "Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients"
SOURCE_BOOK = HERE / "source" / SOURCE_FILENAME
MODULE_PATH = HERE.parent / "MODE_COURTES_COURBES"
if not (MODULE_PATH / "UNIVERSAL_LOG_dose_response_v1.py").is_file():
    MODULE_PATH = (
        HERE.parents[1]
        / "DOSSIER_PREUVES_ET_PROTOCOLE_PDAC"
        / "PIPELINES_ET_CODE_SOURCE"
    )
if not (MODULE_PATH / "UNIVERSAL_LOG_dose_response_v1.py").is_file():
    raise FileNotFoundError(
        "UNIVERSAL_LOG_dose_response_v1.py introuvable dans MODE_COURTES_COURBES "
        "ou dans DOSSIER_PREUVES_ET_PROTOCOLE_PDAC/PIPELINES_ET_CODE_SOURCE"
    )
sys.path.insert(0, str(MODULE_PATH))

import UNIVERSAL_LOG_dose_response_v1 as udr


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(source_book: Path = SOURCE_BOOK, output_dir: Path = HERE):
    print("=" * 80)
    print("ANALYSE EXPLORATOIRE YIN — MODE COURTES COURBES TLOG v1.0.0")
    print("=" * 80)

    if not source_book.is_file():
        raise FileNotFoundError(
            f"Fichier source non trouvé : {source_book}. Téléchargez le fichier "
            f"supplémentaire de l'article et indiquez son chemin avec --source."
        )
    source_sha256 = sha256_file(source_book)
    if source_sha256 != SOURCE_SHA256:
        raise ValueError(
            "Source XLSX non vérifiée : son SHA-256 ne correspond pas au fichier "
            f"supplémentaire contrôlé ({SOURCE_SHA256}). Vérifiez le DOI, la "
            "provenance et le schéma avant toute analyse."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    wb = load_workbook(source_book, read_only=True, data_only=True)
    sheet = wb["Figure 6"]

    # Extraction des concentrations (Ligne 96 à 103, col 1)
    concs_raw = [row[0] for row in sheet.iter_rows(min_row=96, max_row=103, min_col=1, max_col=1, values_only=True)]
    concs = np.array([float(c) for c in concs_raw if c is not None])

    # Extraction des en-têtes (Ligne 95)
    headers = list(next(sheet.iter_rows(min_row=95, max_row=95, values_only=True)))

    # Extraction de toutes les valeurs (Lignes 96 à 103)
    rows_data = list(sheet.iter_rows(min_row=96, max_row=103, values_only=True))
    wb.close()

    expected_concentrations = np.array(
        [200, 50, 12.5, 3.125, 0.78125, 0.1953125, 0.0488281, 0.012207]
    )
    if (
        not headers
        or headers[0] != "Drug Concentration(Log)"
        or len(concs) != len(expected_concentrations)
        or not np.allclose(concs, expected_concentrations, rtol=1e-6, atol=1e-9)
        or len(headers) != 151
        or len(rows_data) != 8
    ):
        raise ValueError(
            "Schéma de la feuille Figure 6 inattendu; aucun résultat n'a été écrit."
        )

    print(f"✓ Source chargée : {source_book.name}")
    print(f"✓ Concentrations de test ({len(concs)} doses) : {concs}")

    # Regroupement des conditions, chacune occupant deux colonnes source.
    conditions = []
    current_label = None
    rep_cols = []

    for col_idx in range(1, len(headers)):
        h = headers[col_idx]
        if h is not None:
            if current_label is not None and len(rep_cols) > 0:
                conditions.append((current_label, rep_cols))
            current_label = str(h).strip()
            rep_cols = [col_idx]
        else:
            if current_label is not None:
                rep_cols.append(col_idx)

    if current_label is not None and len(rep_cols) > 0:
        conditions.append((current_label, rep_cols))

    if len(conditions) != 75 or any(
        len(cols) != 2 or not label.startswith("DAC_")
        for label, cols in conditions
    ):
        raise ValueError(
            "Schéma inattendu : 75 conditions DAC avec deux colonnes source "
            "chacune étaient attendues."
        )

    print(f"✓ Conditions détectées : {len(conditions)} (total {len(headers)-1} colonnes source)")

    # Exécution de l'analyse TLog dose-réponse
    results = []
    t0_start = time.perf_counter()

    for cond_idx, (label, cols) in enumerate(conditions):
        if len(cols) != 2:
            raise ValueError(
                f"Expected two source columns for {label!r}, found {len(cols)}."
            )

        # Parsing Organoid ID et Drug Name
        # Format attendu : "DAC_2_Lumacaftor" -> cell_id="DAC_2", drug="Lumacaftor"
        parts = label.split("_")
        if len(parts) >= 3 and parts[0] == "DAC":
            cell_id = f"{parts[0]}_{parts[1]}"
            drug_name = "_".join(parts[2:])
        else:
            cell_id = label
            drug_name = label

        # Les valeurs de la feuille sont des pourcentages; le module attend des fractions.
        source_series = []
        for c in cols:
            vals = [r[c] for r in rows_data]
            clean_vals = [
                float(v) / 100.0 if v is not None and np.isfinite(float(v)) else np.nan
                for v in vals
            ]
            source_series.append(clean_vals)

        # Two source columns are measurements, not assumed biological replicates.
        mat = np.array(source_series, dtype=float)

        # Gestion des doses valides (Tezacaftor a 7 doses au lieu de 8)
        valid_mask = ~np.isnan(mat).all(axis=0)
        cond_doses = concs[valid_mask]
        cond_mat = mat[:, valid_mask]

        # Tri par dose croissante obligatoire
        order = np.argsort(cond_doses)
        sorted_doses = cond_doses[order]
        sorted_mat = cond_mat[:, order]

        mean_curve = np.nanmean(sorted_mat, axis=0)
        if not np.all(np.isfinite(mean_curve)):
            raise ValueError(f"Non-finite response remains for {label!r}.")

        # One aggregated curve avoids bootstrap claims about undocumented replicates.
        res = udr.analyze_dose_response_curve(
            doses=sorted_doses,
            replicates=mean_curve,
            drug_name=drug_name,
            cell_id=cell_id,
            n_bootstrap=0,
            random_seed=42 + cond_idx
        )

        res_dict = udr.asdict(res)
        fit_diagnostic = udr.fit_4pl_sigmoid(sorted_doses, mean_curve)
        res_dict["condition_label"] = label
        res_dict["n_source_columns"] = len(cols)
        res_dict["source_response_unit"] = "percent_viability"
        res_dict["analysis_response_unit"] = "fraction_viability"
        res_dict["replicate_relationship"] = "not established; columns averaged"
        res_dict["fit_4pl_in_range"] = bool(fit_diagnostic.get("in_range", False))
        results.append(res_dict)

    elapsed = time.perf_counter() - t0_start
    print(f"✓ Analyse terminée en {elapsed:.2f} s ({elapsed/len(conditions)*1000:.1f} ms/condition)")

    # Synthèse globale
    df = pd.DataFrame(results)
    csv_path = output_dir / "YIN_2025_FIG6D_TLOG_CORRECTED_UNITS_RESULTS.csv"
    json_path = output_dir / "YIN_2025_FIG6D_TLOG_CORRECTED_UNITS_RESULTS.json"
    manifest_path = output_dir / "YIN_2025_FIG6D_TLOG_CORRECTED_UNITS_MANIFEST.json"
    if csv_path.exists() or json_path.exists() or manifest_path.exists():
        raise FileExistsError(
            "Corrected output exists; choose an empty output directory to preserve it."
        )
    df.to_csv(csv_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    manifest = {
        "status": "EXPLORATORY_POST_HOC_REANALYSIS",
        "source_filename": source_book.name,
        "source_sha256": source_sha256,
        "article_doi": ARTICLE_DOI,
        "article_title": ARTICLE_TITLE,
        "article_pmid": "40044664",
        "article_pmcid": "PMC11882848",
        "provenance_note": (
            "The article reports patient-derived organoid drug screening; "
            "Figure 6d describes dose-response curves for CFTR correctors."
        ),
        "source_sheet": "Figure 6",
        "source_rows": [95, 103],
        "source_measurement_columns": len(headers) - 1,
        "condition_count": len(conditions),
        "response_conversion": "percent viability divided by 100",
        "missing_values": "omit dose only when both source columns are missing; no imputation",
        "source_column_relationship": (
            "not documented as independent biological replicates; averaged by dose"
        ),
        "bootstrap_replicates": 0,
        "analysis_module": "UNIVERSAL_LOG_dose_response_v1.py",
        "analysis_module_version": udr.VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scipy_version": scipy.__version__,
        "outputs": {
            csv_path.name: sha256_file(csv_path),
            json_path.name: sha256_file(json_path),
        },
        "limitations": [
            "The same source data were previously inspected; this analysis is post hoc.",
            "The results are not an independent or confirmatory validation.",
            "The 4PL comparison uses the same dose-response observations as TLog.",
            "TLog VALIDE status does not establish accuracy or clinical utility.",
        ],
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    n_valide = sum(df["status"] == "VALIDE")
    n_indet = sum(df["status"] == "INDÉTERMINÉ")
    n_abst = sum(df["abstention"])
    n_4pl_conv = sum(df["fit_4pl_converged"])
    n_4pl_in_range = sum(df["fit_4pl_in_range"])
    t0_available = df["t0_dose"].notna().sum()
    ic50_available = df["ic50_tlog"].notna().sum()

    print("\n" + "=" * 80)
    print("RÉSULTATS EXPLORATOIRES YIN Figure 6d — unités corrigées")
    print("=" * 80)
    print(f"Total conditions analysées : {len(df)}")
    print(f"Statut VALIDE              : {n_valide} / {len(df)} ({n_valide/len(df)*100:.1f}%)")
    print(f"Statut INDÉTERMINÉ         : {n_indet} / {len(df)} ({n_indet/len(df)*100:.1f}%)")
    print(f"T0_dose calculé            : {t0_available} / {len(df)} ({t0_available/len(df)*100:.1f}%)")
    print(f"IC50_tlog calculé          : {ic50_available} / {len(df)} ({ic50_available/len(df)*100:.1f}%)")
    print(f"Modèle Hill 4PL convergent : {n_4pl_conv} / {len(df)} ({n_4pl_conv/len(df)*100:.1f}%)")
    print(f"Modèle Hill 4PL en plage   : {n_4pl_in_range} / {len(df)} ({n_4pl_in_range/len(df)*100:.1f}%)")
    print(f"Nombre moyen d'estimateurs : {df['n_finite_estimators'].mean():.2f} / 5")
    print(f"Régimes dominants          : {dict(df['regime_tlog'].value_counts())}")
    print(f"\nFichiers sauvegardés :")
    print(f"  - CSV  : {csv_path}")
    print(f"  - JSON : {json_path}")
    print(f"  - Manifest: {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyse exploratoire TLog des courbes source Yin; ne constitue pas une validation."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE_BOOK,
        help="Chemin du fichier supplémentaire XLSX de l'étude (non inclus).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=HERE,
        help="Dossier de sortie; les fichiers existants ne sont jamais écrasés.",
    )
    args = parser.parse_args()
    main(source_book=args.source, output_dir=args.output_dir)
