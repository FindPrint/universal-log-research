# UNIVERSAL_LOG — Tiriac 2018 PDAC PDO run summary

- Requested target: `Gemcitabine`
- Domain: `pdac`
- Input observations: 60 PDOs
- Controls requested: 25; completed successfully: 25; errors/missing: 0
- Pipeline SHA-256: `72fd242c4cb26e5663fa40f1b4998de60c63e2aebbae2773d0d34d904152001b`
- Input CSV SHA-256: `eb9fc0b9092e6dd18eb6896ae27ade6c0410cb2ed7b2129e5e9ba384e191bad4`

## Pipeline outputs (source order; no ranking)

| Control column | Status | Domain | N | T0 (%) | T0 ambiguous | Control monotone |
|---|---|---|---:|---:|---|---|
| Paclitaxel | ok | pdac | 60 | 94.9803 | True | False |
| SN-38 | ok | pdac | 60 | 94.9803 | True | False |
| 5-FU | ok | pdac | 60 | 94.9803 | True | False |
| Oxaliplatin | ok | pdac | 60 | 96.6536 | True | False |
| Selumetinib | ok | pdac | 60 | 36.2505 | True | False |
| Afatinib | ok | pdac | 60 | 89.9607 | True | False |
| Bortezomib | ok | pdac | 60 | 94.9803 | True | False |
| Lapatinib | ok | pdac | 60 | 26.2739 | True | False |
| Sunitinib | ok | pdac | 60 | 34.577 | True | False |
| Olaparib | ok | pdac | 60 | 52.7223 | True | False |
| Nutlin-3 | ok | pdac | 60 | 27.916 | True | False |
| MK-2206 | ok | pdac | 60 | 43.1979 | True | False |
| KU-55933 | ok | pdac | 60 | 24.6317 | True | False |
| Everolimus | ok | pdac | 60 | 6.56847 | True | False |
| Celecoxib | ok | pdac | 60 | 84.941 | True | False |
| Ruxolitinib | ok | pdac | 60 | 63.5041 | True | False |
| SB5225334 | ok | pdac | 60 | 43.1979 | True | False |
| SGI-1776 | ok | pdac | 60 | 52.7223 | True | False |
| OSI-420 | ok | pdac | 60 | 58.0709 | True | False |
| TPCA-1 | ok | pdac | 60 | 79.9213 | True | False |
| LY2874455 | ok | pdac | 60 | 52.7223 | True | False |
| SF1670 | ok | pdac | 60 | 41.5431 | True | False |
| K-ras(G12C) Inhibitor 9 | ok | pdac | 60 | 69.882 | True | False |
| WIKI4 | ok | pdac | 60 | 81.5945 | True | False |
| Disulfuram | ok | pdac | 60 | 29.5581 | True | False |

## Reading limit

This is a cross-sectional PDO response-profile dataset. The pipeline uses each selected AUC control as its configured axis; it does not create calendar time or a disease progression trajectory. `T0` and ambiguity flags below are raw pipeline outputs. This table contains no drug ranking, patient recommendation, or claim of efficacy.

## Files

- Numeric summary: `PIPELINE_OUTPUT_SUMMARY.csv`
- Full machine-readable summary: `PIPELINE_OUTPUT_SUMMARY.json`
- Figure: `GEMCITABINE_T0_BY_CONTROL.png`
- Per-control console logs and all pipeline JSON/CSV/TXT exports are retained under `by_control/`.
