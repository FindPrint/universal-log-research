"""Append the V9 ctDNA source and grouped-input audit to the V8 whitepaper."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21"
ARCHIVED_V8 = ROOT / "archive_sources" / "master_whitepaper_v8"
ACTIVE_V8 = ROOT / "output" / "master_whitepaper_v8"
BASE_DIR = ARCHIVED_V8 if ARCHIVED_V8.is_dir() else ACTIVE_V8
BASE_PDF = BASE_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V8_2026-11-21.pdf"
OUT_DIR = ROOT / "output" / "master_whitepaper_v9"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = ROOT / "tmp" / "pdfs"
TMP_DIR.mkdir(parents=True, exist_ok=True)
APPENDIX = TMP_DIR / "appendix_ctdna_group_audit_v9.pdf"
FINAL_PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V9_2026-11-22.pdf"

if FINAL_PDF.exists():
    raise FileExistsError(FINAL_PDF)
if not BASE_PDF.is_file():
    raise FileNotFoundError(BASE_PDF)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="V9Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=colors.HexColor("#17324d"), spaceAfter=11))
styles.add(ParagraphStyle(name="V9H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=colors.HexColor("#17324d"), spaceBefore=10, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="V9H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=colors.HexColor("#285276"), spaceBefore=7, spaceAfter=3, keepWithNext=True))
styles.add(ParagraphStyle(name="V9Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, alignment=TA_LEFT, spaceAfter=4))
styles.add(ParagraphStyle(name="V9Bullet", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10, leftIndent=12, firstLineIndent=-8, spaceAfter=2.5))
styles.add(ParagraphStyle(name="V9Num", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10, leftIndent=16, firstLineIndent=-14, spaceAfter=2.5))
styles.add(ParagraphStyle(name="V9Cell", parent=styles["BodyText"], fontName="Helvetica", fontSize=6.6, leading=8, spaceAfter=0, wordWrap="CJK"))
styles.add(ParagraphStyle(name="V9Head", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=6.6, leading=8, textColor=colors.white, spaceAfter=0, wordWrap="CJK"))
styles.add(ParagraphStyle(name="V9Code", fontName="Courier", fontSize=6.2, leading=7.5, leftIndent=4, rightIndent=4, backColor=colors.HexColor("#f2f5f7"), borderPadding=3, spaceBefore=2, spaceAfter=4))
styles.add(ParagraphStyle(name="V9Footer", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=7, leading=8.5, alignment=TA_CENTER, textColor=colors.HexColor("#526272"), spaceAfter=4))


def inline(text: str) -> str:
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#1b6e9c">\1</link>', text)
    return text


def make_table(rows: list[list[str]], widths: list[float] | None = None) -> Table:
    ncols = max(len(row) for row in rows)
    data = []
    for index, row in enumerate(rows):
        style = styles["V9Head"] if index == 0 else styles["V9Cell"]
        data.append([Paragraph(inline(cell), style) for cell in row] + [Paragraph("", style)] * (ncols - len(row)))
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#285276")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c5d1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
    ]))
    return table


def add_markdown(story: list, path: Path, *, page_break_before: bool = True) -> None:
    if page_break_before:
        story.append(PageBreak())
    lines = path.read_text(encoding="utf-8").splitlines()
    in_code = False
    code_lines: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        s = raw.strip()
        if s.startswith("```"):
            if in_code:
                story.append(Preformatted(html.escape("\n".join(code_lines)), styles["V9Code"], maxLineLength=100))
                code_lines, in_code = [], False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(raw)
            i += 1
            continue
        if not s or s == "---":
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                    rows.append(cells)
                i += 1
            story.extend([Spacer(1, 2), make_table(rows), Spacer(1, 5)])
            continue
        if s.startswith("# "):
            story.append(Paragraph(inline(s[2:]), styles["V9Title"]))
            i += 1
            continue
        if s.startswith("## "):
            story.append(Paragraph(inline(s[3:]), styles["V9H2"]))
            i += 1
            continue
        if s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), styles["V9H3"]))
            i += 1
            continue
        if s.startswith("- "):
            story.append(Paragraph("• " + inline(s[2:]), styles["V9Bullet"]))
            i += 1
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            story.append(Paragraph(m.group(1) + ". " + inline(m.group(2)), styles["V9Num"]))
            i += 1
            continue
        paragraph = [s]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt == "---" or nxt.startswith(("#", "|", "- ", "```")) or re.match(r"^\d+\.\s+", nxt):
                break
            paragraph.append(nxt)
            i += 1
        story.append(Paragraph(inline(" ".join(paragraph)), styles["V9Body"]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c8d2dc"))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#526272"))
    canvas.drawString(18 * mm, 10 * mm, "Annexe V9 - ctDNA, groupes patients et erratum - 22 novembre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


story = [
    Paragraph("Mise à jour V9 - Données ctDNA longitudinales et groupes patients", styles["V9Title"]),
    Paragraph("Nouvel audit documentaire et statique. Aucun jeu patient obtenu; aucun run clinique ctDNA effectué.", styles["V9Body"]),
    Paragraph("Erratum bibliographique à V8", styles["V9H2"]),
    Paragraph("Le DOI 10.3389/fonc.2022.902177 correspond à Kirchweger et al. (2022), et non à Schlick. L'étude rapporte 70 patients; 45 étaient ctDNA positifs au départ et 32 avaient des mesures précoces et une réponse disponibles (PD 12, non-PD 20). Les prélèvements étaient répétés toutes les deux semaines jusqu'à la restadification. La déclaration de disponibilité annonce que les données brutes seront fournies par les auteurs sans restriction indue.", styles["V9Body"]),
    Paragraph("Schlick et al. est une publication distincte de 2021, DOI 10.1016/j.pan.2021.09.004. V8 demeure conservée dans les archives sans modification; V9 apporte la correction documentée.", styles["V9Body"]),
    Paragraph("Inspection du code v6.0.1", styles["V9H2"]),
]

audit = json.loads((DATA_DIR / "V6_0_1_GROUPED_INPUT_AUDIT.json").read_text(encoding="utf-8"))
checks_rows = [["Contrôle de code", "Résultat"],
               ["Paramètres run_pipeline", ", ".join(audit["entry_point_parameters"])],
               ["Identifiant/groupe patient transmis", "Non" if audit["checks"]["entry_point_has_no_patient_group_parameter"] else "À revoir"],
               ["groupby ou équivalent dans le point d'entrée", "Aucun" if audit["checks"]["entry_point_has_no_groupby_call"] else "Présent"],
               ["Mode fast", "min_len=50; w_size=80"],
               ["Audit AST", "Réussi" if audit["static_audit_passed"] else "Échec"],
               ["SHA-256 du script", audit["pipeline_sha256"]]]
story.append(make_table(checks_rows, widths=[64 * mm, 110 * mm]))
story.append(Spacer(1, 5))
story.append(Paragraph("Le point d'entrée transforme toutes les lignes gardées en une seule série de contrôle. Les 50 valeurs du mode fast comptent des lignes, pas des patients. Un tableau empilé ne peut donc pas être interprété comme une trajectoire cohorte. L'analyse par patient préserverait les frontières, mais les séries courtes s'abstiendraient avec le minimum actuel. Un futur mode panel doit être évalué sur données synthétiques et ne doit pas franchir les frontières patient.", styles["V9Body"]))

add_markdown(story, DATA_DIR / "AUDIT_DONNEES_LONGITUDINALES_ET_GROUPES_V9_FR.md")
add_markdown(story, DATA_DIR / "BROUILLON_DEMANDE_DONNEES_KIRCHWEGER_2022_EN.md")
add_markdown(story, DATA_DIR / "BROUILLON_DEMANDE_DONNEES_EDLAND_2023_EN.md")

doc = SimpleDocTemplate(str(APPENDIX), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=21 * mm, title="Annexe V9 - Audit ctDNA et groupes patients", author="UNIVERSAL_LOG research audit")
doc.build(story, onFirstPage=footer, onLaterPages=footer)

base_reader = PdfReader(str(BASE_PDF))
appendix_reader = PdfReader(str(APPENDIX))
writer = PdfWriter()
writer.append(base_reader)
writer.append(appendix_reader)
writer.add_metadata({
    "/Title": "UNIVERSAL_LOG - Livre blanc complet V9 - données ctDNA et compatibilité groupes",
    "/Subject": "Mise à jour V8 avec audit v6.0.1 longitudinal, comparaison des sources et erratum bibliographique",
    "/Author": "UNIVERSAL_LOG research audit",
})
with FINAL_PDF.open("wb") as stream:
    writer.write(stream)

check = PdfReader(str(FINAL_PDF))
digest = hashlib.sha256()
with FINAL_PDF.open("rb") as stream:
    for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(chunk)
FINAL_PDF.with_suffix(FINAL_PDF.suffix + ".sha256").write_text(f"{digest.hexdigest()}  {FINAL_PDF.name}\n", encoding="ascii")
print(json.dumps({
    "base_pages": len(base_reader.pages),
    "appendix_pages": len(appendix_reader.pages),
    "final_pages": len(check.pages),
    "final_pdf_bytes": FINAL_PDF.stat().st_size,
    "sha256": digest.hexdigest(),
    "attachments": list(check.attachments.keys()),
    "pdf": str(FINAL_PDF),
}, indent=2, ensure_ascii=False))
