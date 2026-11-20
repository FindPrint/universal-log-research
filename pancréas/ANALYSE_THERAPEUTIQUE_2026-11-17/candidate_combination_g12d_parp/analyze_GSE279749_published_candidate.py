#!/usr/bin/env python3
"""Exploratory reproduction of the published KRAS-G12D/HR expression signal.

This analysis uses GEO GSE279749 processed FPKM matrices. It tests only the
paper-named HR genes BRCA1, RAD51, and RPA2. It is a same-study computational
reproduction, not independent validation or a therapeutic efficacy test.
"""
from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE / "source"
OUT = HERE / "results"
CELL_FILE = SOURCE_DIR / "GSE279749_gene_fpkm_cell_lines.txt.gz"
PDX_FILE = SOURCE_DIR / "GSE279749_gene_fpkm_PDX.txt.gz"
SOFT_FILE = SOURCE_DIR / "GSE279749_family.soft.gz"
GENES = ["BRCA1", "RAD51", "RPA2"]  # explicitly reported in the source article
SEED = 20261117


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cohen_d(treated: np.ndarray, control: np.ndarray) -> float:
    """Equal-variance Cohen's d, matching the pipeline's primary effect metric."""
    a = np.asarray(treated, dtype=float)
    b = np.asarray(control, dtype=float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    var = ((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1)) / (len(a) + len(b) - 2)
    return float((np.mean(a) - np.mean(b)) / math.sqrt(var)) if var > 0 else float("nan")


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def bh(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    ok = np.flatnonzero(np.isfinite(p))
    if len(ok):
        order = ok[np.argsort(p[ok])]
        adj = p[order] * len(order) / np.arange(1, len(order) + 1)
        q[order] = np.minimum.accumulate(adj[::-1])[::-1].clip(max=1)
    return q


def exact_blocked_permutation(frame: pd.DataFrame, gene: str) -> tuple[float, float, int]:
    """Exact label swaps within each provisionally mapped G12D line.

    The calculation assumes the three GEO columns per arm are exchangeable;
    biological replicate independence is not confirmed by the source records.
    """
    choices = []
    observed = 0.0
    for model, g in frame.groupby("model", sort=True):
        t = g.loc[g["treatment"].eq("MRTX1133"), gene].to_numpy(float)
        c = g.loc[g["treatment"].eq("vehicle"), gene].to_numpy(float)
        if len(t) != 3 or len(c) != 3:
            raise ValueError(f"Expected 3 cultures per treatment/model; {model}: {len(t)} vs {len(c)}")
        observed += float(np.mean(t) - np.mean(c)) / 3.0
        values = np.concatenate([t, c])
        choices.append([(ix, values[list(ix)].mean() - values[[j for j in range(6) if j not in ix]].mean())
                        for ix in itertools.combinations(range(6), 3)])
    stats = np.fromiter((sum(x[1] for x in combo) / 3.0 for combo in itertools.product(*choices)), float)
    p = float(np.mean(np.abs(stats) >= abs(observed) - 1e-12))
    return observed, p, int(len(stats))


def exact_two_group(frame: pd.DataFrame, gene: str, treatment: str) -> tuple[float, float, int]:
    t = frame.loc[frame["treatment"].eq(treatment), gene].to_numpy(float)
    c = frame.loc[frame["treatment"].eq("vehicle"), gene].to_numpy(float)
    if len(t) != 3 or len(c) != 3:
        raise ValueError(f"Expected three samples per group: {treatment}={len(t)}, vehicle={len(c)}")
    obs = float(np.mean(t) - np.mean(c))
    vals = np.concatenate([t, c])
    stats = np.fromiter((vals[list(ix)].mean() - vals[[j for j in range(6) if j not in ix]].mean()
                         for ix in itertools.combinations(range(6), 3)), float)
    return obs, float(np.mean(np.abs(stats) >= abs(obs) - 1e-12)), len(stats)


def parse_soft() -> pd.DataFrame:
    rows = []
    text = gzip.open(SOFT_FILE, "rt", encoding="utf-8", errors="replace").read()
    for block in text.split("^SAMPLE = ")[1:]:
        lines = block.splitlines()
        gsm = lines[0].strip()
        fields = {"sample_id": gsm}
        for line in lines:
            if line.startswith("!Sample_title = "):
                fields["title"] = line.split("=", 1)[1].strip()
            if line.startswith("!Sample_source_name_ch1 = "):
                fields["model"] = line.split("=", 1)[1].strip()
            if line.startswith("!Sample_characteristics_ch1 = "):
                key, _, value = line.split("=", 1)[1].strip().partition(":")
                fields[key.strip().casefold().replace(" ", "_")] = value.strip()
        fields["replicate"] = int(re.search(r"_(\d+)\s*$", fields.get("title", "")).group(1))
        rows.append(fields)
    meta = pd.DataFrame(rows)
    return meta


def get_cell_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    mat = pd.read_csv(CELL_FILE, sep="\t", compression="gzip")
    if "gene_name" not in mat:
        raise ValueError("Cell-line matrix lacks gene_name")
    cells = mat[mat["gene_name"].isin(GENES)].copy()
    if cells["gene_name"].duplicated().any():
        # Ensembl versions can occasionally map multiple rows to one symbol.
        # Use the row with the largest mean FPKM across sample columns and log it.
        sample_cols = [c for c in mat.columns if re.match(r"^(A|P|C|S9)_(NT|M)_\d+$", c)]
        cells = (cells.assign(_mean=cells[sample_cols].mean(axis=1))
                 .sort_values("_mean", ascending=False).drop_duplicates("gene_name"))
    sample_cols = [c for c in mat.columns if re.match(r"^(A|P|C|S9)_(NT|M)_\d+$", c)]
    wide = cells.set_index("gene_name")[sample_cols].T
    wide.index.name = "sample_column"
    wide = np.log2(wide.astype(float) + 1.0)
    wide = wide.reset_index()
    prefix_model = {"A": "AsPC-1", "P": "PANC-1", "S9": "SW1990", "C": "CFPAC-1"}
    wide["prefix"] = wide["sample_column"].str.extract(r"^([A-Z0-9]+)_", expand=False)
    wide["model"] = wide["prefix"].map(prefix_model)
    wide["replicate"] = wide["sample_column"].str.extract(r"_(\d+)$", expand=False).astype(int)
    wide["treatment"] = np.where(wide["sample_column"].str.contains("_NT_"), "vehicle",
                                  np.where(wide["model"].eq("CFPAC-1"), "BI-2865", "MRTX1133"))
    wide["genotype"] = np.where(wide["model"].eq("CFPAC-1"), "KRAS G12V", "KRAS G12D")
    wide["stage_hours"] = 24
    return mat, wide


def get_pdx_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    mat = pd.read_csv(PDX_FILE, sep="\t", compression="gzip")
    subset = mat[mat["gene_name"].isin(GENES)].copy()
    if subset["gene_name"].duplicated().any():
        subset["_mean"] = subset[[f"p{i}" for i in range(1, 7)]].mean(axis=1)
        subset = subset.sort_values("_mean", ascending=False).drop_duplicates("gene_name")
    wide = subset.set_index("gene_name")[[f"p{i}" for i in range(1, 7)]].T
    wide.index.name = "pdx_column"
    wide = np.log2(wide.astype(float) + 1.0).reset_index()
    wide["replicate"] = wide["pdx_column"].str.extract(r"p(\d+)$", expand=False).astype(int)
    wide["treatment"] = np.where(wide["replicate"] <= 3, "vehicle", "MRTX1133+Olaparib")
    wide["genotype"] = "KRAS G12D"
    return mat, wide


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    md = parse_soft()
    md.to_csv(OUT / "GSE279749_sample_metadata.csv", index=False)
    mapping_assumptions = pd.DataFrame([
        {"matrix": "cell_lines", "matrix_label": "A", "interpreted_as": "AsPC-1", "basis": "prefix abbreviation; no explicit crosswalk column in matrix", "certainty": "provisional"},
        {"matrix": "cell_lines", "matrix_label": "P", "interpreted_as": "PANC-1", "basis": "prefix abbreviation; no explicit crosswalk column in matrix", "certainty": "provisional"},
        {"matrix": "cell_lines", "matrix_label": "C", "interpreted_as": "CFPAC-1", "basis": "prefix abbreviation; no explicit crosswalk column in matrix", "certainty": "provisional"},
        {"matrix": "cell_lines", "matrix_label": "S9", "interpreted_as": "SW1990", "basis": "prefix abbreviation; no explicit crosswalk column in matrix", "certainty": "provisional"},
        {"matrix": "cell_lines", "matrix_label": "NT/M", "interpreted_as": "vehicle/compound", "basis": "treatment suffix interpreted against GEO sample records", "certainty": "provisional"},
        {"matrix": "PDX", "matrix_label": "p1-p3 / p4-p6", "interpreted_as": "vehicle / MRTX1133+Olaparib", "basis": "positional mapping to ordered GEO sample records; no direct GSM-to-column crosswalk", "certainty": "provisional"},
    ])
    mapping_assumptions.to_csv(OUT / "GSE279749_mapping_assumptions.csv", index=False)
    _, cells = get_cell_data()
    _, pdx = get_pdx_data()
    cells.to_csv(OUT / "cell_line_HR_expression_log2FPKM.csv", index=False, float_format="%.8g")
    pdx.to_csv(OUT / "PDX_HR_expression_log2FPKM.csv", index=False, float_format="%.8g")

    g12d = cells[cells["genotype"].eq("KRAS G12D")].copy()
    g12v = cells[cells["genotype"].eq("KRAS G12V")].copy()
    rows = []
    for gene in GENES:
        if gene in g12d.columns:
            diff, p, nperm = exact_blocked_permutation(g12d, gene)
            ds = {model: cohen_d(g.loc[g.treatment.eq("MRTX1133"), gene].to_numpy(),
                                 g.loc[g.treatment.eq("vehicle"), gene].to_numpy())
                  for model, g in g12d.groupby("model")}
            tvals = g12d.loc[g12d.treatment.eq("MRTX1133"), gene].to_numpy(float)
            cvals = g12d.loc[g12d.treatment.eq("vehicle"), gene].to_numpy(float)
            rows.append({"control": "MRTX1133 vs vehicle, blocked by cell line; G12D only", "flow": gene,
                         "n_treated": len(tvals), "n_control": len(cvals), "treatment_minus_control_mean_log2FPKM": diff,
                         "Cohens_d_pooled": cohen_d(tvals, cvals), "Cohens_d_by_model": json.dumps(ds),
                         "p_exact_blocked": p, "permutations": nperm, "status": "estimable",
                         "family": "paper-named HR gene; available GEO flows only"})
        else:
            rows.append({"control": "MRTX1133 vs vehicle, blocked by cell line; G12D only", "flow": gene,
                         "n_treated": 0, "n_control": 0, "treatment_minus_control_mean_log2FPKM": np.nan,
                         "Cohens_d_pooled": np.nan, "Cohens_d_by_model": "", "p_exact_blocked": np.nan,
                         "permutations": 0, "status": "not_available_in_cell_line_GEO_matrix; not zero-imputed",
                         "family": "paper-named HR gene"})
        if gene in pdx.columns:
            diff_pdx, p_pdx, nperm_pdx = exact_two_group(pdx, gene, "MRTX1133+Olaparib")
            a = pdx.loc[pdx.treatment.eq("MRTX1133+Olaparib"), gene].to_numpy(float)
            b = pdx.loc[pdx.treatment.eq("vehicle"), gene].to_numpy(float)
            rows.append({"control": "PDX combo vs vehicle; no single-agent RNA-seq arm", "flow": gene,
                         "n_treated": len(a), "n_control": len(b), "treatment_minus_control_mean_log2FPKM": diff_pdx,
                         "Cohens_d_pooled": cohen_d(a, b), "Cohens_d_by_model": "not reported; PDX IDs not mapped in matrix",
                         "p_exact_blocked": p_pdx, "permutations": nperm_pdx, "status": "estimable",
                         "family": "paper-named HR gene; exploratory PDX endpoint"})
        else:
            rows.append({"control": "PDX combo vs vehicle; no single-agent RNA-seq arm", "flow": gene,
                         "n_treated": 0, "n_control": 0, "treatment_minus_control_mean_log2FPKM": np.nan,
                         "Cohens_d_pooled": np.nan, "Cohens_d_by_model": "", "p_exact_blocked": np.nan,
                         "permutations": 0, "status": "not_available_in_PDX_GEO_matrix; not zero-imputed",
                         "family": "paper-named HR gene"})
        if gene in g12v.columns:
            diff_v, p_v, nperm_v = exact_two_group(g12v, gene, "BI-2865")
            a = g12v.loc[g12v.treatment.eq("BI-2865"), gene].to_numpy(float)
            b = g12v.loc[g12v.treatment.eq("vehicle"), gene].to_numpy(float)
            rows.append({"control": "BI-2865 vs vehicle in single G12V line; separate exploratory stratum", "flow": gene,
                         "n_treated": len(a), "n_control": len(b), "treatment_minus_control_mean_log2FPKM": diff_v,
                         "Cohens_d_pooled": cohen_d(a, b), "Cohens_d_by_model": json.dumps({"CFPAC-1": cohen_d(a, b)}),
                         "p_exact_blocked": p_v, "permutations": nperm_v, "status": "estimable",
                         "family": "not comparable to G12D/MRTX1133 arm"})
        else:
            rows.append({"control": "BI-2865 vs vehicle in single G12V line; separate exploratory stratum", "flow": gene,
                         "n_treated": 0, "n_control": 0, "treatment_minus_control_mean_log2FPKM": np.nan,
                         "Cohens_d_pooled": np.nan, "Cohens_d_by_model": "", "p_exact_blocked": np.nan,
                         "permutations": 0, "status": "not_available_in_cell_line_GEO_matrix; not zero-imputed",
                         "family": "not comparable to G12D/MRTX1133 arm"})
    res = pd.DataFrame(rows)
    res["q_bh_over_estimable_of_9_planned"] = bh(res["p_exact_blocked"].to_numpy())
    res.to_csv(OUT / "controls_by_flows_HR_candidate.csv", index=False, float_format="%.10g")

    # Plot biological replicates, preserving each group and not pooling cell lines.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    x = np.arange(len(GENES))
    for model, g in g12d.groupby("model", sort=True):
        prefix = str(g["prefix"].iloc[0])
        means_t = [g.loc[g.treatment.eq("MRTX1133"), gene].mean() if gene in g.columns else np.nan for gene in GENES]
        means_c = [g.loc[g.treatment.eq("vehicle"), gene].mean() if gene in g.columns else np.nan for gene in GENES]
        axes[0].plot(x, np.array(means_t) - np.array(means_c), marker="o",
                     label=f"{prefix}→{model} (provisoire)")
    axes[0].axhline(0, color="black", lw=.8)
    axes[0].set_xticks(x, GENES)
    axes[0].set_ylabel("Δ mean log₂(FPKM + 1), MRTX1133 − véhicule")
    axes[0].set_title("Mapping préfixe→lignée provisoire; 3 colonnes GEO/bras")
    axes[0].legend(frameon=False, fontsize=8)
    for treatment, g in pdx.groupby("treatment", sort=True):
        means = [g[gene].mean() for gene in GENES]
        axes[1].plot(x, means, marker="o", label=treatment)
    axes[1].set_xticks(x, GENES)
    axes[1].set_ylabel("Mean log₂(FPKM + 1)")
    axes[1].set_title("PDX point final; mapping des colonnes présumé")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Reproduction exploratoire d’un signal HR publié — pas une découverte thérapeutique")
    fig.savefig(OUT / "HR_gene_effects_GSE279749.png", dpi=190)
    plt.close(fig)

    g12d_summary = res[res["control"].str.startswith("MRTX1133")].copy()
    g12d_available = g12d_summary[g12d_summary["status"].eq("estimable")]
    n_down = int((g12d_available["treatment_minus_control_mean_log2FPKM"] < 0).sum())
    pds = pdx.groupby("treatment")[GENES].mean()
    pdx_delta = (pds.loc["MRTX1133+Olaparib"] - pds.loc["vehicle"]).to_dict()
    with (OUT / "REPORT_GSE279749_HR_candidate.md").open("w", encoding="utf-8") as f:
        f.write("# Réexamen exploratoire d’une piste publiée KRAS G12D + PARP\n\n")
        f.write("**Date:** 17 novembre 2026. **Données:** GEO GSE279749, matrices FPKM publiées dans la même étude qui propose la combinaison; ce n’est donc pas une validation indépendante. **Axes biologiques:** trois gènes HR explicitement nommés par l’article (BRCA1, RAD51, RPA2). **Mesure:** log2(FPKM+1), Cohen d et permutation exacte. Cohen d n’est pas une p-value. Les permutations supposent des colonnes d’échantillons indépendantes et échangeables; cette hypothèse n’est pas confirmée par les fichiers.\n\n")
        f.write("## Résultat réexaminé\n\n")
        rpa = g12d_summary[g12d_summary["flow"].eq("RPA2")].iloc[0]
        rpa_ds = json.loads(rpa["Cohens_d_by_model"])
        f.write(f"Sous le mapping provisoire des préfixes (A=AsPC-1, P=PANC-1, S9=SW1990), la matrice cellule contient seulement {len(g12d_available)}/3 marqueurs préspécifiés: {', '.join(g12d_available['flow']) if len(g12d_available) else 'aucun'}. Parmi les marqueurs disponibles, l’effet MRTX1133−véhicule est négatif pour {n_down}/{len(g12d_available)}. Pour RPA2, Δ moyen groupé={float(rpa['treatment_minus_control_mean_log2FPKM']):.3f} log2(FPKM+1), Cohen d={float(rpa['Cohens_d_pooled']):.3f}, permutation bloquée p={float(rpa['p_exact_blocked']):.3f}, q={float(rpa['q_bh_over_estimable_of_9_planned']):.3f}; Cohen d par groupe de préfixe: " + ", ".join(f"{k} {v:.2f}" for k,v in rpa_ds.items()) + ". Le sens n’est pas cohérent: les groupes A et P baissent, S9 augmente. BRCA1 et RAD51 sont absents du fichier GEO traité; ils restent non disponibles et ne sont jamais remplacés par 0. Cette analyse est conditionnelle au crosswalk de préfixes et ne constitue ni une réplication indépendante ni une preuve de sensibilité au PARP dans des patients.\n\n")
        f.write("Dans les six colonnes PDX, le mapping condition p1-p3=véhicule et p4-p6=combinaison est lui aussi déduit de leur ordre par rapport aux six enregistrements GEO; aucun identifiant GSM n’est directement attaché à ces noms de colonne. Sous ce mapping provisoire, les groupes ne comprennent que véhicule et combinaison, sans bras MRTX1133 seul ou olaparib seul. Différences de moyenne log2(FPKM+1), combo−véhicule: " + ", ".join(f"{g}={v:.3f}" for g,v in pdx_delta.items()) + ". On ne peut pas estimer l’interaction/synergie à partir de ces seuls échantillons RNA-seq, ni bloquer par PDX individuel faute d’identifiant mappé. Les analyses de croissance tumorale de l’article sont des résultats publiés séparés, pas notre résultat pipeline.\n\n")
        f.write("## Contrôles, flux et limites\n\n")
        f.write("Le scan croise trois contrôles expérimentaux (MRTX1133 dans les groupes présumés G12D; BI-2865 dans le groupe présumé CFPAC-1/G12V comme stratum séparé; combinaison dans le PDX) avec les trois flux HR. Les préfixes A/P/C/S9 et l’affectation p1-p6 sont des hypothèses de correspondance, exportées dans `GSE279749_mapping_assumptions.csv`; il faut une confirmation de l’auteur ou un crosswalk brut avant un résultat confirmatoire. La fiche GEO donne trois colonnes par condition, tandis que les Méthodes de l’article décrivent les cellules comme cultivées en double; cette discordance rend les p-values conditionnelles et empêche de considérer les trois colonnes comme trois réplications biologiques confirmées. Le bras G12V n’est pas une comparaison génotype-valide, car médicament et modèle changent aussi. Aucun axe temporel régulier n’est fourni; aucun T0/TLog ou dérivée temporelle n’est calculé.\n\n")
        f.write("Cette reproduction utilise les matrices FPKM de l’étude d’origine et une sélection de 3 flux définie par l’article. Elle ne lance pas les 29 estimateurs de complexité, le pipeline complet ou son TLog; elle teste uniquement les effets entre groupes avec Cohen d et permutations exactes conditionnelles au mapping et à l’indépendance. Elle ne démontre pas un remède, une efficacité clinique ou une nouvelle combinaison.\n\n")
        f.write("**Étape suivante recommandée:** examiner GSE309596, dont les métadonnées GEO listent 12 échantillons répartis en quatre bras (véhicule, MRTX1133, olaparib, combinaison), trois par bras. Avant le pseudobulk, vérifier la correspondance échantillon-animal et l’unité biologique dans les métadonnées et l’article; les cellules ne sont jamais des réplicats indépendants. Si les quatre affectations et unités sont confirmées, un contraste factoriel 2×2 au point final pourra estimer une interaction, avec n faible. Ce jeu ponctuel ne permet pas TLog. Ensuite seulement, concevoir un suivi longitudinal organoïde/PDX avec temps, mesures et témoins préspécifiés.\n\n")
        f.write("Source des matrices: GEO [GSE279749](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279749). Étude: Xu et al., Nature Communications 2026, DOI 10.1038/s41467-026-69695-4; correction d’auteur du 22 avril 2026, DOI 10.1038/s41467-026-72371-2 (correction d’une image DAPI du panneau 1c). Les métadonnées GEO listent trois échantillons par condition cellulaire, tandis que les Méthodes parlent de cultures en double; cette discordance doit être résolue. La matrice PDX ne fournit pas d’identifiant de modèle directement lié à p1-p6.\n")

    outputs = [p for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"]
    manifest = {
        "analysis_id": "pdac_g12d_parp_published_candidate_expression_recheck_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_series": "GSE279749",
        "source_page": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279749",
        "source_article_doi": "10.1038/s41467-026-69695-4",
        "author_correction_doi": "10.1038/s41467-026-72371-2",
        "inputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p), "md5": md5(p)} for p in [SOFT_FILE, CELL_FILE, PDX_FILE]},
        "unit_of_analysis": "GEO expression-matrix columns; biological independence is unverified; exact tests condition on exchangeability",
        "mapping_assumptions": {"cell_prefix_crosswalk": "A=AsPC-1, P=PANC-1, C=CFPAC-1, S9=SW1990, inferred from abbreviations; no explicit matrix crosswalk",
                                "treatment_suffix": "NT=vehicle; M=the applicable inhibitor, interpreted against GEO sample metadata",
                                "pdx_column_crosswalk": "p1-p3 vehicle and p4-p6 MRTX1133+Olaparib inferred by positional order of GEO sample records",
                                "confirmatory_status": "All effects and permutations are conditional until sample-to-column mapping and replicate independence are confirmed"},
        "replicate_design_discrepancy": "GEO provides three columns per condition; article Methods say cells were cultured in duplicate. Replicate independence/count requires clarification.",
        "primary_flows": GENES,
        "groups": {"G12D_cell_lines": "three provisional cell-line mappings, vehicle vs MRTX1133, 3 GEO columns per group per line, 24 h; biological replicate independence unverified",
                   "G12V_line": "provisional CFPAC-1 mapping; vehicle vs BI-2865, 3 GEO columns per group; separate exploratory stratum",
                   "PDX": "3 vehicle vs 3 MRTX1133+olaparib endpoint columns under provisional positional mapping; no single-agent arms in this expression matrix"},
        "statistics": {"effect": "Cohen d, equal-variance pooled SD, on log2(FPKM+1)",
                       "G12D_cell_lines": "exact permutations of 3/6 labels within each provisional cell-line mapping, 8000 combinations; conditional on independence",
                       "two_group_small_strata": "exact 3/6 label permutations, 20 combinations; minimum two-sided p may be 0.10",
                       "multiple_testing": "BH across estimable tests from 9 predeclared control x gene comparisons; unavailable markers remain unestimated",
                       "coverage": {"cell_lines": [g for g in GENES if g in cells.columns],
                                    "pdx": [g for g in GENES if g in pdx.columns],
                                    "unavailable_cell_line_markers": [g for g in GENES if g not in cells.columns]}},
        "scope": "does not run the universal 29-estimator core/TLog; expression reproduction only; no clinical/cure claim",
        "script_sha256": sha256(Path(__file__)),
        "software": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__},
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in outputs},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"cell_lines_n": len(cells), "pdx_n": len(pdx), "flows": GENES,
                      "g12d_primary": g12d_summary[["flow", "treatment_minus_control_mean_log2FPKM", "Cohens_d_pooled", "p_exact_blocked", "q_bh_over_estimable_of_9_planned"]].to_dict("records"),
                      "results": str(OUT), "manifest": str(OUT / "manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
