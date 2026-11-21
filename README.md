# UNIVERSAL_LOG

**An audit-first research pipeline for ordered, multi-stream data.**

UNIVERSAL_LOG is a research project that explores how multiple numerical streams can be analyzed along an explicitly configured axis. The project includes the pipeline code, its analysis layers, theory notes, benchmark runs, audit reports, and reproducibility records. TLog is one part of this framework; the project is not defined by a single final formula.

> **Research status:** this is exploratory software. The results below do not establish a treatment, a cure, clinical utility, or universal validity. Do not use the pipeline to make medical decisions.

## What is in the project

- Several historical pipeline versions, including Cohen-d scan variants.
- A 29-estimator analysis layer, six question groups, F1/F2 derivative outputs, and the TLog/Voie 1/Voie 2 analyses, with version-specific behavior documented in the audit files.
- Classical Ising experiments across network sizes, controls, synthetic null cases, calibration runs, and reproduction instructions.
- PDAC analyses of published patient-derived organoid, mouse-model, single-cell, and clinical datasets, with source manifests and run logs.
- Beginner-oriented theory and reading guides, full audit reports, checksums, and license notes.

## Current evidence snapshot — 21 November 2026

### Classical Ising

Some larger-network runs, including one blinded L64 run, returned a threshold near the known two-dimensional Ising critical temperature. This is a promising result to retain, but it is not by itself a proof of general detection or universality. In the separate synthetic pilot, the pipeline also returned candidate thresholds for no-event inputs; that pilot had one realization per case and therefore did not estimate a false-positive rate. A separate calibration study measured performance for specified simulated nulls and alternatives, and found limited power for weaker transitions. See the [pilot report](ising_classique_test/finite_size/pipeline_v6_0_pathway_audit/synthetic_pilot_v1/PILOT_REPORT_FR.md), [calibration results](ising_classique_test/finite_size/pipeline_v6_0_pathway_audit/calibration_v1/RESULTATS_CALIBRATION_V1.md), and [reproduction guide](ising_classique_test/finite_size/pipeline_v6_0_pathway_audit/REPRODUCTION_FR.md).

### Pancreatic ductal adenocarcinoma (PDAC)

- **Tiriac 2018 organoid matrix:** 60 complete PDO models and 26 drug-response columns were analyzed with Gemcitabine fixed as the target and each of the other 25 columns tested individually as a control. All 25 runs completed; each reported T0 as ambiguous and the configured control as non-monotone. The rows are cross-sectional PDO models, not a longitudinal patient trajectory; T0 is not a calendar-time threshold or treatment recommendation. See the [compact run summary](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/TIRIAC2018_ALL_CONTROL_RUN_SUMMARY.md); the full per-control traces are in the separate audit bundle.
- **Nature Communications 2025 matrix:** 46 PDO models and 63 drug AUC columns were prepared without imputation or scaling. The configured pipeline refused the input at its current minimum of 50 valid points, before computing estimators. This is an input-eligibility result, not evidence for or against a drug. Details are in the [external-data screen](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/EXTERNAL_REPLICATION_SCREEN_REPORT_2026-11-20.md) and its [source manifest](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/SCREENING_SOURCE_MANIFEST_2026-11-20.json).
- **Small-cohort / dose-curve recommendation audit (21 November 2026):** the public Nature Source Data Figure 6d contains 75 PDO–drug curve groups, each with two measurement columns and 7–8 concentrations per column. The unchanged v6.0.0 fast-mode function was applied separately to all 150 columns: 0 passed the current 50-point minimum, and 0/29 estimates were finite. This is only an input-gate result. The audit also separates evidence for MRTX1133 + olaparib from the untested proposed triplet, flags an ambiguous AS-77/KCNN4 identity, and recommends calibrated short-curve benchmarking against standard dose-response fits before adding a mode. See the [recommendation audit](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/AUDIT_RECOMMANDATIONS_PETITES_COHORTES/REVUE_RECOMMANDATIONS_PDAC_ET_PETITES_COHORTES_FR.md) and its [gate summary](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/AUDIT_RECOMMANDATIONS_PETITES_COHORTES/PDO_FIG6D_PIPELINE_GATE_SUMMARY.json).
- **MRTX1133 resistance and MUC1-C data-fit audit (21 November 2026):** GEO inventories found 30 RNA-seq libraries in GSE269985, 17 tumor specimens in GSE269313, and 6 RNA-seq libraries in GSE293756. A follow-up marker-panel reanalysis added GSE181961 and GSE279749, yielding 13 descriptive group contrasts across four RNA-seq series. MUC1 transcript changes under MRTX1133 were heterogeneous by model; this is not an ADC-response result. The v6.0.0 core-entry probe returned 0/29 finite estimates for 218 complete streams because each contrast has six samples, below the configured minimum of 50; 16 incomplete streams were skipped. No full target/control run, T0, or TLog was produced. See the [data-fit audit](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/RAPPORT_AUDIT_DONNEES_FR.md), [RNA-seq reanalysis](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/RAPPORT_REANALYSE_RNASEQ_MUC1C_FR.md), [sample inventory](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/RNASEQ_SAMPLE_INVENTORY_EXTENDED.csv), and [analysis manifest](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/RNASEQ_REANALYSIS_MANIFEST.json).
- **Direct anti-MUC1-C ADC data availability audit (21 November 2026):** the 2025 study reports cell, organoid, combination, and xenograft response figures, but its additional per-unit raw data are available from the corresponding author upon reasonable request. The ten Figshare supplements associated with the article are documents, not a per-well/per-animal response table; the audit found no ≥50-point ordered stream to run through v6.0.0. No ADC values were digitized or synthesized, and no full pipeline/T0/TLog run was made. See the [availability and fit audit](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/AUDIT_DISPONIBILITE_REPONSE_ADC_FR.md), [Figshare inventory](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/ADC_FIGSHARE_SUPPLEMENT_INVENTORY.csv), and [source manifest](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/ADC_SOURCE_DISCOVERY_MANIFEST.json).
- **Published KRAS G12D plus PARP-inhibitor study:** the project reanalyzed published mouse tumor-volume data and the accompanying cell data. These results support a preclinical signal in the models studied; they do not establish patient benefit, a cure, or a new multi-drug regimen. See the [reanalysis report](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-17/candidate_combination_g12d_parp/results_in_vivo_source_data/RAPPORT_REANALYSE_THERAPEUTIQUE_2026-11-17.md).

## Reproducing analyses

Use the exact script version, input, configuration, and dependencies recorded in each run manifest. The repository contains historical versions; do not assume that a command or configuration from one version applies to another. For the v6 Ising audit, start with its [French reproduction guide](ising_classique_test/finite_size/pipeline_v6_0_pathway_audit/REPRODUCTION_FR.md). The project `.venv` is machine-specific and is intentionally not a project dependency specification.

The full project folder contains large generated archives and source datasets. A GitHub source repository should contain the reproducible code, documentation, compact outputs, manifests, and checksums. Large generated snapshots belong in release assets or a separately archived distribution, and source data should be linked to its original repository unless its license explicitly permits redistribution.

## Related repository map

This repository is a curated snapshot of the local project folder, not the single source of truth for every later branch. Its version boundaries, links to the active PDAC work, and reproducibility gaps are documented in the [cross-repository map](REPOSITORY_MAP_2026-11-20.md). Results in the linked repositories have not automatically been reproduced by this snapshot.

## Licensing and third-party data

- Project code: MIT; see [`LICENSE`](LICENSE).
- Project-authored documentation and results: CC BY 4.0; see [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt) and [`LICENSES.md`](LICENSES.md).
- Third-party datasets, articles, and supplements retain their own licenses and terms. The project licenses do not relicense them. Check the relevant source manifest and source license before redistributing any third-party file.

## Limitations

UNIVERSAL_LOG is an evolving research framework, not a validated clinical test. An output called T0 may be a selected location even when no real transition exists. Interpretations require a valid ordered axis, independent biological units, appropriate null comparisons, uncertainty estimates, and independent validation. A successful run is not proof that the detected feature is biological or causal.

## Language

Most audit and theory documents are in French. The code and source references include English material. A plain-language French guide is available in [`GUIDE_DEBUTANT_UNIVERSAL_LOG.md`](GUIDE_DEBUTANT_UNIVERSAL_LOG.md) and [`FICHE_TLOG_DEBUTANT.md`](FICHE_TLOG_DEBUTANT.md).
