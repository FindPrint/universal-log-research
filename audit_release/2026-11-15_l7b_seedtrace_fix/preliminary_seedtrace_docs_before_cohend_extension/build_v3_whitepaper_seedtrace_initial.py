# SPDX-License-Identifier: MIT
"""Append the 2026-11-15 seed-trace audit addendum to the V2 whitepaper."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit_release"
TRACE = AUDIT / "2026-11-15_l7b_seedtrace_fix"
V2_PDF = ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER_V2.pdf"
V3_PDF = ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER_V3.pdf"
APPENDIX_PDF = TRACE / "seedtrace_audit_addendum_source.pdf"
INDEX = ROOT / "SUPPLEMENT_ATTACHMENT_INDEX_V3.csv"
QA = AUDIT / "whitepaper_qa" / "supplement_2026-11-15" / "v3_whitepaper_qa.json"
ADDENDUM = ROOT / "AUDIT_SUPPLEMENT_2026-11-15.md"
README = ROOT / "README_AUDIT_REPRODUCTION_V3.md"
REPRO = ROOT / "REPRODUCE_SUPPLEMENT_V3.ps1"
BUILDER = AUDIT / "build_v3_whitepaper_seedtrace.py"
FINALIZER = AUDIT / "finalize_v3_package.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe(value) -> str:
    return html.escape("" if value is None else str(value), quote=False)


def trace_files() -> list[Path]:
    files = [p for p in TRACE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"]
    files.extend([ADDENDUM, README, REPRO, BUILDER, FINALIZER])
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing V3 attachment source(s): " + ", ".join(missing))
    return sorted({p.resolve() for p in files}, key=lambda p: str(p).casefold())


def write_index(paths: list[Path]) -> list[tuple[str, str, int, str]]:
    rows = []
    with INDEX.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["embedded_name", "project_path", "bytes", "sha256"])
        for i, path in enumerate(paths, 1):
            rel = path.relative_to(ROOT).as_posix()
            embedded = "V3SUPP%04d__%s" % (i, rel.replace("/", "__"))
            if len(embedded) > 180:
                embedded = f"V3SUPP{i:04d}__{sha256(path)[:12]}__{path.stem[:100]}{path.suffix}"
            row = (embedded, rel, path.stat().st_size, sha256(path))
            rows.append(row)
            writer.writerow(row)
        index_rel = INDEX.relative_to(ROOT).as_posix()
        row = ("SUPPLEMENT_ATTACHMENT_INDEX_V3.csv", index_rel, INDEX.stat().st_size, sha256(INDEX))
        rows.append(row)
        writer.writerow(row)
    return rows


def make_appendix(base_pages: int, base_attachments: int, added_attachments: int) -> int:
    pagesize = landscape(letter)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="V3Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=21, leading=26, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=10))
    styles.add(ParagraphStyle(name="V3Sub", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#44546A"), spaceAfter=14))
    styles.add(ParagraphStyle(name="V3Head", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#17365D"), spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="V3Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.3, leading=13, spaceAfter=6))
    styles.add(ParagraphStyle(name="V3Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10, spaceAfter=3))
    styles.add(ParagraphStyle(name="V3Code", parent=styles["Code"], fontName="Courier", fontSize=7.5, leading=10, backColor=colors.HexColor("#F3F5F7"), borderColor=colors.HexColor("#D6DCE4"), borderWidth=0.4, borderPadding=5, spaceBefore=4, spaceAfter=5))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CAD2DC"))
        canvas.line(0.45 * inch, 0.42 * inch, pagesize[0] - 0.45 * inch, 0.42 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(0.48 * inch, 0.25 * inch, "UNIVERSAL_LOG — supplément d’audit V3 — 2026-11-15")
        canvas.drawRightString(pagesize[0] - 0.48 * inch, 0.25 * inch, f"Page {doc.page}")
        canvas.restoreState()

    story = [
        Paragraph("ADDENDUM D’AUDIT — 15 NOVEMBRE 2026", styles["V3Title"]),
        Paragraph("Correction de traçabilité de la graine dans L7b-FULL", styles["V3Sub"]),
        Paragraph("Portée de cette correction : métadonnées et traçabilité uniquement. Le livre blanc V2 conserve les résultats historiques v5.9.1; le présent addendum documente un candidat v5.9.2 distinct.", styles["V3Body"]),
        Paragraph("1. Constat et hypothèse", styles["V3Head"]),
        Paragraph("Dans le résultat L7b-full archivé, <font name='Courier'>graine_alternative</font> vaut <font name='Courier'>null</font> alors que le code choisit la graine 123 lorsque la graine de référence est différente. Le helper connaît cette valeur, puis l’extracteur de résumé l’omet.", styles["V3Body"]),
        Paragraph("Hypothèse auditée : la valeur null résulte d’une perte de métadonnée entre le lancement du rerun et la construction du résumé; le calcul numérique du contrôle peut néanmoins s’être achevé.", styles["V3Body"]),
        Paragraph("2. Correction versionnée", styles["V3Head"]),
        Paragraph("Le candidat <font name='Courier'>v5.9.2-L7aL7b-DKind-AuditFix-SeedTrace</font> transmet la graine connue par l’appelant à <font name='Courier'>_l7b_extract_summary</font>, qui l’ajoute au résumé. Le diff joint ne modifie ni estimateur, ni seuil, ni formule de score, ni règle de verdict.", styles["V3Body"]),
        Paragraph("3. Résultat observé", styles["V3Head"]),
        Paragraph("Les cinq contrôles ciblés passent. Un test d’orchestration utilise un CSV synthétique de 60 lignes et un moteur simulé; les graines observées sont [123, 77, 77, 77] et la graine alternative exportée vaut 123. Les journaux, le test, le générateur, le pipeline corrigé, le diff et les empreintes sont joints au PDF.", styles["V3Body"]),
        Paragraph("Cette vérification confirme le transport du champ dans le chemin logiciel testé. Elle ne constitue pas une nouvelle expérience d’Ising ni une validation de la transition ou de l’universalité.", styles["V3Body"]),
        PageBreak(),
        Paragraph("VÉRIFICATION REPRODUCTIBLE ET LIMITES", styles["V3Title"]),
        Paragraph("4. Contrôles ciblés exécutés avec le Python 3.11.9 du projet", styles["V3Head"]),
    ]
    test_rows = [
        ["Contrôle", "Résultat", "Portée"],
        ["Graine connue (123)", "PASS", "Le résumé conserve la valeur fournie."],
        ["Graine nulle (0)", "PASS", "La valeur zéro n’est pas supprimée."],
        ["Graine omise", "PASS", "Le champ reste optionnel pour les références."],
        ["Export du check L7b", "PASS", "graine_alternative vaut 123."],
        ["Orchestration L7b simulée", "PASS", "123, 77, 77, 77 transmis aux quatre reruns."],
    ]
    table = Table(test_rows, colWidths=[1.65 * inch, 0.75 * inch, 6.6 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D0DA")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        table,
        Spacer(1, 10),
        Paragraph("5. Reproduction", styles["V3Head"]),
        Paragraph("Depuis la racine du projet, les deux commandes ci-dessous reconstruisent le candidat à partir du v5.9.1 archivé puis exécutent les contrôles ciblés :", styles["V3Body"]),
        Paragraph(".\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\build_v5_9_2_seedtrace.py<br/>.\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\test_l7b_seedtrace.py", styles["V3Code"]),
        Paragraph("Le générateur échoue si les fragments attendus du code source ne sont pas uniques. Il écrit un diff unifié et un enregistrement de build avec les empreintes SHA-256.", styles["V3Body"]),
        Paragraph("6. Limites explicites", styles["V3Head"]),
        Paragraph("Le moteur de pipeline a été simulé pour tester le câblage des graines. Le full L7b de près de 28 minutes n’a pas été relancé après ce correctif de métadonnées. Aucune conclusion nouvelle sur Tc, l’identification d’une transition ou l’universalité n’est tirée.", styles["V3Body"]),
        Paragraph("7. Empreintes du code", styles["V3Head"]),
        Paragraph("Entrée v5.9.1 : " + safe(json.loads((TRACE / "build_record.json").read_text(encoding="utf-8"))["source_sha256"]), styles["V3Small"]),
        Paragraph("Candidat v5.9.2 : " + safe(json.loads((TRACE / "build_record.json").read_text(encoding="utf-8"))["output_sha256"]), styles["V3Small"]),
        Paragraph(f"Le présent PDF contient {base_pages + 2} pages prévues et {base_attachments + added_attachments} pièces jointes prévues, index V3 compris.", styles["V3Small"]),
    ])
    doc = SimpleDocTemplate(str(APPENDIX_PDF), pagesize=pagesize, rightMargin=0.55 * inch, leftMargin=0.55 * inch, topMargin=0.48 * inch, bottomMargin=0.62 * inch, title="Audit addendum — L7b seed traceability — 2026-11-15", author="UNIVERSAL_LOG audit")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return len(PdfReader(str(APPENDIX_PDF)).pages)


def main() -> None:
    if not V2_PDF.is_file():
        raise FileNotFoundError(V2_PDF)
    if V3_PDF.exists() or V3_PDF.with_suffix(".pdf.tmp").exists():
        raise FileExistsError("V3 PDF or temporary output already exists; refusing overwrite")
    paths = trace_files()
    rows = write_index(paths)
    base = PdfReader(str(V2_PDF))
    base_pages = len(base.pages)
    base_attachments = len(base.attachments)
    appendix_pages = make_appendix(base_pages, base_attachments, len(rows))
    supplement = PdfReader(str(APPENDIX_PDF))
    if appendix_pages != 2:
        raise AssertionError(f"Expected 2 appendix pages, got {appendix_pages}")

    writer = PdfWriter()
    writer.clone_document_from_reader(base)
    for page in supplement.pages:
        writer.add_page(page)
    writer.add_outline_item("Audit addendum 2026-11-15 — L7b seed traceability", base_pages)
    writer.add_metadata({
        "/Title": "UNIVERSAL_LOG — livre blanc d’audit V3 — traçabilité L7b",
        "/Subject": "Correctif de traçabilité de la graine et tests ciblés L7b",
        "/Author": "UNIVERSAL_LOG audit",
        "/Keywords": "audit, L7b, seed, reproductibilité, Ising",
    })
    for embedded_name, project_path, _, _ in rows:
        path = ROOT / Path(project_path)
        writer.add_attachment(embedded_name, path.read_bytes())

    temp_out = V3_PDF.with_suffix(".pdf.tmp")
    with temp_out.open("wb") as f:
        writer.write(f)
    os.replace(temp_out, V3_PDF)

    check = PdfReader(str(V3_PDF))
    qa = {
        "status": "pass" if len(check.pages) == base_pages + appendix_pages and len(check.attachments) == base_attachments + len(rows) else "check_mismatch",
        "source_pdf": V2_PDF.name,
        "source_pdf_sha256": sha256(V2_PDF),
        "source_pages": base_pages,
        "source_attachments": base_attachments,
        "supplement_pages": appendix_pages,
        "final_pages": len(check.pages),
        "expected_final_pages": base_pages + appendix_pages,
        "new_embedded_files_including_index": len(rows),
        "final_attachments": len(check.attachments),
        "expected_final_attachments": base_attachments + len(rows),
        "attachment_index": INDEX.name,
        "attachment_index_sha256": sha256(INDEX),
        "pdf_bytes": V3_PDF.stat().st_size,
        "pdf_sha256": sha256(V3_PDF),
        "appendix_source": str(APPENDIX_PDF.relative_to(ROOT)),
    }
    QA.parent.mkdir(parents=True, exist_ok=True)
    QA.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if qa["status"] != "pass":
        raise AssertionError(json.dumps(qa, ensure_ascii=False, indent=2))
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
