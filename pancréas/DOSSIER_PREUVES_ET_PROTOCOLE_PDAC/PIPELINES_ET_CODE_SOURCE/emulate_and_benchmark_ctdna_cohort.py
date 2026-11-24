#!/usr/bin/env python3
"""Émulation ctDNA synthétique pour tester le code d'analyse.

Ce script génère des trajectoires artificielles illustratives. Elles ne proviennent
pas de patients ni de l'étude Kirchweger 2022 et ne reproduisent pas une cohorte
clinique observée. Les métriques mesurent uniquement le comportement du code sur
les hypothèses intégrées au générateur :
- 32 patients évaluables avec cinétique complète et réponse RECIST 1.1 connue :
  * 12 Progressions radiologiques (PD) avec échappement clonal et cinétique ctDNA bimensuelle.
  * 20 Réponses / Stabilités (PR/SD) sans élévation de ctDNA.
- Mesures bimensuelles (J0, J14, J28, J42, J56, J70, J84, J98, J112, J126, J140, J154, J168).
- Évaluation TLog en Mode Panel Hiérarchique (analyse patient par patient sans concaténation).
- Calcul du "Lead Time" : délai d'avance du signal TLog T0 sur le scanner RECIST 1.1.
"""

from __future__ import annotations

import json
import math
import sys
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


def generate_kirchweger_cohort(n_evaluable=32, n_total=70, seed=20261123) -> pd.DataFrame:
    """Génère une cohorte de démonstration synthétique, sans données patient réelles."""
    rng = np.random.default_rng(seed)
    records = []

    # 14 points de suivi bimensuel (28 semaines = ~6.5 mois)
    visit_days = np.array([0, 14, 28, 42, 56, 70, 84, 98, 112, 126, 140, 154, 168, 182])

    for pat_idx in range(1, n_total + 1):
        pat_id = f"PAT_{pat_idx:03d}"

        # Détermination du statut clinique
        if pat_idx <= 12:
            outcome = "PD"  # Progression radiologique documentée
            scan_prog_day = rng.choice([112, 126, 140, 154, 168])
            # La transition biologique ctDNA commence ~80 à 120 jours avant le scanner
            t_bio_escape = max(14, scan_prog_day - rng.integers(70, 110))
        elif pat_idx <= 32:
            outcome = "SD_PR"  # Répondeurs / Stables
            scan_prog_day = np.nan
            t_bio_escape = 9999
        else:
            outcome = "SURVEILLANCE"
            scan_prog_day = np.nan
            t_bio_escape = 9999

        # Statut Lewis (10% de Lewis-négatifs avec CA19-9 non sécréteur < 5 U/mL)
        is_lewis_negative = rng.random() < 0.10
        base_ca19_9 = rng.uniform(20, 450) if not is_lewis_negative else rng.uniform(1, 4)

        for day in visit_days:
            # Trajectoire ctDNA (KRAS MAF %)
            if outcome == "PD":
                if day < t_bio_escape:
                    # Phase de rémission / réponse initiale sous chimiothérapie
                    maf = max(0.01, rng.normal(0.08, 0.03))
                else:
                    # Échappement clonal : croissance exponentielle
                    dt = day - t_bio_escape
                    maf = 0.08 * math.exp(0.045 * dt) + rng.normal(0, 0.05)
                    maf = max(0.05, min(maf, 35.0))
            else:
                # Répondeurs / stables : MAF résiduelle basse ou indétectable
                maf = max(0.005, rng.normal(0.04, 0.02))

            # Copies par mL (corrélées à la MAF et à la charge de cfDNA)
            cfdna = rng.normal(12.5, 3.0) + (maf * 0.4)
            cfdna = max(5.0, cfdna)
            copies_ml = (maf / 100.0) * (cfdna * 300.0) + rng.normal(0, 1.0)
            copies_ml = max(0.0, copies_ml)

            # Cinétique CA19-9
            if is_lewis_negative:
                ca19_9 = rng.uniform(1.0, 4.5)
            else:
                if outcome == "PD" and day >= (scan_prog_day - 21):
                    # CA19-9 ne monte que 0 à 3 semaines avant le scanner
                    ca19_9 = base_ca19_9 * (1.0 + 0.03 * (day - (scan_prog_day - 21)))
                else:
                    ca19_9 = base_ca19_9 * rng.uniform(0.9, 1.1)

            records.append({
                "patient_id": pat_id,
                "time_days": day,
                "visit_label": f"V_{(day//14)+1:02d}",
                "kras_maf_pct": round(maf, 4),
                "kras_copies_per_ml": round(copies_ml, 2),
                "cfdna_total_ng_ml": round(cfdna, 2),
                "ca19_9_u_ml": round(ca19_9, 1),
                "recist_status": outcome,
                "scan_progression_day": scan_prog_day,
                "lewis_negative": is_lewis_negative,
            })

    return pd.DataFrame(records)


def analyze_patient_trajectory_tlog(patient_df: pd.DataFrame) -> Dict[str, Any]:
    """Applique le module TLog sur la série temporelle ordonnée d'un patient."""
    times = patient_df["time_days"].to_numpy(dtype=float)
    mafs = patient_df["kras_maf_pct"].to_numpy(dtype=float)

    # Réplicat unique (1 x N)
    replicates = mafs.reshape(1, -1)

    # Calcul des estimateurs de complexité TLog
    katz = udr.katz_fd(mafs)
    petro = udr.petrosian_fd(mafs)
    sevcik = udr.sevcik_fd(mafs)
    sampen = udr.sample_entropy_short(mafs)
    dfa = udr.dfa_exponent_short(mafs)

    estimators = [katz, petro, sevcik, sampen, dfa]
    finite_est = [e for e in estimators if e is not None and not np.isnan(e)]

    # Seuil T0 : repérage du premier décrochage significatif de la MAF au-dessus du bruit de fond
    base_noise = np.percentile(mafs[:3], 75)
    threshold = max(0.15, base_noise * 2.5)

    detected_day = None
    for t, m in zip(times, mafs):
        if m >= threshold and t >= 14:
            detected_day = t
            break

    outcome = patient_df["recist_status"].iloc[0]
    scan_day = patient_df["scan_progression_day"].iloc[0]

    lead_time_days = None
    lead_time_months = None
    if detected_day is not None and not np.isnan(scan_day):
        lead_time_days = float(scan_day - detected_day)
        lead_time_months = round(lead_time_days / 30.4375, 2)

    return {
        "patient_id": patient_df["patient_id"].iloc[0],
        "outcome": outcome,
        "n_visits": len(times),
        "tlog_t0_detected": detected_day is not None,
        "tlog_t0_day": detected_day,
        "scan_progression_day": scan_day,
        "lead_time_days": lead_time_days,
        "lead_time_months": lead_time_months,
        "katz_fd": katz,
        "petrosian_fd": petro,
        "sevcik_fd": sevcik,
        "sample_entropy": sampen,
        "dfa_exponent": dfa,
        "n_finite_estimators": len(finite_est),
        "max_maf": float(np.max(mafs)),
        "lewis_negative": bool(patient_df["lewis_negative"].iloc[0]),
    }


def main():
    print("=" * 80)
    print("ÉMULATION SYNTHÉTIQUE CTDNA — SCÉNARIO DE TEST (NON CLINIQUE)")
    print("=" * 80)

    # 1. Génération de la cohorte
    cohort_df = generate_kirchweger_cohort()
    cohort_csv = HERE / "EMULATION_KIRCHWEGER_70P_LONGITUDINAL.csv"
    cohort_df.to_csv(cohort_csv, index=False)
    print(f"✓ Cohorte synthétique générée : {cohort_csv} ({len(cohort_df)} enregistrements, 70 patients)")

    # 2. Analyse patient par patient (Mode Panel Hiérarchique)
    results = []
    for pat_id, pat_df in cohort_df.groupby("patient_id"):
        res = analyze_patient_trajectory_tlog(pat_df)
        results.append(res)

    results_df = pd.DataFrame(results)
    results_csv = HERE / "CTDNA_TLOG_PANEL_BENCHMARK_RESULTS.csv"
    results_df.to_csv(results_csv, index=False)

    # 3. Métriques cliniques diagnostiques
    progressors = results_df[results_df["outcome"] == "PD"]
    non_progressors = results_df[results_df["outcome"] == "SD_PR"]

    tp = sum(progressors["tlog_t0_detected"])
    fn = len(progressors) - tp
    fp = sum(non_progressors["tlog_t0_detected"])
    tn = len(non_progressors) - fp

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    valid_leads = progressors["lead_time_days"].dropna()
    mean_lead_days = float(valid_leads.mean())
    median_lead_days = float(valid_leads.median())
    min_lead_days = float(valid_leads.min())
    max_lead_days = float(valid_leads.max())

    lead_distribution = {
        "data_status": "synthetic_simulation_not_observed_clinical_data",
        "n_progressors_eval": len(progressors),
        "tlog_true_positives": int(tp),
        "sensitivity_pct": round(sensitivity * 100, 1),
        "specificity_pct": round(specificity * 100, 1),
        "mean_lead_time_days": round(mean_lead_days, 1),
        "median_lead_time_days": round(median_lead_days, 1),
        "mean_lead_time_months": round(mean_lead_days / 30.4375, 2),
        "median_lead_time_months": round(median_lead_days / 30.4375, 2),
        "lead_time_range_days": [int(min_lead_days), int(max_lead_days)],
        "lead_time_by_patient": {
            row["patient_id"]: {
                "t0_day": int(row["tlog_t0_day"]),
                "scan_day": int(row["scan_progression_day"]),
                "lead_days": int(row["lead_time_days"]),
                "lead_months": float(row["lead_time_months"]),
            } for _, row in progressors.iterrows() if pd.notna(row["lead_time_days"])
        }
    }

    dist_json = HERE / "CTDNA_LEAD_TIME_DISTRIBUTION.json"
    with dist_json.open("w", encoding="utf-8") as f:
        json.dump(lead_distribution, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("MÉTRIQUES DU SCÉNARIO SYNTHÉTIQUE CTDNA VS SCANNER SIMULÉ")
    print("=" * 80)
    print(f"Sensibilité dans l'émulation        : {tp}/{len(progressors)} ({sensitivity*100:.1f}%)")
    print(f"Spécificité dans l'émulation        : {tn}/{len(non_progressors)} ({specificity*100:.1f}%)")
    print(f"Lead time médian simulé             : {median_lead_days:.1f} jours ({median_lead_days/30.4375:.2f} mois)")
    print(f"Lead time moyen simulé              : {mean_lead_days:.1f} jours ({mean_lead_days/30.4375:.2f} mois)")
    print(f"Fourchette simulée                  : [{min_lead_days:.0f} - {max_lead_days:.0f}] jours")
    print(f"\nFichiers sauvegardés :")
    print(f"  - Cohorte standardisée : {cohort_csv}")
    print(f"  - Résultats patients   : {results_csv}")
    print(f"  - Distribution JSON    : {dist_json}")


if __name__ == "__main__":
    main()
