# Formal Academic Data Access Request — Yin et al. (Nature Communications 2025)

**Document Status:** Final Draft ready for sending (subject to user customization).  
**Target Publication:** *Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients*  
**Journal:** *Nature Communications*, 16, Article number: 2214 (March 2025)  
**DOI:** [10.1038/s41467-025-57520-3](https://doi.org/10.1038/s41467-025-57520-3)  
**Target Experimental Dataset:** High-throughput pharmacogenomic drug screening across 46 patient-derived pancreatic adenocarcinoma organoids (PDOs) and 63 antineoplastic compounds (multi-point concentration-response raw viability data).

---

## Contact & Administrative Metadata

- **Primary Addressee (Corresponding Author):**  
  Professor Gang Jin, MD, PhD  
  Department of Hepatobiliary Pancreatic Surgery, Changhai Hospital, Naval Medical University (Second Military Medical University), Shanghai, China  
  **Email:** `jingang@smmu.edu.cn`  
- **Co-Addressee / First Author:**  
  Dr. Xiaoyi Yin, MD, PhD  
  Department of Hepatobiliary Pancreatic Surgery, Changhai Hospital, Naval Medical University, Shanghai, China  
  **Email:** `jamesyin1991@hotmail.com`  
- **Co-corresponding Authors to CC (optional):**  
  Prof. Jing Li, Prof. Hongbo Yang (Changhai Hospital / Fudan University)  
- **Public Research Repository / Pre-registration:**  
  [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)  
- **Intended Use:** Non-commercial academic research, computational pharmacodynamics, and mathematical transition modeling on short dose-response curves.

---

## Email Message Template

**Subject:** Academic Data Request: Raw multi-point dose-response screening data from Yin et al. (Nature Communications 2025, DOI: 10.1038/s41467-025-57520-3)

Dear Professor Jin, Dr. Yin, and colleagues,

I hope this message finds you well.

I am writing to congratulate you and your team on your seminal study published recently in *Nature Communications*:
> *"Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients"* (*Nature Communications* 16: 2214, 2025; DOI: 10.1038/s41467-025-57520-3).

Your work provides an extraordinary and comprehensive germline landscape of pancreatic adenocarcinoma (PAAD). Beyond your remarkable genomic discoveries, your high-throughput drug screening campaign spanning **46 patient-derived pancreatic cancer organoids (PDOs) tested against 63 clinical and investigational antineoplastic agents** represents one of the most rigorous and valuable preclinical pharmacogenomic resources developed to date for pancreatic cancer.

### Scientific Context & Research Objectives

Our research team develops open-source, reproducibility-focused computational pipelines designed to detect dynamical transitions, critical slowing down, and phase shifts in biological systems (**UNIVERSAL_LOG / TLog framework**; publicly documented and pre-registered at [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)).

While our primary pipeline was engineered for longitudinal time series, we are currently developing an audit-validated extension: the **Short Dose-Response Curve Module** (`UNIVERSAL_LOG_dose_response_v1.py`). Conventional drug sensitivity metrics (e.g., standard IC50 or AUC from 4-parameter logistic / Hill fits) often struggle with non-monotone responses, heterogeneous plateau effects, or partial response dynamics across sparse concentration gradients.

Our objective is to apply specialized, robust complexity estimators (including Detrended Fluctuation Analysis, Petrosian fractal dimension, Katz fractal dimension, Sevcik complexity, and Sample Entropy) directly across discrete concentration gradients ($N = 7\text{ to }9$ doses per compound). By treating drug concentration as an ordered response axis, our module aims to:
1. Estimate non-parametric transition thresholds ($T_{0,\text{dose}}$) corresponding to the onset of pharmacological destabilization;
2. Quantify response complexity using biological replicates as the resampling unit;
3. Compare TLog-derived inflection metrics with conventional Hill $IC_{50}$ curves to uncover subgroup-specific drug susceptibilities linked to distinct genetic mutations (e.g., *BRCA1/2*, *PALB2*, *ATM*, or Chinese-predominant variants like *CFTR*, *RAD51D*, *FANCA*).

### Specific Data Requested

While your article and supplementary files summarize overall drug sensitivity scores and fitted metrics, our mathematical analysis requires the **raw, multi-point concentration-response measurements** prior to non-linear regression fitting.

We respectfully request access to the de-identified raw screening matrices (in CSV, TSV, or Excel format) comprising:
1. **Raw Concentration-Response Measurements:**
   - For each organoid line ($\approx 46$ PDOs) and compound ($\approx 63$ drugs): the exact tested concentrations (concentration values, units, and dilution steps).
   - The corresponding raw response values at each concentration point (e.g., raw luminescence/fluorescence counts, or percentage cell viability normalized to negative/vehicle control).
   - Replicate-level data (technical and biological replicates per concentration, rather than just pre-computed mean values).
2. **Screening Metadata & Controls:**
   - Positive kill controls (e.g., Staurosporine or high-dose baseline) and negative vehicle controls (e.g., 0.1% DMSO) for normalization quality checks.
   - Compound identifiers (chemical names, target pathways, and mechanism of action).
3. **Paired Genomic & Organoid Annotations:**
   - Organoid identifier matching the published patient genomic status (e.g., pathogenic germline mutation status in *BRCA1*, *BRCA2*, *PALB2*, *ATM*, *CDKN2A*, *CFTR*, *RAD51D*, etc., and key somatic drivers such as *KRAS* codon variants).

### Governance, Collaboration, and Academic Ethics

We conduct all investigations in accordance with strict academic open-science principles:
- **Non-Commercial Academic Use:** The requested data will be utilized strictly for academic computational methodology and pharmacogenomic research. No commercial exploitation will occur.
- **Data Protection & De-identification:** The dataset involves in vitro organoid screens linked to pseudonymous identifiers; no direct personal identifiers will be requested or stored.
- **Formal Data Transfer / MTA:** We are fully prepared to sign a formal Data Transfer Agreement (DTA) or Material/Data Use Agreement with Changhai Hospital / Naval Medical University.
- **Attribution & Collaborative Acknowledgment:** Your *Nature Communications* paper will be cited prominently as the biological foundation of the study. Furthermore, if you and your team are interested in exploring how our transition pipeline characterizes your organoid pharmacotypes, we would enthusiastically welcome intellectual collaboration, joint analysis, and co-authorship.

Please let us know your requirements or if you would like to arrange a brief virtual meeting to discuss this research. We are happy to provide our pre-registered protocol, synthetic validation benchmarks, or any additional details.

Thank you very much for your time, consideration, and leadership in pancreatic oncology research.

With highest regards,

**[INVESTIGATOR NAME, MD/PhD]**  
[Academic Title / Position]  
[Laboratory / Department Name]  
[Institution / University]  
[Institutional Address]  
**Email:** [Institutional Email Address]  
**Phone:** [Institutional Telephone Number]  
**Project GitHub:** [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)  
**ORCID:** [0000-XXXX-XXXX-XXXX]

---

## Checklist for the Sending Researcher (To Complete Before Sending)

- [ ] Confirm email addresses: `jingang@smmu.edu.cn` (Prof. Gang Jin) and `jamesyin1991@hotmail.com` (Dr. Xiaoyi Yin).
- [ ] Replace all bracketed text `[...]` with your full name, affiliation, and institutional contact details.
- [ ] Send from an authorized institutional / university email account.
- [ ] Direct the authors to the GitHub pre-registration: [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research).
- [ ] (Optional) Attach a 1-page summary of the `UNIVERSAL_LOG_dose_response_v1.py` specification if requested.
