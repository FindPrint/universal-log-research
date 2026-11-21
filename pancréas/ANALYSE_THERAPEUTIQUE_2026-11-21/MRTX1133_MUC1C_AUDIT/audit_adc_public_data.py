#!/usr/bin/env python3
"""Inventory public supplement metadata for the PDAC anti-MUC1-C ADC study.

This script queries Figshare metadata only. It does not download article figures,
supplementary documents, or experimental response data, and it does not run the
UNIVERSAL_LOG pipeline.
"""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PIPELINE = ROOT / "pancréas" / "universal_v6.0.0_cohen - Copie.py.txt"
FIGSHARE_RESOURCE_DOI = "10.1158/1078-0432.CCR-25-2333"
FIGSHARE_API = "https://api.figshare.com/v2"
USER_AGENT = "UNIVERSAL_LOG_PDAD_source_audit/1.0"


def fetch_json(url: str) -> tuple[object, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=40) as response:
        body = response.read()
    return json.loads(body), body


def main() -> None:
    doi_query = urllib.parse.quote(FIGSHARE_RESOURCE_DOI, safe="")
    search_url = f"{FIGSHARE_API}/articles?resource_doi={doi_query}"
    search_result, search_body = fetch_json(search_url)
    if not isinstance(search_result, list):
        raise RuntimeError("Figshare API returned an unexpected article search result.")

    records: list[dict[str, object]] = []
    api_hashes: list[dict[str, str]] = [
        {"url": search_url, "response_sha256": hashlib.sha256(search_body).hexdigest()}
    ]
    for item in search_result:
        detail_url = str(item["url"])
        detail, detail_body = fetch_json(detail_url)
        api_hashes.append(
            {"url": detail_url, "response_sha256": hashlib.sha256(detail_body).hexdigest()}
        )
        license_info = detail.get("license") or {}
        for file_info in detail.get("files", []):
            records.append(
                {
                    "figshare_id": detail.get("id"),
                    "title": detail.get("title"),
                    "doi": detail.get("doi"),
                    "published_date": detail.get("published_date"),
                    "public_record_url": detail.get("url_public_html"),
                    "license_name": license_info.get("name"),
                    "license_url": license_info.get("url"),
                    "file_name": file_info.get("name"),
                    "file_bytes": file_info.get("size"),
                    "mime_type": file_info.get("mimetype"),
                    "provider_md5": file_info.get("computed_md5"),
                    "download_url": file_info.get("download_url"),
                }
            )

    expected_titles = {
        *(f"Figure S{i} from" for i in range(1, 9)),
        "Supplemental Table S1 from",
        "Supplementary Data1 from",
    }
    found_titles = [str(item.get("title", "")) for item in search_result]
    file_extensions = sorted(
        {Path(str(row["file_name"])).suffix.lower() for row in records}
    )
    if len(search_result) != 10 or len(records) != 10:
        raise RuntimeError(
            f"Expected 10 public Figshare records/files, found {len(search_result)} records "
            f"and {len(records)} files. Review the source before drawing a conclusion."
        )
    if file_extensions != [".docx"]:
        raise RuntimeError(
            f"Figshare file types changed ({file_extensions}); review for a new data file."
        )
    if not all(any(title.startswith(expected) for title in found_titles) for expected in expected_titles):
        raise RuntimeError("The expected figure/table/supplement inventory has changed.")

    pipeline_sha = hashlib.sha256(PIPELINE.read_bytes()).hexdigest()
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "audit_scope": "Public source-availability audit only; no experimental response values downloaded or analyzed.",
        "primary_study": {
            "title": "Targeting KRAS Inhibitor-Resistant Pancreatic Cancer with an MUC1-C Antibody-Drug Conjugate",
            "doi": FIGSHARE_RESOURCE_DOI,
            "article_url": "https://aacrjournals.org/clincancerres/article/31/24/5246/770511/Targeting-KRAS-Inhibitor-Resistant-Pancreatic",
            "figshare_search_url": search_url,
            "figshare_record_count": len(search_result),
            "supplement_file_count": len(records),
            "supplement_file_extensions": file_extensions,
            "figshare_inventory_csv": "ADC_FIGSHARE_SUPPLEMENT_INVENTORY.csv",
            "data_availability_statement": "The article states that additional raw data are available from the corresponding author upon reasonable request.",
            "response_assay_details_reported_in_article": {
                "cell_line_viability": "alamarBlue endpoint after 6 days; figure captions report three determinations",
                "organoid_viability": "CellTiter-Glo 3D endpoint after 6 days; Figure S8 reports five determinations",
                "combination_endpoint": "M1C ADC plus MRTX1133; Bliss combination indices are reported",
                "xenograft_endpoint": "longitudinal tumor volume; figures report group summaries, with cohorts of 6-7 mice per arm in cited models",
                "tumor_measurement_schedule": "Methods report tumor dimensions every 3-4 days",
            },
        },
        "related_sources": [
            {
                "title": "Development of novel MUC1-C targeting antibody-drug conjugate for pancreatic cancer treatment",
                "doi": "10.1200/JCO.2024.42.16_suppl.e15025",
                "url": "https://ascopubs.org/doi/10.1200/JCO.2024.42.16_suppl.e15025",
                "note": "Conference abstract reports 3D1-MMAE/7B8-MMAE and an HPAF-II xenograft; no per-animal response matrix was found in the abstract record.",
            },
            {
                "title": "Therapeutic effect of a MUC1-specific monoclonal antibody-drug conjugates against pancreatic cancer model",
                "doi": "10.1186/s12935-022-02839-w",
                "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9793597/",
                "note": "HzMUC1-MMAE targets a different MUC1 epitope from the 3D1 anti-MUC1-C agent; the paper says study data are available from the corresponding author upon reasonable request.",
            },
            {
                "title": "GSE181961 and GSE293756",
                "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE181961; https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE293756",
                "note": "RNA-expression series; they do not contain ADC response measurements.",
            },
        ],
        "pipeline_fit": {
            "pipeline_path": "pancréas/universal_v6.0.0_cohen - Copie.py.txt",
            "pipeline_sha256": pipeline_sha,
            "minimum_stream_length": 50,
            "full_pipeline_run": False,
            "reason": "Public supplements provide documents/figures, not per-well or per-animal numeric response tables. The original article directs readers to request additional raw data. No ordered stream with 50 documented values can be assembled without those measurements; repeated tumor measurements cannot be pooled across animals as independent rows.",
        },
        "retrieval": {
            "method": "HTTP GET to public Figshare v2 metadata API",
            "downloaded_supplement_files": False,
            "downloaded_raw_experimental_data": False,
            "api_response_sha256": api_hashes,
        },
        "figshare_records": records,
    }

    csv_path = HERE / "ADC_FIGSHARE_SUPPLEMENT_INVENTORY.csv"
    fieldnames = list(records[0]) if records else []
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    json_path = HERE / "ADC_SOURCE_DISCOVERY_MANIFEST.json"
    json_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "figshare_records": len(search_result),
                "files": len(records),
                "file_extensions": file_extensions,
                "raw_response_values_downloaded": False,
                "pipeline_full_run": False,
                "csv": str(csv_path),
                "manifest": str(json_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
