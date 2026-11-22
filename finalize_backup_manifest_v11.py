"""Copy V11 deliverables to D: and verify file sets, hashes, and master PDF status."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
BACKUP = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V11")
BACKUP_PACKAGE = BACKUP / "master_whitepaper_v11"
BACKUP_UPDATES = BACKUP / "project_updates_v11"
SOURCE_PACKAGE = ROOT / "output" / "master_whitepaper_v11"
SOURCE_TEST = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "TRANSITION_SENSITIVITY_V2"
BACKUP_TEST = BACKUP_UPDATES / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "TRANSITION_SENSITIVITY_V2"
PREVIOUS_V10 = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V10\BACKUP_MANIFEST_V10.json")

ROOT_FILES = [
    "README.md", "README_V11_CURRENT.md", "COMPLETE_WHITEPAPER_V11_README.md",
    "PUBLICATION_SCOPE.md", "PUBLICATION_SCOPE_V11.md", "RELEASE_V11_CHANGELOG_FR.md",
    "BACKUP_README_V11_FR.md", "PUBLICATION_MANIFEST_2026-11-22_SENSITIVITY_V11.csv",
    "build_master_whitepaper_v11.py", "build_snapshot_v11.py",
    "build_publication_manifest_v11.py", "finalize_backup_manifest_v11.py",
]
PACKAGE_FILES = [
    "PROJECT_SNAPSHOT_V11_OVERLAY_MANIFEST.json",
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf",
    "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf.sha256",
    "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip",
    "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip.sha256",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def compare(source: Path, dest: Path) -> dict:
    if not source.is_file() or not dest.is_file():
        return {"source": str(source), "backup": str(dest), "verified": False, "reason": "missing"}
    source_hash, backup_hash = sha256(source), sha256(dest)
    return {
        "source": str(source), "backup": str(dest),
        "source_bytes": source.stat().st_size, "backup_bytes": dest.stat().st_size,
        "source_sha256": source_hash, "backup_sha256": backup_hash,
        "verified": source.stat().st_size == dest.stat().st_size and source_hash == backup_hash,
    }

if not PREVIOUS_V10.is_file() or not json.loads(PREVIOUS_V10.read_text(encoding="utf-8")).get("verified"):
    raise RuntimeError("A verified V10 D-drive backup is required.")
BACKUP.mkdir(parents=True, exist_ok=True)
BACKUP_PACKAGE.mkdir(parents=True, exist_ok=True)
BACKUP_UPDATES.mkdir(parents=True, exist_ok=True)

for name in PACKAGE_FILES:
    source = SOURCE_PACKAGE / name
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = BACKUP_PACKAGE / name
    temporary = destination.with_name(destination.name + ".partial")
    shutil.copy2(source, temporary)
    if source.stat().st_size != temporary.stat().st_size or sha256(source) != sha256(temporary):
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Package copy failed pre-commit verification: {name}")
    temporary.replace(destination)
for name in ROOT_FILES:
    source = ROOT / name
    if not source.is_file():
        raise FileNotFoundError(source)
    shutil.copy2(source, BACKUP_UPDATES / name)
shutil.copytree(SOURCE_TEST, BACKUP_TEST, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                copy_function=shutil.copy2)

source_package_names = {p.name for p in SOURCE_PACKAGE.iterdir() if p.is_file()}
backup_package_names = {p.name for p in BACKUP_PACKAGE.iterdir() if p.is_file()}
package_set_ok = source_package_names == set(PACKAGE_FILES) == backup_package_names
package_checks = [compare(SOURCE_PACKAGE / name, BACKUP_PACKAGE / name) for name in PACKAGE_FILES]
source_test_files = {
    p.relative_to(SOURCE_TEST).as_posix(): p for p in SOURCE_TEST.rglob("*")
    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
}
backup_test_files = {
    p.relative_to(BACKUP_TEST).as_posix(): p for p in BACKUP_TEST.rglob("*")
    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
}
test_set_ok = set(source_test_files) == set(backup_test_files)
test_checks = [compare(source_test_files[key], backup_test_files[key]) for key in sorted(source_test_files)]
root_checks = [compare(ROOT / name, BACKUP_UPDATES / name) for name in ROOT_FILES]

pdf_path = SOURCE_PACKAGE / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf"
zip_path = SOURCE_PACKAGE / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip"
pdf = PdfReader(str(pdf_path))
attachments = list(pdf.attachments.keys())
active = list((ROOT / "output").glob("*/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET*.pdf"))
single_master = len(active) == 1 and active[0] == pdf_path
previous = json.loads(PREVIOUS_V10.read_text(encoding="utf-8"))
checks = {
    "previous_v10_backup_verified": previous["verified"],
    "package_file_set_exact": package_set_ok,
    "package_hashes_match": all(row["verified"] for row in package_checks),
    "campaign_file_set_exact": test_set_ok,
    "campaign_hashes_match": all(row["verified"] for row in test_checks),
    "root_docs_and_scripts_match": all(row["verified"] for row in root_checks),
    "pdf_has_no_attachments": not attachments,
    "single_active_master_pdf": single_master,
}
manifest = {
    "created": "2026-11-22", "backup_root": str(BACKUP),
    "purpose": "Verify V11 whitepaper, full-project snapshot, and synthetic sensitivity campaign on D:.",
    "previous_v10_manifest_sha256": sha256(PREVIOUS_V10),
    "checks": checks, "package_files": package_checks,
    "campaign_files": test_checks, "root_docs_and_scripts": root_checks,
    "pdf_pages": len(pdf.pages), "pdf_attachments": attachments,
    "active_master_pdfs": [str(path) for path in active],
    "zip_bytes": zip_path.stat().st_size, "zip_sha256": sha256(zip_path),
    "verified": all(checks.values()),
}
manifest_path = BACKUP / "BACKUP_MANIFEST_V11.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "verified": manifest["verified"], "checks": checks, "pdf_pages": len(pdf.pages),
    "zip_bytes": zip_path.stat().st_size, "manifest": str(manifest_path),
}, indent=2, ensure_ascii=False))
if not manifest["verified"]:
    raise SystemExit(1)
