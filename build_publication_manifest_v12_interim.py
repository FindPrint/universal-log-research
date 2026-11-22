#!/usr/bin/env python
"""Build a narrow, path-redacted allowlist for the interim V12 GitHub update."""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "PUBLICATION_MANIFEST_V12_INTERIM.csv"
AI4I = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V1")
BIKE = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V2_BIKESHARING")
AIR = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V3_AIR_QUALITY")

ROOT_FILES = [
    ".gitattributes", "README.md", "README_V12_CURRENT.md", "PUBLICATION_SCOPE_V12.md", "RELEASE_V12_CHANGELOG_FR.md",
    "ACTIVITY_LOG_V12_2026-11-22.md", "PROTOCOLE_TRIAGE_SEUILS_ET_ORIGINE_V1_FR.md", "THREE_LEVELS_AND_DELTA_ARCHIVE_PLAN_V1_FR.md",
    "DELTA_ARCHIVE_GUIDE_V1_FR.md", "build_project_delta.py", "reconstruct_project_from_delta.py",
    "test_delta_archive_smoke.py", "summarize_pipeline_layers.py", "build_publication_manifest_v12.py",
    "build_publication_manifest_v12_interim.py", "sync_manifest_from_git_index.py",
    "LICENSE", "LICENSE-CC-BY-4.0.txt", "LICENSES.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/REPLICATION_P2_010_GEO_2026-11-20/pipeline_source/UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py",
]
AI4I_FILES = [
    "README_FR.md", "fetch_ai4i_dataset.py", "dataset_manifest.json", "run_ai4i_prediction_benchmark.py",
    "requirements-ai4i-benchmark.txt", "RESULTS_AI4I_PREDICTION_V1_FR.md", "PROTOCOLE_AI4I_PIPELINE_CONTROLS_V1_FR.md",
    "build_ai4i_pipeline_rotation_report.py", "source/ai4i2020.csv",
    "prediction_benchmark_v1/fold_metrics.csv", "prediction_benchmark_v1/holdout_predictions.csv", "prediction_benchmark_v1/benchmark_manifest.json",
    "pipeline_control_rotation_v1/inputs/ai4i_100_bins.csv", "pipeline_control_rotation_v1/campaign_plan.json",
    "pipeline_control_rotation_v1/campaign_manifest.json", "pipeline_control_rotation_v1/control_rotation_summary.csv",
    "pipeline_control_rotation_v1/AI4I_PIPELINE_CONTROL_ROTATION_V1_REPORT_FR.md",
    "pipeline_control_rotation_v1/public_summary_manifest.json", "pipeline_control_rotation_v1/t0_by_control_v1.png",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_AI4I_SUMMARY.csv",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_AI4I_REPORT_FR.md",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_AI4I_QUESTIONS_HEATMAP.png",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_AI4I_CASCADE_THRESHOLDS.png",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_AI4I_TLOG_CLASSES.png",
]
BIKE_FILES = [
    "README_FR.md", "fetch_bike_sharing_dataset.py", "dataset_manifest.json", "requirements-bikesharing.txt",
    "PROTOCOLE_BIKESHARING_V1_FR.md", "PROTOCOLE_BENCHMARK_PREDICTION_V2_FR.md",
    "PROTOCOLE_BENCHMARK_PREDICTION_V3_FR.md", "RESULTS_BIKESHARING_PREDICTION_V1_FR.md",
    "RESULTS_BIKESHARING_PREDICTION_V2_FR.md", "run_bike_prediction_benchmark_v1.py",
    "run_bike_prediction_benchmark_v2.py", "run_bike_prediction_benchmark.py",
    "run_bike_pipeline_control_rotation.py", "build_bike_pipeline_rotation_report.py",
    "source/hour.csv", "source/day.csv", "source/Readme.txt",
    "prediction_benchmark_v1/fold_metrics.csv", "prediction_benchmark_v1/selected_holdout_predictions.csv", "prediction_benchmark_v1/benchmark_manifest.json",
    "prediction_benchmark_v2/fold_metrics.csv", "prediction_benchmark_v2/selected_holdout_predictions.csv", "prediction_benchmark_v2/benchmark_manifest.json",
    "audit_bike_data_quality.py", "source_quality_audit_v1.json", "audit_bike_measurement_process_v1.py",
    "measurement_process_audit_v1.json", "RESULTS_MEASUREMENT_PROCESS_AUDIT_V1_FR.md",
    "pipeline_control_rotation_v1/inputs/bike_hour_100_bins.csv", "pipeline_control_rotation_v1/campaign_plan.json",
]
AIR_FILES = [
    ".gitignore", "README_FR.md", "fetch_air_quality_dataset.py", "audit_air_quality_source_v1.py",
    "source_manifest.json", "source_quality_audit_v1.json", "RESULTS_SOURCE_QUALITY_AUDIT_V1_FR.md",
    "PROTOCOLE_AIR_QUALITY_INSTRUMENTATION_V1_FR.md", "AMENDEMENT_PIPELINE_AIR_QUALITY_V1A_FR.md",
    "AIR_QUALITY_MISSINGNESS_BY_MONTH_V1.png",
    "run_air_quality_pipeline_control_rotation.py",
    "pipeline_control_rotation_v1/campaign_plan.json",
    "pipeline_control_rotation_v1/campaign_plan_superseded_v1.json",
    "pipeline_control_rotation_v1/campaign_plan_superseded_v2.json",
    "pipeline_control_rotation_v1/campaign_plan_superseded_v3.json",
    "pipeline_control_rotation_v1/campaign_plan_superseded_v4.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    grouped = [(name, ROOT / name, "project") for name in ROOT_FILES]
    for rels, base, group in [(AI4I_FILES, AI4I, "AI4I"), (BIKE_FILES, BIKE, "Bike Sharing"), (AIR_FILES, AIR, "Air Quality")]:
        grouped.extend(((base / rel).as_posix(), ROOT / base / rel, group) for rel in rels)
    unique = {path: (path, disk, group) for path, disk, group in grouped}
    missing = [rel for rel, disk, _group in unique.values() if not disk.is_file()]
    if missing:
        raise FileNotFoundError("Interim allowlist is incomplete:\n" + "\n".join(missing))
    forbidden_ext = {".pdf", ".zip", ".pstats", ".log"}
    private = [re.compile(r"C:\\Users\\citys\\", re.I), re.compile(r"D:\\UNIVERSAL_LOG_BACKUPS", re.I)]
    rows = []
    for rel, disk, group in sorted(unique.values()):
        if disk.suffix.lower() in forbidden_ext:
            raise ValueError(f"Forbidden file type: {rel}")
        if disk.suffix.lower() in {".md", ".py", ".json", ".csv", ".txt"}:
            content = disk.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(content) for pattern in private):
                raise ValueError(f"Local absolute path found: {rel}")
        rows.append({"path": rel, "group": group, "bytes": disk.stat().st_size, "sha256": sha256(disk)})
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "group", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT.name}: {len(rows)} explicit files, {sum(int(r['bytes']) for r in rows):,} bytes.")


if __name__ == "__main__":
    main()
