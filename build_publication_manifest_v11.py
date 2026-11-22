"""Create the curated, size/hash-pinned public source manifest for V11."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEST = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "TRANSITION_SENSITIVITY_V2"
OUTPUT = ROOT / "PUBLICATION_MANIFEST_2026-11-22_SENSITIVITY_V11.csv"
RUN_MANIFEST = TEST / "run_manifest.json"
PUBLIC_RUN_MANIFEST = TEST / "run_manifest_public.json"
FILES = [
    "README.md", "README_V11_CURRENT.md", "COMPLETE_WHITEPAPER_V11_README.md",
    "PUBLICATION_SCOPE.md", "PUBLICATION_SCOPE_V11.md", "RELEASE_V11_CHANGELOG_FR.md",
    "BACKUP_README_V11_FR.md", "build_master_whitepaper_v11.py", "build_snapshot_v11.py",
    "build_publication_manifest_v11.py", "finalize_backup_manifest_v11.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/README_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/PROTOCOLE_SENSIBILITE_TRANSITIONS_V2_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/CORRECTION_RAPPORT_V2_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/ENVIRONMENT_LOCK_V2.txt",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/run_transition_sensitivity_v2.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/build_sensitivity_report_v2.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/AUDIT_RESULTATS_SENSIBILITE_V2_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/PUBLIC_VALIDATION_SUMMARY_V2.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/campaign_plan.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/run_manifest_public.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/validation_results.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/patient_control_summary.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/descriptive_summary.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/time_axis_localization_summary.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/runtime_summary_v2.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/V2_T0_BY_CONTROL.png",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/V2_TLOG_BY_CONDITION_CONTROL.png",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/logs/AUDIT_RESULTATS_SENSIBILITE_V2_FR_PRE_CORRECTION.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/REPLICATION_P2_010_GEO_2026-11-20/pipeline_source/UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py",
]
FILES.extend(
    f"pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/inputs/{path.name}"
    for path in sorted((TEST / "inputs").glob("*.csv"))
)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

records = []
run_manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
run_manifest["pipeline_source"] = (
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-20/REPLICATION_P2_010_GEO_2026-11-20/"
    "pipeline_source/UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
)
run_manifest["summary_path"] = (
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/"
    "patient_control_summary.csv"
)
run_manifest["local_absolute_paths_redacted"] = True
PUBLIC_RUN_MANIFEST.write_text(json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for relative in FILES:
    path = ROOT / Path(relative)
    if not path.is_file():
        raise FileNotFoundError(path)
    records.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
print(f"Wrote {len(records)} file records to {OUTPUT}")
