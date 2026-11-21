#!/usr/bin/env python3
"""Download and inventory the public supplementary files for the 46-PDO PDAC study.

The downloaded workbooks remain under source/ (excluded by the project .gitignore).
This script records their URLs, byte counts, SHA-256 digests, workbook sheets,
dimensions, and header previews so the source data can be reacquired and audited.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from openpyxl import load_workbook


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
FILES = {
    "supplementary_data_10": (
        "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-025-57520-3/"
        "MediaObjects/41467_2025_57520_MOESM13_ESM.xlsx",
        SOURCE / "41467_2025_57520_MOESM13_ESM.xlsx",
    ),
    "source_data": (
        "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-025-57520-3/"
        "MediaObjects/41467_2025_57520_MOESM17_ESM.xlsx",
        SOURCE / "41467_2025_57520_MOESM17_ESM.xlsx",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        return
    request = Request(url, headers={"User-Agent": "UNIVERSAL_LOG research audit/1.0"})
    with urlopen(request, timeout=90) as response, path.open("wb") as output:
        output.write(response.read())


def inventory_workbook(path: Path) -> dict:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheets = []
    for sheet in workbook.worksheets:
        sheets.append(
            {
                "name": sheet.title,
                "max_row": sheet.max_row,
                "max_column": sheet.max_column,
            }
        )
    workbook.close()
    return {
        "path": str(path.relative_to(HERE)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "sheets": sheets,
    }


def main() -> int:
    records = {}
    for label, (url, path) in FILES.items():
        download(url, path)
        records[label] = {"url": url, **inventory_workbook(path)}
    result = {
        "article": "Yin et al., Nature Communications 16, 2214 (2025)",
        "doi": "10.1038/s41467-025-57520-3",
        "source_files": records,
        "note": (
            "Inventory only; no biological effect or pipeline result is calculated. "
            "The paper states 46 PDOs, 63 compounds, >7000 organoid-drug measurements, "
            "duplicate wells, two independent experiments, and seven concentrations."
        ),
    }
    out = HERE / "PDO_SOURCE_WORKBOOK_INVENTORY.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
