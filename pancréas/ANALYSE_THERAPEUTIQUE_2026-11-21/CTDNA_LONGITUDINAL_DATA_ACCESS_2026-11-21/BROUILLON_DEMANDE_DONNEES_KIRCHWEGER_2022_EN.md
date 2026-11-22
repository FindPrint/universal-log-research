# Unsent data request draft — Kirchweger et al. 2022

**Status: draft only; not sent.**

**Subject:** Request for de-identified patient-level longitudinal ctDNA data (Kirchweger et al., 2022)

Dear Dr. Kirchweger and colleagues,

I am preparing a reproducibility-focused analysis of your study, *Prediction of response to systemic treatment by kinetics of circulating tumor DNA in metastatic pancreatic cancer* (Frontiers in Oncology, 2022; DOI 10.3389/fonc.2022.902177). Your data availability statement says the raw data supporting the conclusions will be made available by the authors without undue reservation.

Would you be able to share a de-identified patient-by-visit table and data dictionary for the 70-patient cohort, especially the serial measurements and response fields for the 32 patients described in the early-kinetics analysis? A stable pseudonymous patient key, relative visit time, ctDNA/MAF value and units, detection status, treatment line, radiological response category, missingness, and permitted-use and citation conditions would be sufficient for the initial audit. No direct identifiers are requested.

The first step will be a method-compatibility audit. Visits will remain grouped by patient; they will not be concatenated and treated as one uninterrupted biological series or as independent patients. The current pipeline version requires at least 50 valid control observations and does not preserve patient-group boundaries in its analysis entry point. I will not run the cohort as a pooled longitudinal series. If individual trajectories are too short for the current mode, I will report abstention and first validate a separate group-aware mode on synthetic data.

Please let me know whether a data-use agreement, institutional review, or other approval is required, and whether there is a preferred application route. I can provide the frozen analysis protocol before any use of the data.

Thank you for your time.

Best regards,

[Name and affiliation to be completed before any contact]
