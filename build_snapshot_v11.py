"""Extend the D-verified V10 snapshot with the synthetic sensitivity V2 campaign."""
from __future__ import annotations
import hashlib, json, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEST_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "TRANSITION_SENSITIVITY_V2"
V10_ACTIVE = ROOT / "output" / "master_whitepaper_v10"
V10_ARCHIVE = ROOT / "archive_sources" / "master_whitepaper_v10"
V10_DIR = V10_ARCHIVE if V10_ARCHIVE.is_dir() else V10_ACTIVE
BASE_ZIP = V10_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V10_2026-11-22.zip"
BACKUP_V10_MANIFEST = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V10\BACKUP_MANIFEST_V10.json")
OUT_DIR = ROOT / "output" / "master_whitepaper_v11"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_ZIP = OUT_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip"
BUILD_ZIP = OUT_ZIP.with_name(OUT_ZIP.name + ".building")
OUT_SHA = OUT_ZIP.with_suffix(OUT_ZIP.suffix + ".sha256")
OVERLAY_MANIFEST = OUT_DIR / "PROJECT_SNAPSHOT_V11_OVERLAY_MANIFEST.json"
OVERLAY_ARC = "output/master_whitepaper_v11/PROJECT_SNAPSHOT_V11_OVERLAY_MANIFEST.json"
PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf"
PDF_SHA = PDF.with_suffix(PDF.suffix + ".sha256")

ROOT_FILES = [
    "README_V11_CURRENT.md", "COMPLETE_WHITEPAPER_V11_README.md",
    "PUBLICATION_SCOPE_V11.md", "RELEASE_V11_CHANGELOG_FR.md",
    "BACKUP_README_V11_FR.md", "PUBLICATION_MANIFEST_2026-11-22_SENSITIVITY_V11.csv",
    "build_master_whitepaper_v11.py", "build_snapshot_v11.py",
    "build_publication_manifest_v11.py", "finalize_backup_manifest_v11.py",
]
VERSIONED_ROOT_DOCS = {
    "project_updates_v11/README.md": ROOT / "README.md",
    "project_updates_v11/PUBLICATION_SCOPE.md": ROOT / "PUBLICATION_SCOPE.md",
}
OUTPUT_FILES = [
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf",
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf.sha256",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

if not BASE_ZIP.is_file():
    raise FileNotFoundError(BASE_ZIP)
if not PDF.is_file() or not PDF_SHA.is_file():
    raise FileNotFoundError("V11 master PDF and checksum are required first.")
if not BACKUP_V10_MANIFEST.is_file() or not json.loads(BACKUP_V10_MANIFEST.read_text(encoding="utf-8")).get("verified"):
    raise RuntimeError("A verified V10 D-drive backup is required before extending the snapshot.")
if BUILD_ZIP.exists():
    raise FileExistsError(f"Refusing to overwrite unfinished snapshot build {BUILD_ZIP}")

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
    if not path.is_file() or "__pycache__" in path.parts or path.suffix.lower() == ".pyc":
        continue
    overlay[path.relative_to(ROOT).as_posix()] = path

with zipfile.ZipFile(BASE_ZIP, "r") as base:
    base_names = set(base.namelist())
collisions = base_names & (set(overlay) | {OVERLAY_ARC})
if collisions:
    raise RuntimeError(f"V11 overlay collisions: {sorted(collisions)[:20]}")
nested = [name for name in overlay if Path(name).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_")]
if nested:
    raise RuntimeError(f"Refusing to nest a snapshot ZIP: {nested}")

base_sidecar = BASE_ZIP.with_suffix(BASE_ZIP.suffix + ".sha256")
expected_base_sha = base_sidecar.read_text(encoding="ascii").split()[0].lower()
digest = hashlib.sha256()
print(f"Copying verified V10 base snapshot ({BASE_ZIP.stat().st_size:,} bytes)...", flush=True)
copied, next_notice = 0, 1024 * 1024 * 1024
with BASE_ZIP.open("rb") as source, BUILD_ZIP.open("wb") as dest:
    while True:
        block = source.read(8 * 1024 * 1024)
        if not block:
            break
        dest.write(block)
        digest.update(block)
        copied += len(block)
        if copied >= next_notice:
            print(f"Copied {copied / (1024**3):.1f} GiB...", flush=True)
            next_notice += 1024 * 1024 * 1024
base_sha = digest.hexdigest()
if base_sha != expected_base_sha:
    BUILD_ZIP.unlink(missing_ok=True)
    raise RuntimeError(f"V10 base SHA mismatch: {base_sha} != {expected_base_sha}")
shutil.copystat(BASE_ZIP, BUILD_ZIP)

records = [
    {"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)}
    for rel, path in sorted(overlay.items())
]
print(f"Adding {len(records)} V11 overlay files...", flush=True)
OVERLAY_MANIFEST.write_text(json.dumps({
    "snapshot": OUT_ZIP.name, "created": "2026-11-22",
    "base_snapshot": BASE_ZIP.name, "base_snapshot_sha256": base_sha,
    "overlay_file_count": len(records), "overlay_files": records,
    "note": "V11 extends the D-verified V10 snapshot with a frozen synthetic transition-sensitivity campaign, full per-run v6.0.1 outputs, source inputs, logs, figures, and the updated master whitepaper. The V10 root README and scope remain as the earlier baseline; current V11 copies are stored in project_updates_v11/. No clinical data are included. The snapshot ZIP is not embedded in the PDF.",
}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

with zipfile.ZipFile(BUILD_ZIP, "a", allowZip64=True) as dest:
    for rel, path in sorted(overlay.items()):
        method = zipfile.ZIP_STORED if path.suffix.lower() in {".pdf", ".png", ".zip"} else zipfile.ZIP_DEFLATED
        dest.write(path, arcname=rel, compress_type=method)
    dest.write(OVERLAY_MANIFEST, arcname=OVERLAY_ARC, compress_type=zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(BUILD_ZIP, "r") as final:
    names = final.namelist()
    duplicates = len(names) != len(set(names))
    nested_all = [name for name in names if Path(name).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_")]
    checks = []
    for rel, path in sorted(overlay.items()):
        embedded_sha = hashlib.sha256(final.read(rel)).hexdigest()
        expected = next(row["sha256"] for row in records if row["path"] == rel)
        checks.append(embedded_sha == expected)
if duplicates or nested_all or not all(checks):
    BUILD_ZIP.unlink(missing_ok=True)
    raise RuntimeError("V11 snapshot verification failed.")
zip_sha = sha256(BUILD_ZIP)
BUILD_ZIP.replace(OUT_ZIP)
OUT_SHA.write_text(f"{zip_sha}  {OUT_ZIP.name}\n", encoding="ascii")
print(json.dumps({
    "base_sha256": base_sha, "overlay_files": len(records),
    "overlay_members_read_back": sum(checks), "zip_members": len(names),
    "duplicate_names": duplicates, "nested_snapshots": nested_all,
    "zip_bytes": OUT_ZIP.stat().st_size, "zip_sha256": zip_sha, "zip": str(OUT_ZIP),
}, indent=2, ensure_ascii=False))
