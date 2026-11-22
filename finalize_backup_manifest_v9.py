"""Verify V9 whitepaper/snapshot and the new PDAC audit backup on D:."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
BACKUP = Path(r"D:\UNIVERSAL_LOG_BACKUPS\2026-11-21_V5")
SOURCE_PACKAGE = ROOT / "output" / "master_whitepaper_v9"
BACKUP_PACKAGE = BACKUP / "master_whitepaper_v9"
BACKUP_PROJECT = BACKUP / "project_updates_v9"
DATA_REL = Path("pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21")
DATA_FILES = [
    "AUDIT_DONNEES_LONGITUDINALES_ET_GROUPES_V9_FR.md",
    "audit_v6_0_1_grouped_input.py",
    "V6_0_1_GROUPED_INPUT_AUDIT.json",
    "DATASET_DISCOVERY_V9.csv",
    "SOURCE_REGISTER_V9.json",
    "BROUILLON_DEMANDE_DONNEES_KIRCHWEGER_2022_EN.md",
    "BROUILLON_DEMANDE_DONNEES_EDLAND_2023_EN.md",
]
ROOT_FILES = [
    "README.md",
    "README_V9_CURRENT.md",
    "COMPLETE_WHITEPAPER_V9_README.md",
    "PUBLICATION_SCOPE.md",
    "PUBLICATION_SCOPE_V9.md",
    "RELEASE_V9_CHANGELOG_FR.md",
    "BACKUP_README_V9_FR.md",
    "PUBLICATION_MANIFEST_2026-11-22_LONGITUDINAL_V9.csv",
    "build_ctdna_group_audit_appendix_v9.py",
    "build_snapshot_v9.py",
    "build_publication_manifest_v9.py",
    "finalize_backup_manifest_v9.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare(source: Path, dest: Path, label: str, known_source_sha: dict[str, str] | None = None) -> dict:
    problems, records = [], []
    if not source.is_file() or not dest.is_file():
        return {"label": label, "verified": False, "problem": "missing source or backup"}
    src_size, dst_size = source.stat().st_size, dest.stat().st_size
    src_sha = (known_source_sha or {}).get(source.name) or sha256(source)
    dst_sha = sha256(dest)
    if src_size != dst_size or src_sha != dst_sha:
        problems.append({"source_bytes": src_size, "backup_bytes": dst_size, "source_sha256": src_sha, "backup_sha256": dst_sha})
    records.append({"source": str(source), "backup": str(dest), "bytes": dst_size, "sha256": dst_sha})
    return {"label": label, "files": records, "mismatches": problems, "verified": not problems}


previous = json.loads((BACKUP / "BACKUP_MANIFEST_V8.json").read_text(encoding="utf-8"))
if not previous.get("verified", False):
    raise RuntimeError("V8 backup manifest is not verified")

pdf_name = "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V9_2026-11-22.pdf"
zip_name = "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V9_2026-11-22.zip"
expected_package = {"PROJECT_SNAPSHOT_V9_OVERLAY_MANIFEST.json", pdf_name, f"{pdf_name}.sha256", zip_name, f"{zip_name}.sha256"}
source_files = {p.name for p in SOURCE_PACKAGE.iterdir() if p.is_file()}
backup_files = {p.name for p in BACKUP_PACKAGE.iterdir() if p.is_file()}
package_file_set_ok = source_files == expected_package and backup_files == expected_package
zip_sha = (SOURCE_PACKAGE / f"{zip_name}.sha256").read_text(encoding="ascii").split()[0].lower()
pdf_sha = (SOURCE_PACKAGE / f"{pdf_name}.sha256").read_text(encoding="ascii").split()[0].lower()
package_checks = [
    compare(SOURCE_PACKAGE / name, BACKUP_PACKAGE / name, name, {zip_name: zip_sha, pdf_name: pdf_sha})
    for name in sorted(expected_package)
]
package_verified = package_file_set_ok and all(c["verified"] for c in package_checks)

data_source = ROOT / DATA_REL
data_dest = BACKUP_PROJECT / DATA_REL
data_checks = [compare(data_source / name, data_dest / name, name) for name in DATA_FILES]
data_verified = all(c["verified"] for c in data_checks)

root_checks = []
for name in ROOT_FILES:
    root_checks.append(compare(ROOT / name, BACKUP_PROJECT / name, name))
root_verified = all(c["verified"] for c in root_checks)

reader = PdfReader(str(SOURCE_PACKAGE / pdf_name))
page_count = len(reader.pages)
attachments = list(reader.attachments.keys())
active_pdfs = list((ROOT / "output").glob("*/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET*.pdf"))
single_active = len(active_pdfs) == 1 and active_pdfs[0] == SOURCE_PACKAGE / pdf_name
checks = {
    "v8_backup_verified": previous["verified"],
    "v9_package_contents_exact": package_file_set_ok,
    "v9_package_source_backup_hashes_match": package_verified,
    "v9_audit_files_match_source": data_verified,
    "v9_root_docs_and_scripts_match_source": root_verified,
    "pdf_has_no_attachments": not attachments,
    "single_active_master_pdf": single_active,
}
manifest = {
    "created": "2026-11-22",
    "backup_root": str(BACKUP),
    "purpose": "Verify V9 whitepaper, full project snapshot and grouped longitudinal ctDNA audit on D:.",
    "previous_v8_manifest_sha256": sha256(BACKUP / "BACKUP_MANIFEST_V8.json"),
    "checks": checks,
    "package_files": package_checks,
    "audit_files": data_checks,
    "root_docs_and_scripts": root_checks,
    "pdf_pages": page_count,
    "pdf_attachments": attachments,
    "active_master_pdfs": [str(p) for p in active_pdfs],
    "zip_bytes": (BACKUP_PACKAGE / zip_name).stat().st_size if (BACKUP_PACKAGE / zip_name).is_file() else None,
    "verified": all(checks.values()),
}
target = BACKUP / "BACKUP_MANIFEST_V9.json"
target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "verified": manifest["verified"],
    "checks": checks,
    "pdf_pages": page_count,
    "zip_bytes": manifest["zip_bytes"],
    "manifest": str(target),
}, indent=2, ensure_ascii=False))
if not manifest["verified"]:
    raise SystemExit(1)
