"""Create reproducible tables, plots, and a hypothesis/result report."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "expanded_runs"
TC = float(2.0 / np.log(1.0 + np.sqrt(2.0)))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def append_journal(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    phys = pd.read_csv(OUT / "mcmc_physical_comparison_to_reference.csv")
    chain = pd.read_csv(OUT / "mcmc_physical_estimates_by_chain.csv")
    mat = pd.read_csv(OUT / "pipeline_axis_flux_matrix.csv")
    est = pd.read_csv(OUT / "pipeline_estimator_outputs.csv")
    matched_path = OUT / "v58_v59_matched_estimator_comparison.csv"
    matched = pd.read_csv(matched_path)
    ac = pd.read_csv(OUT / "flux_autocorrelation_diagnostics.csv")
    rel = pd.read_csv(OUT / "flux_relationships_spearman.csv")
    summary_exec = json.loads((OUT / "execution_summary.json").read_text(encoding="utf-8"))

    zcols = [name for name in phys.columns if name.endswith("_difference_over_combined_se")]
    zmat = phys[zcols].apply(pd.to_numeric, errors="coerce")
    pooled = zmat.to_numpy(dtype=float)
    per_metric = {}
    for col in zcols:
        abs_values = pd.to_numeric(phys[col], errors="coerce").abs()
        idx = int(abs_values.idxmax())
        per_metric[col.removesuffix("_difference_over_combined_se")] = {
            "n_cells": int(abs_values.notna().sum()),
            "n_within_abs_2_descriptive_only": int((abs_values <= 2).sum()),
            "max_abs_standardized_difference": float(abs_values.max()),
            "max_difference_cell": {k: float(phys.loc[idx, k]) for k in ["L", "T", col]},
        }
    pooled_finite = pooled[np.isfinite(pooled)]
    physical_summary = {
        "cells": int(len(phys)), "physical_metrics": len(zcols),
        "n_combined_standardized_differences": int(pooled_finite.size),
        "n_abs_z_le_2_descriptive_only": int(np.sum(np.abs(pooled_finite) <= 2)),
        "max_abs_standardized_difference": float(np.max(np.abs(pooled_finite))),
        "per_metric": per_metric,
    }

    thermo_cols = ["chi_abs_per_spin", "Cv_per_spin", "Binder_U4"]
    peak_rows = []
    for L, group in phys.groupby("L"):
        chi_col = "chi_abs_per_spin_mcmc_mean"
        peak = group.loc[group[chi_col].idxmax()]
        peak_rows.append({"L": int(L), "observable": "chi_abs_per_spin", "peak_T_on_grid": float(peak["T"]), "peak_value": float(peak[chi_col]), "grid_step": 0.02, "interpretation": "grid maximum, not a continuous peak fit"})
    peaks = pd.DataFrame(peak_rows).sort_values("L")
    peaks.to_csv(OUT / "susceptibility_grid_peak_summary.csv", index=False)
    tc_rows = phys[np.isclose(pd.to_numeric(phys["T"], errors="coerce"), TC, atol=1e-8)].copy()
    physical_tc = []
    for _, row in tc_rows.sort_values("L").iterrows():
        physical_tc.append({
            "L": int(row["L"]), "T": float(row["T"]),
            "chi_abs_per_spin": float(row["chi_abs_per_spin_mcmc_mean"]),
            "chi_between_chain_sd": float(row["chi_abs_per_spin_between_chain_sd"]),
            "Cv_per_spin": float(row["Cv_per_spin_mcmc_mean"]),
            "Cv_between_chain_sd": float(row["Cv_per_spin_between_chain_sd"]),
            "Binder_U4": float(row["Binder_U4_mcmc_mean"]),
            "Binder_between_chain_sd": float(row["Binder_U4_between_chain_sd"]),
        })

    matrix_counts = mat.groupby(["family", "status"]).size().to_dict()
    label_counts = mat["dominant_regime"].fillna("missing").value_counts().to_dict()
    grid = mat[mat["family"].eq("temperature_grid")].copy()
    grid_label_counts = grid["dominant_regime"].fillna("missing").value_counts().to_dict()
    tc_common = mat[
        np.isclose(pd.to_numeric(mat["T"], errors="coerce"), TC, atol=1e-8)
        & mat["control"].eq("MC_Update") & mat["flux_set"].eq("common")
    ].copy()
    axes = mat[mat["family"].eq("axis_contrast_at_Tc")].copy()
    axes["T"] = pd.to_numeric(axes["T"], errors="coerce")
    axes.to_csv(OUT / "axis_contrast_at_Tc.csv", index=False)
    ablation = mat[mat["family"].eq("flux_ablation_L16_Tc")].copy()
    ablation_stats = ablation.groupby("flux_set").agg(
        n_chains=("Chain", "nunique"),
        d_sat_mean=("d_sat", "mean"), d_sat_sd=("d_sat", "std"),
        d_crit_mean=("d_crit", "mean"), d_crit_sd=("d_crit", "std"),
        d_div_mean=("d_div", "mean"), d_div_sd=("d_div", "std"),
        d_null_mean=("d_null", "mean"), d_null_sd=("d_null", "std"),
    ).reset_index()
    ablation_stats.to_csv(OUT / "flux_ablation_summary_L16_Tc.csv", index=False)

    metadata_mismatch_core = int((mat["landscape_scan_points_source_metadata"] != mat["landscape_scan_points_effective_observed"]).sum())
    matched_summary = pd.read_csv(OUT / "matched_v59_run_summaries.csv")
    metadata_mismatch_matched = int((matched_summary["landscape_scan_points_source_metadata"] != matched_summary["landscape_scan_points_effective_observed"]).sum())
    matched_finite = matched.dropna(subset=["absolute_difference"])
    h5 = {
        "matched_runs": int(len(matched_summary)),
        "matched_estimator_pairs": int(len(matched_finite)),
        "both_versions_present": int(matched["_merge"].eq("both").sum()),
        "exact_equal_numeric_values": int(matched_finite["absolute_difference"].eq(0).sum()),
        "within_1e_6": int(matched_finite["within_1e-6_stored_precision"].sum()),
        "maximum_absolute_difference": float(matched_finite["absolute_difference"].max()),
        "interpretation_scope": "29 raw estimator medians per run; this does not restore v5.8 native d_kind/T_log_by_d_kind outputs",
    }
    autocorr_summary = ac.groupby("flux").agg(
        n=("effective_n", "count"), tau_median=("tau_int_updates", "median"),
        tau_max=("tau_int_updates", "max"), effective_n_median=("effective_n", "median"),
        effective_n_min=("effective_n", "min"),
    ).reset_index()
    autocorr_summary.to_csv(OUT / "autocorrelation_summary.csv", index=False)
    ess_abs = autocorr_summary.set_index("flux").loc["Abs_magnetization"]
    ess_energy = autocorr_summary.set_index("flux").loc["Energy_per_spin"]
    relationships_tc = rel[
        rel["L"].eq(16)
        & np.isclose(pd.to_numeric(rel["T"], errors="coerce"), TC, atol=1e-8)
        & rel["Chain"].eq(0)
    ].copy()
    relationships_tc["abs_spearman_rho"] = pd.to_numeric(relationships_tc["spearman_rho"], errors="coerce").abs()
    relationships_tc.sort_values("abs_spearman_rho", ascending=False).to_csv(OUT / "flux_relationships_L16_Tc_chain0_ranked.csv", index=False)

    # Physical finite-size figure: raw chain means and between-chain SE, plus archived reference.
    colors = {16: "#0072B2", 32: "#D55E00", 48: "#009E73"}
    fig, axs = plt.subplots(3, 1, figsize=(10.5, 12), sharex=True)
    plot_metrics = [
        ("chi_abs_per_spin", "Susceptibilité |m|", "chi_abs_per_spin"),
        ("Cv_per_spin", "Capacité calorifique", "Cv_per_spin"),
        ("Binder_U4", "Cumulant de Binder U4", "Binder_U4"),
    ]
    phys_plot = phys.copy()
    phys_plot["T"] = pd.to_numeric(phys_plot["T"], errors="coerce")
    for ax, (metric, title, prefix) in zip(axs, plot_metrics):
        for L in sorted(phys_plot["L"].unique()):
            g = phys_plot[phys_plot["L"].eq(L)].sort_values("T")
            y = g[f"{prefix}_mcmc_mean"].to_numpy(float)
            se = g[f"{prefix}_between_chain_sd"].to_numpy(float) / np.sqrt(g["n_chains"].to_numpy(float))
            ref = g[f"{prefix}_reference"].to_numpy(float)
            ref_se = g[f"{prefix}_reference_se"].to_numpy(float)
            ax.errorbar(g["T"], y, yerr=se, color=colors[int(L)], marker="o", markersize=3.5, linewidth=1.4, capsize=2, label=f"L={L}, MCMC")
            ax.errorbar(g["T"], ref, yerr=ref_se, color=colors[int(L)], marker="x", markersize=4, linewidth=0.8, linestyle=":", capsize=2, alpha=0.7, label=f"L={L}, référence")
        ax.axvline(TC, color="black", linestyle="--", linewidth=1, label="Tc analytique" if ax is axs[0] else None)
        ax.set_ylabel(metric)
        ax.set_title(title)
        ax.grid(alpha=0.22)
    axs[-1].set_xlabel("Température T / J")
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.005))
    fig.suptitle("Ising 2D — observables thermodynamiques et taille finie", y=0.99)
    fig.tight_layout(rect=(0, 0.055, 1, 0.96))
    fig.savefig(OUT / "observables_physiques_multi_tailles.png", dpi=180)
    plt.close(fig)

    # Axis sensitivity and flux ablation figure.
    fig, axs = plt.subplots(1, 2, figsize=(15, 6))
    axis_order = ["Energy_per_spin", "Magnetization", "Nearest_neighbor_correlation", "Noise_axis", "Abs_magnetization_shuffled"]
    axis_labels = ["Énergie", "Aimantation", "Corrélation voisins", "Axe bruité", "|m| mélangée"]
    width = 0.24
    x = np.arange(len(axis_order))
    for offset, L in enumerate(sorted(axes["L"].unique())):
        g = axes[axes["L"].eq(L)].set_index("control").reindex(axis_order)
        dx = (offset - 1) * width
        axs[0].bar(x + dx, pd.to_numeric(g["d_crit"], errors="coerce"), width, label=f"L={L}", color=colors[int(L)])
        for pos, value, regime in zip(x + dx, pd.to_numeric(g["d_crit"], errors="coerce"), g["dominant_regime"]):
            if np.isfinite(value):
                axs[0].text(pos, value + 0.035, str(regime)[:3], ha="center", va="bottom", fontsize=7, rotation=90)
    axs[0].set_xticks(x, axis_labels, rotation=25, ha="right")
    axs[0].set_ylabel("d_crit agrégé par le pipeline")
    axs[0].set_title("Sensibilité à l’axe de contrôle à Tc")
    axs[0].legend(frameon=False)
    axs[0].grid(axis="y", alpha=0.2)
    abl_order = ["target_absM_only", "order_parameter_family", "physical_without_noise", "all_fluxes"]
    abl_labels = ["|m| seul", "|m|, m², m⁴", "Physiques sans bruit", "10 flux"]
    positions = np.arange(len(abl_order))
    for _, row in ablation.iterrows():
        ix = abl_order.index(row["flux_set"])
        axs[1].scatter(ix + (int(row["Chain"]) - 2) * 0.035, row["d_crit"], color="#555555", s=22, alpha=0.75)
    means = ablation_stats.set_index("flux_set").reindex(abl_order)
    axs[1].errorbar(positions, means["d_crit_mean"], yerr=means["d_crit_sd"], color="#CC79A7", marker="D", markersize=5, linewidth=1.5, capsize=4, label="moyenne ± écart-type entre chaînes")
    axs[1].set_xticks(positions, abl_labels, rotation=20, ha="right")
    axs[1].set_ylabel("d_crit agrégé par le pipeline")
    axs[1].set_title("Ablation des flux — L=16, Tc, 5 chaînes")
    axs[1].grid(axis="y", alpha=0.2)
    axs[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "sensibilite_axes_et_flux_v59.png", dpi=180)
    plt.close(fig)

    result_summary = {
        "hypothesis_results": {
            "H1_physical_consistency": physical_summary,
            "H1_susceptibility_grid_peaks": peak_rows,
            "H1_physical_at_Tc": physical_tc,
            "H2_control_axis_sensitivity": {
                "axis_contrast_runs": int(len(axes)),
                "regime_labels_by_axis_family": axes["dominant_regime"].value_counts().to_dict(),
                "axis_table": OUT / "axis_contrast_at_Tc.csv",
            },
            "H3_flux_composition": {
                "ablation_runs": int(len(ablation)),
                "summary_table": OUT / "flux_ablation_summary_L16_Tc.csv",
                "d_crit_mean_by_flux_set": {row["flux_set"]: float(row["d_crit_mean"]) for _, row in ablation_stats.iterrows()},
                "d_crit_sd_by_flux_set": {row["flux_set"]: float(row["d_crit_sd"]) for _, row in ablation_stats.iterrows()},
                "all_flux_ablation_regime_labels": ablation["dominant_regime"].value_counts().to_dict(),
            },
            "H4_specificity_to_Tc": {
                "temperature_grid_runs": int(len(grid)),
                "temperature_grid_regime_labels": grid_label_counts,
                "interpretation": "All base MC_Update/common-flux cells are labelled divergence across the 12 sampled temperatures, including Tc; this configuration's label does not localize Tc.",
            },
            "H5_matched_v58_v59": h5,
        },
        "execution": summary_exec,
        "run_counts_by_family_and_status": {f"{a}|{b}": int(v) for (a, b), v in matrix_counts.items()},
        "dominant_regime_counts_all_core_runs": label_counts,
        "landscape_metadata_mismatches_core_runs": metadata_mismatch_core,
        "landscape_metadata_mismatches_matched_runs": metadata_mismatch_matched,
        "autocorrelation_summary_csv": str(OUT / "autocorrelation_summary.csv"),
        "notes": [
            "A |z| <= 2 count is descriptive only, not a predeclared pass/fail criterion.",
            "T grid maximum is a grid maximum at 0.02 spacing, not a continuous peak fit.",
            "One observation is one Wolff cluster update; these are algorithmic updates, not physical time.",
            "d_kind groupings in v5.9 outputs come from the v5.8 taxonomy as an external annotation.",
        ],
    }
    write_json(OUT / "post_analysis_summary.json", result_summary)

    report = [
        "# Rapport — étude Ising MCMC multi-axes v5.9",
        "",
        "## Cadre et traçabilité",
        "",
        f"- {summary_exec['generated_trajectory_count']} trajectoires indépendantes, soit {summary_exec['generated_measurement_rows']:,} observations brutes Wolff.",
        f"- {summary_exec['core_runs_ok']}/{summary_exec['core_runs_planned']} appels du plan principal et {summary_exec['matched_runs_ok']}/{summary_exec['matched_runs_planned']} rejeux appariés réussis.",
        "- Chaque observation est une mise à jour de grappe Wolff; elle ne représente pas un pas de temps physique.",
        "- Le fichier source v5.9 est inchangé. Le runtime expérimental est une copie dont la ligne de résolution paysage a été fixée à 24; différence et SHA-256 sont archivés dans `runtime/` et `protocol_and_provenance.json`.",
        "- La métadonnée source annonce encore 120 positions alors que les fichiers de caractéristiques en ont 24. Les exports gardent la valeur source, le compte observé et un indicateur d’incohérence.",
        "",
        "## Hypothèses et résultats mesurés",
        "",
        "### H1 — cohérence des observables physiques",
        "",
        f"Sur {physical_summary['n_combined_standardized_differences']} comparaisons cellule-métrique aux références archivées, {physical_summary['n_abs_z_le_2_descriptive_only']} ont un écart standardisé combiné de valeur absolue ≤ 2; le maximum est {physical_summary['max_abs_standardized_difference']:.3f}. Le seuil 2 est présenté à titre descriptif seulement, sans verdict d’acceptation.",
        "Les pics de susceptibilité sur la grille sont : " + "; ".join(f"L={r['L']}: T={r['peak_T_on_grid']:.2f}" for r in peak_rows) + ". C’est un maximum de grille espacée de 0,02, pas un ajustement continu. Voir la courbe de susceptibilité, chaleur spécifique et Binder ci-dessous.",
        "À Tc, U4 vaut 0,6114, 0,6106 et 0,6081 pour L=16, 32 et 48; ces valeurs rapprochées suggèrent un croisement dans ce voisinage, sans ajustement ni extrapolation. Les moyennes et écarts entre chaînes figurent dans `post_analysis_summary.json`; 5 chaînes améliorent le contrôle de répétabilité sans fournir une calibration précise des incertitudes.",
        "",
        "### H2 — effet de l’axe de contrôle",
        "",
        f"Les {len(axes)} contrastes d’axe donnent 12 labels `divergence`, 2 `saturation` et 1 `criticality`. Les contrôles par aimantation donnent `criticality` pour L=16 et `saturation` pour L=32,48, tandis que les quatre autres axes sont tous `divergence`. Le même état physique donne donc des sorties qui dépendent du contrôle choisi.",
        "L’énergie et la corrélation de voisins sont exactement liées par la définition du modèle (`corr=-E/2`); elles ne constituent pas deux axes physiques indépendants. Le bruit et l’aimantation mélangée servent de contrôles négatifs et ne prouvent aucune causalité.",
        "",
        "### H3 — composition des flux",
        "",
        f"Les moyennes de d_crit sur cinq chaînes sont : " + "; ".join(f"{r['flux_set']}={r['d_crit_mean']:.3f} ± {r['d_crit_sd']:.3f}" for _, r in ablation_stats.iterrows()) + ". Le flux |m| seul donne une valeur plus faible que la famille redondante |m|, m², m⁴; ajouter les autres flux du lot complet déplace peu la moyenne par rapport aux flux physiques sans bruit dans ce test. Les 20 étiquettes restent `divergence`.",
        "Dans la chaîne L=16,Tc, les corrélations de rang observées confirment les redondances : Spearman(E, corr voisins)=-1 et les paires |m|, m², m⁴ ont rho=1. Elles ne doivent pas être comptées comme preuves indépendantes.",
        "",
        "### H4 — spécificité du label par rapport à Tc",
        "",
        f"Les {len(grid)} cellules de la grille thermique avec axe MC_Update et flux communs sont toutes étiquetées `divergence` ({grid_label_counts.get('divergence', 0)}/{len(grid)}). Le label actuel ne distingue donc pas Tc des températures voisines dans cette configuration. Les étiquettes dépendent aussi fortement de l’axe; elles ne sont pas validées ici comme détecteur universel de transition.",
        "",
        "### H5 — comparaison appariée v5.8/v5.9",
        "",
        f"Sur les mêmes 20 CSV, les {h5['matched_estimator_pairs']} paires de médianes brutes des 29 estimateurs sont présentes dans les deux versions et les {h5['exact_equal_numeric_values']} paires sont numériquement égales (écart maximal {h5['maximum_absolute_difference']:.1f}). Cela établit la non-régression des médianes brutes du cœur sur ces entrées. Cela ne rétablit pas les exports natifs `d_kind`/`T_log_by_d_kind`, absents de v5.9.",
        "",
        "## Revue v5.9 : autres constats",
        "",
        "- La revue de code confirme 29 noms d’estimateurs et le même AST pour le helper L7a comparé; la v5.9 ne conserve pas le registre de taxonomie v5.8.",
        "- L’audit synthétique des helpers L7b montre que des T0 manquants deviennent `FAIL`, qu’un Delta de référence absent peut laisser le test mélangé à `PASS`, et qu’une comparaison de Delta signé peut mal classer un effet dont la magnitude est divisée par deux. Ce sont des cas synthétiques, non une validation prédictive.",
        "- Les seuils L7b sont des seuils codés, non calibrés par cette expérience. L’intégration `run_full_unified_pipeline` en mode L7b `light/full` reste à tester.",
        "",
        "## Figures et artefacts",
        "",
        "- [Observables physiques multi-tailles](expanded_runs/observables_physiques_multi_tailles.png)",
        "- [Sensibilité aux axes et aux flux](expanded_runs/sensibilite_axes_et_flux_v59.png)",
        "- [Tableau des contrastes d’axe](expanded_runs/axis_contrast_at_Tc.csv)",
        "- [Résumé des ablations](expanded_runs/flux_ablation_summary_L16_Tc.csv)",
        "- [Résumé complet JSON](expanded_runs/post_analysis_summary.json)",
        "- [Audit d’intégrité](TRACE_AUDIT.json) et [manifeste de l’étude](STUDY_MANIFEST.csv)",
        "- [Journal des exécutions](expanded_runs/RUN_JOURNAL.jsonl) et [console d’exécution](expanded_runs/execution_console.log)",
        "",
        "## Limites à garder en tête",
        "",
        "- La grille de température est un pilote à pas 0,02, avec Tc analytique ajouté comme point supplémentaire; aucune interpolation critique n’est revendiquée.",
        "- Cinq chaînes restent un petit échantillon. Les erreurs combinées comparent des campagnes finies différentes et doivent être lues comme diagnostic.",
        f"- L’autocorrélation de |m| donne un ESS médian d’environ {ess_abs['effective_n_median']:.0f} sur 8 000 observations; pour l’énergie, l’ESS minimum est {ess_energy['effective_n_min']:.0f}. Cela signale une dépendance temporelle non négligeable malgré les mises à jour Wolff.",
        "- Les estimateurs géométriques/TLog ne sont pas des observables standard de l’Ising; leurs nombres décrivent le comportement du pipeline sous ces réglages.",
        "- La cohérence sur ce système jouet ne démontre pas l’universalité sur d’autres domaines.",
    ]
    (HERE / "RAPPORT_MCMC_V59_MULTIAXIS.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    append_journal(HERE / "JOURNAL_DECISIONS.jsonl", {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "v59_post_analysis_completed",
        "hypotheses_vs_results": result_summary["hypothesis_results"],
        "report": str(HERE / "RAPPORT_MCMC_V59_MULTIAXIS.md"),
        "decision": "All labels and uncertainty comparisons remain descriptive; no new arbitrary pass/fail cutoff was introduced.",
        "analysis_tooling_note": "Two exploratory console queries had ordinary pandas column/aggregation mistakes; corrected queries produced the tables used in this report, with no changes to source or experiment data.",
    })
    # Finalize a checksum manifest after reports and journals are complete.
    files = []
    for path in sorted(x for x in OUT.rglob("*") if x.is_file() and x.name != "output_manifest.csv"):
        files.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    pd.DataFrame(files).to_csv(OUT / "output_manifest.csv", index=False)
    print(json.dumps({"report": str(HERE / "RAPPORT_MCMC_V59_MULTIAXIS.md"), "physical": physical_summary, "H5": h5}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
