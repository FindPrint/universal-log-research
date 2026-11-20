from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ANALYSIS = Path(__file__).resolve().parent
DATA = ANALYSIS / "candidate_GSE194249_sources"
ZIP_PATH = DATA / "GSE194249_CANDIDATE_ELIGIBILITY_AUDIT.zip"
SHA_PATH = DATA / "GSE194249_CANDIDATE_ELIGIBILITY_AUDIT_SHA256.txt"

FILES = [
    (ANALYSIS / "acquire_GSE194249_sources.py", "scripts/acquire_GSE194249_sources.py"),
    (ANALYSIS / "audit_GSE194249_candidate.py", "scripts/audit_GSE194249_candidate.py"),
    (DATA / "GSE194249_PDPCOs_FPKM.txt.gz", "source/GSE194249_PDPCOs_FPKM.txt.gz"),
    (DATA / "41467_2022_29857_MOESM4_ESM.xlsx", "source/Supplementary_Data_1_cohort.xlsx"),
    (DATA / "41467_2022_29857_MOESM11_ESM.xlsx", "source/Supplementary_Data_8_drug_AUC.xlsx"),
    (DATA / "41467_2022_29857_MOESM13_ESM.xlsx", "source/Supplementary_Data_10_clinical_followup.xlsx"),
    (DATA / "41467_2022_29857_MOESM3_ESM.pdf", "source/Supplementary_file_descriptions.pdf"),
    (DATA / "CANDIDATE_DATA_AUDIT.json", "audit/CANDIDATE_DATA_AUDIT.json"),
    (DATA / "CANDIDATE_DATA_AUDIT.md", "audit/CANDIDATE_DATA_AUDIT.md"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    files = [{"archive_path": dest, "source_path": str(src), "bytes": src.stat().st_size, "sha256": sha256(src)} for src, dest in FILES]
    audit = json.loads((DATA / "CANDIDATE_DATA_AUDIT.json").read_text(encoding="utf-8"))
    readme = f"""# GSE194249 candidate dataset intake audit

This package preserves the source files and code used to check whether this dataset can be submitted to UNIVERSAL_LOG v5.9.4.

## Observed inventory

- Expression matrix: {audit['expression_matrix']['sample_columns']} sample columns.
- Public drug-response matrix: {audit['drug_response_matrix']['n_samples']} PDOs and {audit['drug_response_matrix']['n_drug_rows_with_id']} drug rows.
- Clinical follow-up workbook: {audit['clinical_followup_unique_sample_ids']} distinct sample IDs across its three sheets.
- Drug-response samples also present in follow-up: {audit['drug_response_sample_ids_in_followup']}.
- v5.9.4 fast minimum: 50 valid points. Pipeline run: not performed for this candidate because the complete drug-response matrix has N={audit['eligibility_check']['response_profile_n']}.

No drug ranking, therapeutic conclusion, or biological interpretation is made in this intake audit. This is an eligibility and provenance package.

## Reproduction

Run the audit from the project root with `.venv/Scripts/python.exe pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/audit_GSE194249_candidate.py`.

## Source

- GEO GSE194249: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE194249
- Nature Communications paper DOI: https://doi.org/10.1038/s41467-022-29857-6
- Article states CC BY 4.0; observe source attribution and license terms.
"""
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr("README.md", readme)
        for src, dest in FILES:
            archive.write(src, arcname=dest)
        archive.writestr("PACKAGE_FILE_SHA256.json", json.dumps(files, indent=2, ensure_ascii=False) + "\n")
    SHA_PATH.write_text(f"{sha256(ZIP_PATH)}  {ZIP_PATH.name}\n", encoding="ascii")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP integrity check failed")
    print(f"ZIP: {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes; SHA-256 {sha256(ZIP_PATH)})")
    print(f"SHA: {SHA_PATH}")


if __name__ == "__main__":
    main()
