"""Rebuild the V9 publication manifest from the frozen deliverable list."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21"
OUTPUT = ROOT / "PUBLICATION_MANIFEST_2026-11-22_LONGITUDINAL_V9.csv"

FILES = [
    "README.md",
    "README_V9_CURRENT.md",
    "COMPLETE_WHITEPAPER_V9_README.md",
    "PUBLICATION_SCOPE.md",
    "PUBLICATION_SCOPE_V9.md",
    "RELEASE_V9_CHANGELOG_FR.md",
    "BACKUP_README_V9_FR.md",
    "build_ctdna_group_audit_appendix_v9.py",
    "build_snapshot_v9.py",
    "build_publication_manifest_v9.py",
    "finalize_backup_manifest_v9.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/AUDIT_DONNEES_LONGITUDINALES_ET_GROUPES_V9_FR.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/audit_v6_0_1_grouped_input.py",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/V6_0_1_GROUPED_INPUT_AUDIT.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/DATASET_DISCOVERY_V9.csv",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/SOURCE_REGISTER_V9.json",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/BROUILLON_DEMANDE_DONNEES_KIRCHWEGER_2022_EN.md",
    "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/BROUILLON_DEMANDE_DONNEES_EDLAND_2023_EN.md",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
