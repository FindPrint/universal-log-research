#!/usr/bin/env python
"""Bundle the exact Ising v6 audit, source theory, inputs and raw results."""
from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
FINITE = PROJECT / "ising_classique_test" / "finite_size"
PIPELINE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
ARCHIVE = PROJECT / "pipeline_v6_ising_audit_bundle.zip"
INCLUDES = [
    PROJECT / "TLog.txt",
    PROJECT / "LICENSE",
    PROJECT / "LICENSE-CC-BY-4.0.txt",
    PROJECT / "LICENSE_STATUS.md",
    PROJECT / "LICENSES.md",
    PROJECT / "pancréas" / "ARCHIVE_FINAL.zip",
    FINITE / "finite_size_ising.py",
    FINITE / "finite_size_results.csv",
    FINITE / "finite_size_peaks.csv",
    FINITE / "binder_crossings.csv",
    PIPELINE,
    HERE,
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_files():
    files = []
    for entry in INCLUDES:
        if not entry.exists():
            continue
        if entry.is_file():
            files.append(entry)
        else:
            for path in entry.rglob("*"):
                if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                    continue
                files.append(path)
    # Stable order and unique archive members.
    return sorted({path.resolve() for path in files}, key=lambda p: p.relative_to(PROJECT).as_posix().lower())


def main():
    files = selected_files()
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "archive_path": str(ARCHIVE.resolve()),
        "contents": [{"path": path.relative_to(PROJECT).as_posix(),
                      "bytes": path.stat().st_size, "sha256": sha256(path)} for path in files],
    }
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as archive:
        for path in files:
            archive.write(path, arcname=path.relative_to(PROJECT).as_posix())
        archive.writestr("AUDIT_BUNDLE_MANIFEST.json",
                         json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Archive : {ARCHIVE}")
    print(f"Fichiers : {len(files)}")
    print(f"Taille : {ARCHIVE.stat().st_size:,} octets")


if __name__ == "__main__":
    main()
