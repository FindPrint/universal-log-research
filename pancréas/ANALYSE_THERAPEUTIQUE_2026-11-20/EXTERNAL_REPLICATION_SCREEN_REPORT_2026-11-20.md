# PDAC external-data screen and pipeline gate — 2026-11-20

## Decision recorded before/after the pilot

The 2025 Nature Communications drug-response matrix contains 46 PDO models and 63 drug AUC columns. It is the closest fully public multi-drug matrix found in this screen, but it is below the UNIVERSAL_LOG runtime minimum of 50 valid points. One prespecified diagnostic call was run to observe the pipeline's behavior at this boundary; the pipeline rejected the input before calculating estimators. No other control calls were launched because they would encounter the same sample-count gate. The matrix is not counted as external validation.

## Dataset screening

| Candidate | Available evidence | Decision |
|---|---|---|
| Chen et al., Nature Communications 2025 | Public `All Drugs AUC` sheet: 63 drugs × 46 PDOs. | Prepared without imputation or scaling. One call (Gemcitabine target, APR-246 control) was rejected: 46 points, minimum 50. Remaining 61 controls not run. Pilot only. |
| Nicholson et al., Annals of Surgery 2024 | Article reports 95 PDOs and IC50 profiles for 5 agents; accessible supplement includes matching code and aggregate clinical tables. The inspected supplement does not provide a PDO-by-drug IC50 matrix. | Not runnable from the accessed public files; do not reconstruct values from plots or aggregate tables. |
| Feizi et al., AACR 2025 abstract | Reports screening ~3,000 compounds at one dose and 600 at six doses on 120 PDAC PDOs. No row-level matrix was linked in the proceedings inspected. | Potential data-access lead, not a runnable public dataset. |
| Zhu et al., arXiv 2026 | Four PDO screening datasets total 57 organoids across colorectal, head-and-neck, and sarcoma models. | Excluded from PDAC-specific replication; disease domain differs. |
| GSE271300, Singhal et al. | Existing local analysis has 3/3 and 4/3 mice by treatment in PC69/PC106. | Not a patient-derived drug-AUC cohort; the mouse-level sample size is too small for the pipeline's 50-point run. Do not use cell counts as independent biological replicates. |

## Pilot configuration

- Pipeline: `UNIVERSAL_LOG_v5.9.4.py`, `.venv`, domain `pdac`, mode `fast`, seed 42, L7b-light.
- Target: Gemcitabine, fixed in advance to match the previous Tiriac all-controls experiment.
- Planned controls: the other 62 drug columns, each individually, with all remaining numeric columns retained as fluxes.
- Actual call: APR-246 as control; the first non-target drug in source order.
- Input: 46 PDO rows, 63 drug AUC fluxes, zero missing cells. Source PDO ordering was preserved; values were transposed only.
- Observed stdout error: `Série trop courte : 46 points valides. Au moins 50 sont requis avec la configuration actuelle.`
- Result: no estimator outputs were produced; this is a pipeline input-gate result, not a biological finding.

## Next data requirement

To perform a valid independent pipeline replication, obtain a public or authorized patient/organoid-level PDAC drug-response matrix with at least 50 valid independent PDO models and usable numeric response values. Prefer a dataset with paired patient clinical outcomes, but do not infer individual outcomes from cohort-level summaries. The Toronto 58/120-PDO screening program is a data-access lead; no request was sent.

## Source records

- Tiriac et al. 2018: https://doi.org/10.1158/2159-8290.CD-18-0349
- Chen et al. 2025: https://doi.org/10.1038/s41467-025-57520-3
- Nicholson et al. 2024: https://doi.org/10.1097/SLA.0000000000006517
- Feizi et al. AACR 2025 abstract: https://www.aacr.org/wp-content/uploads/2025/05/AACR2025_Proceedings_050725.pdf
- Zhu et al. 2026 preprint and data: https://arxiv.org/abs/2611.15769 and https://doi.org/10.5281/zenodo.22920452
- GSE271300: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300
