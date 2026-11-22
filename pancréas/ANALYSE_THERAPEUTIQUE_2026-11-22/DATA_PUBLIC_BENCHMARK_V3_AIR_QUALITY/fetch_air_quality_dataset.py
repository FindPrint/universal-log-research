#!/usr/bin/env python
"""Fetch the UCI Air Quality archive for local research use; do not publish raw data."""
from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
ARCHIVE = SOURCE / "air_quality_uci_source.zip"
CSV = SOURCE / "AirQualityUCI.csv"
MANIFEST = HERE / "source_manifest.json"
URL = "https://archive.ics.uci.edu/static/public/360/air+quality.zip"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        request = urllib.request.Request(URL, headers={"User-Agent": "UNIVERSAL_LOG research audit"})
        with urllib.request.urlopen(request, timeout=60) as response, ARCHIVE.open("wb") as output:
            output.write(response.read())
    with zipfile.ZipFile(ARCHIVE) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith("airqualityuci.csv")]
        if len(members) != 1:
            raise RuntimeError(f"Expected exactly one AirQualityUCI.csv member; found {members!r}")
        CSV.write_bytes(archive.read(members[0]))
    manifest = {
        "status": "fetched",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_page": "https://archive.ics.uci.edu/dataset/360/air%2Bquality",
        "doi": "10.24432/C59K5F",
        "download_url": URL,
        "archive_file": ARCHIVE.name,
        "archive_bytes": ARCHIVE.stat().st_size,
        "archive_sha256": sha256(ARCHIVE),
        "csv_file": CSV.name,
        "csv_bytes": CSV.stat().st_size,
        "csv_sha256": sha256(CSV),
        "fetch_script_sha256": sha256(Path(__file__).resolve()),
        "distribution_policy": "Raw source retained locally only. UCI page states both research-only/noncommercial use and CC BY 4.0; do not redistribute raw data until this wording is clarified.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
