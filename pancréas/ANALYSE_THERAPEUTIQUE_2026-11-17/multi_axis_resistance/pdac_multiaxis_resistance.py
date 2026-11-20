#!/usr/bin/env python3
"""Typed patient-block multiaxis scan of the published daraxonrasib cohort.

This companion module maps every predeclared patient-level control to every
predeclared resistance/ctDNA flow. It deliberately does not run T0/TLog: the
44 patients were selected for initial benefit followed by progression, and
the sampling stages are not equally spaced numeric time points.
"""
from __future__ import annotations

import csv
import hashlib
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
from scipy.stats import chi2_contingency, fisher_exact, rankdata, t as t_distribution

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
SOURCE = (HERE.parents[1] / "ANALYSE_THERAPEUTIQUE_2026-11-16" /
          "daraxonrasib_resistance_2026" / "reanalyzed" /
          "clinical_high_dose_44.csv")
SEED = 20261117
N_PERM = 9999


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_vaf(value: object) -> tuple[float, str]:
    """Keep non-detect / not-tested as status, never impute either to zero."""
    s = str(value).strip()
    sl = s.casefold()
    if not s or sl in {"nan", "na", "n/a"}:
        return np.nan, "missing"
    if "not detected" in sl:
        return np.nan, "not_detected"
    if "not tested" in sl:
        return np.nan, "not_tested"
    try:
        x = float(s.replace(",", ""))
        if np.isfinite(x):
            return x, "detected"
    except (TypeError, ValueError):
        pass
    return np.nan, "unparsed"


def has_event(value: object) -> bool:
    s = str(value).strip().casefold()
    return bool(s and s not in {"nan", "na", "n/a", "not detected", "not detected ", "none"})


def clean_data() -> pd.DataFrame:
    # The extracted source CSV has one title row before its header and one
    # repeated-header record; select explicit patient IDs and audit uniqueness.
    raw = pd.read_csv(SOURCE, skiprows=1, dtype=str, keep_default_na=False)
    raw = raw[raw.iloc[:, 0].str.fullmatch(r"Patient \d+")].copy()
    if len(raw) != 44 or raw.iloc[:, 0].duplicated().any():
        raise ValueError(f"Expected 44 unique patients; got {len(raw)} rows")
    d = pd.DataFrame({
        "patient_id": raw.iloc[:, 0].str.strip(),
        "dose_text": raw.iloc[:, 1].str.strip(),
        "kras_subtype": raw.iloc[:, 2].str.strip(),
        "best_response": raw.iloc[:, 3].str.strip(),
        "acquired_ras_short_text": raw.iloc[:, 4].str.strip(),
        "acquired_ras_cna_text": raw.iloc[:, 5].str.strip(),
        "baseline_tp53": raw.iloc[:, 6].str.strip(),
        "other_acquired_text": raw.iloc[:, 7].str.strip(),
    })
    d["dose_mg"] = pd.to_numeric(d["dose_text"].str.extract(r"(\d+(?:\.\d+)?)", expand=False), errors="coerce")
    d["dose_group"] = d["dose_mg"].map(lambda x: f"{int(x)} mg" if pd.notna(x) else "missing")
    d["baseline_tp53"] = d["baseline_tp53"].str.casefold().map({"mut": "Mut", "wt": "WT"}).fillna("missing")
    d["kras_subtype"] = d["kras_subtype"].str.replace("KRAS ", "", regex=False)
    d["best_response"] = d["best_response"].replace({"": "missing"})
    for col, src in [("ras_vaf_pre", 9), ("ras_vaf_on", 10), ("ras_vaf_eot", 11), ("genomic_max_vaf_eot", 8)]:
        parsed = [parse_vaf(v) for v in raw.iloc[:, src]]
        d[col] = [v for v, _ in parsed]
        d[f"{col}_status"] = [s for _, s in parsed]
    d["acquired_ras_short"] = raw.iloc[:, 4].map(has_event).astype(int)
    d["acquired_ras_cna"] = raw.iloc[:, 5].map(has_event).astype(int)
    d["acquired_kras_amp"] = raw.iloc[:, 5].str.contains(r"KRAS\s+AMP", case=False, regex=True).astype(int)
    d["acquired_myc_amp"] = raw.iloc[:, 5].str.contains(r"MYC\s+AMP", case=False, regex=True).astype(int)
    d["acquired_other"] = raw.iloc[:, 7].map(has_event).astype(int)
    d["acquired_any_listed"] = ((d["acquired_ras_short"] == 1) |
                                 (d["acquired_ras_cna"] == 1) |
                                 (d["acquired_other"] == 1)).astype(int)
    d["n_ras_pathway_classes_acquired"] = d["acquired_ras_short"] + d["acquired_ras_cna"]
    d["multiple_ras_pathway_classes"] = (d["n_ras_pathway_classes_acquired"] > 1).astype(int)
    # Ordered-stage differences in VAF percentage points; these are not rates
    # per day because the source gives C2D1 or C3D1 and no common elapsed days.
    d["delta_pre_to_on_vaf_pp"] = d["ras_vaf_on"] - d["ras_vaf_pre"]
    d["delta_on_to_eot_vaf_pp"] = d["ras_vaf_eot"] - d["ras_vaf_on"]
    d["delta_pre_to_eot_vaf_pp"] = d["ras_vaf_eot"] - d["ras_vaf_pre"]
    return d


def as_values(s: pd.Series, kind: str) -> np.ndarray:
    if kind == "continuous":
        return pd.to_numeric(s, errors="coerce").to_numpy(float)
    v = s.astype("object").to_numpy()
    out = np.empty(len(v), dtype=object)
    for i, x in enumerate(v):
        out[i] = None if pd.isna(x) or str(x).strip() in {"", "missing", "unparsed"} else str(x)
    return out


def _pearson_chi2(x: np.ndarray, y: np.ndarray) -> float:
    table = pd.crosstab(pd.Series(x), pd.Series(y)).to_numpy(dtype=float)
    if min(table.shape) < 2:
        return 0.0
    return float(chi2_contingency(table, correction=False)[0])


def _kw_h(groups: np.ndarray, values: np.ndarray) -> float:
    levels = list(dict.fromkeys(groups.tolist()))
    n = len(values)
    if len(levels) < 2 or n < 3:
        return 0.0
    ranks = rankdata(values, method="average")
    h = 0.0
    for level in levels:
        r = ranks[groups == level]
        h += (float(r.sum()) ** 2) / len(r)
    return max(0.0, (12.0 / (n * (n + 1)) * h) - 3.0 * (n + 1))


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = rankdata(x, method="average"), rankdata(y, method="average")
    if np.std(rx) == 0 or np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def permutation_indices(rng: np.random.Generator, n: int) -> np.ndarray:
    """Vectorized independent permutations of the patient labels/values."""
    return np.argsort(rng.random((N_PERM, n)), axis=1)


def permuted_chi2_tail(x: np.ndarray, y: np.ndarray, obs: float,
                       rng: np.random.Generator) -> int:
    x_levels, x_code = np.unique(x.astype(str), return_inverse=True)
    y_levels, y_code = np.unique(y.astype(str), return_inverse=True)
    perms = permutation_indices(rng, len(x))
    yp = y_code[perms]
    x_hot = (x_code[:, None] == np.arange(len(x_levels))[None, :]).astype(float)
    y_hot = (yp[:, :, None] == np.arange(len(y_levels))[None, None, :]).astype(float)
    tables = np.einsum("nk,rnj->rkj", x_hot, y_hot, optimize=True)
    rows = tables.sum(axis=2, keepdims=True)
    cols = tables.sum(axis=1, keepdims=True)
    expected = rows * cols / len(x)
    stats = np.sum(np.divide((tables - expected) ** 2, expected,
                             out=np.zeros_like(tables), where=expected > 0), axis=(1, 2))
    return int(np.count_nonzero(stats >= obs - 1e-12))


def permuted_spearman_tail(rx: np.ndarray, ry: np.ndarray, obs: float,
                           rng: np.random.Generator) -> int:
    perms = permutation_indices(rng, len(rx))
    ry_perm = ry[perms]
    xc = rx - rx.mean()
    yc = ry_perm - ry.mean()
    denom = np.sqrt(np.sum(xc * xc) * np.sum((ry - ry.mean()) ** 2))
    stats = np.sum(yc * xc[None, :], axis=1) / denom
    return int(np.count_nonzero(np.abs(stats) >= abs(obs) - 1e-12))


def permuted_kw_tail(groups: np.ndarray, ranks: np.ndarray, obs: float,
                     rng: np.random.Generator) -> int:
    levels, code = np.unique(groups.astype(str), return_inverse=True)
    perms = permutation_indices(rng, len(groups))
    perm_code = code[perms]
    hot = perm_code[:, :, None] == np.arange(len(levels))[None, None, :]
    rank_sums = np.einsum("rnk,n->rk", hot, ranks, optimize=True)
    ns = hot.sum(axis=1)
    stats = 12.0 / (len(groups) * (len(groups) + 1)) * np.sum(
        np.divide(rank_sums ** 2, ns, out=np.zeros_like(rank_sums, dtype=float), where=ns > 0), axis=1
    ) - 3.0 * (len(groups) + 1)
    return int(np.count_nonzero(stats >= obs - 1e-12))


def test_pair(control: pd.Series, flow: pd.Series, control_kind: str, flow_kind: str,
              rng: np.random.Generator) -> dict:
    x = as_values(control, control_kind)
    y = as_values(flow, flow_kind)
    valid = np.array([(a is not None and b is not None and
                       (control_kind != "continuous" or np.isfinite(a)) and
                       (flow_kind != "continuous" or np.isfinite(b)))
                      for a, b in zip(x, y)], dtype=bool)
    x, y = x[valid], y[valid]
    n = int(len(x))
    result = {"n_patients": n, "p_value": np.nan, "test": "not_estimable",
              "effect_name": "", "effect": np.nan, "permutations": 0,
              "levels_control": "", "levels_flow": ""}
    if n < 8:
        result["test"] = "not_estimable_n_lt_8"
        return result
    lx = sorted(set(map(str, x))) if control_kind == "categorical" else []
    ly = sorted(set(map(str, y))) if flow_kind == "categorical" else []
    result["levels_control"] = "|".join(lx)
    result["levels_flow"] = "|".join(ly)
    if control_kind == "categorical" and flow_kind == "categorical":
        if len(lx) < 2 or len(ly) < 2:
            result["test"] = "not_estimable_constant"
            return result
        tab = pd.crosstab(pd.Series(x), pd.Series(y)).to_numpy(dtype=int)
        if tab.shape == (2, 2):
            odds, p = fisher_exact(tab, alternative="two-sided")
            result.update(test="Fisher exact (patient-level 2x2)", p_value=float(p),
                          effect_name="odds_ratio", effect=float(odds), permutations=0)
            return result
        obs = _pearson_chi2(x, y)
        ex = np.sqrt(obs / (n * max(1, min(tab.shape) - 1)))
        ge = permuted_chi2_tail(x, y, obs, rng)
        result.update(test="patient-level permutation Pearson chi-square",
                      p_value=(ge + 1) / (N_PERM + 1), effect_name="Cramers_V",
                      effect=float(ex), permutations=N_PERM)
        return result
    if control_kind == "continuous" and flow_kind == "continuous":
        obs = _spearman(x.astype(float), y.astype(float))
        ge = permuted_spearman_tail(rankdata(x.astype(float), method="average"),
                                    rankdata(y.astype(float), method="average"), obs, rng)
        result.update(test="patient-level permutation Spearman", p_value=(ge + 1) / (N_PERM + 1),
                      effect_name="Spearman_rho", effect=obs, permutations=N_PERM)
        return result

    # One categorical, one continuous. A two-level group uses rank-biserial
    # effect and a patient-level label permutation; >2 levels uses Kruskal H.
    if control_kind == "categorical":
        groups, vals, levels = x.astype(str), y.astype(float), lx
        swapped = False
    else:
        groups, vals, levels = y.astype(str), x.astype(float), ly
        swapped = True
    if len(levels) < 2:
        result["test"] = "not_estimable_constant"
        return result
    if len(levels) == 2:
        g0, g1 = levels[0], levels[1]
        a, b = vals[groups == g0], vals[groups == g1]
        if len(a) < 2 or len(b) < 2:
            result["test"] = "not_estimable_sparse_group"
            return result
        ranks = rankdata(vals, method="average")
        n0, n1 = int(np.sum(groups == g0)), int(np.sum(groups == g1))
        r1 = float(ranks[groups == g1].sum())
        u1 = r1 - n1 * (n1 + 1) / 2
        center = n0 * n1 / 2
        obs = u1 - center
        perms = permutation_indices(rng, len(groups))
        g1_code = sorted(set(groups.astype(str).tolist())).index(g1)
        group_code = np.unique(groups, return_inverse=True)[1]
        perm_group_code = group_code[perms]
        perm_rank_sums = np.sum((perm_group_code == g1_code) * ranks[None, :], axis=1)
        perm_u = perm_rank_sums - n1 * (n1 + 1) / 2
        ge = int(np.count_nonzero(np.abs(perm_u - center) >= abs(obs) - 1e-12))
        effect = (float(np.median(b)) - float(np.median(a)))
        result.update(test="patient-level permutation rank test (2 groups)",
                      p_value=(ge + 1) / (N_PERM + 1), effect_name="median_difference_level1_minus_level0",
                      effect=effect, permutations=N_PERM)
        result["effect_levels"] = f"{g1} minus {g0}"
        return result
    obs = _kw_h(groups, vals)
    ge = permuted_kw_tail(groups, rankdata(vals, method="average"), obs, rng)
    grand = float(np.mean(vals))
    ss_total = float(np.sum((vals - grand) ** 2))
    effect = min(1.0, obs / max(1.0, n - 1))
    result.update(test="patient-level permutation Kruskal-Wallis",
                  p_value=(ge + 1) / (N_PERM + 1), effect_name="rank_H_scaled_exploratory",
                  effect=effect, permutations=N_PERM)
    result["effect_levels"] = "omnibus; no category direction"
    return result


def bh(p_values: np.ndarray) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    q = np.full(p.shape, np.nan)
    idx = np.flatnonzero(np.isfinite(p))
    if not len(idx):
        return q
    order = idx[np.argsort(p[idx])]
    m = len(order)
    ranked = p[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q[order] = np.minimum(ranked, 1.0)
    return q


def tp53_shedding_adjustment(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Post-scan confounding check; deliberately labelled exploratory."""
    use = d.dropna(subset=["ras_vaf_pre", "genomic_max_vaf_eot", "dose_mg"]).copy()
    tp = (use["baseline_tp53"].eq("Mut")).to_numpy(float)
    y = np.log1p(use["genomic_max_vaf_eot"].to_numpy(float))
    x = np.column_stack([np.ones(len(use)), tp,
                         np.log1p(use["ras_vaf_pre"].to_numpy(float)),
                         use["dose_mg"].to_numpy(float) / 100.0])
    if len(use) <= x.shape[1] + 5 or np.linalg.matrix_rank(x) < x.shape[1]:
        raise ValueError("Post-scan adjustment model is not estimable")
    inv = np.linalg.inv(x.T @ x)
    beta = inv @ x.T @ y
    resid = y - x @ beta
    leverage = np.sum((x @ inv) * x, axis=1)
    hc3 = inv @ x.T @ np.diag((resid / (1.0 - leverage)) ** 2) @ x @ inv
    se = np.sqrt(np.diag(hc3))
    df = len(use) - x.shape[1]
    tstat = beta / se
    p = 2.0 * t_distribution.sf(np.abs(tstat), df)
    crit = float(t_distribution.ppf(0.975, df))
    names = ["intercept", "baseline_TP53_Mut_vs_WT", "log1p_baseline_RAS_VAF_detected", "planned_dose_per_100mg"]
    table = pd.DataFrame({"term": names, "estimate_log1p_scale": beta,
                          "HC3_standard_error": se, "CI95_low": beta - crit * se,
                          "CI95_high": beta + crit * se, "t_HC3": tstat,
                          "p_nominal_unadjusted": p, "n_complete_patients": len(use),
                          "model": "log1p(EOT max VAF) ~ baseline TP53 + log1p(baseline RAS VAF detected) + planned dose/100mg",
                          "status": "post-scan exploratory; not included in primary BH family"})
    summary = {"n_complete_patients": len(use), "tp53_mut_n": int(tp.sum()),
               "tp53_wt_n": int(len(tp) - tp.sum()),
               "tp53_coefficient_log1p": float(beta[1]), "tp53_hc3_se": float(se[1]),
               "tp53_ci95_low": float(beta[1] - crit * se[1]),
               "tp53_ci95_high": float(beta[1] + crit * se[1]),
               "tp53_nominal_p": float(p[1]), "r_squared": float(1 - np.sum(resid**2) / np.sum((y-y.mean())**2)),
               "formula": "log1p(EOT max VAF) ~ TP53-mut + log1p(baseline RAS VAF, detected only) + dose/100mg",
               "interpretation": "association within a progression-selected cohort; baseline-VAF complete cases only; post-scan and uncorrected for multiplicity"}
    return table, summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = clean_data()
    control_spec = [
        ("baseline_tp53", "categorical", "baseline biomarker"),
        ("kras_subtype", "categorical", "baseline genotype"),
        ("dose_mg", "continuous", "planned exposure; nonrandomized"),
        ("dose_group", "categorical", "planned exposure; alternate encoding"),
        ("best_response", "categorical", "post-baseline response; selected cohort"),
        ("ras_vaf_pre_status", "categorical", "baseline detection status"),
        ("ras_vaf_pre", "continuous", "baseline ctDNA VAF; detected only"),
    ]
    flow_spec = [
        ("acquired_ras_short", "categorical", "acquired RAS/MAPK/PI3K/RTK short alteration listed"),
        ("acquired_ras_cna", "categorical", "acquired RAS-pathway copy-number alteration listed"),
        ("acquired_kras_amp", "categorical", "acquired KRAS amplification listed"),
        ("acquired_myc_amp", "categorical", "acquired MYC amplification listed"),
        ("acquired_other", "categorical", "other acquired alteration listed"),
        ("acquired_any_listed", "categorical", "any listed acquired alteration"),
        ("multiple_ras_pathway_classes", "categorical", "both short-variant and CNA classes listed"),
        ("ras_vaf_on_status", "categorical", "on-treatment detection status"),
        ("ras_vaf_eot_status", "categorical", "end-of-treatment detection status"),
        ("ras_vaf_eot", "continuous", "end-of-treatment RAS VAF; detected only"),
        ("genomic_max_vaf_eot", "continuous", "end-of-treatment maximum genomic VAF; detected only"),
        ("delta_pre_to_on_vaf_pp", "continuous", "pre-to-on stage difference; both detected"),
        ("delta_on_to_eot_vaf_pp", "continuous", "on-to-end stage difference; both detected"),
        ("delta_pre_to_eot_vaf_pp", "continuous", "pre-to-end stage difference; both detected"),
    ]
    rng = np.random.default_rng(SEED)
    rows = []
    for ci, (cname, ckind, cdesc) in enumerate(control_spec):
        for fi, (fname, fkind, fdesc) in enumerate(flow_spec):
            result = test_pair(d[cname], d[fname], ckind, fkind, rng)
            rows.append({"control": cname, "control_type": ckind, "control_description": cdesc,
                         "flow": fname, "flow_type": fkind, "flow_description": fdesc,
                         **result})
    res = pd.DataFrame(rows)
    res["q_bh_global_estimable"] = bh(res["p_value"].to_numpy())
    res["family_estimable_tests"] = int(res["p_value"].notna().sum())
    res.to_csv(OUT / "controls_by_flows_all_tests.csv", index=False, float_format="%.10g")
    d.to_csv(OUT / "patient_level_normalized_44.csv", index=False, float_format="%.10g")
    adjusted_table, adjusted_summary = tp53_shedding_adjustment(d)
    adjusted_table.to_csv(OUT / "posthoc_TP53_eot_vaf_adjusted.csv", index=False, float_format="%.10g")

    # Coverage/status inventory for every signal; non-detection is explicit.
    inventory = []
    for name, typ, desc in control_spec + flow_spec:
        s = d[name]
        inventory.append({"field": name, "role": "control" if any(name == x[0] for x in control_spec) else "flow",
                          "type": typ, "description": desc, "n_patients": len(d),
                          "n_observed": int(s.notna().sum()),
                          "n_missing_or_censored": int(s.isna().sum()),
                          "distinct_nonmissing": int(s.nunique(dropna=True))})
    pd.DataFrame(inventory).to_csv(OUT / "field_coverage.csv", index=False)

    # Visualize adjusted evidence strength; q-values are not effect sizes.
    pivot = res.pivot(index="control", columns="flow", values="q_bh_global_estimable")
    mat = -np.log10(np.clip(pivot.to_numpy(dtype=float), 1e-6, 1.0))
    fig, ax = plt.subplots(figsize=(16, 6.5), constrained_layout=True)
    im = ax.imshow(mat, cmap="viridis", vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)), [x.replace("_", "\n") for x in pivot.columns], fontsize=7)
    ax.set_yticks(np.arange(len(pivot.index)), [x.replace("_", " ") for x in pivot.index], fontsize=9)
    ax.set_title("PDAC résistance daraxonrasib — scan contrôles × flux\n−log10(q BH globale); plus élevé = association mieux soutenue, blanc = non estimable")
    ax.set_xlabel("Flux / mesure de résistance")
    ax.set_ylabel("Contrôle candidat")
    cb = fig.colorbar(im, ax=ax, shrink=.8)
    cb.set_label("−log10(q global), plafonné à 3")
    fig.savefig(OUT / "controls_by_flows_heatmap.png", dpi=180)
    plt.close(fig)

    estimable = res[res["p_value"].notna()].sort_values("q_bh_global_estimable")
    sig = estimable[estimable["q_bh_global_estimable"] < 0.05]
    coupling = res[(res["control"] == "ras_vaf_pre") &
                   (res["flow"] == "delta_pre_to_on_vaf_pp")].iloc[0]
    tp53_krasamp = res[(res["control"] == "baseline_tp53") &
                       (res["flow"] == "acquired_kras_amp")].iloc[0]
    tp53_on = d.groupby("baseline_tp53")["ras_vaf_on_status"].value_counts().unstack(fill_value=0)
    tp53_max = d.groupby("baseline_tp53")["genomic_max_vaf_eot"].median()
    top = estimable.head(12)
    with (OUT / "REPORT_MULTIAxis_PDac_v1.md").open("w", encoding="utf-8") as f:
        f.write("# Scan clinique multiaxial — résistance au daraxonrasib\n\n")
        f.write("**Exécution:** 17 novembre 2026 · **patients:** 44 · **flux:** 14 · **contrôles:** 7 · **famille:** BH globale sur tests estimables.\n\n")
        f.write("## Résultat\n\n")
        f.write(f"La grille contrôle × flux produit **{len(rows)} comparaisons prévues**, dont **{len(estimable)} estimables** après gestion explicite des données absentes/censurées. "
                f"Les associations avec q BH globale < 0,05 sont **{len(sig)}**.\n\n")
        f.write("Cette analyse est descriptive/exploratoire et ne donne ni prédicteur validé, ni combinaison thérapeutique, ni preuve de guérison. Les 44 patients ont tous été sélectionnés parce qu’ils avaient eu un bénéfice initial puis une progression; il n’y a pas de groupe de patients durablement sans progression. Le test de TP53 contre amplification KRAS fait partie des comparaisons et sa valeur brute connue n’est pas une validation indépendante.\n\n")
        f.write(f"Le contraste déjà rapporté TP53 prétraitement ↔ amplification KRAS acquise retrouve p={tp53_krasamp.p_value:.4g}, mais q BH globale={tp53_krasamp.q_bh_global_estimable:.4g}; il ne franchit pas la grille élargie.\n\n")
        f.write("Parmi les quatre q<0,05, le lien baseline RAS-VAF ↔ différence prétraitement/sous-traitement est mathématiquement couplé, car la valeur initiale entre dans le calcul du delta (rho="
                f"{coupling.effect:.3f}, q={coupling.q_bh_global_estimable:.4g}); il ne constitue pas une preuve biologique indépendante. Le lien baseline VAF–détection sous traitement est aussi sensible au seuil de détection.\n\n")
        f.write("Les deux associations non directement couplées au calcul d'un delta concernent TP53: la détection RAS sous traitement est observée chez "
                f"{int(tp53_on.loc['Mut'].get('detected',0))}/{int(tp53_on.loc['Mut'].sum())} TP53-mut contre {int(tp53_on.loc['WT'].get('detected',0))}/{int(tp53_on.loc['WT'].sum())} TP53-WT; la médiane du VAF génomique maximal à fin de traitement est "
                f"{tp53_max['Mut']:.2f}% contre {tp53_max['WT']:.2f}%. Ces mesures à progression peuvent refléter la quantité de tumeur qui relargue de l'ADN ou le profil génomique, et non une résistance causée par TP53.\n\n")
        f.write("Un contrôle de confusion post-scan, défini après observation de la grille et donc non préenregistré, modélise log1p(VAF génomique maximal fin de traitement) selon TP53, log1p(VAF RAS prétraitement détecté) et dose parmi "
                f"{adjusted_summary['n_complete_patients']} cas complets. Coefficient TP53 Mut vs WT={adjusted_summary['tp53_coefficient_log1p']:.3f} (SE HC3={adjusted_summary['tp53_hc3_se']:.3f}, IC95% {adjusted_summary['tp53_ci95_low']:.3f} à {adjusted_summary['tp53_ci95_high']:.3f}, p nominale={adjusted_summary['tp53_nominal_p']:.4g}). Ce contrôle reste exploratoire, non corrigé pour la sélection du modèle et ne transforme pas cette cohorte en validation prédictive.\n\n")
        f.write("## Associations brutes les plus fortes après correction\n\n")
        f.write("| Contrôle | Flux | n | Test | Effet (type) | p | q globale |\n|---|---|---:|---|---:|---:|---:|\n")
        for _, r in top.iterrows():
            f.write(f"| {r.control} | {r.flow} | {r.n_patients} | {r.test} | {r.effect_name}={r.effect:.4g} | {r.p_value:.4g} | {r.q_bh_global_estimable:.4g} |\n")
        f.write("\n## Règles de lecture\n\n")
        f.write("- Une ligne représente un patient. Les prélèvements prétraitement, sous traitement et fin de traitement restent des flux rattachés au même patient; ils ne sont jamais comptés comme trois patients.\n")
        f.write("- Les valeurs ‘Not detected’ et ‘Not tested’ restent distinctes et ne sont jamais remplacées par zéro. Les tests sur VAF numérique portent uniquement sur les valeurs détectées; la couverture apparaît dans field_coverage.csv.\n")
        f.write("- ‘delta’ est une différence entre étapes de prélèvement, pas une pente temporelle : les jours exacts et l’intervalle commun ne sont pas fournis.\n")
        f.write("- La matrice teste chaque contrôle préspecifié avec chaque flux. Elle mesure des associations simples et ne teste pas des interactions d’ordre supérieur ni la causalité. Les encodages dose continue/catégorielle et les mesures corrélées gonflent le nombre de comparaisons; la correction globale les couvre partiellement, pas le biais de sélection antérieur.\n")
        f.write("- Aucun T0/TLog n’est calculé : N=44 est inférieur au seuil séquentiel courant N≥50, et la cohorte est sélectionnée sur progression. Ici, la sortie honnête du pipeline est une cartographie multi-axes avec abstention sur le seuil.\n\n")
        f.write("Le tableau posthoc_TP53_eot_vaf_adjusted.csv est séparé de la famille primaire des 98 tests; son p nominal ne doit pas être lu comme une confirmation.\n\n")
        f.write("## Reproduction\n\nDepuis la racine du projet Windows :\n\n```powershell\n.\\.venv\\Scripts\\python.exe pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-17\\multi_axis_resistance\\pdac_multiaxis_resistance.py\n```\n\n")
        f.write("Entrée source: table clinique supplémentaire de l’étude Aronchik et al., Nature Medicine 2026, DOI 10.1038/s41591-026-04537-w. Cette étude est l’origine des observations, pas une validation externe.\n")

    outputs = [p for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"]
    manifest = {
        "analysis_id": "pdac_daraxonrasib_typed_controls_by_flows_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unit_of_analysis": "one patient (44 unique patient IDs); repeated sample stages remain within patient",
        "source": {"path": str(SOURCE), "sha256": sha256(SOURCE), "bytes": SOURCE.stat().st_size,
                   "paper": "https://doi.org/10.1038/s41591-026-04537-w"},
        "selection": "44 patients with initial CR/PR/SD and subsequent progression on daraxonrasib; no nonprogression control cohort",
        "controls": [{"name": n, "type": t, "status": s} for n,t,s in control_spec],
        "flows": [{"name": n, "type": t, "status": s} for n,t,s in flow_spec],
        "missingness": "Not detected and Not tested preserved as statuses; no numeric imputation",
        "statistics": {"categorical_2x2": "two-sided Fisher exact", "other_pairs": "patient-level permutation tests",
                       "permutations": N_PERM, "seed": SEED, "adjustment": "Benjamini-Hochberg across all estimable control x flow tests"},
        "posthoc_model": adjusted_summary,
        "pipeline_scope": "typed multi-axis companion; no T0/TLog because n<50 and cohort is progression-selected; no causal treatment claim",
        "software": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__},
        "script_sha256": sha256(Path(__file__)),
        "outputs": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in outputs},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"patients": len(d), "planned_tests": len(res), "estimable_tests": len(estimable),
                      "q_lt_0_05": len(sig), "results": str(OUT), "manifest": str(OUT / "manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
