#!/usr/bin/env python3
"""Append the dated GDSC2 supplement to new copies of the white-paper PDFs."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def append_supplement(
    source_pdf: Path,
    supplement_pdf: Path,
    output_pdf: Path,
    title: str,
) -> tuple[int, int]:
    if not source_pdf.is_file():
        raise FileNotFoundError(f"Source PDF not found: {source_pdf}")
    if not supplement_pdf.is_file():
        raise FileNotFoundError(f"Supplement PDF not found: {supplement_pdf}")
    if output_pdf.exists():
        raise FileExistsError(f"Refusing to overwrite existing PDF: {output_pdf}")
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    with fitz.open(source_pdf) as source, fitz.open(supplement_pdf) as supplement:
        if source.is_encrypted or supplement.is_encrypted:
            raise ValueError("Encrypted source or supplement PDFs are not supported.")
        original_page_count = source.page_count
        if original_page_count == 0 or supplement.page_count == 0:
            raise ValueError("Source and supplement PDFs must contain pages.")
        original_toc = source.get_toc()
        source.insert_pdf(supplement, links=True, annots=True)
        if original_toc:
            source.set_toc(
                original_toc
                + [[1, "GDSC2 supplement - 24 November 2026",
                    original_page_count + 1]]
            )
        metadata = dict(source.metadata or {})
        metadata.update(
            {
                "title": title,
                "subject": (
                    "Original white paper with the dated GDSC2 all-lineage "
                    "supplement appended"
                ),
                "modDate": "D:20261124120000-05'00'",
            }
        )
        source.set_metadata(metadata)
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        source.save(output_pdf, garbage=4, deflate=True, clean=True)
        expected_page_count = original_page_count + supplement.page_count

    with fitz.open(output_pdf) as result:
        if result.page_count != expected_page_count:
            output_pdf.unlink(missing_ok=True)
            raise RuntimeError(
                f"Unexpected page count in {output_pdf}: {result.page_count}"
            )
        if "GDSC2 all-lineage" not in result.metadata.get("subject", ""):
            output_pdf.unlink(missing_ok=True)
            raise RuntimeError(f"Supplement metadata missing in {output_pdf}")
    return original_page_count, expected_page_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integral-pdf", type=Path, required=True)
    parser.add_argument("--pdac-dossier-pdf", type=Path, required=True)
    parser.add_argument("--supplement-pdf", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    outputs = (
        (
            args.integral_pdf,
            args.output_dir
            / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_INTEGRAL_V13_2026-11-24.pdf",
            "UNIVERSAL_LOG livre blanc integral V13 - 24 novembre 2026",
        ),
        (
            args.pdac_dossier_pdf,
            args.output_dir
            / "DOSSIER_SCIENTIFIQUE_PREUVES_ET_PROTOCOLE_PDAC_TLOG_V2_2026-11-24.pdf",
            "Dossier scientifique preuves et protocole PDAC TLog V2 - 24 novembre 2026",
        ),
    )
    existing = [str(output) for _, output, _ in outputs if output.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing output PDF(s): " + ", ".join(existing)
        )

    created: list[Path] = []
    try:
        for source, output, title in outputs:
            old_pages, new_pages = append_supplement(
                source,
                args.supplement_pdf,
                output,
                title,
            )
            created.append(output)
            print(f"{output}: {old_pages} -> {new_pages} pages")
    except Exception:
        for output in created:
            output.unlink(missing_ok=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
