#!/usr/bin/env python3
"""Feed the published Figure 6d PDO dose-response columns to v6.0.0's real gate.

This is deliberately only an input-compatibility check. It does not run the
full target/control pipeline, assign T0, interpret IC50, or claim validation.
Each source-data column is kept separate; no duplicate wells are concatenated.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import numpy as np
from openpyxl import load_workbook


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE_BOOK = HERE / "source" / "41467_2025_57520_MOESM17_ESM.xlsx"
PIPELINE = PROJECT / "pancréas" / "universal_v6.0.0_cohen - Copie.py.txt"
OUTPUT_CSV = HERE / "PDO_FIG6D_PIPELINE_GATE.csv"
OUTPUT_JSON = HERE / "PDO_FIG6D_PIPELINE_GATE_SUMMARY.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_pipeline_module():
    loader = importlib.machinery.SourceFileLoader("universal_log_v6_gate_audit", str(PIPELINE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main() -> int:
    if not SOURCE_BOOK.exists():
        raise FileNotFoundError(
            "Run inspect_pdac_organoid_source.py first to download the public source workbook."
        )
    if not PIPELINE.exists():
        raise FileNotFoundError(f"Pipeline source not found: {PIPELINE}")

    book = load_workbook(SOURCE_BOOK, read_only=True, data_only=True)
    sheet = book["Figure 6"]
    concentration_rows = list(sheet.iter_rows(min_row=96, max_row=103, min_col=1, max_col=1, values_only=True))
    concentrations = [float(row[0]) for row in concentration_rows if row[0] is not None]
    header_row = next(sheet.iter_rows(min_row=95, max_row=95, values_only=True))
    value_rows = list(sheet.iter_rows(min_row=96, max_row=103, values_only=True))
    book.close()

    pipeline = load_pipeline_module()
    fast_cfg = dict(pipeline.PARAMETERS["modes"]["fast"])
    records = []
    last_label = None
    for col_index in range(1, len(header_row)):
        label = header_row[col_index]
        if label:
            last_label = str(label)
            replicate_slot = 1
        else:
            replicate_slot = 2
        values = [row[col_index] for row in value_rows]
        values = [float(value) for value in values if value is not None]
        if not values:
            continue
        result = pipeline.apply_complexity(
            np.asarray(values, dtype=float),
            flux_name=f"{last_label}_source_column_{col_index + 1}_slot_{replicate_slot}",
            mode_cfg=fast_cfg,
        )
        finite_estimators = int(sum(np.isfinite(value) for value in result.values()))
        records.append(
            {
                "source_header_group": last_label,
                "source_excel_column_1based": col_index + 1,
                "measurement_slot_within_header_group": replicate_slot,
                "dose_points_available": len(values),
                "finite_values_in_29_estimators": finite_estimators,
                "configured_fast_min_series_length": int(fast_cfg["min_len"]),
                "input_status": "accepted_by_length_gate" if len(values) >= fast_cfg["min_len"] else "rejected_by_length_gate",
            }
        )

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    summary = {
        "question": "Can the published Figure 6d dose-response columns pass the unchanged v6.0.0 fast-mode 29-estimator input gate?",
        "scope": "Compatibility gate only; no full target/control run and no T0/TLog/IC50 equivalence claim.",
        "pipeline_path": str(PIPELINE),
        "pipeline_sha256": sha256_file(PIPELINE),
        "pipeline_version": getattr(pipeline, "VERSION", "not exposed"),
        "analysis_mode": "fast",
        "statistical_test": fast_cfg.get("test"),
        "minimum_series_length": int(fast_cfg.get("min_len")),
        "concentration_points_in_source_curve": sorted(set(len([row[i] for row in value_rows if row[i] is not None]) for i in range(1, len(header_row)))),
        "source_concentrations_nm": concentrations,
        "source_workbook_sha256": sha256_file(SOURCE_BOOK),
        "source_sheet": "Figure 6, rows 95-103; 8 dose levels for Figure 6d",
        "separate_measurement_columns_tested": len(records),
        "accepted_by_length_gate": int(sum(row["input_status"] == "accepted_by_length_gate" for row in records)),
        "rejected_by_length_gate": int(sum(row["input_status"] == "rejected_by_length_gate" for row in records)),
        "with_any_finite_estimator": int(sum(row["finite_values_in_29_estimators"] > 0 for row in records)),
        "all_estimators_finite_total": int(sum(row["finite_values_in_29_estimators"] for row in records)),
        "result_csv": OUTPUT_CSV.name,
        "interpretation": (
            "The current fast gate requires 50 points, whereas each published curve has at most 8 dose levels. "
            "Therefore this source is useful to design a separately calibrated dose-response mode, but it cannot "
            "support a v6.0.0 full pipeline run as-is. Columns remain separate and are not concatenated as pseudo-replicates."
        ),
    }
    OUTPUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
