"""Copy and verify the V10 package and grouped-panel audit on D:."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
BACKUP = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V10")
SOURCE_PACKAGE = ROOT / "output" / "master_whitepaper_v10"
BACKUP_PACKAGE = BACKUP / "master_whitepaper_v10"
SOURCE_TEST = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "PANEL_SYNTHETIQUE_VALIDATION_V1"
BACKUP_TEST = BACKUP / "project_updates_v10" / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "PANEL_SYNTHETIQUE_VALIDATION_V1"
PREVIOUS_V9 = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-21_V5\BACKUP_MANIFEST_V9.json")

ROOT_FILES = [
    "README.md", "README_V10_CURRENT.md", "COMPLETE_WHITEPAPER_V10_README.md",
    "PUBLICATION_SCOPE.md", "PUBLICATION_SCOPE_V10.md",
    "RELEASE_V10_CHANGELOG_FR.md", "BACKUP_README_V10_FR.md",
    "PUBLICATION_MANIFEST_2026-11-22_PANEL_V10.csv",
    "build_grouped_panel_appendix_v10.py", "build_snapshot_v10.py",
    "build_publication_manifest_v10.py", "finalize_backup_manifest_v10.py",
]
PACKAGE_FILES = [
    "PROJECT_SNAPSHOT_V10_OVERLAY_MANIFEST.json",
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf",
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf.sha256",
    "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V10_2026-11-22.zip",
    "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V10_2026-11-22.zip.sha256",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare(source: Path, dest: Path) -> dict:
    if not source.is_file() or not dest.is_file():
        return {"source": str(source), "backup": str(dest), "verified": False, "reason": "missing"}
    source_sha, backup_sha = sha256(source), sha256(dest)
    return {
        "source": str(source), "backup": str(dest),
        "source_bytes": source.stat().st_size, "backup_bytes": dest.stat().st_size,
        "source_sha256": source_sha, "backup_sha256": backup_sha,
        "verified": source.stat().st_size == dest.stat().st_size and source_sha == backup_sha,
    }


if not PREVIOUS_V9.is_file() or not json.loads(PREVIOUS_V9.read_text(encoding="utf-8")).get("verified"):
    raise RuntimeError("Verified V9 D-drive backup manifest is required.")

BACKUP.mkdir(parents=True, exist_ok=True)
BACKUP_PACKAGE.mkdir(parents=True, exist_ok=True)
BACKUP_UPDATES = BACKUP / "project_updates_v10"
BACKUP_UPDATES.mkdir(parents=True, exist_ok=True)
for name in PACKAGE_FILES:
    source = SOURCE_PACKAGE / name
    if not source.is_file():
        raise FileNotFoundError(source)
    shutil.copy2(source, BACKUP_PACKAGE / name)

for name in ROOT_FILES:
    source = ROOT / name
    if not source.is_file():
        raise FileNotFoundError(source)
    shutil.copy2(source, BACKUP_UPDATES / name)

shutil.copytree(
    SOURCE_TEST, BACKUP_TEST, dirs_exist_ok=True,
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    copy_function=shutil.copy2,
)

source_package_names = {p.name for p in SOURCE_PACKAGE.iterdir() if p.is_file()}
backup_package_names = {p.name for p in BACKUP_PACKAGE.iterdir() if p.is_file()}
package_names_ok = source_package_names == set(PACKAGE_FILES) == backup_package_names
package_checks = [compare(SOURCE_PACKAGE / name, BACKUP_PACKAGE / name) for name in PACKAGE_FILES]

source_test_files = {
    p.relative_to(SOURCE_TEST).as_posix(): p
    for p in SOURCE_TEST.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
}
backup_test_files = {
    p.relative_to(BACKUP_TEST).as_posix(): p
    for p in BACKUP_TEST.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
}
test_names_ok = set(source_test_files) == set(backup_test_files)
test_checks = [compare(source_test_files[name], backup_test_files[name]) for name in sorted(source_test_files)]

root_checks = [
    compare(ROOT / name, BACKUP_UPDATES / name)
    for name in ROOT_FILES
]

pdf_path = SOURCE_PACKAGE / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf"
zip_path = SOURCE_PACKAGE / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V10_2026-11-22.zip"
pdf_reader = PdfReader(str(pdf_path))
attachments = list(pdf_reader.attachments.keys())
active_pdfs = list((ROOT / "output").glob("*/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET*.pdf"))
single_active_pdf = len(active_pdfs) == 1 and active_pdfs[0] == pdf_path
previous = json.loads(PREVIOUS_V9.read_text(encoding="utf-8"))
checks = {
    "previous_v9_backup_verified": previous["verified"],
    "package_file_set_exact": package_names_ok,
    "package_source_backup_hashes_match": all(item["verified"] for item in package_checks),
    "panel_file_set_exact": test_names_ok,
    "panel_files_source_backup_hashes_match": all(item["verified"] for item in test_checks),
    "root_docs_and_scripts_match": all(item["verified"] for item in root_checks),
    "pdf_has_no_attachments": not attachments,
    "single_active_master_pdf": single_active_pdf,
}
manifest = {
    "created": "2026-11-22",
    "backup_root": str(BACKUP),
    "purpose": "Verify V10 master whitepaper, full-project snapshot, and synthetic grouped-panel test artifacts on D:.",
    "previous_v9_manifest_sha256": sha256(PREVIOUS_V9),
    "checks": checks,
    "package_files": package_checks,
    "panel_files": test_checks,
    "root_docs_and_scripts": root_checks,
    "pdf_pages": len(pdf_reader.pages),
    "pdf_attachments": attachments,
    "active_master_pdfs": [str(path) for path in active_pdfs],
    "zip_bytes": zip_path.stat().st_size,
    "zip_sha256": sha256(zip_path),
    "verified": all(checks.values()),
}
manifest_path = BACKUP / "BACKUP_MANIFEST_V10.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "verified": manifest["verified"], "checks": checks,
    "pdf_pages": len(pdf_reader.pages), "zip_bytes": zip_path.stat().st_size,
    "manifest": str(manifest_path),
}, indent=2, ensure_ascii=False))
if not manifest["verified"]:
    raise SystemExit(1)
