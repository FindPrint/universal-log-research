#!/usr/bin/env python3
"""Build a complete, auditable PDF addendum for the PDAC multiaxis scan.

The PDF contains the report, figures, methods, all 112 planned scan rows, and
an indexed set of exact source/code/result attachments. Attachments are the
authoritative machine-readable files; their SHA-256 hashes are printed in the
PDF for integrity checks.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties, findfont
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
RESULTS_44 = HERE / "results"
RESULTS_57 = HERE / "results_all_57"
RESULTS_LOW = HERE / "results_low_dose_internal_sensitivity"
RESULTS_G12C = HERE.parent / "external_validation_g12c" / "results"
RESULTS_GEO = HERE.parent / "candidate_combination_g12d_parp" / "results"
SOURCE_GEO = HERE.parent / "candidate_combination_g12d_parp" / "source"
DATA_DIR = (PROJECT_ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-16" /
            "daraxonrasib_resistance_2026")
RAW_DIR = DATA_DIR / "reanalyzed"
OUTPUT_DIR = PROJECT_ROOT / "output" / "pdf"
TMP_DIR = PROJECT_ROOT / "tmp" / "pdfs" / "pdac_multiaxis_2026-11-17"
OUTPUT_PDF = OUTPUT_DIR / "ADDENDUM_AUDIT_PDAC_MULTIFLUX_2026-11-17_v4_MAPPING_QA.pdf"
DRAFT_PDF = TMP_DIR / "draft.pdf"

BLUE = colors.HexColor("#17365D")
BLUE2 = colors.HexColor("#2878B5")
LIGHT_BLUE = colors.HexColor("#EAF1F8")
GREEN = colors.HexColor("#E2F0D9")
GRAY = colors.HexColor("#5B6573")
LIGHT_GRAY = colors.HexColor("#F2F4F7")
RED = colors.HexColor("#A61C2D")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pdf_safe(value: object) -> str:
    """Escape text and normalize dash glyphs to ASCII hyphens for PDF output."""
    s = str(value)
    for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        s = s.replace(dash, "-")
    return escape(s).replace("\n", "<br/>")


def paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(pdf_safe(text), style)


def register_fonts() -> None:
    regular_path = Path(findfont("DejaVu Sans"))
    bold_path = Path(findfont(FontProperties(family="DejaVu Sans", weight="bold")))
    italic_path = Path(findfont(FontProperties(family="DejaVu Sans", style="oblique")))
    pdfmetrics.registerFont(TTFont("DV", str(regular_path)))
    pdfmetrics.registerFont(TTFont("DV-Bold", str(bold_path)))
    pdfmetrics.registerFont(TTFont("DV-Italic", str(italic_path)))
    pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-Bold", italic="DV-Italic", boldItalic="DV-Bold")


class AuditDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name != "AuditH1":
            return
        title = flowable.getPlainText()
        if title == "Sommaire":
            return
        level = 0
        key = f"section-{self.page}-{len(title)}-{abs(hash(title)) % 1000000}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level, closed=False)
        self.notify("TOCEntry", (level, title, self.page))


def on_page(canvas, doc) -> None:
    canvas.saveState()
    width, height = landscape(A4)
    canvas.setStrokeColor(colors.HexColor("#C9D3DF"))
    canvas.setLineWidth(.5)
    if doc.page > 1:
        canvas.line(16 * mm, height - 13 * mm, width - 16 * mm, height - 13 * mm)
        canvas.setFont("DV", 7)
        canvas.setFillColor(GRAY)
        canvas.drawString(16 * mm, height - 10 * mm, "UNIVERSAL_LOG - audit clinique multiaxial PDAC")
        canvas.drawRightString(width - 16 * mm, height - 10 * mm, "17 novembre 2026")
    canvas.line(16 * mm, 12 * mm, width - 16 * mm, 12 * mm)
    canvas.setFont("DV", 7)
    canvas.setFillColor(GRAY)
    canvas.drawString(16 * mm, 8 * mm, "Analyse exploratoire - aucune conclusion thérapeutique individuelle")
    canvas.drawRightString(width - 16 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def add_heading(story, title: str, level: int = 1) -> None:
    style = STYLES["AuditH1"] if level == 1 else STYLES["AuditH2"]
    story.append(Paragraph(pdf_safe(title), style))


def add_body(story, content: str, style: str = "AuditBody") -> None:
    story.append(Paragraph(pdf_safe(content), STYLES[style]))


def make_table(data, widths, font_size=7.2, repeat=1, row_colors=True, highlight_rows=None):
    wrapped = []
    cell_style = ParagraphStyle("DynamicTableCell", parent=STYLES["AuditTableCell"],
                                fontSize=font_size, leading=font_size + 1.4)
    header_style = ParagraphStyle("DynamicTableHeader", parent=STYLES["AuditTableHeader"],
                                  fontSize=font_size, leading=font_size + 1.4)
    for row_i, row in enumerate(data):
        row_style = header_style if row_i == 0 else cell_style
        wrapped.append([cell if isinstance(cell, Paragraph) else Paragraph(pdf_safe(cell), row_style)
                        for cell in row])
    table = LongTable(wrapped, colWidths=widths, repeatRows=repeat, hAlign="LEFT", splitByRow=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "DV-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DV"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 1.4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#CAD2DC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if row_colors:
        for i in range(1, len(data)):
            if i % 2 == 0:
                commands.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))
    for row in (highlight_rows or []):
        commands.append(("BACKGROUND", (0, row), (-1, row), GREEN))
    table.setStyle(TableStyle(commands))
    return table


def read_csv(name: str, folder: Path) -> pd.DataFrame:
    return pd.read_csv(folder / name, keep_default_na=False)


def build_attachments() -> list[tuple[str, Path]]:
    items = [
        ("scan_primary_44.py", HERE / "pdac_multiaxis_resistance.py"),
        ("scan_extended_57.py", HERE / "pdac_multiaxis_resistance_all57.py"),
        ("dose_sensitivity.py", HERE / "analyze_low_dose_internal_sensitivity.py"),
        ("pdf_builder.py", Path(__file__).resolve()),
        ("universal_pipeline_v5_9_4.py", PROJECT_ROOT / "UNIVERSAL_LOG_v5.9.4.py"),
        ("universal_pipeline_v6_cohen_snapshot.py", PROJECT_ROOT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"),
        ("TLog_theory_source.txt", PROJECT_ROOT / "TLog.txt"),
        ("LICENSE_MIT.txt", PROJECT_ROOT / "LICENSE"),
        ("LICENSE_CC_BY_4_0.txt", PROJECT_ROOT / "LICENSE-CC-BY-4.0.txt"),
        ("source_table_high_dose_44.csv", RAW_DIR / "clinical_high_dose_44.csv"),
        ("source_table_low_dose_13.csv", RAW_DIR / "clinical_lower_dose_13.csv"),
        ("source_supplementary_tables.xlsx", DATA_DIR / "41591_2026_4537_MOESM3_ESM.xlsx"),
        ("primary_matrix_44.csv", RESULTS_44 / "controls_by_flows_all_tests.csv"),
        ("primary_heatmap_44.png", RESULTS_44 / "controls_by_flows_heatmap.png"),
        ("primary_coverage_44.csv", RESULTS_44 / "field_coverage.csv"),
        ("primary_patients_44.csv", RESULTS_44 / "patient_level_normalized_44.csv"),
        ("primary_posthoc_tp53_model_44.csv", RESULTS_44 / "posthoc_TP53_eot_vaf_adjusted.csv"),
        ("primary_report_44.md", RESULTS_44 / "REPORT_MULTIAxis_PDac_v1.md"),
        ("extended_matrix_57.csv", RESULTS_57 / "controls_by_flows_all_tests.csv"),
        ("extended_report_57.md", RESULTS_57 / "REPORT_MULTIAxis_PDac_v1.md"),
        ("normalized_patients_57.csv", RESULTS_57 / "patient_level_normalized_57.csv"),
        ("field_coverage_57.csv", RESULTS_57 / "field_coverage.csv"),
        ("field_coverage_57.png", RESULTS_57 / "field_coverage_57.png"),
        ("heatmap_57.png", RESULTS_57 / "controls_by_flows_heatmap.png"),
        ("posthoc_tp53_model_57.csv", RESULTS_57 / "posthoc_TP53_eot_vaf_adjusted.csv"),
        ("dose_sensitivity_table.csv", RESULTS_LOW / "tp53_krasamp_by_dose_stratum.csv"),
        ("dose_sensitivity_patients.csv", RESULTS_LOW / "patient_level_57_tp53_krasamp.csv"),
        ("dose_sensitivity_report.md", RESULTS_LOW / "ADDENDUM_SENSIBILITE_INTERNE_DOSE.md"),
        ("manifest_primary_44.json", RESULTS_44 / "manifest.json"),
        ("manifest_extended_57.json", RESULTS_57 / "manifest.json"),
        ("manifest_dose_sensitivity.json", RESULTS_LOW / "manifest.json"),
        ("external_g12c_scan.py", HERE.parent / "external_validation_g12c" / "analyze_g12c_external.py"),
        ("external_g12c_source_supplement.xlsx", HERE.parent / "external_validation_g12c" / "supplemental_table_1_krasi_g12c_pdac_gi.xlsx"),
        ("external_g12c_all_source_rows.csv", RESULTS_G12C / "source_supplement_all_rows.csv"),
        ("external_g12c_pdac_variant_rows.csv", RESULTS_G12C / "pdac_22_variant_rows_normalized.csv"),
        ("external_g12c_patient_table_22.csv", RESULTS_G12C / "patient_level_external_22.csv"),
        ("external_g12c_controls_by_flows_66.csv", RESULTS_G12C / "controls_by_flows_external_22.csv"),
        ("external_g12c_field_coverage.csv", RESULTS_G12C / "field_coverage_external_22.csv"),
        ("external_g12c_primary_contingency.csv", RESULTS_G12C / "primary_cross_moa_contingency.csv"),
        ("external_g12c_primary_contrast.json", RESULTS_G12C / "primary_cross_moa_contrast.json"),
        ("external_g12c_report.md", RESULTS_G12C / "REPORT_EXTERNAL_G12C_CROSS_MOA.md"),
        ("external_g12c_heatmap.png", RESULTS_G12C / "controls_by_flows_external_22_heatmap.png"),
        ("manifest_external_g12c.json", RESULTS_G12C / "manifest.json"),
        ("GSE279749_analysis.py", HERE.parent / "candidate_combination_g12d_parp" / "analyze_GSE279749_published_candidate.py"),
        ("GSE279749_family.soft.gz", SOURCE_GEO / "GSE279749_family.soft.gz"),
        ("GSE279749_cell_line_FPKM.txt.gz", SOURCE_GEO / "GSE279749_gene_fpkm_cell_lines.txt.gz"),
        ("GSE279749_PDX_FPKM.txt.gz", SOURCE_GEO / "GSE279749_gene_fpkm_PDX.txt.gz"),
        ("GSE279749_sample_metadata.csv", RESULTS_GEO / "GSE279749_sample_metadata.csv"),
        ("GSE279749_cell_HR_log2FPKM.csv", RESULTS_GEO / "cell_line_HR_expression_log2FPKM.csv"),
        ("GSE279749_PDX_HR_log2FPKM.csv", RESULTS_GEO / "PDX_HR_expression_log2FPKM.csv"),
        ("GSE279749_mapping_assumptions.csv", RESULTS_GEO / "GSE279749_mapping_assumptions.csv"),
        ("GSE279749_controls_by_flows.csv", RESULTS_GEO / "controls_by_flows_HR_candidate.csv"),
        ("GSE279749_HR_effects.png", RESULTS_GEO / "HR_gene_effects_GSE279749.png"),
        ("GSE279749_report.md", RESULTS_GEO / "REPORT_GSE279749_HR_candidate.md"),
        ("manifest_GSE279749.json", RESULTS_GEO / "manifest.json"),
    ]
    missing = [str(path) for _, path in items if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing PDF attachment input(s): " + "; ".join(missing))
    return items


def create_story() -> list:
    global STYLES
    base = getSampleStyleSheet()
    STYLES = {
        "AuditTitle": ParagraphStyle("AuditTitle", parent=base["Title"], fontName="DV-Bold", fontSize=26,
                                      leading=31, textColor=BLUE, alignment=TA_LEFT, spaceAfter=12),
        "AuditSubTitle": ParagraphStyle("AuditSubTitle", parent=base["Normal"], fontName="DV", fontSize=12,
                                         leading=17, textColor=GRAY, alignment=TA_LEFT, spaceAfter=10),
        "AuditH1": ParagraphStyle("AuditH1", parent=base["Heading1"], fontName="DV-Bold", fontSize=16,
                                  leading=20, textColor=BLUE, spaceBefore=8, spaceAfter=8, keepWithNext=True),
        "AuditH2": ParagraphStyle("AuditH2", parent=base["Heading2"], fontName="DV-Bold", fontSize=10.5,
                                  leading=14, textColor=BLUE2, spaceBefore=7, spaceAfter=5, keepWithNext=True),
        "AuditBody": ParagraphStyle("AuditBody", parent=base["BodyText"], fontName="DV", fontSize=9,
                                     leading=13, textColor=colors.HexColor("#202A35"), spaceAfter=6),
        "AuditSmall": ParagraphStyle("AuditSmall", parent=base["BodyText"], fontName="DV", fontSize=7.2,
                                      leading=9.3, textColor=colors.HexColor("#202A35"), spaceAfter=3),
        "AuditNote": ParagraphStyle("AuditNote", parent=base["BodyText"], fontName="DV-Italic", fontSize=8.5,
                                     leading=12, textColor=GRAY, leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=7),
        "AuditCode": ParagraphStyle("AuditCode", parent=base["Code"], fontName="Courier", fontSize=7.2,
                                     leading=10, backColor=LIGHT_GRAY, borderColor=colors.HexColor("#CAD2DC"),
                                     borderWidth=.5, borderPadding=7, spaceBefore=4, spaceAfter=8),
        "AuditTOC": ParagraphStyle("AuditTOC", parent=base["Normal"], fontName="DV", fontSize=9,
                                    leading=13, leftIndent=10, firstLineIndent=-10, spaceAfter=3),
        "AuditTableCell": ParagraphStyle("AuditTableCell", parent=base["Normal"], fontName="DV", fontSize=7,
                                          leading=8.5, textColor=colors.HexColor("#202A35"), splitLongWords=1,
                                          spaceAfter=0, spaceBefore=0),
        "AuditTableHeader": ParagraphStyle("AuditTableHeader", parent=base["Normal"], fontName="DV-Bold", fontSize=7,
                                           leading=8.5, textColor=colors.white, splitLongWords=1,
                                           spaceAfter=0, spaceBefore=0),
    }

    m44 = json.loads((RESULTS_44 / "manifest.json").read_text(encoding="utf-8"))
    m57 = json.loads((RESULTS_57 / "manifest.json").read_text(encoding="utf-8"))
    ml = json.loads((RESULTS_LOW / "manifest.json").read_text(encoding="utf-8"))
    mg = json.loads((RESULTS_G12C / "manifest.json").read_text(encoding="utf-8"))
    mgeo = json.loads((RESULTS_GEO / "manifest.json").read_text(encoding="utf-8"))
    report57 = (RESULTS_57 / "REPORT_MULTIAxis_PDac_v1.md").read_text(encoding="utf-8")
    tests = read_csv("controls_by_flows_all_tests.csv", RESULTS_57)
    coverage = read_csv("field_coverage.csv", RESULTS_57)
    dose = read_csv("tp53_krasamp_by_dose_stratum.csv", RESULTS_LOW)
    tests["q_num"] = pd.to_numeric(tests["q_bh_global_estimable"], errors="coerce")
    tests["p_num"] = pd.to_numeric(tests["p_value"], errors="coerce")
    tests = tests.sort_values(["q_num", "p_num"], na_position="last", kind="stable")
    sig_tests = tests[tests["q_num"] < 0.05]
    tp53_amp44 = pd.read_csv(RESULTS_44 / "controls_by_flows_all_tests.csv")
    tp53_amp44_row = tp53_amp44[(tp53_amp44.control == "baseline_tp53") &
                                (tp53_amp44.flow == "acquired_kras_amp")].iloc[0]
    tp53_amp57 = pd.read_csv(RESULTS_57 / "controls_by_flows_all_tests.csv")
    tp53_amp57_row = tp53_amp57[(tp53_amp57.control == "baseline_tp53") &
                                (tp53_amp57.flow == "acquired_kras_amp")].iloc[0]

    story = []
    # Cover
    story += [Spacer(1, 17 * mm), Paragraph("Addendum d’audit", STYLES["AuditTitle"]),
              Paragraph("Analyse multiaxiale de résistance au daraxonrasib dans le cancer du pancréas", STYLES["AuditSubTitle"]),
              Spacer(1, 6 * mm)]
    coverbox = Table([
        [Paragraph("Résultat clé", STYLES["AuditH2"])],
        [Paragraph(f"Scan daraxonrasib: 57 patients, 112 comparaisons prévues, 106 estimables, 7 q<0,05. Scan croisé G12C: 22 patients, 66 comparaisons, 65 estimables, 0 q<0,05. RNA-seq MRTX1133+PARP: 9 prévues, 5 estimables, 0 q<0,05.", STYLES["AuditBody"])],
        [Paragraph("Aucune preuve de remède, de causalité ni de biomarqueur clinique validé n’est obtenue. L’hypothèse TP53–KRAS ne se réplique pas statistiquement dans la petite cohorte G12C; le marqueur HR RNA-seq est partiellement absent et hétérogène.", STYLES["AuditBody"])],
    ], colWidths=[245 * mm])
    coverbox.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE), ("BOX", (0, 0), (-1, -1), 1, BLUE2),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [coverbox, Spacer(1, 9 * mm)]
    add_body(story, "Date d’exécution : 17 novembre 2026. Le document réunit le scan daraxonrasib à 160-300 mg, son extension interne <=120 mg, un test exploratoire de transférabilité sous adagrasib/sotorasib et une relecture RNA-seq ciblée d’une combinaison préclinique KRAS G12D + PARP. Les prélèvements répétés restent liés au même patient/souris/culture.")
    add_body(story, "Objet : documenter ce qui a été calculé, distinguer les faits de l’étude des résultats exploratoires produits par le pipeline, conserver les choix méthodologiques et fournir les éléments exacts de reproduction.")
    add_body(story, "Ce PDF contient le rapport, les graphiques et la matrice complète. Les scripts, tableaux de données, rapports machine lisibles, manifeste et supplément original sont également intégrés comme pièces jointes exactes au PDF. Leur SHA-256 apparaît à la fin.", "AuditNote")
    add_body(story, "Licence du projet selon le choix antérieur : code MIT; documentation et résultats CC BY 4.0.", "AuditSmall")
    story.append(PageBreak())

    # Contents
    add_heading(story, "Sommaire", 1)
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="DV-Bold", fontSize=9, leading=13, textColor=BLUE, leftIndent=0, firstLineIndent=0, spaceBefore=4),
        ParagraphStyle("TOC1", fontName="DV", fontSize=8, leading=11, textColor=GRAY, leftIndent=13, firstLineIndent=0),
    ]
    story += [toc, PageBreak()]

    # Executive summary and source facts
    add_heading(story, "1. Résumé et portée", 1)
    add_body(story, "Ce travail ajoute un module compagnon à axes typés pour cartographier les associations entre des contrôles cliniques/génomiques et des flux de ctDNA ou d’altérations acquises. Il ne modifie pas ni ne valide à lui seul le code universel principal. Il ne cherche pas un seuil T0/TLog dans des étapes de prélèvement inégalement espacées.")
    summary_rows = [
        ["Analyse", "Unité", "Contrôles", "Flux", "Prévus", "Estimables", "q < 0,05", "q TP53-KRAS AMP"],
        ["Cohorte 160-300 mg", "44 patients", "7", "14", "98", "91", "4", f"{tp53_amp44_row.q_bh_global_estimable:.4f}"],
        ["Extension dose <=120 mg", "57 patients", "8", "14", "112", "106", "7", f"{tp53_amp57_row.q_bh_global_estimable:.4f}"],
        ["Transfert G12C externe", "22 patients", "6", "11", str(mg["statistics"]["planned_tests"]), str(mg["statistics"]["estimable_tests"]), str(len(pd.read_csv(RESULTS_G12C / "controls_by_flows_external_22.csv").query("q_bh_global_estimable < 0.05"))), "1.0000"],
        ["Relecture HR RNA-seq G12D", "30 colonnes GEO; indépendance à confirmer", "3", "3", "9", "5", str(int((pd.read_csv(RESULTS_GEO / "controls_by_flows_HR_candidate.csv")["q_bh_over_estimable_of_9_planned"] < .05).sum())), "n.a."],
    ]
    story.append(make_table(summary_rows, [112, 65, 52, 42, 48, 54, 50, 90], font_size=7.2))
    story.append(Spacer(1, 5 * mm))
    add_heading(story, "Faits rapportés par l’article", 2)
    add_body(story, "L’article source décrit 44 patients avec PDAC métastatique traités à 160-300 mg, ayant eu un bénéfice initial puis une progression; les échantillons ctDNA avant traitement et à la progression sont appariés. Les auteurs rapportent des altérations de voies RAS chez 26/44, dont amplification KRAS chez 16/44. Le supplément contient une strate supplémentaire de 13 patients à dose <=120 mg.")
    add_body(story, "L’article rapporte aussi une association brute entre TP53 prétraitement et amplification KRAS acquise : 15/32 TP53-mut contre 1/12 TP53-WT, p = 0,03 par Fisher. Cette observation publiée n’est pas une validation indépendante de notre scan, car elle provient des mêmes patients.")
    add_body(story, "L’article présente des combinaisons soutenues par des modèles précliniques, notamment des stratégies ciblant des voies RTK ou de réponse aux dommages de l’ADN. Ces résultats précliniques ne constituent pas une recommandation de traitement pour une personne.", "AuditNote")
    add_heading(story, "Repères pour les lecteurs", 2)
    glossary = [
        ["Terme", "Sens simple"],
        ["ctDNA", "Fragments d’ADN tumoral circulant dans le sang; quantité observée influencée par la maladie et le relargage tumoral."],
        ["VAF", "Fraction des lectures de séquençage portant une variante; elle dépend aussi de la couverture et du prélèvement."],
        ["p et q BH", "La p mesure la compatibilité des données avec un modèle statistique nul. q BH ajuste la multiplicité sur la famille de tests déclarée; ni p ni q ne prouvent une cause."],
        ["Delta", "Différence entre deux stades de prélèvement. Sans jours écoulés communs, ce n’est pas une vitesse temporelle."],
    ]
    story.append(make_table(glossary, [70, 450], font_size=7.2))
    story.append(PageBreak())

    # Questions and methods
    add_heading(story, "2. Question, données et décisions d’analyse", 1)
    add_body(story, "Question exploratoire : parmi les échantillons disponibles, quelles associations simples entre chaque contrôle défini et chaque flux génomique/ctDNA sont compatibles avec les données, en gardant le patient comme unité statistique?")
    decisions = [
        ["Décision documentée", "Motif et effet sur l’interprétation"],
        ["Une ligne = un patient", "Les stades prétraitement, sous traitement et fin de traitement restent des mesures répétées dans le même bloc patient."],
        ["Statuts de détection conservés", "Not detected, not tested et missing ne sont pas remplacés par zéro; les comparaisons numériques utilisent les valeurs détectées."],
        ["Contrôles et flux typés", "Variables catégorielles et continues sont distinguées; la dose continue et sa strate sont deux codages corrélés et non deux preuves indépendantes."],
        ["Famille de tests déclarée", "La correction Benjamini-Hochberg porte sur toutes les comparaisons estimables de la grille, pas seulement sur les résultats intéressants."],
        ["Abstention T0/TLog", "Les prélèvements on-treatment surviennent à des cycles différents et les patients sont des unités indépendantes; aucune trajectoire temporelle homogène n’est disponible."],
        ["Analyse post-scan séparée", "Le modèle ajusté TP53/VAF/dose est déclenché par le scan; sa p nominale n’est pas une confirmation préenregistrée."],
    ]
    story.append(make_table(decisions, [140, 400], font_size=7.6))
    add_heading(story, "Contrôles du scan étendu", 2)
    ctrls = json.loads((RESULTS_57 / "manifest.json").read_text(encoding="utf-8"))["controls"]
    control_table = [["Contrôle", "Type", "Rôle déclaré"]] + [[x["name"], x["type"], x["status"]] for x in ctrls]
    story.append(make_table(control_table, [150, 75, 315], font_size=7.2))
    add_heading(story, "Flux du scan étendu", 2)
    fls = json.loads((RESULTS_57 / "manifest.json").read_text(encoding="utf-8"))["flows"]
    flow_table = [["Flux", "Type", "Rôle déclaré"]] + [[x["name"], x["type"], x["status"]] for x in fls]
    story.append(make_table(flow_table, [155, 75, 310], font_size=7.0))
    story.append(PageBreak())

    # Results
    add_heading(story, "3. Résultats du scan étendu à 57 patients", 1)
    add_body(story, "La matrice contient 112 couples contrôle-flux. Six sont non estimables selon les règles du test; 106 p-values entrent dans la correction BH globale. Sept couples ont q < 0,05. Cela ne signifie pas qu’il existe sept biomarqueurs indépendants : plusieurs couples partagent les mêmes mesures de détection ou des variables mathématiquement liées.")
    add_heading(story, "Associations sous q < 0,05", 2)
    sig_rows = [["Contrôle", "Flux", "n", "Statistique / effet", "p", "q BH globale"]]
    for _, r in sig_tests.iterrows():
        effect = f"{r['effect_name']} = {float(r['effect']):.4g}" if str(r.get("effect", "")) not in {"", "nan"} else ""
        sig_rows.append([r["control"], r["flow"], str(int(r["n_patients"])), effect,
                         f"{float(r['p_num']):.4g}", f"{float(r['q_num']):.4g}"])
    story.append(make_table(sig_rows, [100, 145, 35, 185, 55, 75], font_size=7.0))
    story.append(Spacer(1, 4 * mm))
    add_heading(story, "Lecture des signaux", 2)
    add_body(story, "Le lien entre le VAF RAS initial et la variation prétraitement-vers-on-treatment est presque déterministe dans les cas détectés (rho = -0,994). Il est mathématiquement couplé puisque la valeur initiale est utilisée dans le calcul du delta; il ne constitue pas une découverte indépendante.")
    add_body(story, "Les autres associations de détection dépendent du seuil analytique et de la disponibilité du ctDNA. Les liens TP53 qui passent q < 0,05 portent sur la détection du VAF sous traitement et le VAF génomique maximal à fin de traitement/progression. Dans les 57 patients, RAS est détecté sous traitement chez 24/41 TP53-mut et 2/16 TP53-WT; le VAF génomique maximal médian à fin de traitement est 17,06 % chez TP53-mut et 4,58 % chez TP53-WT. Ces observations à la progression peuvent refléter le relargage tumoral d’ADN ou le contexte génomique, pas une résistance causée par TP53.")
    add_body(story, "Le KRAS subtype est associé au VAF RAS mesuré à fin de traitement dans une comparaison globale par rangs; le test ne désigne pas à lui seul quel sous-type diffère ni ne prouve un effet de traitement.")
    add_heading(story, "Résultat TP53 - amplification KRAS", 2)
    add_body(story, f"Dans les 44 patients à dose 160-300 mg, le couple TP53 prétraitement / amplification KRAS acquise a p = {float(tp53_amp44_row.p_value):.4g} et q BH globale = {float(tp53_amp44_row.q_bh_global_estimable):.4g}. Dans les 57 patients réunis, p nominale = {float(tp53_amp57_row.p_value):.4g} mais q BH globale = {float(tp53_amp57_row.q_bh_global_estimable):.4g}. Le signal brut ne franchit donc pas q < 0,05 dans la grille élargie.")
    add_body(story, "Le sous-groupe <=120 mg compte 1/9 TP53-mut et 0/4 TP53-WT avec KRAS AMP; Fisher exact donne p = 1,0. L’OR infini vient de la cellule nulle et n’est pas une estimation stable. Le p nominal groupé à 57 patients ne constitue pas une réplication puisqu’il réutilise les 44 personnes de la première strate.", "AuditNote")
    story.append(PageBreak())

    # Figures
    add_heading(story, "4. Figures et couverture", 1)
    add_body(story, "La carte montre -log10(q) global. Une couleur plus intense indique une association avec une q plus petite, pas une taille d’effet plus grande. Les cellules non estimables apparaissent en blanc.")
    story.append(Image(str(RESULTS_57 / "controls_by_flows_heatmap.png"), width=710, height=290))
    story.append(Spacer(1, 3 * mm))
    add_heading(story, "Couverture des champs", 2)
    add_body(story, "La couverture rapporte le nombre de patients observés et absents/censurés par champ. Elle aide à distinguer une absence de signal d’un champ trop incomplet pour être évalué.")
    story.append(Image(str(RESULTS_57 / "field_coverage_57.png"), width=570, height=350))
    story.append(PageBreak())

    # Internal dose sensitivity and limitations
    add_heading(story, "5. Sensibilité interne par niveau de dose", 1)
    add_body(story, "Analyse ciblée après le scan, avec Fisher exact bilatéral. Les cohortes proviennent du même essai et ne sont pas randomisées entre elles; ce n’est pas une cohorte indépendante.")
    dose_rows = [["Strate", "TP53-mut avec KRAS AMP", "TP53-mut n", "TP53-WT avec KRAS AMP", "TP53-WT n", "OR", "p nominale"]]
    for _, r in dose.iterrows():
        or_text = "inf (cellule nulle)" if str(r["odds_ratio"]) == "inf" else f"{float(r['odds_ratio']):.3g}"
        dose_rows.append([r["dose_stratum"], str(int(r["tp53_mut_kras_amp_n"])), str(int(r["tp53_mut_n"])),
                          str(int(r["tp53_wt_kras_amp_n"])), str(int(r["tp53_wt_n"])), or_text,
                          f"{float(r['fisher_two_sided_p_nominal']):.4g}"])
    story.append(make_table(dose_rows, [105, 95, 55, 95, 55, 85, 70], font_size=7.2))
    story.append(Spacer(1, 4 * mm))
    add_body(story, "Lecture : la strate basse est trop petite pour confirmer ou réfuter l’association. La valeur p = 0,022 dans la strate groupée est nominale et utilise des patients déjà présents dans l’analyse initiale. Le résultat global corrigé du scan à 57 patients reste q = 0,106 pour TP53 - KRAS AMP.")
    add_heading(story, "Limites qui empêchent une conclusion clinique", 2)
    limits = [
        ["Limite", "Conséquence"],
        ["Échantillon sélectionné sur progression après bénéfice initial", "Pas de groupe comparateur durable sans progression; impossible d’évaluer une prédiction de résistance dans la population traitée."],
        ["Une seule étude, deux strates de dose", "Aucune validation externe; les patients de la strate dose basse ne sont pas indépendants de l’étude source."],
        ["Données ctDNA et couverture analytique", "Non-détection dépend du shedding, de la profondeur, des tests et de la fraction tumorale."],
        ["Mesures répétées et intervalles variables", "Les deltas sont des différences d’étapes, pas des vitesses par jour ni des séries temporelles communes."],
        ["Variables et tests corrélés", "BH couvre la famille estimable déclarée, mais ne supprime ni confusion, ni sélection préalable, ni couplage mathématique."],
        ["Module compagnon", "Cette exécution ne prouve ni l’universalité du pipeline, ni la formule TLog, ni une causalité biologique."],
    ]
    story.append(make_table(limits, [180, 360], font_size=7.5))
    story.append(PageBreak())

    # Cross-MOA transportability attempt in an independent published cohort
    add_heading(story, "6. Cohorte externe: test exploratoire de transférabilité KRAS G12C", 1)
    ext = pd.read_csv(RESULTS_G12C / "controls_by_flows_external_22.csv")
    ext_patients = pd.read_csv(RESULTS_G12C / "patient_level_external_22.csv")
    ext_primary = json.loads((RESULTS_G12C / "primary_cross_moa_contrast.json").read_text(encoding="utf-8"))
    ext_p = float(ext_primary["p_nominal"])
    ext_q = float(ext_primary["q_bh_global_in_exploratory_grid"])
    ext_event_ids = ", ".join(ext_primary["gain_or_amplification_patient_ids"])
    ext_amp_ids = ", ".join(ext_primary["amplification_only_patient_ids"])
    ext_sig = int((pd.to_numeric(ext["q_bh_global_estimable"], errors="coerce") < .05).sum())
    ext_top = ext.sort_values("q_bh_global_estimable").iloc[0]
    add_body(story, "Cette cohorte publiée distincte comprend 22 patients PDAC traités par adagrasib ou sotorasib, des inhibiteurs sélectifs KRAS G12C. L’article rapporte 18 réponses initiales PR/SD suivies d’une résistance acquise et 4 progressions primaires. Ce test examine la transférabilité d’une association vers ces médicaments et cette cohorte; il ne s’agit pas d’une validation daraxonrasib à traitement identique.")
    add_heading(story, "Résultat principal préspécifié pour cette analyse", 2)
    add_body(story, f"La grille patient-level comporte {mg['statistics']['planned_tests']} comparaisons contrôle × flux; {mg['statistics']['estimable_tests']} sont estimables et {ext_sig} franchissent q BH globale < 0,05. Pour les 4 patients avec gain/amplification KRAS listé ({ext_event_ids}; amplification seule: {ext_amp_ids}), la présence d’un variant TP53 prétraitement listé est observée chez 3/18 patients TP53-liste et 1/4 sans variant TP53 prétraitement listé. Fisher bilatéral donne OR = {ext_primary['odds_ratio_or_effect']:.2f}, p = {ext_p:.3f}; q globale = {ext_q:.3f}. Dans ce tableau, cette association ne se réplique donc pas statistiquement.")
    add_body(story, "La catégorie ‘sans variant TP53 prétraitement listé’ n’équivaut pas à TP53 sauvage; de même, un événement absent du supplément signifie ‘non listé’, pas ‘testé et négatif’. L’échantillon de 22 patients est trop petit pour interpréter l’absence de significativité comme une preuve d’absence d’effet.", "AuditNote")
    add_heading(story, "Flux et contrôles explorés", 2)
    add_body(story, "Six contrôles candidats (traitement, réponse, TP53 prétraitement, disponibilité et VAF KRAS initiales, plateforme) ont été croisés avec onze flux (altérations KRAS copie nombre, événements acquis listés, mutations RAS/PI3K/RTK, VAF KRAS fin de traitement et différence pré-fin). Les tests unitaires restent bloqués par patient. La carte montre les q globales; elle ne montre pas des tailles d’effet.")
    story.append(Image(str(RESULTS_G12C / "controls_by_flows_external_22_heatmap.png"), width=700, height=285))
    story.append(Spacer(1, 2 * mm))
    add_body(story, f"La plus petite q de la grille est {float(ext_top['q_bh_global_estimable']):.4f} pour {ext_top['control']} × {ext_top['flow']} (rho de Spearman = {float(ext_top['effect']):.3f}, p = {float(ext_top['p_value']):.3f}); ce lien relie deux mesures de VAF sur le même oncogène et ne démontre pas un mécanisme de résistance. Aucun seuil temporel n’est calculé: le supplément ne fournit ici que des étapes prétraitement et fin de traitement, sans axe de temps commun.")
    add_body(story, "Champ logiciel: cette application réutilise le moteur de tests patient-level du module multiaxial compagnon. Elle n’exécute pas le cœur universel complet, les 29 estimateurs ni TLog; elle ne prouve donc pas le pipeline entier ni son universalité.", "AuditNote")
    add_heading(story, "Règle de décision pour poursuivre vers une piste thérapeutique", 2)
    add_body(story, "Ne pas transformer le résultat clinique observationnel en combinaison à administrer. La prochaine expérience utile est un test contrôlé, préenregistré, dans des organoïdes/PDX PDAC: stratifier KRAS G12C/G12D et statut TP53, mesurer baseline et réponse, tester monothérapie contre une combinaison motivée par la résistance, inclure témoins et réplications biologiques, suivre viabilité/taille tumorale et toxicité, puis faire relire le plan par un laboratoire/oncologue. Le supplément ici justifie la question de résistance hétérogène; il ne choisit pas à lui seul le médicament de combinaison.")
    story.append(Paragraph("Source principale externe: Dilly et al., Cancer Discovery 2024, <link href='https://doi.org/10.1158/2159-8290.CD-24-0177' color='#2878B5'>doi:10.1158/2159-8290.CD-24-0177</link>. Données supplémentaires: AACR Figshare, CC BY, <link href='https://doi.org/10.1158/2159-8290.32699721' color='#2878B5'>doi:10.1158/2159-8290.32699721</link>.", STYLES["AuditSmall"]))
    story.append(PageBreak())

    # Published preclinical candidate transcriptomic recheck
    add_heading(story, "7. Relecture RNA-seq d’une piste publiée KRAS G12D + PARP", 1)
    geo = pd.read_csv(RESULTS_GEO / "controls_by_flows_HR_candidate.csv")
    geo_manifest = json.loads((RESULTS_GEO / "manifest.json").read_text(encoding="utf-8"))
    geo_cell = geo[(geo["control"].str.startswith("MRTX1133")) & geo["flow"].eq("RPA2")].iloc[0]
    geo_cell_q = float(geo_cell["q_bh_over_estimable_of_9_planned"])
    geo_fig = RESULTS_GEO / "HR_gene_effects_GSE279749.png"
    add_body(story, "Une étude préclinique 2026 rapporte une synergie du KRAS G12D inhibiteur MRTX1133 avec l’olaparib dans des lignées PDAC et des modèles de xénogreffe/résistance. C’est une piste existante dans la littérature, pas une découverte de cette analyse, et le résultat ne prouve pas un bénéfice clinique humain.")
    add_body(story, "J’ai réexaminé les matrices publiques GSE279749 en croisant trois bras/contrôles disponibles avec les trois flux HR que l’article nomme (BRCA1, RAD51, RPA2), sur log2(FPKM+1), Cohen d et permutations exactes. Le plan avait 9 couples; 5 sont estimables, 4 restent explicitement manquants, 0 a q<0,05. Les tests et effets sont conditionnels à l’indépendance/échangeabilité des colonnes GEO, qui n’est pas confirmée.")
    add_heading(story, "Constat de couverture et résultat cellule", 2)
    add_body(story, f"Le fichier GEO de lignées cellulaires ne contient que RPA2 parmi les trois gènes prévus; BRCA1 et RAD51 n’y figurent pas. Sous le mapping de préfixes provisoire, RPA2: différence moyenne MRTX1133−véhicule = {float(geo_cell['treatment_minus_control_mean_log2FPKM']):.3f} log2(FPKM+1), Cohen d agrégé = {float(geo_cell['Cohens_d_pooled']):.3f}, p exact bloqué par lignée = {float(geo_cell['p_exact_blocked']):.3f}, q BH sur les tests estimables = {geo_cell_q:.3f}. Ces statistiques supposent des colonnes échangeables; les Méthodes de l’article parlent de cultures en double, alors que GEO liste trois colonnes par condition. Les lignées ne sont pas cohérentes sous ce mapping: deux baissent, SW1990 augmente. Le fichier PDX contient les trois gènes, mais compare seulement véhicule (n=3) à combinaison (n=3) sous un mapping positionnel provisoire, sans bras monothérapie: cette RNA-seq ne permet pas d’estimer une interaction/synergie.")
    story.append(Image(str(geo_fig), width=620, height=250))
    story.append(Spacer(1, 2 * mm))
    add_body(story, "Limite d’interprétation : il s’agit des fichiers de l’étude ayant proposé le mécanisme, pas d’une cohorte indépendante. Les préfixes A/P/C/S9, la relation des suffixes de traitement aux GSM et l’affectation PDX p1-p6 sont des hypothèses consignées dans le tableau joint GSE279749_mapping_assumptions.csv. Les gènes manquants restent non estimables et ne sont jamais imputés à zéro. Les PDX sont au point final, sans identifiant de modèle directement lié aux colonnes GEO. Cette relecture partielle ne confirme ni ne réfute seule l’efficacité publiée.", "AuditNote")
    add_heading(story, "Piste suivante mieux identifiée", 2)
    add_body(story, "Les métadonnées GEO de GSE309596 listent 12 échantillons, 3 par bras: véhicule, MRTX1133, olaparib et combinaison. L’unité biologique et la correspondance échantillon-animal doivent être vérifiées dans les métadonnées détaillées et l’article avant agrégation. Si les affectations et l’indépendance sont confirmées, ces quatre bras forment un plan factoriel 2×2 à un point final; le pseudobulk doit utiliser l’animal/unité biologique confirmée, jamais la cellule comme réplicat. N=3 par bras reste faible et ne donne pas un TLog temporel.")
    add_body(story, "Pour faire travailler réellement TLog et les 29 estimateurs dans un contexte thérapeutique, l’étape expérimentale serait un suivi longitudinal de PDO/PDX avec mesures répétées de viabilité/taille, activité RAS-ERK et marqueurs HR sous véhicule, chaque monothérapie et combinaison. Il faudra définir des temps et contrôles avant l’expérience; les données GEO actuelles sont ponctuelles.")
    story.append(Paragraph("Sources: étude <link href='https://doi.org/10.1038/s41467-026-69695-4' color='#2878B5'>Xu et al., Nature Communications 2026</link>; <link href='https://doi.org/10.1038/s41467-026-72371-2' color='#2878B5'>correction auteur du 22 avril 2026</link> (image DAPI du panneau 1c corrigée); GEO <link href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279749' color='#2878B5'>GSE279749</link> et <link href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE309596' color='#2878B5'>GSE309596</link>.", STYLES["AuditSmall"]))
    story.append(PageBreak())

    # Pipeline status, future protocol and reproducibility
    add_heading(story, "8. Ce que cette analyse valide du pipeline", 1)
    add_body(story, "Résultat technique observé : le module compagnon a parcouru toutes les paires prévues contrôle-flux, conservé les statuts de détection, gardé le patient comme unité, corrigé la famille de tests déclarée et produit matrices, couverture, graphiques, rapport et empreintes. L’exécution utilise le .venv du projet.")
    add_body(story, "Ce n’est pas encore une validation du pipeline universel complet : le module multiaxial est un script compagnon conçu pour ce schéma clinique. Le test ne démontre pas que les 29 estimateurs, le TLog ou leur enchaînement théorique apportent une information utile ou transportable. Les instantanés du noyau v5.9.4, du v6 Cohen, et le texte source TLog.txt sont joints au PDF pour situer le travail; ils n’ont pas été exécutés dans cette analyse. La prochaine étape logicielle est de formaliser un contrat universel de données typées et de comparer, en validation aveugle, les sorties du noyau principal et du compagnon sur les mêmes contrôles/flux.")
    add_heading(story, "Prochain protocole pour avancer vers une piste thérapeutique", 2)
    next_steps = [
        ["Étape", "Exigence minimale"],
        ["1. Validation clinique indépendante", "Cohorte traitée indépendante avec progressors et non-progressors; données patient-level, dates de prélèvements, traitement/dose, statut de détection, couverture de séquençage et issue clinique."],
        ["2. Hypothèse TP53 - KRAS AMP", "Préenregistrer l’unique critère principal, définir le seuil de détection et ajuster les facteurs de charge/shedding avant l’analyse; rapporter effet et intervalle d’incertitude."],
        ["3. Test mécanistique", "Dans modèles PDAC TP53-mut et TP53-WT, tester perturbation de TP53 et apparition d’amplification KRAS sous exposition contrôlée; distinguer corrélation et causalité."],
        ["4. Combinaisons", "Comparer monothérapie et combinaisons uniquement dans modèles précliniques avec réplications, dose-réponse, toxicité et critères d’interaction définis; passer ensuite par validation réglementaire/clinique."],
        ["5. Comparateur simple", "Comparer le pipeline à des modèles standards et à des règles simples sur un jeu aveugle; mesurer erreurs, calibration, faux positifs et abstentions."],
    ]
    story.append(make_table(next_steps, [150, 390], font_size=7.4))
    add_body(story, "Aucune combinaison thérapeutique n’est recommandée aux patients par cette analyse. Pour une personne malade, les décisions relèvent de son équipe d’oncologie et des essais cliniques appropriés.", "AuditNote")
    add_heading(story, "Reproduction", 2)
    story.append(Paragraph(pdf_safe("Depuis la racine du projet Windows :"), STYLES["AuditBody"]))
    story.append(Paragraph(pdf_safe(r".\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\multi_axis_resistance\pdac_multiaxis_resistance_all57.py"), STYLES["AuditCode"]))
    story.append(Paragraph(pdf_safe(r".\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\multi_axis_resistance\analyze_low_dose_internal_sensitivity.py"), STYLES["AuditCode"]))
    story.append(Paragraph(pdf_safe(r".\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\external_validation_g12c\analyze_g12c_external.py"), STYLES["AuditCode"]))
    story.append(Paragraph(pdf_safe(r".\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\candidate_combination_g12d_parp\analyze_GSE279749_published_candidate.py"), STYLES["AuditCode"]))
    add_body(story, "Versions observées dans l’environnement d’analyse : Python " + str(m57["software"]["python"]) + ", pandas " + str(m57["software"]["pandas"]) + ", numpy " + str(m57["software"]["numpy"]) + ". Le scan étendu utilise 9 999 permutations et la graine 20261117; les tests binaires 2x2 utilisent Fisher exact bilatéral.")
    story.append(PageBreak())

    # Complete test matrix appendix
    add_heading(story, "Annexe A. Matrice complète des 112 tests", 1)
    add_body(story, "Les six couples non estimables sont conservés et leur motif apparaît dans la colonne méthode/statut. Les valeurs p et q vides indiquent qu’aucun test inférentiel n’a été retenu pour cette cellule.")
    all_rows = [["Contrôle", "Flux", "n", "Test / statut", "Type d’effet", "Effet", "p", "q BH"]]
    sig_pdf_rows = []
    for _, r in tests.iterrows():
        n = "" if pd.isna(r["n_patients"]) else str(int(r["n_patients"]))
        eff_raw = str(r.get("effect", "")).strip()
        eff = "" if eff_raw in {"", "nan", "None"} else f"{float(eff_raw):.4g}"
        p = "" if pd.isna(r["p_num"]) else f"{float(r['p_num']):.4g}"
        q = "" if pd.isna(r["q_num"]) else f"{float(r['q_num']):.4g}"
        all_rows.append([r["control"], r["flow"], n, r["test"], str(r.get("effect_name", "")), eff, p, q])
        if q and float(r["q_num"]) < 0.05:
            sig_pdf_rows.append(len(all_rows) - 1)
    story.append(make_table(all_rows, [88, 108, 25, 133, 92, 60, 50, 56], font_size=6.0, highlight_rows=sig_pdf_rows))
    story.append(PageBreak())

    # Coverage and output inventory
    add_heading(story, "Annexe B. Couverture de chaque champ", 1)
    cov_rows = [["Champ", "Rôle", "Type", "Observés", "Absents/censurés", "Distincts", "Description"]]
    for _, r in coverage.iterrows():
        cov_rows.append([r["field"], r["role"], r["type"], str(int(r["n_observed"])),
                         str(int(r["n_missing_or_censored"])), str(int(r["distinct_nonmissing"])), r["description"]])
    story.append(make_table(cov_rows, [125, 43, 50, 45, 70, 45, 230], font_size=6.4))
    story.append(Spacer(1, 5 * mm))
    story.append(PageBreak())
    add_heading(story, "Annexe C. Matrice complète des 66 contrôles × flux externes", 1)
    add_body(story, "La famille BH couvre les 65 tests estimables. Les absences du supplément sont codées comme ‘non listé’ pour cette analyse exploratoire; elles ne sont pas des négatifs confirmés. Aucun couple ne franchit q < 0,05.")
    ext_tests = pd.read_csv(RESULTS_G12C / "controls_by_flows_external_22.csv")
    ext_tests["q_num"] = pd.to_numeric(ext_tests["q_bh_global_estimable"], errors="coerce")
    ext_tests["p_num"] = pd.to_numeric(ext_tests["p_value"], errors="coerce")
    ext_tests = ext_tests.sort_values(["q_num", "p_num"], na_position="last", kind="stable")
    ext_matrix_rows = [["Contrôle", "Flux", "n", "Test / statut", "Effet", "Valeur", "p", "q BH"]]
    for _, r in ext_tests.iterrows():
        n = "" if pd.isna(r["n_patients"]) else str(int(r["n_patients"]))
        effect_name = str(r.get("effect_name", ""))
        effect_value = "" if pd.isna(r.get("effect", np.nan)) else f"{float(r['effect']):.4g}"
        pval = "" if pd.isna(r["p_num"]) else f"{float(r['p_num']):.4g}"
        qval = "" if pd.isna(r["q_num"]) else f"{float(r['q_num']):.4g}"
        ext_matrix_rows.append([r["control"], r["flow"], n, r["test"], effect_name, effect_value, pval, qval])
    story.append(make_table(ext_matrix_rows, [96, 126, 25, 137, 105, 50, 47, 47], font_size=5.7))
    story.append(PageBreak())
    add_heading(story, "Annexe D. Résumé patient-level externe", 1)
    add_body(story, "Tableau de lecture condensé. Le fichier CSV joint conserve toutes les colonnes dérivées pour les 22 patients; le classeur original et le tableau de variants normalisé sont aussi joints comme pièces exactes.")
    patient_rows = [["Patient", "Traitement", "Réponse", "TP53 prétraitement listé", "KRAS G12C VAF pré (%)", "VAF fin (%)", "KRAS CN nouveau listé", "Nouvelles mutations listées"]]
    for _, r in ext_patients.iterrows():
        def fmt(x):
            return "non listé" if pd.isna(x) else f"{float(x):.3g}"
        cn = "Gain/Amp" if r["new_kras_cn_gain_or_amp_listed"] == "yes" else "aucun rapporté"
        patient_rows.append([r["patient_id"], r["treatment"], r["best_response"],
                             "oui" if r["tp53_baseline_variant_listed"] == "yes" else "non listé",
                             fmt(r["baseline_kras_g12c_vaf_pct"]), fmt(r["eot_kras_g12c_vaf_pct"]),
                             cn, str(int(r["n_new_mutation_rows_listed"]))])
    story.append(make_table(patient_rows, [58, 70, 36, 95, 64, 52, 82, 75], font_size=5.8))
    story.append(Spacer(1, 5 * mm))
    story.append(PageBreak())
    add_heading(story, "Annexe E. Matrice complète des 9 contrôles × flux HR", 1)
    add_body(story, "Quatre couples sont non estimables parce que le marqueur est absent de la matrice correspondante; ils restent blancs/non estimables, jamais imputés. La correction BH porte sur les cinq tests calculables.")
    geo_rows = [["Contrôle", "Flux", "n traités / témoins", "Δ moyen log₂ FPKM", "Cohen d", "p exact", "q BH", "Statut"]]
    for _, r in geo.iterrows():
        n = f"{int(r['n_treated'])}/{int(r['n_control'])}" if pd.notna(r["n_treated"]) else ""
        def fmt(value):
            return "" if pd.isna(value) else f"{float(value):.3g}"
        geo_rows.append([r["control"], r["flow"], n, fmt(r["treatment_minus_control_mean_log2FPKM"]),
                         fmt(r["Cohens_d_pooled"]), fmt(r["p_exact_blocked"]),
                         fmt(r["q_bh_over_estimable_of_9_planned"]), r["status"]])
    story.append(make_table(geo_rows, [145, 48, 53, 72, 50, 48, 48, 120], font_size=5.7))
    story.append(PageBreak())
    add_heading(story, "Pièces jointes exactes intégrées au PDF", 2)
    attachments = build_attachments()
    attach_rows = [["Nom intégré", "SHA-256", "Octets"]]
    for name, path in attachments:
        attach_rows.append([name, sha256(path), str(path.stat().st_size)])
    story.append(make_table(attach_rows, [205, 390, 60], font_size=5.8))
    story.append(Spacer(1, 4 * mm))
    add_heading(story, "Sources", 2)
    story.append(Paragraph("Aronchik et al. “Acquired resistance to the RAS(ON) multi-selective inhibitor daraxonrasib guides rational combination therapy strategies in pancreatic cancer.” Nature Medicine, 2026. DOI: 10.1038/s41591-026-04537-w. <link href='https://doi.org/10.1038/s41591-026-04537-w' color='#2878B5'>Article et supplément</link>.", STYLES["AuditBody"]))
    story.append(Paragraph("FDA, “FDA approves daraxonrasib for metastatic pancreatic adenocarcinoma,” 26 août 2026. Cette autorisation clinique concerne des critères d’utilisation définis; elle ne signifie pas guérison. <link href='https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma' color='#2878B5'>Page FDA</link>.", STYLES["AuditBody"]))
    story.append(Paragraph("Dilly et al. “Mechanisms of Resistance to Oncogenic KRAS Inhibition in Pancreatic Cancer.” Cancer Discovery, 2024. DOI: 10.1158/2159-8290.CD-24-0177. <link href='https://doi.org/10.1158/2159-8290.CD-24-0177' color='#2878B5'>Article</link>. Supplément patient-level AACR Figshare, CC BY, DOI: 10.1158/2159-8290.32699721. <link href='https://doi.org/10.1158/2159-8290.32699721' color='#2878B5'>Données</link>.", STYLES["AuditBody"]))
    add_body(story, "Les observations de cet addendum ne remplacent pas les données réglementaires et ne sont pas des conseils médicaux. Elles formulent uniquement des pistes de recherche à valider indépendamment.", "AuditNote")
    return story


def main() -> None:
    register_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if DRAFT_PDF.exists():
        DRAFT_PDF.unlink()
    story = create_story()
    doc = AuditDoc(str(DRAFT_PDF), pagesize=landscape(A4), rightMargin=16 * mm,
                   leftMargin=16 * mm, topMargin=18 * mm, bottomMargin=17 * mm,
                   title="Addendum audit multiaxial PDAC - 17 novembre 2026",
                   author="Projet UNIVERSAL_LOG", subject="Analyse exploratoire patient-level et reproduction")
    doc.multiBuild(story, onFirstPage=on_page, onLaterPages=on_page)

    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(str(DRAFT_PDF)))
    attach_paths = build_attachments()
    for attachment_name, path in attach_paths:
        writer.add_attachment(attachment_name, path.read_bytes())
    writer.add_metadata({
        "/Title": "Addendum d’audit - analyse multiaxiale PDAC",
        "/Author": "Projet UNIVERSAL_LOG",
        "/Subject": "Résistance daraxonrasib; analyse exploratoire, données patient-level, reproductibilité",
        "/Keywords": "PDAC, UNIVERSAL_LOG, audit, ctDNA, TP53, KRAS, reproductibilité",
    })
    with OUTPUT_PDF.open("wb") as f:
        writer.write(f)
    DRAFT_PDF.unlink(missing_ok=True)

    verify = PdfReader(str(OUTPUT_PDF))
    if len(verify.pages) < 8:
        raise ValueError(f"Unexpectedly short audit PDF: {len(verify.pages)} pages")
    attached = verify.attachments
    missing = [name for name, _ in attach_paths if name not in attached]
    if missing:
        raise ValueError(f"PDF attachments missing after write: {missing}")
    text = "\n".join(page.extract_text() or "" for page in verify.pages)
    for required in ["Résultats du scan étendu", "Matrice complète des 112 tests", "Cohorte externe", "Matrice complète des 66", "Relecture RNA-seq", "Matrice complète des 9", "GSE309596", "Aucune preuve de remède", "Sources"]:
        if required.casefold() not in text.casefold():
            raise ValueError(f"Expected PDF text not found after writing: {required}")
    print(json.dumps({"pdf": str(OUTPUT_PDF), "bytes": OUTPUT_PDF.stat().st_size,
                      "sha256": sha256(OUTPUT_PDF), "pages": len(verify.pages),
                      "attachments": len(attached), "attachment_names": sorted(attached)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
