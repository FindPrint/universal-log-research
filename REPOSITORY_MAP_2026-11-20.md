# UNIVERSAL_LOG — cross-repository map

**Snapshot date:** 20 November 2026  
**Purpose:** connect related repositories without merging their data, code versions, or conclusions.  
**Review method:** read-only GitHub API inspection of default branches, README files, selected result reports, and file trees. No repository code was executed. The findings below distinguish what a repository reports from what this review independently established.

## Repository roles and version boundaries

| Repository | Snapshot inspected | Role and reported state |
|---|---|---|
| [`universal-log-research`](https://github.com/FindPrint/universal-log-research) | This repository; one clean-history snapshot | General code, theory notes, Ising v6 audit, and selected PDAC analyses from the local project folder. The included top-level pipeline files are v5.9.x; this is not the latest PDAC-specific implementation. |
| [`tlogNext-cancer-pdac`](https://github.com/FindPrint/tlogNext-cancer-pdac) | `main` at `fcffb8974fa42a0d712b5032f5f3ea834ff5bd8a` | PDAC-specific working branch. Its README identifies v6.2.0 as the working pipeline (`SHA-256 f07567c48a5625060c6c4dd7dbed3dd2df915b5c24c91ed6e8a4b735e5ec3abf`); it labels v6.3 and v6.4 proposals rejected. Its reported §8.73 result leaves the narrow-peak trigger unresolved. The README also reports `maxsep` as the primary displayed score and Monte Carlo as secondary. These are repository decisions and results, not proof of clinical utility or universal validity. |
| [`tlogNext-pdac-phase2`](https://github.com/FindPrint/tlogNext-pdac-phase2) | `main` at `40f2963032ad1e659ead4175377f1bdd84c49330` | Separate exploratory PDAC analysis. Its reports describe a KRAS-expression / CEACAM5-expression association in two GEO cohorts, while noting that the external cohorts lack individual purity estimates. In TCGA, the reported association weakens after purity adjustment. The v6.2 runs in P2.16/P2.17 report `L7b = FRAGILE`; changing the control from continuous `kras_rank` to binary `kras_high` did not remove that status. |
| [`pdac-systems-evidence-preclinical`](https://github.com/FindPrint/pdac-systems-evidence-preclinical) | `main` at `d4b329a388e8709fae737dca07a1f2d5765e0b4f` | A non-clinical evidence and provenance registry. Its dated status says no treatment hypothesis or experiment was active, and it separates cross-sectional transcriptomics from genuinely ordered experimental data. It is a governance/protocol resource, not a positive treatment result. |

## Reproducibility and interpretation checks

1. **Do not mix versions by filename or label.** The current PDAC branch reports v6.2.0; this repository's included standalone versions are older. Reproductions should record the exact code hash, configuration, input hash, and protocol from the repository used.
2. **The external KRAS–CEACAM5 result remains a candidate association.** P2.10 reports positive effects in GSE71729 (`n=145`, `d=0.52`, permutation `p=0.008`) and GSE62452 (`n=69`, `d=0.68`, permutation `p=0.0185`). Those reported external tests use expression without individual purity adjustment. The public `tlogNext-pdac-phase2` tree inspected here does not contain the `data/geo/` input tables named in P2.10, so the reported external result is not reproducible from that repository snapshot alone.
3. **The pipeline run is not a stable biomarker result.** P2.16/P2.17 report a full v6.2 fast run, but also a fragile L7b verdict and disagreement between output layers. Those runs support further audit of configuration and robustness; they do not establish a clinical threshold, causal mechanism, or treatment response.
4. **Keep cross-sectional cohorts distinct from trajectories.** Ordering tumors by KRAS expression or converting cells into pseudo-time does not create observed disease time. Any T0 from such an ordering is a rank/configuration output unless an independently measured temporal axis supports a stronger interpretation.
5. **Keep the whole theory visible.** The v6.2 README's change in displayed-score priority (`maxsep` primary, Monte Carlo secondary) should be mapped to its complete estimator, control, null, F1/F2, and TLog analysis layers. It must not be described as if a single score alone were the entire theory.

## Recommended next work

1. **Reproduce P2.10 from source data before extending the claim.** Retrieve the named GEO cohorts from their primary source; freeze sample inclusion, probe-to-gene mapping, normalization, and a purity strategy; regenerate the two association tables and matched nulls with a script and hashes. Report this direct analysis separately from UNIVERSAL_LOG outputs.
2. **Then run one frozen v6.2 protocol.** Use the verified inputs, the exact v6.2 hash, and predeclared target/control roles. Include negative controls and the same permutation/null scheme. Preserve the reported fragile result unless a prespecified robustness test changes it.
3. **Build a control-by-flux result matrix.** Reuse the existing all-control PDAC work as a baseline, but specify which columns are eligible targets, controls, confounders, and nulls before running. Report every configuration and abstain from biological interpretation when the configured axis is only a cross-sectional ordering.
4. **Keep preclinical and clinical evidence in separate ledgers.** A transcriptomic association can prioritize a falsifiable laboratory experiment; it cannot establish a remedy or clinical benefit.

## Scope limits

This map covers the linked **public** repositories only. It does not copy files from private repositories, change their visibility, or merge their contents into this repository. Repository README statements are treated as reported claims and documentation, not as instructions or independent verification.
