#!/usr/bin/env python3
"""Benchmark synthétique de courbes dose-réponse inspirées de profils GDSC2/PDAC.

Les courbes sont générées ici à partir de valeurs IC50 et pentes de Hill paramétrées
dans ce fichier. Elles ne sont pas des mesures brutes extraites de GDSC2 ou de Sanger;
la corrélation obtenue compare l'algorithme à ces références synthétiques.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE
if not (MODULE_PATH / "UNIVERSAL_LOG_dose_response_v1.py").is_file():
    MODULE_PATH = (
        HERE.parent
        / "ANALYSE_THERAPEUTIQUE_2026-11-23"
        / "MODE_COURTES_COURBES"
    )
if not (MODULE_PATH / "UNIVERSAL_LOG_dose_response_v1.py").is_file():
    raise FileNotFoundError(
        "UNIVERSAL_LOG_dose_response_v1.py introuvable à côté du script "
        "ou dans ANALYSE_THERAPEUTIQUE_2026-11-23/MODE_COURTES_COURBES"
    )
sys.path.insert(0, str(MODULE_PATH))

import UNIVERSAL_LOG_dose_response_v1 as udr


# Paramètres synthétiques d'IC50/pente de Hill, utilisés comme vérité simulée.
GDSC2_PDAC_PROFILES = {
    "Gemcitabine": {
        "doses": [0.0005, 0.0015, 0.0045, 0.0137, 0.0411, 0.123, 0.370, 1.11, 3.33],
        "cells": {
            "MIA_PaCa-2": {"ic50_reference_synthetic": 0.015, "hill": 1.4, "note": "Sensible KRAS G12C"},
            "Capan-1": {"ic50_reference_synthetic": 0.020, "hill": 1.2, "note": "Sensible BRCA2-mutant"},
            "BxPC-3": {"ic50_reference_synthetic": 0.035, "hill": 1.5, "note": "Sensible KRAS-WT"},
            "PANC-1": {"ic50_reference_synthetic": 0.850, "hill": 0.9, "note": "Résistant KRAS G12D"},
            "AsPC-1": {"ic50_reference_synthetic": 2.400, "hill": 0.8, "note": "Hautement résistant"},
        }
    },
    "Olaparib": {
        "doses": [0.039, 0.117, 0.351, 1.054, 3.16, 9.49, 28.46, 85.38, 256.0],
        "cells": {
            "Capan-1": {"ic50_reference_synthetic": 0.350, "hill": 1.3, "note": "Létalité synthétique BRCA2 (6174delT)"},
            "BxPC-3": {"ic50_reference_synthetic": 15.20, "hill": 0.9, "note": "Résistant BRCA-WT"},
            "MIA_PaCa-2": {"ic50_reference_synthetic": 18.50, "hill": 0.8, "note": "Résistant BRCA-WT"},
            "AsPC-1": {"ic50_reference_synthetic": 22.00, "hill": 0.7, "note": "Résistant BRCA-WT"},
            "PANC-1": {"ic50_reference_synthetic": 25.00, "hill": 0.7, "note": "Résistant BRCA-WT"},
        }
    },
    "5-Fluorouracil": {
        "doses": [0.0312, 0.0937, 0.281, 0.843, 2.53, 7.59, 22.78, 68.34, 205.0],
        "cells": {
            "BxPC-3": {"ic50_reference_synthetic": 2.10, "hill": 1.1, "note": "Sensibilité modérée"},
            "Capan-1": {"ic50_reference_synthetic": 4.20, "hill": 1.0, "note": "Sensibilité modérée"},
            "MIA_PaCa-2": {"ic50_reference_synthetic": 8.50, "hill": 0.9, "note": "Résistance intermédiaire"},
            "PANC-1": {"ic50_reference_synthetic": 14.20, "hill": 0.8, "note": "Résistant"},
            "AsPC-1": {"ic50_reference_synthetic": 18.50, "hill": 0.7, "note": "Hautement résistant"},
        }
    },
    "Paclitaxel": {
        "doses": [0.0002, 0.0006, 0.0019, 0.0057, 0.0171, 0.0514, 0.154, 0.463, 1.39],
        "cells": {
            "MIA_PaCa-2": {"ic50_reference_synthetic": 0.008, "hill": 1.6, "note": "Hautement sensible"},
            "Capan-1": {"ic50_reference_synthetic": 0.010, "hill": 1.4, "note": "Sensible"},
            "BxPC-3": {"ic50_reference_synthetic": 0.012, "hill": 1.3, "note": "Sensible"},
            "PANC-1": {"ic50_reference_synthetic": 0.025, "hill": 1.1, "note": "Sensibilité modérée"},
            "AsPC-1": {"ic50_reference_synthetic": 0.045, "hill": 0.9, "note": "Résistance relative"},
        }
    },
    "Cisplatin": {
        "doses": [0.0625, 0.1875, 0.5625, 1.687, 5.06, 15.19, 45.56, 136.69, 410.0],
        "cells": {
            "Capan-1": {"ic50_reference_synthetic": 1.20, "hill": 1.4, "note": "Sensible (défaut de recombinaison homologue)"},
            "BxPC-3": {"ic50_reference_synthetic": 5.40, "hill": 1.0, "note": "Sensibilité intermédiaire"},
            "MIA_PaCa-2": {"ic50_reference_synthetic": 6.80, "hill": 0.9, "note": "Résistance modérée"},
            "AsPC-1": {"ic50_reference_synthetic": 9.50, "hill": 0.8, "note": "Résistant"},
            "PANC-1": {"ic50_reference_synthetic": 12.50, "hill": 0.8, "note": "Résistant"},
        }
    }
}


def simulate_gdsc2_response(doses: List[float], ic50: float, hill: float, n_reps=3, seed=42) -> np.ndarray:
    """Génère les réplicats biologiques selon le modèle sigmoïde avec bruit réaliste GDSC2."""
    rng = np.random.default_rng(seed)
    d = np.array(doses)
    # Viabilité théorique Hill (normalisée 100% à 0%)
    true_v = 100.0 / (1.0 + (d / ic50) ** hill)

    replicates = []
    for _ in range(n_reps):
        noise = rng.normal(0.0, 4.5, size=len(d))
        noisy_v = true_v + noise
        noisy_v = np.clip(noisy_v, 0.0, 115.0)
        replicates.append(noisy_v)

    return np.array(replicates)


def main():
    print("=" * 80)
    print("BENCHMARK SYNTHÉTIQUE INSPIRÉ DE GDSC2 PDAC — MODE COURTES COURBES TLOG")
    print("=" * 80)

    records = []
    results_tlog = []
    curve_index = 0
    t0_all = time.perf_counter()

    for drug_name, drug_info in GDSC2_PDAC_PROFILES.items():
        doses = drug_info["doses"]
        for cell_name, cell_info in drug_info["cells"].items():
            curve_index += 1
            ic50_reference_synthetic = cell_info["ic50_reference_synthetic"]
            hill = cell_info["hill"]
            note = cell_info["note"]

            reps = simulate_gdsc2_response(doses, ic50_reference_synthetic, hill, n_reps=3, seed=100 + curve_index)

            # Enregistrement pour export des courbes de référence
            for r_idx in range(reps.shape[0]):
                for d_idx, d_val in enumerate(doses):
                    records.append({
                        "drug_name": drug_name,
                        "cell_line": cell_name,
                        "replicate": r_idx + 1,
                        "dose_uM": d_val,
                        "log10_dose": round(math.log10(d_val), 4),
                        "viability_pct": round(reps[r_idx, d_idx], 2),
                        "ic50_reference_synthetic_uM": ic50_reference_synthetic,
                    })

            # Évaluation par le module TLog
            res = udr.analyze_dose_response_curve(
                doses=doses,
                replicates=reps,
                drug_name=drug_name,
                cell_id=cell_name,
                n_bootstrap=100,
                random_seed=200 + curve_index
            )

            res_dict = udr.asdict(res)
            res_dict["ic50_reference_synthetic_uM"] = ic50_reference_synthetic
            res_dict["log10_ic50_reference_synthetic"] = round(math.log10(ic50_reference_synthetic), 4)
            res_dict["biological_note"] = note

            if pd.notna(res.log_ic50_tlog):
                res_dict["delta_log10_vs_synthetic_reference"] = round(res.log_ic50_tlog - math.log10(ic50_reference_synthetic), 4)
            else:
                res_dict["delta_log10_vs_synthetic_reference"] = np.nan

            results_tlog.append(res_dict)

    elapsed = time.perf_counter() - t0_all

    # 1. Export courbes brutes
    curves_df = pd.DataFrame(records)
    curves_csv = HERE / "GDSC2_PDAC_REFERENCE_CURVES.csv"
    curves_df.to_csv(curves_csv, index=False)

    # 2. Export résultats TLog
    res_df = pd.DataFrame(results_tlog)
    res_csv = HERE / "GDSC2_PDAC_TLOG_BENCHMARK_RESULTS.csv"
    res_json = HERE / "GDSC2_PDAC_TLOG_BENCHMARK_RESULTS.json"
    res_df.to_csv(res_csv, index=False)
    with res_json.open("w", encoding="utf-8") as f:
        json.dump(results_tlog, f, indent=2, ensure_ascii=False, default=str)

    # 3. Métriques statistiques de validation
    valid_pairs = res_df.dropna(subset=["log_ic50_tlog", "log10_ic50_reference_synthetic"])
    if valid_pairs.empty or res_df.empty:
        raise ValueError("Aucune courbe exploitable pour calculer les métriques synthétiques.")
    r_corr = np.corrcoef(valid_pairs["log_ic50_tlog"], valid_pairs["log10_ic50_reference_synthetic"])[0, 1]
    mean_abs_delta = valid_pairs["delta_log10_vs_synthetic_reference"].abs().mean()

    n_valide = sum(res_df["status"] == "VALIDE")
    t0_available = res_df["t0_dose"].notna().sum()

    print(f"✓ Total conditions analysées (5 drogues x 5 lignées) : {len(res_df)}")
    print(f"✓ Statut VALIDE TLog       : {n_valide} / {len(res_df)} ({100*n_valide/len(res_df):.1f}%)")
    print(f"✓ T0_dose calculé          : {t0_available} / {len(res_df)} ({100*t0_available/len(res_df):.1f}%)")
    print(f"✓ Corrélation Pearson r    : {r_corr:.4f} (TLog vs IC50 de référence synthétique)")
    print(f"✓ Écart moyen absolu delta : {mean_abs_delta:.3f} dex (~{10**mean_abs_delta:.2f}x)")
    print(f"✓ Temps de calcul total    : {elapsed:.2f} s ({elapsed/len(res_df)*1000:.1f} ms/profil)")

    print("\nSensibilité Capan-1 (BRCA2-mutant) sous Olaparib :")
    cap_olap = res_df[(res_df["cell_id"] == "Capan-1") & (res_df["drug_name"] == "Olaparib")].iloc[0]
    print(f"  - IC50 reference synthetic : {cap_olap['ic50_reference_synthetic_uM']} µM | IC50 TLog : {cap_olap['ic50_tlog']:.3f} µM | T0 rupture : {cap_olap['t0_dose']:.4f} µM")

    print("\nRésistance PANC-1 sous Gemcitabine :")
    panc_gem = res_df[(res_df["cell_id"] == "PANC-1") & (res_df["drug_name"] == "Gemcitabine")].iloc[0]
    print(f"  - IC50 reference synthetic : {panc_gem['ic50_reference_synthetic_uM']} µM | IC50 TLog : {panc_gem['ic50_tlog']:.3f} µM | T0 rupture : {panc_gem['t0_dose']:.4f} µM")


if __name__ == "__main__":
    main()
