#!/usr/bin/env python3
"""Sample-level exploratory therapeutic scan of GSE309596 scRNA UMI counts.

Cells are summarized within each submitted GEO specimen before comparisons.
The four treatment arms are crossed with predeclared cell-population and
mechanism flows; cells are never used as independent inferential replicates.
Marker-positive states are deliberately described as marker-defined proxies,
not as a substitute for the authors' unavailable per-cell cluster labels.
"""
from __future__ import annotations

import csv
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
from scipy.io import mmread

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
DATA = SOURCE / "GSE309596_raw_counts"
OUT = HERE / "results_GSE309596_therapeutic_axes"
EXPECTED_CELLS_PAPER = 115_664
SEED = 20261117

# Candidate axes chosen before examining treatment effects. Identity markers
# produce overlapping fractions; pathway panels are exploratory expression
# scores. Mouse gene symbols are used as provided by GEO.
PANELS: dict[str, list[str]] = {
    "tumor_epithelial_identity": ["Epcam", "Krt8", "Krt18", "Krt19", "Krt7", "Sox9", "Muc1"],
    "T_cell_identity": ["Trac", "Cd3d", "Cd3e", "Cd247", "Lck"],
    "cytotoxic_T_NK": ["Nkg7", "Prf1", "Gzmb", "Ccl5", "Cd8a", "Cd8b1", "Ifng"],
    "Treg_identity": ["Foxp3", "Il2ra", "Ctla4", "Ikzf2"],
    "T_exhaustion": ["Pdcd1", "Lag3", "Tigit", "Havcr2", "Tox"],
    "monocyte_macrophage_identity": ["Lyz2", "Csf1r", "Adgre1", "C1qa", "C1qb", "C1qc", "Fcgr1"],
    "myeloid_suppressive_state": ["Arg1", "Mrc1", "Cd163", "Spp1", "Tgfb1", "Il10", "Lgals3"],
    "neutrophil_identity": ["Ly6g", "S100a8", "S100a9", "Mpo", "Elane", "Cxcr2"],
    "antigen_presentation_MHCII": ["H2-Aa", "H2-Ab1", "H2-Eb1", "Cd74", "Ciita"],
    "B_cell_identity": ["Cd79a", "Cd79b", "Ms4a1", "Cd19", "Cd37"],
    "CAF_stromal_identity": ["Col1a1", "Col1a2", "Col3a1", "Dcn", "Pdgfra", "Fap", "Acta2"],
    "endothelial_identity": ["Pecam1", "Vwf", "Kdr", "Emcn", "Cdh5"],
    "HR_DNA_repair": ["Brca1", "Brca2", "Rad51", "Rpa1", "Rpa2", "Palb2", "Atm", "Chek1", "Rad51c", "Mre11a"],
    "DNA_damage_apoptosis": ["Bbc3", "Pmaip1", "Bax", "Bcl2l11", "Casp3", "Casp8", "Fas", "Gadd45a", "Cdkn1a"],
    "type_I_interferon": ["Isg15", "Ifit1", "Ifit2", "Ifit3", "Ifi27l2a", "Mx1", "Oas1a", "Stat1"],
    "IFN_gamma_response": ["Ifng", "Stat1", "Irf1", "Cxcl9", "Cxcl10", "Gbp2", "Icam1"],
    "MAPK_ERK_output": ["Dusp4", "Dusp6", "Etv4", "Etv5", "Spry2", "Fos", "Egr1", "Dusp1"],
    "cell_cycle_proliferation": ["Mki67", "Top2a", "Pcna", "Mcm2", "Mcm5", "Ccnb1", "Cdk1", "Birc5"],
    "EMT_TGF_beta": ["Vim", "Zeb1", "Snai1", "Twist1", "Fn1", "Tgfb1", "Serpine1", "Cdh2"],
    "immune_checkpoint": ["Cd274", "Pdcd1", "Ctla4", "Tigit", "Lag3", "Havcr2", "Tox"],
    "T_cell_inflamed": ["Cd3d", "Cd3e", "Cd8a", "Nkg7", "Prf1", "Gzmb", "Ifng", "Cxcl9", "Cxcl10"],
}
IDENTITY_PANELS = {
    "tumor_epithelial_identity", "T_cell_identity", "cytotoxic_T_NK",
    "Treg_identity", "T_exhaustion", "monocyte_macrophage_identity",
    "neutrophil_identity", "antigen_presentation_MHCII", "B_cell_identity",
    "CAF_stromal_identity", "endothelial_identity",
}
STRATA = {
    "within_tumor_epithelial_marker_positive": "tumor_epithelial_identity",
    "within_T_cell_marker_positive": "T_cell_identity",
    "within_monocyte_macrophage_marker_positive": "monocyte_macrophage_identity",
}
STRATIFIED_FLOWS = {
    "within_tumor_epithelial_marker_positive": ["HR_DNA_repair", "DNA_damage_apoptosis", "MAPK_ERK_output", "cell_cycle_proliferation", "EMT_TGF_beta"],
    "within_T_cell_marker_positive": ["cytotoxic_T_NK", "Treg_identity", "T_exhaustion", "IFN_gamma_response", "immune_checkpoint"],
    "within_monocyte_macrophage_marker_positive": ["myeloid_suppressive_state", "antigen_presentation_MHCII", "type_I_interferon", "IFN_gamma_response"],
}
CONTROLS = ["MRTX1133 marginal", "Olaparib marginal", "MRTX1133 × Olaparib interaction", "Combination vs Vehicle"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def exact_assignments() -> np.ndarray:
    """All balanced allocations of 12 samples to four groups of three."""
    idx = np.arange(12, dtype=np.int8)
    rows = []
    for a in itertools.combinations(idx, 3):
        rem1 = [x for x in idx if x not in a]
        for b in itertools.combinations(rem1, 3):
            rem2 = [x for x in rem1 if x not in b]
            for c in itertools.combinations(rem2, 3):
                d = [x for x in rem2 if x not in c]
                rows.append((*a, *b, *c, *d))
    result = np.asarray(rows, dtype=np.int8).reshape(-1, 4, 3)
    if result.shape != (369600, 4, 3):
        raise AssertionError(result.shape)
    return result


def contrast_values(group_means: np.ndarray) -> dict[str, np.ndarray]:
    # Last axis is ordered vehicle, MRTX1133, olaparib, combination.
    return {
        "MRTX1133 marginal": ((group_means[..., 1] + group_means[..., 3]) -
                              (group_means[..., 0] + group_means[..., 2])) / 2,
        "Olaparib marginal": ((group_means[..., 2] + group_means[..., 3]) -
                              (group_means[..., 0] + group_means[..., 1])) / 2,
        "MRTX1133 × Olaparib interaction": (group_means[..., 3] - group_means[..., 1] -
                                             group_means[..., 2] + group_means[..., 0]),
        "Combination vs Vehicle": group_means[..., 3] - group_means[..., 0],
    }


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    var = ((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2)
    return float((a.mean()-b.mean())/math.sqrt(var)) if var > 0 else float("nan")


def bh(pvals: np.ndarray) -> np.ndarray:
    p = np.asarray(pvals, float)
    q = np.full(p.shape, np.nan)
    keep = np.flatnonzero(np.isfinite(p))
    if len(keep):
        order = keep[np.argsort(p[keep])]
        adj = p[order] * len(order) / np.arange(1, len(order)+1)
        q[order] = np.minimum.accumulate(adj[::-1])[::-1].clip(max=1)
    return q


def load_metadata() -> pd.DataFrame:
    meta = pd.read_csv(DATA / "sample_metadata.csv", keep_default_na=False)
    treatment_map = {"vehicle": "vehicle", "combination": "combination", "olaparib": "olaparib", "mrtx1133": "mrtx1133"}
    meta["treatment_norm"] = meta["treatment"].str.casefold().map(treatment_map)
    if meta["treatment_norm"].isna().any():
        raise ValueError("Unknown treatment in GEO sample metadata")
    meta["replicate_label"] = meta["title"].str.extract(r"_(\d+)$", expand=False).astype(int)
    meta["mrtx1133"] = meta["treatment_norm"].isin(["mrtx1133", "combination"]).astype(int)
    meta["olaparib"] = meta["treatment_norm"].isin(["olaparib", "combination"]).astype(int)
    counts = meta["treatment_norm"].value_counts().to_dict()
    if counts != {"vehicle": 3, "combination": 3, "olaparib": 3, "mrtx1133": 3}:
        raise ValueError(f"Unexpected treatment sample counts: {counts}")
    return meta


def get_files(gsm: str) -> tuple[Path, Path, Path]:
    matches = {p.name: p for p in DATA.glob(f"{gsm}_*")}
    matrices = [p for n, p in matches.items() if "-matrix.mtx.gz" in n]
    bars = [p for n, p in matches.items() if "-barcodes.tsv.gz" in n]
    features = [p for n, p in matches.items() if "-features.tsv.gz" in n]
    if len(matrices) != 1 or len(bars) != 1 or len(features) != 1:
        raise FileNotFoundError(f"Expected one matrix/barcodes/features file for {gsm}")
    return matrices[0], bars[0], features[0]


def process_sample(row: pd.Series) -> tuple[dict[str, object], list[dict[str, object]], dict[str, int]]:
    gsm = str(row["gsm"])
    matrix_path, barcode_path, feature_path = get_files(gsm)
    with gzip.open(feature_path, "rt", encoding="utf-8") as f:
        features = pd.read_csv(f, sep="\t", header=None, names=["ensembl_id", "symbol", "feature_type"])
    with gzip.open(barcode_path, "rt", encoding="utf-8") as f:
        barcodes = [x.strip() for x in f]
    with gzip.open(matrix_path, "rb") as f:
        matrix = mmread(f).tocsr()
    if matrix.shape != (len(features), len(barcodes)):
        raise ValueError(f"Dimension mismatch for {gsm}: {matrix.shape}, {len(features)} features, {len(barcodes)} barcodes")
    gene_names = features["symbol"].astype(str).tolist()
    total_umi = np.asarray(matrix.sum(axis=0)).ravel().astype(float)
    if np.any(total_umi <= 0):
        raise ValueError(f"Empty barcode(s) in {gsm}")
    scale = 10000.0 / total_umi
    # Use the first row for duplicate symbols; duplicate marker symbols are
    # rare, and the source feature ID and retained row are traceable.
    symbol_to_idx: dict[str, int] = {}
    for i, symbol in enumerate(gene_names):
        symbol_to_idx.setdefault(symbol, i)
    union = sorted({g for panel in PANELS.values() for g in panel if g in symbol_to_idx})
    row_idx = np.array([symbol_to_idx[g] for g in union], dtype=int)
    raw = matrix[row_idx, :].toarray().astype(np.float32, copy=False)
    norm = np.log1p(raw * scale[np.newaxis, :]).astype(np.float32, copy=False)
    detected = raw > 0
    uindex = {g: i for i, g in enumerate(union)}
    panel_scores: dict[str, np.ndarray] = {}
    panel_positive_ge1: dict[str, np.ndarray] = {}
    panel_positive_ge2: dict[str, np.ndarray] = {}
    panel_found: dict[str, list[str]] = {}
    for panel, genes in PANELS.items():
        found = [g for g in genes if g in uindex]
        panel_found[panel] = found
        inds = [uindex[g] for g in found]
        if not inds:
            panel_scores[panel] = np.full(len(barcodes), np.nan)
            panel_positive_ge1[panel] = np.zeros(len(barcodes), dtype=bool)
            panel_positive_ge2[panel] = np.zeros(len(barcodes), dtype=bool)
            continue
        panel_scores[panel] = norm[inds, :].mean(axis=0)
        n_detected = detected[inds, :].sum(axis=0)
        panel_positive_ge1[panel] = n_detected >= 1
        panel_positive_ge2[panel] = n_detected >= 2

    sample = {"gsm": gsm, "title": row["title"], "treatment": row["treatment_norm"],
              "replicate_label": int(row["replicate_label"]), "biosample": row.get("biosample", ""),
              "n_cells": len(barcodes), "median_umi_per_cell": float(np.median(total_umi)),
              "mean_umi_per_cell": float(np.mean(total_umi)), "matrix_file": matrix_path.name,
              "matrix_sha256": sha256(matrix_path)}
    long_rows: list[dict[str, object]] = []
    # Marker-positive fractions are sample-level summaries; panels overlap and
    # therefore must not be read as mutually exclusive cell proportions.
    for panel in PANELS:
        for threshold, pos in [("ge1", panel_positive_ge1[panel]), ("ge2", panel_positive_ge2[panel])]:
            long_rows.append({"gsm": gsm, "flow": panel, "metric": f"marker_positive_fraction_{threshold}",
                              "value": float(np.mean(pos)), "n_cells": len(barcodes),
                              "n_stratum_cells": len(barcodes), "genes_available": ";".join(panel_found[panel])})
        long_rows.append({"gsm": gsm, "flow": panel, "metric": "mean_log1p_CPM10k_all_cells",
                          "value": float(np.mean(panel_scores[panel])), "n_cells": len(barcodes),
                          "n_stratum_cells": len(barcodes), "genes_available": ";".join(panel_found[panel])})
    for stratum, identity_panel in STRATA.items():
        for threshold, mask in [("ge1", panel_positive_ge1[identity_panel]),
                                ("ge2", panel_positive_ge2[identity_panel])]:
            for flow in STRATIFIED_FLOWS[stratum]:
                scores = panel_scores[flow]
                value = float(np.mean(scores[mask])) if mask.sum() >= 10 else float("nan")
                long_rows.append({"gsm": gsm, "flow": flow,
                                  "metric": f"mean_log1p_CPM10k_{stratum}_{threshold}",
                                  "value": value, "n_cells": len(barcodes), "n_stratum_cells": int(mask.sum()),
                                  "genes_available": ";".join(panel_found[flow]),
                                  "stratum_rule": f"{identity_panel} with {threshold} positive-marker threshold; >=10 cells"})
    # Keep only per-sample summaries; release the 11k-cell matrix before next sample.
    dim = {"n_features": matrix.shape[0], "n_cells": matrix.shape[1], "nnz": int(matrix.nnz),
           "features_sha256": sha256(feature_path), "barcodes_sha256": sha256(barcode_path)}
    del matrix, raw, norm, detected
    return sample, long_rows, dim


def matrix_dimension_manifest(meta: pd.DataFrame) -> dict[str, dict[str, object]]:
    dimensions = {}
    for _, row in meta.iterrows():
        matrix_path, barcode_path, feature_path = get_files(str(row["gsm"]))
        with gzip.open(matrix_path, "rt", encoding="ascii") as handle:
            next(handle)  # Matrix Market format declaration
            dimensions_line = next(line for line in handle if line.strip() and not line.startswith("%"))
            features_n, cells_n, nnz = map(int, dimensions_line.split())
        dimensions[str(row["gsm"])] = {
            "n_features": features_n, "n_cells": cells_n, "nnz": nnz,
            "features_sha256": sha256(feature_path), "barcodes_sha256": sha256(barcode_path),
        }
    return dimensions


def analyze_sample_summaries(meta: pd.DataFrame, sample_rows: list[dict[str, object]],
                             long_rows: list[dict[str, object]]) -> pd.DataFrame:
    summaries = pd.DataFrame(long_rows).merge(meta[["gsm", "treatment_norm"]], on="gsm", how="left")
    group_order = ["vehicle", "mrtx1133", "olaparib", "combination"]
    assignment_indices = exact_assignments()
    result = []
    planned = summaries.groupby(["flow", "metric"], sort=True)
    for (flow, metric), group in planned:
        values_by_gsm = group.set_index("gsm")["value"]
        sample_gsms = meta["gsm"].tolist()
        y_obs = np.array([values_by_gsm.get(gsm, np.nan) for gsm in sample_gsms], dtype=float)
        if not np.all(np.isfinite(y_obs)):
            # Predeclared flow remains visible, but not inferred where a stratum
            # is absent or the marker panel could not be measured.
            for control in CONTROLS:
                result.append({"control": control, "flow": flow, "metric": metric,
                               "n_samples": int(np.isfinite(y_obs).sum()), "effect": np.nan,
                               "standardized_effect_d": np.nan, "p_exact_balanced": np.nan,
                               "status": "not_estimable_missing_sample_summary"})
            continue
        # Reorder sample summaries to exactly three per factorial cell.
        group_lists = [meta.loc[meta["treatment_norm"].eq(t), "gsm"].tolist() for t in group_order]
        order_gsms = [x for xs in group_lists for x in xs]
        y = np.array([values_by_gsm[gsm] for gsm in order_gsms], dtype=float)
        group_values = y.reshape(4, 3)
        obs_means = group_values.mean(axis=1)
        observed = contrast_values(obs_means)
        # For the exact null, assignments index a vector in the same fixed
        # treatment order. Recompute per contrast in bounded chunks.
        n_perm = len(assignment_indices)
        extreme_by_control = {control: 0 for control in CONTROLS}
        chunk = 8192
        for start in range(0, n_perm, chunk):
            allocated = assignment_indices[start:start+chunk]
            null_means = y[allocated].mean(axis=2)
            nulls = contrast_values(null_means)
            for control in CONTROLS:
                extreme_by_control[control] += int(np.count_nonzero(
                    np.abs(nulls[control]) >= abs(float(observed[control])) - 1e-12))
        for control in CONTROLS:
            est = float(observed[control])
            p = extreme_by_control[control]/n_perm
            if control == "MRTX1133 marginal":
                d = cohen_d(np.r_[group_values[1], group_values[3]], np.r_[group_values[0], group_values[2]])
            elif control == "Olaparib marginal":
                d = cohen_d(np.r_[group_values[2], group_values[3]], np.r_[group_values[0], group_values[1]])
            elif control == "Combination vs Vehicle":
                d = cohen_d(group_values[3], group_values[0])
            else:
                residual = np.concatenate([g - g.mean() for g in group_values])
                sd = float(np.sqrt(np.sum(residual**2)/(len(residual)-4)))
                d = est/sd if sd > 0 else float("nan")
            result.append({"control": control, "flow": flow, "metric": metric, "n_samples": 12,
                           "n_per_group": 3, "effect": est, "standardized_effect_d": d, "p_exact_balanced": p,
                           "effect_size_definition": "Cohen d for two-group/marginal contrasts; interaction divided by within-arm residual SD",
                           "n_permutations": n_perm, "status": "estimable_conditional_on_exchangeability"})
    result_df = pd.DataFrame(result)
    # Correct over the complete planned family for this analysis (control × flow × metric).
    result_df["q_BH_global"] = bh(result_df["p_exact_balanced"].to_numpy())
    return result_df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = load_metadata()
    meta.to_csv(OUT / "GSE309596_sample_metadata_reconciled.csv", index=False)
    sample_cache = OUT / "GSE309596_qc_by_specimen.csv"
    flow_cache = OUT / "GSE309596_sample_level_flows.csv"
    cache_valid = sample_cache.exists() and flow_cache.exists()
    if cache_valid:
        sample_df = pd.read_csv(sample_cache)
        long_df = pd.read_csv(flow_cache)
        cache_valid = len(sample_df) == 12 and sample_df["gsm"].nunique() == 12
        if cache_valid:
            cache_valid = bool(long_df["metric"].astype(str).str.contains(
                "within_T_cell_marker_positive_ge1", regex=False).any())
        if cache_valid:
            for _, row in meta.iterrows():
                matrix_path, _, _ = get_files(str(row["gsm"]))
                recorded = sample_df.loc[sample_df["gsm"].eq(row["gsm"]), "matrix_sha256"]
                if len(recorded) != 1 or recorded.iloc[0] != sha256(matrix_path):
                    cache_valid = False
                    break
    if cache_valid:
        print("Reusing verified cell-summary cache; every source matrix hash matches.", flush=True)
        dimensions = matrix_dimension_manifest(meta)
        all_long = long_df.to_dict("records")
        samples = sample_df.to_dict("records")
    else:
        samples, all_long, dimensions = [], [], {}
        for i, (_, row) in enumerate(meta.iterrows(), 1):
            print(f"[{i}/12] processing {row['gsm']} {row['title']}", flush=True)
            sample, long_rows, dim = process_sample(row)
            samples.append(sample)
            all_long.extend(long_rows)
            dimensions[str(row["gsm"])] = dim
            print(f"      cells={sample['n_cells']:,}; median UMI/cell={sample['median_umi_per_cell']:.0f}", flush=True)
        sample_df = pd.DataFrame(samples)
        sample_df.to_csv(sample_cache, index=False, float_format="%.8g")
        long_df = pd.DataFrame(all_long)
        long_df.to_csv(flow_cache, index=False, float_format="%.10g")
    cell_total = int(sample_df["n_cells"].sum())
    if cell_total != EXPECTED_CELLS_PAPER:
        raise ValueError(f"GEO cell count {cell_total} differs from article's reported {EXPECTED_CELLS_PAPER}")
    sample_df = sample_df.merge(meta[["gsm", "mrtx1133", "olaparib", "batch"]], on="gsm", how="left")
    sample_df.to_csv(sample_cache, index=False, float_format="%.8g")
    long_df.to_csv(flow_cache, index=False, float_format="%.10g")
    tests = analyze_sample_summaries(meta, samples, all_long)
    tests.to_csv(OUT / "GSE309596_controls_by_flows.csv", index=False, float_format="%.10g")
    # Expose the treatment × flow interaction and ordered candidates separately
    # for readers interested in a combination-specific effect.
    interaction = tests[(tests["control"].eq("MRTX1133 × Olaparib interaction")) &
                        (tests["metric"].eq("mean_log1p_CPM10k_all_cells"))].copy()
    interaction = interaction.sort_values(["q_BH_global", "p_exact_balanced"], kind="stable")
    interaction.to_csv(OUT / "GSE309596_interaction_ranked_flows.csv", index=False, float_format="%.10g")
    # Plot all-cell expression-module interaction estimates standardized by the
    # within-group residual SD. This is exploratory ranking, not causal proof.
    plot_df = interaction.dropna(subset=["standardized_effect_d"]).copy()
    plot_df = plot_df.sort_values("standardized_effect_d")
    fig, ax = plt.subplots(figsize=(9, 7), constrained_layout=True)
    colors = ["#B4484B" if x < 0 else "#2878B5" for x in plot_df["standardized_effect_d"]]
    ax.barh(plot_df["flow"], plot_df["standardized_effect_d"], color=colors, alpha=.86)
    ax.axvline(0, color="black", lw=.8)
    ax.set_xlabel("Standardized MRTX1133 × olaparib interaction (exploratory d)")
    ax.set_title("GSE309596: treatment interaction by predeclared flow\n12 GEO specimens; n=3 per factorial arm")
    ax.grid(axis="x", alpha=.2)
    fig.savefig(OUT / "GSE309596_interaction_flows.png", dpi=180)
    plt.close(fig)
    n_q = int((tests["q_BH_global"] < .05).sum())
    t_ge2 = long_df[(long_df["flow"].eq("T_cell_identity")) &
                    (long_df["metric"].eq("marker_positive_fraction_ge2"))].copy()
    t_ge2["n_positive_cells"] = np.rint(t_ge2["value"] * t_ge2["n_cells"]).astype(int)
    low_t_gsms = t_ge2.loc[t_ge2["n_positive_cells"] < 10, "gsm"].tolist()
    with (OUT / "REPORT_GSE309596_therapeutic_axes.md").open("w", encoding="utf-8") as f:
        f.write("# Réanalyse exploratoire scRNA-seq pour prioriser des pistes thérapeutiques PDAC\n\n")
        f.write(f"**Date UTC:** {datetime.now(timezone.utc).isoformat(timespec='seconds')}. **Données:** GEO GSE309596, 12 échantillons KPC1199, 115 664 cellules, quatre bras (véhicule, MRTX1133, olaparib, combinaison), trois échantillons GEO par bras. Le nombre de cellules reproduit le nombre publié.\n\n")
        f.write("## Question thérapeutique\n\n")
        f.write("Quelles populations cellulaires et voies moléculaires montrent une réponse spécifique à la combinaison, et quels axes immunitaires ou tumoraux pourraient expliquer une réponse durable ou une résistance? Les contrôles sont les facteurs MRTX1133, olaparib, leur interaction factorielle, et combinaison versus véhicule. Les flux sont les panneaux de marqueurs de populations et de mécanismes listés dans le script et les tables jointes.\n\n")
        f.write("## Mesures et calculs\n\n")
        f.write("Les UMI ont été agrégés au niveau de chaque spécimen GSM. Aucun test ne traite une cellule comme une réplication. Pour chaque panneau, le flux exprime la moyenne cellulaire log1p(CPM par 10 000) et, pour les panneaux d’identité, la fraction de cellules où au moins un ou au moins deux marqueurs sont détectés. Ces fractions se chevauchent et ne somment pas à 100 %. Des scores restreints aux cellules positives pour des marqueurs tumoraux, T ou myéloïdes sont également fournis avec seuils >=1 et >=2 marqueurs et au moins 10 cellules; ces identités sont des proxys de marqueurs, car aucune annotation par cellule n’est jointe. Les effets sont résumés par contraste, Cohen d descriptif pour les contrastes à deux groupes et effet d’interaction standardisé par l’écart-type résiduel intra-bras; les p sont des permutations exactes des 12 étiquettes d’armement équilibrées (369 600 allocations). La correction BH couvre tous les contrastes × flux × métriques prévus.\n\n")
        f.write("## Résultats observés\n\n")
        f.write(f"La grille contient {len(tests)} comparaisons planifiées; {int(tests['p_exact_balanced'].notna().sum())} sont estimables et {n_q} passent q BH < 0,05. Cette valeur q est conditionnelle à l’échangeabilité des spécimens et au caractère approprié des proxys de marqueurs.\n\n")
        if len(interaction):
            top = interaction.iloc[0]
            f.write(f"Pour le contraste d’interaction sur les scores all-cellules, le plus petit q est {float(top['q_BH_global']):.4g} pour {top['flow']}, avec interaction standardisée d={float(top['standardized_effect_d']):.3g}, p exacte={float(top['p_exact_balanced']):.4g}. Il s’agit d’un classement exploratoire de réponses cellulaires, pas d’une preuve que ce flux est une cible thérapeutique.\n\n")
        f.write("Les tailles des échantillons par bras varient fortement en nombre de cellules (1 281 à 13 625; voir QC par spécimen); les statistiques sont donc réalisées sur 12 spécimens, pas pondérées par le nombre de cellules. Sous le seuil de deux marqueurs T détectés, les spécimens avec moins de 10 cellules positives sont: " + (", ".join(low_t_gsms) if low_t_gsms else "aucun") + ". Les scores restreints aux compartiments T et myéloïdes sont donc non estimables sous ce seuil pour certains bras; les versions avec au moins un marqueur sont fournies comme sensibilité et ne remplacent pas les cellules annotées. Les identifiants GSM/BioSample sont distincts et les titres indiquent des réplicats, mais les métadonnées n’exposent pas d’identifiant souris individuel. L’indépendance entre souris doit être confirmée par les auteurs; les p et q restent conditionnelles. Les scores pan-cellules mélangent expression intrinsèque et composition cellulaire.\n\n")
        f.write("## Limites et portée thérapeutique\n\n")
        f.write("Cette cohorte est la même étude qui décrit la combinaison MRTX1133 + olaparib; elle ne constitue pas une validation indépendante. Les panels sont des choix mécanistiques documentés, pas des résultats sélectionnés après lecture des p-values. Les définitions de marqueurs, les seuils ≥1/≥2, les flux manquants et chaque spécimen sont conservés dans les sorties. Un jeu ponctuel ne permet pas de seuil T0/TLog ou de dynamique de résistance. Les données peuvent aider à prioriser un test préclinique (par exemple une association spécifique avec activation CD8, suppression myéloïde, persistance MAPK/cycle ou déficit HR) mais ne démontrent ni guérison ni efficacité chez des patients.\n\n")
        f.write("**Étape qui peut réellement rapprocher d’un traitement:** prendre le ou les effets les plus solides et leurs cellules porteuses, vérifier la direction dans les comptages et un jeu indépendant; puis les tester dans des organoïdes et modèles immunocompétents avec véhicule, chaque monothérapie et combinaison, mesure de croissance tumorale, survie, toxicité, dose-réponse et marqueurs mécanistiques.\n")
    manifest = {
        "analysis_id": "GSE309596_sample_level_multiflow_therapeutic_scan_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "GEO GSE309596; same published preclinical study as candidate MRTX1133+olaparib paper",
        "unit_of_analysis": "submitted GEO specimen; 12 samples, 3 per arm; animal ID not explicitly provided in GEO metadata",
        "cell_counts": {"sum": cell_total, "published_target": EXPECTED_CELLS_PAPER, "matches_paper": cell_total == EXPECTED_CELLS_PAPER,
                        "by_sample": sample_df.set_index("gsm")["n_cells"].astype(int).to_dict()},
        "design": {"arms": ["vehicle", "MRTX1133", "Olaparib", "Combination"], "replicates_per_arm": 3,
                   "controls": CONTROLS, "time_axis": "single endpoint; no T0/TLog"},
        "estimators": {"cell_summaries": ["mean log1p(CPM per 10,000)", "marker-positive fraction >=1 marker", "marker-positive fraction >=2 markers", "within-marker-positive scores at both thresholds with at least 10 cells"],
                       "effect": "Cohen d for two-group contrasts; factorial interaction contrast standardized by within-arm residual SD",
                       "test": "exact balanced-label permutation over all 369600 assignments of 12 specimens to four groups of 3; conditional on exchangeability",
                       "multiple_testing": "Benjamini-Hochberg over all planned control x flow x metric tests"},
        "panels": PANELS, "strata": STRATA, "stratified_flows": STRATIFIED_FLOWS,
        "identity_threshold_sensitivity": [1, 2],
        "cell_matrix_dimensions": dimensions,
        "input_metadata": {"path": str(SOURCE / "GSE309596_GEO_full_metadata.txt"),
                            "sha256": sha256(SOURCE / "GSE309596_GEO_full_metadata.txt")},
        "download_manifest_sha256": sha256(DATA / "download_manifest.json"),
        "script_sha256": sha256(Path(__file__)),
        "software": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__},
        "scope": "therapeutic hypothesis prioritization only; not a cure, clinical result, independent validation, or full 29-estimator/TLog run",
        "outputs": {},
    }
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"cells": cell_total, "samples": len(sample_df), "planned_tests": len(tests),
                      "estimable_tests": int(tests["p_exact_balanced"].notna().sum()), "q_lt_0_05": n_q,
                      "top_interaction": interaction.head(5)[["flow", "effect", "standardized_effect_d", "p_exact_balanced", "q_BH_global"]].to_dict("records"),
                      "results": str(OUT), "manifest": str(OUT / "manifest.json")}, ensure_ascii=False, default=lambda x: None))


if __name__ == "__main__":
    main()
