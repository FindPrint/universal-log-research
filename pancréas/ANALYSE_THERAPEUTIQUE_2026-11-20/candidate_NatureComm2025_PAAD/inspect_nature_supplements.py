from __future__ import annotations

import json
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
FILES = [
    ROOT / "NatureComm2025_Supplementary_Data10.xlsx",
    ROOT / "NatureComm2025_SourceData.xlsx",
]


def main() -> None:
    report = {}
    for path in FILES:
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheets = []
        for sheet in workbook.worksheets:
            rows = []
            for row in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 1, 8), values_only=True):
                rows.append([cell for cell in row[:16]])
            sheets.append({
                "name": sheet.title,
                "max_row": sheet.max_row,
                "max_column": sheet.max_column,
                "preview_first_rows": rows,
            })
        report[path.name] = {"bytes": path.stat().st_size, "sheets": sheets}
    out = ROOT / "NATURE_SUPPLEMENT_STRUCTURE.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    for filename, details in report.items():
        print(filename, "bytes=", details["bytes"])
        for sheet in details["sheets"]:
            print(" ", sheet["name"], "rows=", sheet["max_row"], "columns=", sheet["max_column"])
            for row in sheet["preview_first_rows"][:4]:
                print("   ", row)
    print("report=", out)


if __name__ == "__main__":
    main()
