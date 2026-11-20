#!/usr/bin/env python
"""Reanalyse transparent of individual-animal source data from PMC13043926.

This is a secondary, exploratory reanalysis of one published preclinical study.
It is not independent validation and it does not establish a patient treatment.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from openpyxl import load_workbook
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "41467_2026_69695_MOESM7_source_data.xlsx"
OUT = ROOT / "results_in_vivo_source_data"
OUT.mkdir(exist_ok=True)
GROUPS = ["Vehicle", "Olaparib", "MRTX1133", "Combination"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_curve(ws, header_row: int, first_data_row: int, last_data_row: int,
               cohort: str, col_starts=(2, 8, 14, 20), width=6,
               labels=GROUPS, outcome="tumor_volume_mm3"):
    """Read columns as animals and rows as repeated time points, retaining zeros."""
    timepoints = []
    per_group = {label: [] for label in labels}
    for row_num in range(first_data_row, last_data_row + 1):
        timepoint = ws.cell(row_num, 1).value
        if timepoint is None:
            continue
        timepoints.append(float(timepoint))
        for label, start in zip(labels, col_starts):
            vals = []
            for col in range(start, start + width):
                v = ws.cell(row_num, col).value
                vals.append(float(v) if isinstance(v, (int, float)) else np.nan)
            per_group[label].append(vals)
    arr = {k: np.asarray(v, dtype=float).T for k, v in per_group.items()}
    n_set = {v.shape[0] for v in arr.values()}
    if len(n_set) != 1 or len(timepoints) < 2:
        raise ValueError(f"Malformed curve in {cohort}: group sizes={n_set}, times={timepoints}")
    rows = []
    for label in labels:
        for animal_idx in range(arr[label].shape[0]):
            for t_idx, tp in enumerate(timepoints):
                rows.append({"cohort": cohort, "treatment": label,
                             "animal_position_within_group": animal_idx + 1,
                             "timepoint_as_reported": tp, "outcome": outcome,
                             "value": arr[label][animal_idx, t_idx]})
    baseline = {k: v[:, 0] for k, v in arr.items()}
    endpoint = {k: v[:, -1] for k, v in arr.items()}
    change = {k: endpoint[k] - baseline[k] for k in labels}
    return rows, timepoints, arr, baseline, endpoint, change


def exact_two_group_permutation(a, b):
    """Enumerate all C(n1+n2,n1) assignments under label exchangeability."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    obs = float(np.mean(a) - np.mean(b))
    joined = np.concatenate([a, b])
    n_a = len(a)
    extreme = 0
    total = 0
    idx = range(len(joined))
    for selected in combinations(idx, n_a):
        selected = np.fromiter(selected, dtype=int)
        mask = np.ones(len(joined), dtype=bool)
        mask[selected] = False
        stat = float(np.mean(joined[selected]) - np.mean(joined[mask]))
        extreme += abs(stat) >= abs(obs) - 1e-12
        total += 1
    return obs, extreme / total, total


def welch_contrast(arrays, coeffs):
    """Welch-Satterthwaite CI/test for a linear contrast across independent arms."""
    means = np.array([np.mean(x) for x in arrays], float)
    variances = np.array([np.var(x, ddof=1) for x in arrays], float)
    ns = np.array([len(x) for x in arrays], float)
    coeffs = np.asarray(coeffs, float)
    estimate = float(np.dot(coeffs, means))
    pieces = coeffs**2 * variances / ns
    se = math.sqrt(float(np.sum(pieces)))
    df = float(np.sum(pieces) ** 2 / np.sum(pieces**2 / (ns - 1)))
    tval = estimate / se if se > 0 else math.inf
    p = float(2 * student_t.sf(abs(tval), df))
    crit = float(student_t.ppf(0.975, df))
    return {"estimate": estimate, "se": se, "df_welch": df, "t": tval,
            "p_welch_two_sided": p,
            "ci95_low": estimate - crit * se,
            "ci95_high": estimate + crit * se}


def baseline_adjusted_ancova(baseline, endpoint, groups):
    """OLS ANCOVA on log1p endpoint with log1p baseline covariate and treatment."""
    baseline = np.asarray(baseline, float)
    endpoint = np.asarray(endpoint, float)
    groups = np.asarray(groups, object)
    x = np.column_stack([
        np.ones(len(groups)), np.log1p(baseline),
        (groups == "Olaparib").astype(float),
        (groups == "MRTX1133").astype(float),
        (groups == "Combination").astype(float)])
    y = np.log1p(endpoint)
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ beta
    df = len(y) - x.shape[1]
    sigma2 = float(resid @ resid / df)
    cov = sigma2 * np.linalg.inv(x.T @ x)
    contrasts = {
        "Combination - Vehicle": np.array([0, 0, 0, 0, 1.]),
        "Combination - Olaparib": np.array([0, 0, -1, 0, 1.]),
        "Combination - MRTX1133": np.array([0, 0, 0, -1, 1.]),
        "Combination - MRTX1133 - Olaparib + Vehicle": np.array([0, 0, -1, -1, 1.])
    }
    results = {}
    for name, c in contrasts.items():
        est = float(c @ beta)
        se = math.sqrt(float(c @ cov @ c))
        tval = est / se if se > 0 else math.inf
        p = float(2 * student_t.sf(abs(tval), df))
        crit = float(student_t.ppf(0.975, df))
        results[name] = {"estimate_log1p_endpoint": est, "se": se, "df": df,
                         "p_two_sided": p,
                         "ci95_low": est - crit * se,
                         "ci95_high": est + crit * se,
                         "adjusted_ratio_of_1plus_endpoint": float(np.exp(est)),
                         "adjusted_ratio_ci95": [float(np.exp(est-crit*se)), float(np.exp(est+crit*se))]}
    return results


def cd8_factorial_ancova(baseline_by_arm, endpoint_by_arm):
    """Baseline-adjusted 2x2 model: combination x anti-CD8 depletion."""
    arm_names = ["Vehicle_IgG", "Vehicle_antiCD8", "Combination_IgG", "Combination_antiCD8"]
    baseline = np.concatenate([baseline_by_arm[a] for a in arm_names])
    endpoint = np.concatenate([endpoint_by_arm[a] for a in arm_names])
    treatment = np.concatenate([[int(a.startswith("Combination"))] * len(baseline_by_arm[a]) for a in arm_names])
    depletion = np.concatenate([[int("antiCD8" in a)] * len(baseline_by_arm[a]) for a in arm_names])
    interaction = treatment * depletion
    x = np.column_stack([np.ones(len(baseline)), np.log1p(baseline), treatment, depletion, interaction])
    y = np.log1p(endpoint)
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ beta
    df = len(y) - x.shape[1]
    sigma2 = float(resid @ resid / df)
    cov = sigma2 * np.linalg.inv(x.T @ x)
    c = np.array([0, 0, 0, 0, 1.])
    est = float(c @ beta)
    se = math.sqrt(float(c @ cov @ c))
    tval = est / se
    p = float(2 * student_t.sf(abs(tval), df))
    crit = float(student_t.ppf(0.975, df))
    return {"estimate_log1p_endpoint_interaction": est, "se": se, "df": df,
            "p_two_sided": p, "ci95_low": est - crit * se,
            "ci95_high": est + crit * se,
            "ratio_of_1plus_endpoint_interaction": float(np.exp(est)),
            "ratio_ci95": [float(np.exp(est-crit*se)), float(np.exp(est+crit*se))],
            "model": "log1p(endpoint) ~ log1p(baseline) + combination + anti-CD8 + combination:anti-CD8"}


def bh_adjust(values):
    vals = np.asarray(values, float)
    n = len(vals)
    order = np.argsort(vals)
    q = np.empty(n, float)
    running = 1.0
    for rank_idx in range(n - 1, -1, -1):
        j = order[rank_idx]
        rank = rank_idx + 1
        running = min(running, vals[j] * n / rank)
        q[j] = min(running, 1.0)
    return q


def add_main_cohort(wb, sheet, cohort, header_row, first_row, last_row):
    ws = wb[sheet]
    rows, times, curves, baseline, endpoint, change = read_curve(
        ws, header_row, first_row, last_row, cohort)
    summary = {"cohort": cohort, "source_sheet": sheet,
               "timepoints": times, "animals_per_arm": len(change["Vehicle"]),
               "endpoint_measurement_day_or_index": times[-1],
               "outcome": "absolute tumor volume change = final - baseline (mm^3)"}
    all_baseline = np.concatenate([baseline[g] for g in GROUPS])
    all_endpoint = np.concatenate([endpoint[g] for g in GROUPS])
    all_group = np.concatenate([[g] * len(baseline[g]) for g in GROUPS])
    ancova = baseline_adjusted_ancova(all_baseline, all_endpoint, all_group)
    log_growth = {k: np.log1p(endpoint[k]) - np.log1p(baseline[k]) for k in GROUPS}
    tests = []
    for comparator in ["Vehicle", "Olaparib", "MRTX1133"]:
        diff, p, n_perm = exact_two_group_permutation(change["Combination"], change[comparator])
        log_diff, log_p, log_n_perm = exact_two_group_permutation(log_growth["Combination"], log_growth[comparator])
        adjusted = ancova[f"Combination - {comparator}"]
        tests.append({"cohort": cohort, "outcome": summary["outcome"],
                      "contrast": f"Combination - {comparator}",
                      "mean_difference_mm3_unadjusted": diff, "p_exact_raw_change_sensitivity": p,
                      "permutations": n_perm,
                      "mean_difference_log1p_growth": log_diff,
                      "p_exact_log1p_growth_sensitivity": log_p,
                      "permutations_log1p_growth": log_n_perm,
                      "ancova_log1p_endpoint_effect": adjusted["estimate_log1p_endpoint"],
                      "ancova_adjusted_1plus_endpoint_ratio": adjusted["adjusted_ratio_of_1plus_endpoint"],
                      "ancova_ratio_ci95_low": adjusted["adjusted_ratio_ci95"][0],
                      "ancova_ratio_ci95_high": adjusted["adjusted_ratio_ci95"][1],
                      "p_ancova_baseline_adjusted": adjusted["p_two_sided"],
                      "assumption": "exchangeable animal labels within this two-arm comparison"})
    inter = welch_contrast(
        [change["Combination"], change["MRTX1133"], change["Olaparib"], change["Vehicle"]],
        [1, -1, -1, 1])
    inter["cohort"] = cohort
    inter["contrast"] = "Combination - MRTX1133 - Olaparib + Vehicle"
    inter["outcome"] = summary["outcome"]
    inter["interpretation"] = "negative means greater suppression than additivity on the raw volume-change scale; descriptive sensitivity"
    inter["baseline_adjusted_ancova_log1p_endpoint"] = ancova["Combination - MRTX1133 - Olaparib + Vehicle"]
    stats = {}
    for group in GROUPS:
        d = change[group]
        r = np.divide(endpoint[group], baseline[group], out=np.full_like(d, np.nan), where=baseline[group] > 0)
        stats[group] = {
            "n": int(len(d)), "mean_baseline_mm3": float(np.mean(baseline[group])),
            "mean_endpoint_mm3": float(np.mean(endpoint[group])),
            "mean_change_mm3": float(np.mean(d)), "median_change_mm3": float(np.median(d)),
            "sd_change_mm3": float(np.std(d, ddof=1)),
            "mean_log1p_growth": float(np.mean(log_growth[group])),
            "geometric_mean_1plus_fold_change": float(np.exp(np.mean(log_growth[group]))),
            "n_positive_baseline_for_ratio": int(np.isfinite(r).sum()),
            "median_fold_change_secondary": float(np.nanmedian(r)) if np.isfinite(r).any() else None
        }
    summary["by_arm"] = stats
    summary["relative_suppression_combination_vs_vehicle_percent"] = (
        100 * (stats["Vehicle"]["mean_change_mm3"] - stats["Combination"]["mean_change_mm3"])
        / stats["Vehicle"]["mean_change_mm3"]
        if stats["Vehicle"]["mean_change_mm3"] > 0 else None)
    summary["combination_baseline_to_vehicle_baseline_mean_ratio"] = (
        stats["Combination"]["mean_baseline_mm3"] / stats["Vehicle"]["mean_baseline_mm3"])
    summary["baseline_adjusted_ancova"] = ancova
    return rows, summary, tests, inter, curves


def main():
    if not SOURCE.exists() or SOURCE.read_bytes()[:4] != b"PK\x03\x04":
        raise SystemExit(f"Missing or invalid XLSX source: {SOURCE}")
    wb = load_workbook(SOURCE, read_only=True, data_only=True)
    cohorts = [
        ("SW1990_CDx", "Fig.4", 2, 3, 10),
        ("PANC1_CDx", "Fig.4", 24, 25, 32),
        ("PDX1", "Fig.5", 2, 3, 10),
        ("PDX2", "Fig.5", 24, 25, 32),
        ("KPC_subcutaneous", "Supp.Fig.13", 2, 3, 10),
    ]
    all_rows, summaries, pair_tests, interactions, curves = [], [], [], [], {}
    for name, sheet, hdr, first, last in cohorts:
        rows, summary, tests, interaction, arr = add_main_cohort(
            wb, sheet, name, hdr, first, last)
        all_rows.extend(rows)
        summaries.append(summary)
        pair_tests.extend(tests)
        interactions.append(interaction)
        curves[name] = arr
    pair_q = bh_adjust([r["p_ancova_baseline_adjusted"] for r in pair_tests])
    pair_q_raw = bh_adjust([r["p_exact_raw_change_sensitivity"] for r in pair_tests])
    pair_q_log = bh_adjust([r["p_exact_log1p_growth_sensitivity"] for r in pair_tests])
    for row, q in zip(pair_tests, pair_q):
        row["q_BH_global_15_baseline_adjusted_ANCOVA_comparisons"] = float(q)
    for row, q_raw, q_log in zip(pair_tests, pair_q_raw, pair_q_log):
        row["q_BH_global_15_exact_raw_change_sensitivity"] = float(q_raw)
        row["q_BH_global_15_exact_log1p_growth_sensitivity"] = float(q_log)
    interaction_q = bh_adjust([x["baseline_adjusted_ancova_log1p_endpoint"]["p_two_sided"] for x in interactions])
    for row, q in zip(interactions, interaction_q):
        row["q_BH_across_5_model_interaction_tests"] = float(q)

    # Orthotopic KPC-luc bioluminescence: three reported values/arm, day 0 to day 14.
    ws = wb["Fig.9"]
    bli_groups = ["Vehicle", "Olaparib", "MRTX1133", "Combination"]
    bli_starts = [2, 5, 8, 11]
    bli = {}
    for g, start in zip(bli_groups, bli_starts):
        start_value = np.array([ws.cell(3, c).value for c in range(start, start + 3)], float)
        end_value = np.array([ws.cell(5, c).value for c in range(start, start + 3)], float)
        bli[g] = np.log(end_value / start_value)
    bli_summary = {g: {"n": len(x), "mean_log_fold_day14_vs_day0": float(np.mean(x)),
                       "median_log_fold_day14_vs_day0": float(np.median(x)),
                       "geometric_mean_fold_change": float(np.exp(np.mean(x)))}
                   for g, x in bli.items()}
    bli_tests = []
    for comp in ["Vehicle", "Olaparib", "MRTX1133"]:
        diff, p, nperm = exact_two_group_permutation(bli["Combination"], bli[comp])
        bli_tests.append({"contrast": f"Combination - {comp}",
                          "mean_difference_log_fold": diff,
                          "p_exact_two_sided": p, "permutations": nperm,
                          "note": "n=3/arm; coarse exact p-value resolution; secondary endpoint"})

    # CD8 depletion: four independently reported arms, tumor-volume change over recorded time points.
    cd8_rows, cd8_times, cd8_curves, cd8_base, cd8_end, cd8_change = read_curve(
        ws, 48, 49, 56, "KPC_luc_CD8_depletion",
        col_starts=(2, 8, 14, 20), width=6,
        labels=["Vehicle_IgG", "Vehicle_antiCD8", "Combination_IgG", "Combination_antiCD8"])
    cd8_contrast = welch_contrast(
        [cd8_change["Combination_antiCD8"], cd8_change["Vehicle_antiCD8"],
         cd8_change["Combination_IgG"], cd8_change["Vehicle_IgG"]],
        [1, -1, -1, 1])
    cd8_contrast["contrast"] = "(Combination - Vehicle)_antiCD8 - (Combination - Vehicle)_IgG"
    cd8_contrast["interpretation"] = "positive means CD8 depletion attenuates combination benefit on raw volume-change scale"
    cd8_contrast["n_per_arm"] = 6
    cd8_ancova = cd8_factorial_ancova(cd8_base, cd8_end)
    cd8_pairwise = []
    for a, b in [("Combination_IgG", "Vehicle_IgG"),
                 ("Combination_antiCD8", "Vehicle_antiCD8"),
                 ("Combination_IgG", "Combination_antiCD8")]:
        diff, p, nperm = exact_two_group_permutation(cd8_change[a], cd8_change[b])
        cd8_pairwise.append({"contrast": f"{a} - {b}", "mean_difference_mm3": diff,
                             "p_exact_two_sided": p, "permutations": nperm})

    # Published flow-cytometry values: three mice/arm for three endpoints.
    # The separate CD8/CD3 row contains one value/group and is therefore descriptive only.
    flow_ws = wb["Fig.8"]
    flow_specs = [
        ("CD4_fraction_within_CD3_percent", 1, 3),
        ("TNFa_positive_fraction_within_CD8_percent", 6, 3),
        ("PD1_positive_fraction_within_CD8_percent", 11, 3),
    ]
    flow_rows, flow_tests, flow_summary = [], [], []
    for label, start_col, n_reps in flow_specs:
        values = {}
        for g_idx, group in enumerate(GROUPS):
            col = start_col + g_idx
            vals = np.array([flow_ws.cell(row, col).value for row in range(3, 3+n_reps)], float)
            values[group] = vals
            for idx, value in enumerate(vals, 1):
                flow_rows.append({"endpoint": label, "treatment": group,
                                  "animal_position_within_group": idx, "value_percent": float(value)})
        flow_summary.append({"endpoint": label, "n_per_arm": n_reps,
                             "mean_percent_by_arm": {g: float(np.mean(v)) for g, v in values.items()},
                             "median_percent_by_arm": {g: float(np.median(v)) for g, v in values.items()}})
        for comparator in ["Vehicle", "Olaparib", "MRTX1133"]:
            diff, p, nperm = exact_two_group_permutation(values["Combination"], values[comparator])
            flow_tests.append({"endpoint": label, "contrast": f"Combination - {comparator}",
                               "mean_difference_percentage_points": diff,
                               "p_exact_two_sided": p, "permutations": nperm})
    flow_q = bh_adjust([x["p_exact_two_sided"] for x in flow_tests])
    for row, q in zip(flow_tests, flow_q):
        row["q_BH_across_9_flow_comparisons"] = float(q)
    cd8_cd3_summary = {"endpoint": "CD8 fraction within CD3 percent", "values": {
        GROUPS[i]: flow_ws.cell(8, i+1).value for i in range(4)},
        "note": "one source value per treatment arm; no inferential test"}

    # Individual source data used in primary trajectories and CD8-depletion curves.
    all_rows.extend(cd8_rows)
    with (OUT / "individual_animal_tumor_volume_long.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        w.writeheader(); w.writerows(all_rows)
    (OUT / "primary_cohort_summary.json").write_text(
        json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(),
                    "source_file": str(SOURCE), "source_sha256": sha256(SOURCE),
                    "primary_cohorts": summaries, "pairwise_tests": pair_tests,
                    "factorial_interaction_welch": interactions,
                    "orthotopic_KPC_luc_bioluminescence": {
                        "endpoint": "log(day14/day0 fold-change)", "by_arm": bli_summary,
                        "pairwise_tests": bli_tests,
                        "source limitation": "3 measurements/arm in Source Data sheet; survival event times not supplied"},
                    "CD8_depletion": {"timepoints": cd8_times,
                        "by_arm_mean_change_mm3": {g: float(np.mean(v)) for g, v in cd8_change.items()},
                        "interaction_welch_raw_change": cd8_contrast,
                        "interaction_baseline_adjusted_ancova": cd8_ancova,
                        "pairwise_exact_raw_change": cd8_pairwise},
                    "published_flow_cytometry": {"replicate_unit": "mouse; n=3/arm",
                        "descriptive_summary": flow_summary, "pairwise_exact_tests": flow_tests,
                        "CD8_fraction_within_CD3": cd8_cd3_summary}},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    with (OUT / "flow_cytometry_mouse_values.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(flow_rows[0])); w.writeheader(); w.writerows(flow_rows)
    with (OUT / "flow_cytometry_tests.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(flow_tests[0])); w.writeheader(); w.writerows(flow_tests)
    with (OUT / "primary_pairwise_tests.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(pair_tests[0])); w.writeheader(); w.writerows(pair_tests)
    with (OUT / "factorial_interactions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(interactions[0])); w.writeheader(); w.writerows(interactions)

    # Plot all primary raw trajectories as individual-animal lines plus arm means.
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), constrained_layout=True)
    colors = {"Vehicle": "#666666", "Olaparib": "#e69f00",
              "MRTX1133": "#0072b2", "Combination": "#d55e00"}
    for ax, (name, arr) in zip(axes.flat, curves.items()):
        for group in GROUPS:
            values = arr[group]
            x = np.arange(values.shape[1])
            for individual in values:
                ax.plot(x, individual, color=colors[group], alpha=0.16, linewidth=0.8)
            ax.plot(x, np.mean(values, axis=0), color=colors[group], marker="o",
                    linewidth=2, label=group)
        ax.set_title(name.replace("_", " "))
        ax.set_xlabel("Measurement index (as source sheet; not assumed daily)")
        ax.set_ylabel("Tumor volume (mm³)")
        ax.spines[["top", "right"]].set_visible(False)
    axes.flat[-1].axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.97, 0.08), frameon=False)
    fig.suptitle("Published individual-animal tumor-volume trajectories\n"
                 "Secondary reanalysis of one preclinical study; lines are animals, thick lines are means")
    fig.savefig(OUT / "published_in_vivo_trajectories.png", dpi=180)
    plt.close(fig)

    manifest = {
        "analysis_id": "PMC13043926_individual_animal_in_vivo_reanalysis_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(Path(__file__).resolve()), "script_sha256": sha256(Path(__file__).resolve()),
        "source": str(SOURCE), "source_sha256": sha256(SOURCE),
        "method": {
            "primary_outcome": "baseline-adjusted log1p endpoint volume model; BH across 15 pairwise comparisons",
            "secondary_outcome": "absolute tumor volume change (mm^3); exact two-arm permutations and raw-scale interaction sensitivity",
            "experimental_unit": "animal position within a treatment block, as implied by source workbook layout",
            "pairwise": "enumerated two-sided label permutation for combination vs vehicle and each monotherapy; all assignments for each 6-vs-6 comparison",
            "multiplicity": "BH across 15 primary pairwise comparisons (3 per 5 models)",
            "factorial_interaction": "Welch-Satterthwaite contrast with t-based 95% CI on raw change scale; approximate under small n",
            "important": "animal identifiers are not supplied; within-animal identity across repeated time points assumed from column position; this is a reanalysis of the same publication, not independent replication"
        },
        "outputs": ["primary_cohort_summary.json", "primary_pairwise_tests.csv",
                    "factorial_interactions.csv", "individual_animal_tumor_volume_long.csv",
                    "published_in_vivo_trajectories.png", "flow_cytometry_mouse_values.csv",
                    "flow_cytometry_tests.csv"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"cohorts": [{"name": x["cohort"], "n": x["animals_per_arm"],
                                  "suppression_pct": x["relative_suppression_combination_vs_vehicle_percent"]}
                      for x in summaries],
                      "pairwise": [{"cohort": x["cohort"], "contrast": x["contrast"],
                                    "difference_mm3_unadjusted": x["mean_difference_mm3_unadjusted"],
                                    "adjusted_ratio_1plus_endpoint": x["ancova_adjusted_1plus_endpoint_ratio"],
                                    "p_ancova": x["p_ancova_baseline_adjusted"],
                                    "q_ancova": x["q_BH_global_15_baseline_adjusted_ANCOVA_comparisons"]}
                                   for x in pair_tests],
                      "interactions": [{"cohort": x["cohort"], "estimate": x["estimate"],
                                        "ci95": [x["ci95_low"], x["ci95_high"]],
                                        "p": x["p_welch_two_sided"]} for x in interactions],
                      "cd8_depletion_interaction": cd8_contrast,
                      "outputs": str(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
