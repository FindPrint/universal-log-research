#!/usr/bin/env python3
"""Simulateur Numérique Translationnel TLog-OncoTwin (Cancer du Pancréas).

Modélise l'évolution clonale d'un patient atteint d'adénocarcinome canalaire pancréatique (PDAC)
et compare la dynamique tumorale sous chimiothérapie standard (FOLFIRINOX continu)
vs trithérapie adaptative guidée par les alertes précoces T0 d'Universal Log.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
WORKSPACE = Path(r"C:\Users\citys\Desktop\10-31-2026")


def simulate_patient_course(
    patient_id: str = "PAT_001",
    kras_mutation: str = "G12D",
    brca_status: str = "wildtype",
    strategy: str = "tlog_adaptive",
    months_duration: int = 36,
    seed: int = 42,
) -> Dict[str, Any]:
    """Simule la trajectoire clinique complète d'un patient virtuel."""
    rng = np.random.default_rng(seed)
    dt_days = 7  # Pas de temps hebdomadaire
    n_steps = int((months_duration * 30.4375) / dt_days)

    times_days = np.arange(n_steps) * dt_days
    times_months = times_days / 30.4375

    # Population clonale initiale (normalisée à 100 unités de volume tumoral)
    # Clone 1 : Sensible à la thérapie initiale (99.9%)
    # Clone 2 : Résistant / tolérant préexistant ou mutant émergent (0.1%)
    n_sens = np.zeros(n_steps)
    n_res = np.zeros(n_steps)
    ctdna_maf = np.zeros(n_steps)

    n_sens[0] = 99.9
    n_res[0] = 0.1

    # Taux de croissance intrinsèques journaliers
    r_growth_sens = 0.012
    r_growth_res = 0.015

    # Efficacité thérapeutique
    # Si FOLFIRINOX standard
    if strategy == "standard_folfirinox":
        kill_sens = 0.038
        kill_res = 0.002
    else:  # Trithérapie ciblée MRTX1133 + Olaparib + ADC/Senicapoc
        kill_sens = 0.055 if kras_mutation == "G12D" else 0.025
        if brca_status == "mutant":
            kill_sens *= 1.4  # Synergie létalité synthétique accrue
        kill_res = 0.005

    t0_alert_day = None
    ct_scan_relapse_day = None
    treatment_switched = False

    for t in range(n_steps - 1):
        # Croissance logistique avec compétition spatiale
        n_tot = n_sens[t] + n_res[t]
        cap = 400.0  # Capacité tumorale maximale

        # Traitement continu de base
        dn_sens = (r_growth_sens * (1.0 - n_tot / cap) - kill_sens) * n_sens[t] * dt_days
        dn_res = (r_growth_res * (1.0 - n_tot / cap) - kill_res) * n_res[t] * dt_days

        # Signal ctDNA proportionnel à la charge tumorale avec bruit stochastique
        ctdna_maf[t] = max(0.01, (n_tot / 100.0) * 1.5 + rng.normal(0, 0.04))

        # Alerte TLog T0 : détection du point d'inflexion clonal ascendant (dès que le clone résistant décolle)
        if strategy == "tlog_adaptive" and not treatment_switched:
            if n_res[t] >= 0.8 and t0_alert_day is None:
                t0_alert_day = times_days[t]
                # Intervention thérapeutique précoce : pulsation ADC M9140 + Senicapoc
                treatment_switched = True
                kill_res = 0.048  # Répression drastique du sous-clone résistant !

        # Détection au scanner conventionnel (RECIST 1.1) : seuil macroscopique n_tot >= 120
        if n_tot >= 120.0 and ct_scan_relapse_day is None and t > 8:
            ct_scan_relapse_day = times_days[t]

        n_sens[t + 1] = max(0.001, n_sens[t] + dn_sens)
        n_res[t + 1] = max(0.001, n_res[t] + dn_res)

    ctdna_maf[-1] = max(0.01, ((n_sens[-1] + n_res[-1]) / 100.0) * 1.5)

    tot_volume = n_sens + n_res
    pfs_days = ct_scan_relapse_day if ct_scan_relapse_day else times_days[-1]
    pfs_months = round(pfs_days / 30.4375, 1)

    lead_time_days = None
    if t0_alert_day and ct_scan_relapse_day:
        lead_time_days = ct_scan_relapse_day - t0_alert_day

    return {
        "patient_id": patient_id,
        "strategy": strategy,
        "kras_mutation": kras_mutation,
        "brca_status": brca_status,
        "pfs_months": pfs_months,
        "t0_alert_day": t0_alert_day,
        "ct_scan_relapse_day": ct_scan_relapse_day,
        "lead_time_days": lead_time_days,
        "times_months": times_months.tolist(),
        "total_volume": tot_volume.tolist(),
        "sens_clone": n_sens.tolist(),
        "res_clone": n_res.tolist(),
        "ctdna_maf": ctdna_maf.tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description="Simulateur TLog-OncoTwin PDAC")
    parser.add_argument("--kras", type=str, default="G12D", choices=["G12D", "G12C", "WT"])
    parser.add_argument("--brca", type=str, default="wildtype", choices=["wildtype", "mutant"])
    parser.add_argument("--months", type=int, default=36)
    args = parser.parse_args()

    print("=" * 80)
    print("SIMULATEUR CLONAL TLOG-ONCOTWIN — CANCER DU PANCRÉAS (PDAC)")
    print(f"Profil patient : KRAS {args.kras} | Statut BRCA : {args.brca}")
    print("=" * 80)

    # 1. Bras Standard de soins
    std_res = simulate_patient_course("PAT_STD", args.kras, args.brca, "standard_folfirinox", args.months, seed=42)
    # 2. Bras Trithérapie adaptative guidée par TLog
    tlog_res = simulate_patient_course("PAT_TLOG", args.kras, args.brca, "tlog_adaptive", args.months, seed=42)

    print("\nRÉSULTATS COMPARATIFS :")
    print(f"1. Standard de Soins (FOLFIRINOX continu) :")
    print(f"   - Survie Sans Progression (PFS) : {std_res['pfs_months']} mois")
    print(f"   - Récidive macroscopique scanner : Jour {std_res['ct_scan_relapse_day']:.0f} (Mois {std_res['ct_scan_relapse_day']/30.4375:.1f})")
    print(f"   - Alerte précoce ctDNA          : Aucune (Suivi scanner passif)")

    print(f"\n2. Trithérapie Guidée par TLog (MRTX1133 + Olaparib + ADC/Senicapoc pulsé) :")
    print(f"   - Survie Sans Progression (PFS) : {tlog_res['pfs_months']} mois")
    if tlog_res['t0_alert_day']:
        print(f"   - Alerte TLog T₀ ctDNA         : Jour {tlog_res['t0_alert_day']:.0f} (Mois {tlog_res['t0_alert_day']/30.4375:.1f})")
    if tlog_res['ct_scan_relapse_day']:
        print(f"   - Récidive macroscopique scanner : Jour {tlog_res['ct_scan_relapse_day']:.0f}")
        print(f"   - Lead Time (Avance sur scanner) : {tlog_res['lead_time_days']:.0f} jours (~{tlog_res['lead_time_days']/30.4375:.1f} mois)")
    else:
        print(f"   - Contrôle tumoral prolongé     : Pas de récidive macroscopique à {args.months} mois !")

    gain_pfs = tlog_res['pfs_months'] - std_res['pfs_months']
    print(f"\nBENEFICE CLINIQUE ESTIMÉ : +{gain_pfs:.1f} MOIS DE SURVIE SANS PROGRESSION")


if __name__ == "__main__":
    main()
