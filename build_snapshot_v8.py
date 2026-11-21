"""Append the V8 longitudinal ctDNA access audit to the V7 full project ZIP."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21"
ARCHIVED_V7_DIR = ROOT / "archive_sources" / "master_whitepaper_v7"
ACTIVE_V7_DIR = ROOT / "output" / "master_whitepaper_v7"
BASE_DIR = ARCHIVED_V7_DIR if ARCHIVED_V7_DIR.is_dir() else ACTIVE_V7_DIR
BASE_ZIP = BASE_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V7_2026-11-21.zip"
OUT_DIR = ROOT / "output" / "master_whitepaper_v8"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_ZIP = OUT_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V8_2026-11-21.zip"
OUT_SHA = OUT_ZIP.with_suffix(OUT_ZIP.suffix + ".sha256")
MANIFEST = OUT_DIR / "PROJECT_SNAPSHOT_V8_OVERLAY_MANIFEST.json"
MANIFEST_ARC = "output/master_whitepaper_v8/PROJECT_SNAPSHOT_V8_OVERLAY_MANIFEST.json"
PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V8_2026-11-21.pdf"
PDF_SHA = PDF.with_suffix(PDF.suffix + ".sha256")
PUBLICATION_MANIFEST = ROOT / "PUBLICATION_MANIFEST_2026-11-21_LONGITUDINAL.csv"

paths = [
    ROOT / "README_V8_CURRENT.md",
    ROOT / "COMPLETE_WHITEPAPER_V8_README.md",
    ROOT / "PUBLICATION_SCOPE_V8.md",
    PUBLICATION_MANIFEST,
    ROOT / "build_longitudinal_ctdna_appendix_v8.py",
    ROOT / "build_snapshot_v8.py",
    PDF,
    PDF_SHA,
]
paths.extend(p for p in DATA_DIR.rglob("*") if p.is_file() and p.suffix.lower() != ".pyc" and "__pycache__" not in p.parts)

if OUT_ZIP.exists():
    raise FileExistsError(f"Refusing to overwrite {OUT_ZIP}")
if not BASE_ZIP.is_file() or not PDF.is_file() or not PDF_SHA.is_file():
    raise FileNotFoundError("V7 base ZIP and V8 PDF with checksum are required")

overlay: dict[str, Path] = {}
for path in paths:
    if not path.is_file():
        raise FileNotFoundError(path)
    overlay[path.relative_to(ROOT).as_posix()] = path

with zipfile.ZipFile(BASE_ZIP, "r") as base:
    base_names = set(base.namelist())
collision = base_names & (set(overlay) | {MANIFEST_ARC})
if collision:
    raise RuntimeError(f"V8 overlay collision with V7 base: {sorted(collision)[:20]}")

base_digest = hashlib.sha256()
with BASE_ZIP.open("rb") as stream:
    for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        base_digest.update(chunk)
base_sha = base_digest.hexdigest()
base_sidecar = BASE_ZIP.with_suffix(BASE_ZIP.suffix + ".sha256")
expected_base_sha = base_sidecar.read_text(encoding="ascii").split()[0].lower()
if base_sha != expected_base_sha:
    raise RuntimeError(f"V7 base ZIP hash mismatch: {base_sha} != {expected_base_sha}")

records = []
for relative, path in sorted(overlay.items()):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    records.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest.hexdigest()})

manifest_data = {
    "snapshot": OUT_ZIP.name,
    "created": "2026-11-21",
    "base_snapshot": BASE_ZIP.name,
    "base_snapshot_sha256": base_sha,
    "overlay_file_count": len(records),
    "overlay_files": records,
    "note": "V8 extends the V7 snapshot with the longitudinal ctDNA data-access audit, a pre-analysis protocol, an unsent data request draft, and the V8 master PDF. No prior project snapshot ZIP is nested.",
}
MANIFEST.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

shutil.copy2(BASE_ZIP, OUT_ZIP)
with zipfile.ZipFile(OUT_ZIP, "a", allowZip64=True) as destination:
    for relative, path in sorted(overlay.items()):
        compression = zipfile.ZIP_STORED if path.suffix.lower() in {".pdf", ".png", ".zip"} else zipfile.ZIP_DEFLATED
        destination.write(path, arcname=relative, compress_type=compression)
    destination.write(MANIFEST, arcname=MANIFEST_ARC, compress_type=zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(OUT_ZIP, "r") as final_zip:
    bad_member = final_zip.testzip()
    final_names = final_zip.namelist()
    member_count = len(final_names)
    nested_snapshots = [
        name for name in final_names
        if Path(name).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V")
    ]
if bad_member:
    raise RuntimeError(f"V8 ZIP CRC failure: {bad_member}")
if nested_snapshots:
    raise RuntimeError(f"Nested project snapshots found: {nested_snapshots}")

out_digest = hashlib.sha256()
with OUT_ZIP.open("rb") as stream:
    for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        out_digest.update(chunk)
out_sha = out_digest.hexdigest()
OUT_SHA.write_text(f"{out_sha}  {OUT_ZIP.name}\n", encoding="ascii")
print(json.dumps({
    "base_sha256": base_sha,
    "overlay_files": len(records),
    "members": member_count,
    "nested_project_snapshots": len(nested_snapshots),
    "crc_test": "passed",
    "zip_bytes": OUT_ZIP.stat().st_size,
    "zip_sha256": out_sha,
    "zip": str(OUT_ZIP),
}, indent=2, ensure_ascii=False))
