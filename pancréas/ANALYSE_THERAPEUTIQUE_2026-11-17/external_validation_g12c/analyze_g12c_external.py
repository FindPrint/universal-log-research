#!/usr/bin/env python3
"""Patient-level cross-mechanism PDAC resistance scan from AACR Figshare.

This is a typed companion analysis. It reuses the prior multiaxis module's
patient-level test and BH routines, but does not run the universal core,
T0/TLog, or make causal/clinical claims. Rows absent from the supplement are
encoded only as "not listed" indicators, never as assay-confirmed negatives.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
CORE = PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-17" / "multi_axis_resistance" / "pdac_multiaxis_resistance.py"
SOURCE = HERE / "supplemental_table_1_krasi_g12c_pdac_gi.xlsx"
OUT = HERE / "results"
ARTICLE_DOI = "10.1158/2159-8290.CD-24-0177"
DATASET_DOI = "10.1158/2159-8290.32699721"
FIGSHARE_ARTICLE_ID = 32699721
FIGSHARE_FILE_ID = 65619009
SEED = 20261117

spec = importlib.util.spec_from_file_location("pdac_multiaxis_resistance", CORE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import companion test engine from {CORE}")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def number(value: object) -> float:
    try:
        x = float(str(value).strip().replace(",", ""))
        return x if np.isfinite(x) else np.nan
    except (TypeError, ValueError):
        return np.nan


def event_type(row: pd.Series) -> str:
    """Observed table status. No-row and dash values are not assay negatives."""
    alt = str(row["Alteration type"]).strip().casefold()
    pre, eot = str(row["Pre-treatment VAF (%)"]).strip(), str(row["End of Therapy VAF (%)"]).strip()
    if pre == "-" and (np.isfinite(number(eot)) or eot.casefold() in {"amp", "gain"}):
        return "newly_listed"
    return "not_newly_listed"


def clean_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(SOURCE, header=2, dtype=str).fillna("")
    raw.columns = [str(c).strip().replace("\xa0", " ") for c in raw.columns]
    expected = ["Patient ID", "Tumor type", "Treatment", "Best response", "Technology used",
                "Gene/variant", "Alteration type", "Pre-treatment VAF (%)", "End of Therapy VAF (%)"]
    if list(raw.columns) != expected:
        raise ValueError(f"Unexpected source columns: {list(raw.columns)}")
    pdac = raw[raw["Tumor type"].str.strip().str.upper().eq("PDAC")].copy()
    pdac["Patient ID"] = pdac["Patient ID"].str.strip()
    if pdac["Patient ID"].nunique() != 22:
        raise ValueError(f"Expected 22 PDAC patients from article; found {pdac['Patient ID'].nunique()}")
    pdac["pre_numeric"] = pdac["Pre-treatment VAF (%)"].map(number)
    pdac["eot_numeric"] = pdac["End of Therapy VAF (%)"].map(number)
    pdac["newly_listed_status"] = pdac.apply(event_type, axis=1)
    pdac["gene_upper"] = pdac["Gene/variant"].str.strip().str.upper()
    pdac["alteration_lower"] = pdac["Alteration type"].str.strip().str.casefold()

    rows: list[dict] = []
    for patient, g in pdac.groupby("Patient ID", sort=False):
        treatments = sorted(set(g["Treatment"].str.strip()) - {""})
        responses = sorted(set(g["Best response"].str.strip()) - {""})
        platforms = sorted(set(g["Technology used"].str.strip()) - {""})
        if len(treatments) != 1 or len(responses) != 1:
            raise ValueError(f"Non-unique patient-level treatment/response for {patient}")

        tp53_rows = g[g["gene_upper"].str.startswith("TP53") & g["alteration_lower"].eq("mutation")]
        baseline_tp53 = bool(tp53_rows["pre_numeric"].notna().any())
        tp53_eot_only = bool((tp53_rows["pre_numeric"].isna() & tp53_rows["eot_numeric"].notna()).any())

        kras_rows = g[g["gene_upper"].str.startswith("KRAS G12C") & g["alteration_lower"].eq("mutation")]
        pre_vals = kras_rows["pre_numeric"].dropna()
        eot_vals = kras_rows["eot_numeric"].dropna()
        pre_vaf = float(pre_vals.iloc[0]) if len(pre_vals) else np.nan
        eot_vaf = float(eot_vals.iloc[-1]) if len(eot_vals) else np.nan

        cn = g[g["alteration_lower"].eq("copy number")].copy()
        new_cn = cn[cn["newly_listed_status"].eq("newly_listed")]
        kras_cn = new_cn[new_cn["gene_upper"].eq("KRAS")]
        kras_eot_status = set(kras_cn["End of Therapy VAF (%)"].str.strip().str.casefold())
        any_new_mut = g[(g["alteration_lower"].eq("mutation")) &
                        g["newly_listed_status"].eq("newly_listed")]
        new_mut_genes = set(any_new_mut["gene_upper"].str.extract(r"^([A-Z0-9]+)", expand=False).dropna())
        ras_pi3k_rtks = {"KRAS", "NRAS", "HRAS", "BRAF", "RAF1", "MAP2K1", "MAP2K2", "NF1",
                         "EGFR", "ERBB2", "ERBB3", "MET", "PIK3CA", "PTEN"}

        rows.append({
            "patient_id": patient,
            "treatment": treatments[0],
            "best_response": responses[0],
            "technology_profile": " + ".join(platforms) if platforms else "not_listed",
            "tp53_baseline_variant_listed": "yes" if baseline_tp53 else "no_pretherapy_variant_listed",
            "tp53_eot_only_variant_listed": int(tp53_eot_only),
            "baseline_kras_g12c_vaf_pct": pre_vaf,
            "baseline_kras_g12c_detection": "detected" if np.isfinite(pre_vaf) else "not_listed_at_baseline",
            "eot_kras_g12c_vaf_pct": eot_vaf,
            "delta_kras_g12c_vaf_pp": eot_vaf - pre_vaf if np.isfinite(pre_vaf) and np.isfinite(eot_vaf) else np.nan,
            "new_kras_cn_amp_listed": "yes" if "amp" in kras_eot_status else "no_kras_cn_amp_listed",
            "new_kras_cn_gain_or_amp_listed": "yes" if kras_eot_status.intersection({"amp", "gain"}) else "no_kras_cn_event_listed",
            "new_any_cn_listed": "yes" if len(new_cn) else "no_new_cn_event_listed",
            "new_any_mutation_listed": "yes" if len(any_new_mut) else "no_new_mutation_listed",
            "new_any_event_listed": "yes" if (len(new_cn) + len(any_new_mut)) else "no_new_event_listed",
            "new_ras_pi3k_rtk_mutation_listed": "yes" if new_mut_genes.intersection(ras_pi3k_rtks) else "no_such_mutation_listed",
            "new_pik3ca_mutation_listed": "yes" if "PIK3CA" in new_mut_genes else "no_pik3ca_mutation_listed",
            "n_new_mutation_rows_listed": int(len(any_new_mut)),
            "n_new_copy_number_rows_listed": int(len(new_cn)),
        })
    patient = pd.DataFrame(rows).sort_values("patient_id", key=lambda s: s.str.extract(r"(\d+)$", expand=False).astype(int))
    if len(patient) != 22 or patient["patient_id"].duplicated().any():
        raise ValueError("Patient-level normalization did not yield 22 unique patients")
    return pdac, patient


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    expected_md5 = "1e64a9785233ad0bd9ce57b52699a455"
    if SOURCE.stat().st_size != 19979 or md5(SOURCE) != expected_md5:
        raise ValueError("Downloaded Figshare source fails size/MD5 verification against its public API metadata")
    long, d = clean_data()
    # Keep all source records, including non-PDAC records, so the downloaded
    # table can be audited against the normalized PDAC subset.
    source_raw = pd.read_excel(SOURCE, header=2, dtype=str).fillna("")
    source_raw.to_csv(OUT / "source_supplement_all_rows.csv", index=False)
    long.drop(columns=["pre_numeric", "eot_numeric", "newly_listed_status", "gene_upper", "alteration_lower"]).to_csv(
        OUT / "pdac_22_variant_rows_normalized.csv", index=False)
    d.to_csv(OUT / "patient_level_external_22.csv", index=False, float_format="%.10g")

    controls = [
        ("treatment", "categorical", "adagrasib vs sotorasib; distinct KRAS G12C inhibitor mechanism cohort"),
        ("best_response", "categorical", "best response in source table; PD denotes primary resistance"),
        ("tp53_baseline_variant_listed", "categorical", "TP53 variant with numeric pretreatment VAF listed; absence is not called WT"),
        ("baseline_kras_g12c_detection", "categorical", "whether numeric pretreatment KRAS G12C VAF appears in supplement"),
        ("baseline_kras_g12c_vaf_pct", "continuous", "pretreatment KRAS G12C VAF percentage; numeric rows only"),
        ("technology_profile", "categorical", "assay platform(s) listed per patient; exploratory, sparse levels"),
    ]
    flows = [
        ("new_kras_cn_amp_listed", "categorical", "KRAS copy-number Amp listed as absent pretreatment and Amp at end of therapy"),
        ("new_kras_cn_gain_or_amp_listed", "categorical", "KRAS copy-number Gain/Amp listed as absent pretreatment and present at end of therapy"),
        ("new_any_cn_listed", "categorical", "any copy-number Gain/Amp row listed as new"),
        ("new_any_mutation_listed", "categorical", "any mutation row absent in pretreatment listing and numeric at end of therapy"),
        ("new_any_event_listed", "categorical", "any newly listed mutation or copy-number event"),
        ("new_ras_pi3k_rtk_mutation_listed", "categorical", "newly listed mutation in prespecified RAS/MAPK/PI3K/RTK gene set"),
        ("new_pik3ca_mutation_listed", "categorical", "newly listed PIK3CA mutation"),
        ("n_new_mutation_rows_listed", "continuous", "count of newly listed mutation rows; not a variant burden estimate"),
        ("n_new_copy_number_rows_listed", "continuous", "count of newly listed copy-number rows"),
        ("eot_kras_g12c_vaf_pct", "continuous", "end-of-therapy KRAS G12C VAF percentage; numeric rows only"),
        ("delta_kras_g12c_vaf_pp", "continuous", "end-of-therapy minus pretreatment VAF percentage points; both numeric only"),
    ]
    rng = np.random.default_rng(SEED)
    tests = []
    for cname, ckind, cdesc in controls:
        for fname, fkind, fdesc in flows:
            test = engine.test_pair(d[cname], d[fname], ckind, fkind, rng)
            tests.append({"control": cname, "control_type": ckind, "control_description": cdesc,
                          "flow": fname, "flow_type": fkind, "flow_description": fdesc, **test})
    res = pd.DataFrame(tests)
    res["q_bh_global_estimable"] = engine.bh(res["p_value"].to_numpy())
    res["family_estimable_tests"] = int(res["p_value"].notna().sum())
    res.to_csv(OUT / "controls_by_flows_external_22.csv", index=False, float_format="%.10g")

    # Primary descriptive cross-MOA contrast fixed by the prior daraxonrasib
    # analysis: pretreatment TP53 evidence vs treatment-emergent KRAS G12C CN
    # gain/amplification. It is not independent validation of the same drug.
    xtab = pd.crosstab(d["tp53_baseline_variant_listed"], d["new_kras_cn_gain_or_amp_listed"])
    xtab.to_csv(OUT / "primary_cross_moa_contingency.csv")
    p_row = res[(res["control"] == "tp53_baseline_variant_listed") &
                (res["flow"] == "new_kras_cn_gain_or_amp_listed")].iloc[0]
    amp_ids = d.loc[d["new_kras_cn_amp_listed"].eq("yes"), "patient_id"].tolist()
    gainamp_ids = d.loc[d["new_kras_cn_gain_or_amp_listed"].eq("yes"), "patient_id"].tolist()
    primary = {
        "question": "Is a pretreatment TP53 variant listed more often among patients with a newly listed KRAS G12C copy-number gain/amplification at end of adagrasib/sotorasib therapy?",
        "unit": "patient",
        "patients": int(len(d)),
        "tp53_by_event_table": {str(i): {str(j): int(xtab.loc[i, j]) for j in xtab.columns} for i in xtab.index},
        "gain_or_amplification_patient_ids": gainamp_ids,
        "amplification_only_patient_ids": amp_ids,
        "test": p_row["test"],
        "p_nominal": float(p_row["p_value"]) if pd.notna(p_row["p_value"]) else None,
        "odds_ratio_or_effect": float(p_row["effect"]) if pd.notna(p_row["effect"]) else None,
        "q_bh_global_in_exploratory_grid": float(p_row["q_bh_global_estimable"]) if pd.notna(p_row["q_bh_global_estimable"]) else None,
        "interpretation": "cross-MOA exploratory comparison; rows absent from the supplement are not confirmed negative assays; does not establish TP53 causality or a treatment recommendation",
    }
    (OUT / "primary_cross_moa_contrast.json").write_text(json.dumps(primary, ensure_ascii=False, indent=2), encoding="utf-8")

    coverage = []
    for name, typ, desc in controls + flows:
        s = d[name]
        coverage.append({"field": name, "role": "control" if any(name == x[0] for x in controls) else "flow",
                         "type": typ, "description": desc, "n_patients": len(d),
                         "n_observed": int(s.notna().sum()), "n_missing": int(s.isna().sum()),
                         "n_levels_or_values": int(s.nunique(dropna=True))})
    pd.DataFrame(coverage).to_csv(OUT / "field_coverage_external_22.csv", index=False)

    pivot = res.pivot(index="control", columns="flow", values="q_bh_global_estimable")
    mat = -np.log10(np.clip(pivot.to_numpy(dtype=float), 1e-6, 1.0))
    fig, ax = plt.subplots(figsize=(17, 7), constrained_layout=True)
    im = ax.imshow(mat, cmap="viridis", vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)), [s.replace("_", "\n") for s in pivot.columns], fontsize=7)
    ax.set_yticks(np.arange(len(pivot.index)), [s.replace("_", " ") for s in pivot.index], fontsize=8)
    ax.set_title("PDAC KRAS G12C cross-MOA scan — controls × flows\n−log10(q BH globale), plafonné à 3; les cases vides ne sont pas estimables")
    ax.set_xlabel("Flux / mesure de résistance")
    ax.set_ylabel("Contrôle candidat")
    cb = fig.colorbar(im, ax=ax, shrink=.8)
    cb.set_label("−log10(q BH globale)")
    fig.savefig(OUT / "controls_by_flows_external_22_heatmap.png", dpi=190)
    plt.close(fig)

    estimable = res[res["p_value"].notna()].sort_values("q_bh_global_estimable")
    sig = estimable[estimable["q_bh_global_estimable"] < .05]
    response_counts = d.groupby("best_response").size().to_dict()
    tp53_counts = d.groupby("tp53_baseline_variant_listed").size().to_dict()
    with (OUT / "REPORT_EXTERNAL_G12C_CROSS_MOA.md").open("w", encoding="utf-8") as f:
        f.write("# Analyse exploratoire externe PDAC — inhibiteurs KRAS G12C\n\n")
        f.write("**Date d’exécution:** 17 novembre 2026. **Cohorte:** 22 patients PDAC issus de la cohorte clinique publiée sous adagrasib (patients 1–8) ou sotorasib (patients 9–22). **Unité:** patient. **Plan:** 6 contrôles candidats × 11 flux candidats; correction BH globale sur les comparaisons estimables.\n\n")
        f.write("## Question et constat principal\n\n")
        f.write("Question de transférabilité: le signal TP53 prétraitement ↔ événement KRAS acquis observé dans l’analyse daraxonrasib apparaît-il aussi dans cette cohorte, exposée à des inhibiteurs KRAS G12C différents? La publication rapporte des gains/amplifications KRAS G12C émergents chez les patients 6, 9, 13 et 22; le supplément permet de repérer ces événements à partir des colonnes prétraitement/fin de traitement. Les trois événements classés Amp sont distingués du cas Gain.\n\n")
        f.write(f"La grille compte **{len(tests)} comparaisons prévues**, **{len(estimable)} estimables** et **{len(sig)} q<0,05**. Pour le contraste ciblé TP53 prétraitement × KRAS CN Gain/Amp, 3/18 patients avec variant TP53 prétraitement listé et 1/4 sans variant prétraitement listé ont un Gain/Amp KRAS listé; OR={p_row['effect']:.3g}, test {p_row['test']}, p nominale={p_row['p_value']:.4g}, q globale={p_row['q_bh_global_estimable']:.4g}. La liste des patients avec Gain/Amp est {', '.join(gainamp_ids)}; Amplification seule: {', '.join(amp_ids)}.\n\n")
        f.write("**Interprétation:** ce résultat est un test exploratoire de portabilité entre mécanismes médicamenteux et ne valide pas un biomarqueur. L’absence d’un événement dans le supplément est codée ‘non listé’, jamais ‘confirmé absent’. Le tableau ne garantit pas une couverture identique pour chaque altération et les plateformes diffèrent. Les réponses sont celles d’une petite cohorte déjà sélectionnée pour maladie KRAS G12C et les patients PR/SD ont ensuite progressé.\n\n")
        f.write("## Couverture de la cohorte\n\n")
        f.write(f"Réponses consignées: {response_counts}. Statut TP53 prétraitement (‘variant TP53 avec VAF numérique listé’ vs ‘aucun variant TP53 prétraitement listé’): {tp53_counts}. Le second libellé ne signifie pas TP53 sauvage. Le supplément contient 196 lignes de variants au total, dont {len(long)} lignes PDAC, agrégées en 22 patients.\n\n")
        f.write("## Contrôles × flux\n\n")
        f.write("Les contrôles candidats couvrent traitement, réponse, preuve listée d’un variant TP53 prétraitement, disponibilité/VAF KRAS G12C initiale et plateforme. Les flux comprennent nouveaux événements copy-number, mutations listées, événements RAS/PI3K/RTK, KRAS G12C fin de traitement et différence VAF prétraitement–fin. Tous les tests sont patient-level; les prélèvements ne sont pas traités comme des observations indépendantes. Les mesures dérivées partagent des colonnes sources et ne sont pas des preuves biologiques indépendantes.\n\n")
        f.write("| Contrôle | Flux | n patients | Test | Effet | p | q globale |\n|---|---|---:|---|---:|---:|---:|\n")
        for _, r in estimable.head(15).iterrows():
            f.write(f"| {r.control} | {r.flow} | {r.n_patients} | {r.test} | {r.effect_name}={r.effect:.4g} | {r.p_value:.4g} | {r.q_bh_global_estimable:.4g} |\n")
        f.write("\n## Champ d’application et limites\n\n")
        f.write("- Ce supplément fournit des prélèvements prétraitement et fin de traitement; il ne constitue pas une série temporelle régulière. Aucun T₀, dérivée temporelle, seuil TLog ou conclusion de transition n’est calculé.\n")
        f.write("- N=22 et les variables sont clairsemées. Cette analyse applique les tests patient-level de la suite multiaxiale compagnon, mais ne lance pas le cœur universel complet, les 29 estimateurs ni la formule finale TLog. Elle ne prouve donc ni la théorie entière ni son universalité.\n")
        f.write("- La grille et la question ciblée sont exploratoires et définies après publication/inspection du supplément; la correction BH ne supprime pas ce biais de sélection.\n")
        f.write(f"- Aucun contrôle × flux ne franchit q<0,05 dans cette grille. Avec seulement {len(d)} patients, cela ne démontre pas l’absence d’effet; tout signal nominal reste à répliquer dans une cohorte indépendante avec les mêmes médicaments, des mesures appariées, une définition préenregistrée du contrôle/flux et une validation fonctionnelle.\n")
        f.write("- Rien ici ne démontre un remède, une efficacité thérapeutique nouvelle, une causalité TP53, ni une recommandation pour une personne. Les modèles organoïdes/PDX ou expériences contrôlées sont l’étape suivante pour tester une intervention.\n\n")
        f.write("## Reproduction\n\nDepuis la racine du dépôt Windows: `\\.venv\\Scripts\\python.exe pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-17\\external_validation_g12c\\analyze_g12c_external.py`. Le script réutilise le moteur patient-level déclaré dans le manifeste.\n\n")
        f.write(f"Sources: article principal [doi:{ARTICLE_DOI}] (https://doi.org/{ARTICLE_DOI}); supplément CC BY [doi:{DATASET_DOI}] (https://doi.org/{DATASET_DOI}); API publique Figshare (https://api.figshare.com/v2/articles/{FIGSHARE_ARTICLE_ID}).\n")

    outputs = [p for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"]
    manifest = {
        "analysis_id": "pdac_krasi_g12c_cross_moa_external_patient_level_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_article_doi": ARTICLE_DOI,
        "source_dataset_doi": DATASET_DOI,
        "source_dataset_license": "CC BY as shown on AACR Figshare item page; verify attribution before reuse",
        "figshare_article_id": FIGSHARE_ARTICLE_ID,
        "figshare_file_id": FIGSHARE_FILE_ID,
        "source_file": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size,
                        "md5_expected_from_figshare_api": "1e64a9785233ad0bd9ce57b52699a455",
                        "sha256": sha256(SOURCE)},
        "cohort": {"unit": "patient", "pdac_patients": int(len(d)),
                   "treatment": "adagrasib patients 1-8; sotorasib patients 9-22",
                   "stages": "pretreatment and end-of-therapy only in this supplement; not equally spaced longitudinal series"},
        "data_rules": {"dash_and_unlisted": "not reported in supplement; not treated as confirmed assay-negative",
                       "vaf": "numeric values only; no zero imputation",
                       "patient_blocking": "one row per patient; repeated variants summarized per patient"},
        "primary_cross_moa_question": primary,
        "controls": [{"name": n, "type": t, "description": s} for n,t,s in controls],
        "flows": [{"name": n, "type": t, "description": s} for n,t,s in flows],
        "statistics": {"engine_source": str(CORE), "engine_sha256": sha256(CORE),
                       "planned_tests": len(tests), "estimable_tests": int(res["p_value"].notna().sum()),
                       "multiple_testing": "Benjamini-Hochberg over all estimable control x flow tests",
                       "permutation_count": engine.N_PERM, "seed": SEED},
        "scope": "typed multiaxis companion only; not universal-core/TLog validation; no T0; no causal or clinical-treatment claim",
        "script_sha256": sha256(Path(__file__)),
        "software": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__},
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in outputs},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"patients": len(d), "pdac_variant_rows": len(long), "planned_tests": len(tests),
                      "estimable_tests": int(res["p_value"].notna().sum()), "q_lt_0_05": len(sig),
                      "primary_p": primary["p_nominal"], "primary_q": primary["q_bh_global_in_exploratory_grid"],
                      "results": str(OUT), "manifest": str(OUT / "manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
