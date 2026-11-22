"""Append the synthetic sensitivity V2 audit to the active whitepaper."""
from __future__ import annotations
import argparse, csv, gc, hashlib, html, json, math, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from PIL import Image as PILImage
import pymupdf as fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
V10_ACTIVE = ROOT / "output" / "master_whitepaper_v10"
V10_ARCHIVE = ROOT / "archive_sources" / "master_whitepaper_v10"
V10_DIR = V10_ARCHIVE if V10_ARCHIVE.is_dir() else V10_ACTIVE
BASE_PDF = V10_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf"
TEST_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "TRANSITION_SENSITIVITY_V2"
PIPELINE_SOURCE = (ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20"
                   / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source"
                   / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py")
OUT_DIR = ROOT / "output" / "master_whitepaper_v11"
TMP_DIR = ROOT / "tmp" / "pdfs"
APPENDIX = TMP_DIR / "appendix_transition_sensitivity_v2_v11.pdf"
FINAL_PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf"
PDF_SHA = FINAL_PDF.with_suffix(FINAL_PDF.suffix + ".sha256")
IMAGE_CACHE = TMP_DIR / "v11_sensitivity_pdf_images"
NATIVE_DIR = TMP_DIR / "v11_native_artifact_chunks_20261122"
STATE, QA = TEST_DIR / "run_state.json", TEST_DIR / "validation_results.json"
PLAN, SUMMARY = TEST_DIR / "campaign_plan.json", TEST_DIR / "patient_control_summary.csv"
REPORT, INPUTS = TEST_DIR / "AUDIT_RESULTATS_SENSIBILITE_V2_FR.md", TEST_DIR / "inputs"
RUNS, LOGS = TEST_DIR / "runs", TEST_DIR / "logs"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def inline(text: str) -> str:
    text = str(text).replace("—", "-").replace("–", "-").replace("−", "-").replace("×", "x")
    return html.escape(text, quote=False)

def safe(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}" if value == value else "NA"
    return str(value)

def table(rows, widths=None, font_size=6.1, repeat=1):
    data = []
    for index, row in enumerate(rows):
        style = ParagraphStyle(
            name=f"CellV11_{index}", fontName="Helvetica-Bold" if index == 0 else "Helvetica",
            fontSize=font_size, leading=font_size + 1.2,
            textColor=colors.white if index == 0 else colors.HexColor("#17212b"),
            wordWrap="CJK")
        data.append([Paragraph(inline(cell), style) for cell in row])
    result = Table(data, colWidths=widths, repeatRows=repeat, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#234e70")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf3f7")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#a9bac7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.2), ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0)]))
    return result

def ready_image(source: Path, label: str) -> Path:
    IMAGE_CACHE.mkdir(parents=True, exist_ok=True)
    destination = IMAGE_CACHE / f"{label}.jpg"
    if destination.is_file() and destination.stat().st_size and destination.stat().st_mtime >= source.stat().st_mtime:
        return destination
    with PILImage.open(source) as original:
        image = original.convert("RGBA") if "A" in original.getbands() else original.convert("RGB")
        image.thumbnail((1500, 2000), PILImage.Resampling.LANCZOS)
        if image.mode == "RGBA":
            background = PILImage.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        image.save(destination, format="JPEG", quality=86, optimize=True, dpi=(150, 150))
    return destination

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#b8c8d3"))
    canvas.line(17*mm, 15*mm, A4[0]-17*mm, 15*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#52697a"))
    canvas.drawString(17*mm, 10*mm, "Annexe V11 - sensibilité synthétique - UNIVERSAL_LOG")
    canvas.drawRightString(A4[0]-17*mm, 10*mm, str(doc.page))
    canvas.restoreState()

def native_footer(part_number):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#b8c8d3"))
        canvas.line(17*mm, 15*mm, A4[0]-17*mm, 15*mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#52697a"))
        canvas.drawString(17*mm, 10*mm, f"Annexe V11 - fichiers natifs - partie {part_number}")
        canvas.drawRightString(A4[0]-17*mm, 10*mm, str(doc.page))
        canvas.restoreState()
    return draw

def append_markdown(story, path: Path, styles):
    in_code, code_lines = False, []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith(chr(96)*3):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["V11Code"], maxLineLength=115))
                story.append(Spacer(1, 4))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
        elif not stripped:
            continue
        elif stripped.startswith("# "):
            story.append(Paragraph(inline(stripped[2:]), styles["V11H2"]))
        elif stripped.startswith("## ") or stripped.startswith("### "):
            story.append(Paragraph(inline(stripped.lstrip("#").strip()), styles["V11H2"]))
        elif stripped.startswith("|"):
            story.append(Preformatted(inline(stripped), styles["V11Code"], maxLineLength=115))
        elif stripped.startswith("- "):
            story.append(Paragraph("&bull; " + inline(stripped[2:]), styles["V11Body"]))
        elif stripped.startswith(">"):
            story.append(Paragraph(inline(stripped[1:].strip()), styles["V11Body"]))
        else:
            story.append(Paragraph(inline(stripped), styles["V11Body"]))
    if code_lines:
        story.append(Preformatted("\n".join(code_lines), styles["V11Code"], maxLineLength=115))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    for path in (BASE_PDF, STATE, QA, PLAN, SUMMARY, REPORT):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if (FINAL_PDF.exists() or APPENDIX.exists()) and not args.rebuild:
        raise FileExistsError("V11 PDF outputs exist; use --rebuild to replace generated outputs.")
    qa = json.loads(QA.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if qa.get("status") != "passed" or qa.get("completed_runs") != 35:
        raise RuntimeError("The complete 35-run V2 campaign is required before PDF generation.")
    runs = []
    for planned in plan["planned_runs"]:
        record = state.get("runs", {}).get(planned["run_key"], {})
        if record.get("status") != "complete":
            raise RuntimeError(f"Missing completed run {planned['run_key']}")
        result_path = Path(record["result_path"])
        runs.append({"run_key": planned["run_key"], "record": record,
                     "result_path": result_path, "brief": record["brief"]})

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="V11H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                              fontSize=11.5, leading=14, textColor=colors.HexColor("#17324d"),
                              spaceBefore=8, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="V11Body", parent=styles["BodyText"], fontName="Helvetica",
                              fontSize=7.4, leading=9.5, alignment=TA_LEFT, spaceAfter=3))
    styles.add(ParagraphStyle(name="V11Code", fontName="Courier", fontSize=5.0, leading=5.9,
                              leftIndent=2, rightIndent=2, backColor=colors.HexColor("#f2f5f7"),
                              borderPadding=2, spaceBefore=1, spaceAfter=2))

    story = [
        Paragraph("V11 - Sensibilité synthétique aux transitions", styles["Title"]),
        Paragraph("Annexe du livre blanc maître. Les 35 appels utilisent des séries générées; aucune donnée clinique n’a été chargée.", styles["V11Body"]),
        Paragraph(f"État technique : {qa['status']} | appels terminés : 35 | cœur : {qa.get('pipeline_version')}", styles["V11Body"]),
        PageBreak(),
    ]
    release_docs = [
        ROOT / "README_V11_CURRENT.md", ROOT / "COMPLETE_WHITEPAPER_V11_README.md",
        ROOT / "RELEASE_V11_CHANGELOG_FR.md", ROOT / "PUBLICATION_SCOPE_V11.md",
        ROOT / "BACKUP_README_V11_FR.md", TEST_DIR / "README_FR.md",
        TEST_DIR / "PROTOCOLE_SENSIBILITE_TRANSITIONS_V2_FR.md",
        TEST_DIR / "CORRECTION_RAPPORT_V2_FR.md",
        LOGS / "AUDIT_RESULTATS_SENSIBILITE_V2_FR_PRE_CORRECTION.md", REPORT,
    ]
    for path in release_docs:
        if path.is_file():
            append_markdown(story, path, styles)
            story.append(PageBreak())
    story.append(Paragraph("Plan gelé avec paramètres et empreintes", styles["V11H2"]))
    story.append(Preformatted(PLAN.read_text(encoding="utf-8"), styles["V11Code"], maxLineLength=115))
    story.append(PageBreak())
    for machine_path in [
        TEST_DIR / "validation_results.json",
        TEST_DIR / "PUBLIC_VALIDATION_SUMMARY_V2.json",
        TEST_DIR / "run_manifest.json",
        TEST_DIR / "ENVIRONMENT_LOCK_V2.txt",
        TEST_DIR / "run_state.json",
        TEST_DIR / "descriptive_summary.csv",
        TEST_DIR / "time_axis_localization_summary.csv",
        TEST_DIR / "runtime_summary_v2.csv",
    ]:
        if machine_path.is_file():
            story.append(Paragraph(inline(f"Trace machine lisible - {machine_path.name}"), styles["V11H2"]))
            machine_text = machine_path.read_text(encoding="utf-8", errors="replace")
            story.append(Preformatted(textwrap.dedent(machine_text), styles["V11Code"], maxLineLength=115))
            story.append(PageBreak())

    rows = [["N", "Condition", "Graine", "Contrôle", "Monotone", "T0 %", "Seuil", "TLog sat.", "TLog crit.", "TLog div.", "TLog nul", "Repli"]]
    tlog_rows = [["N", "Condition", "Graine", "Contrôle", "Saturation", "Criticité", "Divergence", "Réf. nulle"]]
    for run in runs:
        b = run["brief"]
        tlog = b.get("tlog_class_median") or {}
        rows.append([
            safe(b.get("n_points")), safe(b.get("condition")), safe(b.get("input_seed")),
            safe(b.get("control")), safe(b.get("control_monotone")), safe(b.get("t0_pct")),
            safe(b.get("threshold_status")), safe(tlog.get("saturation")), safe(tlog.get("criticality")),
            safe(tlog.get("divergence")), safe(tlog.get("null_reference")), safe(b.get("target_fallback_used")),
        ])
        tlog_rows.append([
            safe(b.get("n_points")), safe(b.get("condition")), safe(b.get("input_seed")),
            safe(b.get("control")), safe(tlog.get("saturation")), safe(tlog.get("criticality")),
            safe(tlog.get("divergence")), safe(tlog.get("null_reference")),
        ])
    story.append(Paragraph("Table complète par entrée et contrôle", styles["V11H2"]))
    story.append(table(rows, widths=[8*mm, 14*mm, 15*mm, 24*mm, 12*mm, 12*mm, 15*mm, 14*mm, 14*mm, 14*mm, 14*mm, 12*mm], font_size=4.8))
    story.append(PageBreak())
    story.append(Paragraph("Sorties TLog détaillées par exécution", styles["V11H2"]))
    story.append(table(tlog_rows, widths=[8*mm, 14*mm, 15*mm, 24*mm, 28*mm, 28*mm, 28*mm, 28*mm], font_size=5.1))
    story.append(PageBreak())

    time_rows = [["N", "Condition", "Runs", "T0 disponibles", "T0 médian %", "Erreur abs. médiane", "Erreur min", "Erreur max"]]
    time_path = TEST_DIR / "time_axis_localization_summary.csv"
    time_csv = list(csv.DictReader(time_path.open(encoding="utf-8-sig", newline="")))
    for row in time_csv:
        time_rows.append([
            row.get("n_points"), row.get("condition"), row.get("runs"), row.get("t0_available_count"),
            row.get("t0_median_pct"), row.get("absolute_t0_error_median_pct_points") or "non définie",
            row.get("absolute_t0_error_min_pct_points") or "non définie",
            row.get("absolute_t0_error_max_pct_points") or "non définie",
        ])
    story.append(Paragraph("Comparaison au centre connu, contrôle temporel uniquement", styles["V11H2"]))
    story.append(Paragraph("L’erreur est définie seulement pour les transitions injectées et le contrôle time_index. Le cas nul n’a pas de centre de transition.", styles["V11Body"]))
    story.append(table(time_rows, widths=[13*mm, 22*mm, 15*mm, 22*mm, 23*mm, 29*mm, 25*mm, 25*mm], font_size=6.0))
    story.append(PageBreak())

    for path, caption in [
        (TEST_DIR / "V2_T0_BY_CONTROL.png", "T0 par entrée synthétique et contrôle"),
        (TEST_DIR / "V2_TLOG_BY_CONDITION_CONTROL.png", "Classes TLog par condition et contrôle"),
    ]:
        if path.is_file():
            story.append(Paragraph(caption, styles["V11H2"]))
            image = Image(str(ready_image(path, path.stem)))
            scale = min((A4[0]-36*mm)/image.imageWidth, (A4[1]-55*mm)/image.imageHeight)
            image.drawWidth, image.drawHeight = image.imageWidth*scale, image.imageHeight*scale
            story.append(image)
            story.append(PageBreak())

    story.append(Paragraph("Entrées synthétiques complètes", styles["V11H2"]))
    for path in sorted(INPUTS.glob("*.csv")):
        story.append(Paragraph(inline(f"Entrée - {path.name}"), styles["V11H2"]))
        with path.open("r", encoding="utf-8", newline="") as stream:
            data = list(csv.reader(stream))
        story.append(table(data, widths=[20*mm, 27*mm, 16*mm, 16*mm, 24*mm, 24*mm, 24*mm, 24*mm], font_size=4.8))
        story.append(PageBreak())

    story.append(Paragraph("Harnais V2 reproductible", styles["V11H2"]))
    harness = (TEST_DIR / "run_transition_sensitivity_v2.py").read_text(encoding="utf-8")
    story.append(Preformatted(textwrap.dedent(harness), styles["V11Code"], maxLineLength=112))
    story.append(PageBreak())
    report_builder = (TEST_DIR / "build_sensitivity_report_v2.py").read_text(encoding="utf-8")
    story.append(Paragraph("Générateur de rapport", styles["V11H2"]))
    story.append(Preformatted(textwrap.dedent(report_builder), styles["V11Code"], maxLineLength=112))
    story.append(PageBreak())
    story.append(Paragraph("Cœur complet UNIVERSAL_LOG v6.0.1 utilisé par la campagne", styles["V11H2"]))
    story.append(Paragraph(
        f"Source appelée sans modification par le harnais. Taille : {PIPELINE_SOURCE.stat().st_size} octets. SHA-256 : {sha256(PIPELINE_SOURCE)}.",
        styles["V11Body"]))
    pipeline_lines = PIPELINE_SOURCE.read_text(encoding="utf-8", errors="replace").replace("—", "-").replace("–", "-").replace("×", "x").splitlines()
    for start in range(0, len(pipeline_lines), 400):
        story.append(Preformatted("\n".join(pipeline_lines[start:start + 400]), styles["V11Code"], maxLineLength=112))
    story.append(PageBreak())

    for run in runs:
        saved_run = json.loads(run["result_path"].read_text(encoding="utf-8"))
        result = saved_run.get("result", {})
        transitions = (result.get("run_pipeline") or {}).get("transition_analysis") or {}
        detail = [["Estimateur", "Flux", "Pré", "Post", "d1 pré", "d1 post", "d2 pré", "d2 post", "Delta d1", "Delta d2"]]
        for estimator, flux_map in transitions.items():
            if not isinstance(flux_map, dict):
                continue
            for flux, entry in flux_map.items():
                if flux == "Tous" or not isinstance(entry, dict):
                    continue
                detail.append([
                    estimator, flux, safe(entry.get("status_pre")), safe(entry.get("status")),
                    safe(entry.get("first_derivative_pre")), safe(entry.get("first_derivative")),
                    safe(entry.get("second_derivative_pre")), safe(entry.get("second_derivative")),
                    safe(entry.get("delta_first_derivative")), safe(entry.get("delta_second_derivative")),
                ])
        b = run["brief"]
        caption = f"Dérivées avant/après - N{b['n_points']} / {b['condition']} / graine {b['input_seed']} / {b['control']}"
        story.append(Paragraph(inline(caption), styles["V11H2"]))
        story.append(Paragraph("Les lignes agrégées Tous sont omises ici; les flux analysés restent distincts.", styles["V11Body"]))
        story.append(table(detail, widths=[20*mm, 22*mm, 10*mm, 10*mm, 18*mm, 18*mm, 18*mm, 18*mm, 20*mm, 20*mm], font_size=5.2))
        story.append(PageBreak())
        del saved_run, result, transitions, detail
        gc.collect()

    figures = sorted(RUNS.glob("*/*/*.png"))
    for index, path in enumerate(figures):
        caption = f"Figure - {path.parent.parent.name} / {path.parent.name} / {path.name}"
        story.append(Paragraph(inline(caption), styles["V11H2"]))
        image = Image(str(ready_image(path, f"run_{index:04d}")))
        scale = min((A4[0]-36*mm)/image.imageWidth, (A4[1]-55*mm)/image.imageHeight)
        image.drawWidth, image.drawHeight = image.imageWidth*scale, image.imageHeight*scale
        story.append(image)
        story.append(PageBreak())

    for path in sorted(LOGS.glob("*.log")):
        story.append(Paragraph(inline(f"Trace complète - {path.stem}"), styles["V11H2"]))
        log_text = path.read_text(encoding="utf-8", errors="replace").replace("—", "-").replace("–", "-").replace("×", "x")
        story.append(Preformatted(textwrap.dedent(log_text), styles["V11Code"], maxLineLength=125))
        story.append(PageBreak())

    native_text_files = sorted(
        path for path in RUNS.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".csv", ".txt", ".html"}
    )
    story.append(Paragraph("Fichiers natifs de résultats par appel - contenu texte intégral", styles["V11H2"]))
    story.append(Paragraph(
        f"Les {len(native_text_files)} fichiers JSON, JSONL, CSV, TXT et HTML de chaque appel sont reproduits dans les pages qui suivent. Les chemins, tailles et empreintes les identifient. Le ZIP séparé conserve les octets sources exacts.",
        styles["V11Body"]))
    story.append(PageBreak())

    doc = SimpleDocTemplate(str(APPENDIX), pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=16*mm, bottomMargin=20*mm,
                            title="Annexe V11 - sensibilité synthétique",
                            author="UNIVERSAL_LOG research audit")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    story.clear()
    del story
    gc.collect()

    NATIVE_DIR.mkdir(parents=True, exist_ok=True)
    native_parts = []
    files_per_part = 10
    for part_start in range(0, len(native_text_files), files_per_part):
        part_number = part_start // files_per_part + 1
        part_path = NATIVE_DIR / f"native_artifacts_{part_number:03d}.pdf"
        native_story = []
        for path in native_text_files[part_start:part_start + files_per_part]:
            relative = path.relative_to(TEST_DIR).as_posix()
            native_story.append(Paragraph(inline(f"Fichier natif - {relative}"), styles["V11H2"]))
            native_story.append(Preformatted(
                f"bytes={path.stat().st_size} sha256={sha256(path)}",
                styles["V11Code"], maxLineLength=125))
            try:
                artifact_text = path.read_text(encoding="utf-8", errors="replace").replace("—", "-").replace("–", "-").replace("×", "x")
            except OSError as exc:
                artifact_text = f"[Lecture impossible: {exc}]"
            artifact_lines = artifact_text.splitlines() or [""]
            for line_start in range(0, len(artifact_lines), 400):
                native_story.append(Preformatted(
                    "\n".join(artifact_lines[line_start:line_start + 400]),
                    styles["V11Code"], maxLineLength=125))
            native_story.append(PageBreak())
        part_doc = SimpleDocTemplate(str(part_path), pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                                     topMargin=16*mm, bottomMargin=20*mm,
                                     title=f"V11 fichiers natifs - partie {part_number}",
                                     author="UNIVERSAL_LOG research audit")
        part_footer = native_footer(part_number)
        part_doc.build(native_story, onFirstPage=part_footer, onLaterPages=part_footer)
        native_parts.append(part_path)
        del native_story, part_doc
        gc.collect()

    temporary_pdf = FINAL_PDF.with_name(FINAL_PDF.stem + ".building.pdf")
    merged = fitz.open()
    source_pdfs = [BASE_PDF, APPENDIX, *native_parts]
    part_page_counts = []
    for source_path in source_pdfs:
        source_doc = fitz.open(source_path)
        part_page_counts.append(source_doc.page_count)
        merged.insert_pdf(source_doc, links=True, annots=True)
        source_doc.close()
        gc.collect()
    merged.set_metadata({
        "title": "UNIVERSAL_LOG - Livre blanc complet V11 - sensibilité synthétique aux transitions",
        "subject": "Mise à jour V10 avec campagne synthétique V2 sur tailles, amplitudes, graines et axes de contrôle",
        "author": "UNIVERSAL_LOG research audit",
    })
    merged.save(str(temporary_pdf), garbage=0, deflate=False)
    merged.close()
    del merged
    gc.collect()
    final_reader = fitz.open(temporary_pdf)
    attachments = final_reader.embfile_count()
    if attachments:
        final_reader.close()
        temporary_pdf.unlink(missing_ok=True)
        raise RuntimeError("PDF must not contain attachments.")
    final_pages = final_reader.page_count
    final_reader.close()
    temporary_pdf.replace(FINAL_PDF)
    digest = sha256(FINAL_PDF)
    PDF_SHA.write_text(f"{digest}  {FINAL_PDF.name}\n", encoding="ascii")
    print(json.dumps({
        "base_pages": part_page_counts[0], "appendix_pages": part_page_counts[1],
        "native_text_artifacts": len(native_text_files), "native_parts": len(native_parts),
        "final_pages": final_pages, "pdf_bytes": FINAL_PDF.stat().st_size,
        "pdf_sha256": digest, "attachments": attachments,
        "pipeline_figures": len(figures), "logs": len(list(LOGS.glob("*.log"))),
        "pdf": str(FINAL_PDF),
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
