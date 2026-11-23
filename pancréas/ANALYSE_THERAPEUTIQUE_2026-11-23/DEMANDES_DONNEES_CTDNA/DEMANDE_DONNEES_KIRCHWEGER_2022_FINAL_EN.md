# Formal Academic Data Access Request — Kirchweger et al. (2022)

**Document Status:** Final Draft ready for sending (subject to user customization).  
**Target Publication:** *Prediction of response to systemic treatment by kinetics of circulating tumor DNA in metastatic pancreatic cancer*  
**Journal:** *Frontiers in Oncology*, 12:902177 (August 30, 2022)  
**DOI:** [10.3389/fonc.2022.902177](https://doi.org/10.3389/fonc.2022.902177)  
**Data Availability Statement:** *"The raw data supporting the conclusions of this article will be made available by the authors, without undue reservation."*

---

## Contact & Administrative Metadata

- **Primary Addressee (Corresponding Author):**  
  Dr. Holger Rumpold, MD  
  Department of Internal Medicine II / Center for Oncology and Hematology, Ordensklinikum Linz Barmherzige Schwestern, Linz, Austria  
  **Email:** `holger.rumpold@ordensklinikum.at`  
- **Co-authors to CC (optional):**  
  Dr. Patrick Kirchweger, MD (First Author), Department of Surgery, Ordensklinikum Linz, Linz, Austria  
- **Public Research Repository / Pre-registration:**  
  [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)  
- **Intended Use:** Non-commercial academic research, open-science methodological reproducibility and transition modeling.

---

## Email Message Template

**Subject:** Academic Data Request: De-identified serial ctDNA trajectory data from Kirchweger et al. (Frontiers in Oncology 2022, DOI: 10.3389/fonc.2022.902177)

Dear Dr. Rumpold and colleagues,

I hope this email finds you well.

I am writing to respectfully request access to the de-identified, patient-level serial circulating tumor DNA (ctDNA) dataset associated with your landmark 2022 publication in *Frontiers in Oncology*, entitled:
> *"Prediction of response to systemic treatment by kinetics of circulating tumor DNA in metastatic pancreatic cancer"* (DOI: 10.3389/fonc.2022.902177).

We note in your data availability statement that the raw data supporting your findings will be made available without undue reservation upon reasonable request. We greatly admire your prospective study design—specifically the high-frequency biweekly plasma sampling protocol—which provides a unique and vital empirical reference for understanding ctDNA kinetics in advanced pancreatic ductal adenocarcinoma (PDAC).

### Scientific Context & Objectives

Our research team develops and validates open-source, reproducibility-first computational frameworks for multi-stream ordered biological time series (**UNIVERSAL_LOG / TLog pipeline**; pre-registered and publicly documented at [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)). 

A central clinical question in our current investigation is whether non-linear dynamical systems estimators (e.g., critical slowing down, multi-scale complexity, and transition metrics) can detect therapeutic failure and pancreatic cancer progression significantly earlier than conventional imaging or serum CA19-9.

Having successfully validated our **Hierarchical Panel Mode (V1)** on controlled synthetic multi-trajectory panels (preserving within-patient group boundaries and abstaining from invalid sample concatenation), our immediate objective is to apply this method to real-world, high-frequency longitudinal ctDNA trajectories. Your cohort of 70 patients—and in particular the subset of 32 patients with complete serial measurements and definitive restaging outcomes (12 progressive disease vs. 20 non-progressive disease)—is the ideal benchmark to rigorously evaluate whether early kinetic signals can predict subsequent radiological response.

### Specific Data Requested

To conduct this audit and modeling, we are requesting a de-identified, patient-by-visit tabular dataset (in CSV, TSV, or Excel format) along with a brief data dictionary, containing where available:

1. **Patient & Visit Identifiers:**
   - A stable pseudonymous patient identifier (e.g., `Patient_01`, `Patient_02`) to group repeated measurements.
   - Sample identifier and sampling timeline: relative time from treatment initiation (e.g., baseline / Day 0, Week 2, Week 4, etc., or calendar days relative to Day 0).
2. **ctDNA & cfDNA Metrics:**
   - Quantitative ctDNA measurement: Mutant Allele Frequency (MAF / VAF %), absolute mutant copies per mL of plasma, or mutant fragment counts.
   - Specific gene/target tested (e.g., *KRAS* p.G12D, G12V, G12R, etc.).
   - Qualitative ctDNA status (detected vs. not detected) and assay limit of detection (LoD).
   - Total cell-free DNA (cfDNA) concentration (e.g., ng/mL plasma) and extracted DNA volume.
3. **Clinical & Outcome Covariates:**
   - Systemic chemotherapy regimen administered (e.g., FOLFIRINOX, Gemcitabine/nab-Paclitaxel) and treatment line.
   - Time of first restaging evaluation and objective radiological response category (RECIST 1.1: PD, SD, PR, CR) or continuous tumor burden metrics (e.g., sum of longest diameters, % change from baseline).
   - Serial serum CA19-9 measurements at corresponding visits (if recorded).
   - Progression-Free Survival (PFS) and Overall Survival (OS) intervals with right-censoring indicators.
4. **Data Dictionary:**
   - Brief variable definitions, units of measurement, assay methodology notes (e.g., ddPCR vs. NGS), and explanation of any missingness codes.

### Ethics, Confidentiality, and Governance

We operate strictly under academic, non-commercial standards:
- **Zero Re-identification Risk:** We do not request, nor will we accept, any direct personal identifiers (no names, dates of birth, medical record numbers, or hospital admission IDs). All data will remain completely anonymized / pseudonymized.
- **Strict Methodological Safeguards:** In our pipeline, serial observations are strictly bound to individual patient trajectories; repeated samples are never pooled or concatenated across distinct individuals as independent data points.
- **Compliance & Agreements:** We are fully prepared to review and execute an institutional Data Transfer / Data Use Agreement (DUA/MTA), submit to an expedited institutional review board / ethics review if required by your institution, or comply with any transfer terms you specify.
- **Academic Attribution:** Your primary publication will be prominently cited, and all methodological comparisons will explicitly reference your findings as the original benchmark.

If participant-level real data cannot be transferred immediately or requires specific regulatory approvals, even an initial mock/schema-matched test file or intermediate summary table would be tremendously appreciated to assist our ongoing pipeline audit.

Please let us know your preferred procedure or if any formal application forms need to be completed. We would be delighted to schedule a brief call or provide any additional information about our open-source protocol.

Thank you very much for your time, consideration, and leadership in liquid biopsy research.

Respectfully yours,

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

- [ ] Confirm email address: `holger.rumpold@ordensklinikum.at`
- [ ] Replace all bracketed text `[...]` with your actual name, affiliation, and contact details.
- [ ] Ensure sending from an institutional / academic email address (.edu, .org, hospital/university domain).
- [ ] Attach your academic CV or institutional biosketch if required.
- [ ] Link to the public GitHub repository: [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research).
