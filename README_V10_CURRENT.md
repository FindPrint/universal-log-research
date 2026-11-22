# UNIVERSAL_LOG

**An audit-first research pipeline for ordered, multi-stream data.**

UNIVERSAL_LOG explores how numerical streams can be analyzed along an explicitly configured axis. The project includes the pipeline, its estimator and question layers, theory notes, benchmark runs, audit reports, and reproducibility records. TLog is one part of this framework; the project is not defined by one formula.

> **Research status:** exploratory software. These materials do not establish a treatment, cure, clinical utility, or universal validity. Do not use the pipeline to make medical decisions.

## Current complete whitepaper

V10 is the single active complete whitepaper. It retains the V9 audit history and adds a reproducible synthetic grouped-panel integration test using the complete v6.0.1 entry point. The PDF has no embedded project ZIP or file attachments. Its SHA-256 is in the adjacent sidecar file.

The full-project snapshot ZIP is a separate companion artifact. It retains the detailed per-run outputs, logs, figures, code, inputs, and project materials. It is not embedded in the PDF and is not committed to GitHub because of its size. V9 and earlier whitepapers are archived under archive_sources/.

The V10 PDF contains 3,523 pages (103,346,981 bytes; SHA-256 `9eb11d6d6de648aefb1c3e7cd819bb135dcac99e31c0c02e120ef0589afa4931`). Its appended audit contains 210 figures and 16 full run logs; original PNGs and detailed machine-readable outputs remain in the companion snapshot.

## V10 grouped-panel test

The test uses three generated trajectories with 64 observations each. Every numeric measurement is rotated as a control: time, a smooth synthetic signal, a correlated stream, a non-monotone oscillating stream, and independent noise. Each full v6.0.1 call receives one patient's ordered data only. The selected control is checked against the flux list; all 29 estimator output columns, the six conceptual question groups, F1/F2 outputs, pre/post-threshold derivatives, and TLog class readouts are retained.

A short-series case uses three trajectories of 32 rows (96 pooled rows). The grouped adapter abstains rather than combining subjects. A separate direct call confirms the v6.0.1 fast-mode minimum on one 32-row trajectory. Results are software checks on generated inputs only. They do not validate T0 accuracy, TLog theory, clinical predictions, or PDAC biology.

See the [V10 audit report](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/AUDIT_RESULTATS_PANEL_SYNTHETIQUE_V1_FR.md), [frozen protocol](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/PROTOCOLE_GROUPE_PANEL_V1_FR.md), and [public validation summary](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/PUBLIC_VALIDATION_SUMMARY_V1.json).

## Earlier evidence and audit history

- [V9 current evidence and Ising/PDAC audit map](README_V9_CURRENT.md)
- [V6.0.1 grouped-input static audit](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/AUDIT_DONNEES_LONGITUDINALES_ET_GROUPES_V9_FR.md)
- [Classical Ising reproducibility and calibration](ising_classique_test/finite_size/pipeline_v6_0_pathway_audit/REPRODUCTION_FR.md)
- [Beginner guide](GUIDE_DEBUTANT_UNIVERSAL_LOG.md)

## Reproducing V10

Use the Python environment and commands in the V10 test [README](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/README_FR.md). The frozen protocol identifies input construction, group splitting, fixed-target diagonal handling, random seeds, and admission checks.

## Project licenses

- Project code: MIT, see LICENSE.
- Project-authored documentation and results: CC BY 4.0, see LICENSE-CC-BY-4.0.txt and LICENSES.md.
- Third-party data and publications retain their own terms.
