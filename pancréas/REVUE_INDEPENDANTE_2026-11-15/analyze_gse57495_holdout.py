#!/usr/bin/env python
"""Run the frozen CEACAM5/KRAS holdout analysis for GEO GSE57495.

All gene selection, sample inclusion, probe aggregation, tests and resampling
settings are defined in PROTOCOLE_HOLDOUT_GSE57495.md. This script does not
import or call UNIVERSAL_LOG/TLog.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import rankdata, spearmanr


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data_GSE57495"
MATRIX_PATH = DATA_DIR / "GSE57495_series_matrix.txt.gz"
PLATFORM_PATH = DATA_DIR / "GPL15048_official_geo.txt"
PROTOCOL_PATH = ROOT / "PROTOCOLE_HOLDOUT_GSE57495.md"
SAMPLE_OUTPUT = DATA_DIR / "GSE57495_holdout_sample_data.csv"
BOOTSTRAP_OUTPUT = DATA_DIR / "GSE57495_bootstrap_rho.csv"
PERMUTATION_OUTPUT = DATA_DIR / "GSE57495_permutation_rho.npz"
FIGURE_OUTPUT = DATA_DIR / "GSE57495_holdout_results.png"
RESULT_JSON = DATA_DIR / "GSE57495_holdout_results.json"
REPORT_PATH = ROOT / "RESULTATS_HOLDOUT_GSE57495.md"
MANIFEST_PATH = DATA_DIR / "GSE57495_holdout_manifest.json"

SEED = 20261115
N_PERMUTATIONS = 100_000
N_BOOTSTRAPS = 10_000
ALPHA = 0.05
ACINAR_GENES = [
    "PNLIP", "CTRB2", "CELA3A", "CTRB1", "CPA1", "CELA2A",
    "CPB1", "CELA3B", "CLPS", "CTRC", "CPA2",
]
ISLET_GENES = ["INS", "GCG", "PPY", "SST"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_series_metadata(path: Path) -> tuple[list[str], list[str], dict[str, list[str]]]:
    metadata: dict[str, list[str]] = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        for line in handle:
            if line.startswith("!series_matrix_table_begin"):
                break
            if line.startswith(("!Sample_geo_accession", "!Sample_title", "!Sample_source_name_ch1")):
                fields = next(csv.reader([line], delimiter="\t"))
                metadata[fields[0]] = [value.strip().strip('"') for value in fields[1:]]
    ids = metadata.get("!Sample_geo_accession", [])
    titles = metadata.get("!Sample_title", [])
    if not ids or len(ids) != len(titles):
        raise ValueError("GEO sample IDs/titles are missing or have unequal lengths")
    return ids, titles, metadata


def read_matrix(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        lines = []
        in_table = False
        for line in handle:
            if line.startswith("!series_matrix_table_begin"):
                in_table = True
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if in_table:
                lines.append(line)
    if not lines:
        raise ValueError("No GEO expression table found")
    frame = pd.read_csv(io.StringIO("".join(lines)), sep="\t", index_col=0)
    frame.index = frame.index.astype(str).str.strip().str.strip('"')
    frame.columns = frame.columns.astype(str).str.strip().str.strip('"')
    frame = frame.apply(pd.to_numeric, errors="coerce")
    return frame


def read_platform_table(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    try:
        begin = lines.index("!platform_table_begin") + 1
        end = lines.index("!platform_table_end", begin)
    except ValueError as exc:
        raise ValueError("Official GEO platform table markers are missing") from exc
    annotation = pd.read_csv(io.StringIO("\n".join(lines[begin:end])), sep="\t", dtype=str, keep_default_na=False)
    required = {"ID", "GeneSymbol"}
    if not required.issubset(annotation.columns):
        raise ValueError(f"Platform annotation lacks required columns: {required - set(annotation.columns)}")
    annotation["ID"] = annotation["ID"].str.strip()
    annotation["GeneSymbol"] = annotation["GeneSymbol"].str.strip()
    return annotation


def pearson_of_ranks(x: np.ndarray, y: np.ndarray) -> float:
    rx = rankdata(x, method="average").astype(float)
    ry = rankdata(y, method="average").astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    denominator = np.sqrt(np.dot(rx, rx) * np.dot(ry, ry))
    return float(np.dot(rx, ry) / denominator) if denominator else float("nan")


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    sample_ids, sample_titles, metadata = parse_series_metadata(MATRIX_PATH)
    matrix = read_matrix(MATRIX_PATH)
    annotation = read_platform_table(PLATFORM_PATH)

    if matrix.index.has_duplicates:
        duplicate_probe_rows = int(matrix.index.duplicated(keep=False).sum())
    else:
        duplicate_probe_rows = 0
    if len(annotation["ID"]) != len(annotation["ID"].drop_duplicates()):
        raise ValueError("Platform probe IDs are not unique; refusing implicit annotation joins")
    if not set(sample_ids).issubset(set(matrix.columns)):
        missing = sorted(set(sample_ids) - set(matrix.columns))
        raise ValueError(f"Series matrix columns do not match GEO sample metadata: {missing}")
    matrix = matrix.loc[:, sample_ids]

    symbols = annotation.set_index("ID")["GeneSymbol"].reindex(matrix.index).fillna("")
    # The protocol excludes rows with zero or multiple symbols. Whitespace is
    # the delimiter used by the official GPL15048 GeneSymbol field.
    unambiguous = symbols.map(lambda value: len(value.split()) == 1)
    mapped = matrix.loc[unambiguous].copy()
    mapped["__gene_symbol"] = symbols.loc[unambiguous].to_numpy()
    gene_expression = mapped.groupby("__gene_symbol", sort=True).median(numeric_only=True)

    absent_targets = [gene for gene in ("CEACAM5", "KRAS") if gene not in gene_expression.index]
    if absent_targets:
        raise ValueError(f"Primary target genes are not uniquely mapped: {absent_targets}")
    x = gene_expression.loc["CEACAM5"].to_numpy(dtype=float)
    y = gene_expression.loc["KRAS"].to_numpy(dtype=float)
    complete = np.isfinite(x) & np.isfinite(y)
    x, y = x[complete], y[complete]
    used_ids = [sample_ids[i] for i, ok in enumerate(complete) if ok]
    used_titles = [sample_titles[i] for i, ok in enumerate(complete) if ok]
    n = len(x)
    if n < 3:
        raise ValueError(f"Only {n} complete target pairs are available")

    rho = float(spearmanr(x, y).statistic)
    rng = np.random.default_rng(SEED)
    rank_x = rankdata(x, method="average").astype(float)
    rank_y = rankdata(y, method="average").astype(float)
    centered_x = rank_x - rank_x.mean()
    centered_y = rank_y - rank_y.mean()
    denominator = np.sqrt(np.dot(centered_x, centered_x) * np.dot(centered_y, centered_y))
    permutation_rhos = np.empty(N_PERMUTATIONS, dtype=np.float64)
    chunk_size = 2_000
    cursor = 0
    while cursor < N_PERMUTATIONS:
        count = min(chunk_size, N_PERMUTATIONS - cursor)
        order = np.argsort(rng.random((count, n)), axis=1)
        permuted_y = rank_y[order]
        permutation_rhos[cursor:cursor + count] = (permuted_y - rank_y.mean()) @ centered_x / denominator
        cursor += count
    p_permutation = float((1 + np.count_nonzero(permutation_rhos >= rho)) / (N_PERMUTATIONS + 1))

    bootstrap_rhos = np.empty(N_BOOTSTRAPS, dtype=np.float64)
    for index in range(N_BOOTSTRAPS):
        draws = rng.integers(0, n, size=n)
        bootstrap_rhos[index] = pearson_of_ranks(x[draws], y[draws])
    bootstrap_rhos = bootstrap_rhos[np.isfinite(bootstrap_rhos)]
    ci_low, ci_high = np.quantile(bootstrap_rhos, [0.025, 0.975])

    acinar_present = [gene for gene in ACINAR_GENES if gene in gene_expression.index]
    islet_present = [gene for gene in ISLET_GENES if gene in gene_expression.index]
    partial_result: dict[str, object] = {
        "defined_by_protocol": "rank residual correlation controlling the two fixed rank scores",
        "acinar_genes_present": acinar_present,
        "acinar_genes_absent": [gene for gene in ACINAR_GENES if gene not in gene_expression.index],
        "islet_genes_present": islet_present,
        "islet_genes_absent": [gene for gene in ISLET_GENES if gene not in gene_expression.index],
        "status": "omitted: fewer than 3 acinar genes or fewer than 2 islet genes measured",
        "rho_partial": None,
    }
    if len(acinar_present) >= 3 and len(islet_present) >= 2:
        acinar_score = gene_expression.loc[acinar_present].median(axis=0).to_numpy(dtype=float)[complete]
        islet_score = gene_expression.loc[islet_present].median(axis=0).to_numpy(dtype=float)[complete]
        controls = np.column_stack((rankdata(acinar_score, method="average"), rankdata(islet_score, method="average")))
        design = np.column_stack((np.ones(n), controls))
        rank_x_all = rankdata(x, method="average")
        rank_y_all = rankdata(y, method="average")
        resid_x = rank_x_all - design @ np.linalg.lstsq(design, rank_x_all, rcond=None)[0]
        resid_y = rank_y_all - design @ np.linalg.lstsq(design, rank_y_all, rcond=None)[0]
        partial_rho = float(np.corrcoef(resid_x, resid_y)[0, 1])
        partial_result["rho_partial"] = partial_rho
        partial_result["status"] = "computed"

    target_probe_ids: dict[str, list[str]] = {}
    for target in ("CEACAM5", "KRAS"):
        target_probe_ids[target] = annotation.loc[annotation["GeneSymbol"].eq(target), "ID"].tolist()
    proxy_probe_counts: dict[str, int] = {}
    for gene in ACINAR_GENES + ISLET_GENES:
        proxy_probe_counts[gene] = int(annotation["GeneSymbol"].eq(gene).sum())

    sample_frame = pd.DataFrame({
        "geo_sample_id": used_ids,
        "sample_title": used_titles,
        "CEACAM5_median_probe_expression": x,
        "KRAS_median_probe_expression": y,
    })
    for gene in sorted(set(acinar_present + islet_present)):
        sample_frame[f"{gene}_expression"] = gene_expression.loc[gene, used_ids].to_numpy(dtype=float)
    if len(acinar_present) >= 3:
        sample_frame["acinar_proxy_median"] = gene_expression.loc[acinar_present, used_ids].median(axis=0).to_numpy(dtype=float)
    if len(islet_present) >= 2:
        sample_frame["islet_proxy_median"] = gene_expression.loc[islet_present, used_ids].median(axis=0).to_numpy(dtype=float)
    sample_frame.to_csv(SAMPLE_OUTPUT, index=False, float_format="%.10g", encoding="utf-8")
    pd.DataFrame({"bootstrap_rho": bootstrap_rhos}).to_csv(BOOTSTRAP_OUTPUT, index=False, float_format="%.10g", encoding="utf-8")
    np.savez_compressed(PERMUTATION_OUTPUT, permutation_rho=permutation_rhos)

    result: dict[str, object] = {
        "study": "GSE57495",
        "platform": "GPL15048",
        "n_in_series_matrix": len(sample_ids),
        "n_complete_pairs": n,
        "n_missing_target_pairs": len(sample_ids) - n,
        "sample_ids_used": used_ids,
        "primary": {
            "outcome": "Spearman correlation of CEACAM5 and KRAS transcript expression",
            "rho": rho,
            "permutation_p_one_sided_positive": p_permutation,
            "permutation_count": N_PERMUTATIONS,
            "bootstrap_ci_95_percentile": [float(ci_low), float(ci_high)],
            "bootstrap_count_requested": N_BOOTSTRAPS,
            "bootstrap_count_finite": int(len(bootstrap_rhos)),
            "decision_at_alpha_0_05": bool(rho > 0 and p_permutation < ALPHA and ci_low > 0),
        },
        "secondary_partial_rank": partial_result,
        "probe_ids_by_target_symbol": target_probe_ids,
        "proxy_probe_counts_by_gene": proxy_probe_counts,
        "annotation_counts": {
            "rows": int(len(annotation)),
            "unambiguous_probe_rows_used": int(unambiguous.sum()),
            "ambiguous_or_blank_probe_rows_excluded": int((~unambiguous).sum()),
            "matrix_probe_rows": int(len(matrix)),
            "duplicate_matrix_probe_rows": duplicate_probe_rows,
            "matrix_numeric_missing_cells": int(matrix.isna().sum().sum()),
        },
        "method": {
            "seed": SEED,
            "alpha": ALPHA,
            "permutation_p_formula": "(1 + count(permuted rho >= observed rho)) / (B + 1)",
            "bootstrap": "paired sample resampling with replacement; percentile 2.5% and 97.5% quantiles",
            "gene_probe_aggregation": "median across official GPL15048 probe rows with exactly one GeneSymbol",
        },
        "not_assessed": ["TLog", "UNIVERSAL_LOG change-point performance", "causality", "KRAS mutation status", "clinical utility"],
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    axes[0].scatter(x, y, s=42, alpha=0.8, color="#205493", edgecolor="white", linewidth=0.45)
    axes[0].set_xlabel("CEACAM5 (sondes: médiane, expression déposée)")
    axes[0].set_ylabel("KRAS (sondes: médiane, expression déposée)")
    axes[0].set_title(f"GSE57495 — n={n}, Spearman ρ={rho:.3f}")
    axes[0].grid(alpha=0.2)
    axes[1].hist(permutation_rhos, bins=55, color="#8ab4d6", edgecolor="white")
    axes[1].axvline(rho, color="#a61c2d", linewidth=2, label=f"ρ observé = {rho:.3f}")
    axes[1].set_xlabel("ρ après permutation des patients")
    axes[1].set_ylabel("Nombre de permutations")
    axes[1].set_title(f"Test unilatéral de permutation (p={p_permutation:.4g})")
    axes[1].legend(frameon=False)
    fig.suptitle("GSE57495 - analyse fixée avant lecture des valeurs d'expression", fontsize=13)
    fig.savefig(FIGURE_OUTPUT, dpi=180, facecolor="white")
    plt.close(fig)

    decision = result["primary"]["decision_at_alpha_0_05"]  # type: ignore[index]
    interpretation = (
        "Le critère directionnel préfixé est satisfait dans cette cohorte pour l'association d'expression ARN."
        if decision else
        "Le critère directionnel préfixé n'est pas satisfait dans cette cohorte; aucun seuil ou sous-groupe de remplacement n'a été essayé."
    )
    report = f"""# Résultats du test externe GSE57495

**Statut :** analyse exploratoire de cohorte tenue à l'écart des trois cohortes antérieures; cible choisie après exploration du projet. Elle ne constitue pas une confirmation préenregistrée avant toute analyse.

## Résultat primaire

- Cohorte : {len(sample_ids)} échantillons GEO; paires CEACAM5/KRAS complètes : **n={n}**.
- Expression : matrice GEO déposée; sondes réunies par médiane, uniquement quand l'annotation officielle GPL15048 donne un symbole unique.
- Sondes retenues : CEACAM5 `{', '.join(target_probe_ids['CEACAM5'])}`; KRAS `{', '.join(target_probe_ids['KRAS'])}`.
- Spearman : **ρ={rho:.4f}**; test de permutation unilatéral positif, **B={N_PERMUTATIONS:,}, p={p_permutation:.6g}**.
- IC percentile bootstrap 95 % (**{len(bootstrap_rhos):,}** rééchantillonnages finis) : **[{ci_low:.4f}, {ci_high:.4f}]**.
- Décision préfixée : **{'critère satisfait' if decision else 'critère non satisfait'}** (ρ>0, p<0,05 et borne basse IC>0).

**Conclusion mesurée :** {interpretation}

Cette association entre deux niveaux d'expression ARN ne montre ni mutation KRAS, ni relation causale, ni transition temporelle, ni performance de TLog/pipeline, ni utilité clinique.

## Analyse secondaire de composition

- Statut : **{partial_result['status']}**.
- Score acineux mesuré : {', '.join(acinar_present)}; absent : {', '.join(partial_result['acinar_genes_absent']) or 'aucun'}.
- Score d'îlots mesuré : {', '.join(islet_present)}; absent : {', '.join(partial_result['islet_genes_absent']) or 'aucun'}.
- Corrélation de rang partielle selon la définition préfixée : **{partial_result['rho_partial']}**.

Ce contrôle de composition est un proxy grossier, et non un ajustement complet de pureté tumorale. Il ne remplace pas le résultat primaire.

## Reproductibilité et périmètre

- Graine : `{SEED}`; permutation : `{N_PERMUTATIONS:,}`; bootstrap : `{N_BOOTSTRAPS:,}` demandé.
- Script : `analyze_gse57495_holdout.py`; environnement : `.venv` du projet.
- Données source et annotation officielles conservées dans `data_GSE57495/`; empreintes SHA-256 dans `data_GSE57495/GSE57495_holdout_manifest.json`.
- Table d'analyse par échantillon : `data_GSE57495/GSE57495_holdout_sample_data.csv`.
- Distributions de rééchantillonnage : `data_GSE57495/GSE57495_permutation_rho.npz`, `data_GSE57495/GSE57495_bootstrap_rho.csv`.
- Figure : `data_GSE57495/GSE57495_holdout_results.png`.
- Pas d'import ni d'appel à UNIVERSAL_LOG/TLog dans cette analyse.

## Limites préfixées

Cette étude est une cohorte publique de tumeurs congelées mesurées par microarray. Elle ne teste qu'une association transversale RNA/RNA. La sélection de CEACAM5/KRAS a été motivée par les analyses antérieures; les données ne sont donc pas totalement indépendantes du processus de sélection. Les chevauchements éventuels de patients entre GEO sont non vérifiés. L'annotation GPL15048 est celle fournie par GEO et sa nomenclature historique peut être imparfaite. Aucun résultat ne permet d'inférer l'état mutationnel de KRAS.

Source primaire : [GEO GSE57495](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE57495); annotation : [GEO GPL15048](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15048).
"""
    REPORT_PATH.write_text(report, encoding="utf-8")

    manifest = {
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256(Path(__file__).resolve()),
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "series_matrix": {
            "path": str(MATRIX_PATH.resolve()),
            "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE57nnn/GSE57495/matrix/GSE57495_series_matrix.txt.gz",
            "size_bytes": MATRIX_PATH.stat().st_size,
            "sha256": sha256(MATRIX_PATH),
        },
        "official_platform_annotation": {
            "path": str(PLATFORM_PATH.resolve()),
            "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15048&targ=self&form=text&view=full",
            "size_bytes": PLATFORM_PATH.stat().st_size,
            "sha256": sha256(PLATFORM_PATH),
        },
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {"numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
        "outputs": {path.name: sha256(path) for path in [SAMPLE_OUTPUT, BOOTSTRAP_OUTPUT, PERMUTATION_OUTPUT, FIGURE_OUTPUT, RESULT_JSON, REPORT_PATH]},
        "result_summary": {"n": n, "rho": rho, "p_permutation": p_permutation, "ci95": [float(ci_low), float(ci_high)]},
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"n": n, "rho": rho, "p_permutation": p_permutation, "ci95": [float(ci_low), float(ci_high)], "partial": partial_result["rho_partial"], "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
