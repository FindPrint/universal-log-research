"""Build V10's readable grouped-panel audit appendix from frozen run outputs."""
from __future__ import annotations

import csv
import argparse
import hashlib
import html
import json
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
TEST_DIR = ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "PANEL_SYNTHETIQUE_VALIDATION_V1"
OUT_DIR = ROOT / "output" / "master_whitepaper_v10"
TMP_DIR = ROOT / "tmp" / "pdfs"
V9_ACTIVE = ROOT / "output" / "master_whitepaper_v9"
V9_ARCHIVED = ROOT / "archive_sources" / "master_whitepaper_v9"
V9_BASE = V9_ARCHIVED if V9_ARCHIVED.is_dir() else V9_ACTIVE
BASE_PDF = V9_BASE / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V9_2026-11-22.pdf"
FINAL_PDF = OUT_DIR / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf"
APPENDIX_PDF = TMP_DIR / "appendix_grouped_panel_v10.pdf"
REPORT_MD = TEST_DIR / "AUDIT_RESULTATS_PANEL_SYNTHETIQUE_V1_FR.md"
PUBLIC_SUMMARY = TEST_DIR / "PUBLIC_VALIDATION_SUMMARY_V1.json"
STATE_PATH = TEST_DIR / "run_state.json"
QA_PATH = TEST_DIR / "validation_results.json"
SUMMARY_CSV = TEST_DIR / "patient_control_summary.csv"
RUNS_DIR = TEST_DIR / "runs"
LOGS_DIR = TEST_DIR / "logs"
PANEL_CSV = TEST_DIR / "inputs" / "synthetic_longitudinal_panel_v1.csv"
HARNESS = TEST_DIR / "run_grouped_panel_validation.py"
SHORT_GATE_SCRIPT = TEST_DIR / "verify_short_core_gate.py"
SHORT_GATE_RESULT = TEST_DIR / "short_core_gate_check.json"
SUMMARY_FIGURE = TEST_DIR / "PANEL_T0_TLOG_HEATMAP_V1.png"
PDF_IMAGE_CACHE = TMP_DIR / "panel_v10_pdf_images"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4g}" if value == value else "indisponible"
    return str(value)


def pdf_ready_image(source: Path, label: str) -> Path:
    """Make an archival PNG readable in the PDF without embedding a huge bitmap."""
    PDF_IMAGE_CACHE.mkdir(parents=True, exist_ok=True)
    destination = PDF_IMAGE_CACHE / f"{label}.jpg"
    if (destination.is_file() and destination.stat().st_size > 0
            and destination.stat().st_mtime >= source.stat().st_mtime):
        return destination
    with PILImage.open(source) as original:
        image = original.convert("RGBA") if "A" in original.getbands() else original.convert("RGB")
        image.thumbnail((1600, 2200), PILImage.Resampling.LANCZOS)
        if image.mode == "RGBA":
            background = PILImage.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        image.save(destination, format="JPEG", quality=88, optimize=True, dpi=(150, 150))
    return destination


def inline(value: str) -> str:
    value = value.replace("—", "-").replace("–", "-").replace("−", "-").replace("×", "x")
    return html.escape(value, quote=False)


def make_table(rows, widths=None, font_size=6.4, repeat=1):
    data = []
    for index, row in enumerate(rows):
        style = ParagraphStyle(
            name=f"Cell{index}", fontName="Helvetica-Bold" if index == 0 else "Helvetica",
            fontSize=font_size, leading=font_size + 1.3,
            textColor=colors.white if index == 0 else colors.HexColor("#17212b"),
            wordWrap="CJK",
        )
        data.append([Paragraph(inline(safe(cell)), style) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=repeat, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#285276")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b8c5d1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f8")]),
    ]))
    return table


def read_runs(state):
    result = []
    for run_id, record in sorted(state.get("runs", {}).items()):
        if record.get("status") != "complete":
            continue
        result_path = Path(record.get("result_path", ""))
        if not result_path.is_file():
            raise FileNotFoundError(f"Missing saved result for {run_id}: {result_path}")
        saved = json.loads(result_path.read_text(encoding="utf-8"))
        result.append({"run_id": run_id, **record, "saved": saved, "brief": saved.get("brief", {})})
    return result


def inspect_results(runs):
    checks = {
        "all_groups_have_one_patient": True,
        "all_controls_excluded_from_analyzed_fluxes": True,
        "all_29_estimators_declared": True,
        "all_29_estimator_flux_columns_emitted": True,
        "six_conceptual_question_groups_emitted": True,
        "q5_aliases_identical": True,
        "q6_aliases_identical": True,
        "all_requested_controls_covered": True,
        "all_patient_groups_covered": True,
        "oscillatory_control_retained": True,
        "diagonal_target_fallback_explicit": True,
    }
    expected_controls = {
        "week_from_start", "signal_primary", "marker_correlated",
        "marker_oscillatory", "noise_independent",
    }
    expected_groups = {"SYN-P01", "SYN-P02", "SYN-P03"}
    controls, patients = set(), set()
    details = []
    metrics = {"finite_estimator_value_cells": 0, "completed_run_count": len(runs)}
    for row in runs:
        record = row["brief"]
        patient, control = row["patient_key"], row["control"]
        patients.add(patient)
        controls.add(control)
        result = row["saved"]["result"]
        meta = result.get("metadata", {}) or {}
        scores = ((result.get("run_pipeline") or {}).get("scores") or {})
        per_patient = ((result.get("run_pipeline") or {}).get("threshold_metadata") or {}).get("n_pts")
        input_path = TEST_DIR / "inputs" / f"{patient}.csv"
        with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
            input_rows = list(csv.DictReader(stream))
        input_groups = {item.get("patient_key") for item in input_rows}
        checks["all_groups_have_one_patient"] &= (
            input_groups == {patient} and len(input_rows) == record.get("n_samples_reported") == per_patient
        )
        checks["all_controls_excluded_from_analyzed_fluxes"] &= not record.get("control_present_as_analyzed_flux", True)
        checks["all_29_estimators_declared"] &= record.get("n_estimator_names_in_class_map") == 29
        expected_q_keys = {
            "Q1_Calme_vs_Chaos", "Q2_Tension_Seuil", "Q3_Agressivite", "Q4_Persistence",
            "Q5_Actif_Receptif", "Q5_Active_Reactive",
            "Q6_Actif_Receptif_Echelle", "Q6_Active_Reactive_Scaled",
        }
        checks["six_conceptual_question_groups_emitted"] &= expected_q_keys.issubset(scores)
        output_dir = Path(row.get("output_dir", ""))
        feature_csv = output_dir / "df_feat.csv"
        with feature_csv.open("r", encoding="utf-8-sig", newline="") as stream:
            feature_rows = csv.reader(stream)
            header = next(feature_rows)
            header_set = set(header)
            class_map = meta.get("estimator_classes", {}) or {}
            estimator_names = sorted({name for names in class_map.values() for name in names})
            flux_names = sorted((meta.get("global_flux_stats") or {}).keys())
            expected_features = [f"{flux}_{estimator}_mean" for flux in flux_names for estimator in estimator_names]
            emitted_features = [column for column in expected_features if column in header_set]
            checks["all_29_estimator_flux_columns_emitted"] &= len(emitted_features) == len(expected_features) == 29 * len(flux_names)
            finite_cells = 0
            for values in feature_rows:
                cells = dict(zip(header, values))
                for column in emitted_features:
                    try:
                        value = float(cells.get(column, "nan"))
                        finite_cells += int(value == value and abs(value) != float("inf"))
                    except (TypeError, ValueError):
                        pass
            metrics["finite_estimator_value_cells"] += finite_cells
        checks["q5_aliases_identical"] &= (
            "Q5_Actif_Receptif" in scores and "Q5_Active_Reactive" in scores
            and json.dumps(scores.get("Q5_Actif_Receptif"), sort_keys=True, allow_nan=True)
                == json.dumps(scores.get("Q5_Active_Reactive"), sort_keys=True, allow_nan=True)
        )
        checks["q6_aliases_identical"] &= (
            "Q6_Actif_Receptif_Echelle" in scores and "Q6_Active_Reactive_Scaled" in scores
            and json.dumps(scores.get("Q6_Actif_Receptif_Echelle"), sort_keys=True, allow_nan=True)
                == json.dumps(scores.get("Q6_Active_Reactive_Scaled"), sort_keys=True, allow_nan=True)
        )
        if control == "signal_primary":
            checks["diagonal_target_fallback_explicit"] &= meta.get("target_fallback_used") is True
        if control == "marker_oscillatory":
            checks["oscillatory_control_retained"] &= (
                record.get("control_reported") == control
                and record.get("control_non_monotone") is True
            )
        tlog = record.get("tlog_class_median") or {}
        cascade = result.get("five_threshold_cascade", {}) or {}
        transition = (result.get("run_pipeline") or {}).get("transition_analysis") or {}
        transition_entries = [
            (estimator, flux, value)
            for estimator, flux_map in transition.items() if isinstance(flux_map, dict)
            for flux, value in flux_map.items() if flux != "Tous" and isinstance(value, dict)
        ]
        details.append({
            "patient": patient, "control": control,
            "n": record.get("n_samples_reported"), "seconds": row.get("elapsed_seconds"),
            "monotone": record.get("control_monotone"),
            "nonmonotone": record.get("control_non_monotone"),
            "t0": record.get("t0_pct"), "cascade": record.get("cascade_status"),
            "mc": record.get("mc_axis_status"),
            "sat": tlog.get("saturation"), "crit": tlog.get("criticality"),
            "div": tlog.get("divergence"), "null": tlog.get("null_reference"),
            "f1max": cascade.get("max_F1_velocity"), "f2max": cascade.get("max_F2_curvature"),
            "derivative_post_ok": sum(value.get("status") == "success" for _, _, value in transition_entries),
            "derivative_pre_ok": sum(value.get("status_pre") == "success" for _, _, value in transition_entries),
            "target": record.get("target_used"), "diagonal": record.get("target_fallback_used"),
            "q_keys": ",".join(record.get("q_score_groups", [])),
            "estimator_flux_columns_emitted": len(emitted_features),
            "finite_estimator_value_cells": finite_cells,
        })
    checks["all_requested_controls_covered"] = controls == expected_controls
    checks["all_patient_groups_covered"] = patients == expected_groups
    return checks, details, metrics


def make_summary_figure(details):
    patients = sorted({row["patient"] for row in details})
    controls = ["week_from_start", "signal_primary", "marker_correlated", "marker_oscillatory", "noise_independent"]
    t0 = np.array([[next(row["t0"] for row in details if row["patient"] == patient and row["control"] == control)
                    for control in controls] for patient in patients], dtype=float)
    class_names = ["saturation", "criticality", "divergence", "null"]
    def median_for_control(control, key):
        values = np.asarray([float(row[key]) for row in details
                             if row["control"] == control and row[key] is not None], dtype=float)
        values = values[np.isfinite(values)]
        return float(np.median(values)) if values.size else np.nan
    tlog = np.array([
        [median_for_control(control, key) for key in ("sat", "crit", "div", "null")]
        for control in controls
    ], dtype=float)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 11), constrained_layout=True,
                                   gridspec_kw={"height_ratios": [1, 2]})
    im1 = ax1.imshow(t0, aspect="auto", cmap="viridis")
    ax1.set_title("T0 retourné par patient et contrôle - données synthétiques")
    ax1.set_xticks(range(len(controls)), controls, rotation=18, ha="right")
    ax1.set_yticks(range(len(patients)), patients)
    for i in range(t0.shape[0]):
        for j in range(t0.shape[1]):
            ax1.text(j, i, f"{t0[i, j]:.1f}", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im1, ax=ax1, label="T0 (%)")
    im2 = ax2.imshow(tlog, aspect="auto", cmap="coolwarm")
    ax2.set_title("TLog par contrôle - médiane descriptive sur trois trajectoires synthétiques")
    ax2.set_xticks(range(len(class_names)), class_names, rotation=0, ha="center")
    ax2.set_yticks(range(len(controls)), controls, fontsize=7)
    for i in range(tlog.shape[0]):
        for j in range(tlog.shape[1]):
            ax2.text(j, i, f"{tlog[i, j]:.2f}", ha="center", va="center", fontsize=8,
                     color="white" if abs(tlog[i, j]) > 8 else "black")
    fig.colorbar(im2, ax=ax2, label="TLog class median")
    fig.savefig(SUMMARY_FIGURE, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_report(qa, checks, details, metrics, runs):
    short_gate = json.loads(SHORT_GATE_RESULT.read_text(encoding="utf-8"))
    lines = [
        "# Rapport V1 — validation synthétique d’un panel groupé",
        "",
        "**Date de génération :** " + datetime.now().strftime("%Y-%m-%d"),
        "**Statut de la campagne :** " + qa.get("status", "inconnu"),
        "**Données patient :** aucune; panel entièrement généré.",
        "**Cœur :** " + str(qa.get("pipeline_version")),
        "",
        "## Résultat mesuré",
        "",
        f"{len(runs)} appels complets ont été enregistrés pour trois trajectoires de 64 visites et cinq colonnes numériques candidates comme contrôles. Le tableau détaillé ci-dessous garde une ligne par couple patient/contrôle.",
        "",
        "| Patient | Contrôle | N | Contrôle monotone | T0 (%) | Statut cascade | TLog saturation | TLog criticité | TLog divergence | TLog référence nulle | Cible utilisée | Repli diagonal |",
        "|---|---|---:|---|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for row in details:
        lines.append(
            f"| {row['patient']} | {row['control']} | {row['n']} | {row['monotone']} | "
            f"{safe(row['t0'])} | {row['cascade']} | {safe(row['sat'])} | {safe(row['crit'])} | "
            f"{safe(row['div'])} | {safe(row['null'])} | {row['target']} | {row['diagonal']} |"
        )
    lines.extend([
        "",
        "## Contrôles techniques post-exécution",
        "",
        "| Assertion | Résultat observé |",
        "|---|---|",
    ])
    for key, value in checks.items():
        lines.append(f"| {key} | {'PASS' if value else 'FAIL'} |")
    lines.extend([
        "",
        "## Sorties F1/F2 et dérivées",
        "",
        "Les maxima F1/F2 de la cascade et le nombre d’entrées estimateur-flux avec dérivées pré/post disponibles sont ci-dessous. Les valeurs détaillées de première et deuxième dérivée avant/après T0 sont reproduites dans l’annexe PDF et dans chaque résultat JSON du snapshot.",
        "",
        "| Patient | Contrôle | F1 max | F2 max | dérivées post valides | dérivées pré valides |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in details:
        lines.append(f"| {row['patient']} | {row['control']} | {safe(row['f1max'])} | {safe(row['f2max'])} | {row['derivative_post_ok']} | {row['derivative_pre_ok']} |")
    short = qa["tests"]["panel_split_precedes_minimum_gate"]
    lines.extend([
        "",
        f"Cas court : {short['pooled_rows']} lignes au total auraient dépassé le garde de {qa['configuration']['minimum_per_patient']}, mais chaque patient avait {qa['configuration']['short_series_visits_per_patient']} visites. Le harnais a enregistré {short['abstention_count']} abstentions et {short['engine_call_count']} appel(s) au moteur.",
        f"Un appel direct supplémentaire au cœur v6.0.1 sur SYN-P01 a retourné {short_gate['observed_core_exception']['type']} : {short_gate['observed_core_exception']['message']}",
        "",
        f"Dans les CSV df_feat, {metrics['finite_estimator_value_cells']} cellules numériques finies ont été comptées parmi les colonnes moyennes des estimateurs. Ce décompte décrit les cellules finies présentes; il n’est pas une mesure de justesse.",
        "",
        "## Ce que ces résultats établissent",
        "",
        "Les sorties documentent l’exécution de v6.0.1 par trajectoire et par contrôle sur des séries construites, ainsi que l’absence de mélange d’identifiants dans chaque CSV transmis au moteur. Le contrôle oscillatoire a été conservé dans le plan. Les valeurs T0 et TLog sont des sorties de la configuration, pas des mesures de précision.",
        "",
        "Le générateur place délibérément un changement lisse dans une partie des flux. Il ne s’agit pas d’un test indépendant de localisation : le panel est simulé, la forme du signal est connue par construction, et la configuration n’a pas été calibrée sur des données externes.",
        "",
        "## Limites et suites",
        "",
        "- Aucune donnée PDAC ou autre donnée patient n’a été chargée.",
        "- Aucun bénéfice thérapeutique, biomarqueur, diagnostic ou résultat clinique n’est évalué.",
        "- Le contrôle diagonal partage son identité avec la cible fixe et le pipeline l’a replié explicitement; ce run n’est pas comparable aux autres contrôles pour les niveaux dépendant de la cible.",
        "- Les résumés restent individuels. Aucun bootstrap ou intervalle inférentiel sur trois sujets synthétiques n’est présenté.",
        "- Le cas court confirme l’abstention du harnais; il ne résout pas le minimum de longueur du cœur pour les trajectoires cliniques courtes.",
        "- Les JSON complets, traces, CSV et images générés sont conservés dans le snapshot séparé du projet.",
        "",
        "## Reproduction et empreintes",
        "",
        f"- Script du banc d’essai SHA-256 : {qa.get('harness_sha256')}",
        f"- Source v6.0.1 SHA-256 : {qa.get('pipeline_sha256')}",
        f"- CSV panel SHA-256 : {qa.get('panel_sha256')}",
        "- Instructions : README_FR.md et PROTOCOLE_GROUPE_PANEL_V1_FR.md dans ce dossier.",
        "",
        "## Question de méthode à garder ouverte",
        "",
        "Les paramètres synthétiques, la cible fixe, le mode fast et le budget auxiliaire ont été spécifiés pour tester le câblage, non pour optimiser T0. Toute agrégation cohorte, rééchantillonnage patient, interprétation des flux ou modification du minimum doit faire l’objet d’un protocole distinct avant d’examiner une cohorte réelle.",
        "",
        "### Déclaration",
        "",
        "Résultats observés et décision de portée sont séparés. Hypothèse d’ingénierie : le wrapper peut préserver des trajectoires si les appels restent isolés. Résultat de cette campagne : critères de câblage listés dans le JSON. Aucun de ces éléments ne prouve la théorie générale ni une application biomédicale.",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def markdown_blocks(story, path: Path, styles):
    lines = path.read_text(encoding="utf-8").splitlines()
    body = styles["BodyText"]
    index = 0
    while index < len(lines):
        s = lines[index].strip()
        if not s or s == "---":
            index += 1
            continue
        if s.startswith("|"):
            block = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(set(cell.replace(":", "")) <= {"-"} for cell in cells):
                    block.append(cells)
                index += 1
            ncols = max((len(row) for row in block), default=1)
            available_width = A4[0] - 34 * mm
            story.append(make_table(block, widths=[available_width / ncols] * ncols, font_size=6.2))
            story.append(Spacer(1, 5))
            continue
        if s.startswith("# "):
            story.append(Paragraph(inline(s[2:]), styles["Title"]))
        elif s.startswith("## "):
            story.append(Paragraph(inline(s[3:]), styles["Heading2"]))
        elif s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), styles["Heading3"]))
        elif s.startswith("- "):
            story.append(Paragraph("• " + inline(s[2:]), styles["BodyText"]))
        else:
            story.append(Paragraph(inline(s.replace("**", "")), body))
        index += 1


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c8d2dc"))
    canvas.line(17 * mm, 14 * mm, A4[0] - 17 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#536575"))
    canvas.drawString(17 * mm, 9 * mm, "Annexe V10 - panel longitudinal synthétique - UNIVERSAL_LOG")
    canvas.drawRightString(A4[0] - 17 * mm, 9 * mm, str(doc.page))
    canvas.restoreState()


def main():
    parser = argparse.ArgumentParser(description="Build the V10 complete whitepaper appendix.")
    parser.add_argument("--rebuild", action="store_true", help="replace this script's generated V10 PDF outputs")
    args = parser.parse_args()
    for path in (BASE_PDF, STATE_PATH, QA_PATH, PANEL_CSV, HARNESS, SHORT_GATE_SCRIPT, SHORT_GATE_RESULT):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if (FINAL_PDF.exists() or APPENDIX_PDF.exists()) and not args.rebuild:
        raise FileExistsError("Refusing to overwrite V10 PDF/appendix outputs.")
    qa = json.loads(QA_PATH.read_text(encoding="utf-8"))
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    runs = read_runs(state)
    if qa.get("status") != "passed" or len(runs) != 15:
        raise RuntimeError(f"V1 panel campaign is not complete/passed: status={qa.get('status')}, runs={len(runs)}")
    checks, details, metrics = inspect_results(runs)
    short_gate = json.loads(SHORT_GATE_RESULT.read_text(encoding="utf-8"))
    checks["actual_v6_short_series_refusal"] = short_gate.get("status") == "passed"
    failed_checks = [name for name, value in checks.items() if value is not True]
    if failed_checks:
        raise RuntimeError(f"Additional PDF audit assertions failed: {failed_checks}")
    PUBLIC_SUMMARY.write_text(json.dumps({
        "status": qa.get("status"),
        "scope": "Generated synthetic software validation only; no clinical data.",
        "pipeline_version": qa.get("pipeline_version"),
        "pipeline_sha256": qa.get("pipeline_sha256"),
        "harness_sha256": qa.get("harness_sha256"),
        "panel_sha256": qa.get("panel_sha256"),
        "configuration": qa.get("configuration"),
        "panel_structure": qa.get("panel_structure"),
        "pre_run_tests": qa.get("tests"),
        "direct_short_core_gate": json.loads(SHORT_GATE_RESULT.read_text(encoding="utf-8")),
        "post_run_checks": checks,
        "metrics": metrics,
        "patient_control_results": details,
        "limitations": qa.get("next_limitations"),
        "interpretation_boundary": qa.get("interpretation_boundary"),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_report(qa, checks, details, metrics, runs)
    make_summary_figure(details)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="V10Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=colors.HexColor("#17324d"), spaceAfter=10))
    styles.add(ParagraphStyle(name="V10H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.HexColor("#17324d"), spaceBefore=9, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle(name="V10Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10, alignment=TA_LEFT, spaceAfter=4))
    styles.add(ParagraphStyle(name="V10Code", fontName="Courier", fontSize=5.4, leading=6.4, leftIndent=2, rightIndent=2, backColor=colors.HexColor("#f2f5f7"), borderPadding=3, spaceBefore=2, spaceAfter=3))

    story = [
        Paragraph("Mise à jour V10 — validation synthétique d’un mode panel", styles["V10Title"]),
        Paragraph("Annexe technique ajoutée au livre blanc maître. Exécution exclusivement synthétique; aucune donnée clinique chargée.", styles["V10Body"]),
        Paragraph(f"État de campagne : {qa['status']} | appels terminés : {len(runs)} | version pipeline : {qa.get('pipeline_version')}", styles["V10Body"]),
        PageBreak(),
    ]
    for release_doc in [
        ROOT / "README_V10_CURRENT.md",
        ROOT / "COMPLETE_WHITEPAPER_V10_README.md",
        ROOT / "RELEASE_V10_CHANGELOG_FR.md",
        ROOT / "PUBLICATION_SCOPE_V10.md",
        ROOT / "BACKUP_README_V10_FR.md",
    ]:
        markdown_blocks(story, release_doc, styles)
        story.append(PageBreak())
    markdown_blocks(story, TEST_DIR / "README_FR.md", styles)
    story.append(PageBreak())
    markdown_blocks(story, TEST_DIR / "PROTOCOLE_GROUPE_PANEL_V1_FR.md", styles)
    story.append(PageBreak())
    short_gate = json.loads(SHORT_GATE_RESULT.read_text(encoding="utf-8"))
    story.append(Paragraph("Exécution directe du cas court dans le cœur v6.0.1", styles["V10H2"]))
    story.append(Paragraph("Sur 32 visites, l’entrée complète a levé l’exception attendue avant le calcul analytique. Les trois trajectoires courtes totalisaient 96 lignes; cette somme n’a pas été passée au moteur.", styles["V10Body"]))
    story.append(Preformatted(json.dumps(short_gate, indent=2, ensure_ascii=False), styles["V10Code"], maxLineLength=110))
    story.append(PageBreak())
    markdown_blocks(story, REPORT_MD, styles)
    story.append(PageBreak())

    story.append(Paragraph("Résumé tabulaire complet par patient et contrôle", styles["V10H2"]))
    rows = [["Patient", "Contrôle", "N", "Monotone", "T0 %", "Cible utilisée", "Repli diagonal", "Secondes"]]
    tlog_rows = [["Patient", "Contrôle", "TLog saturation", "TLog criticité", "TLog divergence", "TLog référence nulle"]]
    for row in details:
        rows.append([row["patient"], row["control"], safe(row["n"]), safe(row["monotone"]),
                     safe(row["t0"]), safe(row["target"]), safe(row["diagonal"]), safe(row["seconds"])])
        tlog_rows.append([row["patient"], row["control"], safe(row["sat"]), safe(row["crit"]), safe(row["div"]), safe(row["null"])])
    story.append(make_table(rows, widths=[23*mm, 32*mm, 10*mm, 19*mm, 18*mm, 27*mm, 22*mm, 17*mm], font_size=6.4))
    story.append(Spacer(1, 4))
    story.append(make_table(tlog_rows, widths=[23*mm, 30*mm, 28*mm, 27*mm, 28*mm, 33*mm], font_size=6.4))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Les valeurs ne sont pas poolées sur les prélèvements. Elles décrivent la sortie de chaque appel indépendant.", styles["V10Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Carte comparative des sorties", styles["V10H2"]))
    story.append(Paragraph("Les axes de couleur décrivent les valeurs retournées par le pipeline. Elles ne constituent pas des mesures de performance et ne doivent pas être lues comme une validation du seuil. Les images incorporées sont des copies JPEG optimisées pour l’impression; les PNG source restent conservés dans les sorties d’exécution.", styles["V10Body"]))
    image = Image(str(pdf_ready_image(SUMMARY_FIGURE, "summary_heatmap")))
    scale = min((A4[0] - 38*mm) / image.imageWidth, (A4[1] - 58*mm) / image.imageHeight)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    story.append(image)
    story.append(PageBreak())

    story.append(Paragraph("F1/F2 et dérivées avant/après T0", styles["V10H2"]))
    story.append(Paragraph("Les colonnes F1 max et F2 max reprennent les champs max_F1_velocity et max_F2_curvature de la cascade. Les comptes indiquent les paires estimateur-flux dont les champs de dérivées avant ou après le seuil ont status = success. Les tableaux détaillés suivent après le code.", styles["V10Body"]))
    derivative_summary = [["Patient", "Contrôle", "F1 max", "F2 max", "Post valides", "Pré valides"]]
    for row in details:
        derivative_summary.append([row["patient"], row["control"], safe(row["f1max"]), safe(row["f2max"]), row["derivative_post_ok"], row["derivative_pre_ok"]])
    story.append(make_table(derivative_summary, widths=[25*mm, 38*mm, 27*mm, 27*mm, 28*mm, 28*mm], font_size=6.5))
    story.append(PageBreak())

    story.append(Paragraph("Panel synthétique complet utilisé", styles["V10H2"]))
    with PANEL_CSV.open("r", encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.reader(stream))
    panel_rows = [[cell for cell in csv_rows[0]]]
    panel_rows.extend(csv_rows[1:])
    panel_widths = [20*mm, 26*mm, 15*mm, 18*mm, 20*mm, 20*mm, 18*mm, 23*mm]
    story.append(make_table(panel_rows, widths=panel_widths, font_size=5.2))
    story.append(PageBreak())

    story.append(Paragraph("Script complet du banc d’essai", styles["V10H2"]))
    code = HARNESS.read_text(encoding="utf-8")
    code = code.replace("—", "-").replace("–", "-").replace("×", "x").replace("’", "'")
    story.append(Preformatted(textwrap.dedent(code), styles["V10Code"], maxLineLength=112))
    story.append(PageBreak())

    story.append(Paragraph("Script complet — vérification directe du garde court", styles["V10H2"]))
    short_code = SHORT_GATE_SCRIPT.read_text(encoding="utf-8").replace("—", "-").replace("–", "-").replace("×", "x").replace("’", "'")
    story.append(Preformatted(textwrap.dedent(short_code), styles["V10Code"], maxLineLength=112))
    story.append(PageBreak())

    for run in runs:
        result = run["saved"]["result"]
        transition = (result.get("run_pipeline") or {}).get("transition_analysis") or {}
        detail_rows = [["Estimateur", "Flux", "Pré", "Post", "d1 pré", "d1 post", "d2 pré", "d2 post", "Delta d1", "Delta d2"]]
        for estimator, flux_map in transition.items():
            if not isinstance(flux_map, dict):
                continue
            for flux, entry in flux_map.items():
                if flux == "Tous" or not isinstance(entry, dict):
                    continue
                detail_rows.append([
                    estimator, flux, safe(entry.get("status_pre")), safe(entry.get("status")),
                    safe(entry.get("first_derivative_pre")), safe(entry.get("first_derivative")),
                    safe(entry.get("second_derivative_pre")), safe(entry.get("second_derivative")),
                    safe(entry.get("delta_first_derivative")), safe(entry.get("delta_second_derivative")),
                ])
        story.append(Paragraph(inline(f"Dérivées avant/après seuil — {run['patient_key']} / {run['control']}"), styles["V10H2"]))
        story.append(Paragraph("Champs source : first_derivative_pre, first_derivative, second_derivative_pre, second_derivative, delta_first_derivative, delta_second_derivative. Les lignes Tous sont omises ici, car elles agrègent les flux; les flux individuels restent séparés.", styles["V10Body"]))
        story.append(make_table(detail_rows, widths=[20*mm, 22*mm, 10*mm, 10*mm, 18*mm, 18*mm, 18*mm, 18*mm, 20*mm, 20*mm], font_size=5.3))
        story.append(PageBreak())

    pngs = sorted(RUNS_DIR.glob("*/*/*.png"))
    for image_index, image_path in enumerate(pngs):
        story.append(Paragraph(inline(f"Figure — {image_path.parent.parent.name} / {image_path.parent.name} / {image_path.name}"), styles["V10H2"]))
        pdf_image = pdf_ready_image(image_path, f"run_chart_{image_index:03d}")
        img = Image(str(pdf_image))
        max_w, max_h = A4[0] - 38*mm, A4[1] - 55*mm
        scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
        img.drawWidth = img.imageWidth * scale
        img.drawHeight = img.imageHeight * scale
        story.append(img)
        story.append(PageBreak())

    log_paths = sorted(LOGS_DIR.glob("*.log"))
    for log_path in log_paths:
        story.append(Paragraph(inline(f"Trace complète — {log_path.stem}"), styles["V10H2"]))
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        story.append(Preformatted(textwrap.dedent(log_text), styles["V10Code"], maxLineLength=125))
        story.append(PageBreak())

    doc = SimpleDocTemplate(str(APPENDIX_PDF), pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=16*mm, bottomMargin=20*mm,
                            title="Annexe V10 - validation synthétique d'un panel groupe",
                            author="UNIVERSAL_LOG research audit")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    base_reader, appendix_reader = PdfReader(str(BASE_PDF)), PdfReader(str(APPENDIX_PDF))
    writer = PdfWriter()
    writer.append(base_reader)
    writer.append(appendix_reader)
    writer.add_metadata({
        "/Title": "UNIVERSAL_LOG - Livre blanc complet V10 - validation synthétique d'un panel groupé",
        "/Subject": "Mise à jour V9 avec résultats reproductibles d'un adaptateur panel synthétique v6.0.1",
        "/Author": "UNIVERSAL_LOG research audit",
    })
    with FINAL_PDF.open("wb") as stream:
        writer.write(stream)
    final_reader = PdfReader(str(FINAL_PDF))
    if final_reader.attachments:
        raise RuntimeError("Unexpected PDF attachments.")
    digest = sha256(FINAL_PDF)
    FINAL_PDF.with_suffix(FINAL_PDF.suffix + ".sha256").write_text(f"{digest}  {FINAL_PDF.name}\n", encoding="ascii")
    print(json.dumps({
        "base_pages": len(base_reader.pages), "appendix_pages": len(appendix_reader.pages),
        "final_pages": len(final_reader.pages), "bytes": FINAL_PDF.stat().st_size,
        "sha256": digest, "attachments": list(final_reader.attachments.keys()),
        "figures_appended": len(pngs), "logs_appended": len(log_paths),
        "report": str(REPORT_MD), "pdf": str(FINAL_PDF),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
