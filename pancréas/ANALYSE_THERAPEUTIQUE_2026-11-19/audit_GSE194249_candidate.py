from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import openpyxl


ANALYSIS = Path(__file__).resolve().parent
DATA = ANALYSIS / "candidate_GSE194249_sources"
OUT_JSON = DATA / "CANDIDATE_DATA_AUDIT.json"
OUT_MD = DATA / "CANDIDATE_DATA_AUDIT.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def workbook_data_rows(path: Path, sheet_name: str, first_data_row: int) -> list[tuple]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet_name]
    result = list(ws.iter_rows(min_row=first_data_row, values_only=True))
    wb.close()
    return result


def main() -> None:
    drug_path = DATA / "41467_2022_29857_MOESM11_ESM.xlsx"  # Supplementary Data 8
    clinical_path = DATA / "41467_2022_29857_MOESM13_ESM.xlsx"  # Supplementary Data 10
    cohort_path = DATA / "41467_2022_29857_MOESM4_ESM.xlsx"  # Supplementary Data 1
    fpkm_path = DATA / "GSE194249_PDPCOs_FPKM.txt.gz"

    wb = openpyxl.load_workbook(drug_path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    title = ws.cell(1, 1).value
    headers = [cell.value for cell in ws[2]]
    sample_ids = [str(v) for v in headers[1:] if v not in (None, "")]
    drug_rows = [row for row in ws.iter_rows(min_row=3, values_only=True) if row[0] not in (None, "")]
    drug_ids = [str(row[0]) for row in drug_rows]
    numeric_values = [v for row in drug_rows for v in row[1:] if isinstance(v, (int, float))]
    missing_values = sum(v is None for row in drug_rows for v in row[1:len(sample_ids)+1])
    matrix = {
        "title": title,
        "sample_ids": sample_ids,
        "n_samples": len(sample_ids),
        "n_drug_rows_with_id": len(drug_ids),
        "unique_drug_ids": len(set(drug_ids)),
        "numeric_cell_count": len(numeric_values),
        "missing_matrix_cells": missing_values,
        "dimensions_declared": [ws.max_row, ws.max_column],
    }
    wb.close()

    wb = openpyxl.load_workbook(clinical_path, read_only=True, data_only=True)
    clinical_records = []
    sheet_rows = {}
    for ws in wb.worksheets:
        records = [r for r in ws.iter_rows(min_row=3, values_only=True) if r[0] is not None]
        sheet_rows[ws.title] = len(records)
        for row in records:
            sample_idx = next((i for i, value in enumerate(row) if isinstance(value, str) and value.startswith("CAS-")), None)
            if sample_idx is not None:
                clinical_records.append(row[sample_idx])
    wb.close()
    clinical_ids = [str(x) for x in clinical_records]

    wb = openpyxl.load_workbook(cohort_path, read_only=True, data_only=True)
    ws = wb["84 PDPCOs"]
    cohort_headers = [cell.value for cell in ws[2]]
    id_col = cohort_headers.index("Sample ID")
    type_col = cohort_headers.index("Tumor Type")
    detail_col = cohort_headers.index("Tumorr Type Detailed")
    cohort_rows = [r for r in ws.iter_rows(min_row=3, values_only=True) if r[id_col] not in (None, "")]
    cohort_map = {str(r[id_col]): {"tumor_type": r[type_col], "histology": r[detail_col]} for r in cohort_rows}
    wb.close()

    with gzip.open(fpkm_path, "rt", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\r\n").split("\t")
        first_gene = f.readline().rstrip("\r\n").split("\t")
    fpkm = {
        "columns_including_gene_id": len(header),
        "sample_columns": max(0, len(header)-1),
        "first_gene_row_fields": len(first_gene),
        "first_row_id": first_gene[0] if first_gene else None,
        "sample_ids": header[1:],
    }

    clinical_unique = sorted(set(clinical_ids))
    response_unique = sorted(set(sample_ids))
    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "GEO": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE194249",
            "article": "https://doi.org/10.1038/s41467-022-29857-6",
            "license_reported_by_article": "CC BY 4.0",
        },
        "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in [fpkm_path, drug_path, clinical_path, cohort_path]},
        "expression_matrix": fpkm,
        "drug_response_matrix": matrix,
        "clinical_followup_rows_by_sheet": sheet_rows,
        "clinical_followup_record_rows": len(clinical_ids),
        "clinical_followup_unique_sample_ids": len(clinical_unique),
        "clinical_followup_sample_ids": clinical_unique,
        "drug_response_unique_sample_ids": len(response_unique),
        "drug_response_sample_ids": response_unique,
        "drug_response_sample_ids_in_followup": len(set(response_unique) & set(clinical_unique)),
        "drug_response_sample_ids_in_expression": len(set(response_unique) & set(fpkm["sample_ids"])),
        "response_sample_histology_counts": {
            str(k): sum(1 for sid in response_unique if cohort_map.get(sid, {}).get("histology") == k)
            for k in sorted({str(cohort_map.get(sid, {}).get("histology")) for sid in response_unique})
        },
        "pipeline_v5_9_4_fast_minimum_points_observed_in_source": 50,
        "eligibility_check": {
            "response_profile_n": len(response_unique),
            "meets_pipeline_minimum": len(response_unique) >= 50,
            "pipeline_run_performed": False,
            "reason": "Drug-response matrix has fewer than the pipeline's 50 required valid points; the matrix is retained for the data-selection audit only.",
        },
    }
    OUT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# GSE194249 — audit de sélection des données\n\n"
        "Cet audit ne contient pas de résultat du pipeline. Il vérifie les fichiers publics avant un éventuel lancement.\n\n"
        f"- Expression : {fpkm['sample_columns']} colonnes échantillon dans la matrice FPKM.\n"
        f"- Réponse aux médicaments : {len(response_unique)} organoïdes, {matrix['n_drug_rows_with_id']} lignes avec identifiant de médicament.\n"
        f"- Suivi clinique : {len(clinical_ids)} lignes dans les trois feuilles; {len(clinical_unique)} identifiants uniques.\n"
        f"- Identifiants de réponse présents dans le suivi : {audit['drug_response_sample_ids_in_followup']}.\n"
        f"- Résultat du contrôle d'admissibilité : pipeline lancé = non; N réponse = {len(response_unique)}; minimum v5.9.4 fast = 50.\n\n"
        "Voir `CANDIDATE_DATA_AUDIT.json` pour les ID d'échantillon, dimensions et empreintes SHA-256.\n",
        encoding="utf-8",
    )
    print(json.dumps({k: audit[k] for k in ["expression_matrix", "drug_response_matrix", "clinical_followup_rows_by_sheet", "clinical_followup_record_rows", "clinical_followup_unique_sample_ids", "drug_response_sample_ids_in_followup", "eligibility_check"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
