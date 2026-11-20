# SPDX-License-Identifier: MIT
"""Append the 2026-11-15 Cohen-d/seed-trace audit supplement to V2."""
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
BENCHMARK = TRACE / "cliff_vs_cohen_scan_benchmark.json"
BUILD_RECORD = TRACE / "cohend_only_variant_build_record.json"
SEED_RECORD = TRACE / "build_record.json"
SMOKE_RECORD = TRACE / "v5_9_2_cohen_standard_fast_smoke" / "smoke_run_record.json"
INDEX = ROOT / "SUPPLEMENT_ATTACHMENT_INDEX_V3.csv"
QA = AUDIT / "whitepaper_qa" / "supplement_2026-11-15" / "v3_whitepaper_qa.json"
ADDENDUM = ROOT / "AUDIT_SUPPLEMENT_2026-11-15.md"
README = ROOT / "README_AUDIT_REPRODUCTION_V3.md"
REPRO = ROOT / "REPRODUCE_SUPPLEMENT_V3.ps1"
BUILDER = AUDIT / "build_v3_whitepaper_seedtrace.py"
FINALIZER = AUDIT / "finalize_v3_package.py"
VERSION_FILES = [
    ROOT / "UNIVERSAL_LOG_v5.3_COHEND_ONLY.py",
    ROOT / "UNIVERSAL_LOG_v5.8_COHEND_ONLY.py",
    ROOT / "UNIVERSAL_LOG_v5.9.0_COHEND_ONLY.py",
    ROOT / "UNIVERSAL_LOG_v5.9.2.py",
]


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
    files.extend([ADDENDUM, README, REPRO, BUILDER, FINALIZER, *VERSION_FILES])
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing V3 attachment source(s): " + ", ".join(missing))
    return sorted({p.resolve() for p in files if p.resolve() != APPENDIX_PDF.resolve()}, key=lambda p: str(p).casefold())


def write_index(paths: list[Path]) -> list[tuple[str, str, int, str]]:
    rows = []
    with INDEX.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["embedded_name", "project_path", "bytes", "sha256"])
        for i, path in enumerate(paths, 1):
            rel = path.relative_to(ROOT).as_posix()
            embedded = f"V3SUPP{i:04d}__{rel.replace('/', '__')}"
            if len(embedded) > 180:
                embedded = f"V3SUPP{i:04d}__{sha256(path)[:12]}__{path.stem[:100]}{path.suffix}"
            row = (embedded, rel, path.stat().st_size, sha256(path))
            rows.append(row)
            writer.writerow(row)
    index_rel = INDEX.relative_to(ROOT).as_posix()
    # The index cannot contain its own final hash without a self-reference
    # cycle. Its hash is captured in the PDF QA JSON and this embedding row.
    rows.append(("SUPPLEMENT_ATTACHMENT_INDEX_V3.csv", index_rel, INDEX.stat().st_size, sha256(INDEX)))
    return rows


def make_appendix(base_pages: int, final_attachments: int) -> int:
    pagesize = landscape(letter)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="V3Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=7))
    styles.add(ParagraphStyle(name="V3Sub", parent=styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#44546A"), spaceAfter=10))
    styles.add(ParagraphStyle(name="V3Head", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#17365D"), spaceBefore=5, spaceAfter=3))
    styles.add(ParagraphStyle(name="V3Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.6, leading=11.2, spaceAfter=4))
    styles.add(ParagraphStyle(name="V3Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.4, leading=9, spaceAfter=2))
    styles.add(ParagraphStyle(name="V3Code", parent=styles["Code"], fontName="Courier", fontSize=7, leading=9, backColor=colors.HexColor("#F3F5F7"), borderColor=colors.HexColor("#D6DCE4"), borderWidth=0.4, borderPadding=4, spaceBefore=2, spaceAfter=4))

    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    ratios = [row["cliff_over_cohen_speed_ratio"] for row in benchmark["results"]]
    correlations = [row["spearman_score_curve_correlation"] for row in benchmark["results"] if row["spearman_score_curve_correlation"] is not None]
    build = json.loads(BUILD_RECORD.read_text(encoding="utf-8"))
    seed = json.loads(SEED_RECORD.read_text(encoding="utf-8"))
    smoke = json.loads(SMOKE_RECORD.read_text(encoding="utf-8"))

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
        Paragraph("SUPPLÉMENT D’AUDIT — 15 NOVEMBRE 2026", styles["V3Title"]),
        Paragraph("Cohen-d-only : comparaison des scans et choix de version", styles["V3Sub"]),
        Paragraph("Cohen-d est un écart moyen standardisé, signé et non borné. Cliff’s delta est une différence de probabilités de dominance, signée et bornée entre -1 et +1. Ils répondent à des questions différentes; un espace numérique plus large n’implique pas, à lui seul, davantage d’information.", styles["V3Body"]),
        Paragraph("Correction de formule : l’archive utilisait une moyenne non pondérée des variances dans cohen_d. Les nouvelles variantes utilisent le SD pooled classique, pondéré par les degrés de liberté. Les valeurs peuvent donc différer de celles des versions historiques lorsque les groupes ont des tailles inégales.", styles["V3Body"]),
        Paragraph("1. Benchmark apparié sur les données Ising archivées", styles["V3Head"]),
        Paragraph("Même axe MC_Update, mêmes trois flux, 31 candidats et mêmes tailles de fenêtre/groupe pour chaque paire. Une chauffe est exclue; temps médians sur cinq appels. Cohen-d utilise le scan optimisé déjà présent en v5.9.1; Cliff utilise le scan hérité.", styles["V3Body"]),
    ]
    scan_rows = [["Entrée", "Mode", "Seuil d", "Seuil Cliff", "Scan d (s)", "Scan Cliff (s)", "Ratio"]]
    for row in benchmark["results"]:
        label = "80 lignes" if row["input"] == "archived_80_row_slice" else "200 lignes"
        scan_rows.append([
            label, row["mode_parameters_from_v5_9_1"],
            f"{row['cohen_threshold']:.2f}", f"{row['cliff_threshold']:.2f}",
            f"{row['cohen_median_seconds']:.4f}", f"{row['cliff_median_seconds']:.4f}",
            f"{row['cliff_over_cohen_speed_ratio']:.2f}x",
        ])
    scan_table = Table(scan_rows, colWidths=[1.15 * inch, 0.86 * inch, 0.9 * inch, 1.05 * inch, 1.05 * inch, 1.15 * inch, 0.75 * inch], repeatRows=1)
    scan_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.4),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D0DA")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([
        scan_table,
        Spacer(1, 5),
        Paragraph(f"Observation : le scan Cohen-d est {min(ratios):.2f} à {max(ratios):.2f} fois plus rapide dans ces six appels; ce n’est pas une mesure de vitesse totale du pipeline. Les seuils sont différents dans les trois cas à 80 lignes (36,67 contre 40,00) et identiques à 200 lignes (63,33). Corrélation de rang des courbes : {min(correlations):.3f} à {max(correlations):.3f}; les résultats ne sont donc pas généralement identiques.", styles["V3Body"]),
        Paragraph("2. Variantes livrées", styles["V3Head"]),
        Paragraph("Copies dérivées : v5.3, v5.8, v5.9.0 et le candidat courant v5.9.2. Toutes les configurations actives et le diagnostic inter-classes utilisent Cohen-d; la clé exportée devient <font name='Courier'>cohen_d_between_classes</font>. Les demandes explicites de Cliff sont rejetées. Le helper Cliff reste uniquement pour compatibilité d’import, avec zéro appel actif.", styles["V3Body"]),
        Paragraph(f"TLog est conservé : T_log(d)=(d-4)*ln(n), avec n=nombre de lignes CSV, uniquement pour les estimateurs dimensionnels admissibles; les z-scores n’entrent pas dans cette formule. Le run rapide a exporté {smoke['tlog']['eligible_estimator_count']} estimateurs, {smoke['tlog']['d_kind_group_count']} groupes d_kind et {smoke['tlog']['class_median_count']} médianes de classe. Cohen-d remplace Cliff dans les scans et la séparation relative; la formule TLog reste en place.", styles["V3Body"]),
        Paragraph("Les sources anciennes ne sont pas modifiées. Les nouvelles variantes n’ont pas reçu de validation scientifique complète; le changement peut modifier seuils, scores et classifications. Les lecteurs du résultat doivent migrer de <font name='Courier'>cliff_between_classes</font> à <font name='Courier'>cohen_d_between_classes</font>.", styles["V3Body"]),
        PageBreak(),
        Paragraph("CORRECTION L7b ET REPRODUCTIBILITÉ", styles["V3Title"]),
        Paragraph("3. Correction de traçabilité de la graine", styles["V3Head"]),
        Paragraph("Le résultat v5.9.1 archivé indique <font name='Courier'>graine_alternative=null</font>, alors que le runner choisit 123. Le résumé perdait la valeur connue par le helper. Le candidat v5.9.2 la transmet et l’exporte; les formules, seuils et verdicts L7b ne changent pas.", styles["V3Body"]),
        Paragraph("4. Contrôles exécutés", styles["V3Head"]),
    ])
    checks = [
        ["Suite", "Vérifications", "Résultat"],
        ["Traçabilité seed", "5 : graine 123/0, option absente, export et orchestration simulée", "5/5 PASS"],
        ["Cohen-only", "7 : import des 4 versions, presets, absence d’appels Cliff, rejet, formule pooled, seed fix et scans", "7/7 PASS"],
        ["Benchmark", "6 comparaisons de scan sur 80/200 lignes", "écarts à n=80"],
        ["Run CLI 80 lignes", f"fast terminé; T0={smoke['threshold_optimizer']['T0_pct']:.2f}%; TLog {smoke['tlog']['eligible_estimator_count']} estimateurs / {smoke['tlog']['d_kind_group_count']} d_kind / {smoke['tlog']['class_median_count']} classes; L7b désactivé", "succès; logiciel"],
    ]
    check_table = Table(checks, colWidths=[1.35 * inch, 6.4 * inch, 1.55 * inch], repeatRows=1)
    check_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D0DA")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        check_table,
        Spacer(1, 5),
        Paragraph("L’orchestration seed utilise un CSV synthétique de 60 lignes et un moteur simulé; elle vérifie le passage des graines [123, 77, 77, 77], pas les estimateurs. Le smoke run rapporte T0 interne, L7a UP à 50% et régime criticality, sans estimer Tc. Son journal conserve des avertissements de précision sur moments presque constants et de spectre nul/insuffisant. Aucun full L7b de 28 minutes n’a été relancé. Aucune conclusion nouvelle sur Tc, la transition ou l’universalité n’est tirée.", styles["V3Body"]),
        Paragraph("5. Reproduction", styles["V3Head"]),
        Paragraph(".\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\build_v5_9_2_seedtrace.py<br/>.\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\build_cohend_only_variants.py<br/>.\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\benchmark_cliff_vs_cohen.py<br/>.\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\test_l7b_seedtrace.py<br/>.\\.venv\\Scripts\\python.exe .\\audit_release\\2026-11-15_l7b_seedtrace_fix\\test_cohend_only_variants.py", styles["V3Code"]),
        Paragraph("6. SHA-256 des sources", styles["V3Head"]),
        Paragraph("v5.9.1 entrée : " + safe(seed["source_sha256"]), styles["V3Small"]),
        Paragraph("Candidat seed-trace : " + safe(seed["output_sha256"]), styles["V3Small"]),
        Paragraph("v5.9.2 Cohen-only : " + safe(next(item["target_sha256"] for item in build["variants"] if item["name"].startswith("v5.9.2"))), styles["V3Small"]),
        Paragraph("7. Sources méthodologiques", styles["V3Head"]),
        Paragraph("Cliff (1993), <i>Dominance statistics</i>, DOI 10.1037/0033-2909.114.3.494. Marfo &amp; Okyere (2019), <i>Heliyon</i> 5(6):e01838, PMCID PMC6562325. Les liens directs et le détail des hypothèses sont dans le supplément Markdown joint.", styles["V3Small"]),
        Paragraph(f"Après ajout : {base_pages + 2} pages prévues, {final_attachments} pièces jointes prévues, index V3 compris.", styles["V3Small"]),
    ])
    doc = SimpleDocTemplate(str(APPENDIX_PDF), pagesize=pagesize, rightMargin=0.55 * inch, leftMargin=0.55 * inch, topMargin=0.43 * inch, bottomMargin=0.62 * inch, title="Audit addendum — Cohen d and L7b seed traceability — 2026-11-15", author="UNIVERSAL_LOG audit")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return len(PdfReader(str(APPENDIX_PDF)).pages)


def main() -> None:
    if not V2_PDF.is_file():
        raise FileNotFoundError(V2_PDF)
    if V3_PDF.exists():
        if not QA.is_file() or json.loads(QA.read_text(encoding="utf-8")).get("pdf_sha256") != sha256(V3_PDF):
            raise FileExistsError("Existing V3 PDF is not the previously validated builder output; refusing overwrite")
    if V3_PDF.with_suffix(".pdf.tmp").exists():
        raise FileExistsError("V3 temporary output already exists; refusing overwrite")
    paths = trace_files()
    # The attachment index and standalone appendix PDF are both embedded.
    final_attachments = len(PdfReader(str(V2_PDF)).attachments) + len(paths) + 2
    appendix_pages = make_appendix(len(PdfReader(str(V2_PDF)).pages), final_attachments)
    if appendix_pages != 2:
        raise AssertionError(f"Expected 2 appendix pages, got {appendix_pages}")
    paths.append(APPENDIX_PDF)
    rows = write_index(paths)

    base = PdfReader(str(V2_PDF))
    base_pages = len(base.pages)
    base_attachments = len(base.attachments)
    supplement = PdfReader(str(APPENDIX_PDF))
    writer = PdfWriter()
    writer.clone_document_from_reader(base)
    for page in supplement.pages:
        writer.add_page(page)
    writer.add_outline_item("Audit addendum 2026-11-15 — Cohen-d and L7b seed traceability", base_pages)
    writer.add_metadata({
        "/Title": "UNIVERSAL_LOG — livre blanc d’audit V3 — Cohen-d et traçabilité L7b",
        "/Subject": "Benchmark des scans d’effet et correctif de graine L7b",
        "/Author": "UNIVERSAL_LOG audit",
        "/Keywords": "audit, Cohen d, Cliff delta, L7b, reproductibilité, Ising",
    })
    for embedded_name, project_path, _, _ in rows:
        writer.add_attachment(embedded_name, (ROOT / Path(project_path)).read_bytes())

    temp_out = V3_PDF.with_suffix(".pdf.tmp")
    if temp_out.exists():
        raise FileExistsError(f"Refusing to overwrite temporary PDF: {temp_out}")
    with temp_out.open("wb") as f:
        writer.write(f)
    check = PdfReader(str(temp_out))
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
        "pdf_bytes": temp_out.stat().st_size,
        "pdf_sha256": sha256(temp_out),
        "appendix_source": str(APPENDIX_PDF.relative_to(ROOT)),
    }
    if qa["status"] != "pass":
        raise AssertionError(json.dumps(qa, ensure_ascii=False, indent=2))
    os.replace(temp_out, V3_PDF)
    QA.parent.mkdir(parents=True, exist_ok=True)
    QA.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
