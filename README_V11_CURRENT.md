# UNIVERSAL_LOG

**An audit-first research pipeline for ordered, multi-stream data.**

UNIVERSAL_LOG analyzes numerical streams along an explicitly configured control axis. Its theory is the full pipeline, including data configuration, estimators, question layers, TLog, diagnostics, and audit outputs.

> **Research status:** exploratory software. These materials establish no treatment, cure, clinical utility, or universal validity. Do not use the pipeline to make medical decisions.

## Current complete whitepaper

V11 is the current complete whitepaper. It retains the V10 audit history and appends a frozen sensitivity campaign with 35 full v6.0.1 calls over seven synthetic inputs and five controls. It includes the unmodified v6.0.1 core source, environment lock, corrected report, runtime summary, all synthetic inputs, derived tables, per-run derivative tables and figures, execution logs, and all per-run JSON/CSV/TXT/HTML/JSONL text artifacts. The PDF has no embedded ZIP or attachments. Its SHA-256 is in the adjacent sidecar.

The full-project ZIP is a separate companion artifact and preserves exact files. V10 and earlier complete whitepapers are archived under `archive_sources/`.

## V2 sensitivity campaign — measured results

- Technical status: **35/35 calls complete; all 8 frozen integrity assertions passed**. Every input was tested against `time_index`, `signal_primary`, `marker_correlated`, `marker_oscillatory`, and `noise_independent`. The selected control was excluded from the analyzed flux list in all calls; the target-diagonal fallback was explicit; all 29 estimator outputs were present.
- Data scope: generated synthetic series only. No patient, clinical, or biological data were used.
- T0 was emitted in all 15 null-condition runs. Because no alarm/abstention rule was specified, this is an output-availability count, **not** a false-alarm rate.
- For the four non-null `time_index` runs with a known injected center of 58%, absolute localization errors ranged from 3.99 to 38.15 percentage points (median 28.00). Replication is sparse and uneven; this pilot does not establish reliable threshold localization.
- Across all configurations T0 ranged from 4.73% to 96.15%, showing substantial configuration-dependent output variation in this synthetic campaign. This is descriptive sensitivity, not a claim about general or biological behavior.
- Four calls exceeded 300 seconds. The longest took 729.6 seconds (`marker_correlated`, N=64, strong, seed 20261124). Per-estimator profiling has not yet been done, so the runtime outliers do not identify a cause.

The [corrected V2 audit report](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/AUDIT_RESULTATS_SENSIBILITE_V2_FR.md), [erratum](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/CORRECTION_RAPPORT_V2_FR.md), [frozen protocol](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/PROTOCOLE_SENSIBILITE_TRANSITIONS_V2_FR.md), and [public summary](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/PUBLIC_VALIDATION_SUMMARY_V2.json) distinguish observations from interpretation.

## Earlier work

- [V10 panel integration report](pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/AUDIT_RESULTATS_PANEL_SYNTHETIQUE_V1_FR.md)
- [V9 project and evidence map](README_V9_CURRENT.md)
- [Beginner guide](GUIDE_DEBUTANT_UNIVERSAL_LOG.md)

## Licenses

- Project code: MIT, see LICENSE.
- Project-authored documentation and results: CC BY 4.0, see LICENSE-CC-BY-4.0.txt and LICENSES.md.
- Third-party data and publications retain their own terms.
