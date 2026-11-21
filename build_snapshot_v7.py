"""Append the V7 update to the archived V6 project ZIP without nesting ZIPs."""

import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21"
BASE_DIR = ROOT / "archive_sources" / "master_whitepaper_v6"
BASE_ZIP = BASE_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V6_2026-11-21.zip"
OUT_DIR = ROOT / "output" / "master_whitepaper_v7"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_ZIP = OUT_DIR / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V7_2026-11-21.zip"
OUT_SHA = OUT_ZIP.with_suffix(OUT_ZIP.suffix + ".sha256")
MANIFEST = OUT_DIR / "PROJECT_SNAPSHOT_V7_OVERLAY_MANIFEST.json"
MANIFEST_ARC = "output/master_whitepaper_v7/PROJECT_SNAPSHOT_V7_OVERLAY_MANIFEST.json"
PUBLICATION_MANIFEST = ROOT / "PUBLICATION_MANIFEST_2026-11-21_AXIS_FLUX.csv"

PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V7_2026-11-21.pdf"
PDF_SHA = PDF.with_suffix(PDF.suffix + ".sha256")
SOURCES = [
    ROOT / "README_V7_CURRENT.md",
    ROOT / "COMPLETE_WHITEPAPER_V7_README.md",
    ROOT / "PUBLICATION_SCOPE_V7.md",
    PUBLICATION_MANIFEST,
    ROOT / "build_patient_axis_flux_appendix_v7.py",
    ROOT / "build_snapshot_v7.py",
    PDF,
    PDF_SHA,
]
SOURCES.extend(p for p in AUDIT_DIR.rglob("*") if p.is_file())

if OUT_ZIP.exists():
    raise FileExistsError(f"Refusing to overwrite existing snapshot: {OUT_ZIP}")
if not BASE_ZIP.is_file():
    raise FileNotFoundError(BASE_ZIP)
if not PDF.is_file() or not PDF_SHA.is_file():
    raise FileNotFoundError("Build and checksum the V7 PDF before the V7 project snapshot")

windows_path = re.compile(rb"(?i)[A-Z]:\\[^\s,;\"']+")


def safe_log_bytes(path: Path) -> bytes | None:
    if path.suffix.lower() != ".log":
        return None
    return windows_path.sub(b"<LOCAL_WINDOWS_PATH>", path.read_bytes())


overlay: dict[str, tuple[Path, bytes | None]] = {}
for path in SOURCES:
    if not path.is_file():
        raise FileNotFoundError(path)
    relative = "README_V7_CURRENT.md" if path == ROOT / "README_V7_CURRENT.md" else path.relative_to(ROOT).as_posix()
    overlay[relative] = (path, safe_log_bytes(path))

for path in AUDIT_DIR.rglob("*"):
    if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
        continue
    relative = path.relative_to(ROOT).as_posix()
    overlay[relative] = (path, safe_log_bytes(path))

with zipfile.ZipFile(BASE_ZIP, "r") as base:
    base_names = set(base.namelist())
collision = base_names & (set(overlay) | {MANIFEST_ARC})
if collision:
    raise RuntimeError(f"V7 overlay path collides with base entries: {sorted(collision)[:12]}")

base_digest = hashlib.sha256()
with BASE_ZIP.open("rb") as stream:
    for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        base_digest.update(chunk)
base_sha = base_digest.hexdigest()
base_sha_file = BASE_ZIP.with_suffix(BASE_ZIP.suffix + ".sha256")
if base_sha_file.is_file():
    expected = base_sha_file.read_text(encoding="ascii").split()[0].lower()
    if base_sha != expected:
        raise RuntimeError(f"V6 base SHA-256 mismatch: {base_sha} != {expected}")

records = []
for relative, (path, replacement_bytes) in sorted(overlay.items()):
    digest = hashlib.sha256()
    if replacement_bytes is None:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        size = path.stat().st_size
    else:
        digest.update(replacement_bytes)
        size = len(replacement_bytes)
    records.append({
        "path": relative,
        "bytes": size,
        "sha256": digest.hexdigest(),
        "sanitized_copy": replacement_bytes is not None,
    })

manifest_data = {
    "snapshot": OUT_ZIP.name,
    "created": "2026-11-21",
    "base_snapshot": BASE_ZIP.name,
    "base_snapshot_sha256": base_sha,
    "overlay_file_count": len(records),
    "overlay_files": records,
    "note": "V7 appends the V7 whitepaper and PDAC control-axis × flux audit to the V6 full snapshot. The ZIP contains no nested ZIP. Local absolute paths are neutralized in distributed console-log copies; original working logs remain unchanged.",
}
MANIFEST.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

shutil.copy2(BASE_ZIP, OUT_ZIP)
with zipfile.ZipFile(OUT_ZIP, "a", allowZip64=True) as destination:
    for relative, (path, replacement_bytes) in sorted(overlay.items()):
        compression = zipfile.ZIP_STORED if path.suffix.lower() in {".pdf", ".png", ".zip"} else zipfile.ZIP_DEFLATED
        if replacement_bytes is None:
            destination.write(path, arcname=relative, compress_type=compression)
        else:
            destination.writestr(relative, replacement_bytes, compress_type=zipfile.ZIP_DEFLATED)
    destination.write(MANIFEST, arcname=MANIFEST_ARC, compress_type=zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(OUT_ZIP, "r") as final_zip:
    bad_member = final_zip.testzip()
    member_count = len(final_zip.namelist())
    nested_zips = [name for name in final_zip.namelist() if name.lower().endswith(".zip")]
if bad_member:
    raise RuntimeError(f"ZIP CRC failure: {bad_member}")
if any(Path(name).name.startswith("UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V") for name in nested_zips):
    raise RuntimeError(f"A prior project ZIP was nested in the V7 archive: {nested_zips}")

final_digest = hashlib.sha256()
with OUT_ZIP.open("rb") as stream:
    for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        final_digest.update(chunk)
final_sha = final_digest.hexdigest()
OUT_SHA.write_text(f"{final_sha}  {OUT_ZIP.name}\n", encoding="ascii")
print(json.dumps({
    "base_sha256": base_sha,
    "overlay_files": len(records),
    "member_count": member_count,
    "nested_zip_count": len(nested_zips),
    "zip_bytes": OUT_ZIP.stat().st_size,
    "zip_sha256": final_sha,
    "crc_test": "passed",
    "zip": str(OUT_ZIP),
}, indent=2))
