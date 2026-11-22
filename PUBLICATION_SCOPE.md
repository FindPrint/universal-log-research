# Scope of the public source repository

`PUBLICATION_MANIFEST_2026-11-22_PANEL_V10.csv` records the V10 synthetic grouped-panel protocol, harness, generated input, concise run outputs, audit report, scripts, and hashes. The 3,523-page complete PDF and full-project ZIP are retained locally and on the D: backup; neither is embedded in the PDF or committed to this source repository. The full per-run JSON/CSV/image/log artifacts remain in the separate project snapshot.

This repository began as a clean-history publication copy of the project files present on 2026-11-20. Later dated updates are additive. `PUBLICATION_MANIFEST_2026-11-20.csv` records the baseline snapshot; `PUBLICATION_MANIFEST_2026-11-21.csv` records files added or changed in the MRTX1133/MUC1-C data-fit audit; `PUBLICATION_MANIFEST_2026-11-21_RNASEQ.csv` records the marker-panel RNA-seq reanalysis; `PUBLICATION_MANIFEST_2026-11-21_ADC.csv` records the direct ADC response-data availability audit; `PUBLICATION_MANIFEST_2026-11-21_SMALL_COHORTS.csv` records the PDO small-cohort, dose-curve gate, and recommendation audit; `PUBLICATION_MANIFEST_2026-11-21_LONGITUDINAL_V9.csv` records the patient-group code audit and corrected ctDNA source comparison. Each manifest records file sizes and SHA-256 digests and excludes itself and this scope note.

`PUBLICATION_MANIFEST_2026-11-21_AXIS_FLUX.csv` records the additive 57-patient PDAC axis × flux audit. All numeric controls were rotated through the same core analysis; the selected control was excluded from its own flux set, non-monotone controls were retained, and row-order sensitivity was recorded. The public copy includes compact outputs and detailed run traces. Console-log copies neutralize local absolute paths; the raw local logs are retained unchanged in the working project.

`PUBLICATION_MANIFEST_2026-11-21_LONGITUDINAL.csv` records the V8 source-access audit and pre-analysis protocol. `PUBLICATION_MANIFEST_2026-11-21_LONGITUDINAL_V9.csv` adds a source-level v6.0.1 group-boundary audit and compares three longitudinal ctDNA sources. V9 corrects V8's attribution of DOI `10.3389/fonc.2022.902177` from Schlick to Kirchweger et al. (2022); Schlick et al. (2021) is a distinct paper. Two data-request drafts are explicitly unsent; no patient-level raw data were obtained and no clinical pipeline run was made on these studies.

## Excluded from this source repository

The local Python virtual environment, caches and temporary files; large PDF/ZIP archive copies; HDF5 AnnData matrices; and source-data directories or files identified by `.gitignore` are not included. Third-party data should be obtained from the cited source repository and used under that source's terms. These exclusions keep machine-specific environments, duplicate archive bundles and data with unverified redistribution rights out of GitHub. Absolute Windows paths in the publication copy are redacted to neutral markers; the unmodified run records remain in the original local project folder.

## Licenses and research status

Project code is licensed under MIT. Project-authored documentation and results are licensed under CC BY 4.0. Third-party components and data keep their original licenses and terms. This is exploratory research software and does not establish clinical utility, a treatment recommendation, cure, or universal validity.
