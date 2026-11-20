from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "NIHMS2020869_Supplemental_Data_File.docx"
OUT = ROOT / "SUPPLEMENT_STRUCTURE.txt"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def text_of(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.findall(".//w:t", NS)).strip()


def main() -> None:
    with ZipFile(DOCX) as docx:
        xml = ET.fromstring(docx.read("word/document.xml"))
    body = xml.find("w:body", NS)
    output: list[str] = []
    table_number = 0
    for child in list(body or []):
        if child.tag.endswith("}p"):
            value = text_of(child)
            if value:
                output.append(value)
        elif child.tag.endswith("}tbl"):
            table_number += 1
            rows = []
            for row in child.findall("w:tr", NS):
                rows.append([text_of(cell) for cell in row.findall("w:tc", NS)])
            ncols = max((len(row) for row in rows), default=0)
            output.append(f"\n[TABLE {table_number}: rows={len(rows)} max_columns={ncols}]")
            for row in rows:
                output.append("\t".join(row))
    OUT.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"tables={table_number} text_lines={len(output)} output={OUT}")


if __name__ == "__main__":
    main()
