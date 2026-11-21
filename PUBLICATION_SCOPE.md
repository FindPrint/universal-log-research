# Scope of the public source repository

This repository began as a clean-history publication copy of the project files present on 2026-11-20. Later dated updates are additive. `PUBLICATION_MANIFEST_2026-11-20.csv` records the baseline snapshot; `PUBLICATION_MANIFEST_2026-11-21.csv` records files added or changed in the MRTX1133/MUC1-C data-fit audit; `PUBLICATION_MANIFEST_2026-11-21_RNASEQ.csv` records the marker-panel RNA-seq reanalysis; `PUBLICATION_MANIFEST_2026-11-21_ADC.csv` records the direct ADC response-data availability audit; `PUBLICATION_MANIFEST_2026-11-21_SMALL_COHORTS.csv` records the PDO small-cohort, dose-curve gate, and recommendation audit. Each manifest records file sizes and SHA-256 digests and excludes itself and this scope note.

## Excluded from this source repository

The local Python virtual environment, caches and temporary files; large PDF/ZIP archive copies; HDF5 AnnData matrices; and source-data directories or files identified by `.gitignore` are not included. Third-party data should be obtained from the cited source repository and used under that source's terms. These exclusions keep machine-specific environments, duplicate archive bundles and data with unverified redistribution rights out of GitHub. Absolute Windows paths in the publication copy are redacted to neutral markers; the unmodified run records remain in the original local project folder.

## Licenses and research status

Project code is licensed under MIT. Project-authored documentation and results are licensed under CC BY 4.0. Third-party components and data keep their original licenses and terms. This is exploratory research software and does not establish clinical utility, a treatment recommendation, cure, or universal validity.
