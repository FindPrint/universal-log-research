"""Extend the verified V9 full-project snapshot with the synthetic panel V1."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEST_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "PANEL_SYNTHETIQUE_VALIDATION_V1"
ACTIVE_V9 = ROOT / "output" / "master_whitepaper_v9"
ARCHIVED_V9 = ROOT / "archive_sources" / "master_whitepaper_v9"
V9_DIR = ARCHIVED_V9 if ARCHIVED_V9.is_dir() else ACTIVE_V9
BASE_ZIP = V9_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V9_2026-11-22.zip"
BACKUP_V9_MANIFEST = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-21_V5\BACKUP_MANIFEST_V9.json")
OUT_DIR = ROOT / "output" / "master_whitepaper_v10"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_ZIP = OUT_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V10_2026-11-22.zip"
OUT_SHA = OUT_ZIP.with_suffix(OUT_ZIP.suffix + ".sha256")
OVERLAY_MANIFEST = OUT_DIR / "PROJECT_SNAPSHOT_V10_OVERLAY_MANIFEST.json"
OVERLAY_ARC = "output/master_whitepaper_v10/PROJECT_SNAPSHOT_V10_OVERLAY_MANIFEST.json"
PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf"
PDF_SHA = PDF.with_suffix(PDF.suffix + ".sha256")

ROOT_FILES = [
    "README_V10_CURRENT.md", "COMPLETE_WHITEPAPER_V10_README.md",
    "PUBLICATION_SCOPE_V10.md",
    "RELEASE_V10_CHANGELOG_FR.md", "BACKUP_README_V10_FR.md",
    "PUBLICATION_MANIFEST_2026-11-22_PANEL_V10.csv",
    "build_grouped_panel_appendix_v10.py", "build_snapshot_v10.py",
    "build_publication_manifest_v10.py", "finalize_backup_manifest_v10.py",
]
OUTPUT_FILES = [
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf",
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf.sha256",
]
EXCLUDED_DIRS = {"__pycache__"}
VERSIONED_ROOT_DOCS = {
    "project_updates_v10/README.md": ROOT / "README.md",
    "project_updates_v10/PUBLICATION_SCOPE.md": ROOT / "PUBLICATION_SCOPE.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if not BASE_ZIP.is_file():
    raise FileNotFoundError(BASE_ZIP)
if not PDF.is_file() or not PDF_SHA.is_file():
    raise FileNotFoundError("V10 master PDF and checksum are required first.")
if not BACKUP_V9_MANIFEST.is_file() or not json.loads(BACKUP_V9_MANIFEST.read_text(encoding="utf-8")).get("verified"):
    raise RuntimeError("Verified V9 D-drive backup manifest is required before snapshot extension.")
if OUT_ZIP.exists():
    raise FileExistsError(f"Refusing to overwrite {OUT_ZIP}")

overlay: dict[str, Path] = {}
for name in ROOT_FILES:
    path = ROOT / name
    if not path.is_file():
        raise FileNotFoundError(path)
    overlay[path.relative_to(ROOT).as_posix()] = path
for relative, path in VERSIONED_ROOT_DOCS.items():
    if not path.is_file():
        raise FileNotFoundError(path)
    overlay[relative] = path
for name in OUTPUT_FILES:
    path = OUT_DIR / name
    if not path.is_file():
        raise FileNotFoundError(path)
    overlay[path.relative_to(ROOT).as_posix()] = path
for path in sorted(TEST_DIR.rglob("*")):
    if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts) or path.suffix.lower() == ".pyc":
        continue
    overlay[path.relative_to(ROOT).as_posix()] = path

with zipfile.ZipFile(BASE_ZIP, "r") as base:
    base_names = set(base.namelist())
collisions = base_names & (set(overlay) | {OVERLAY_ARC})
if collisions:
    raise RuntimeError(f"V10 overlay path collision: {sorted(collisions)[:20]}")
nested_zip_paths = [p for p in overlay if Path(p).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_")]
if nested_zip_paths:
    raise RuntimeError(f"Refusing nested project snapshot ZIP: {nested_zip_paths}")

# Copy the verified base without recompressing its large, previously audited members.
base_sidecar = BASE_ZIP.with_suffix(BASE_ZIP.suffix + ".sha256")
expected_base_sha = base_sidecar.read_text(encoding="ascii").split()[0].lower()
base_digest = hashlib.sha256()
print(f"Copying verified V9 base snapshot ({BASE_ZIP.stat().st_size:,} bytes) to the V10 path...", flush=True)
copied_bytes = 0
next_notice = 1024 * 1024 * 1024
with BASE_ZIP.open("rb") as source, OUT_ZIP.open("wb") as destination:
    while True:
        chunk = source.read(8 * 1024 * 1024)
        if not chunk:
            break
        destination.write(chunk)
        base_digest.update(chunk)
        copied_bytes += len(chunk)
        if copied_bytes >= next_notice:
            print(f"Copied {copied_bytes / (1024**3):.1f} GiB...", flush=True)
            next_notice += 1024 * 1024 * 1024
base_sha = base_digest.hexdigest()
if base_sha != expected_base_sha:
    OUT_ZIP.unlink(missing_ok=True)
    raise RuntimeError(f"V9 base SHA mismatch: {base_sha} != {expected_base_sha}")
shutil.copystat(BASE_ZIP, OUT_ZIP)

records = [
    {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}
    for relative, path in sorted(overlay.items())
]
print(f"Adding {len(records)} V10 overlay files...", flush=True)
OVERLAY_MANIFEST.write_text(json.dumps({
    "snapshot": OUT_ZIP.name,
    "created": "2026-11-22",
    "base_snapshot": BASE_ZIP.name,
    "base_snapshot_sha256": base_sha,
    "overlay_file_count": len(records),
    "overlay_files": records,
    "note": "V10 extends the D-verified V9 snapshot with a synthetic group-aware panel integration test, per-patient/per-control complete pipeline outputs, traces, protocol, and the updated master whitepaper. The V9 baseline README.md and PUBLICATION_SCOPE.md remain untouched at archive root; the current V10 copies are included at project_updates_v10/README.md and project_updates_v10/PUBLICATION_SCOPE.md. No clinical patient data are included. The snapshot ZIP is separate from and not embedded in the PDF.",
}, indent=2, ensure_ascii=False), encoding="utf-8")

with zipfile.ZipFile(OUT_ZIP, "a", allowZip64=True) as destination:
    for relative, path in sorted(overlay.items()):
        method = zipfile.ZIP_STORED if path.suffix.lower() in {".pdf", ".png", ".zip"} else zipfile.ZIP_DEFLATED
        destination.write(path, arcname=relative, compress_type=method)
    destination.write(OVERLAY_MANIFEST, arcname=OVERLAY_ARC, compress_type=zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(OUT_ZIP, "r") as final:
    names = final.namelist()
    duplicates = len(names) != len(set(names))
    nested = [name for name in names if Path(name).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_")]
    checks = []
    for relative, path in sorted(overlay.items()):
        payload_sha = hashlib.sha256(final.read(relative)).hexdigest()
        expected_sha = next(row["sha256"] for row in records if row["path"] == relative)
        checks.append({"path": relative, "sha256_matches": payload_sha == expected_sha})
if duplicates or nested or any(not row["sha256_matches"] for row in checks):
    raise RuntimeError("V10 ZIP verification failed.")
zip_sha = sha256(OUT_ZIP)
OUT_SHA.write_text(f"{zip_sha}  {OUT_ZIP.name}\n", encoding="ascii")
print(json.dumps({
    "base_sha256": base_sha, "base_crc_status": "inherited from verified V9 D-drive backup",
    "overlay_files": len(records), "overlay_members_read_back": len(checks),
    "zip_members": len(names), "duplicate_names": duplicates, "nested_snapshots": nested,
    "zip_bytes": OUT_ZIP.stat().st_size, "zip_sha256": zip_sha, "zip": str(OUT_ZIP),
}, indent=2, ensure_ascii=False))
