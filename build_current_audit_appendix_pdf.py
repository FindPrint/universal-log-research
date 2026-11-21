#!/usr/bin/env python3
"""Render the latest short-curve/PDAC audit Markdown as a readable PDF appendix."""
from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "AUDIT_RECOMMANDATIONS_PETITES_COHORTES" / "ADDENDUM_PILOTE_COURBES_COURTES_2026-11-21_FR.md"
OUT = ROOT / "output" / "master_whitepaper_v5" / "appendices" / "AUDIT_COURBES_COURTES_ET_KCNN4_2026-11-21.pdf"
FONT_DIR = ROOT / ".venv" / "Lib" / "site-packages" / "matplotlib" / "mpl-data" / "fonts" / "ttf"


def register_fonts() -> None:
    regular = FONT_DIR / "DejaVuSans.ttf"
    bold = FONT_DIR / "DejaVuSans-Bold.ttf"
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("DV", str(regular)))
        pdfmetrics.registerFont(TTFont("DV-Bold", str(bold)))
        pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-Bold", italic="DV", boldItalic="DV-Bold")


def inline_markup(text: str) -> str:
    text = text.replace("–", "-").replace("—", "-").replace("‑", "-").replace("−", "-")
    placeholders: list[str] = []

    def save(fragment: str) -> str:
        key = f"@@H{len(placeholders)}@@"
        placeholders.append(fragment)
        return key

    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", lambda m: save(f'<link href="{html.escape(m.group(2), quote=True)}" color="#167D88">{html.escape(m.group(1))}</link>'), text)
    text = re.sub(r"`([^`]+)`", lambda m: save(f'<font name="Courier">{html.escape(m.group(1))}</font>'), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text))
    # Reapply placeholders after escaping; saved fragments contain controlled ReportLab markup.
    for index, fragment in enumerate(placeholders):
        text = text.replace(f"@@H{index}@@", fragment)
    return text


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def main() -> None:
    if not REPORT.is_file():
        raise FileNotFoundError(REPORT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    register_fonts()
    font, font_bold = ("DV", "DV-Bold") if "DV" in pdfmetrics.getRegisteredFontNames() else ("Helvetica", "Helvetica-Bold")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName=font_bold, fontSize=22, leading=27, textColor=colors.HexColor("#12233F"), alignment=TA_CENTER, spaceAfter=15))
    styles.add(ParagraphStyle(name="AuditH2", parent=styles["Heading2"], fontName=font_bold, fontSize=15, leading=19, textColor=colors.HexColor("#167D88"), spaceBefore=12, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle(name="AuditH3", parent=styles["Heading3"], fontName=font_bold, fontSize=11, leading=14, textColor=colors.HexColor("#12233F"), spaceBefore=9, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="AuditBody", parent=styles["BodyText"], fontName=font, fontSize=8.6, leading=12.2, textColor=colors.HexColor("#1F2937"), spaceAfter=6))
    styles.add(ParagraphStyle(name="AuditBullet", parent=styles["BodyText"], fontName=font, fontSize=8.5, leading=12, leftIndent=12, firstLineIndent=-7, spaceAfter=3))
    styles.add(ParagraphStyle(name="AuditSmall", parent=styles["BodyText"], fontName=font, fontSize=7.2, leading=9, spaceAfter=2))

    story = []
    lines = REPORT.read_text(encoding="utf-8").splitlines()
    index = 0
    in_code = False
    code_lines: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(part.strip() for part in paragraph)), styles["AuditBody"]))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                code_style = ParagraphStyle("code", fontName="Courier", fontSize=7.2, leading=9, backColor=colors.HexColor("#F1F5F9"), borderPadding=5, spaceBefore=4, spaceAfter=7, wordWrap="CJK")
                story.append(Paragraph("<br/>".join(html.escape(line) for line in code_lines), code_style))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(stripped)
            index += 1
            continue
        image_match = re.fullmatch(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            image_path = (REPORT.parent / image_match.group(1)).resolve()
            if image_path.is_file():
                img = Image(str(image_path))
                max_w, max_h = 16.2 * cm, 8.2 * cm
                scale = min(max_w / img.imageWidth, max_h / img.imageHeight, 1.0)
                img.drawWidth = img.imageWidth * scale
                img.drawHeight = img.imageHeight * scale
                img.hAlign = "CENTER"
                story.extend([Spacer(1, 4), img, Spacer(1, 8)])
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            group = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                group.append(lines[index].strip())
                index += 1
            rows = table_rows(group)
            if rows:
                header_style = ParagraphStyle("AuditTableHeader", parent=styles["AuditSmall"], fontName=font_bold, textColor=colors.white)
                formatted = [[Paragraph(inline_markup(cell), header_style if row_idx == 0 else styles["AuditSmall"]) for cell in row] for row_idx, row in enumerate(rows)]
                col_count = max(len(row) for row in rows)
                widths = [16.2 * cm / col_count] * col_count
                table = Table(formatted, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12233F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), font_bold),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F8")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.extend([Spacer(1, 5), table, Spacer(1, 7)])
            continue
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), styles["CoverTitle"]))
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:]), styles["AuditH2"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:]), styles["AuditH3"]))
            index += 1
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph("• " + inline_markup(stripped[2:]), styles["AuditBullet"]))
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush_paragraph()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font, 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(1.8 * cm, 1.0 * cm, "UNIVERSAL_LOG - Annexe d'audit du 21 novembre 2026")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=1.6*cm, bottomMargin=1.6*cm, title="Audit des courbes courtes et de KCNN4", author="Projet UNIVERSAL_LOG")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
