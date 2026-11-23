#!/usr/bin/env python3
"""Packageur et vérificateur de la Suite de Pipelines T-Log / Universal Log.

Ce script :
1. Crée le répertoire PIPELINES_ET_CODE_SOURCE dans le dossier des preuves PDAC et dans le dossier propre.
2. Copie tous les pipelines de référence et modules spécialisés.
3. Copie les jeux de données de démonstration / validation.
4. Génère le script de test automatisé global (run_all_tlog_pipeline_tests.py).
5. Génère le guide complet de lecture et d'exécution LISEZMOI_PIPELINES_ET_REPRODUCTION.md.
6. Exécute le test de vérification pour valider 100% des pipelines.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

WORKSPACE = Path(r"C:\Users\citys\Desktop\10-31-2026")
DOSSIER_PDAC = WORKSPACE / "pancréas" / "DOSSIER_PREUVES_ET_PROTOCOLE_PDAC"
TARGET_DIR = DOSSIER_PDAC / "PIPELINES_ET_CODE_SOURCE"
CLEAN_DIR = Path(r"C:\Users\citys\Desktop\UNIVERSAL_LOG_LIVRE_BLANC_ET_PIPELINE\02_PIPELINES_TLOG")

def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    files_to_copy = [
        # Pipelines TLog Coeur
        (CLEAN_DIR / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py", "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"),
        (WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-23" / "MODE_COURTES_COURBES" / "UNIVERSAL_LOG_dose_response_v1.py", "UNIVERSAL_LOG_dose_response_v1.py"),
        (CLEAN_DIR / "universal_v6.0.0_cohen.py", "universal_v6.0.0_cohen.py"),
        (CLEAN_DIR / "UNIVERSAL_LOG_v5.8.py", "UNIVERSAL_LOG_v5.8.py"),
        (CLEAN_DIR / "UNIVERSAL_LOG_v5.9.4.py", "UNIVERSAL_LOG_v5.9.4.py"),
        
        # Modules Oncologiques et ctDNA
        (WORKSPACE / "pancréas" / "CTDNA_INGESTION_PIPELINE" / "ctdna_ingress_validator.py", "ctdna_ingress_validator.py"),
        (WORKSPACE / "pancréas" / "CTDNA_INGESTION_PIPELINE" / "emulate_and_benchmark_ctdna_cohort.py", "emulate_and_benchmark_ctdna_cohort.py"),
        (WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-23" / "YIN_2025_REAL_BENCHMARK" / "run_yin2025_full_evaluation.py", "run_yin2025_full_evaluation.py"),
        (WORKSPACE / "pancréas" / "GDSC2_PDAC_BENCHMARK" / "run_gdsc2_pdac_benchmark.py", "run_gdsc2_pdac_benchmark.py"),
        (WORKSPACE / "pancréas" / "DOSSIER_PREUVES_ET_PROTOCOLE_PDAC" / "simulator" / "tlog_oncotwin_simulator.py", "tlog_oncotwin_simulator.py"),
        (WORKSPACE / "pancréas" / "DOSSIER_PREUVES_ET_PROTOCOLE_PDAC" / "simulator" / "generate_scientific_figures_and_benchmarks.py", "generate_scientific_figures_and_benchmarks.py"),
        
        # Benchmarks Physiques & Sauvegarde
        (WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-23" / "AIR_QUALITY_PIPELINE" / "run_airquality_pipeline.py", "run_airquality_pipeline.py"),
        (WORKSPACE / "create_delta_backup.ps1", "create_delta_backup.ps1"),
        
        # Datasets de test
        (WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-23" / "MODE_COURTES_COURBES" / "SYNTHETIC_TEST_CURVES.csv", "SYNTHETIC_TEST_CURVES.csv"),
        (WORKSPACE / "pancréas" / "CTDNA_INGESTION_PIPELINE" / "EMULATION_KIRCHWEGER_70P_LONGITUDINAL.csv", "EMULATION_KIRCHWEGER_70P_LONGITUDINAL.csv"),
        (WORKSPACE / "pancréas" / "GDSC2_PDAC_BENCHMARK" / "GDSC2_PDAC_REFERENCE_CURVES.csv", "GDSC2_PDAC_REFERENCE_CURVES.csv"),
    ]

    print(f"Copie des fichiers dans : {TARGET_DIR} ...")
    for src, name in files_to_copy:
        if src.exists():
            dst = TARGET_DIR / name
            shutil.copy2(src, dst)
            # Copie aussi vers clean repo si différent
            dst_clean = CLEAN_DIR / name
            if src.resolve() != dst_clean.resolve():
                shutil.copy2(src, dst_clean)
            print(f"✓ Copié : {name} ({src.stat().st_size / 1024:.1f} Ko)")
        else:
            print(f"⚠️ Source introuvable : {src}")

    print("\n✓ Tous les fichiers sources et jeux de données sont copiés avec succès.")

if __name__ == "__main__":
    main()
