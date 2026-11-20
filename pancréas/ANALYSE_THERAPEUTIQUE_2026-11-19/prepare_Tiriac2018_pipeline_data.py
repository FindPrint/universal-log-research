from __future__ import annotations

import hashlib
import json
from pathlib import Path

import openpyxl
import pandas as pd


HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE / "candidate_Tiriac2018"
SUPP = SOURCE_DIR / "supplement_4775187.xlsx"
COHORT = SOURCE_DIR / "supplement_4775186.xlsx"
OUT_CSV = SOURCE_DIR / "Tiriac2018_60PDO_completecase_drug_AUC.csv"
MANIFEST = SOURCE_DIR / "PIPELINE_INPUT_MANIFEST.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_table(workbook: openpyxl.Workbook, sheet_name: str) -> pd.DataFrame:
    sheet = workbook[sheet_name]
    rows = sheet.iter_rows(min_row=2, values_only=True)
    header_row = next(rows)
    headers = [str(value).strip() if value is not None else "" for value in header_row]
    data = []
    for row in rows:
        sample_id = row[0] if row else None
        if sample_id is None or str(sample_id).strip() == "":
            break
        record = {headers[i]: row[i] for i in range(min(len(headers), len(row))) if headers[i]}
        data.append(record)
    frame = pd.DataFrame(data)
    if "Sample ID" not in frame:
        raise ValueError(f"Missing Sample ID in {sheet_name}")
    if frame["Sample ID"].duplicated().any():
        dupes = frame.loc[frame["Sample ID"].duplicated(), "Sample ID"].tolist()
        raise ValueError(f"Duplicate PDO identifiers in {sheet_name}: {dupes}")
    return frame


def main() -> None:
    if not SUPP.is_file() or not COHORT.is_file():
        raise FileNotFoundError("Expected both official AACR supplementary workbooks in candidate_Tiriac2018")

    workbook = openpyxl.load_workbook(SUPP, read_only=True, data_only=True)
    chemo = read_table(workbook, "Chemo ")
    targeted = read_table(workbook, "Targeted")
    workbook.close()

    # Table S4A's sixth column is a categorical annotation, not a numeric response flux.
    chemo_fluxes = [column for column in chemo.columns if column not in {"Sample ID", "Insensitive"}]
    targeted_fluxes = [column for column in targeted.columns if column != "Sample ID"]
    if not chemo_fluxes or not targeted_fluxes:
        raise ValueError("No numeric drug-response flux columns were found")

    # Trim whitespace only in IDs (one source cell contains a trailing space), then
    # retain the exact shared cohort. Do not impute or pair the source-specific rows.
    chemo["Sample ID"] = chemo["Sample ID"].astype(str).str.strip()
    targeted["Sample ID"] = targeted["Sample ID"].astype(str).str.strip()
    if chemo["Sample ID"].duplicated().any() or targeted["Sample ID"].duplicated().any():
        raise ValueError("Trimming whitespace creates duplicate PDO IDs")
    chemo_ids = set(chemo["Sample ID"])
    targeted_ids = set(targeted["Sample ID"])
    chemo_only = sorted(chemo_ids - targeted_ids)
    targeted_only = sorted(targeted_ids - chemo_ids)

    # Preserve S4A sample order; join S4B profiles by normalized, exact PDO ID.
    merged = chemo[["Sample ID", *chemo_fluxes]].merge(
        targeted[["Sample ID", *targeted_fluxes]], on="Sample ID", how="inner", validate="one_to_one", sort=False
    )
    merged = merged.rename(columns={"Sample ID": "PDO_ID"})
    fluxes = [*chemo_fluxes, *targeted_fluxes]
    for column in fluxes:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    missing_by_flux = {column: int(merged[column].isna().sum()) for column in fluxes if merged[column].isna().any()}
    incomplete_ids = merged.loc[merged[fluxes].isna().any(axis=1), "PDO_ID"].astype(str).tolist()
    source_rows_matched = int(len(merged))
    # Use one common complete-case cohort for every target/control pair. No values
    # are imputed, and excluded PDO identifiers are retained in the manifest.
    merged = merged.dropna(subset=fluxes).reset_index(drop=True)
    if len(merged) < 50:
        raise ValueError(
            f"Only {len(merged)} complete matched PDOs remain; v5.9.4 fast-mode minimum is 50"
        )

    merged.to_csv(OUT_CSV, index=False, float_format="%.17g", encoding="utf-8")
    manifest = {
        "dataset": "Tiriac et al. 2018 PDAC patient-derived organoid drug AUC tables",
        "article_doi": "10.1158/2159-8290.CD-18-0349",
        "source_article_url": "https://aacrjournals.org/cancerdiscovery/article/8/9/1112/10165/Organoid-Profiling-Identifies-Common-Responders-to",
        "source_files": [
            {"path": SUPP.name, "sha256": sha256(SUPP), "table": "Table S4A (Chemo) and S4B (Targeted)"},
            {"path": COHORT.name, "sha256": sha256(COHORT), "table": "Table S1A-D cohort/genomic descriptors; not used as fluxes"},
        ],
        "input_csv": OUT_CSV.name,
        "input_sha256": sha256(OUT_CSV),
        "observations": int(len(merged)),
        "source_table_rows": {"S4A_chemo": int(len(chemo)), "S4B_targeted": int(len(targeted))},
        "observation_unit": "PDO model; only PDO IDs with both chemotherapy and targeted-agent AUC profiles",
        "matched_pdo_ids": int(len(merged)),
        "unmatched_source_ids_excluded_without_imputation": {
            "chemo_only": chemo_only,
            "targeted_only": targeted_only,
            "cohort_sheet_check": "S1A marks hT83 Chemo=YES/Targeted=NO and hT96 Chemo=NO/Targeted=YES",
        },
        "matched_before_complete_case_filter": source_rows_matched,
        "missing_values_by_flux_before_filter": missing_by_flux,
        "incomplete_matched_pdo_ids_excluded_without_imputation": incomplete_ids,
        "complete_case_n_after_filter": int(len(merged)),
        "id_normalization": "leading/trailing whitespace stripped; S4B hF74 has a trailing space and matches S4A hF74",
        "row_order": "S4A published sample order preserved for shared PDO IDs; targeted rows joined by normalized exact PDO ID",
        "axis_note": "No physical time axis is supplied; the pipeline constructs its progress axis from each selected drug-AUC control. T0 is not interpreted as a temporal or biological transition in this cross-sectional dataset.",
        "response_metric": "The source key states the displayed values are AUC. Values are copied without transformation; no new sensitivity cutoff is applied.",
        "chemo_fluxes": chemo_fluxes,
        "targeted_fluxes": targeted_fluxes,
        "n_fluxes": len(fluxes),
        "n_missing_response_values_after_filter": int(merged[fluxes].isna().sum().sum()),
        "excluded_source_annotation": {
            "column": "Insensitive",
            "reason": "categorical source annotation; excluded from numeric flux matrix because its coding/threshold is not specified in the copied AUC key",
        },
        "planned_pipeline_test": {
            "version": "UNIVERSAL_LOG_v5.9.4.py",
            "mode": "fast",
            "domain": "pdac",
            "estimator_profile": "Cohen-d-only as configured by the source pipeline",
            "design": "fixed Gemcitabine AUC target against each of the other numeric drug-AUC columns as control, preserving all 26 AUC profiles as the multiflux input",
            "n_target_control_pairs": len(fluxes) - 1,
            "selection_note": "Gemcitabine is the prespecified standard-chemotherapy anchor for this first all-controls pass. This is an exploratory response-profile analysis, not a drug ranking or clinical recommendation.",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "input_csv": str(OUT_CSV),
        "input_sha256": manifest["input_sha256"],
        "n_observations": len(merged),
        "n_chemo_fluxes": len(chemo_fluxes),
        "n_targeted_fluxes": len(targeted_fluxes),
        "n_fluxes_total": len(fluxes),
        "n_missing": int(merged[fluxes].isna().sum().sum()),
        "sample_ids_match": True,
        "manifest": str(MANIFEST),
    }, indent=2))


if __name__ == "__main__":
    main()
