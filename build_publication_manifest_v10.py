"""Create the compact public V10 source/result manifest with SHA-256 hashes."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "PUBLICATION_MANIFEST_2026-11-22_PANEL_V10.csv"

FILES = [
    "README.md",
    "README_V10_CURRENT.md",
    "COMPLETE_WHITEPAPER_V10_README.md",
    "PUBLICATION_SCOPE.md",
    "PUBLICATION_SCOPE_V10.md",
    "RELEASE_V10_CHANGELOG_FR.md",
    "BACKUP_README_V10_FR.md",
    "build_grouped_panel_appendix_v10.py",
    "build_snapshot_v10.py",
    "build_publication_manifest_v10.py",
    "finalize_backup_manifest_v10.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/README_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/PROTOCOLE_GROUPE_PANEL_V1_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/AUDIT_RESULTATS_PANEL_SYNTHETIQUE_V1_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/run_grouped_panel_validation.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/verify_short_core_gate.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/PUBLIC_VALIDATION_SUMMARY_V1.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/short_core_gate_check.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/patient_control_summary.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/inputs/synthetic_longitudinal_panel_v1.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/PANEL_SYNTHETIQUE_VALIDATION_V1/PANEL_T0_TLOG_HEATMAP_V1.png",
]


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


rows = []
for relative in FILES:
    path = ROOT / Path(relative)
    if not path.is_file():
        raise FileNotFoundError(path)
    rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} file records to {OUTPUT}")
