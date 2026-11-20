from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "NatureComm2025_Supplementary_Data10.xlsx"
OUTPUT = HERE / "NatureComm2025_46PDO_63Drug_AUC.csv"
MANIFEST = HERE / "PIPELINE_INPUT_MANIFEST.json"
TARGET = "Gemcitabine"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    workbook = load_workbook(SOURCE, read_only=True, data_only=True)
    sheet = workbook["All Drugs AUC"]
    records = list(sheet.iter_rows(values_only=True))
    header = records[0]
    if header[0] is not None or header[1] != "cluster":
        raise ValueError(f"Unexpected source header: {header[:4]!r}")
    sample_ids = [str(value).strip() for value in header[2:] if value is not None]
    drug_rows = [row for row in records[1:] if row[0] is not None]
    drug_names = [str(row[0]).strip() for row in drug_rows]
    if len(sample_ids) != 46 or len(drug_names) != 63:
        raise ValueError(f"Unexpected matrix dimensions: {len(sample_ids)} PDOs x {len(drug_names)} drugs")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("Duplicate PDO identifiers in source header")
    if len(drug_names) != len(set(drug_names)):
        raise ValueError("Duplicate drug names in source rows")
    if TARGET not in drug_names:
        raise ValueError(f"Prespecified target not found: {TARGET!r}")

    values: dict[str, list[float]] = {}
    for drug_name, row in zip(drug_names, drug_rows):
        raw_values = list(row[2 : 2 + len(sample_ids)])
        if len(raw_values) != len(sample_ids) or any(value is None for value in raw_values):
            raise ValueError(f"Missing or short response row for {drug_name!r}")
        numeric = [float(value) for value in raw_values]
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError(f"Non-finite AUC value in {drug_name!r}")
        values[drug_name] = numeric

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["PDO_ID", *drug_names])
        writer.writeheader()
        for sample_index, sample_id in enumerate(sample_ids):
            writer.writerow({"PDO_ID": sample_id, **{drug: values[drug][sample_index] for drug in drug_names}})

    manifest = {
        "source_title": "Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients",
        "source_doi": "10.1038/s41467-025-57520-3",
        "source_file": SOURCE.name,
        "source_sha256": sha256(SOURCE),
        "source_sheet": sheet.title,
        "source_layout": "drug rows; PDO columns; cluster is categorical metadata",
        "input_csv": OUTPUT.name,
        "input_sha256": sha256(OUTPUT),
        "observations": len(sample_ids),
        "flux_count": len(drug_names),
        "pdo_ids_in_source_order": sample_ids,
        "drug_fluxes_in_source_order": drug_names,
        "target_prespecified": TARGET,
        "controls_prespecified": [drug for drug in drug_names if drug != TARGET],
        "missing_values": 0,
        "imputation": "none",
        "transformations": "transpose only; numeric AUC values copied unchanged",
        "eligibility_note": "N=46 is below the confirmatory N>=50 floor; pilot only, not external validation",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"input={OUTPUT}")
    print(f"observations={len(sample_ids)} fluxes={len(drug_names)} controls={len(drug_names)-1}")
    print(f"target={TARGET}; missing=0; csv_sha256={manifest['input_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
