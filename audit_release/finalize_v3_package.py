# SPDX-License-Identifier: MIT
"""Append the 2026-11-15 audit correction to V2 and validate the V3 archive."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2_ZIP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V2.zip"
V3_ZIP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V3.zip"
TEMP_ZIP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V3.zip.tmp"
CATALOG = ROOT / "PROJECT_FILE_CATALOG_V3.csv"
SUMS = ROOT / "SHA256SUMS_V3.txt"
SIDE_CAR = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V3.zip.sha256"
QA = ROOT / "audit_release" / "whitepaper_qa" / "supplement_2026-11-15" / "v3_package_qa.json"

ROOT_FILES = [
    "AUDIT_UNIVERSAL_LOG_WHITEPAPER_V3.pdf",
    "AUDIT_SUPPLEMENT_2026-11-15.md",
    "README_AUDIT_REPRODUCTION_V3.md",
    "REPRODUCE_SUPPLEMENT_V3.ps1",
    "SUPPLEMENT_ATTACHMENT_INDEX_V3.csv",
    "UNIVERSAL_LOG_v5.3_COHEND_ONLY.py",
    "UNIVERSAL_LOG_v5.8_COHEND_ONLY.py",
    "UNIVERSAL_LOG_v5.9.0_COHEND_ONLY.py",
    "UNIVERSAL_LOG_v5.9.2.py",
    "audit_release/build_v3_whitepaper_seedtrace.py",
    "audit_release/finalize_v3_package.py",
    "audit_release/whitepaper_qa/supplement_2026-11-15/v3_whitepaper_qa.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_entry(zf: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with zf.open(name) as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gather_new_files() -> list[Path]:
    dated = ROOT / "audit_release" / "2026-11-15_l7b_seedtrace_fix"
    paths = [p for p in dated.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"]
    paths.extend(ROOT / rel for rel in ROOT_FILES)
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing V3 package files: " + ", ".join(missing))
    return sorted({p.resolve() for p in paths}, key=lambda p: str(p).casefold())


def main() -> None:
    if not V2_ZIP.is_file():
        raise FileNotFoundError(V2_ZIP)
    for path in (V3_ZIP, TEMP_ZIP):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    new_files = gather_new_files()
    with zipfile.ZipFile(V2_ZIP, "r") as old:
        old_infos = [i for i in old.infolist() if not i.is_dir()]
        old_names = {i.filename for i in old_infos}
        if old.testzip() is not None:
            raise zipfile.BadZipFile("V2 archive CRC failure")
        old_records = {i.filename: {"path": i.filename, "bytes": i.file_size, "sha256": sha256_entry(old, i.filename)} for i in old_infos}

    new_records = {}
    for path in new_files:
        arcname = path.relative_to(ROOT).as_posix()
        if arcname in old_names:
            raise ValueError(f"V2 ZIP already contains {arcname}; refusing duplicate")
        new_records[arcname] = {"path": arcname, "bytes": path.stat().st_size, "sha256": sha256_file(path)}

    catalog_buffer = io.StringIO(newline="")
    writer = csv.writer(catalog_buffer)
    writer.writerow(["path", "bytes", "sha256"])
    for record in sorted([*old_records.values(), *new_records.values()], key=lambda row: row["path"].casefold()):
        writer.writerow([record["path"], record["bytes"], record["sha256"]])
    CATALOG.write_text(catalog_buffer.getvalue(), encoding="utf-8-sig")

    sum_records = sorted([*old_records.values(), *new_records.values()], key=lambda row: row["path"].casefold())
    sum_records.append({"path": CATALOG.name, "bytes": CATALOG.stat().st_size, "sha256": sha256_file(CATALOG)})
    with SUMS.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# SHA-256 for V3 archive payload and catalog; excludes this file and the archive itself.\n")
        for record in sum_records:
            f.write(f"{record['sha256']}  {record['path']}\n")

    shutil.copy2(V2_ZIP, TEMP_ZIP)
    with zipfile.ZipFile(TEMP_ZIP, "a", allowZip64=True) as zf:
        existing = set(zf.namelist())
        for path in [*new_files, CATALOG, SUMS]:
            arcname = path.relative_to(ROOT).as_posix()
            if arcname in existing:
                raise ValueError(f"Duplicate V3 archive path: {arcname}")
            suffix = path.suffix.lower()
            compression = zipfile.ZIP_STORED if suffix in {".pdf", ".png", ".jpg", ".jpeg", ".zip"} else zipfile.ZIP_DEFLATED
            zf.write(path, arcname=arcname, compress_type=compression, compresslevel=6 if compression == zipfile.ZIP_DEFLATED else None)
            existing.add(arcname)
    os.replace(TEMP_ZIP, V3_ZIP)

    with zipfile.ZipFile(V3_ZIP, "r") as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise AssertionError("Duplicate ZIP entries")
        if zf.testzip() is not None:
            raise zipfile.BadZipFile("V3 archive CRC failure")
        if any(".venv/" in name or name.startswith(".venv\\") for name in names):
            raise AssertionError(".venv unexpectedly included")
        for name, record in {**old_records, **new_records}.items():
            if sha256_entry(zf, name) != record["sha256"]:
                raise AssertionError(f"Payload hash mismatch: {name}")
        for manifest in (CATALOG, SUMS):
            if sha256_entry(zf, manifest.name) != sha256_file(manifest):
                raise AssertionError(f"Manifest mismatch: {manifest.name}")

    SIDE_CAR.write_text(f"{sha256_file(V3_ZIP)}  {V3_ZIP.name}\n", encoding="utf-8")
    report = {
        "status": "pass",
        "source_archive": V2_ZIP.name,
        "source_entries": len(old_records),
        "new_payload_files": len(new_files),
        "manifest_files": 2,
        "expected_entries": len(old_records) + len(new_files) + 2,
        "archive": V3_ZIP.name,
        "entries": len(names),
        "bytes": V3_ZIP.stat().st_size,
        "sha256": sha256_file(V3_ZIP),
        "catalog": CATALOG.name,
        "sha256sums": SUMS.name,
        "sidecar": SIDE_CAR.name,
        "crc": "pass",
        "hash_validation": "pass",
        "venv_included": False,
    }
    QA.parent.mkdir(parents=True, exist_ok=True)
    QA.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
