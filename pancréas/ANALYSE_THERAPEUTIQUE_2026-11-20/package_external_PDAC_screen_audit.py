from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
OUTPUT = PROJECT / "output" / "pdac_pipeline_audit_2026-11-20"
OUTPUT.mkdir(parents=True, exist_ok=True)
PIP_FREEZE = ANALYSIS / "ENVIRONMENT_PIP_FREEZE.txt"
PIP_FREEZE.write_text(
    subprocess.run([sys.executable, "-m", "pip", "freeze"], check=True, capture_output=True, text=True).stdout,
    encoding="utf-8",
)

ZIP_PATH = OUTPUT / "PDAC_EXTERNAL_REPLICATION_SCREEN_AUDIT_2026-11-20.zip"
SOURCES = [
    (ANALYSIS / "candidate_NatureComm2025_PAAD", "candidate_NatureComm2025_PAAD"),
    (ANALYSIS / "JHH_PDAC_pharmacotyping", "candidate_JHH_2024"),
    (ANALYSIS / "SCREENING_SOURCE_MANIFEST_2026-11-20.json", "SCREENING_SOURCE_MANIFEST_2026-11-20.json"),
    (ANALYSIS / "EXTERNAL_REPLICATION_SCREEN_REPORT_2026-11-20.md", "EXTERNAL_REPLICATION_SCREEN_REPORT_2026-11-20.md"),
    (ANALYSIS / "ENVIRONMENT_PIP_FREEZE.txt", "ENVIRONMENT_PIP_FREEZE.txt"),
    (ANALYSIS / "package_external_PDAC_screen_audit.py", "package_external_PDAC_screen_audit.py"),
    (ANALYSIS / ".." / ".." / "UNIVERSAL_LOG_v5.9.4.py", "UNIVERSAL_LOG_v5.9.4.py"),
    (ANALYSIS / ".." / "ANALYSE_THERAPEUTIQUE_2026-11-19" / "results_mouse_level" / "GSE271300_ANALYSIS_REPORT.md", "prior_GSE271300_mouse_level_report.md"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for source, arcbase in SOURCES:
            if source.is_dir():
                for path in sorted(source.rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                        archive.write(path, Path(arcbase) / path.relative_to(source))
            elif source.is_file():
                archive.write(source, arcbase)
            else:
                print(f"MISSING (skipped): {source}")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad = archive.testzip()
        count = len(archive.namelist())
        if bad:
            raise RuntimeError(f"Corrupt member: {bad}")
    hash_value = sha256(ZIP_PATH)
    sidecar = OUTPUT / "PDAC_EXTERNAL_REPLICATION_SCREEN_AUDIT_2026-11-20_SHA256.txt"
    sidecar.write_text(f"{hash_value}  {ZIP_PATH.name}\n", encoding="ascii")
    print(f"zip={ZIP_PATH}")
    print(f"bytes={ZIP_PATH.stat().st_size} members={count} testzip=None")
    print(f"sha256={hash_value}")


if __name__ == "__main__":
    main()
