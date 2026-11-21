"""Build and append the audited PDAC axis/flux results to the V7 whitepaper."""

import hashlib
import html
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
AUDIT_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21"
SOURCE_MD = AUDIT_DIR / "REPORT_PDACPATIENT_AXIS_FLUX_AUDIT_FR.md"
TMP_DIR = ROOT / "tmp" / "pdfs"
TMP_DIR.mkdir(parents=True, exist_ok=True)
APPENDIX_PDF = TMP_DIR / "appendix_pdac_patient_axis_flux_v7.pdf"
BASE_PDF = ROOT / "archive_sources" / "master_whitepaper_v6" / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V6_2026-11-21.pdf"
FINAL_PDF = ROOT / "output" / "master_whitepaper_v7" / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V7_2026-11-21.pdf"
FINAL_PDF.parent.mkdir(parents=True, exist_ok=True)
if FINAL_PDF.exists():
    raise FileExistsError(f"Refusing to overwrite {FINAL_PDF}")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="V7Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=colors.HexColor("#17324d"), spaceAfter=16))
styles.add(ParagraphStyle(name="V7H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#17324d"), spaceBefore=13, spaceAfter=7, keepWithNext=True))
styles.add(ParagraphStyle(name="V7H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#285276"), spaceBefore=9, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="V7Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.4, leading=11.5, alignment=TA_LEFT, spaceAfter=6))
styles.add(ParagraphStyle(name="V7Bullet", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.2, leading=11, leftIndent=12, firstLineIndent=-8, spaceAfter=4))
styles.add(ParagraphStyle(name="V7Number", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.2, leading=11, leftIndent=17, firstLineIndent=-15, spaceAfter=4))
styles.add(ParagraphStyle(name="V7Cell", parent=styles["BodyText"], fontName="Helvetica", fontSize=6.3, leading=7.5, spaceAfter=0, wordWrap="CJK"))
styles.add(ParagraphStyle(name="V7Head", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=6.5, leading=7.8, textColor=colors.white, spaceAfter=0, wordWrap="CJK"))
styles.add(ParagraphStyle(name="V7Code", fontName="Courier", fontSize=6.7, leading=8.3, leftIndent=6, rightIndent=6, backColor=colors.HexColor("#f2f5f7"), borderPadding=5, spaceBefore=2, spaceAfter=6))
styles.add(ParagraphStyle(name="V7Caption", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=7.3, leading=9, alignment=TA_CENTER, textColor=colors.HexColor("#526272"), spaceAfter=6))


def inline(text: str) -> str:
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#1b6e9c">\1</link>', text)
    return text


def table_cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c8d2dc"))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#526272"))
    canvas.drawString(18 * mm, 10 * mm, "Annexe V7 - PDAC, balayage multi-axes contrôle × flux - 21 novembre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


lines = SOURCE_MD.read_text(encoding="utf-8").splitlines()
story = []
page_width = A4[0] - 36 * mm
i = 0
in_code = False
code_lines: list[str] = []
while i < len(lines):
    raw = lines[i].rstrip()
    stripped = raw.strip()
    if stripped.startswith("```"):
        if in_code:
            story.append(Preformatted(html.escape("\n".join(code_lines)), styles["V7Code"], maxLineLength=105))
            code_lines = []
            in_code = False
        else:
            in_code = True
        i += 1
        continue
    if in_code:
        code_lines.append(raw)
        i += 1
        continue
    if not stripped:
        i += 1
        continue
    image_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
    if image_match:
        alt, image_rel = image_match.groups()
        image_path = (SOURCE_MD.parent / image_rel).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        img = Image(str(image_path), width=page_width, height=160 * mm, kind="proportional", hAlign="CENTER")
        img._restrictSize(page_width, 160 * mm)
        story.append(KeepTogether([Spacer(1, 4), img, Paragraph(inline(alt), styles["V7Caption"])]))
        i += 1
        continue
    if stripped.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = table_cells(lines[i])
            if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row):
                rows.append(row)
            i += 1
        if rows:
            col_count = max(map(len, rows))
            cell_style = styles["V7Head"]
            data = []
            for r_index, row in enumerate(rows):
                row_style = styles["V7Head"] if r_index == 0 else styles["V7Cell"]
                data.append([Paragraph(inline(value), row_style) for value in row] + [Paragraph("", row_style)] * (col_count - len(row)))
            widths = [page_width / col_count] * col_count
            if col_count == 5 and len(rows[0]) == 5 and "Estimateurs" in " ".join(rows[0]):
                widths = [page_width * 0.34, page_width * 0.15, page_width * 0.21, page_width * 0.14, page_width * 0.16]
            if col_count == 3:
                widths = [page_width * 0.47, page_width * 0.26, page_width * 0.27]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#285276")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c5d1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
            ]))
            story.extend([Spacer(1, 2), table, Spacer(1, 7)])
        continue
    if stripped.startswith("# "):
        story.append(Paragraph(inline(stripped[2:]), styles["V7Title"]))
        i += 1
        continue
    if stripped.startswith("## "):
        story.append(Paragraph(inline(stripped[3:]), styles["V7H2"]))
        i += 1
        continue
    if stripped.startswith("### "):
        story.append(Paragraph(inline(stripped[4:]), styles["V7H3"]))
        i += 1
        continue
    if stripped.startswith("- "):
        story.append(Paragraph("• " + inline(stripped[2:]), styles["V7Bullet"]))
        i += 1
        continue
    numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
    if numbered:
        story.append(Paragraph(numbered.group(1) + ". " + inline(numbered.group(2)), styles["V7Number"]))
        i += 1
        continue
    paragraph = [stripped]
    i += 1
    while i < len(lines):
        nxt = lines[i].strip()
        if not nxt or nxt.startswith(("#", "|", "- ", "![", "```")) or re.match(r"^\d+\.\s+", nxt):
            break
        paragraph.append(nxt)
        i += 1
    story.append(Paragraph(inline(" ".join(paragraph)), styles["V7Body"]))

doc = SimpleDocTemplate(
    str(APPENDIX_PDF), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=17 * mm, bottomMargin=21 * mm,
    title="Annexe V7 - PDAC patient axis and flux audit",
    author="UNIVERSAL_LOG research audit",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)

base_reader = PdfReader(str(BASE_PDF))
appendix_reader = PdfReader(str(APPENDIX_PDF))
writer = PdfWriter()
writer.append(base_reader)
writer.append(appendix_reader)
writer.add_metadata({
    "/Title": "UNIVERSAL_LOG - Livre blanc complet V7 - audit multi-axes patient PDAC",
    "/Subject": "Livre blanc complet avec annexe de balayage axe de contrôle × flux sur cohorte transversale PDAC",
    "/Author": "UNIVERSAL_LOG research audit",
})
with FINAL_PDF.open("wb") as stream:
    writer.write(stream)

check = PdfReader(str(FINAL_PDF))
digest = hashlib.sha256()
with FINAL_PDF.open("rb") as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(block)
FINAL_PDF.with_suffix(FINAL_PDF.suffix + ".sha256").write_text(f"{digest.hexdigest()}  {FINAL_PDF.name}\n", encoding="ascii")
print({
    "base_pages": len(base_reader.pages),
    "appendix_pages": len(appendix_reader.pages),
    "final_pages": len(check.pages),
    "final_pdf_bytes": FINAL_PDF.stat().st_size,
    "sha256": digest.hexdigest(),
    "pdf": str(FINAL_PDF),
})
