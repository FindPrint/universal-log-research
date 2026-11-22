#!/usr/bin/env python
"""Record row-order, timestamp-gap, target-identity and provenance checks."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
CSV = HERE / "source" / "hour.csv"
OUT = HERE / "source_quality_audit_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    frame = pd.read_csv(CSV, parse_dates=["dteday"])
    timestamp = frame["dteday"] + pd.to_timedelta(frame["hr"], unit="h")
    gap_hours = timestamp.diff().dropna().dt.total_seconds() / 3600
    gap_counts = {str(int(key)): int(value) for key, value in gap_hours.value_counts().sort_index().items()}
    expected_slots = int((timestamp.max() - timestamp.min()).total_seconds() // 3600) + 1
    observed = int(timestamp.nunique())
    report = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_csv": "source/hour.csv",
        "source_csv_sha256": sha256(CSV),
        "source_rows": int(len(frame)),
        "source_first_timestamp": timestamp.min().isoformat(),
        "source_last_timestamp": timestamp.max().isoformat(),
        "unique_observed_timestamps": observed,
        "expected_clock_hour_slots_in_inclusive_range": expected_slots,
        "unrepresented_clock_hour_slots_between_first_and_last": expected_slots - observed,
        "inter_record_gap_counts_in_hours": gap_counts,
        "maximum_inter_record_gap_hours": float(gap_hours.max()),
        "instant_monotone_increasing": bool(frame["instant"].is_monotonic_increasing),
        "timestamps_monotone_increasing": bool(timestamp.is_monotonic_increasing),
        "casual_plus_registered_equals_cnt_for_every_row": bool((frame["casual"] + frame["registered"] == frame["cnt"]).all()),
        "source_readme_reports_hour_records": 17379,
        "readme_provenance_note": "UCI Readme says the 2011-2012 hourly/daily data originate from Capital Bikeshare and weather/seasonal information was added; weather information is attributed there to freemeteo.",
        "gap_interpretation": "The file has fewer timestamped records than clock-hour slots in the span. The included Readme does not explain these specific gaps; no zero-rental imputation or missingness mechanism is assumed.",
        "instrumentation_limit": "The included source files do not identify the weather sensor models, calibration records, sampling instruments, or sensor-level uncertainty.",
        "action_taken": "No rows imputed, removed, or reordered by this audit.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
