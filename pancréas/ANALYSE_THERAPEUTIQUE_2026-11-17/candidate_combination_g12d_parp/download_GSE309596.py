#!/usr/bin/env python3
"""Download and checksum the 12 public GEO GSE309596 count matrices.

Inputs are the complete GEO sample records saved in source/. Downloads preserve
the submitted matrix, barcode, and feature files. This script does not analyze
cells or treat them as independent experimental replicates.
"""
from __future__ import annotations

import concurrent.futures
import gzip
import hashlib
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
META = SOURCE / "GSE309596_GEO_full_metadata.txt"
OUT = SOURCE / "GSE309596_raw_counts"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_samples() -> list[dict[str, str]]:
    text = META.read_text(encoding="utf-8", errors="replace")
    samples = []
    for block in text.split("^SAMPLE = ")[1:]:
        lines = block.splitlines()
        row = {"gsm": lines[0].strip()}
        for line in lines:
            if line.startswith("!Sample_title = "):
                row["title"] = line.split("=", 1)[1].strip()
            elif line.startswith("!Sample_characteristics_ch1 = "):
                key, _, value = line.split("=", 1)[1].strip().partition(":")
                row[key.strip().casefold().replace(" ", "_")] = value.strip()
            elif line.startswith("!Sample_relation = BioSample:"):
                row["biosample"] = line.rsplit("/", 1)[-1]
            elif line.startswith("!Sample_relation = SRA:"):
                match = re.search(r"SRX\d+", line)
                row["sra"] = match.group(0) if match else line.rsplit("/", 1)[-1]
        row["supplementary_urls"] = [
            line.split("=", 1)[1].strip().replace("ftp://", "https://")
            for line in lines if line.startswith("!Sample_supplementary_file_")
        ]
        samples.append(row)
    if len(samples) != 12:
        raise ValueError(f"Expected 12 sample records, found {len(samples)}")
    return samples


def download_one(url: str) -> dict[str, object]:
    name = url.rsplit("/", 1)[-1]
    destination = OUT / name
    if destination.exists() and destination.stat().st_size:
        try:
            with gzip.open(destination, "rb") as handle:
                handle.read(1)
            return {"file": name, "bytes": destination.stat().st_size,
                    "sha256": sha256(destination), "status": "reused_valid_gzip"}
        except Exception:
            destination.unlink()
    last_error = None
    for attempt in range(5):
        temp = destination.with_suffix(destination.suffix + ".part")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "UNIVERSAL_LOG research audit/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response, temp.open("wb") as output:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    output.write(chunk)
            with gzip.open(temp, "rb") as handle:
                handle.read(1)
            temp.replace(destination)
            return {"file": name, "bytes": destination.stat().st_size,
                    "sha256": sha256(destination), "status": "downloaded"}
        except Exception as exc:  # retry transient GEO 5xx/timeouts
            last_error = repr(exc)
            temp.unlink(missing_ok=True)
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"Could not download {url}: {last_error}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    samples = parse_samples()
    urls = [url for sample in samples for url in sample["supplementary_urls"]]
    if len(urls) != 36:
        raise ValueError(f"Expected 36 matrix/barcode/feature files, found {len(urls)}")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(download_one, url): url for url in urls}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            item = future.result()
            results.append(item)
            print(f"[{index:02d}/36] {item['status']} {item['file']} {item['bytes']:,} bytes", flush=True)
    table = [{k: v for k, v in sample.items() if k != "supplementary_urls"} for sample in samples]
    import csv
    with (OUT / "sample_metadata.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({k for row in table for k in row}))
        writer.writeheader()
        writer.writerows(table)
    manifest = {
        "analysis_id": "GSE309596_public_count_matrices_download_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_series": "GSE309596",
        "source_metadata_file": {"name": META.name, "bytes": META.stat().st_size, "sha256": sha256(META)},
        "source_page": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE309596",
        "unit_note": "Each GEO GSM/BioSample is preserved as one submitted specimen. GEO titles show replicate numbers, but animal identity/independence must be cross-checked against article/source data before inferential replication claims.",
        "n_samples": len(samples), "n_files": len(results),
        "files": sorted(results, key=lambda x: str(x["file"])),
        "total_downloaded_bytes": sum(int(x["bytes"]) for x in results),
    }
    (OUT / "download_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"samples": len(samples), "files": len(results), "bytes": manifest["total_downloaded_bytes"],
                      "manifest": str(OUT / "download_manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
