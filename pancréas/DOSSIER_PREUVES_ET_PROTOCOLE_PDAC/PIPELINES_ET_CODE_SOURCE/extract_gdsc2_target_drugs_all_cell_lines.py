#!/usr/bin/env python3
"""Extract selected GDSC2 single-agent drugs across all cell lines."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from extract_gdsc2_pdac_raw_curves import (
    AUDIT_FIELDS,
    CONTROL_TAGS,
    DRUGS,
    EXPECTED_SIZE_BYTES,
    MISSING_DRUG_TAG,
    POINT_FIELDS,
    RAW_FILENAME,
    REQUIRED_COLUMNS,
    WELL_FIELDS,
    _sha256,
    _write_csv,
    normalize_scan,
)

TARGET_DRUG_IDS = frozenset(DRUGS)
RELEVANT_TAGS = CONTROL_TAGS | {"FAIL"}


def _read_header(reader: csv.DictReader) -> None:
    if reader.fieldnames is None:
        raise ValueError("GDSC2 raw CSV has no header")
    missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames)
    if missing_columns:
        raise ValueError(
            f"GDSC2 raw CSV is missing required columns: {sorted(missing_columns)}"
        )


def _should_keep(row: dict[str, str], target_scans: set[str]) -> bool:
    if (row.get("SCAN_ID") or "").strip() not in target_scans:
        return False
    tag = (row.get("TAG") or "").strip()
    drug_id = (row.get("DRUG_ID") or "").strip()
    return (
        tag in RELEVANT_TAGS
        or (
            MISSING_DRUG_TAG.match(tag) is not None
            and drug_id.casefold() in {"", "na"}
        )
        or drug_id in TARGET_DRUG_IDS
    )


def extract(raw_csv: Path, output_dir: Path) -> dict[str, object]:
    if not raw_csv.is_file():
        raise FileNotFoundError(f"Raw GDSC2 CSV not found: {raw_csv}")
    if raw_csv.name != RAW_FILENAME:
        raise ValueError(f"Expected the pinned source file named {RAW_FILENAME}")
    if raw_csv.stat().st_size != EXPECTED_SIZE_BYTES:
        raise ValueError(
            f"Unexpected size for {RAW_FILENAME}: {raw_csv.stat().st_size} bytes; "
            f"expected {EXPECTED_SIZE_BYTES}"
        )

    target_scans: set[str] = set()
    source_rows_read = 0
    with raw_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _read_header(reader)
        for row in reader:
            source_rows_read += 1
            if (row.get("DRUG_ID") or "").strip() in TARGET_DRUG_IDS:
                scan_id = (row.get("SCAN_ID") or "").strip()
                if not scan_id:
                    raise ValueError(
                        f"Empty SCAN_ID at source row {source_rows_read + 1}"
                    )
                target_scans.add(scan_id)

    if not target_scans:
        raise ValueError("No scans with the configured GDSC2 drug IDs were found")

    scans: dict[str, list[dict[str, str]]] = defaultdict(list)
    retained_source_rows = 0
    with raw_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _read_header(reader)
        for row in reader:
            if not _should_keep(row, target_scans):
                continue
            retained_source_rows += 1
            scan_id = (row.get("SCAN_ID") or "").strip()
            scans[scan_id].append(
                {
                    "SCAN_ID": scan_id,
                    "BARCODE": (row.get("BARCODE") or "").strip(),
                    "RESEARCH_PROJECT": (row.get("RESEARCH_PROJECT") or "").strip(),
                    "DATE_CREATED": (row.get("DATE_CREATED") or "").strip(),
                    "SCAN_DATE": (row.get("SCAN_DATE") or "").strip(),
                    "COSMIC_ID": (row.get("COSMIC_ID") or "").strip(),
                    "CELL_ID": (row.get("CELL_ID") or "").strip(),
                    "MASTER_CELL_ID": (row.get("MASTER_CELL_ID") or "").strip(),
                    "SANGER_MODEL_ID": (row.get("SANGER_MODEL_ID") or "").strip(),
                    "CELL_LINE_NAME": (row.get("CELL_LINE_NAME") or "").strip(),
                    "ASSAY": (row.get("ASSAY") or "").strip(),
                    "DURATION": (row.get("DURATION") or "").strip(),
                    "SEEDING_DENSITY": (row.get("SEEDING_DENSITY") or "").strip(),
                    "DRUGSET_ID": (row.get("DRUGSET_ID") or "").strip(),
                    "POSITION": (row.get("POSITION") or "").strip(),
                    "TAG": (row.get("TAG") or "").strip(),
                    "DRUG_ID": (row.get("DRUG_ID") or "").strip(),
                    "CONC": (row.get("CONC") or "").strip(),
                    "INTENSITY": (row.get("INTENSITY") or "").strip(),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    wells: list[dict[str, object]] = []
    points: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    cell_counts: Counter[str] = Counter()
    cell_scan_counts: Counter[str] = Counter()
    drug_counts: Counter[str] = Counter()
    for scan_id, rows in scans.items():
        scan_wells, audit, scan_points = normalize_scan(scan_id, rows)
        wells.extend(scan_wells)
        points.extend(scan_points)
        audits.append(audit)
        cell_line = str(audit["cell_line"])
        cell_counts[cell_line] += int(audit["n_extracted_single_agent_wells"])
        if audit["n_extracted_single_agent_wells"]:
            cell_scan_counts[cell_line] += 1
        drug_counts.update(str(well["drug_id"]) for well in scan_wells)

    wells_path = output_dir / "gdsc2_all_lines_normalized_wells.csv"
    points_path = output_dir / "gdsc2_all_lines_curve_points.csv"
    audits_path = output_dir / "gdsc2_all_lines_scan_audit.csv"
    manifest_path = output_dir / "gdsc2_all_lines_manifest.json"
    _write_csv(wells_path, WELL_FIELDS, wells)
    _write_csv(points_path, POINT_FIELDS, points)
    _write_csv(audits_path, AUDIT_FIELDS, audits)

    valid_scans = sum(audit["status"] == "OK" for audit in audits)
    manifest: dict[str, object] = {
        "status": "NORMALIZED_WELLS_EXTRACTED",
        "source_filename": raw_csv.name,
        "source_size_bytes": raw_csv.stat().st_size,
        "source_sha256": _sha256(raw_csv),
        "source_rows_read_per_scan_discovery_pass": source_rows_read,
        "target_drug_ids": DRUGS,
        "target_scan_count": len(target_scans),
        "retained_source_rows": retained_source_rows,
        "valid_scan_count": valid_scans,
        "excluded_scan_count": len(audits) - valid_scans,
        "normalized_well_count": len(wells),
        "curve_point_count": len(points),
        "cell_line_scan_counts": dict(sorted(cell_scan_counts.items())),
        "cell_line_well_counts": dict(sorted(cell_counts.items())),
        "drug_well_counts": dict(sorted(drug_counts.items())),
        "outputs": [wells_path.name, points_path.name, audits_path.name],
        "limitations": [
            "Only the configured five single-agent GDSC2 drug IDs are retained.",
            "This is normalized in-vitro assay data, not patient or clinical data.",
            "Technical wells are not independent biological replicates.",
            "This extractor does not fit the GDSC nonlinear mixed-effects model.",
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(extract(args.raw_csv, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
