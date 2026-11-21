import html
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(r"C:\Users\citys\Desktop\10-31-2026")
SOURCE_MD = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "ARCHIVE_AUDIT_2026-11-21" / "D_ARCHIVE_AUDIT_REPORT_FR.md"
TMP = ROOT / "tmp" / "pdfs"
TMP.mkdir(parents=True, exist_ok=True)
APPENDIX_PDF = TMP / "appendix_D_archive_review_2026-11-21.pdf"
BASE_PDF = ROOT / "archive_sources" / "master_whitepaper_v5" / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V5_2026-11-21.pdf"
FINAL_PDF = ROOT / "output" / "master_whitepaper_v6" / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V6_2026-11-21.pdf"
FINAL_PDF.parent.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=colors.HexColor("#17324d"), spaceAfter=16))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#17324d"), spaceBefore=13, spaceAfter=7, keepWithNext=True))
styles.add(ParagraphStyle(name="H3Custom", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#285276"), spaceBefore=9, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.7, leading=12.2, alignment=TA_LEFT, spaceAfter=6))
styles.add(ParagraphStyle(name="BulletCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.7, leading=12.2, leftIndent=12, firstLineIndent=-8, spaceAfter=4))
styles.add(ParagraphStyle(name="NumberCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.7, leading=12.2, leftIndent=17, firstLineIndent=-15, spaceAfter=5))
styles.add(ParagraphStyle(name="TableCellCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.3, leading=9.2, spaceAfter=0))
styles.add(ParagraphStyle(name="TableHeadCustom", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.4, leading=9.4, textColor=colors.white, spaceAfter=0))

def clean_markdown(text):
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

def table_cells(line):
    return [x.strip() for x in line.strip().strip("|").split("|")]

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c8d2dc"))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#526272"))
    canvas.drawString(18 * mm, 10 * mm, "Annexe - Revue des archives et des axes de controle - 21 novembre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()

lines = SOURCE_MD.read_text(encoding="utf-8").splitlines()
story = []
i = 0
while i < len(lines):
    raw = lines[i].strip()
    if not raw:
        i += 1
        continue
    if raw.startswith("|"):
        table_lines = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = table_cells(lines[i])
            if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row):
                table_lines.append(row)
            i += 1
        if table_lines:
            data = []
            for row_index, row in enumerate(table_lines):
                style = styles["TableHeadCustom"] if row_index == 0 else styles["TableCellCustom"]
                data.append([Paragraph(clean_markdown(cell), style) for cell in row])
            col_count = max(len(row) for row in table_lines)
            page_width = A4[0] - 36 * mm
            if col_count == 4:
                widths = [page_width * 0.37, page_width * 0.13, page_width * 0.37, page_width * 0.13]
            elif col_count == 3:
                widths = [page_width * 0.45, page_width * 0.28, page_width * 0.27]
            else:
                widths = [page_width / col_count] * col_count
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#285276")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c5d1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
            ]))
            story.extend([Spacer(1, 3), KeepTogether([table, Spacer(1, 8)])])
        continue
    if raw.startswith("# "):
        story.append(Paragraph(clean_markdown(raw[2:]), styles["ReportTitle"]))
        i += 1
        continue
    if raw.startswith("## "):
        story.append(Paragraph(clean_markdown(raw[3:]), styles["H2Custom"]))
        i += 1
        continue
    if raw.startswith("### "):
        story.append(Paragraph(clean_markdown(raw[4:]), styles["H3Custom"]))
        i += 1
        continue
    if raw.startswith("- "):
        bullet_parts = [raw[2:]]
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
            bullet_parts.append(lines[i].strip())
            i += 1
        story.append(KeepTogether([Paragraph("- " + clean_markdown(" ".join(bullet_parts)), styles["BulletCustom"])]))
        continue
    numbered = re.match(r"^(\d+)\.\s+(.*)$", raw)
    if numbered:
        story.append(KeepTogether([Paragraph(numbered.group(1) + ". " + clean_markdown(numbered.group(2)), styles["NumberCustom"])]))
        i += 1
        continue
    paragraph = [raw]
    i += 1
    while i < len(lines):
        nxt = lines[i].strip()
        if not nxt or nxt.startswith(("#", "|", "- ")) or re.match(r"^\d+\.\s+", nxt):
            break
        paragraph.append(nxt)
        i += 1
    story.append(Paragraph(clean_markdown(" ".join(paragraph)), styles["BodyCustom"]))

doc = SimpleDocTemplate(
    str(APPENDIX_PDF), pagesize=A4,
    rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=17 * mm, bottomMargin=21 * mm,
    title="Annexe - Revue des archives et axes de controle",
    author="UNIVERSAL_LOG research audit",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)

base_reader = PdfReader(str(BASE_PDF))
appendix_reader = PdfReader(str(APPENDIX_PDF))
writer = PdfWriter()
writer.append(base_reader)
writer.append(appendix_reader)
writer.add_metadata({
    "/Title": "UNIVERSAL_LOG - Livre blanc complet V6 - audit archives et roles axe/flux",
    "/Subject": "Livre blanc du projet avec annexe d'audit des archives, Ising, PDAC et regle de role controle/flux",
    "/Author": "UNIVERSAL_LOG research audit",
})
with FINAL_PDF.open("wb") as stream:
    writer.write(stream)

check = PdfReader(str(FINAL_PDF))
print({
    "base_pages": len(base_reader.pages),
    "appendix_pages": len(appendix_reader.pages),
    "final_pages": len(check.pages),
    "appendix_pdf_bytes": APPENDIX_PDF.stat().st_size,
    "final_pdf_bytes": FINAL_PDF.stat().st_size,
    "final_pdf": str(FINAL_PDF),
})
