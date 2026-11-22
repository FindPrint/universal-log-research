# Scope of the public source repository — V10

V10 adds the grouped-panel synthetic integration protocol, its reproducible harness, a generated input panel, compact patient/control summaries, the direct short-series gate result, a readable audit report, and an aggregate figure. The publication manifest lists exact paths, byte counts, and SHA-256 hashes.

The experiment uses generated data only. It does not include patient records, clinical measurements, a therapy comparison, a biomarker claim, or a treatment recommendation. The archived UNIVERSAL_LOG v6.0.1 source is called as-is; its pipeline code is not modified by this V10 update.

The local full-project snapshot separately retains detailed per-run JSON, CSV files, figures, console traces, and other project files. The 3,523-page complete whitepaper PDF (SHA-256 `9eb11d6d6de648aefb1c3e7cd819bb135dcac99e31c0c02e120ef0589afa4931`) and the large full-project ZIP are not committed to this source repository. The PDF does not contain the ZIP as an attachment. The V10 appendix preserves 210 figures and all 16 run logs; the publication update includes the compact panel table and summary heatmap.

## Included in the V10 source update

- Frozen protocol and beginner-facing reproduction instructions.
- Synthetic data generator and patient-group adapter.
- Direct v6.0.1 short-series gate check.
- Generated 192-row panel, compact run summary, public validation summary, and aggregate heatmap.
- Audit report, PDF builder, snapshot builder, publication manifest builder, and D-drive backup verifier.

## Licensing and limits

Project code is MIT licensed. Project-authored documentation and results are CC BY 4.0. Third-party sources keep their own terms. The V10 synthetic checks support only the tested software wiring and configuration; they do not validate threshold accuracy, TLog theory, general universality, clinical utility, or PDAC biology.
