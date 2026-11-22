#!/usr/bin/env python
"""Fetch the CC BY 4.0 UCI Bike Sharing source and record its provenance."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
EXPECTED_FILES = {"Readme.txt", "day.csv", "hour.csv"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    response = requests.get(URL, timeout=120)
    response.raise_for_status()
    archive_bytes = response.content
    archive_path = SOURCE / "uci_bike_sharing_dataset.zip"
    archive_path.write_bytes(archive_bytes)
    extracted: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = {Path(item.filename).name for item in archive.infolist() if not item.is_dir()}
        if not EXPECTED_FILES.issubset(names):
            raise RuntimeError(f"Expected {sorted(EXPECTED_FILES)}; received {sorted(names)}")
        for info in archive.infolist():
            name = Path(info.filename).name
            if name not in EXPECTED_FILES:
                continue
            data = archive.read(info)
            (SOURCE / name).write_bytes(data)
            extracted[name] = {"bytes": len(data), "sha256": sha256(data), "zip_crc32": f"{info.CRC:08x}"}
    manifest = {
        "dataset": "Bike Sharing Dataset (hourly and daily)",
        "creator": "Hadi Fanaee-T",
        "doi": "10.24432/C5W894",
        "source_url": URL,
        "source_page": "https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "archive": {"file": archive_path.name, "bytes": len(archive_bytes), "sha256": sha256(archive_bytes)},
        "extracted_files": extracted,
        "attribution": "Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5W894",
    }
    (HERE / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
