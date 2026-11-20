#!/usr/bin/env python3
"""Targeted internal sensitivity for TP53 vs acquired KRAS amplification.

Uses the separately reported <=120 mg dose cohort (13 patients) and compares
it descriptively with the 160-300 mg cohort (44 patients). These are from the
same phase 1/2 study, selected for benefit followed by progression; this is
not an independent validation cohort and does not support causal inference.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from scipy.stats import fisher_exact

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_DIR = ROOT / "ANALYSE_THERAPEUTIQUE_2026-11-16" / "daraxonrasib_resistance_2026"
DATA_DIR = SOURCE_DIR / "reanalyzed"
SUPPLEMENT = SOURCE_DIR / "41591_2026_4537_MOESM3_ESM.xlsx"
OUT = HERE / "results_low_dose_internal_sensitivity"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_cohort(filename: str, label: str, expected_n: int) -> pd.DataFrame:
    path = DATA_DIR / filename
    raw = pd.read_csv(path, skiprows=1, dtype=str, keep_default_na=False)
    first = raw.columns[0]
    raw = raw[raw[first].str.fullmatch(r"Patient \d+")].copy()
    if len(raw) != expected_n or raw[first].duplicated().any():
        raise ValueError(f"{filename}: expected {expected_n} unique patient rows, got {len(raw)}")

    tp53 = raw.iloc[:, 6].str.strip().str.casefold().map({"mut": "Mut", "wt": "WT"})
    kras_amp = raw.iloc[:, 5].str.contains(r"\bKRAS\s+AMP\b", case=False, regex=True)
    dose = pd.to_numeric(raw.iloc[:, 1].str.extract(r"(\d+(?:\.\d+)?)", expand=False), errors="coerce")
    return pd.DataFrame({
        "patient_id": raw.iloc[:, 0].str.strip(),
        "dose_stratum": label,
        "planned_dose_mg": dose,
        "baseline_tp53": tp53,
        "acquired_kras_amp": kras_amp.astype(int),
        "acquired_ras_short_text": raw.iloc[:, 4].str.strip(),
        "acquired_ras_cna_text": raw.iloc[:, 5].str.strip(),
    })


def summarize(d: pd.DataFrame, label: str) -> dict[str, object]:
    x = d[d["baseline_tp53"].isin(["Mut", "WT"])].copy()
    mut = x[x["baseline_tp53"] == "Mut"]
    wt = x[x["baseline_tp53"] == "WT"]
    a = int(mut["acquired_kras_amp"].sum())
    b = int(len(mut) - a)
    c = int(wt["acquired_kras_amp"].sum())
    dd = int(len(wt) - c)
    odds_ratio, p_value = fisher_exact([[a, b], [c, dd]], alternative="two-sided")
    return {
        "dose_stratum": label,
        "n_patients_with_tp53_status": int(len(x)),
        "tp53_mut_n": int(len(mut)),
        "tp53_mut_kras_amp_n": a,
        "tp53_mut_kras_amp_fraction": a / len(mut) if len(mut) else float("nan"),
        "tp53_wt_n": int(len(wt)),
        "tp53_wt_kras_amp_n": c,
        "tp53_wt_kras_amp_fraction": c / len(wt) if len(wt) else float("nan"),
        "table_rows_mut_then_wt_columns_amp_then_no_amp": f"[[{a},{b}],[{c},{dd}]]",
        "odds_ratio": float(odds_ratio),
        "fisher_two_sided_p_nominal": float(p_value),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    high = load_cohort("clinical_high_dose_44.csv", "160-300 mg", 44)
    low = load_cohort("clinical_lower_dose_13.csv", "<=120 mg", 13)
    pooled = pd.concat([high, low], ignore_index=True)
    if pooled["patient_id"].nunique() != 57:
        raise ValueError("The two dose cohorts must contain 57 distinct patient IDs")

    comparisons = [
        summarize(high, "160-300 mg"),
        summarize(low, "<=120 mg"),
        summarize(pooled, "pooled 20-300 mg; descriptive only"),
    ]
    summary = pd.DataFrame(comparisons)
    patients = pooled.sort_values("patient_id", key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))

    patients_path = OUT / "patient_level_57_tp53_krasamp.csv"
    summary_path = OUT / "tp53_krasamp_by_dose_stratum.csv"
    report_path = OUT / "ADDENDUM_SENSIBILITE_INTERNE_DOSE.md"
    patients.to_csv(patients_path, index=False)
    summary.to_csv(summary_path, index=False)

    lo = comparisons[1]
    hi = comparisons[0]
    with report_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Sensibilité interne par niveau de dose — TP53 et amplification KRAS\n\n")
        f.write("**Date d’exécution:** 2026-11-17. **Analyse ciblée exploratoire**, ajoutée après la grille principale.\n\n")
        f.write("## Question\n\n")
        f.write("L’association prétraitement TP53 ↔ amplification KRAS acquise observée dans la cohorte 160–300 mg est-elle directionnellement compatible avec la cohorte publiée à ≤120 mg? Le contraste porte sur le statut TP53 prétraitement et l’amplification KRAS acquise reportée à la progression.\n\n")
        f.write("## Résultats descriptifs et tests exacts\n\n")
        f.write("| Strate | TP53 mut avec KRAS AMP | TP53 mut total | TP53 WT avec KRAS AMP | TP53 WT total | OR | p Fisher bilatérale nominale |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for r in comparisons:
            f.write(f"| {r['dose_stratum']} | {r['tp53_mut_kras_amp_n']} | {r['tp53_mut_n']} | {r['tp53_wt_kras_amp_n']} | {r['tp53_wt_n']} | {r['odds_ratio']:.4g} | {r['fisher_two_sided_p_nominal']:.4g} |\n")
        f.write("\n")
        f.write(f"Dans la petite strate ≤120 mg, les proportions observées sont {lo['tp53_mut_kras_amp_fraction']:.1%} pour TP53-mut ({lo['tp53_mut_kras_amp_n']}/{lo['tp53_mut_n']}) et {lo['tp53_wt_kras_amp_fraction']:.1%} pour TP53-WT ({lo['tp53_wt_kras_amp_n']}/{lo['tp53_wt_n']}). Dans la strate 160–300 mg, elles sont {hi['tp53_mut_kras_amp_fraction']:.1%} et {hi['tp53_wt_kras_amp_fraction']:.1%}.\n\n")
        f.write(f"L’OR infini de la petite strate est dû à une cellule nulle (0/4 TP53-WT avec KRAS AMP); le test exact donne p={lo['fisher_two_sided_p_nominal']:.4g}. Ce n’est pas une estimation stable d’un effet très grand. Le résultat regroupé 57-patients (p={comparisons[2]['fisher_two_sided_p_nominal']:.4g}) est nominal, inclut la cohorte principale et ne fournit aucune réplication indépendante.\n\n")
        f.write("## Interprétation permise\n\n")
        f.write("Cette analyse ne constitue pas une réplication indépendante: les deux strates proviennent du même essai de phase 1/2 et sont des cohortes appariées prétraitement/fin de traitement publiées dans le même article. La strate ≤120 mg est petite; son test exact peu puissant et son OR à cellule nulle sont fragiles. La comparaison par dose est descriptive, car dose, époque d’inclusion, durée d’exposition et sélection clinique ne sont pas randomisées ici. Les p sont nominales et ne valent pas validation après la sélection postérieure de cette question. Dans le scan multiaxial complet des 57 patients, le lien TP53–KRAS AMP ne passe pas la correction BH globale (voir rapport principal).\n\n")
        f.write("Aucune conclusion de causalité, de prédiction avant traitement, de choix de combinaison, d’efficacité clinique ou de guérison n’en découle. Le signal de la cohorte principale reste une hypothèse à tester dans une cohorte indépendante incluant aussi les patients sans progression.\n\n")
        f.write("## Reproduction\n\n")
        f.write(r"""Depuis la racine du projet, exécuter:

```powershell
.\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\multi_axis_resistance\analyze_low_dose_internal_sensitivity.py
```

""")
        f.write("Entrées: `clinical_high_dose_44.csv` et `clinical_lower_dose_13.csv`, extraites des tableaux supplémentaires de l’article cité dans le manifeste. Le script conserve une ligne par patient et utilise Fisher exact bilatéral pour le seul contraste défini dans cet addendum après la grille principale.\n")

    inputs = {}
    for name in ["clinical_high_dose_44.csv", "clinical_lower_dose_13.csv"]:
        path = DATA_DIR / name
        inputs[name] = {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
    if SUPPLEMENT.exists():
        inputs[SUPPLEMENT.name] = {"path": str(SUPPLEMENT), "sha256": sha256(SUPPLEMENT), "bytes": SUPPLEMENT.stat().st_size}
    outputs = {}
    for path in [patients_path, summary_path, report_path]:
        outputs[path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    manifest = {
        "analysis_id": "pdac_tp53_krasamp_internal_dose_sensitivity_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "question_status": "targeted exploratory sensitivity; selected after main scan",
        "unit_of_analysis": "one patient; 44 high-dose and 13 lower-dose patients from the same phase 1/2 study",
        "selection_limitation": "both dose strata are drawn from progression-selected acquired-resistance cohorts; no independent validation cohort",
        "comparison": "baseline TP53 mutation status vs KRAS amplification acquired by end of treatment",
        "test": "two-sided Fisher exact test; nominal p-values; no claim of multiplicity-adjusted confirmation",
        "seed": None,
        "inputs": inputs,
        "outputs": outputs,
        "script_sha256": sha256(Path(__file__).resolve()),
        "interpretation": "descriptive within-trial sensitivity only; not causal, predictive, therapeutic, or evidence of cure",
    }
    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary.to_json(orient="records", force_ascii=False))
    print(json.dumps({"output": str(OUT), "manifest": str(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
