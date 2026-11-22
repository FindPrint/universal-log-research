"""Extend the V8 full-project ZIP with the V9 audit and master whitepaper."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21"
ARCHIVED_V8 = ROOT / "archive_sources" / "master_whitepaper_v8"
ACTIVE_V8 = ROOT / "output" / "master_whitepaper_v8"
BASE_DIR = ARCHIVED_V8 if ARCHIVED_V8.is_dir() else ACTIVE_V8
BASE_ZIP = BASE_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V8_2026-11-21.zip"
OUT_DIR = ROOT / "output" / "master_whitepaper_v9"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_ZIP = OUT_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V9_2026-11-22.zip"
OUT_SHA = OUT_ZIP.with_suffix(OUT_ZIP.suffix + ".sha256")
MANIFEST = OUT_DIR / "PROJECT_SNAPSHOT_V9_OVERLAY_MANIFEST.json"
MANIFEST_ARC = "output/master_whitepaper_v9/PROJECT_SNAPSHOT_V9_OVERLAY_MANIFEST.json"
PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V9_2026-11-22.pdf"
PDF_SHA = PDF.with_suffix(PDF.suffix + ".sha256")
PUBLICATION_MANIFEST = ROOT / "PUBLICATION_MANIFEST_2026-11-22_LONGITUDINAL_V9.csv"

root_paths = [
    ROOT / "README_V9_CURRENT.md",
    ROOT / "COMPLETE_WHITEPAPER_V9_README.md",
    ROOT / "PUBLICATION_SCOPE_V9.md",
    ROOT / "RELEASE_V9_CHANGELOG_FR.md",
    ROOT / "BACKUP_README_V9_FR.md",
    PUBLICATION_MANIFEST,
    ROOT / "build_ctdna_group_audit_appendix_v9.py",
    ROOT / "build_snapshot_v9.py",
    ROOT / "build_publication_manifest_v9.py",
    ROOT / "finalize_backup_manifest_v9.py",
    PDF,
    PDF_SHA,
]
data_names = [
    "AUDIT_DONNEES_LONGITUDINALES_ET_GROUPES_V9_FR.md",
    "audit_v6_0_1_grouped_input.py",
    "V6_0_1_GROUPED_INPUT_AUDIT.json",
    "DATASET_DISCOVERY_V9.csv",
    "SOURCE_REGISTER_V9.json",
    "BROUILLON_DEMANDE_DONNEES_KIRCHWEGER_2022_EN.md",
    "BROUILLON_DEMANDE_DONNEES_EDLAND_2023_EN.md",
]
overlay: dict[str, Path] = {p.relative_to(ROOT).as_posix(): p for p in root_paths}
for name in data_names:
    p = DATA_DIR / name
    overlay[p.relative_to(ROOT).as_posix()] = p

if OUT_ZIP.exists():
    raise FileExistsError(f"Refusing to overwrite {OUT_ZIP}")
if not BASE_ZIP.is_file() or not PDF.is_file() or not PDF_SHA.is_file():
    raise FileNotFoundError("V8 base ZIP and V9 PDF with checksum are required")
missing = [str(path) for path in overlay.values() if not path.is_file()]
if missing:
    raise FileNotFoundError(missing)

with zipfile.ZipFile(BASE_ZIP, "r") as base:
    base_names = set(base.namelist())
collision = base_names & (set(overlay) | {MANIFEST_ARC})
if collision:
    raise RuntimeError(f"V9 overlay collision with V8 base: {sorted(collision)[:20]}")

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

base_sidecar = BASE_ZIP.with_suffix(BASE_ZIP.suffix + ".sha256")
expected_base_sha = base_sidecar.read_text(encoding="ascii").split()[0].lower()
previous_backup = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-21_V5\BACKUP_MANIFEST_V8.json")
if not previous_backup.is_file() or not json.loads(previous_backup.read_text(encoding="utf-8")).get("verified", False):
    raise RuntimeError("The V8 D-drive backup manifest must be verified before extending its snapshot")

# Copy the base once while calculating its digest. V8's backup manifest records
# a passed CRC check, so only new overlay members are read back for CRC/SHA QA.
base_digest = hashlib.sha256()
with BASE_ZIP.open("rb") as src, OUT_ZIP.open("wb") as dst:
    while True:
        chunk = src.read(8 * 1024 * 1024)
        if not chunk:
            break
        dst.write(chunk)
        base_digest.update(chunk)
base_sha = base_digest.hexdigest()
shutil.copystat(BASE_ZIP, OUT_ZIP)
if base_sha != expected_base_sha:
    OUT_ZIP.unlink(missing_ok=True)
    raise RuntimeError(f"V8 base ZIP hash mismatch: {base_sha} != {expected_base_sha}")

records = [
    {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}
    for relative, path in sorted(overlay.items())
]
MANIFEST.write_text(json.dumps({
    "snapshot": OUT_ZIP.name,
    "created": "2026-11-22",
    "base_snapshot": BASE_ZIP.name,
    "base_snapshot_sha256": base_sha,
    "overlay_file_count": len(records),
    "overlay_files": records,
    "note": "V9 extends the V8 snapshot with a source-level repeated-measures compatibility audit, a corrected attribution for the 70-patient ctDNA paper, a multi-source data-access screen, two unsent data-request drafts, and the V9 master PDF. No patient-level ctDNA data are embedded and no previous snapshot ZIP is nested.",
}, indent=2, ensure_ascii=False), encoding="utf-8")

with zipfile.ZipFile(OUT_ZIP, "a", allowZip64=True) as destination:
    for relative, path in sorted(overlay.items()):
        compression = zipfile.ZIP_STORED if path.suffix.lower() in {".pdf", ".png", ".zip"} else zipfile.ZIP_DEFLATED
        destination.write(path, arcname=relative, compress_type=compression)
    destination.write(MANIFEST, arcname=MANIFEST_ARC, compress_type=zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(OUT_ZIP, "r") as final_zip:
    final_names = final_zip.namelist()
    nested = [name for name in final_names if Path(name).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V")]
    duplicate_names = len(final_names) != len(set(final_names))
    overlay_checks = []
    for relative, path in sorted(overlay.items()):
        payload = final_zip.read(relative)
        digest = hashlib.sha256(payload).hexdigest()
        expected = next(record["sha256"] for record in records if record["path"] == relative)
        overlay_checks.append({"path": relative, "crc_ok": True, "sha256_matches": digest == expected})
    bad_overlay = [item for item in overlay_checks if not item["sha256_matches"]]
if duplicate_names:
    raise RuntimeError("Duplicate ZIP member names found")
if nested:
    raise RuntimeError(f"Nested project snapshots found: {nested}")
if bad_overlay:
    raise RuntimeError(f"V9 overlay member verification failed: {bad_overlay}")

out_sha = sha256(OUT_ZIP)
OUT_SHA.write_text(f"{out_sha}  {OUT_ZIP.name}\n", encoding="ascii")
print(json.dumps({
    "base_sha256": base_sha,
    "base_v8_crc_status": "reused from verified V8 snapshot; V9 overlay members read back and verified",
    "overlay_files": len(records),
    "members": len(final_names),
    "duplicate_members": duplicate_names,
    "overlay_members_verified": len(overlay_checks),
    "nested_project_snapshots": len(nested),
    "crc_test": "passed",
    "zip_bytes": OUT_ZIP.stat().st_size,
    "zip_sha256": out_sha,
    "zip": str(OUT_ZIP),
}, indent=2, ensure_ascii=False))
