#!/usr/bin/env python3
"""Independent, threshold-free audit of KRAS/MUC16/CEACAM5 in three PDAC RNA cohorts.

Reads source matrices from the supplied PDAC v6 archive. It does not import or
call UNIVERSAL_LOG. The source archive is read-only; outputs go beside this file.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import platform
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.stats import norm, t, spearmanr
from scipy.optimize import minimize


HERE = Path(__file__).resolve().parent
ARCHIVE = (HERE.parent / "Archive complète PDAC v6 — ZIP" /
           "pdac-v6-archive-complete-2026-11-15")
DATA = ARCHIVE / "03_runs-pdac-v6-2026-11-15" / "data"
TARGETS = ("MUC16", "CEACAM5")
ACINAR = ("PNLIP", "CTRB2", "CELA3A", "CTRB1", "CPA1", "CELA2A",
          "CPB1", "CELA3B", "CLPS", "CTRC", "CPA2")
ISLET = ("INS", "GCG", "PPY", "SST")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def bh_adjust(pvalues: np.ndarray) -> np.ndarray:
    p = np.asarray(pvalues, dtype=float)
    q = np.full(p.shape, np.nan)
    good = np.flatnonzero(np.isfinite(p))
    if not len(good):
        return q
    order = good[np.argsort(p[good])]
    ranked = p[order] * len(order) / np.arange(1, len(order) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q[order] = np.minimum(ranked, 1.0)
    return q


def load_tcga() -> tuple[pd.DataFrame, dict]:
    path = DATA / "tcga_paad_rsem.tar.gz"
    with tarfile.open(path, "r:gz") as tf:
        member = next(m for m in tf.getmembers() if m.name.endswith(".data.txt"))
        frame = pd.read_csv(tf.extractfile(member), sep="\t", index_col=0,
                            low_memory=False)
    frame.index = frame.index.to_series().str.split("|").str[0]
    frame = frame.loc[~frame.index.duplicated(keep="first")]
    tumor_cols = [c for c in frame.columns if str(c)[13:15] == "01"]
    matrix = frame[tumor_cols].apply(pd.to_numeric, errors="coerce")
    matrix = matrix.dropna(axis=0, how="any")
    matrix = np.log2(matrix + 1.0)
    meta = {"cohort": "TCGA-PAAD Firehose 2016-01-28",
            "source_file": str(path), "sha256": sha256(path),
            "sample_rule": "TCGA barcode sample-type code 01; primary tumors",
            "expression_scale": "log2(RSEM normalized + 1)",
            "n_samples": int(matrix.shape[1]), "n_genes": int(matrix.shape[0]),
            "removed_rows_with_missing": int(frame.shape[0] - matrix.shape[0]),
            "purity_proxy_genes_acinar": [g for g in ACINAR if g in matrix.index],
            "purity_proxy_genes_islet": [g for g in ISLET if g in matrix.index]}
    return matrix, meta


def geo_metadata(path: Path, prefix: str) -> tuple[list[str], list[str]]:
    characteristics = []
    titles: list[str] = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("!series_matrix_table_begin"):
                break
            if line.startswith(prefix):
                characteristics.append([x.strip().strip('"')
                                        for x in line.rstrip("\r\n").split("\t")[1:]])
            elif line.startswith("!Sample_title"):
                titles = [x.strip().strip('"')
                          for x in line.rstrip("\r\n").split("\t")[1:]]
    return characteristics, titles


def load_geo71729() -> tuple[pd.DataFrame, dict]:
    path = DATA / "GSE71729_series_matrix.txt.gz"
    matrix = pd.read_csv(path, sep="\t", comment="!", index_col=0,
                         low_memory=False)
    matrix.index = matrix.index.astype(str).str.strip().str.strip('"')
    matrix.columns = [str(c).strip().strip('"') for c in matrix.columns]
    characteristics, titles = geo_metadata(path, "!Sample_characteristics_ch2")
    sample_kinds = []
    for i in range(matrix.shape[1]):
        joined = " | ".join(row[i] for row in characteristics if i < len(row))
        if "tissue type: Primary" in joined:
            sample_kinds.append("Primary")
        elif "tissue type: Metastasis" in joined:
            sample_kinds.append("Metastasis")
        elif "tissue type: Normal" in joined:
            sample_kinds.append("Normal")
        elif i < len(titles) and titles[i].endswith("-CellLine"):
            sample_kinds.append("CellLine")
        else:
            sample_kinds.append("Unknown")
    matrix = matrix.loc[:, np.array(sample_kinds) == "Primary"]
    matrix = matrix.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    matrix = matrix.groupby(level=0).median()
    meta = {"cohort": "GEO GSE71729 (Moffitt et al. 2015)",
            "source_file": str(path), "sha256": sha256(path),
            "sample_rule": "GEO characteristics_ch2 tissue type: Primary",
            "expression_scale": "author-provided log2 Cy5 values",
            "n_samples": int(matrix.shape[1]), "n_genes": int(matrix.shape[0]),
            "removed_rows_with_missing": None,
            "purity_proxy_genes_acinar": [g for g in ACINAR if g in matrix.index],
            "purity_proxy_genes_islet": [g for g in ISLET if g in matrix.index]}
    return matrix, meta


def load_geo62452() -> tuple[pd.DataFrame, dict]:
    path = DATA / "GSE62452_series_matrix.txt.gz"
    map_path = DATA / "GPL6244_probe2symbol.tsv"
    probes = pd.read_csv(path, sep="\t", comment="!", index_col=0,
                         low_memory=False)
    probes.index = probes.index.astype(str).str.strip().str.strip('"')
    probes.columns = [str(c).strip().strip('"') for c in probes.columns]
    characteristics, _titles = geo_metadata(path, "!Sample_characteristics_ch1")
    sample_kinds = []
    for i in range(probes.shape[1]):
        joined = " | ".join(row[i] for row in characteristics if i < len(row))
        if "tissue: Pancreatic tumor" in joined:
            sample_kinds.append("Tumor")
        elif "tissue: adjacent pancreatic non-tumor" in joined:
            sample_kinds.append("Normal")
        else:
            sample_kinds.append("Unknown")
    probes = probes.loc[:, np.array(sample_kinds) == "Tumor"]
    probes = probes.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    mapping = pd.read_csv(map_path, sep="\t", dtype=str).fillna("")
    probe_to_symbol = dict(zip(mapping["probe"].astype(str), mapping["symbol"].str.strip()))
    symbols = probes.index.map(probe_to_symbol)
    keep = np.array([(s is not None) and (str(s).strip() != "") for s in symbols])
    probes = probes.iloc[keep].copy()
    probes.index = [str(s).strip() for s in symbols[keep]]
    matrix = probes.groupby(level=0).median()
    meta = {"cohort": "GEO GSE62452 (Hussain et al.)",
            "source_file": str(path), "sha256": sha256(path),
            "mapping_file": str(map_path), "mapping_sha256": sha256(map_path),
            "sample_rule": "GEO characteristics_ch1 tumor tissue; GPL6244 probe-to-symbol, median across probes",
            "expression_scale": "author-provided log2 Affymetrix intensity values",
            "n_samples": int(matrix.shape[1]), "n_genes": int(matrix.shape[0]),
            "removed_rows_with_missing": None,
            "purity_proxy_genes_acinar": [g for g in ACINAR if g in matrix.index],
            "purity_proxy_genes_islet": [g for g in ISLET if g in matrix.index]}
    return matrix, meta


def geo62452_probe_sensitivity() -> tuple[pd.DataFrame, dict]:
    """Check if GSE62452 marker results depend on averaging probe sets by median."""
    path = DATA / "GSE62452_series_matrix.txt.gz"
    map_path = DATA / "GPL6244_probe2symbol.tsv"
    probes = pd.read_csv(path, sep="\t", comment="!", index_col=0, low_memory=False)
    probes.index = probes.index.astype(str).str.strip().str.strip('"')
    probes.columns = [str(c).strip().strip('"') for c in probes.columns]
    characteristics, _titles = geo_metadata(path, "!Sample_characteristics_ch1")
    sample_kinds = []
    for i in range(probes.shape[1]):
        joined = " | ".join(row[i] for row in characteristics if i < len(row))
        sample_kinds.append("Tumor" if "tissue: Pancreatic tumor" in joined else "Other")
    probes = probes.loc[:, np.array(sample_kinds) == "Tumor"]
    probes = probes.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    mapping = pd.read_csv(map_path, sep="\t", dtype=str).fillna("")
    probe_to_symbol = dict(zip(mapping["probe"].astype(str), mapping["symbol"].str.strip()))
    symbols = probes.index.map(probe_to_symbol)
    keep = np.array([(s is not None) and (str(s).strip() != "") for s in symbols])
    probe_ids = probes.index[keep].astype(str).to_numpy()
    probes = probes.iloc[keep].copy()
    probes.index = [str(s).strip() for s in symbols[keep]]
    kras = probes.loc[["KRAS"]].median(axis=0)
    rows = []
    for method in ("median", "mean"):
        grouped = probes.groupby(level=0).agg(method)
        for gene in TARGETS:
            rho, p = spearmanr(kras.to_numpy(dtype=float),
                               grouped.loc[gene].to_numpy(dtype=float))
            rows.append({"aggregation": method, "gene": gene,
                         "n_samples": int(grouped.shape[1]),
                         "n_gene_probes": int((probes.index == gene).sum()),
                         "n_KRAS_probes": int((probes.index == "KRAS").sum()),
                         "spearman_rho_with_KRAS_median": float(rho),
                         "p_two_sided": float(p)})
    for gene in TARGETS:
        target_probe_ids = probe_ids[probes.index == gene]
        for probe_id, (_, values) in zip(target_probe_ids, probes.loc[[gene]].iterrows()):
            rho, p = spearmanr(kras.to_numpy(dtype=float), values.to_numpy(dtype=float))
            rows.append({"aggregation": "individual_probe", "gene": gene,
                         "probe_id": str(probe_id), "n_samples": int(probes.shape[1]),
                         "n_gene_probes": int((probes.index == gene).sum()),
                         "n_KRAS_probes": int((probes.index == "KRAS").sum()),
                         "spearman_rho_with_KRAS_median": float(rho),
                         "p_two_sided": float(p)})
    table = pd.DataFrame(rows)
    table["BH_q_aggregate_methods_only"] = np.nan
    aggregate_mask = table["aggregation"].isin(["median", "mean"])
    table.loc[aggregate_mask, "BH_q_aggregate_methods_only"] = bh_adjust(
        table.loc[aggregate_mask, "p_two_sided"].to_numpy(dtype=float))
    meta = {"source_file": str(path), "source_sha256": sha256(path),
            "mapping_file": str(map_path), "mapping_sha256": sha256(map_path),
            "scope": "Sensitivity only: median versus mean across mapped GPL6244 probes; also reports each target probe against median KRAS probe expression. The per-probe tests are descriptive and not independently FDR-adjusted.",
            "tumor_samples": int(probes.shape[1])}
    return table, meta


def genome_spearman(matrix: pd.DataFrame) -> pd.DataFrame:
    """Vectorized Spearman of every gene against KRAS, BH over all measured genes."""
    if "KRAS" not in matrix.index:
        raise ValueError("KRAS missing from expression matrix")
    genes = matrix.index.astype(str).to_numpy()
    values = matrix.to_numpy(dtype=np.float64, copy=True)
    x = values[np.flatnonzero(genes == "KRAS")[0]]
    x_rank = pd.Series(x).rank(method="average").to_numpy(dtype=np.float64)
    xc = x_rank - x_rank.mean()
    y_rank = pd.DataFrame(values).rank(axis=1, method="average").to_numpy(dtype=np.float64)
    yc = y_rank - y_rank.mean(axis=1, keepdims=True)
    denom = np.sqrt(np.sum(yc * yc, axis=1) * np.sum(xc * xc))
    rho = np.divide(yc @ xc, denom, out=np.full(len(genes), np.nan), where=denom > 0)
    rho = np.clip(rho, -1.0, 1.0)
    n = matrix.shape[1]
    with np.errstate(divide="ignore", invalid="ignore"):
        statistic = rho * np.sqrt((n - 2) / (1 - rho * rho))
    p = 2 * t.sf(np.abs(statistic), df=n - 2)
    p[genes == "KRAS"] = np.nan  # self-correlation is not a tested feature
    q = bh_adjust(p)
    return pd.DataFrame({"gene": genes, "n": n, "spearman_rho_with_KRAS": rho,
                         "p_two_sided": p, "BH_q_within_cohort": q})


def genome_partial_spearman(matrix: pd.DataFrame) -> pd.DataFrame:
    """Genome-wide partial Spearman, controlling acinar/islet expression proxies."""
    acinar = [g for g in ACINAR if g in matrix.index]
    islet = [g for g in ISLET if g in matrix.index]
    if "KRAS" not in matrix.index or not acinar or not islet:
        raise ValueError("KRAS and acinar/islet proxies are required")
    genes = matrix.index.astype(str).to_numpy()
    values = matrix.to_numpy(dtype=np.float64, copy=True)
    ranks = pd.DataFrame(values).rank(axis=1, method="average").to_numpy(dtype=np.float64)
    kras_i = int(np.flatnonzero(genes == "KRAS")[0])
    x_rank = ranks[kras_i]
    ac_score = matrix.loc[acinar].median(axis=0).to_numpy(dtype=float)
    islet_score = matrix.loc[islet].median(axis=0).to_numpy(dtype=float)
    ac_rank = pd.Series(ac_score).rank(method="average").to_numpy(dtype=float)
    islet_rank = pd.Series(islet_score).rank(method="average").to_numpy(dtype=float)
    design = np.column_stack([np.ones(matrix.shape[1]), ac_rank, islet_rank])
    beta = np.linalg.lstsq(design, ranks.T, rcond=None)[0]
    residual_y = ranks - (design @ beta).T
    residual_x = x_rank - design @ np.linalg.lstsq(design, x_rank, rcond=None)[0]
    denom = np.sqrt(np.sum(residual_y * residual_y, axis=1) * np.sum(residual_x * residual_x))
    rho = np.divide(residual_y @ residual_x, denom,
                    out=np.full(len(genes), np.nan), where=denom > 0)
    rho = np.clip(rho, -1.0, 1.0)
    df = matrix.shape[1] - design.shape[1] - 1
    with np.errstate(divide="ignore", invalid="ignore"):
        statistic = rho * np.sqrt(df / (1 - rho * rho))
    p = 2 * t.sf(np.abs(statistic), df=df)
    p[genes == "KRAS"] = np.nan
    q = bh_adjust(p)
    return pd.DataFrame({"gene": genes, "partial_spearman_rho": rho,
                         "partial_p_two_sided": p, "partial_BH_q_within_cohort": q})


def partial_spearman(matrix: pd.DataFrame, gene: str) -> dict:
    """Partial rank correlation KRAS~gene conditional on acinar/islet proxy scores."""
    acinar = [g for g in ACINAR if g in matrix.index]
    islet = [g for g in ISLET if g in matrix.index]
    if gene not in matrix.index or not acinar or not islet:
        return {"gene": gene, "partial_spearman_rho": None, "p_two_sided": None,
                "conditioned_on_acinar": acinar, "conditioned_on_islet": islet}
    x = matrix.loc["KRAS"].to_numpy(dtype=float)
    y = matrix.loc[gene].to_numpy(dtype=float)
    ac = matrix.loc[acinar].median(axis=0).to_numpy(dtype=float)
    isl = matrix.loc[islet].median(axis=0).to_numpy(dtype=float)
    rx = pd.Series(x).rank().to_numpy(dtype=float)
    ry = pd.Series(y).rank().to_numpy(dtype=float)
    rac = pd.Series(ac).rank().to_numpy(dtype=float)
    risl = pd.Series(isl).rank().to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x)), rac, risl])
    rx_res = rx - design @ np.linalg.lstsq(design, rx, rcond=None)[0]
    ry_res = ry - design @ np.linalg.lstsq(design, ry, rcond=None)[0]
    rho = float(np.corrcoef(rx_res, ry_res)[0, 1])
    df = len(x) - design.shape[1] - 1
    stat = rho * np.sqrt(df / max(1e-15, 1.0 - rho * rho))
    p = float(2 * t.sf(abs(stat), df=df))
    return {"gene": gene, "partial_spearman_rho": rho, "p_two_sided": p,
            "conditioned_on_acinar": acinar, "conditioned_on_islet": islet}


def stouffer_partial_one_sided(rows: list[dict], gene: str,
                               cohorts: tuple[str, ...]) -> dict:
    """Combine independent, cohort-level purity-adjusted rank tests directionally."""
    selected = [r for r in rows if r["gene"] == gene and r["cohort"] in cohorts]
    z_values, weights = [], []
    for r in selected:
        rho = r["partial_spearman_rho_adjusted_purity_proxies"]
        p2 = max(r["partial_spearman_p_two_sided"], np.finfo(float).tiny)
        z = norm.isf(p2 / 2) * (1 if rho >= 0 else -1)
        w = np.sqrt(max(1, r["n_samples"] - 3))
        z_values.append(z)
        weights.append(w)
    combined_z = float(np.dot(z_values, weights) / np.sqrt(np.dot(weights, weights)))
    return {"gene": gene, "cohorts": list(cohorts), "directional_weighted_z": combined_z,
            "p_one_sided_positive": float(norm.sf(combined_z)),
            "n_independent_cohorts": len(selected)}


def cox_breslow(X: np.ndarray, time: np.ndarray, event: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
    """Cox PH fit with Breslow handling of tied event times (small dense models)."""
    event_times = np.unique(time[event == 1])

    def likelihood(beta: np.ndarray) -> tuple[float, np.ndarray]:
        eta = X @ beta
        loglik = 0.0
        gradient = np.zeros(X.shape[1], dtype=float)
        for t_event in event_times:
            deaths = (time == t_event) & (event == 1)
            risk = time >= t_event
            d = int(deaths.sum())
            eta_risk = eta[risk]
            shift = float(np.max(eta_risk))
            weights = np.exp(eta_risk - shift)
            denom = float(weights.sum())
            mean_x = (weights[:, None] * X[risk]).sum(axis=0) / denom
            loglik += float(eta[deaths].sum()) - d * (shift + np.log(denom))
            gradient += X[deaths].sum(axis=0) - d * mean_x
        return -loglik, -gradient

    fit = minimize(lambda b: likelihood(b), np.zeros(X.shape[1]), jac=True,
                   method="BFGS", options={"gtol": 1e-8, "maxiter": 3000})
    beta = np.asarray(fit.x, dtype=float)
    # Observed information: negative Hessian of the partial log likelihood.
    eta = X @ beta
    information = np.zeros((X.shape[1], X.shape[1]), dtype=float)
    for t_event in event_times:
        deaths = (time == t_event) & (event == 1)
        risk = time >= t_event
        d = int(deaths.sum())
        eta_risk = eta[risk]
        weights = np.exp(eta_risk - np.max(eta_risk))
        weights /= weights.sum()
        xr = X[risk]
        mean_x = (weights[:, None] * xr).sum(axis=0)
        second = (xr.T * weights) @ xr
        information += d * (second - np.outer(mean_x, mean_x))
    covariance = np.linalg.pinv(information)
    se = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    return beta, se, bool(fit.success)


def analyze_tcga_survival(matrix: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Exploratory Cox audit; matches expression and clinical records by TCGA case barcode."""
    clinical_path = ARCHIVE / "03_runs-pdac-v6-2026-11-15" / "data_clinical_patient.txt"
    clinical = pd.read_csv(clinical_path, sep="\t", skiprows=4, dtype=str,
                           low_memory=False)
    clinical = clinical.loc[clinical["CANCER_TYPE_ACRONYM"] == "PAAD"].copy()
    clinical["time"] = pd.to_numeric(clinical["OS_MONTHS"], errors="coerce")
    clinical["event"] = clinical["OS_STATUS"].str.split(":").str[0].map({"1": 1, "0": 0})
    clinical["age"] = pd.to_numeric(clinical["AGE"], errors="coerce")
    clinical["female"] = clinical["SEX"].map({"Female": 1.0, "Male": 0.0})
    stage = clinical["AJCC_PATHOLOGIC_TUMOR_STAGE"].fillna("").str.upper()
    clinical["stage_group"] = np.select(
        [stage.str.fullmatch(r"STAGE I(?:A|B)?"), stage.str.fullmatch(r"STAGE II(?:A|B)?"),
         stage.str.fullmatch(r"STAGE III|STAGE IV")],
        ["I", "II", "III_IV"], default="Unknown")
    clinical = clinical.drop_duplicates("PATIENT_ID", keep="first").set_index("PATIENT_ID")

    samples = pd.DataFrame({"sample": matrix.columns.astype(str)})
    samples["patient"] = samples["sample"].str.slice(0, 12)
    expr = pd.DataFrame({g: matrix.loc[g].to_numpy(dtype=float) for g in
                         ("KRAS", "MUC16", "CEACAM5")}, index=samples["patient"])
    expr = expr.loc[~expr.index.duplicated(keep="first")]
    joined = expr.join(clinical[["time", "event", "age", "female", "stage_group"]], how="inner")
    joined = joined.replace([np.inf, -np.inf], np.nan)

    rows: list[dict] = []
    models = {
        "univariable_KRAS": ["KRAS"],
        "univariable_MUC16": ["MUC16"],
        "univariable_CEACAM5": ["CEACAM5"],
        "markers_only": ["KRAS", "MUC16", "CEACAM5"],
        "markers_plus_age_sex_stage": ["KRAS", "MUC16", "CEACAM5", "age", "female",
                                        "stage_I", "stage_III_IV"],
    }
    for model_name, columns in models.items():
        frame = joined.copy()
        frame["stage_I"] = (frame["stage_group"] == "I").astype(float)
        frame["stage_III_IV"] = (frame["stage_group"] == "III_IV").astype(float)
        needed = columns + ["time", "event"]
        if "stage_I" in columns:
            needed.append("stage_group")
        frame = frame[needed].dropna()
        if "stage_group" in frame:
            frame = frame.loc[frame["stage_group"] != "Unknown"]
        frame = frame.loc[(frame["time"] >= 0) & frame["event"].isin([0, 1])]
        if len(frame) < 20 or int(frame["event"].sum()) < 10:
            continue
        Xcols = []
        for col in columns:
            value = frame[col].to_numpy(dtype=float)
            sd = float(np.std(value, ddof=0))
            if sd <= 0:
                continue
            frame[f"z_{col}"] = (value - float(np.mean(value))) / sd
            Xcols.append(f"z_{col}")
        X = frame[Xcols].to_numpy(dtype=float)
        beta, se, converged = cox_breslow(X, frame["time"].to_numpy(dtype=float),
                                          frame["event"].to_numpy(dtype=int))
        for col, b, s in zip(Xcols, beta, se):
            rows.append({"model": model_name, "term": col.removeprefix("z_"),
                         "n": len(frame), "events": int(frame["event"].sum()),
                         "hazard_ratio_per_SD": float(np.exp(b)),
                         "ci95_low": float(np.exp(b - 1.96 * s)),
                         "ci95_high": float(np.exp(b + 1.96 * s)),
                         "p_wald_two_sided": float(2 * norm.sf(abs(b / s))) if s > 0 else None,
                         "converged": converged, "tie_method": "Breslow",
                         "stage_group_counts": json.dumps(frame["stage_group"].value_counts().to_dict())
                         if "stage_group" in frame else "not included"})
    meta = {"clinical_source": str(clinical_path), "clinical_sha256": sha256(clinical_path),
            "clinical_rows_PAAD": int(len(clinical)), "expression_patients": int(len(expr)),
            "joined_patients": int(len(joined)),
            "method": "Cox proportional hazards partial likelihood; Breslow tied-event approximation; Wald CI/p from observed information; RNA and age standardized within each complete-case model; marker-only and age/sex/pathologic-stage adjusted models; exploratory, no external clinical validation.",
            "stage_counts_all_joined": joined["stage_group"].value_counts().to_dict()}
    return pd.DataFrame(rows), meta


def cohen_d_top_group(matrix: pd.DataFrame, gene: str, n_top: int) -> dict:
    kras = matrix.loc["KRAS"].to_numpy(dtype=float)
    y = matrix.loc[gene].to_numpy(dtype=float)
    order = np.argsort(kras, kind="mergesort")
    top, rest = y[order[-n_top:]], y[order[:-n_top]]
    pooled_var = ((len(top) - 1) * np.var(top, ddof=1) +
                  (len(rest) - 1) * np.var(rest, ddof=1)) / (len(top) + len(rest) - 2)
    d = float((np.mean(top) - np.mean(rest)) / np.sqrt(pooled_var)) if pooled_var > 0 else np.nan
    return {"n_top": n_top, "top_mean_minus_rest_mean": float(np.mean(top) - np.mean(rest)),
            "cohen_d_top_vs_rest": d}


def analyze_cohort(matrix: pd.DataFrame, meta: dict) -> tuple[list[dict], pd.DataFrame]:
    all_correlations = genome_spearman(matrix)
    all_partial = genome_partial_spearman(matrix)
    all_correlations = all_correlations.merge(all_partial, on="gene", validate="one_to_one")
    rows = []
    for gene in TARGETS:
        if gene not in matrix.index:
            raise ValueError(f"{gene} missing in {meta['cohort']}")
        genome_row = all_correlations.loc[all_correlations["gene"] == gene].iloc[0]
        row = {"cohort": meta["cohort"], "n_samples": matrix.shape[1], "gene": gene,
               "spearman_rho_with_KRAS": float(genome_row["spearman_rho_with_KRAS"]),
               "p_two_sided": float(genome_row["p_two_sided"]),
               "BH_q_across_all_measured_genes": float(genome_row["BH_q_within_cohort"]),
               "partial_spearman_rho_adjusted_purity_proxies": float(genome_row["partial_spearman_rho"]),
               "partial_spearman_p_two_sided": float(genome_row["partial_p_two_sided"]),
               "partial_BH_q_all_measured_genes": float(genome_row["partial_BH_q_within_cohort"]),
               "partial_purity_proxies_acinar": ";".join(meta["purity_proxy_genes_acinar"]),
               "partial_purity_proxies_islet": ";".join(meta["purity_proxy_genes_islet"])}
        for n_top in (7, 12, 20, max(5, int(np.ceil(matrix.shape[1] * 0.25)))):
            if n_top < matrix.shape[1]:
                row.update({f"top{n_top}_{k}": v for k, v in cohen_d_top_group(matrix, gene, n_top).items()
                            if k != "n_top"})
        rows.append(row)
    all_correlations.insert(0, "cohort", meta["cohort"])
    return rows, all_correlations


def stouffer_one_sided(rows: list[dict], gene: str, cohorts: tuple[str, ...]) -> dict:
    selected = [r for r in rows if r["gene"] == gene and r["cohort"] in cohorts]
    z_values, weights = [], []
    for r in selected:
        rho = r["spearman_rho_with_KRAS"]
        p2 = max(r["p_two_sided"], np.finfo(float).tiny)
        z = norm.isf(p2 / 2) * (1 if rho >= 0 else -1)
        w = np.sqrt(max(1, r["n_samples"] - 3))
        z_values.append(z); weights.append(w)
    combined_z = float(np.dot(z_values, weights) / np.sqrt(np.dot(weights, weights)))
    return {"gene": gene, "cohorts": list(cohorts), "directional_weighted_z": combined_z,
            "p_one_sided_positive": float(norm.sf(combined_z)),
            "n_independent_cohorts": len(selected)}


def main() -> None:
    cohort_loaders = (load_tcga, load_geo71729, load_geo62452)
    cohort_meta, summary_rows, all_gene_tables = [], [], []
    survival_rows: pd.DataFrame | None = None
    survival_meta: dict | None = None
    for cohort_i, loader in enumerate(cohort_loaders):
        matrix, meta = loader()
        cohort_meta.append(meta)
        rows, all_gene = analyze_cohort(matrix, meta)
        if cohort_i == 0:
            survival_rows, survival_meta = analyze_tcga_survival(matrix)
        summary_rows.extend(rows)
        all_gene_tables.append(all_gene)
        print(meta["cohort"], "n=", meta["n_samples"], "genes=", meta["n_genes"])
        for row in rows:
            print(row["gene"], "rho=", round(row["spearman_rho_with_KRAS"], 4),
                  "p=", f"{row['p_two_sided']:.4g}",
                  "BH_q=", f"{row['BH_q_across_all_measured_genes']:.4g}",
                  "partial_rho=", (None if row["partial_spearman_rho_adjusted_purity_proxies"] is None else
                                    round(row["partial_spearman_rho_adjusted_purity_proxies"], 4)))
        del matrix
    summary = pd.DataFrame(summary_rows)
    all_genes = pd.concat(all_gene_tables, ignore_index=True)
    summary.to_csv(HERE / "target_associations.csv", index=False)
    all_genes.to_csv(HERE / "all_gene_spearman_vs_KRAS.csv", index=False)
    if survival_rows is None or survival_meta is None:
        raise RuntimeError("TCGA survival audit was not produced")
    survival_rows.to_csv(HERE / "survival_cox_audit.csv", index=False)
    probe_sensitivity, probe_meta = geo62452_probe_sensitivity()
    probe_sensitivity.to_csv(HERE / "geo62452_probe_sensitivity.csv", index=False)
    geo_meta = [stouffer_one_sided(summary_rows, g, (cohort_meta[1]["cohort"], cohort_meta[2]["cohort"])) for g in TARGETS]
    geo_partial_meta = [stouffer_partial_one_sided(summary_rows, g,
                                                   (cohort_meta[1]["cohort"], cohort_meta[2]["cohort"]))
                        for g in TARGETS]
    all_meta = [stouffer_one_sided(summary_rows, g, tuple(m["cohort"] for m in cohort_meta)) for g in TARGETS]
    geo_q = bh_adjust(np.array([x["p_one_sided_positive"] for x in geo_meta]))
    geo_partial_q = bh_adjust(np.array([x["p_one_sided_positive"] for x in geo_partial_meta]))
    all_q = bh_adjust(np.array([x["p_one_sided_positive"] for x in all_meta]))
    for item, q in zip(geo_meta, geo_q):
        item["BH_q_across_two_targets"] = float(q)
    for item, q in zip(all_meta, all_q):
        item["BH_q_across_two_targets"] = float(q)
    for item, q in zip(geo_partial_meta, geo_partial_q):
        item["BH_q_across_two_targets"] = float(q)
    meta = {"analysis": "independent threshold-free expression audit; no UNIVERSAL_LOG code imported",
            "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "scipy": scipy.__version__,
            "archive_root": str(ARCHIVE), "source_inputs": cohort_meta,
            "tests": "Spearman of each measured gene with KRAS expression; partial Spearman of every measured gene conditional on acinar/islet expression proxies; BH within each cohort across every measured gene except KRAS itself for both tests; descriptive top-k Cohen d only.",
            "selected_targets": list(TARGETS),
            "important_limit": "Targets were highlighted after exploratory TCGA discovery; the two GEO cohorts are the independent replication set. This expression analysis does not validate a change point, TLog, protein abundance, serum biomarkers, KRAS mutation/activity, treatment response, causality, or clinical utility.",
            "geo_replication_stouffer": geo_meta,
            "geo_replication_partial_spearman_stouffer_adjusted_for_purity_proxies": geo_partial_meta,
            "three_cohort_stouffer_exploratory": all_meta,
            "survival_audit": survival_meta,
            "geo62452_probe_aggregation_sensitivity": probe_meta,
            "outputs": {"target_associations.csv": sha256(HERE / "target_associations.csv"),
                        "all_gene_spearman_vs_KRAS.csv": sha256(HERE / "all_gene_spearman_vs_KRAS.csv"),
                        "survival_cox_audit.csv": sha256(HERE / "survival_cox_audit.csv"),
                        "geo62452_probe_sensitivity.csv": sha256(HERE / "geo62452_probe_sensitivity.csv")}}
    (HERE / "analysis_manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", HERE / "target_associations.csv")
    print("Wrote", HERE / "all_gene_spearman_vs_KRAS.csv")
    print("Wrote", HERE / "analysis_manifest.json")


if __name__ == "__main__":
    main()
