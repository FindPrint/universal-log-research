"""Append the longitudinal ctDNA access audit and protocol to the V8 whitepaper."""

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
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-21" / "CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21"
OUT_DIR = ROOT / "output" / "master_whitepaper_v8"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = ROOT / "tmp" / "pdfs"
TMP_DIR.mkdir(parents=True, exist_ok=True)
APPENDIX = TMP_DIR / "appendix_longitudinal_ctdna_v8.pdf"
ARCHIVED_V7 = ROOT / "archive_sources" / "master_whitepaper_v7"
ACTIVE_V7 = ROOT / "output" / "master_whitepaper_v7"
BASE_V7_DIR = ARCHIVED_V7 if ARCHIVED_V7.is_dir() else ACTIVE_V7
BASE_PDF = BASE_V7_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V7_2026-11-21.pdf"
FINAL_PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V8_2026-11-21.pdf"
if FINAL_PDF.exists():
    raise FileExistsError(FINAL_PDF)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="V8Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#17324d"), spaceAfter=12))
styles.add(ParagraphStyle(name="V8H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#17324d"), spaceBefore=11, spaceAfter=6, keepWithNext=True))
styles.add(ParagraphStyle(name="V8H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10, leading=12.5, textColor=colors.HexColor("#285276"), spaceBefore=8, spaceAfter=4, keepWithNext=True))
styles.add(ParagraphStyle(name="V8Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.3, leading=11, alignment=TA_LEFT, spaceAfter=5))
styles.add(ParagraphStyle(name="V8Bullet", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
styles.add(ParagraphStyle(name="V8Num", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, leftIndent=16, firstLineIndent=-14, spaceAfter=3))
styles.add(ParagraphStyle(name="V8Cell", parent=styles["BodyText"], fontName="Helvetica", fontSize=7, leading=8.5, spaceAfter=0, wordWrap="CJK"))
styles.add(ParagraphStyle(name="V8Head", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7, leading=8.5, textColor=colors.white, spaceAfter=0, wordWrap="CJK"))
styles.add(ParagraphStyle(name="V8Code", fontName="Courier", fontSize=6.5, leading=8, leftIndent=5, rightIndent=5, backColor=colors.HexColor("#f2f5f7"), borderPadding=4, spaceBefore=2, spaceAfter=5))
styles.add(ParagraphStyle(name="V8Label", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.6, leading=9.2, textColor=colors.HexColor("#17324d"), spaceAfter=0))
styles.add(ParagraphStyle(name="V8Footer", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=7.2, leading=9, alignment=TA_CENTER, textColor=colors.HexColor("#526272"), spaceAfter=5))


def inline(text: str) -> str:
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#1b6e9c">\1</link>', text)
    return text


def split_table_line(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def make_table(rows: list[list[str]], widths: list[float] | None = None) -> Table:
    columns = max(len(row) for row in rows)
    data = []
    for index, row in enumerate(rows):
        style = styles["V8Head"] if index == 0 else styles["V8Cell"]
        data.append([Paragraph(inline(cell), style) for cell in row] + [Paragraph("", style)] * (columns - len(row)))
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
    code_mode = False
    code_lines: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()
        if stripped.startswith("```"):
            if code_mode:
                story.append(Preformatted(html.escape("\n".join(code_lines)), styles["V8Code"], maxLineLength=100))
                code_lines = []
                code_mode = False
            else:
                code_mode = True
            i += 1
            continue
        if code_mode:
            code_lines.append(raw)
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = split_table_line(lines[i])
                if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row):
                    rows.append(row)
                i += 1
            if rows:
                story.extend([Spacer(1, 2), make_table(rows), Spacer(1, 6)])
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(inline(stripped[2:]), styles["V8Title"]))
            i += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(inline(stripped[3:]), styles["V8H2"]))
            i += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(inline(stripped[4:]), styles["V8H3"]))
            i += 1
            continue
        if stripped.startswith("- "):
            story.append(Paragraph("• " + inline(stripped[2:]), styles["V8Bullet"]))
            i += 1
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            story.append(Paragraph(numbered.group(1) + ". " + inline(numbered.group(2)), styles["V8Num"]))
            i += 1
            continue
        paragraph = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "|", "- ", "```")) or re.match(r"^\d+\.\s+", nxt):
                break
            paragraph.append(nxt)
            i += 1
        story.append(Paragraph(inline(" ".join(paragraph)), styles["V8Body"]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c8d2dc"))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(colors.HexColor("#526272"))
    canvas.drawString(18 * mm, 10 * mm, "Annexe V8 - Accès aux données longitudinales ctDNA - 21 novembre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


story = []
story.append(Paragraph("Audit d'accès aux données longitudinales ctDNA", styles["V8Title"]))
story.append(Paragraph("Synthèse documentaire — données brutes non obtenues; aucun run complet UNIVERSAL_LOG réalisé sur cette étude.", styles["V8Body"]))
story.append(Paragraph("Source primaire : Schlick et al., Frontiers in Oncology (2022). Mesures ctDNA toutes les deux semaines selon l'article; 70 patients inclus, 32 séries complètes positives avec réponse disponible (PD 12, non-PD 20). Les auteurs indiquent que les données brutes sont disponibles sur demande.", styles["V8Body"]))
story.append(Paragraph("Décision actuelle", styles["V8H2"]))
story.append(Paragraph("Obtenir le fichier patient × prélèvement et son dictionnaire avant tout run. Compter patients et prélèvements séparément. Ne pas aplatir plusieurs patients en une seule série continue. Conserver la règle d'admission du pipeline et signaler une abstention si une série ne la franchit pas.", styles["V8Body"]))
story.append(Paragraph("Repère publié", styles["V8H2"]))
story.append(Paragraph("L'article rapporte un seuil relatif de ctDNA à deux semaines de 57,9 % de la valeur initiale, choisi et évalué dans cette même cohorte. Ce chiffre est un benchmark de l'étude, pas un résultat UNIVERSAL_LOG ni une validation indépendante.", styles["V8Body"]))

add_markdown(story, DATA_DIR / "AUDIT_ACCES_DONNEES_FR.md")
add_markdown(story, DATA_DIR / "PROTOCOLE_ANALYSE_AXE_FLUX_FR.md")
add_markdown(story, DATA_DIR / "BROUILLON_DEMANDE_DONNEES_EN.md")

story.append(PageBreak())
story.append(Paragraph("Registre compact de source et de décision", styles["V8Title"]))
with (DATA_DIR / "DATA_FIT_DECISION.csv").open(encoding="utf-8", newline="") as stream:
    fit_row = next(csv.DictReader(stream))
manifest = json.loads((DATA_DIR / "SOURCE_REGISTER.json").read_text(encoding="utf-8"))
decision_rows = [["Champ", "Valeur documentaire"],
                 ["Étude", manifest["study"]],
                 ["DOI", manifest["doi"]],
                 ["Patients / positifs baseline", f"{manifest['cohort_counts_as_reported']['total_patients']} / {manifest['cohort_counts_as_reported']['baseline_ctdna_positive']}"],
                 ["Séries complètes avec réponse", f"{manifest['cohort_counts_as_reported']['complete_serial_measurement_and_response']} (PD {manifest['cohort_counts_as_reported']['progressive_disease']}; non-PD {manifest['cohort_counts_as_reported']['non_progressive_disease']})"],
                 ["Axe temporel publié", manifest["sampling_as_reported"]],
                 ["État de données", fit_row["raw_patient_sample_matrix"]],
                 ["État pipeline", fit_row["pipeline_status"]],
                 ["Demande aux auteurs", "Brouillon préparé, non envoyé"]]
story.append(make_table(decision_rows, widths=[48 * mm, 126 * mm]))
story.append(Spacer(1, 10))
story.append(Paragraph("Traçabilité", styles["V8H2"]))
story.append(Paragraph("Le manifeste source est SOURCE_REGISTER.json; la décision tabulaire est DATA_FIT_DECISION.csv; le protocole et le modèle de demande sont conservés dans le même dossier du projet. La tentative de téléchargement du DOCX supplémentaire a renvoyé une page HTML d'interposition et n'a pas été retenue comme donnée.", styles["V8Body"]))

doc = SimpleDocTemplate(str(APPENDIX), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=21 * mm, title="Annexe V8 - Audit données ctDNA", author="UNIVERSAL_LOG research audit")
doc.build(story, onFirstPage=footer, onLaterPages=footer)

base_reader = PdfReader(str(BASE_PDF))
appendix_reader = PdfReader(str(APPENDIX))
writer = PdfWriter()
writer.append(base_reader)
writer.append(appendix_reader)
writer.add_metadata({
    "/Title": "UNIVERSAL_LOG - Livre blanc complet V8 - audit accès ctDNA longitudinal",
    "/Subject": "Livre blanc cumulatif avec audit source de données, protocole contrôle × flux et demande de données non envoyée",
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
