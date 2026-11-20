from __future__ import annotations

"""Mouse-level audit reanalysis of the published GEO GSE271300 experiment.

The biological unit is the mouse, not the cell. PC69 sample labels are read
from the analyzed H5AD. PC106 vehicle cells are assigned using the dominant
vehicle HTO count in the matching QC H5AD; cell barcodes are required to match
exactly. MRTX cells use the study-provided Classification label. GA60 is kept
as pooled, cell-level descriptive context because no mouse label is present.

No TLog value is calculated: these are treatment-arm snapshots, not an ordered
longitudinal axis. Exact permutation p-values are conditional on exchangeability
of mouse-level labels and are exploratory due to very small sample sizes.
"""

import csv
import hashlib
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.sparse import csr_matrix


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_GSE271300"
OUT = ROOT / "results_mouse_level"
OUT.mkdir(exist_ok=True)
SOURCE_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300"
TARGET_PANEL = ("KRAS", "EGFR", "ERBB2", "ERBB3", "STAT3", "GATA6", "KRT19", "CEACAM5", "KRT5", "TP63")


def decode(value) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def read_obs_column(obs: h5py.Group, name: str) -> np.ndarray:
    item = obs[name]
    if isinstance(item, h5py.Group) and "codes" in item and "categories" in item:
        codes = np.asarray(item["codes"])
        categories = [decode(v) for v in np.asarray(item["categories"])]
        return np.asarray([categories[int(i)] if int(i) >= 0 else "" for i in codes], dtype=object)
    raw = np.asarray(item)
    return np.asarray([decode(v) for v in raw], dtype=object)


def read_numeric_column(obs: h5py.Group, name: str) -> np.ndarray:
    raw = read_obs_column(obs, name)
    out = np.full(len(raw), np.nan, dtype=float)
    for i, value in enumerate(raw):
        try:
            out[i] = float(value)
        except (ValueError, TypeError):
            pass
    return out


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_model(model: str) -> tuple[dict[str, list[dict]], dict]:
    analyzed_path = DATA / f"GSE271300_PDX_{model}_analyzed.h5ad"
    qc_path = DATA / f"GSE271300_PDX_{model}_QC.h5ad"
    animals: dict[str, list[dict]] = {}
    diagnostics: dict = {
        "model": model,
        "analyzed_file": analyzed_path.name,
        "qc_file": qc_path.name,
        "analyzed_sha256": sha256(analyzed_path),
        "qc_sha256": sha256(qc_path),
    }

    with h5py.File(analyzed_path, "r") as analyzed, h5py.File(qc_path, "r") as qc:
        aobs, qobs = analyzed["obs"], qc["obs"]
        a_ids = read_obs_column(aobs, "_index")
        a_treatment = read_obs_column(aobs, "treatment")
        a_classification = read_obs_column(aobs, "Classification") if "Classification" in aobs else np.full(len(a_ids), "", dtype=object)
        values: dict[str, np.ndarray] = {}
        for name in (
            "scBasalScore", "scClassicalScore", "EMTScore", "S_score",
            "G2M_score", "G1Score", "G2MScore", "cellState"
        ):
            if name in aobs:
                values[name] = read_numeric_column(aobs, name) if name != "cellState" else read_obs_column(aobs, name)

        if model == "PC106":
            q_ids = read_obs_column(qobs, "_index")
            if len(set(q_ids)) != len(q_ids):
                raise ValueError("PC106 QC cell IDs are not unique; refusing ambiguous join.")
            q_lookup = {cell_id: index for index, cell_id in enumerate(q_ids)}
            if not set(a_ids).issubset(q_lookup):
                raise ValueError("Some analyzed PC106 barcodes are absent from the QC file.")
            q_rows = np.asarray([q_lookup[cell_id] for cell_id in a_ids], dtype=int)
            diagnostics["analyzed_cells"] = int(len(a_ids))
            diagnostics["qc_cells"] = int(len(q_ids))
            diagnostics["exact_barcode_matches"] = int(len(q_rows))
            tag_names = [
                "PC106-ANS184-VEH-B0252",
                "PC106-ANS185-VEH-B0253",
                "PC106-ANS187-VEH-B0254",
            ]
            tag_matrix = np.column_stack([
                read_numeric_column(qobs, tag)[q_rows] for tag in tag_names
            ])
            argmax = np.argmax(tag_matrix, axis=1)
            sorted_tags = np.sort(tag_matrix, axis=1)
            top = sorted_tags[:, -1]
            second = sorted_tags[:, -2]
            ratio = top / np.maximum(second, 1.0)
            diagnostics["vehicle_tag_columns"] = tag_names
            diagnostics["vehicle_tag_argmax_counts"] = {
                tag_names[i]: int(np.sum((a_treatment == "veh") & (argmax == i)))
                for i in range(len(tag_names))
            }
            diagnostics["vehicle_cells_with_top_tag_at_least_2x_second"] = int(
                np.sum((a_treatment == "veh") & (ratio >= 2.0))
            )
            diagnostics["vehicle_cells_total"] = int(np.sum(a_treatment == "veh"))
            diagnostics["vehicle_tag_ratio_median"] = float(np.median(ratio[a_treatment == "veh"]))
        elif model == "PC69":
            q_rows = None
            tag_matrix = None
            argmax = None
            ratio = None
        else:
            raise ValueError(f"Unsupported model for mouse assignment: {model}")

        included = 0
        excluded = 0
        for i, treatment in enumerate(a_treatment):
            label = str(a_classification[i])
            if model == "PC69":
                if label in ("", "Doublet", "Negative"):
                    excluded += 1
                    continue
                animal = label
            elif treatment == "mrtx":
                if not label.startswith("PC106-") or "MRTX" not in label:
                    excluded += 1
                    continue
                animal = label
            elif treatment == "veh":
                if tag_matrix is None:
                    excluded += 1
                    continue
                animal = [
                    "PC106-ANS184-VEH-B0252",
                    "PC106-ANS185-VEH-B0253",
                    "PC106-ANS187-VEH-B0254",
                ][int(argmax[i])]
            else:
                excluded += 1
                continue

            if ("MRTX" in animal) != (treatment == "mrtx") and model == "PC69":
                raise ValueError(f"Treatment/classification mismatch at cell row {i}: {animal}, {treatment}")
            record = {
                "cell_id": str(a_ids[i]),
                "model": model,
                "animal": animal,
                "treatment": str(treatment),
                "tag_ratio": float(ratio[i]) if model == "PC106" and treatment == "veh" else None,
            }
            for name, column in values.items():
                if name == "cellState":
                    record[name] = str(column[i])
                else:
                    value = float(column[i])
                    record[name] = value if math.isfinite(value) else None
            animals.setdefault(animal, []).append(record)
            included += 1

        diagnostics["assigned_cells"] = included
        diagnostics["unassigned_or_doublet_cells"] = excluded
        diagnostics["animals"] = {
            name: {
                "treatment": rows[0]["treatment"],
                "cells": len(rows),
                "basal_cells": sum(row.get("cellState") == "basal" for row in rows),
            }
            for name, rows in sorted(animals.items())
        }
    return animals, diagnostics


def mean(values: list[float]) -> float | None:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(np.mean(finite)) if finite else None


def animal_summaries(animals: dict[str, list[dict]], ratio_filter: float | None = None) -> list[dict]:
    result = []
    for animal, cells in sorted(animals.items()):
        selected = [
            row for row in cells
            if ratio_filter is None or row["tag_ratio"] is None or row["tag_ratio"] >= ratio_filter
        ]
        if not selected:
            continue
        basal = sum(row.get("cellState") == "basal" for row in selected)
        n_state = sum(row.get("cellState") in ("basal", "classical") for row in selected)
        item = {
            "model": selected[0]["model"],
            "animal": animal,
            "treatment": selected[0]["treatment"],
            "n_cells_assigned": len(cells),
            "n_cells_in_analysis": len(selected),
            "basal_fraction": basal / n_state if n_state else None,
            "basal_cells": basal,
            "state_labeled_cells": n_state,
        }
        for feature in ("scBasalScore", "scClassicalScore", "EMTScore", "S_score", "G2M_score", "G1Score", "G2MScore"):
            feature_values = [row.get(feature) for row in selected]
            val = mean(feature_values)
            if val is not None:
                item[f"mean_{feature}"] = val
        result.append(item)
    return result


def exact_permutation(values: np.ndarray, treated_mask: np.ndarray) -> dict:
    values = np.asarray(values, dtype=float)
    treated_mask = np.asarray(treated_mask, dtype=bool)
    valid = np.isfinite(values)
    values, treated_mask = values[valid], treated_mask[valid]
    n = len(values)
    n_treated = int(treated_mask.sum())
    n_control = n - n_treated
    if n_treated < 1 or n_control < 1:
        return {"p_exact_two_sided": None, "permutations": 0, "difference_mrtx_minus_veh": None}
    observed = float(values[treated_mask].mean() - values[~treated_mask].mean())
    stats = []
    for chosen in itertools.combinations(range(n), n_treated):
        mask = np.zeros(n, dtype=bool)
        mask[list(chosen)] = True
        stats.append(float(values[mask].mean() - values[~mask].mean()))
    p = sum(abs(t) >= abs(observed) - 1e-12 for t in stats) / len(stats)
    pooled_denom = ((n_treated - 1) * np.var(values[treated_mask], ddof=1) +
                    (n_control - 1) * np.var(values[~treated_mask], ddof=1))
    pooled_denom /= max(n_treated + n_control - 2, 1)
    pooled_sd = math.sqrt(max(float(pooled_denom), 0.0))
    cohens_d = observed / pooled_sd if pooled_sd > 0 else None
    return {
        "n_mice": n,
        "n_mrtx": n_treated,
        "n_vehicle": n_control,
        "difference_mrtx_minus_veh": observed,
        "cohens_d_mice": cohens_d,
        "p_exact_two_sided": float(p),
        "permutations": len(stats),
        "exchangeability_assumption": "mouse-level treatment labels are exchangeable within this PDX model",
    }


def build_contrasts(summaries: list[dict], analysis_name: str) -> list[dict]:
    output = []
    models = sorted({row["model"] for row in summaries})
    features = sorted({key for row in summaries for key in row if key == "basal_fraction" or key.startswith("mean_")})
    for model in models:
        rows = [r for r in summaries if r["model"] == model]
        rows.sort(key=lambda r: r["animal"])
        labels = np.asarray([r["treatment"] == "mrtx" for r in rows], dtype=bool)
        for feature in features:
            vals = np.asarray([r.get(feature, np.nan) if r.get(feature) is not None else np.nan for r in rows], dtype=float)
            if np.isfinite(vals).sum() < 3:
                continue
            test = exact_permutation(vals, labels)
            output.append({
                "analysis": analysis_name,
                "model": model,
                "outcome": feature,
                "primary_endpoint": feature == "basal_fraction",
                "mouse_values": json.dumps({r["animal"]: r.get(feature) for r in rows}, ensure_ascii=False),
                **test,
            })
    return output


def load_gene_expression_by_mouse_state(model: str, animals: dict[str, list[dict]]) -> tuple[list[dict], dict]:
    """Aggregate the exported sparse expression-like matrix by mouse and state."""
    qc_path = DATA / f"GSE271300_PDX_{model}_QC.h5ad"
    rows_out: list[dict] = []
    with h5py.File(qc_path, "r") as qc:
        obs = qc["obs"]
        cell_ids = read_obs_column(obs, "_index")
        row_lookup = {cell_id: i for i, cell_id in enumerate(cell_ids)}
        var_names = [decode(v) for v in np.asarray(qc["var"]["_index"])]
        var_lookup = {name: i for i, name in enumerate(var_names)}
        genes = [gene for gene in TARGET_PANEL if gene in var_lookup]
        x = qc["X"]
        shape = tuple(int(v) for v in np.asarray(x.attrs["shape"]).ravel())
        matrix = csr_matrix((
            np.asarray(x["data"], dtype=np.float32),
            np.asarray(x["indices"], dtype=np.int32),
            np.asarray(x["indptr"], dtype=np.int64),
        ), shape=shape)
        sample = np.asarray(x["data"][: min(50000, len(x["data"]))])
        report = {
            "model": model,
            "qc_matrix_shape": list(shape),
            "matrix_dtype": str(x["data"].dtype),
            "sampled_values_are_integer_counts": bool(np.allclose(sample, np.round(sample))),
            "raw_counts_layer_present": bool("layers" in qc and len(qc["layers"].keys()) > 0),
            "target_panel_available": genes,
            "target_panel_missing": [gene for gene in TARGET_PANEL if gene not in var_lookup],
            "matrix_interpretation": "Sparse float feature matrix; no raw-count layer is supplied in this H5AD. Means are descriptive summaries of the provided expression-like scale, not raw-count pseudobulk differential expression.",
        }
        for animal, cell_rows in sorted(animals.items()):
            selected = [row for row in cell_rows if row["cell_id"] in row_lookup]
            for state in ("basal", "classical"):
                group = [row for row in selected if row.get("cellState") == state]
                if not group:
                    continue
                matrix_rows = np.asarray([row_lookup[row["cell_id"]] for row in group], dtype=int)
                state_means = np.asarray(matrix[matrix_rows, :][:, [var_lookup[g] for g in genes]].mean(axis=0)).ravel()
                for gene, gene_mean in zip(genes, state_means):
                    rows_out.append({
                        "model": model,
                        "animal": animal,
                        "treatment": group[0]["treatment"],
                        "cell_state": state,
                        "gene": gene,
                        "n_cells": len(group),
                        "mean_expression_like_value": float(gene_mean),
                        "matrix_scale": "provided sparse float values; not raw counts",
                    })
    return rows_out, report


def target_expression_contrasts(rows: list[dict]) -> list[dict]:
    output = []
    for model in sorted({row["model"] for row in rows}):
        for gene in sorted({row["gene"] for row in rows}):
            group = [row for row in rows if row["model"] == model and row["gene"] == gene and row["cell_state"] == "classical"]
            group.sort(key=lambda row: row["animal"])
            if len(group) < 3:
                continue
            vals = np.asarray([row["mean_expression_like_value"] for row in group], dtype=float)
            treated = np.asarray([row["treatment"] == "mrtx" for row in group], dtype=bool)
            result = exact_permutation(vals, treated)
            output.append({
                "model": model,
                "cell_state": "classical",
                "gene": gene,
                "outcome": "mouse_mean_expression_like_value",
                "mouse_values": json.dumps({row["animal"]: row["mean_expression_like_value"] for row in group}, ensure_ascii=False),
                **result,
                "interpretation_limit": "exploratory; small mouse n; RNA abundance is not protein abundance or pathway activity",
            })
    return output


def load_ga60_pooled_descriptive() -> list[dict]:
    """Keep GA60 visible as a pooled description without inferential replication."""
    path = DATA / "GSE271300_PDX_GA60_analyzed.h5ad"
    output = []
    with h5py.File(path, "r") as h5:
        obs = h5["obs"]
        treatment = read_obs_column(obs, "treatment")
        state = read_obs_column(obs, "cellState")
        fields = {name: read_numeric_column(obs, name) for name in ("scBasalScore", "scClassicalScore", "S_score", "G2M_score") if name in obs}
        for arm in ("veh", "mrtx"):
            mask = treatment == arm
            state_mask = mask & np.isin(state, ("basal", "classical"))
            n_state = int(state_mask.sum())
            item = {
                "model": "GA60",
                "treatment": arm,
                "n_cells": int(mask.sum()),
                "basal_fraction": float(np.sum(mask & (state == "basal")) / n_state) if n_state else None,
                "n_mice_available": None,
                "inferential_status": "pooled descriptive only; animal labels unavailable in inspected H5AD obs",
            }
            for name, values in fields.items():
                vals = values[mask & np.isfinite(values)]
                item[f"mean_{name}"] = float(vals.mean()) if len(vals) else None
            output.append(item)
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_primary(summaries: list[dict], out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.2), sharey=True)
    colors = {"veh": "#3A6EA5", "mrtx": "#D1495B"}
    for ax, model in zip(axes, ("PC69", "PC106")):
        rows = [r for r in summaries if r["model"] == model]
        groups = [("veh", "Véhicule"), ("mrtx", "MRTX1133")]
        for x, (treatment, label) in enumerate(groups):
            group = [r for r in rows if r["treatment"] == treatment and r.get("basal_fraction") is not None]
            ys = np.asarray([r["basal_fraction"] for r in group], dtype=float)
            jitter = np.linspace(-0.12, 0.12, len(ys)) if len(ys) > 1 else np.zeros(len(ys))
            ax.scatter(np.full(len(ys), x) + jitter, ys, color=colors[treatment], s=56, zorder=3, label=label)
            for j, row in enumerate(group):
                short_id = ("V" if treatment == "veh" else "M") + str(j + 1)
                ax.annotate(short_id, (x + jitter[j], ys[j]), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
            if len(ys):
                ax.hlines(float(ys.mean()), x - 0.23, x + 0.23, colors=colors[treatment], linewidth=2.4)
        ax.set_xticks([0, 1], ["Véhicule", "MRTX1133"])
        ax.set_title(model)
        ax.set_xlim(-0.45, 1.45)
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Fraction basale par souris")
    fig.suptitle("GSE271300 — état basal par animal (chaque point = une souris)")
    fig.text(0.5, 0.01, "V1–V3 = souris véhicule; M1–M4 = souris MRTX. Barre = moyenne des souris; points et noms complets dans le CSV.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    animals_by_model = {}
    diagnostics = []
    for model in ("PC69", "PC106"):
        animals, diag = load_model(model)
        animals_by_model[model] = animals
        diagnostics.append(diag)

    primary = [item for model in ("PC69", "PC106") for item in animal_summaries(animals_by_model[model])]
    strict = [item for model in ("PC69", "PC106") for item in animal_summaries(animals_by_model[model], ratio_filter=2.0)]
    contrasts = build_contrasts(primary, "PC106_vehicle_HTO_argmax_all")
    strict_contrasts = build_contrasts(strict, "PC106_vehicle_HTO_ratio_ge_2_sensitivity")
    gene_expression_rows = []
    expression_reports = []
    for model in ("PC69", "PC106"):
        rows, expression_report = load_gene_expression_by_mouse_state(model, animals_by_model[model])
        gene_expression_rows.extend(rows)
        expression_reports.append(expression_report)
    gene_contrasts = target_expression_contrasts(gene_expression_rows)
    ga60_pooled = load_ga60_pooled_descriptive()

    write_csv(OUT / "GSE271300_mouse_level_summaries.csv", primary)
    write_csv(OUT / "GSE271300_exact_mouse_permutation_contrasts.csv", contrasts)
    write_csv(OUT / "GSE271300_HTO_ratio_ge_2_sensitivity_mouse_summaries.csv", strict)
    write_csv(OUT / "GSE271300_HTO_ratio_ge_2_sensitivity_contrasts.csv", strict_contrasts)
    write_csv(OUT / "GSE271300_target_expression_by_mouse_state.csv", gene_expression_rows)
    write_csv(OUT / "GSE271300_classical_state_target_expression_contrasts.csv", gene_contrasts)
    write_csv(OUT / "GSE271300_GA60_pooled_descriptive.csv", ga60_pooled)
    plot_primary(primary, OUT / "GSE271300_basal_fraction_by_mouse.png")

    pc69_primary = next((r for r in contrasts if r["model"] == "PC69" and r["outcome"] == "basal_fraction"), None)
    pc106_primary = next((r for r in contrasts if r["model"] == "PC106" and r["outcome"] == "basal_fraction"), None)
    pc106_sens = next((r for r in strict_contrasts if r["model"] == "PC106" and r["outcome"] == "basal_fraction"), None)
    report = {
        "title": "GSE271300 mouse-level exploratory reanalysis",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": sys.version.split()[0],
            "h5py": h5py.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
            "virtual_environment_expected": ".venv",
        },
        "source": SOURCE_URL,
    "scope": "Mouse-level audit reanalysis of the same published GSE271300 experiment; this is not a new independent experimental replication and makes no clinical efficacy or cure claim.",
        "source_relationship": "The published paper using this dataset already reports KRAS-inhibitor-driven enrichment of the classical state and sensitivity of basal cells. The direction in this audit reanalysis therefore reproduces a published result on the same experiment; it is not a new biological discovery or validation of UNIVERSAL_LOG.",
        "source_publication": "Singhal et al., Cancer Discovery 2024, doi:10.1158/2159-8290.CD-24-0740; https://pmc.ncbi.nlm.nih.gov/articles/PMC11624508/",
        "unit_of_analysis": "mouse-level pseudobulk summaries; cells are subsamples, not independent biological replicates",
        "primary_endpoint": "fraction of assigned singlet cells labeled basal by the study-provided cellState field, summarized per mouse",
        "secondary_endpoints": "per-mouse mean of study-provided scBasalScore, scClassicalScore, cell-cycle fields, and EMTScore where available; exploratory",
        "candidate_target_panel": TARGET_PANEL,
        "candidate_target_expression_method": "For PC69 and PC106, provided sparse QC expression-like matrix values were averaged within mouse x cellState for a small panel around KRAS/EGFR-family/STAT3 plus identity markers. The H5AD contains float X values and no raw-count layer; this is not count-based differential expression.",
        "mapping": {
            "PC69": "study-provided Classification field in analyzed H5AD; labels identify each mouse; doublets/negatives excluded",
            "PC106_MRTX": "study-provided Classification field for MRTX singlets; doublets/negatives excluded",
            "PC106_vehicle": "exact barcode join from analyzed H5AD to QC H5AD, then largest of three raw vehicle HTO tag counts assigns a mouse; sensitivity requires largest/second-largest >= 2.0",
            "GA60": "not included in mouse-level inference because individual mouse tags are not available in the current H5AD obs; a pooled arm comparison would be cell-level descriptive only",
        },
        "inference": "Two-sided exact permutation of treatment labels across mice within each PDX model; this relies on exchangeability and is exploratory. No cell-level p-values. No multiplicity-adjusted confirmatory claims.",
        "pipeline_fit": "TLog/ordered-axis pipeline not run: treatment arms are unordered snapshots and there are only 6 or 7 animals per model; the current pipeline's standard minimum-series/walk-forward requirements are not met. Forcing cells into rows would pseudoreplicate.",
        "key_primary_results": {"PC69": pc69_primary, "PC106_all_vehicle_HTO_argmax": pc106_primary, "PC106_vehicle_HTO_ratio_ge_2_sensitivity": pc106_sens},
        "candidate_target_expression_matrix_audits": expression_reports,
        "candidate_target_classical_state_contrasts": gene_contrasts,
        "GA60_pooled_descriptive": ga60_pooled,
        "diagnostics": diagnostics,
        "limits": [
            "Preclinical PDX models, not patients; MRTX1133 monotherapy only in this dataset.",
            "Very small mouse counts limit exact p-value resolution and generalization.",
            "PC106 vehicle sample labels are reconstructed from dominant HTO raw-count tags because its supplied Classification field is blank for those cells.",
            "A tag-ratio cutoff of 2.0 is a sensitivity rule selected for this audit, not a published validated classifier threshold.",
            "Study-provided cell-state calls/scores are correlated outcomes and are exploratory, not independent confirmations.",
            "This analysis cannot establish treatment efficacy, a combination therapy benefit, a human biomarker, or a cure.",
        ],
        "outputs": [
            "GSE271300_mouse_level_summaries.csv",
            "GSE271300_exact_mouse_permutation_contrasts.csv",
            "GSE271300_HTO_ratio_ge_2_sensitivity_mouse_summaries.csv",
            "GSE271300_HTO_ratio_ge_2_sensitivity_contrasts.csv",
            "GSE271300_target_expression_by_mouse_state.csv",
            "GSE271300_classical_state_target_expression_contrasts.csv",
            "GSE271300_GA60_pooled_descriptive.csv",
            "GSE271300_basal_fraction_by_mouse.png",
        ],
    }
    (OUT / "GSE271300_ANALYSIS_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# GSE271300 — analyse exploratoire au niveau animal",
        "",
        f"Date UTC : {report['created_utc']}",
        f"Source : {SOURCE_URL}",
        "",
        "## Question",
        "Dans PC69 et PC106, la monothérapie MRTX1133 est-elle associée à un changement de la fraction de cellules tumorales classées basales, en traitant chaque souris comme unité biologique ?",
        "",
        "## Résultat principal",
        "",
        "Le jeu GSE271300 est le jeu de séquençage unicellulaire de l’article de Singhal et al. (Cancer Discovery, 2024). Cet article rapporte déjà l’enrichissement de l’état classique sous inhibition de KRAS. Les calculs ci-dessous auditent ce même jeu au niveau souris : ils ne constituent ni une réplication expérimentale indépendante ni une validation du pipeline UNIVERSAL_LOG.",
        "",
        "| Modèle | n souris MRTX / véhicule | Différence de fraction basale (MRTX − véhicule) | Cohen d entre souris | p exacte bilatérale |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, result in (("PC69", pc69_primary), ("PC106", pc106_primary)):
        if result:
            fmt = lambda v: "NA" if v is None else f"{v:.4g}"
            md.append(f"| {label} | {result['n_mrtx']} / {result['n_vehicle']} | {fmt(result['difference_mrtx_minus_veh'])} | {fmt(result['cohens_d_mice'])} | {fmt(result['p_exact_two_sided'])} |")
    md += [
        "",
        "Les valeurs par souris sont dans `GSE271300_mouse_level_summaries.csv`; l’image montre chaque souris séparément.",
        "",
        "## Sensibilité PC106",
        "",
        "Les cellules véhicule sont assignées par le plus grand des trois comptes HTO après jointure exacte des barcodes QC/analyse. Une analyse de sensibilité conserve seulement les cellules où le premier tag est au moins deux fois le second. Ce seuil est une règle exploratoire de qualité, pas une règle validée dans l’article.",
        "",
        "Résultat primaire de cette sensibilité : " + (json.dumps(pc106_sens, ensure_ascii=False) if pc106_sens else "non calculable"),
        "",
        "## Méthode et limites",
        "",
        "- PC69 : affectation par la colonne `Classification`; doublets/négatifs exclus.",
        "- PC106 MRTX : affectation par `Classification`; doublets/négatifs exclus.",
        "- PC106 véhicule : jointure exacte des identifiants cellulaires entre H5AD analysé et QC; affectation HTO par argmax; test de sensibilité avec ratio ≥ 2.",
        "- Mesure primaire : part basale parmi cellules basal/classical assignées, d’abord calculée par souris. Chaque souris reçoit le même poids dans la comparaison.",
        "- Test : permutation exacte bilatérale des étiquettes de traitement entre souris au sein de chaque modèle; l’échangeabilité des groupes est une hypothèse.",
        "- Les scores de cellule et le cycle cellulaire sont secondaires et exploratoires. Aucun test cellule par cellule n’est utilisé.",
        "- GA60 est laissé hors de l’inférence animale faute de tags individuels disponibles dans les fichiers inspectés.",
        "- Il s’agit de xénogreffes précliniques et de MRTX1133 seul. Ces données ne démontrent ni efficacité chez l’humain, ni bénéfice d’une combinaison, ni remède.",
        "- Le TLog n’est pas calculé : ces groupes sont des instantanés non ordonnés. Avec seulement 6–7 souris, le minimum standard de série / walk-forward du pipeline ne convient pas; les cellules ne doivent pas être utilisées pour gonfler N.",
        "- Les cibles EGFR/ERBB2/ERBB3/STAT3/KRAS et les marqueurs d’état sont résumés dans `GSE271300_target_expression_by_mouse_state.csv`. La matrice QC est sparse et contient des flottants non entiers sans couche de comptes bruts : ces moyennes ne sont pas des tests de différentiel d’expression de type DESeq2. Une abondance d’ARN ne prouve ni protéine, ni phosphorylation, ni dépendance thérapeutique.",
        "- GA60 est présenté en description agrégée seulement; ses cellules ne remplacent pas des répétitions animales.",
        "",
        "## Limite d’interprétation statistique",
        "",
        "Le nombre de souris est trop petit pour une validation confirmatoire. Les p exactes ont une résolution très grossière; les différences et les valeurs individuelles sont plus informatives pour planifier une expérience plus large que pour établir un fait clinique.",
        "",
        "## Reproduction",
        "",
        "Depuis le dossier racine du projet, avec `.venv` actif :",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe .\\pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-19\\analyze_GSE271300_mouse_level.py",
        "```",
        "Les sources H5AD originales restent dans `data_GSE271300`; les SHA-256 et diagnostics de jointure sont dans `GSE271300_ANALYSIS_REPORT.json`.",
        "",
    ]
    (OUT / "GSE271300_ANALYSIS_REPORT.md").write_text("\n".join(md), encoding="utf-8")

    manifest = {
        "source_url": SOURCE_URL,
        "script": {"path": str(Path(__file__).name), "sha256": sha256(Path(__file__))},
        "inputs": [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(DATA.glob("GSE271300_PDX_*.h5ad"))],
        "analysis_report_sha256": sha256(OUT / "GSE271300_ANALYSIS_REPORT.json"),
        "analysis_outputs": [],
    }
    manifest["analysis_outputs"] = [
        {"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "GSE271300_REPRODUCIBILITY_MANIFEST.json"
    ]
    (OUT / "GSE271300_REPRODUCIBILITY_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Mouse-level summaries:")
    for row in primary:
        print(row)
    print("\nPrimary exact contrasts:")
    for row in contrasts:
        if row["outcome"] == "basal_fraction":
            print(row)
    print(f"\nReports and outputs: {OUT}")


if __name__ == "__main__":
    main()
