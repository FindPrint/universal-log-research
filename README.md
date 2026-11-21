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
- **MRTX1133 resistance and MUC1-C data-fit audit (21 November 2026):** GEO inventories found 30 RNA-seq libraries in GSE269985, 17 tumor specimens in GSE269313, and 6 RNA-seq libraries in GSE293756. These records do not provide a sufficiently sampled, naturally ordered ADC response trajectory for the current v6.0.0 configuration. No pipeline estimates were generated; this is a data-fit decision, not a negative biological result. See the [audit report](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/RAPPORT_AUDIT_DONNEES_FR.md), [sample inventory](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/GEO_SAMPLE_INVENTORY.csv), and [source manifest](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/MRTX1133_MUC1C_AUDIT/GEO_DATA_FIT_MANIFEST.json).
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
