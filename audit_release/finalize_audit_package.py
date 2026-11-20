"""Refresh audit hashes, assemble the complete ZIP, and verify its contents."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "PROJECT_FILE_CATALOG.csv"
CHECKSUMS = ROOT / "SHA256SUMS.txt"
PDF = ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER.pdf"
ZIP_PATH = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip"
ZIP_TMP = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip.building"
ZIP_HASH = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip.sha256"
EXCLUDED_DIRS = {".venv", ".git", "__pycache__", "node_modules", "whitepaper_qa"}
EXCLUDED_FILES = {
    ZIP_PATH.name, ZIP_TMP.name, ZIP_HASH.name, CHECKSUMS.name,
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def project_files(include_catalog: bool = True) -> list[Path]:
    files = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
        folder = Path(base)
        for name in names:
            if name in EXCLUDED_FILES or name.endswith((".pyc", ".pyo")):
                continue
            path = folder / name
            if path == CATALOG and not include_catalog:
                continue
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix().lower())


def count_csv_rows(path: Path) -> int | str:
    try:
        count = 0
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            count = sum(1 for _ in csv.reader(f))
        return max(0, count - 1)
    except Exception as exc:
        return "unavailable:" + type(exc).__name__


def write_catalog() -> list[dict[str, object]]:
    rows = []
    for n, path in enumerate(project_files(include_catalog=False), 1):
        ext = path.suffix.lower() or "[sans extension]"
        rows.append({
            "path": path.relative_to(ROOT).as_posix(),
            "type": ext,
            "bytes": path.stat().st_size,
            "records": count_csv_rows(path) if ext == ".csv" else "",
            "sha256": digest(path),
        })
        if n % 100 == 0:
            print(f"[catalogue final] {n} fichiers hachés", flush=True)
    with CATALOG.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "type", "bytes", "records", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_checksums() -> int:
    files = project_files(include_catalog=True)
    with CHECKSUMS.open("w", encoding="utf-8", newline="\n") as f:
        for path in files:
            f.write(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n")
    return len(files)


def build_zip() -> tuple[int, int]:
    files = project_files(include_catalog=True) + [CHECKSUMS]
    expected = {path.relative_to(ROOT).as_posix() for path in files}
    if not PDF.exists():
        raise FileNotFoundError(PDF)
    with ZipFile(ZIP_TMP, "w", compression=ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for index, path in enumerate(files, 1):
            rel = path.relative_to(ROOT).as_posix()
            compression = ZIP_STORED if path.suffix.lower() in {".pdf", ".png", ".npz"} else ZIP_DEFLATED
            info = ZipInfo.from_file(path, arcname=rel)
            info.compress_type = compression
            with path.open("rb") as source, archive.open(info, "w", force_zip64=True) as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            if index % 100 == 0:
                print(f"[ZIP] {index}/{len(files)} fichiers", flush=True)
    ZIP_TMP.replace(ZIP_PATH)
    with ZipFile(ZIP_PATH, "r") as archive:
        bad = archive.testzip()
        actual = set(archive.namelist())
    if bad:
        raise RuntimeError(f"CRC incorrect dans l’archive : {bad}")
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise RuntimeError(json.dumps({"missing": missing[:10], "extra": extra[:10]}, ensure_ascii=False))
    zip_hash = digest(ZIP_PATH)
    ZIP_HASH.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="ascii")
    return len(actual), ZIP_PATH.stat().st_size


def main():
    if not PDF.exists():
        raise FileNotFoundError(PDF)
    rows = write_catalog()
    checksum_count = write_checksums()
    zip_count, zip_bytes = build_zip()
    print(json.dumps({
        "catalog_entries": len(rows),
        "checksummed_files": checksum_count,
        "zip_entries": zip_count,
        "zip_bytes": zip_bytes,
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": digest(PDF),
        "zip_sha256": digest(ZIP_PATH),
        "zip_sidecar": str(ZIP_HASH),
        "venv_included": any(".venv" in part for path in project_files() for part in path.parts),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
