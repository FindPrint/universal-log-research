#!/usr/bin/env python
"""Create a path-redacted allowlist manifest for the V12 GitHub publication."""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "PUBLICATION_MANIFEST_V12.csv"
AI4I = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V1")
BIKE = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V2_BIKESHARING")
PROFILE = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/RUNTIME_PROFILE_V1")

EXACT = [
    ".gitattributes", "README.md", "README_V12_CURRENT.md", "PUBLICATION_SCOPE_V12.md", "RELEASE_V12_CHANGELOG_FR.md",
    "ACTIVITY_LOG_V12_2026-11-22.md", "THREE_LEVELS_AND_DELTA_ARCHIVE_PLAN_V1_FR.md",
    "DELTA_ARCHIVE_GUIDE_V1_FR.md", "build_project_delta.py", "reconstruct_project_from_delta.py",
    "test_delta_archive_smoke.py", "build_publication_manifest_v12.py", "LICENSE", "LICENSE-CC-BY-4.0.txt",
    "summarize_pipeline_layers.py",
    "LICENSES.md", "archive_sources/sanitize_snapshot_audit_public.py",
    "archive_sources/SNAPSHOT_OVERLAP_AUDIT_PUBLIC_V12.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/REPLICATION_P2_010_GEO_2026-11-20/pipeline_source/UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py",
]
AI4I_EXACT = [
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
BIKE_EXACT = [
    "README_FR.md", "fetch_bike_sharing_dataset.py", "dataset_manifest.json", "requirements-bikesharing.txt",
    "PROTOCOLE_BIKESHARING_V1_FR.md", "PROTOCOLE_BENCHMARK_PREDICTION_V2_FR.md",
    "PROTOCOLE_BENCHMARK_PREDICTION_V3_FR.md", "RESULTS_BIKESHARING_PREDICTION_V1_FR.md",
    "RESULTS_BIKESHARING_PREDICTION_V2_FR.md", "RESULTS_BIKESHARING_PREDICTION_V3_FR.md",
    "run_bike_prediction_benchmark_v1.py", "run_bike_prediction_benchmark_v2.py", "run_bike_prediction_benchmark.py",
    "run_bike_pipeline_control_rotation.py", "build_bike_pipeline_rotation_report.py",
    "source/hour.csv", "source/day.csv", "source/Readme.txt",
    "audit_bike_data_quality.py", "source_quality_audit_v1.json",
    "audit_bike_measurement_process_v1.py", "measurement_process_audit_v1.json",
    "RESULTS_MEASUREMENT_PROCESS_AUDIT_V1_FR.md",
    "prediction_benchmark_v1/fold_metrics.csv", "prediction_benchmark_v1/selected_holdout_predictions.csv", "prediction_benchmark_v1/benchmark_manifest.json",
    "prediction_benchmark_v2/fold_metrics.csv", "prediction_benchmark_v2/selected_holdout_predictions.csv", "prediction_benchmark_v2/benchmark_manifest.json",
    "prediction_benchmark_v3/fold_metrics.csv", "prediction_benchmark_v3/selected_holdout_predictions.csv", "prediction_benchmark_v3/benchmark_manifest.json",
    "pipeline_control_rotation_v1/inputs/bike_hour_100_bins.csv", "pipeline_control_rotation_v1/campaign_plan.json",
    "pipeline_control_rotation_v1/campaign_manifest.json", "pipeline_control_rotation_v1/control_rotation_summary.csv",
    "pipeline_control_rotation_v1/BIKESHARING_PIPELINE_CONTROL_ROTATION_V1_REPORT_FR.md",
    "pipeline_control_rotation_v1/public_summary_manifest.json", "pipeline_control_rotation_v1/t0_by_control_bike_v1.png",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_BIKESHARING_SUMMARY.csv",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_BIKESHARING_REPORT_FR.md",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_BIKESHARING_QUESTIONS_HEATMAP.png",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_BIKESHARING_CASCADE_THRESHOLDS.png",
    "pipeline_control_rotation_v1/PIPELINE_LAYERS_BIKESHARING_TLOG_CLASSES.png",
]
AIR_QUALITY = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V3_AIR_QUALITY")
AIR_QUALITY_EXACT = [
    "README_FR.md",
    "AIR_QUALITY_MISSINGNESS_BY_MONTH_V1.png",
    "PROTOCOLE_AIR_QUALITY_INSTRUMENTATION_V1_FR.md",
    "AMENDEMENT_PIPELINE_AIR_QUALITY_V1A_FR.md",
    "fetch_air_quality_dataset.py", "audit_air_quality_source_v1.py",
    "source_manifest.json", "source_quality_audit_v1.json",
    "RESULTS_SOURCE_QUALITY_AUDIT_V1_FR.md", "run_air_quality_pipeline_control_rotation.py",
]
PROFILE_EXACT = [
    "RUNTIME_PROFILE_REPORT_V1_FR.md", "profile_slow_run.py", "run_no_plot_experiment.py", "run_full_repeat.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    entries: list[tuple[str, Path, str]] = []
    for rel in EXACT:
        entries.append((rel, ROOT / rel, "project"))
    for rel in AI4I_EXACT:
        entries.append(((AI4I / rel).as_posix(), ROOT / AI4I / rel, "AI4I"))
    for rel in BIKE_EXACT:
        entries.append(((BIKE / rel).as_posix(), ROOT / BIKE / rel, "Bike Sharing"))
    for rel in AIR_QUALITY_EXACT:
        entries.append(((AIR_QUALITY / rel).as_posix(), ROOT / AIR_QUALITY / rel, "Air Quality"))
    for rel in PROFILE_EXACT:
        entries.append(((PROFILE / rel).as_posix(), ROOT / PROFILE / rel, "profiling"))
    unique: dict[str, tuple[str, Path, str]] = {entry[0]: entry for entry in entries}
    missing = [name for name, path, _group in unique.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Publication artifacts are not ready:\n" + "\n".join(missing))
    private_patterns = [re.compile(r"C:\\Users\\citys\\", re.I), re.compile(r"D:\\UNIVERSAL_LOG_BACKUPS", re.I)]
    output_rows = []
    for name, path, group in sorted(unique.values()):
        if path.suffix.lower() in {".zip", ".pdf", ".pstats", ".log"}:
            raise ValueError(f"Disallowed file type in public allowlist: {name}")
        if path.suffix.lower() in {".md", ".py", ".json", ".csv", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(text) for pattern in private_patterns):
                raise ValueError(f"Local absolute path found in would-be public artifact: {name}")
        output_rows.append({"path": name, "group": group, "bytes": path.stat().st_size, "sha256": sha256(path)})
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "group", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {OUTPUT.name}: {len(output_rows)} explicit public files; {sum(row['bytes'] for row in output_rows):,} bytes total.")


if __name__ == "__main__":
    main()
