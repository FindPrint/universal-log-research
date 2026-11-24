#!/usr/bin/env python3
"""Vérifications fonctionnelles des modules Universal Log / TLog.

Ces tests vérifient le comportement logiciel sur des entrées synthétiques ou
publiques. Ils ne constituent pas une validation clinique.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def _check_core() -> str:
    module_path = HERE / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
    if not module_path.is_file():
        raise FileNotFoundError(f"Moteur central absent : {module_path}")
    spec = importlib.util.spec_from_file_location("universal_v601", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Chargement impossible : {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    sample = np.sin(np.linspace(0, 12 * np.pi, 256)) + 0.05 * np.cos(
        np.linspace(0, 49 * np.pi, 256)
    )
    estimate = module.get_katz_fd(sample)
    if not np.isfinite(estimate):
        raise AssertionError(f"get_katz_fd a retourné une valeur non finie : {estimate}")
    return f"estimateur Katz exécuté (D={estimate:.4f})"


def _check_short_curves() -> str:
    from UNIVERSAL_LOG_dose_response_v1 import analyze_dose_response_curve

    doses = np.array([0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0])
    expected_ic50 = 0.5
    response = 1.0 / (1.0 + (doses / expected_ic50) ** 1.2)
    rng = np.random.RandomState(42)
    replicates = np.array(
        [
            np.clip(response + rng.normal(0, 0.02, size=len(doses)), 0.01, 1.2)
            for _ in range(3)
        ]
    )
    result = analyze_dose_response_curve(doses, replicates, n_bootstrap=20)
    if result.status != "VALIDE":
        raise AssertionError(f"Courbe synthétique attendue VALIDE, reçu {result.status}")
    if result.n_finite_estimators < 3:
        raise AssertionError(
            f"Nombre insuffisant d'estimateurs finis : {result.n_finite_estimators}"
        )
    if not np.isfinite(result.ic50_tlog) or not 0.1 < result.ic50_tlog < 2.0:
        raise AssertionError(f"IC50 TLog incohérente : {result.ic50_tlog}")
    if not np.isfinite(result.t0_dose) or not np.isfinite(result.auc_tlog):
        raise AssertionError("T0 ou AUC non fini pour la courbe synthétique")

    short_result = analyze_dose_response_curve(
        doses[:5], replicates[:, :5], n_bootstrap=0
    )
    if short_result.status != "INDÉTERMINÉ" or not short_result.abstention:
        raise AssertionError("Une courbe sous la longueur minimale doit être abstentionnée")
    return (
        f"courbe synthétique IC50={result.ic50_tlog:.4f} µM, "
        f"T0={result.t0_dose:.4f} µM; abstention courte vérifiée"
    )


def _check_ctdna_emulation() -> str:
    import ctdna_ingress_validator as validator
    import emulate_and_benchmark_ctdna_cohort as benchmark

    cohort_path = HERE / "EMULATION_KIRCHWEGER_70P_LONGITUDINAL.csv"
    if not cohort_path.is_file():
        raise FileNotFoundError(f"Cohorte d'émulation absente : {cohort_path}")
    normalized, metadata = validator.validate_and_normalize(cohort_path)
    if metadata["n_patients"] != 70 or metadata["total_records"] != 980:
        raise AssertionError(
            "Dimensions inattendues pour l'émulation ctDNA : "
            f"{metadata['n_patients']} patients, {metadata['total_records']} lignes"
        )

    patient_results = pd.DataFrame(
        [
            benchmark.analyze_patient_trajectory_tlog(group)
            for _, group in normalized.groupby("patient_id", sort=True)
        ]
    )
    progressors = patient_results[patient_results["outcome"] == "PD"]
    stable = patient_results[patient_results["outcome"] == "SD_PR"]
    leads = progressors["lead_time_days"].dropna()
    false_alerts = int(stable["tlog_t0_detected"].sum())
    if len(progressors) != 12 or len(leads) != len(progressors):
        raise AssertionError(
            f"Détections/temps d'avance incomplets : {len(leads)}/{len(progressors)}"
        )
    if false_alerts:
        raise AssertionError(f"{false_alerts} fausses alertes dans les cas SD/PR simulés")
    median_lead = float(leads.median())
    if not np.isfinite(median_lead) or median_lead <= 0:
        raise AssertionError(f"Médiane de lead-time invalide : {median_lead}")
    return (
        f"ÉMULATION uniquement : 70 patients, 12/12 progressions détectées, "
        f"0/20 alerte SD/PR, médiane={median_lead:.1f} jours"
    )


def _check_oncotwin_simulation() -> str:
    import tlog_oncotwin_simulator as simulator

    standard = simulator.simulate_patient_course(
        patient_id="VERIFY_STD", strategy="standard_folfirinox", seed=42
    )
    adaptive = simulator.simulate_patient_course(
        patient_id="VERIFY_TLOG", strategy="tlog_adaptive", seed=42
    )
    standard_pfs = float(standard["pfs_months"])
    adaptive_pfs = float(adaptive["pfs_months"])
    if not np.isfinite(standard_pfs) or not np.isfinite(adaptive_pfs):
        raise AssertionError("PFS simulée non finie")
    if adaptive_pfs <= standard_pfs:
        raise AssertionError(
            "Le scénario adaptatif doit dépasser le scénario standard dans "
            f"cette simulation fixe : {adaptive_pfs} <= {standard_pfs}"
        )
    return (
        f"SIMULATION uniquement : standard={standard_pfs:.1f} mois, "
        f"adaptatif={adaptive_pfs:.1f} mois, différence={adaptive_pfs-standard_pfs:+.1f}"
    )


def _check_gdsc2_inspired_curves() -> str:
    from UNIVERSAL_LOG_dose_response_v1 import analyze_dose_response_curve

    curves_path = HERE / "GDSC2_PDAC_REFERENCE_CURVES.csv"
    if not curves_path.is_file():
        raise FileNotFoundError(f"Jeu de courbes absent : {curves_path}")
    curves = pd.read_csv(curves_path)
    required = {
        "drug_name",
        "cell_line",
        "replicate",
        "dose_uM",
        "viability_pct",
        "ic50_reference_synthetic_uM",
    }
    missing = required.difference(curves.columns)
    if missing:
        raise AssertionError(f"Colonnes manquantes dans le jeu de courbes : {sorted(missing)}")
    if curves[list(required)].isna().any().any():
        raise AssertionError("Valeurs manquantes dans les colonnes requises du jeu de courbes")

    estimates: list[float] = []
    references: list[float] = []
    n_valid = 0
    grouped = curves.groupby(["drug_name", "cell_line"], sort=True)
    for (drug_name, cell_line), group in grouped:
        if group["ic50_reference_synthetic_uM"].nunique() != 1:
            raise AssertionError(f"IC50 de référence incohérente : {drug_name}/{cell_line}")
        matrix = group.pivot(index="replicate", columns="dose_uM", values="viability_pct")
        if matrix.isna().any().any():
            raise AssertionError(f"Courbe incomplète : {drug_name}/{cell_line}")
        result = analyze_dose_response_curve(
            doses=matrix.columns.to_numpy(dtype=float),
            replicates=matrix.to_numpy(dtype=float),
            drug_name=str(drug_name),
            cell_id=str(cell_line),
            n_bootstrap=0,
        )
        if result.status != "VALIDE" or not np.isfinite(result.log_ic50_tlog):
            raise AssertionError(
                f"Courbe non exploitable {drug_name}/{cell_line} : "
                f"{result.status}, IC50={result.log_ic50_tlog}"
            )
        reference = float(group["ic50_reference_synthetic_uM"].iloc[0])
        if reference <= 0:
            raise AssertionError(f"IC50 de référence non positive : {reference}")
        estimates.append(float(result.log_ic50_tlog))
        references.append(float(np.log10(reference)))
        n_valid += 1

    if len(grouped) != 25 or len(curves) != 675:
        raise AssertionError(
            f"Dimensions inattendues : {len(grouped)} courbes, {len(curves)} mesures"
        )
    correlation = float(np.corrcoef(estimates, references)[0, 1])
    if not np.isfinite(correlation) or correlation < 0.95:
        raise AssertionError(f"Corrélation TLog/référence hors tolérance : r={correlation}")
    return (
        f"courbes inspirées GDSC2 simulées : 25 profils analysés, "
        f"675 points, Pearson r={correlation:.4f}"
    )


def run_test_suite() -> bool:
    print("=" * 80)
    print("VÉRIFICATIONS FONCTIONNELLES UNIVERSAL LOG / TLOG")
    print(f"Répertoire : {HERE}")
    print("Portée : tests logiciels; aucun résultat clinique n'est validé ici.")
    print("=" * 80)

    checks: list[tuple[str, Callable[[], str]]] = [
        ("Estimateur central Katz v6.0.1", _check_core),
        ("Dose-réponse courte", _check_short_curves),
        ("Validation et benchmark ctDNA", _check_ctdna_emulation),
        ("Simulateur OncoTwin", _check_oncotwin_simulation),
        ("Courbes GDSC2-inspired", _check_gdsc2_inspired_curves),
    ]
    results = []
    for name, check in checks:
        started = time.perf_counter()
        try:
            detail = check()
            results.append((name, True, time.perf_counter() - started, detail))
        except Exception as exc:
            results.append(
                (name, False, time.perf_counter() - started, f"{type(exc).__name__}: {exc}")
            )

    print("\nRÉSULTATS")
    all_ok = True
    for name, passed, elapsed, detail in results:
        status = "OK" if passed else "ÉCHEC"
        all_ok = all_ok and passed
        print(f"{status:6} | {name:<34} | {elapsed * 1000:>8.1f} ms | {detail}")
    print("=" * 80)
    print(
        "Vérifications fonctionnelles réussies."
        if all_ok
        else "Une ou plusieurs vérifications ont échoué."
    )
    print("Ces résultats ne constituent pas une validation clinique.")
    print("=" * 80)
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if run_test_suite() else 1)
