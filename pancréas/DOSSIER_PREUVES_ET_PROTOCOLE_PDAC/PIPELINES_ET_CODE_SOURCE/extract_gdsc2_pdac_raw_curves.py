#!/usr/bin/env python3
"""Extract and normalize selected GDSC2 PDAC wells using the gdscIC50 rules.

This prepares empirical in-vitro dose-response curves; it does not fit TLog,
the GDSC nonlinear mixed-effects model, or a clinical prediction model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

RAW_URL = (
    "https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/"
    "current_release/GDSC2_public_raw_data_24Jul22.csv"
)
RAW_FILENAME = "GDSC2_public_raw_data_24Jul22.csv"
EXPECTED_SIZE_BYTES = 2_112_924_313

DRUGS = {
    "1005": "Cisplatin",
    "1017": "Olaparib",
    "1073": "5-Fluorouracil",
    "1080": "Paclitaxel",
    "1190": "Gemcitabine",
}

CELL_LINES = {
    "aspc-1": "AsPC-1",
    "bxpc-3": "BxPC-3",
    "capan-1": "CAPAN-1",
    "mia paca-2": "MIA PaCa-2",
    "panc-1": "PANC-1",
}

REQUIRED_COLUMNS = {
    "SCAN_ID",
    "BARCODE",
    "DATE_CREATED",
    "SCAN_DATE",
    "COSMIC_ID",
    "CELL_LINE_NAME",
    "CELL_ID",
    "MASTER_CELL_ID",
    "SANGER_MODEL_ID",
    "RESEARCH_PROJECT",
    "ASSAY",
    "DURATION",
    "SEEDING_DENSITY",
    "DRUGSET_ID",
    "POSITION",
    "TAG",
    "DRUG_ID",
    "CONC",
    "INTENSITY",
}

LIBRARY_TAG = re.compile(r"^([LR]\d+)-D(\d+)-(S|C)$")
MISSING_DRUG_TAG = re.compile(r"^[LRA]\d+")
CONTROL_TAGS = {"NC-1", "B"}

WELL_FIELDS = [
    "scan_id",
    "barcode",
    "research_project",
    "date_created",
    "scan_date",
    "cosmic_id",
    "cell_id",
    "master_cell_id",
    "sanger_model_id",
    "cell_line",
    "drugset_id",
    "assay",
    "duration_days",
    "seeding_density",
    "drug_id",
    "drug_name",
    "library_tag",
    "dose_tag",
    "concentration_uM",
    "position",
    "intensity",
    "nc1_mean_intensity",
    "blank_mean_intensity",
    "viability_fraction",
]

POINT_FIELDS = [
    "scan_id",
    "barcode",
    "research_project",
    "date_created",
    "scan_date",
    "cosmic_id",
    "cell_id",
    "master_cell_id",
    "sanger_model_id",
    "cell_line",
    "drugset_id",
    "assay",
    "duration_days",
    "seeding_density",
    "drug_id",
    "drug_name",
    "library_tag",
    "concentration_uM",
    "n_technical_wells",
    "mean_viability_fraction",
    "sd_viability_fraction",
]

AUDIT_FIELDS = [
    "scan_id",
    "barcode",
    "research_project",
    "date_created",
    "scan_date",
    "cosmic_id",
    "cell_id",
    "master_cell_id",
    "sanger_model_id",
    "cell_line",
    "drugset_id",
    "assay",
    "duration_days",
    "seeding_density",
    "n_nc1_wells",
    "nc1_mean_intensity",
    "n_blank_wells",
    "blank_mean_intensity",
    "n_target_drug_rows",
    "n_failed_positions",
    "n_missing_drug_positions",
    "n_extracted_single_agent_wells",
    "status",
    "issues",
]


def _number(value: str | None, field: str, scan_id: str) -> float:
    if value is None or value.strip().casefold() in {"", "na", "nan"}:
        raise ValueError(f"{field} is missing for SCAN_ID {scan_id}")
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(
            f"{field} is not numeric for SCAN_ID {scan_id}: {value!r}"
        ) from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} is not finite for SCAN_ID {scan_id}")
    return result


def _mean(values: list[float]) -> float:
    return math.fsum(values) / len(values)


def normalize_scan(
    scan_id: str, rows: list[dict[str, str]]
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    """Normalize target single-agent wells for one plate scan."""
    if not rows:
        raise ValueError(f"No retained records for SCAN_ID {scan_id}")

    identity_fields = {
        "BARCODE": {row["BARCODE"] for row in rows},
        "RESEARCH_PROJECT": {row["RESEARCH_PROJECT"] for row in rows},
        "DATE_CREATED": {row["DATE_CREATED"] for row in rows},
        "SCAN_DATE": {row["SCAN_DATE"] for row in rows},
        "CELL_LINE_NAME": {row["CELL_LINE_NAME"] for row in rows},
        "CELL_ID": {row["CELL_ID"] for row in rows},
        "MASTER_CELL_ID": {row["MASTER_CELL_ID"] for row in rows},
        "SANGER_MODEL_ID": {row["SANGER_MODEL_ID"] for row in rows},
        "ASSAY": {row["ASSAY"] for row in rows},
        "DURATION": {row["DURATION"] for row in rows},
        "SEEDING_DENSITY": {row["SEEDING_DENSITY"] for row in rows},
        "DRUGSET_ID": {row["DRUGSET_ID"] for row in rows},
        "COSMIC_ID": {row["COSMIC_ID"] for row in rows},
    }
    inconsistent = [name for name, values in identity_fields.items() if len(values) > 1]
    if inconsistent:
        raise ValueError(
            f"Inconsistent scan metadata for SCAN_ID {scan_id}: "
            f"{', '.join(inconsistent)}"
        )

    cell_line = rows[0]["CELL_LINE_NAME"]
    cell_key = cell_line.strip().casefold()
    display_cell = CELL_LINES.get(cell_key, cell_line)
    positions_to_remove = {
        row["POSITION"]
        for row in rows
        if row["TAG"] == "FAIL"
        or (
            MISSING_DRUG_TAG.match(row["TAG"]) is not None
            and row["DRUG_ID"].strip().casefold() in {"", "na"}
        )
    }

    retained = [row for row in rows if row["POSITION"] not in positions_to_remove]
    nc_values = [
        _number(row["INTENSITY"], "INTENSITY", scan_id)
        for row in retained
        if row["TAG"] == "NC-1"
    ]
    blank_values = [
        _number(row["INTENSITY"], "INTENSITY", scan_id)
        for row in retained
        if row["TAG"] == "B"
    ]

    issues: list[str] = []
    if not nc_values:
        issues.append("missing_NC-1_control")
    if not blank_values:
        issues.append("missing_B_blank")

    nc_mean = _mean(nc_values) if nc_values else math.nan
    blank_mean = _mean(blank_values) if blank_values else math.nan
    denominator = nc_mean - blank_mean
    if nc_values and blank_values and denominator <= 0:
        issues.append("nonpositive_control_dynamic_range")

    target_rows = [
        row
        for row in retained
        if row["DRUG_ID"].strip() in DRUGS
    ]
    wells: list[dict[str, object]] = []
    excluded_combinations = 0
    if not issues:
        for row in target_rows:
            match = LIBRARY_TAG.fullmatch(row["TAG"])
            if match is None:
                excluded_combinations += 1
                continue
            library_tag, dose_tag, treatment = match.groups()
            if treatment != "S":
                excluded_combinations += 1
                continue

            concentration = _number(row["CONC"], "CONC", scan_id)
            if concentration <= 0:
                raise ValueError(
                    f"CONC must be positive for SCAN_ID {scan_id}, "
                    f"POSITION {row['POSITION']}"
                )
            intensity = _number(row["INTENSITY"], "INTENSITY", scan_id)
            viability = (intensity - blank_mean) / denominator
            viability = min(1.0, max(0.0, viability))
            drug_id = row["DRUG_ID"].strip()
            wells.append(
                {
                    "scan_id": scan_id,
                    "barcode": row["BARCODE"],
                    "research_project": row["RESEARCH_PROJECT"],
                    "date_created": row["DATE_CREATED"],
                    "scan_date": row["SCAN_DATE"],
                    "cosmic_id": row["COSMIC_ID"],
                    "cell_id": row["CELL_ID"],
                    "master_cell_id": row["MASTER_CELL_ID"],
                    "sanger_model_id": row["SANGER_MODEL_ID"],
                    "cell_line": display_cell,
                    "drugset_id": row["DRUGSET_ID"],
                    "assay": row["ASSAY"],
                    "duration_days": row["DURATION"],
                    "seeding_density": row["SEEDING_DENSITY"],
                    "drug_id": drug_id,
                    "drug_name": DRUGS[drug_id],
                    "library_tag": library_tag,
                    "dose_tag": f"D{dose_tag}",
                    "concentration_uM": concentration,
                    "position": row["POSITION"],
                    "intensity": intensity,
                    "nc1_mean_intensity": nc_mean,
                    "blank_mean_intensity": blank_mean,
                    "viability_fraction": viability,
                }
            )

    grouped: dict[tuple[str, str, float], list[float]] = defaultdict(list)
    metadata: dict[tuple[str, str, float], dict[str, object]] = {}
    for well in wells:
        key = (
            str(well["drug_id"]),
            str(well["library_tag"]),
            float(well["concentration_uM"]),
        )
        grouped[key].append(float(well["viability_fraction"]))
        metadata[key] = well

    points: list[dict[str, object]] = []
    for key, values in sorted(grouped.items()):
        well = metadata[key]
        mean_value = _mean(values)
        variance = (
            math.fsum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
            if len(values) > 1
            else math.nan
        )
        points.append(
            {
                "scan_id": scan_id,
                "barcode": well["barcode"],
                "research_project": well["research_project"],
                "date_created": well["date_created"],
                "scan_date": well["scan_date"],
                "cosmic_id": well["cosmic_id"],
                "cell_id": well["cell_id"],
                "master_cell_id": well["master_cell_id"],
                "sanger_model_id": well["sanger_model_id"],
                "cell_line": well["cell_line"],
                "drugset_id": well["drugset_id"],
                "assay": well["assay"],
                "duration_days": well["duration_days"],
                "seeding_density": well["seeding_density"],
                "drug_id": well["drug_id"],
                "drug_name": well["drug_name"],
                "library_tag": well["library_tag"],
                "concentration_uM": well["concentration_uM"],
                "n_technical_wells": len(values),
                "mean_viability_fraction": mean_value,
                "sd_viability_fraction": math.sqrt(variance) if math.isfinite(variance) else "",
            }
        )

    audit: dict[str, object] = {
        "scan_id": scan_id,
        "barcode": rows[0]["BARCODE"],
        "research_project": rows[0]["RESEARCH_PROJECT"],
        "date_created": rows[0]["DATE_CREATED"],
        "scan_date": rows[0]["SCAN_DATE"],
        "cosmic_id": rows[0]["COSMIC_ID"],
        "cell_id": rows[0]["CELL_ID"],
        "master_cell_id": rows[0]["MASTER_CELL_ID"],
        "sanger_model_id": rows[0]["SANGER_MODEL_ID"],
        "cell_line": display_cell,
        "drugset_id": rows[0]["DRUGSET_ID"],
        "assay": rows[0]["ASSAY"],
        "duration_days": rows[0]["DURATION"],
        "seeding_density": rows[0]["SEEDING_DENSITY"],
        "n_nc1_wells": len(nc_values),
        "nc1_mean_intensity": nc_mean if nc_values else "",
        "n_blank_wells": len(blank_values),
        "blank_mean_intensity": blank_mean if blank_values else "",
        "n_target_drug_rows": len(target_rows),
        "n_failed_positions": len(
            {
                row["POSITION"]
                for row in rows
                if row["TAG"] == "FAIL"
            }
        ),
        "n_missing_drug_positions": len(
            {
                row["POSITION"]
                for row in rows
                if MISSING_DRUG_TAG.match(row["TAG"]) is not None
                and row["DRUG_ID"].strip().casefold() in {"", "na"}
            }
        ),
        "n_extracted_single_agent_wells": len(wells),
        "status": "OK" if not issues else "EXCLUDED",
        "issues": ";".join(issues),
    }
    if excluded_combinations:
        audit["issues"] = ";".join(
            filter(None, [str(audit["issues"]), f"excluded_non_single_agent_rows={excluded_combinations}"])
        )
    return wells, audit, points


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    output_dir.mkdir(parents=True, exist_ok=True)

    scans: dict[str, list[dict[str, str]]] = defaultdict(list)
    cell_counts: Counter[str] = Counter()
    rows_read = 0

    with raw_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("GDSC2 raw CSV has no header")
        missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                f"GDSC2 raw CSV is missing required columns: {sorted(missing_columns)}"
            )

        for row in reader:
            rows_read += 1
            cell_line = (row.get("CELL_LINE_NAME") or "").strip()
            cell_key = cell_line.casefold()
            if cell_key not in CELL_LINES:
                continue
            cell_counts[cell_key] += 1
            tag = (row.get("TAG") or "").strip()
            drug_id = (row.get("DRUG_ID") or "").strip()
            if (
                tag in CONTROL_TAGS
                or tag == "FAIL"
                or (MISSING_DRUG_TAG.match(tag) is not None and drug_id.casefold() in {"", "na"})
                or drug_id in DRUGS
            ):
                scan_id = (row.get("SCAN_ID") or "").strip()
                if not scan_id:
                    raise ValueError(f"Empty SCAN_ID at source row {rows_read + 1}")
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
                        "CELL_LINE_NAME": cell_line,
                        "ASSAY": (row.get("ASSAY") or "").strip(),
                        "DURATION": (row.get("DURATION") or "").strip(),
                        "SEEDING_DENSITY": (row.get("SEEDING_DENSITY") or "").strip(),
                        "DRUGSET_ID": (row.get("DRUGSET_ID") or "").strip(),
                        "POSITION": (row.get("POSITION") or "").strip(),
                        "TAG": tag,
                        "DRUG_ID": drug_id,
                        "CONC": (row.get("CONC") or "").strip(),
                        "INTENSITY": (row.get("INTENSITY") or "").strip(),
                    }
                )

    if not cell_counts:
        raise ValueError(
            "None of the configured PDAC cell-line names were found in the pinned source"
        )
    if not scans:
        raise ValueError(
            "No configured cell-line rows with controls or target drug IDs were found"
        )

    all_wells: list[dict[str, object]] = []
    all_points: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    for scan_id, rows in scans.items():
        wells, audit, points = normalize_scan(scan_id, rows)
        all_wells.extend(wells)
        all_points.extend(points)
        audits.append(audit)

    wells_path = output_dir / "gdsc2_pdac_normalized_wells.csv"
    points_path = output_dir / "gdsc2_pdac_curve_points.csv"
    audits_path = output_dir / "gdsc2_pdac_scan_audit.csv"
    _write_csv(wells_path, WELL_FIELDS, all_wells)
    _write_csv(points_path, POINT_FIELDS, all_points)
    _write_csv(audits_path, AUDIT_FIELDS, audits)

    coverage = {
        CELL_LINES[key]: {
            "matched_source_rows": cell_counts[key],
            "scan_ids": sum(1 for audit in audits if audit["cell_line"] == CELL_LINES[key]),
            "single_agent_wells": sum(
                int(audit["n_extracted_single_agent_wells"])
                for audit in audits
                if audit["cell_line"] == CELL_LINES[key]
            ),
        }
        for key in CELL_LINES
    }
    manifest: dict[str, object] = {
        "status": (
            "NORMALIZED_WELLS_EXTRACTED"
            if all_wells
            else "NO_NORMALIZED_SINGLE_AGENT_WELLS"
        ),
        "source_url": RAW_URL,
        "source_filename": raw_csv.name,
        "source_size_bytes": raw_csv.stat().st_size,
        "source_sha256": _sha256(raw_csv),
        "source_rows_read": rows_read,
        "normalization": {
            "method_reference": (
                "CancerRxGene/gdscIC50 R/nlme_fit_prep.R, normalizeData"
            ),
            "method_reference_url": (
                "https://github.com/CancerRxGene/gdscIC50/blob/master/R/nlme_fit_prep.R"
            ),
            "negative_control_tag": "NC-1",
            "blank_tag": "B",
            "formula": "(INTENSITY - mean(B)) / (mean(NC-1) - mean(B))",
            "trimmed_range": [0, 1],
            "failed_tag_removed_by_scan_and_position": "FAIL",
            "missing_library_drug_positions_removed": True,
            "included_treatments": "single-agent library/reference tags ending -S",
            "combination_treatments_included": False,
            "technical_replicates_are_not_biological_replicates": True,
        },
        "cell_line_coverage": coverage,
        "scan_count": len(scans),
        "valid_scan_count": sum(audit["status"] == "OK" for audit in audits),
        "excluded_scan_count": sum(audit["status"] == "EXCLUDED" for audit in audits),
        "normalized_well_count": len(all_wells),
        "curve_point_count": len(all_points),
        "outputs": [wells_path.name, points_path.name, audits_path.name],
        "limitations": [
            "This is normalized in-vitro assay data, not patient or clinical data.",
            "No TLog or GDSC nonlinear mixed-effects model is fitted by this extractor.",
            "Curve points summarize technical wells; they are not independent biological replicates.",
            "Coverage is restricted to the configured five cell-line names and five GDSC2 drug IDs.",
        ],
    }
    (output_dir / "gdsc2_pdac_raw_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-csv",
        type=Path,
        required=True,
        help="Path to GDSC2_public_raw_data_24Jul22.csv (about 2.1 GB)",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = extract(args.raw_csv, args.output_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
