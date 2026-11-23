#!/usr/bin/env python3
"""UNIVERSAL_LOG - Benchmark Réel Yin et al. 2025 (Nature Comms) via Mode Courtes Courbes v1.

Ce script résout formellement le verrou identifié le 21 novembre 2026 :
- Le 21 nov, v6.0.0 avait rejeté 150/150 colonnes de la Figure 6d (46 PDOs x médicaments) par le seuil N >= 50.
- Aujourd'hui, UNIVERSAL_LOG_dose_response_v1.py évalue l'ensemble des 75 conditions appariées
  (150 colonnes réplicats) et extrait T0_dose, IC50_tlog, AUC_tlog et le consensus dimensionnel.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
WORKSPACE = Path(r"C:\Users\citys\Desktop\10-31-2026")
SOURCE_BOOK = WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "AUDIT_RECOMMANDATIONS_PETITES_COHORTES" / "source" / "41467_2025_57520_MOESM17_ESM.xlsx"
MODULE_PATH = WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-23" / "MODE_COURTES_COURBES"
sys.path.insert(0, str(MODULE_PATH))

import UNIVERSAL_LOG_dose_response_v1 as udr


def main():
    print("=" * 80)
    print("BENCHMARK RÉEL YIN ET AL. (2025) — MODE COURTES COURBES TLOG v1.0.0")
    print("=" * 80)

    if not SOURCE_BOOK.is_file():
        raise FileNotFoundError(f"Fichier source non trouvé : {SOURCE_BOOK}")

    wb = load_workbook(SOURCE_BOOK, read_only=True, data_only=True)
    sheet = wb["Figure 6"]

    # Extraction des concentrations (Ligne 96 à 103, col 1)
    concs_raw = [row[0] for row in sheet.iter_rows(min_row=96, max_row=103, min_col=1, max_col=1, values_only=True)]
    concs = np.array([float(c) for c in concs_raw if c is not None])

    # Extraction des en-têtes (Ligne 95)
    headers = list(next(sheet.iter_rows(min_row=95, max_row=95, values_only=True)))

    # Extraction de toutes les valeurs (Lignes 96 à 103)
    rows_data = list(sheet.iter_rows(min_row=96, max_row=103, values_only=True))
    wb.close()

    print(f"✓ Source chargée : {SOURCE_BOOK.name}")
    print(f"✓ Concentrations de test ({len(concs)} doses) : {concs}")

    # Regroupement des 75 conditions (chacune occupant 2 colonnes réplicats)
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

    print(f"✓ Conditions expérimentales détectées : {len(conditions)} conditions (total {len(headers)-1} colonnes)")

    # Exécution de l'analyse TLog dose-réponse
    results = []
    t0_start = time.perf_counter()

    for cond_idx, (label, cols) in enumerate(conditions):
        # Parsing Organoid ID et Drug Name
        # Format attendu : "DAC_2_Lumacaftor" -> cell_id="DAC_2", drug="Lumacaftor"
        parts = label.split("_")
        if len(parts) >= 3 and parts[0] == "DAC":
            cell_id = f"{parts[0]}_{parts[1]}"
            drug_name = "_".join(parts[2:])
        else:
            cell_id = label
            drug_name = label

        # Extraction des séries réplicats
        rep_series = []
        for c in cols:
            vals = [r[c] for r in rows_data]
            clean_vals = [float(v) if v is not None and not np.isnan(float(v)) else np.nan for v in vals]
            rep_series.append(clean_vals)

        # Matrice (R, N)
        mat = np.array(rep_series, dtype=float)

        # Gestion des doses valides (Tezacaftor a 7 doses au lieu de 8)
        valid_mask = ~np.isnan(mat).all(axis=0)
        cond_doses = concs[valid_mask]
        cond_mat = mat[:, valid_mask]

        # Tri par dose croissante obligatoire
        order = np.argsort(cond_doses)
        sorted_doses = cond_doses[order]
        sorted_mat = cond_mat[:, order]

        # Imputation médiane simple si un seul puits manque dans un réplicat
        for i in range(sorted_mat.shape[0]):
            for j in range(sorted_mat.shape[1]):
                if np.isnan(sorted_mat[i, j]):
                    col_vals = sorted_mat[:, j]
                    col_valid = col_vals[~np.isnan(col_vals)]
                    sorted_mat[i, j] = np.median(col_valid) if len(col_valid) > 0 else 100.0

        # Appel du module TLog
        res = udr.analyze_dose_response_curve(
            doses=sorted_doses,
            replicates=sorted_mat,
            drug_name=drug_name,
            cell_id=cell_id,
            n_bootstrap=100,
            random_seed=42 + cond_idx
        )

        res_dict = udr.asdict(res)
        res_dict["condition_label"] = label
        res_dict["n_source_columns"] = len(cols)
        results.append(res_dict)

    elapsed = time.perf_counter() - t0_start
    print(f"✓ Analyse terminée en {elapsed:.2f} s ({elapsed/len(conditions)*1000:.1f} ms/condition)")

    # Synthèse globale
    df = pd.DataFrame(results)
    csv_path = HERE / "YIN_2025_PDO_TLOG_BENCHMARK_RESULTS.csv"
    json_path = HERE / "YIN_2025_PDO_TLOG_BENCHMARK_RESULTS.json"
    df.to_csv(csv_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    n_valide = sum(df["status"] == "VALIDE")
    n_indet = sum(df["status"] == "INDÉTERMINÉ")
    n_abst = sum(df["abstention"])
    n_4pl_conv = sum(df["fit_4pl_converged"])
    t0_available = df["t0_dose"].notna().sum()
    ic50_available = df["ic50_tlog"].notna().sum()

    print("\n" + "=" * 80)
    print("RÉSULTATS DU BENCHMARK YIN 2025 Figure 6d")
    print("=" * 80)
    print(f"Total conditions analysées : {len(df)}")
    print(f"Statut VALIDE              : {n_valide} / {len(df)} ({n_valide/len(df)*100:.1f}%)")
    print(f"Statut INDÉTERMINÉ         : {n_indet} / {len(df)} ({n_indet/len(df)*100:.1f}%)")
    print(f"T0_dose calculé            : {t0_available} / {len(df)} ({t0_available/len(df)*100:.1f}%)")
    print(f"IC50_tlog calculé          : {ic50_available} / {len(df)} ({ic50_available/len(df)*100:.1f}%)")
    print(f"Modèle Hill 4PL convergent : {n_4pl_conv} / {len(df)} ({n_4pl_conv/len(df)*100:.1f}%)")
    print(f"Nombre moyen d'estimateurs : {df['n_finite_estimators'].mean():.2f} / 5")
    print(f"Régimes dominants          : {dict(df['regime_tlog'].value_counts())}")
    print(f"\nFichiers sauvegardés :")
    print(f"  - CSV  : {csv_path}")
    print(f"  - JSON : {json_path}")


if __name__ == "__main__":
    main()
