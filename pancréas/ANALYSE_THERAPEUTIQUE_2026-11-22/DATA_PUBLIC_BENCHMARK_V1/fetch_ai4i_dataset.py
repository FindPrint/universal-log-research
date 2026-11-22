#!/usr/bin/env python
"""Fetch the public AI4I 2020 benchmark, preferring its Kaggle mirror."""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
RAW = HERE / "source"
RAW.mkdir(parents=True, exist_ok=True)
DEST_CSV = RAW / "ai4i2020.csv"
MANIFEST = HERE / "dataset_manifest.json"
SOURCES = [
    {
        "name": "Kaggle mirror by original dataset author",
        "url": "https://www.kaggle.com/api/v1/datasets/download/stephanmatzka/predictive-maintenance-dataset-ai4i-2020",
        "attribution": "Stephan Matzka, Predictive Maintenance Dataset (AI4I 2020), Kaggle; original dataset citation below.",
    },
    {
        "name": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/static/public/601/ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip",
        "attribution": "AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository. DOI: 10.24432/C5HS5C.",
    },
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


errors = []
selected = None
csv_bytes = None
selected_csv_hash = None
for source in SOURCES:
    request = urllib.request.Request(source["url"], headers={"User-Agent": "UNIVERSAL_LOG-reproducible-benchmark/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "")
        if not zipfile.is_zipfile(__import__("io").BytesIO(payload)):
            raise ValueError(f"Response was not a ZIP archive (Content-Type: {content_type}).")
        with zipfile.ZipFile(__import__("io").BytesIO(payload)) as archive:
            candidates = [name for name in archive.namelist() if Path(name).name.lower() == "ai4i2020.csv"]
            if not candidates:
                raise ValueError("Archive did not contain ai4i2020.csv.")
            csv_bytes = archive.read(candidates[0])
        selected = {**source, "http_content_type": content_type, "archive_sha256": sha256(payload)}
        selected_csv_hash = sha256(csv_bytes)
        break
    except Exception as exc:  # log a source fallback without exposing credentials
        errors.append({"source": source["name"], "error_type": type(exc).__name__, "message": str(exc)[:300]})

if selected is None or csv_bytes is None:
    raise RuntimeError(f"Could not obtain the public dataset from either source: {errors}")

cross_source_checks = []
for source in SOURCES:
    if source["url"] == selected["url"]:
        continue
    request = urllib.request.Request(source["url"], headers={"User-Agent": "UNIVERSAL_LOG-reproducible-benchmark/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "")
        with zipfile.ZipFile(__import__("io").BytesIO(payload)) as archive:
            candidates = [name for name in archive.namelist() if Path(name).name.lower() == "ai4i2020.csv"]
            if not candidates:
                raise ValueError("Archive did not contain ai4i2020.csv.")
            counterpart = archive.read(candidates[0])
        cross_source_checks.append({
            "source": source["name"], "archive_sha256": sha256(payload),
            "csv_sha256": sha256(counterpart), "csv_byte_identical_to_selected": sha256(counterpart) == selected_csv_hash,
            "http_content_type": content_type,
        })
    except Exception as exc:
        cross_source_checks.append({"source": source["name"], "error_type": type(exc).__name__, "message": str(exc)[:300]})

DEST_CSV.write_bytes(csv_bytes)
frame = pd.read_csv(DEST_CSV)
if len(frame) != 10000 or len(frame.columns) != 14:
    raise ValueError(f"Unexpected dataset dimensions: {frame.shape}; expected 10000 x 14.")
manifest = {
    "status": "downloaded_and_shape_checked",
    "retrieved_utc": datetime.now(timezone.utc).isoformat(),
    "selected_source": selected,
    "fallback_attempts": errors,
    "cross_source_identity_checks": cross_source_checks,
    "dataset_citation": "AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C.",
    "license": "CC BY 4.0, as stated by UCI; attribution required.",
    "dataset_type": "synthetic data intended to reflect predictive-maintenance data; not a real plant cohort",
    "rows": len(frame),
    "columns": list(frame.columns),
    "numeric_columns": frame.select_dtypes(include="number").columns.tolist(),
    "machine_failure_count": int(pd.to_numeric(frame["Machine failure"], errors="coerce").sum()),
    "csv_size_bytes": len(csv_bytes),
    "csv_sha256": sha256(csv_bytes),
    "raw_dataset_path": "source/ai4i2020.csv",
}
MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: manifest[k] for k in ["status", "selected_source", "rows", "columns", "numeric_columns", "machine_failure_count", "csv_size_bytes", "csv_sha256"]}, indent=2, ensure_ascii=False))
