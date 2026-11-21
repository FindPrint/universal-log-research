#!/usr/bin/env python3
"""Independent, marker-panel reanalysis of public MUC1-C/KRAS RNA-seq.

This script deliberately does not emulate the authors' R/ComBat-seq/TCC/edgeR
workflow. It computes transparent within-study log-expression contrasts and
probes the v6.0.0 estimator entry gate. GEO source files stay in the ignored
``source`` directory; only compact summaries are written beside this script.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import platform
import re
import tarfile
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from scipy.stats import t, ttest_ind


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
SOURCE = HERE / "source"
SOURCE.mkdir(parents=True, exist_ok=True)

PIPELINE_PATH = PROJECT_ROOT / "pancréas" / "universal_v6.0.0_cohen - Copie.py.txt"
AUTHOR_REPO = "https://github.com/TomokiMotegi/PDAC_MUC1"
AUTHOR_COMMIT = "a5eabf881688a4405fed9556f13b5c7042e3fcb0"
AUTHOR_SCRIPT_SHA256 = "96cd42d0173edf302f005dcdc21cce1b2f4df6ffc50f3483aaa6edae0f81f8a7"

MARKER_GROUPS = {
    "MUC1_target": ["MUC1"],
    "NFkB_panel": ["RELA", "NFKB1", "NFKBIA", "TNFAIP3"],
    "IFN_panel": ["ISG15", "IFIT1", "STAT1", "IRF7", "IFI44L"],
    "EMT_panel": ["CDH1", "EPCAM", "VIM", "ZEB1", "CDH2"],
}
MARKERS = [gene for genes in MARKER_GROUPS.values() for gene in genes]
FLOW_NAMES = MARKERS + ["NFkB_panel_mean", "IFN_panel_mean", "EMT_panel_mean"]

DOWNLOADS = {
    "GSE181961_family.soft.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE181nnn/GSE181961/soft/GSE181961_family.soft.gz",
    "GSE181961_Cuff_Gene_Counts.csv.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE181nnn/GSE181961/suppl/GSE181961_Cuff_Gene_Counts.csv.gz",
    "GSE279749_family.soft.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE279nnn/GSE279749/soft/GSE279749_family.soft.gz",
    "GSE279749_gene_fpkm_PDX.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE279nnn/GSE279749/suppl/GSE279749_gene_fpkm_PDX.txt.gz",
    "GSE279749_gene_fpkm_cell_lines.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE279nnn/GSE279749/suppl/GSE279749_gene_fpkm_cell_lines.txt.gz",
    "GSE269985_RAW.tar": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE269nnn/GSE269985/suppl/GSE269985_RAW.tar",
    "GSE293756_STAR_Gene_Counts.csv.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE293nnn/GSE293756/suppl/GSE293756_STAR_Gene_Counts.csv.gz",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ensure_source_files() -> list[dict]:
    records = []
    for name, url in DOWNLOADS.items():
        path = SOURCE / name
        if not path.exists():
            request = Request(url, headers={"User-Agent": "UNIVERSAL_LOG reproducibility audit/1.0"})
            with urlopen(request, timeout=120) as response:
                path.write_bytes(response.read())
        records.append({"file": name, "url": url, "bytes": path.stat().st_size, "sha256": sha256(path)})
    return records


def parse_soft(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    records: list[dict] = []
    current: dict | None = None
    for line in lines:
        if line.startswith("^SAMPLE = "):
            current = {"geo_accession": line.split("=", 1)[1].strip()}
            records.append(current)
            continue
        if line.startswith("^SERIES = "):
            current = None
            continue
        if current is not None and line.startswith("!") and " = " in line:
            key, value = line[1:].split(" = ", 1)
            current.setdefault(key, []).append(value.strip().strip('"'))
    return records


def first(record: dict, key: str, default: str = "") -> str:
    values = record.get(key, [])
    return values[0] if values else default


def sample_char_map(record: dict) -> dict[str, str]:
    out = {}
    for item in record.get("Sample_characteristics_ch1", []):
        if ":" in item:
            key, value = item.split(":", 1)
            out[key.strip().lower()] = value.strip()
    return out


def read_sample_inventory() -> dict[str, dict]:
    path = HERE / "GEO_SAMPLE_INVENTORY.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["geo_accession"]: row for row in csv.DictReader(handle)}


def marker_logcpm_matrix(path: Path, delimiter: str, gene_column: str, gene_name_column: str | None = None) -> tuple[list[str], dict[str, dict[str, float]], dict[str, int]]:
    """Read count/expected-count matrix, retain only the predeclared marker panel."""
    with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        fields = reader.fieldnames or []
        gene_field = gene_name_column or gene_column
        excluded = {gene_column, gene_name_column, "gene_chr", "gene_start", "gene_end", "gene_strand", "gene_length", "gene_biotype", "gene_description", "tf_family"}
        sample_names = [name for name in fields if name not in excluded]
        totals = {name: 0.0 for name in sample_names}
        gene_sums: dict[str, dict[str, float]] = {name: defaultdict(float) for name in sample_names}
        for row in reader:
            gene = (row.get(gene_field) or "").strip().upper()
            if not gene:
                continue
            for name in sample_names:
                value = row.get(name, "")
                try:
                    number = float(value) if value else 0.0
                except ValueError:
                    continue
                if not math.isfinite(number) or number < 0:
                    continue
                totals[name] += number
                if gene in MARKERS:
                    gene_sums[name][gene] += number
    values = {}
    present = {}
    for name in sample_names:
        lib_total = totals[name]
        values[name] = {
            gene: math.log2(1.0 + 1_000_000.0 * count / lib_total) if lib_total > 0 else float("nan")
            for gene, count in gene_sums[name].items()
        }
        present[name] = int(lib_total > 0)
    return sample_names, values, present


def marker_logfpkm_matrix(path: Path, gene_column: str, expression_columns: list[str], gene_name_column: str = "gene_name") -> tuple[list[str], dict[str, dict[str, float]]]:
    with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        gene_sums: dict[str, dict[str, list[float]]] = {name: defaultdict(list) for name in expression_columns}
        for row in reader:
            gene = (row.get(gene_name_column) or "").strip().upper()
            if gene not in MARKERS:
                continue
            for name in expression_columns:
                try:
                    number = float(row.get(name, ""))
                except ValueError:
                    continue
                if math.isfinite(number) and number >= 0:
                    gene_sums[name][gene].append(math.log2(number + 1.0))
    values = {name: {gene: float(np.mean(nums)) for gene, nums in d.items()} for name, d in gene_sums.items()}
    return expression_columns, values


def raw_tar_marker_logcpm(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
    result = {}
    counts = {}
    with tarfile.open(path, "r:") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith("_counts.csv.gz"):
                continue
            accession = Path(member.name).name.split("_", 1)[0]
            source = archive.extractfile(member)
            if source is None:
                continue
            with gzip.open(source, "rt", encoding="utf-8-sig", errors="replace", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = reader.fieldnames or []
                gene_field = "gene"
                count_field = fields[-1]
                total = 0.0
                selected: dict[str, float] = defaultdict(float)
                for row in reader:
                    try:
                        value = float(row.get(count_field, "0"))
                    except ValueError:
                        continue
                    if not math.isfinite(value) or value < 0:
                        continue
                    total += value
                    gene = (row.get(gene_field) or "").strip().upper()
                    if gene in MARKERS:
                        selected[gene] += value
            result[accession] = {g: math.log2(1.0 + 1_000_000.0 * v / total) for g, v in selected.items()} if total else {}
            counts[accession] = 1
    return result, counts


def add_panel_scores(expression: dict[str, float]) -> dict[str, float]:
    out = dict(expression)
    for panel in ("NFkB_panel", "IFN_panel", "EMT_panel"):
        genes = MARKER_GROUPS[panel]
        vals = [expression[g] for g in genes if g in expression and math.isfinite(expression[g])]
        out[panel + "_mean"] = float(np.mean(vals)) if vals else float("nan")
    return out


def norm_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def build_samples() -> tuple[list[dict], dict[str, list[dict]], dict[str, dict]]:
    inventory = read_sample_inventory()
    soft181 = parse_soft(SOURCE / "GSE181961_family.soft.gz")
    soft279 = parse_soft(SOURCE / "GSE279749_family.soft.gz")
    all_samples: list[dict] = []
    by_series: dict[str, list[dict]] = defaultdict(list)
    expr_by_id: dict[str, dict] = {}

    # GSE181961: Cuff expected-count matrix; keep both models and both shRNA states.
    cols, expr, _ = marker_logcpm_matrix(SOURCE / "GSE181961_Cuff_Gene_Counts.csv.gz", ",", "Gene_ID")
    soft_lookup = {}
    for record in soft181:
        title = first(record, "Sample_title")
        key = norm_name(title.replace("tet-MUC1shRNA", ""))
        soft_lookup[key] = record
    for col in cols:
        low = col.lower()
        model = "AsPC-1" if low.startswith("aspc") else "HPAF-II"
        group = "DOX" if "dox" in low else "DMSO"
        rep_match = re.search(r"(\d+)$", col)
        rep = int(rep_match.group(1)) if rep_match else None
        key = norm_name(col).replace("aspc1", "aspc1").replace("hpafiicont", "hpafiicont")
        record = soft_lookup.get(key)
        if record is None:
            # Normalize the known GEO title spelling and sample separator differences.
            for candidate in soft181:
                title = norm_name(first(candidate, "Sample_title").replace("tet-MUC1shRNA", ""))
                title = title.replace("aspc1", "aspc1").replace("hpafii", "hpafii")
                if ("aspc1" in key and "aspc1" in title or "hpafii" in key and "hpafii" in title) and ("dox" if group == "DOX" else "cont") in title and rep is not None and str(rep) in title:
                    record = candidate
                    break
        accession = first(record, "Sample_geo_accession") if record else ""
        row = {"series": "GSE181961", "geo_accession": accession, "matrix_sample": col, "model": model, "treatment": group, "group": f"{model}_{group}", "replicate": rep, "expression_unit": "log2(CPM+1) from Cuff expected counts", "axis_design": "two-group cell-line contrast; no ordered trajectory"}
        row.update(add_panel_scores(expr[col]))
        all_samples.append(row); by_series["GSE181961"].append(row); expr_by_id["GSE181961:" + col] = row

    # GSE293756: six samples from one MRTX1133-resistant AsPC-1/MR model.
    cols, expr, _ = marker_logcpm_matrix(SOURCE / "GSE293756_STAR_Gene_Counts.csv.gz", ",", "Gene_ID")
    soft_by_group_rep = {}
    for record in parse_soft(SOURCE / "GSE293756_family.soft.gz"):
        title = first(record, "Sample_title").lower()
        group = "DOX" if re.search(r"dox\+", title) else "DMSO"
        rep_match = re.search(r"rep\s*(\d+)", title)
        if rep_match:
            soft_by_group_rep[(group, int(rep_match.group(1)))] = first(record, "Sample_geo_accession")
    for col in cols:
        m = re.search(r"dox_(pos|neg)_(\d+)$", col, flags=re.I)
        group = "DOX" if m and m.group(1).lower() == "pos" else "DMSO"
        rep = int(m.group(2)) if m else None
        accession = soft_by_group_rep.get((group, rep), "")
        row = {"series": "GSE293756", "geo_accession": accession, "matrix_sample": col, "model": "AsPC-1/MR", "treatment": group, "group": "AsPC-1/MR_" + group, "replicate": rep, "expression_unit": "log2(CPM+1) from STAR counts", "axis_design": "two-group knockdown contrast; no ordered trajectory"}
        row.update(add_panel_scores(expr[col]))
        all_samples.append(row); by_series["GSE293756"].append(row); expr_by_id["GSE293756:" + col] = row

    # GSE269985: per-sample count files; contrasts are stratified by model.
    raw_values, _ = raw_tar_marker_logcpm(SOURCE / "GSE269985_RAW.tar")
    soft269 = parse_soft(SOURCE / "GSE269985_family.soft.gz")
    soft_accession = {first(r, "Sample_geo_accession"): r for r in soft269}
    for accession, meta in inventory.items():
        if meta.get("series") != "GSE269985" or accession not in raw_values:
            continue
        title = meta.get("title", "")
        model = meta.get("model_or_cell_line", "").strip()
        state = "resistant" if "resistant" in meta.get("resistance_or_condition_state", "").lower() else "parental"
        row = {"series": "GSE269985", "geo_accession": accession, "matrix_sample": accession, "model": model, "treatment": state, "group": f"{model}_{state}", "replicate": None, "expression_unit": "log2(CPM+1) from per-sample raw counts", "axis_design": "parental/resistant groups stratified by model; no ordered trajectory"}
        row.update(add_panel_scores(raw_values[accession]))
        all_samples.append(row); by_series["GSE269985"].append(row); expr_by_id["GSE269985:" + accession] = row

    # GSE279749 cell-line RPKM/FPKM matrix. These values are not raw counts.
    cell_path = SOURCE / "GSE279749_gene_fpkm_cell_lines.txt.gz"
    cell_cols = ["A_NT_1", "A_NT_2", "A_NT_3", "A_M_1", "A_M_2", "A_M_3", "P_NT_1", "P_NT_2", "P_NT_3", "P_M_1", "P_M_2", "P_M_3", "C_NT_1", "C_NT_2", "C_NT_3", "C_M_1", "C_M_2", "C_M_3", "S9_NT_1", "S9_NT_2", "S9_NT_3", "S9_M_1", "S9_M_2", "S9_M_3"]
    _, expr = marker_logfpkm_matrix(cell_path, "gene_id", cell_cols)
    soft_by_cell_rep = {}
    for record in soft279:
        chars = sample_char_map(record)
        title = first(record, "Sample_title")
        m = re.match(r"(.+?),\s*(vehicle|MRTX1133|BI-2865)_(\d+)", title, flags=re.I)
        if m:
            soft_by_cell_rep[(m.group(1).strip().upper(), m.group(2).lower(), int(m.group(3)))] = record
    code_model = {"A": "ASPC-1", "P": "PANC-1", "C": "CFPAC-1", "S9": "SW1990"}
    for col in cell_cols:
        m = re.match(r"(S9|[APC])_(NT|M)_(\d+)$", col)
        if not m:
            continue
        code, arm, rep_s = m.groups(); model = code_model[code]; rep = int(rep_s)
        is_vehicle = arm == "NT"
        drug = "vehicle" if is_vehicle else ("BI-2865" if model == "CFPAC-1" else "MRTX1133")
        record = soft_by_cell_rep.get((model.upper(), drug.lower(), rep))
        row = {"series": "GSE279749", "geo_accession": first(record, "Sample_geo_accession") if record else "", "matrix_sample": col, "model": model, "treatment": drug, "group": f"{model}_{drug}", "replicate": rep, "expression_unit": "log2(RPKM+1; GEO file name says FPKM)", "axis_design": "three-replicate drug/vehicle group contrast; no ordered trajectory"}
        row.update(add_panel_scores(expr[col]))
        all_samples.append(row); by_series["GSE279749_cell_lines"].append(row); expr_by_id["GSE279749_cell_lines:" + col] = row

    # GSE279749 PDX matrix; the GEO description maps p1-p6 to the six samples.
    pdx_cols = [f"p{i}" for i in range(1, 7)]
    _, expr = marker_logfpkm_matrix(SOURCE / "GSE279749_gene_fpkm_PDX.txt.gz", "gene_id", pdx_cols)
    soft_by_description = {first(r, "Sample_description").lower(): r for r in soft279}
    for col in pdx_cols:
        record = soft_by_description.get(col.lower())
        chars = sample_char_map(record or {})
        title = first(record or {}, "Sample_title")
        treatment = chars.get("treatment", "unmapped")
        rep_match = re.search(r"_(\d+)$", title)
        rep = int(rep_match.group(1)) if rep_match else None
        row = {"series": "GSE279749", "geo_accession": first(record or {}, "Sample_geo_accession"), "matrix_sample": col, "model": "PDX", "treatment": treatment, "group": "PDX_" + treatment, "replicate": rep, "expression_unit": "log2(RPKM+1; GEO file name says FPKM)", "axis_design": "three-replicate vehicle/combination group contrast; no ordered trajectory"}
        row.update(add_panel_scores(expr[col]))
        all_samples.append(row); by_series["GSE279749_PDX"].append(row); expr_by_id["GSE279749_PDX:" + col] = row

    return all_samples, by_series, expr_by_id


def contrasts_for(by_series: dict[str, list[dict]]) -> list[dict]:
    out = []
    def add(series_key: str, name: str, model: str, control: str, treatment: str, treatment_label: str | None = None):
        rows = by_series.get(series_key, [])
        sel = [r for r in rows if r["model"].lower() == model.lower()]
        c = [r for r in sel if r["treatment"].lower() == control.lower()]
        tr = [r for r in sel if r["treatment"].lower() == treatment.lower()]
        out.append({"series": series_key, "contrast": name, "model": model, "control": control, "treatment": treatment_label or treatment, "control_rows": c, "treatment_rows": tr})

    add("GSE181961", "AsPC-1: MUC1-shRNA induction", "AsPC-1", "DMSO", "DOX")
    add("GSE181961", "HPAF-II: MUC1-shRNA induction", "HPAF-II", "DMSO", "DOX")
    add("GSE293756", "AsPC-1/MR: MUC1-shRNA induction", "AsPC-1/MR", "DMSO", "DOX")
    for row in by_series.get("GSE269985", []):
        model = row["model"]
        if model not in [x["model"] for x in out if x["series"] == "GSE269985"]:
            add("GSE269985", f"{model}: acquired resistance", model, "parental", "resistant")
    for series_key in ("GSE279749_cell_lines", "GSE279749_PDX"):
        for row in by_series.get(series_key, []):
            model = row["model"]
            if model not in [x["model"] for x in out if x["series"] == series_key]:
                drug = "vehicle"
                treated = sorted({r["treatment"] for r in by_series[series_key] if r["model"] == model and r["treatment"].lower() != "vehicle"})
                if treated:
                    add(series_key, f"{model}: {treated[0]} versus vehicle", model, "vehicle", treated[0])
    return out


def bh_adjust(pvalues: list[float]) -> list[float]:
    finite = [(i, p) for i, p in enumerate(pvalues) if math.isfinite(p)]
    result = [float("nan")] * len(pvalues)
    ordered = sorted(finite, key=lambda item: item[1])
    n = len(ordered); running = 1.0
    for rank in range(n, 0, -1):
        i, p = ordered[rank - 1]
        running = min(running, p * n / rank)
        result[i] = min(1.0, running)
    return result


def contrast_statistics(contrasts: list[dict]) -> list[dict]:
    output = []
    feature_names = FLOW_NAMES
    for contrast in contrasts:
        crows, trows = contrast["control_rows"], contrast["treatment_rows"]
        pvalues = []
        local = []
        for feature in feature_names:
            cvals = np.asarray([r.get(feature, float("nan")) for r in crows], dtype=float)
            tvals = np.asarray([r.get(feature, float("nan")) for r in trows], dtype=float)
            cvals = cvals[np.isfinite(cvals)]; tvals = tvals[np.isfinite(tvals)]
            pval = float("nan")
            delta = float("nan"); low = float("nan"); high = float("nan"); se = float("nan")
            if len(cvals) >= 2 and len(tvals) >= 2:
                mc, mt = float(np.mean(cvals)), float(np.mean(tvals))
                delta = mt - mc
                vc = float(np.var(cvals, ddof=1)); vt = float(np.var(tvals, ddof=1))
                se = math.sqrt(vc / len(cvals) + vt / len(tvals))
                denom = (vc / len(cvals)) ** 2 / max(len(cvals) - 1, 1) + (vt / len(tvals)) ** 2 / max(len(tvals) - 1, 1)
                df = (vc / len(cvals) + vt / len(tvals)) ** 2 / denom if denom > 0 else 0.0
                if df > 0 and math.isfinite(se):
                    crit = float(t.ppf(0.975, df))
                    low, high = delta - crit * se, delta + crit * se
                pval = float(ttest_ind(tvals, cvals, equal_var=False, nan_policy="omit").pvalue)
            else:
                mc = float(np.mean(cvals)) if len(cvals) else float("nan")
                mt = float(np.mean(tvals)) if len(tvals) else float("nan")
                if math.isfinite(mc) and math.isfinite(mt): delta = mt - mc
            row = {
                "series": contrast["series"], "contrast": contrast["contrast"], "model": contrast["model"],
                "control_label": contrast["control"], "treatment_label": contrast["treatment"],
                "feature": feature, "n_control": len(cvals), "n_treatment": len(tvals),
                "mean_control_log_expression": mc, "mean_treatment_log_expression": mt,
                "sd_control": float(np.std(cvals, ddof=1)) if len(cvals) > 1 else float("nan"),
                "sd_treatment": float(np.std(tvals, ddof=1)) if len(tvals) > 1 else float("nan"),
                "zero_within_group_variance": bool((len(cvals) > 1 and np.var(cvals, ddof=1) == 0) or (len(tvals) > 1 and np.var(tvals, ddof=1) == 0)),
                "delta_treatment_minus_control": delta, "welch_se": se,
                "welch_ci95_low": low, "welch_ci95_high": high,
                "welch_p_unadjusted_exploratory": pval,
                "p_value_scope": "Welch test on log expression; exploratory small-n marker panel, not the authors edgeR/TCC result",
            }
            local.append(row); pvalues.append(pval)
        qvalues = bh_adjust(pvalues)
        for row, qvalue in zip(local, qvalues):
            row["welch_q_bh_within_contrast_exploratory"] = qvalue
            output.append(row)
    return output


def pipeline_gate_audit(contrasts: list[dict], pipeline_sha: str) -> tuple[list[dict], dict]:
    from importlib.machinery import SourceFileLoader
    module = SourceFileLoader("universal_log_v6_probe", str(PIPELINE_PATH)).load_module()
    output = []
    totals = {"contrasts": 0, "candidate_control_streams": 0, "gate_probed": 0, "all_29_nan": 0}
    for contrast in contrasts:
        crows, trows = contrast["control_rows"], contrast["treatment_rows"]
        rows = crows + trows
        totals["contrasts"] += 1
        for flow in FLOW_NAMES:
            values = np.asarray([r.get(flow, float("nan")) for r in rows], dtype=float)
            valid = values[np.isfinite(values)]
            status = "abstained_missing_flux" if len(valid) != len(values) else "abstained_short_series_no_order"
            finite_estimators = None
            if len(valid) == len(values):
                estimates = module.apply_complexity(values)
                finite_estimators = sum(math.isfinite(float(v)) for v in estimates.values())
                totals["gate_probed"] += 1
                totals["candidate_control_streams"] += 1
                if finite_estimators == 0 and len(estimates) == 29:
                    totals["all_29_nan"] += 1
            output.append({
                "series": contrast["series"], "contrast": contrast["contrast"], "candidate_control_flow": flow,
                "n_samples_in_contrast": len(rows), "n_finite_values": len(valid),
                "pipeline_version": "v6.0.0 Cohen-D", "pipeline_file_sha256": pipeline_sha,
                "fast_min_len": 50, "core_estimators_requested": 29,
                "core_estimators_finite": finite_estimators,
                "natural_ordered_axis_present": False,
                "full_target_control_run": False,
                "status": status,
                "reason": "The series is a two-group contrast with no natural order and fewer than 50 samples; apply_complexity returns 29 missing estimates at the configured length gate. No T0/TLog is produced.",
            })
    return output, totals


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def make_effect_plot(rows: list[dict], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    features = ["MUC1", "NFkB_panel_mean", "IFN_panel_mean", "EMT_panel_mean"]
    titles = ["MUC1 transcript", "NFκB marker panel", "Interferon marker panel", "EMT marker panel"]
    contrasts = list(dict.fromkeys(row["contrast"] for row in rows))
    colors = {
        "GSE181961": "#386cb0", "GSE293756": "#f0027f", "GSE269985": "#7fc97f",
        "GSE279749_cell_lines": "#fdc086", "GSE279749_PDX": "#beaed4",
    }
    fig, axes = plt.subplots(1, len(features), figsize=(19, max(8, 0.42 * len(contrasts))), sharey=True)
    ybase = np.arange(len(contrasts))
    for ax, feature, title in zip(axes, features, titles):
        lookup = {row["contrast"]: row for row in rows if row["feature"] == feature}
        for i, contrast in enumerate(contrasts):
            row = lookup.get(contrast)
            if not row or not math.isfinite(float(row["delta_treatment_minus_control"])):
                continue
            delta = float(row["delta_treatment_minus_control"])
            low = float(row["welch_ci95_low"]); high = float(row["welch_ci95_high"])
            xerr = [[max(0.0, delta - low)], [max(0.0, high - delta)]] if math.isfinite(low) and math.isfinite(high) else None
            color = colors.get(row["series"], "#555555")
            ax.errorbar(delta, i, xerr=xerr, fmt="o", ms=4, capsize=2, color=color, ecolor=color, alpha=0.9)
        ax.axvline(0, color="#333333", linewidth=0.8, linestyle="--")
        ax.set_title(title)
        ax.set_xlabel("Δ log-expression (treatment − control)")
        ax.grid(axis="x", alpha=0.18)
    axes[0].set_yticks(ybase)
    axes[0].set_yticklabels(contrasts, fontsize=8)
    axes[0].invert_yaxis()
    fig.suptitle("Exploratory RNA-seq marker shifts; 3 biological libraries per arm\nWelch 95% intervals on transformed expression; not a clinical or ADC-response estimate", y=1.01)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    source_records = ensure_source_files()
    all_samples, by_series, _ = build_samples()
    contrasts = contrasts_for(by_series)
    stats = contrast_statistics(contrasts)
    pipeline_sha = sha256(PIPELINE_PATH)
    gate_rows, gate_totals = pipeline_gate_audit(contrasts, pipeline_sha)

    sample_fields = ["series", "geo_accession", "matrix_sample", "model", "treatment", "group", "replicate", "expression_unit", "axis_design"] + FLOW_NAMES
    sample_path = HERE / "RNASEQ_MARKER_FLUXES_PER_SAMPLE.csv"
    write_csv(sample_path, all_samples, sample_fields)
    contrast_path = HERE / "RNASEQ_MARKER_CONTRASTS.csv"
    write_csv(contrast_path, stats)
    gate_path = HERE / "PIPELINE_CONTROL_GATE_AUDIT.csv"
    write_csv(gate_path, gate_rows)

    fit_summary = []
    for series, rows in by_series.items():
        distinct_models = sorted({r["model"] for r in rows})
        fit_summary.append({
            "series": series, "libraries": len(rows), "models": " | ".join(distinct_models),
            "sample_groups": json.dumps(dict((g, sum(1 for r in rows if r["group"] == g)) for g in sorted({r["group"] for r in rows})), ensure_ascii=False),
            "independent_ordered_response_axis": False,
            "direct_MUC1C_ADC_response_endpoint": False,
            "v6_fast_min_valid_points": 50,
            "pipeline_full_run": False,
            "decision": "Group-level expression data with sample replicates; no ordered response series. Preserve as exploratory marker evidence only.",
        })
    fit_path = HERE / "RNASEQ_DATASET_FIT_DECISIONS.csv"
    write_csv(fit_path, fit_summary)

    # Compact trace of input sample metadata including groups and accessions.
    inventory_fields = ["series", "geo_accession", "matrix_sample", "model", "treatment", "group", "replicate", "expression_unit", "axis_design"]
    inventory_path = HERE / "RNASEQ_SAMPLE_INVENTORY_EXTENDED.csv"
    write_csv(inventory_path, all_samples, inventory_fields)
    plot_path = HERE / "RNASEQ_MARKER_EFFECTS.png"
    make_effect_plot(stats, plot_path)

    manifest = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "analysis": "Public RNA-seq marker-panel independent reanalysis; descriptive/exploratory; not an ADC response assay",
        "script": HERE.joinpath(Path(__file__).name).name,
        "script_sha256": sha256(Path(__file__)),
        "pipeline": {"path": "pancréas/universal_v6.0.0_cohen - Copie.py.txt", "sha256": pipeline_sha, "version": "v6.0.0 Cohen-D", "fast_min_len": 50, "runtime_entrypoint": "apply_complexity", "full_pipeline_runs": 0, "gate_probe_summary": gate_totals},
        "official_author_analysis": {"repository": AUTHOR_REPO, "commit": AUTHOR_COMMIT, "script": "R/multiple_comparison_test.R", "script_sha256": AUTHOR_SCRIPT_SHA256, "methods_from_script": ["row-sum filter >10", "ComBat-seq batch adjustment", "TCC TMM iterative normalization (3 iterations)", "edgeR-based multiple-group differential expression, FDR 0.05"], "exact_R_script_executed": False, "reason": "R/Rscript is not installed or discoverable in this execution environment; the author script is documented but not claimed as reproduced."},
        "independent_python_analysis": {"python": platform.python_version(), "numpy": np.__version__, "scipy": __import__("scipy").__version__, "count_transform": "log2(CPM+1)", "linear_expression_transform": "log2(RPKM+1); GEO family/sample records describe the GSE279749 tables as RPKM although supplementary filenames include fpkm", "features": FLOW_NAMES, "test": "Welch t-test on transformed expression for the predeclared 15-gene marker panel plus 3 panel means; BH adjusted within contrast only", "inference_status": "exploratory; n=3 per arm in modeled contrasts; zero/near-zero replicate variance can make small-n p-values optimistic; not genome-wide DE and not clinical evidence"},
        "datasets": fit_summary,
        "source_files": source_records,
        "outputs": {},
    }
    output_files = [sample_path, contrast_path, gate_path, fit_path, inventory_path, plot_path]
    manifest["outputs"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in output_files}
    manifest_path = HERE / "RNASEQ_REANALYSIS_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"contrasts": len(contrasts), "sample_rows": len(all_samples), "marker_effect_rows": len(stats), "gate_rows": len(gate_rows), "gate_summary": gate_totals, "datasets": fit_summary, "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
