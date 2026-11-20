# SPDX-License-Identifier: MIT
"""Append the dated audit supplement to V1 and produce a V2 ZIP plus hashes."""
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
V1_ZIP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip"
V2_ZIP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V2.zip"
TEMP_ZIP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V2.zip.tmp"
CATALOG = ROOT / "PROJECT_FILE_CATALOG_V2.csv"
SUMS = ROOT / "SHA256SUMS_V2.txt"
SIDE_CAR = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT_V2.zip.sha256"

ROOT_FILES = [
    "AUDIT_UNIVERSAL_LOG_WHITEPAPER_V2.pdf",
    "AUDIT_SUPPLEMENT_2026-11-14.md",
    "README_AUDIT_REPRODUCTION_V2.md",
    "REPRODUCE_SUPPLEMENT_V2.ps1",
    "SUPPLEMENT_ATTACHMENT_INDEX.csv",
    "audit_release/build_v2_whitepaper_supplement.py",
    "audit_release/run_matched_v59_v591_replay.py",
    "audit_release/run_l7b_integration.py",
    "audit_release/run_l7b_full_reduced.py",
    "audit_release/summarize_l7b_light.py",
    "audit_release/finalize_v2_package.py",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_zip_entry(zf: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with zf.open(name) as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gather_new_files() -> list[Path]:
    paths = []
    dated = ROOT / "audit_release"
    for folder in sorted(dated.glob("2026-11-14_*")):
        if folder.is_dir():
            paths.extend(p for p in folder.rglob("*") if p.is_file())
    qa_dir = dated / "whitepaper_qa" / "supplement_2026-11-14"
    if qa_dir.exists():
        paths.extend(p for p in qa_dir.rglob("*") if p.is_file())
    paths.extend(ROOT / rel for rel in ROOT_FILES)
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing V2 package files: " + ", ".join(missing))
    return sorted({p.resolve() for p in paths}, key=lambda p: str(p).casefold())


def main() -> None:
    for path in (V1_ZIP, V2_ZIP, TEMP_ZIP):
        if path == V1_ZIP and not path.is_file():
            raise FileNotFoundError(path)
        if path != V1_ZIP and path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    new_files = gather_new_files()

    # Hash the exact V1 ZIP payload before adding the supplement.
    with zipfile.ZipFile(V1_ZIP, "r") as old:
        infos = [i for i in old.infolist() if not i.is_dir()]
        old_names = {i.filename for i in infos}
        if old.testzip() is not None:
            raise zipfile.BadZipFile("V1 archive CRC failure")
        records = {
            i.filename: {
                "path": i.filename,
                "bytes": i.file_size,
                "sha256": sha256_zip_entry(old, i.filename),
            }
            for i in infos
        }
    new_records = {}
    for path in new_files:
        arcname = path.relative_to(ROOT).as_posix()
        if arcname in old_names:
            raise ValueError(f"V1 ZIP already contains new path {arcname}; refusing duplicate")
        new_records[arcname] = {"path": arcname, "bytes": path.stat().st_size, "sha256": sha256_file(path)}

    # Catalog covers every payload file but excludes the two V2 manifests to
    # avoid self-reference; SHA256SUMS_V2 covers payload plus catalog.
    catalog_buffer = io.StringIO(newline="")
    catalog_writer = csv.writer(catalog_buffer)
    catalog_writer.writerow(["path", "bytes", "sha256"])
    for record in sorted([*records.values(), *new_records.values()], key=lambda r: r["path"].casefold()):
        catalog_writer.writerow([record["path"], record["bytes"], record["sha256"]])
    CATALOG.write_text(catalog_buffer.getvalue(), encoding="utf-8-sig")

    sum_rows = sorted([*records.values(), *new_records.values()], key=lambda r: r["path"].casefold())
    sum_rows.append({"path": CATALOG.name, "bytes": CATALOG.stat().st_size, "sha256": sha256_file(CATALOG)})
    with SUMS.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# SHA-256 for V2 archive payload and catalog; excludes this file and the archive itself.\n")
        for record in sum_rows:
            f.write(f"{record['sha256']}  {record['path']}\n")

    # Copy V1, append only new files and the two V2 manifests. PDFs and images
    # are stored directly because they are already compressed; text is deflated.
    shutil.copy2(V1_ZIP, TEMP_ZIP)
    with zipfile.ZipFile(TEMP_ZIP, "a", allowZip64=True) as zf:
        existing = set(zf.namelist())
        append_paths = list(new_files) + [CATALOG, SUMS]
        for path in append_paths:
            arcname = path.relative_to(ROOT).as_posix()
            if arcname in existing:
                raise ValueError(f"Duplicate archive path: {arcname}")
            suffix = path.suffix.lower()
            compression = zipfile.ZIP_STORED if suffix in {".pdf", ".png", ".jpg", ".jpeg", ".zip"} else zipfile.ZIP_DEFLATED
            zf.write(path, arcname=arcname, compress_type=compression, compresslevel=6 if compression == zipfile.ZIP_DEFLATED else None)
            existing.add(arcname)
    os.replace(TEMP_ZIP, V2_ZIP)

    # Validate CRC, entry uniqueness, absence of .venv, and all content hashes.
    with zipfile.ZipFile(V2_ZIP, "r") as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise AssertionError("Duplicate ZIP entries")
        if zf.testzip() is not None:
            raise zipfile.BadZipFile("V2 archive CRC failure")
        if any(".venv/" in n or n.startswith(".venv\\") for n in names):
            raise AssertionError(".venv was unexpectedly included")
        for name, record in {**records, **new_records}.items():
            if sha256_zip_entry(zf, name) != record["sha256"]:
                raise AssertionError(f"Hash mismatch inside V2 ZIP: {name}")
        if sha256_zip_entry(zf, CATALOG.name) != sha256_file(CATALOG):
            raise AssertionError("Catalog in V2 ZIP does not match the source file")
        if sha256_zip_entry(zf, SUMS.name) != sha256_file(SUMS):
            raise AssertionError("SHA256SUMS_V2 in ZIP does not match the source file")

    sidecar = f"{sha256_file(V2_ZIP)}  {V2_ZIP.name}\n"
    SIDE_CAR.write_text(sidecar, encoding="utf-8")
    report = {
        "status": "pass",
        "v1_archive": V1_ZIP.name,
        "v1_entries": len(records),
        "new_payload_files": len(new_files),
        "v2_manifest_files": 2,
        "v2_entries_expected": len(records) + len(new_files) + 2,
        "v2_archive": V2_ZIP.name,
        "v2_entries": len(zipfile.ZipFile(V2_ZIP, "r").namelist()),
        "v2_bytes": V2_ZIP.stat().st_size,
        "v2_sha256": sha256_file(V2_ZIP),
        "catalog": CATALOG.name,
        "sha256sums": SUMS.name,
        "sidecar": SIDE_CAR.name,
        "crc": "pass",
        "hash_validation": "pass",
        "venv_included": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
