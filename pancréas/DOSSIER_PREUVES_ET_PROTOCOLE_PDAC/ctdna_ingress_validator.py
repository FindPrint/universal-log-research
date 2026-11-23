#!/usr/bin/env python3
"""Module d'ingestion et de validation de données ctDNA longitudinales (Format Universal Log).

Ce script automatise la réception de données brutes envoyées par les équipes médicales
(Kirchweger 2022 / Edland 2023 / Schlick 2022). Il normalise les colonnes, vérifie
l'intégrité temporelle et prépare l'entrée pour le Mode Panel Hiérarchique v1.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd


STANDARD_COLUMNS = [
    "patient_id",
    "time_days",
    "visit_label",
    "kras_maf_pct",
    "kras_copies_per_ml",
    "cfdna_total_ng_ml",
    "ca19_9_u_ml",
    "recist_status",
    "scan_progression_day",
    "os_days",
]

# Dictionnaire de correspondances synonymes (regex insensibles à la casse)
COLUMN_SYNONYMS = {
    "patient_id": [r"^pat.*id", r"^subject", r"^patient", r"^id$", r"^num.*patient"],
    "time_days": [r"^time.*day", r"^day", r"^jour", r"^visite.*jour", r"^days_from_baseline"],
    "visit_label": [r"^visit", r"^visite", r"^tp$", r"^timepoint", r"^cycle"],
    "kras_maf_pct": [r"^kras.*maf", r"^maf", r"^vaf", r"^allele_fraction", r"^kras.*pct"],
    "kras_copies_per_ml": [r"^copies.*ml", r"^mut_copies", r"^kras.*copies", r"^conc_mut"],
    "cfdna_total_ng_ml": [r"^cfdna", r"^dna_total", r"^total_cfdna", r"^ng_ml"],
    "ca19_9_u_ml": [r"^ca19", r"^ca_19", r"^ca-19-9", r"^antigene_19"],
    "recist_status": [r"^recist", r"^response", r"^reponse", r"^status.*recist"],
    "scan_progression_day": [r"^pfs.*day", r"^progression.*day", r"^date.*prog", r"^time_to_pd"],
    "os_days": [r"^os.*day", r"^overall.*surv", r"^time_to_death"],
}


def match_column(col_name: str) -> Optional[str]:
    """Associe une colonne brute à son nom standard."""
    clean = col_name.strip().lower()
    for std_name, patterns in COLUMN_SYNONYMS.items():
        for pat in patterns:
            if re.search(pat, clean):
                return std_name
    return None


def validate_and_normalize(input_path: Path, output_path: Optional[Path] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Charge, valide et convertit un fichier clinique brut en format d'ingestion standard."""
    if not input_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    # Chargement CSV, TSV ou XLSX
    if input_path.suffix.lower() in [".xlsx", ".xls"]:
        df_raw = pd.read_excel(input_path)
    elif input_path.suffix.lower() == ".tsv":
        df_raw = pd.read_csv(input_path, sep="\t")
    else:
        df_raw = pd.read_csv(input_path)

    mapping = {}
    for col in df_raw.columns:
        matched = match_column(col)
        if matched and matched not in mapping.values():
            mapping[col] = matched

    df = df_raw.rename(columns=mapping)

    # Vérification des colonnes obligatoires
    required = ["patient_id", "time_days", "kras_maf_pct"]
    missing_req = [c for c in required if c not in df.columns]
    if missing_req:
        raise ValueError(f"Colonnes obligatoires manquantes dans {input_path.name} : {missing_req}. Colonnes détectées : {list(df.columns)}")

    # Tri par patient et temps chronologique
    df = df.sort_values(by=["patient_id", "time_days"]).reset_index(drop=True)

    # Nettoyage des valeurs sentinelles et seuils de détection (ex. '< 0.1%' -> 0.05)
    if "kras_maf_pct" in df.columns:
        df["kras_maf_pct"] = df["kras_maf_pct"].astype(str).str.replace("<", "").str.replace("%", "").str.strip()
        df["kras_maf_pct"] = pd.to_numeric(df["kras_maf_pct"], errors="coerce")

    # Métadonnées de synthèse d'ingestion
    n_patients = df["patient_id"].nunique()
    n_rows = len(df)
    visits_per_patient = df.groupby("patient_id")["time_days"].count()

    summary = {
        "source_file": str(input_path.name),
        "total_records": n_rows,
        "n_patients": int(n_patients),
        "min_visits_per_patient": int(visits_per_patient.min()),
        "max_visits_per_patient": int(visits_per_patient.max()),
        "median_visits_per_patient": float(visits_per_patient.median()),
        "columns_mapped": mapping,
        "has_copies_per_ml": "kras_copies_per_ml" in df.columns,
        "has_ca19_9": "ca19_9_u_ml" in df.columns,
        "has_recist": "recist_status" in df.columns,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        meta_path = output_path.with_suffix(".json")
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    return df, summary


def main():
    parser = argparse.ArgumentParser(description="Ingestion et validation de séries ctDNA pour Universal Log")
    parser.add_argument("input_file", type=str, help="Chemin vers le fichier brut (CSV, TSV ou XLSX)")
    parser.add_argument("--out", type=str, default=None, help="Chemin de sortie standardisé")
    args = parser.parse_args()

    input_p = Path(args.input_file)
    output_p = Path(args.out) if args.out else input_p.with_name(f"{input_p.stem}_STANDARDIZED.csv")

    print(f"Validation du fichier : {input_p}")
    df, summary = validate_and_normalize(input_p, output_p)
    print(f"✓ Ingestion réussie : {summary['n_patients']} patients, {summary['total_records']} visites")
    print(f"✓ Visites médianes par patient : {summary['median_visits_per_patient']}")
    print(f"✓ Fichier prêt pour TLog : {output_p}")


if __name__ == "__main__":
    main()
