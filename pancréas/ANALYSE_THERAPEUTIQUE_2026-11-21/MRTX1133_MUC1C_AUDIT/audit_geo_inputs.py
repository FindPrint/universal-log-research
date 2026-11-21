#!/usr/bin/env python3
"""Download and inventory GEO records for the MRTX1133/MUC1-C data-fit audit.

Raw GEO source files are kept under this audit's ignored ``source`` directory.
The script emits only source metadata, sample inventories, file hashes, and
matrix dimensions. It does not reshape observations or run UNIVERSAL_LOG.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import tarfile
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
SOURCE = HERE / "source"
SOURCE.mkdir(parents=True, exist_ok=True)
USER_AGENT = "UNIVERSAL_LOG reproducibility audit/1.0"

SERIES = {
    "GSE269985": "GSE269nnn",
    "GSE269313": "GSE269nnn",
    "GSE293756": "GSE293nnn",
}


def download(url: str, destination: Path) -> dict:
    if not destination.exists():
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=90) as response:
            destination.write_bytes(response.read())
    payload = destination.read_bytes()
    return {
        "url": url,
        "local_file": str(destination.relative_to(HERE)).replace("\\", "/"),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def soft_url(accession: str) -> str:
    bucket = SERIES[accession]
    return (
        f"https://ftp.ncbi.nlm.nih.gov/geo/series/{bucket}/{accession}/"
        f"soft/{accession}_family.soft.gz"
    )


def parse_soft(path: Path) -> tuple[dict, list[dict]]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    series: dict[str, list[str]] = {}
    samples: list[dict] = []
    current: dict | None = None
    for line in lines:
        if line.startswith("^SAMPLE = "):
            current = {"geo_accession": line.split("=", 1)[1].strip()}
            samples.append(current)
            continue
        if line.startswith("^SERIES = "):
            current = None
            continue
        if not line.startswith("!") or " = " not in line:
            continue
        key, value = line[1:].split(" = ", 1)
        value = value.strip().strip('"')
        if current is None:
            series.setdefault(key, []).append(value)
        elif key.startswith("Sample_"):
            current.setdefault(key, []).append(value)
    return series, samples


def one(sample: dict, key: str) -> str:
    return " | ".join(sample.get(key, []))


def sample_inventory(accession: str, samples: list[dict]) -> list[dict]:
    rows = []
    for sample in samples:
        chars = one(sample, "Sample_characteristics_ch1")
        title = one(sample, "Sample_title")
        treatment = "; ".join(
            value.strip() for value in re.findall(r"treatment:\s*([^|]+)", chars, flags=re.I)
        )
        time_days = "; ".join(
            value.strip() for value in re.findall(r"time point_\(days\):\s*([^|]+)", chars, flags=re.I)
        )
        cell_line = "; ".join(
            value.strip() for value in re.findall(r"cell line:\s*([^|]+)", chars, flags=re.I)
        )
        model = title.split(",")[0].split("/")[0].strip()
        state = ""
        if re.search(r"MRTX1133 resistant", title, flags=re.I):
            state = "MRTX1133-resistant model/state"
        elif re.search(r"early MRTX1133", title, flags=re.I):
            state = "early MRTX1133 exposure"
        elif re.search(r"early Vehicle", title, flags=re.I):
            state = "early vehicle"
        elif treatment and treatment.lower() not in {"none", "not applicable"}:
            state = treatment.strip()
        elif re.search(r"parental", title, flags=re.I):
            state = "parental model/state"
        rows.append({
            "series": accession,
            "geo_accession": sample.get("geo_accession", ""),
            "title": title,
            "sample_type": one(sample, "Sample_type"),
            "model_or_cell_line": (cell_line or model).strip(),
            "treatment": treatment,
            "resistance_or_condition_state": state,
            "time_days": time_days,
            "characteristics": chars,
        })
    return rows


def csv_gzip_shape(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = sum(1 for row in reader if row)
    return {"rows_excluding_header": rows, "columns_in_header": len(header), "header": header}


def first_tar_csv_shape(tar_path: Path, member_name: str) -> dict:
    with tarfile.open(tar_path, "r:") as archive:
        member = archive.extractfile(member_name)
        if member is None:
            raise FileNotFoundError(member_name)
        with gzip.open(member, "rt", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            rows = sum(1 for row in reader if row)
    return {"member": member_name, "rows_excluding_header": rows, "columns_in_header": len(header), "header": header}


def main() -> None:
    downloaded: list[dict] = []
    inventories: dict[str, list[dict]] = {}
    series_records: dict[str, dict] = {}

    for accession in SERIES:
        local = SOURCE / f"{accession}_family.soft.gz"
        downloaded.append(download(soft_url(accession), local))
        series, samples = parse_soft(local)
        inventories[accession] = sample_inventory(accession, samples)
        series_records[accession] = {
            "title": (series.get("Series_title") or [""])[0],
            "summary": (series.get("Series_summary") or [""])[0],
            "sample_count": len(samples),
            "sample_types": dict(Counter(row["sample_type"] for row in inventories[accession])),
            "sample_treatments": dict(Counter(row["treatment"] or "unspecified" for row in inventories[accession])),
            "sample_states": dict(Counter(row["resistance_or_condition_state"] or "unspecified" for row in inventories[accession])),
            "sample_days": dict(Counter(row["time_days"] or "unspecified" for row in inventories[accession])),
            "supplementary_files": series.get("Series_supplementary_file", []),
        }

    raw_url = (
        "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE269nnn/GSE269985/"
        "suppl/GSE269985_RAW.tar"
    )
    raw_tar = SOURCE / "GSE269985_RAW.tar"
    downloaded.append(download(raw_url, raw_tar))
    with tarfile.open(raw_tar, "r:") as archive:
        tar_members = [
            {"name": member.name, "bytes": member.size}
            for member in archive.getmembers()
            if member.isfile()
        ]
    first_count_member = next((item["name"] for item in tar_members if item["name"].endswith("_counts.csv.gz")), None)
    if first_count_member is None:
        raise ValueError("No per-sample counts CSV was found in the GSE269985 raw archive")
    raw_sample_shape = first_tar_csv_shape(raw_tar, first_count_member)

    expression_files = {}
    for label, filename in [
        ("gene_counts", "GSE293756_STAR_Gene_Counts.csv.gz"),
        ("gene_tpm", "GSE293756_STAR_Gene_TPM.csv.gz"),
    ]:
        url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE293nnn/GSE293756/suppl/{filename}"
        local = SOURCE / filename
        downloaded.append(download(url, local))
        expression_files[label] = csv_gzip_shape(local)

    inventory_path = HERE / "GEO_SAMPLE_INVENTORY.csv"
    columns = ["series", "geo_accession", "title", "sample_type", "model_or_cell_line", "treatment", "resistance_or_condition_state", "time_days", "characteristics"]
    with inventory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for accession in SERIES:
            writer.writerows(inventories[accession])

    result = {
        "audit": "MRTX1133 resistance and MUC1-C GEO data-fit inventory",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "script": Path(__file__).name,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": __import__("platform").python_version(),
        "series": series_records,
        "GSE269985_raw_tar_members": tar_members,
        "GSE269985_first_per_sample_count_file_shape": raw_sample_shape,
        "GSE293756_expression_files": expression_files,
        "downloads": downloaded,
        "sample_inventory_csv": inventory_path.name,
        "sample_inventory_csv_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        "pipeline_gate_from_existing_project_audit": {
            "pipeline_path": "pancréas/universal_v6.0.0_cohen - Copie.py.txt",
            "pipeline_sha256": hashlib.sha256((PROJECT_ROOT / "pancréas" / "universal_v6.0.0_cohen - Copie.py.txt").read_bytes()).hexdigest(),
            "version": "v6.0.0 Cohen-D",
            "minimum_valid_points_fast": 50,
            "interpretation": "Eligibility gate only; it does not establish whether the statistical method is valid at other sample sizes.",
        },
        "analysis_decision": {
            "full_pipeline_run": False,
            "reason": "The candidate RNA-seq records have 6, 17, and 30 biological samples, below the current minimum of 50. The candidate designs are replicated groups or cross-sectional animals, not a single ordered treatment-response trajectory. No pseudoreplication, synthetic padding, or arbitrary sample ordering is applied.",
            "therapeutic_endpoint_in_public_GSE293756_matrix": False,
            "GSE293756_design_interpretation": "One acquired-resistant AsPC-1/MR line with doxycycline-inducible MUC1 shRNA; three DOX+ and three DOX- RNA-seq samples. This is a knockdown expression contrast, not an anti-MUC1-C ADC response matrix or MRTX1133-versus-combination drug-response trajectory.",
        },
    }
    output = HERE / "GEO_DATA_FIT_MANIFEST.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest": str(output),
        "sample_inventory": str(inventory_path),
        "series": {
            accession: {
                "n": record["sample_count"],
                "treatments": record["sample_treatments"],
                "states": record["sample_states"],
                "days": record["sample_days"],
            }
            for accession, record in series_records.items()
        },
        "raw_tar_members": len(tar_members),
        "GSE269985_single_sample_counts_shape": {
            "rows": raw_sample_shape["rows_excluding_header"],
            "columns": raw_sample_shape["columns_in_header"],
        },
        "GSE293756_expression_shape": {
            key: (value["rows_excluding_header"], value["columns_in_header"])
            for key, value in expression_files.items()
        },
        "pipeline_run": "not run: below N gate and no valid single ordered trajectory",
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
