# Formal Academic Data Access Request — Edland et al. (2023)

**Document Status:** Final Draft ready for sending (subject to user customization).  
**Target Publication:** *Monitoring of circulating tumour DNA in advanced pancreatic ductal adenocarcinoma predicts clinical outcome and reveals disease progression earlier than radiological imaging*  
**Journal:** *Molecular Oncology*, 17(8): 1466–1478 (Published online May 2023, Issue August 2023)  
**DOI:** [10.1002/1878-0261.13472](https://doi.org/10.1002/1878-0261.13472)  
**PubMed Central / PMID:** PMC10403759 / 37194605

---

## Contact & Administrative Metadata

- **Primary Addressee (Corresponding Author):**  
  Professor Oddmund Nordgård, PhD  
  Department of Hematology and Oncology / Department of Pathology, Stavanger University Hospital (Helse Stavanger HF), Stavanger, Norway  
  **Email:** `oddmund.nordgard@sus.no`  
- **Co-authors to CC (optional):**  
  Dr. Karin Hestnes Edland, MD (First Author), Department of Hematology and Oncology, Stavanger University Hospital  
- **Public Research Repository / Pre-registration:**  
  [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)  
- **Intended Use:** Non-commercial academic research, open-science methodological reproducibility, and dynamical transition modeling.

---

## Email Message Template

**Subject:** Academic Data Request: De-identified longitudinal ctDNA trajectory matrix from Edland et al. (Molecular Oncology 2023, DOI: 10.1002/1878-0261.13472)

Dear Professor Nordgård and colleagues,

I hope this email finds you well.

I am writing to respectfully request access to the de-identified, patient-level longitudinal circulating tumor DNA (ctDNA) dataset generated in your outstanding study published in *Molecular Oncology*:
> *"Monitoring of circulating tumour DNA in advanced pancreatic ductal adenocarcinoma predicts clinical outcome and reveals disease progression earlier than radiological imaging"* (Molecular Oncology 2023; 17(8): 1466–1478; DOI: 10.1002/1878-0261.13472).

Your rigorous prospective cohort—encompassing 81 patients with locally advanced or metastatic pancreatic ductal adenocarcinoma (PDAC), 425 serial blood samples taken every 4 weeks, and 298 longitudinal ctDNA measurements analyzed via joint modeling—represents one of the most comprehensive and high-quality serial ctDNA datasets worldwide. Your findings demonstrating that rising ctDNA detects disease progression with a substantial lead time over routine radiological imaging provide critical clinical motivation for our current computational research.

### Scientific Context & Objectives

Our group is developing and benchmarking an open-source, reproducibility-first computational pipeline for analyzing complex multi-stream biological time series (**UNIVERSAL_LOG / TLog framework**; publicly pre-registered and accessible at [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)).

The fundamental aim of our project is to evaluate whether non-linear dynamical systems indicators (such as critical slowing down, complexity estimators, Petrosian/Katz fractal dimension, and transition metrics) can systematically identify transition states preceding clinical disease relapse.

We have recently finalized and synthetically validated a **Hierarchical Panel Mode (V1)**, specifically designed to handle longitudinal multi-patient clinical cohorts. Our architecture enforces strict patient-trajectory boundaries, ensuring that serial visits from an individual are analyzed as an intact temporal trajectory and never artificially concatenated or treated as independent patients. 

Your longitudinal cohort of 81 patients is exceptionally suited to independently test and calibrate this methodology, allowing us to evaluate whether our transition metrics can reproduce or even enhance the early detection lead-time that your team so clearly described.

### Specific Data Requested

While the supplementary materials of your paper provide valuable cohort summaries and hazard ratio tables, we could not locate a downloadable, patient-by-visit granular data matrix. We would be immensely grateful if you could share a de-identified tabular dataset (CSV, TSV, or Excel) containing:

1. **Patient & Temporal Coordinates:**
   - Pseudonymous patient identifier (e.g., `Patient_01`, `Patient_02`) stable across serial sampling visits.
   - Sampling timeline: relative time from baseline / start of systemic therapy (in weeks or days), sample number, and visit designation (e.g., pre-treatment, 4-week, 8-week, restaging).
2. **Quantitative ctDNA & Biomarker Measurements:**
   - ctDNA quantitative values: *KRAS* mutant copies per mL of plasma and Mutant Allele Frequency (MAF / VAF %).
   - Qualitative ctDNA call (positive / negative / below limit of detection) and assay detection/quantification limits (LoD / LoQ).
   - Total cell-free DNA (cfDNA) concentration (ng/mL) or yield.
   - Concurrent serum CA19-9 measurements (kU/L) at each corresponding visit.
3. **Clinical Milestones & Outcomes:**
   - Date or relative time to objectively confirmed radiological progression (RECIST 1.1) and dates of CT/MRI restaging scans.
   - Progression-Free Survival (PFS) and Overall Survival (OS) time intervals with right-censoring status.
   - Systemic chemotherapy regimen administered (e.g., FOLFIRINOX, Gemcitabine + nab-Paclitaxel) and treatment line.
4. **Data Dictionary & Schema:**
   - Definitions of variables, units, analytical transformations (e.g., log-transformations used in joint models), and missing-value flags.

### Ethics, Privacy, and Data Governance

We are committed to the highest standards of scientific integrity and research governance:
- **Strict Privacy & De-identification:** We require no direct personal identifiers (no names, national ID/Fødselsnummer, dates of birth, or hospital administrative numbers). All records will remain strictly de-identified.
- **Controlled Academic Use:** All data will be utilized strictly for non-commercial, academic methodological research. The software and validation protocols are open-source and pre-registered. No individual patient treatment or clinical decision-making will be derived from these analyses.
- **Institutional & Ethics Compliance:** We are fully prepared to execute a formal Data Transfer Agreement (DTA) or Data Use Agreement (DUA) with Stavanger University Hospital (Helse Stavanger HF), and to comply with any requirements of the Regional Committees for Medical and Health Research Ethics (REK) in Norway.
- **Citation & Authorship Acknowledgment:** Your seminal article will be prominently cited, and we welcome any discussion regarding collaborative input, co-authorship, or specific attribution requirements.

If full participant-level data transfer requires dedicated ethics amendments or data access committee review, we would equally welcome an initial schema-matched synthetic or anonymized pilot subset to begin our data-ingestion audit.

Please let us know the appropriate administrative or ethical channel to initiate this request. We would be pleased to provide our formal analysis protocol or schedule a video conference at your convenience.

Thank you very much for your time, consideration, and pioneering contributions to precision oncology in PDAC.

Warm regards,

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

- [ ] Confirm email address: `oddmund.nordgard@sus.no`
- [ ] Replace all bracketed text `[...]` with your actual name, affiliation, and contact details.
- [ ] Ensure sending from an institutional / university email address.
- [ ] Attach institutional affiliation / short academic bio.
- [ ] Direct the recipient to the pre-registered repository: [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research).
