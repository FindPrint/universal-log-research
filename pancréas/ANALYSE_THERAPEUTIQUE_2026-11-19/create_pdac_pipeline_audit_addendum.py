from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
import subprocess
import sys
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ANALYSIS = Path(__file__).resolve().parent
ROOT = ANALYSIS.parents[1]
RUN_DIR = ANALYSIS / "pipeline_runs_parallel15" / "PC69_target_basal"
BALANCED_INPUT = ANALYSIS / "pipeline_inputs_balanced_15" / "GSE271300_PC69_balanced15_multiflux.csv"
FULL_PC69_INPUT = ANALYSIS / "pipeline_inputs" / "GSE271300_PC69_singlet_cells_multiflux.csv"
INPUT_MANIFEST = ANALYSIS / "pipeline_inputs_balanced_15" / "BALANCED15_PIPELINE_INPUT_MANIFEST.json"
PIPELINE = ROOT / "UNIVERSAL_LOG_v5.9.4.py"
SUMMARY_CSV = RUN_DIR / "ALL_CONTROLS_SUMMARY.csv"
SUMMARY_JSON = RUN_DIR / "ALL_CONTROLS_SUMMARY.json"
SUMMARY_MD = RUN_DIR / "ALL_CONTROLS_SUMMARY.md"
AUDIT_JSON = RUN_DIR / "ALL_CONTROLS_AUDIT_MANIFEST.json"
MOUSE_TRIAL = ANALYSIS / "mouse_level_pipeline_trial"
MOUSE_SOURCE = ANALYSIS / "results_mouse_level" / "GSE271300_mouse_level_summaries.csv"
MOUSE_PREP = ANALYSIS / "prepare_mouse_level_pipeline_input.py"
MOUSE_INPUT = MOUSE_TRIAL / "GSE271300_PC69_PC106_mouse_level_multiflux.csv"
MOUSE_INPUT_MANIFEST = MOUSE_TRIAL / "MOUSE_LEVEL_INPUT_MANIFEST.json"
MOUSE_FAIL_DIR = MOUSE_TRIAL / "runs" / "Treatment_code_attempt02"
MOUSE_AUDIT = MOUSE_TRIAL / "MOUSE_LEVEL_PIPELINE_TEST_AUDIT.json"
OUT_DIR = ROOT / "output" / "pdac_pipeline_audit_2026-11-19"
OUT_DIR.mkdir(parents=True, exist_ok=True)
BUNDLE_ZIP = OUT_DIR / "PDAC_PC69_UNIVERSAL_LOG_17_CONTROLS_AUDIT_BUNDLE_2026-11-19.zip"
REPORT_PDF = OUT_DIR / "PDAC_PC69_UNIVERSAL_LOG_17_CONTROLS_AUDIT_ADDENDUM_2026-11-19.pdf"
CHART_PNG = OUT_DIR / "PC69_T0_and_runtime_by_control_2026-11-19.png"
SHA_FILE = OUT_DIR / "PDAC_PC69_AUDIT_BUNDLE_SHA256.txt"

ACCENT = colors.HexColor("#0C6670")
NAVY = colors.HexColor("#18334A")
INK = colors.HexColor("#263238")
PALE = colors.HexColor("#EAF3F4")
LIGHT = colors.HexColor("#F3F6F8")
AMBER = colors.HexColor("#B85C00")
RED = colors.HexColor("#9A3030")
WHITE = colors.white


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def safe_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def env_description() -> str:
    result = subprocess.run(
        [sys.executable, "-c", "import sys; print(sys.version.split()[0])"],
        check=True, capture_output=True, text=True,
    )
    import importlib.metadata as metadata
    packages = ["numpy", "pandas", "scipy", "h5py", "matplotlib", "numba", "reportlab", "pypdf"]
    installed = []
    for name in packages:
        try:
            installed.append(f"{name}=={metadata.version(name)}")
        except metadata.PackageNotFoundError:
            continue
    return f"Python {result.stdout.strip()}; " + ", ".join(installed)


def create_bundle(summary: dict, audit: dict, manifest: dict) -> None:
    mouse_status_path = MOUSE_FAIL_DIR / "run_status.json"
    mouse_log_path = MOUSE_FAIL_DIR / "console.log"
    mouse_files = [MOUSE_SOURCE, MOUSE_PREP, MOUSE_INPUT, MOUSE_INPUT_MANIFEST, mouse_status_path, mouse_log_path]
    mouse_status = safe_json(mouse_status_path)
    MOUSE_AUDIT.write_text(json.dumps({
        "pipeline": str(PIPELINE),
        "pipeline_sha256": sha256(PIPELINE),
        "test_status": mouse_status.get("status"),
        "exit_code": mouse_status.get("exit_code"),
        "minimum_points_error": mouse_status.get("observed_error"),
        "files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in mouse_files],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme = f"""# UNIVERSAL_LOG v5.9.4 - audit d'execution PDAC PC69

Date du rapport : 2026-11-19 (America/Toronto)

## Contenu

- Le pipeline exact UNIVERSAL_LOG_v5.9.4.py et les scripts d'entree, d'echantillonnage, d'execution et de synthese.
- Les CSV PC69 complets et equilibres utilises pour generer l'entree de ce run.
- Les 17 dossiers de sortie complets, incluant master_results, reading_synthesis, diagnostics, exports estimateurs, run_status et console.log.
- RUN_PROGRESS.json, RUN_SUMMARY.json, la synthese CSV/JSON/Markdown et les manifestes d'empreintes SHA-256.
- Le graphique synthetique de T0 et des durees.
- Un essai secondaire sur 13 lignes souris, avec son entree, son journal console et l'arret de validation enregistre.

## Reproduction de l'execution

Entree exacte : pipeline_inputs_balanced_15/GSE271300_PC69_balanced15_multiflux.csv
SHA-256 : {audit['input']['sha256']}

Pipeline exact : UNIVERSAL_LOG_v5.9.4.py
SHA-256 : {audit['pipeline']['sha256']}

La commande de chaque controle est identique a celle-ci, en remplacant CONTROL par une des 17 colonnes listees dans pipeline_runs_parallel15/PC69_target_basal/RUN_PROGRESS.json :

    .venv/Scripts/python.exe -u UNIVERSAL_LOG_v5.9.4.py --input <balanced-PC69.csv> --target CellState_basal --control CONTROL --control-mode single --target-mode fixed --domain pdac --mode fast --no-l7b --no-harmonic-validation --no-dashboard --no-plots --no-telemetry --no-adaptive-walk-forward --no-regime-weights --seed 42 --output <run-directory>

Le mode fast utilise Cohen-d. Le MC predictif est actif dans ces runs (29 estimateurs, 48 scenarios). L7b et certaines fonctions optionnelles sont desactivees explicitement; voir le rapport PDF et les journaux.

Environnement observe : {env_description()}

## Limites de l'entree

L'entree equilibree comprend 90 cellules, 15 tirees dans chacun de six groupes animaux. Les cellules ne sont pas 90 replicats biologiques independants. Les lignes sont tirees au hasard puis melangees. Le CSV ne contient pas de colonne temps/progression observee. Les T0 en pourcentage produits par le pipeline sont donc des sorties sur un axe interne, pas un temps d'apparition de maladie ou une reponse therapeutique.

## Resultat d'execution

- Runs termines avec exit code 0 : {summary['completed_exit_zero_count']}/{summary['requested_control_count']}.
- Fichiers de sortie controles contre run_status : {summary['output_inventory_matches_run_status_for_every_control']}.
- Fichiers de controles haches : {audit['file_count']}.
- Les donnees sont une reanalyse exploratoire de GSE271300 et ne valident pas independamment le pipeline ou un traitement.
- L'essai souris a une ligne par animal (13 lignes); le pipeline v5.9.4 l'a refuse car le mode fast exige 50 points. Aucun remplissage artificiel n'a ete fait.

## Provenance et licence

Source GEO : https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300
Article original : https://pmc.ncbi.nlm.nih.gov/articles/PMC11624508/
Licence de projet choisie precedemment : code MIT; documentation et resultats CC BY 4.0, sous reserve des licences et conditions de la source de donnees.
"""

    entries: list[tuple[Path, str]] = []
    files = [
        PIPELINE,
        ANALYSIS / "analyze_GSE271300_mouse_level.py",
        ANALYSIS / "prepare_pipeline_inputs_GSE271300.py",
        ANALYSIS / "make_balanced_pipeline_inputs.py",
        ANALYSIS / "run_pipeline_all_controls_parallel.py",
        ANALYSIS / "summarize_pipeline_all_controls.py",
        ANALYSIS / "create_pdac_pipeline_audit_addendum.py",
        ANALYSIS / "compare_all_vs_single_pipeline.py",
        FULL_PC69_INPUT,
        BALANCED_INPUT,
        INPUT_MANIFEST,
        ANALYSIS / "GSE271300_PIPELINE_INPUTS.json",
        RUN_DIR / "RUN_PROGRESS.json",
        RUN_DIR / "RUN_SUMMARY.json",
        SUMMARY_CSV,
        SUMMARY_JSON,
        SUMMARY_MD,
        AUDIT_JSON,
        CHART_PNG,
        MOUSE_AUDIT,
    ]
    for path in files:
        if path.is_file():
            if path == PIPELINE:
                arc = "pipeline/UNIVERSAL_LOG_v5.9.4.py"
            elif path.parent == RUN_DIR:
                arc = f"run/PC69_target_basal/{path.name}"
            elif path.parent == ANALYSIS:
                arc = f"analysis/{path.name}"
            elif path == FULL_PC69_INPUT:
                arc = f"inputs/pipeline_inputs/{path.name}"
            elif path == BALANCED_INPUT:
                arc = f"inputs/pipeline_inputs_balanced_15/{path.name}"
            elif path == INPUT_MANIFEST:
                arc = f"inputs/pipeline_inputs_balanced_15/{path.name}"
            elif path == MOUSE_AUDIT:
                arc = f"mouse_level/{path.name}"
            else:
                arc = f"inputs/{path.name}"
            entries.append((path, arc))

    mouse_entries = [
        (MOUSE_SOURCE, "mouse_level/source/GSE271300_mouse_level_summaries.csv"),
        (MOUSE_PREP, "mouse_level/analysis/prepare_mouse_level_pipeline_input.py"),
        (MOUSE_INPUT, "mouse_level/input/GSE271300_PC69_PC106_mouse_level_multiflux.csv"),
        (MOUSE_INPUT_MANIFEST, "mouse_level/input/MOUSE_LEVEL_INPUT_MANIFEST.json"),
        (mouse_status_path, "mouse_level/run/Treatment_code_attempt02/run_status.json"),
        (mouse_log_path, "mouse_level/run/Treatment_code_attempt02/console.log"),
    ]
    entries.extend((path, arc) for path, arc in mouse_entries if path.is_file())

    for control in summary["controls_requested"]:
        folder = RUN_DIR / control
        for path in sorted(folder.iterdir()):
            if path.is_file():
                entries.append((path, f"run/PC69_target_basal/{control}/{path.name}"))

    with zipfile.ZipFile(BUNDLE_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr("README_AUDIT_FR.md", readme)
        for path, arc in entries:
            archive.write(path, arcname=arc)

    SHA_FILE.write_text(f"{sha256(BUNDLE_ZIP)}  {BUNDLE_ZIP.name}\n", encoding="ascii")


def make_chart(rows: list[dict]) -> None:
    labels = [row["control"] for row in rows]
    t0s = [float(row["T0_pct"]) for row in rows]
    durations = [float(row["elapsed_seconds"]) / 60 for row in rows]
    colors_t0 = ["#0C6670" if row.get("T0_ambiguous") is False else "#B85C00" for row in rows]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [1, 1.15]})
    fig.suptitle("UNIVERSAL_LOG v5.9.4 - PC69: sorties par controle", fontsize=17, fontweight="bold", color="#18334A")
    x = list(range(len(labels)))
    ax1.bar(x, t0s, color=colors_t0, width=0.72)
    ax1.set_ylim(0, 108)
    ax1.set_ylabel("T0 sur axe interne (%)")
    ax1.set_xticks(x, labels, rotation=45, ha="right")
    ax1.grid(axis="y", alpha=0.2)
    for index, value in enumerate(t0s):
        ax1.text(index, value + 1.6, f"{value:.1f}", ha="center", va="bottom", fontsize=7)
    ax1.text(0.01, 0.96, "Tous les controles: non-monotones; T0 brut marque ambigu. Axe non temporel.", transform=ax1.transAxes,
             va="top", fontsize=9, color="#7A3D00", bbox={"facecolor": "white", "alpha": 0.86, "edgecolor": "#E0C8A8"})

    order = sorted(range(len(labels)), key=lambda i: durations[i])
    ax2.barh([labels[i] for i in order], [durations[i] for i in order], color="#507A9A")
    ax2.set_xlabel("Duree du run (minutes)")
    ax2.grid(axis="x", alpha=0.2)
    ax2.invert_yaxis()
    median = sorted(durations)[len(durations) // 2]
    ax2.axvline(median, color="#B85C00", linestyle="--", linewidth=1.2, label=f"Mediane: {median:.1f} min")
    ax2.legend(loc="lower right", frameon=False)
    fig.text(0.5, 0.01, "90 cellules aleatoires, 15 par animal, lignes melangees; aucune colonne temps/progression dans le CSV.",
             ha="center", fontsize=9, color="#455A64")
    fig.tight_layout(rect=(0.02, 0.04, 0.98, 0.95))
    fig.savefig(CHART_PNG, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def generate_pdf(summary: dict, audit: dict, run_summary: dict, rows: list[dict], controls: list[str]) -> None:
    font_regular = Path(r"C:\Windows\Fonts\arial.ttf")
    font_bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    pdfmetrics.registerFont(TTFont("Arial", str(font_regular)))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(font_bold)))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitleFR", fontName="Arial-Bold", fontSize=26, leading=31, textColor=NAVY, alignment=TA_LEFT, spaceAfter=12))
    styles.add(ParagraphStyle(name="SubtitleFR", fontName="Arial", fontSize=14, leading=20, textColor=ACCENT, spaceAfter=10))
    styles.add(ParagraphStyle(name="H1FR", fontName="Arial-Bold", fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=10))
    styles.add(ParagraphStyle(name="H2FR", fontName="Arial-Bold", fontSize=11, leading=14, textColor=ACCENT, spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="BodyFR", fontName="Arial", fontSize=9, leading=13, textColor=INK, spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallFR", fontName="Arial", fontSize=7.4, leading=10, textColor=INK, spaceAfter=3))
    styles.add(ParagraphStyle(name="TinyFR", fontName="Arial", fontSize=6, leading=7.4, textColor=INK))
    styles.add(ParagraphStyle(name="CodeFR", fontName="Courier", fontSize=6.8, leading=8.5, textColor=INK, backColor=LIGHT, leftIndent=6, rightIndent=6, borderPadding=6, spaceBefore=4, spaceAfter=7, splitLongWords=1))
    styles.add(ParagraphStyle(name="LogFR", fontName="Courier", fontSize=6.2, leading=7.6, textColor=INK, backColor=LIGHT, leftIndent=4, rightIndent=4, borderPadding=4, splitLongWords=1))
    page_size = landscape(letter)
    page_width, page_height = page_size

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D6E1E5"))
        canvas.setLineWidth(0.6)
        canvas.line(34, page_height - 28, page_width - 34, page_height - 28)
        canvas.setFont("Arial", 7)
        canvas.setFillColor(colors.HexColor("#52636B"))
        canvas.drawString(36, page_height - 21, "UNIVERSAL_LOG | Supplement d'audit PDAC | GSE271300 / PC69")
        canvas.drawRightString(page_width - 36, 20, f"Page {doc.page}")
        canvas.drawString(36, 20, "Resultats du pipeline; lecture biologique limitee par le plan de donnees")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(REPORT_PDF), pagesize=page_size,
        rightMargin=36, leftMargin=36, topMargin=40, bottomMargin=34,
        title="Audit de l'execution UNIVERSAL_LOG v5.9.4 sur GSE271300 PC69",
        author="Projet UNIVERSAL_LOG",
    )
    story = []
    aggregate = summary["aggregate_observed_pipeline_outputs"]
    durations = summary["duration_seconds"]

    story += [Spacer(1, 42), paragraph("RAPPORT D'AUDIT - EXECUTION REELLE", styles["SubtitleFR"]),
              paragraph("UNIVERSAL_LOG v5.9.4<br/>PDAC - GSE271300 / modele PC69", styles["CoverTitleFR"]),
              paragraph("17 colonnes de controle testees avec la cible fixe CellState_basal", styles["SubtitleFR"]),
              Spacer(1, 12)]
    headline = [
        ["Runs complets", "17 / 17", "Sorties hachees", str(audit["file_count"])],
        ["Entree", "90 cellules", "Mode statistique", "Cohen-d / fast"],
        ["Median run", f"{durations['median']/60:.1f} min", "Max run", f"{durations['max']/60:.1f} min"],
    ]
    top_table = Table(headline, colWidths=[105, 115, 115, 130], rowHeights=30)
    top_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY), ("TEXTCOLOR", (2, 0), (2, -1), NAVY),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"), ("FONTNAME", (0, 0), (0, -1), "Arial-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Arial-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C7D9DE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D9DE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [top_table, Spacer(1, 15), paragraph(
        "Ce supplement decrit ce qui a ete execute, les sorties du logiciel et les limites de l'entree. Il ne transforme pas une analyse de cellules melangees en preuve d'une transition tumorale ou d'une efficacite therapeutique.",
        styles["BodyFR"]),
        paragraph("Le livre blanc complet V4 reste la base du projet. Ce document ajoute le run PC69 et son paquet reproductible.", styles["BodyFR"]),
        paragraph("Date locale du rapport : 19 novembre 2026. Horodatages exacts et empreintes SHA-256 dans les fichiers joints.", styles["SmallFR"]),
        PageBreak()]

    story += [paragraph("1. Donnees, cible et plan d'execution", styles["H1FR"]),
              paragraph("L'entree pipeline est une coupe transversale issue du jeu GEO GSE271300. Le CSV PC69 equilibre contient 90 cellules : 15 cellules echantillonnees sans remise dans chacun des six groupes animaux (3 vehicules et 3 MRTX). Les lignes selectionnees ont ete melangees; le CSV ne contient aucune colonne temps ou progression observee. La cellule est l'observation, mais la souris reste l'unite de replication biologique.", styles["BodyFR"]),
              paragraph("La cible demandee etait CellState_basal. Chaque colonne numerique du CSV a ete lancee comme controle, une par processus, avec le meme echantillon, le meme seed et les memes options. Le controle CellState_basal est la diagonale; le pipeline a applique son repli vers Treatment_code et l'a consigne. Les 16 autres controles ont conserve la cible demandee.", styles["BodyFR"]),
              paragraph("Options identiques pour les 17 lancements", styles["H2FR"]),
              Preformatted("--target CellState_basal --target-mode fixed --domain pdac --mode fast\n--control-mode single --seed 42\n--no-l7b --no-harmonic-validation --no-dashboard --no-plots\n--no-telemetry --no-adaptive-walk-forward --no-regime-weights\n(triangulation omis: valeur par defaut du pipeline)", styles["CodeFR"]),
              paragraph("Le chemin d'execution utilise Cohen-d; le helper Cliff est legacy et non appele par ce chemin. Le MC predictif est actif : 29 estimateurs et 48 scenarios dans chaque run. L7b, la validation harmonique, les figures, le dashboard, le telemetrie, l'adaptive walk-forward et les poids de regime etaient explicitement desactives.", styles["BodyFR"]),
              paragraph("L'axe interne en pourcentage est produit par le pipeline. Il ne peut pas etre assimile au temps de maladie pour cette entree sans progression chronologique observee.", styles["BodyFR"]),
              PageBreak()]

    story += [paragraph("2. Resultats observes dans les sorties du pipeline", styles["H1FR"])]
    results_bullets = [
        f"Monotonie du controle : {aggregate['all_controls_non_monotone_count']}/17 non monotones dans l'ordre fourni.",
        f"Valeur brute de T0 : {aggregate['all_t0_raw_ambiguous_count']}/17 marquees ambiguës; T0 en pourcentage interne s'etend de {aggregate['t0_pct_min']:.2f} a {aggregate['t0_pct_max']:.2f}.",
        f"Diagnostic de bruit : {aggregate['noise_scores_unavailable_count']}/17 portent le statut scores_unavailable; scores complets = {aggregate['noise_complete_score_total']}, diagnostics partiels = {aggregate['noise_partial_diagnostics_total']}.",
        f"MC predictif : termine dans {aggregate['predictive_mc_completed_count']}/17, avec {aggregate['predictive_mc_estimators_values'][0]} estimateurs et {aggregate['predictive_mc_scenarios_values'][0]} scenarios.",
        f"L1 : R2 negatif dans {aggregate['L1_negative_R2_count']}/17 (plage {aggregate['L1_R2_min']:.3f} a {aggregate['L1_R2_max']:.3f}); precision directionnelle rapportee de {aggregate['L1_directional_accuracy_min']:.1f}% a {aggregate['L1_directional_accuracy_max']:.1f}%.",
        f"Vote L7a : direction up dans 17/17; L7b desactive dans 17/17, donc aucun verdict de robustesse L7b.",
        f"Tension holographique : regimes {aggregate['holographic_regime_counts']}; test du nul interne signalant une non-linearite significative : {aggregate['tension_null_significant_count']}/17.",
        f"Le controle diagonal a ete replie pour : {', '.join(aggregate['target_diagonal_fallback_controls'])}.",
    ]
    for item in results_bullets:
        story.append(Paragraph("&#8226; " + html.escape(item), styles["BodyFR"]))
    story += [Spacer(1, 6), Image(str(CHART_PNG), width=710, height=444), PageBreak()]

    story += [paragraph("3. Tableau de chaque controle", styles["H1FR"])]
    header = ["Controle", "T0 %", "Monotonie", "T0 brut ambigu", "Bruit", "L1 R2", "L1 acc. %", "min/run"]
    table_data = [header]
    for row in rows:
        acc = row.get("L1_directional_accuracy_pct")
        r2 = row.get("L1_R2")
        table_data.append([
            row["control"],
            f"{float(row['T0_pct']):.2f}" if row.get("T0_pct") is not None else "NA",
            row.get("control_direction") or "NA",
            str(row.get("T0_ambiguous")),
            row.get("noise_status") or "NA",
            f"{float(r2):.3f}" if r2 is not None else "NA",
            f"{float(acc):.1f}" if acc is not None else "NA",
            f"{float(row['elapsed_seconds'])/60:.1f}",
        ])
    detail = LongTable(table_data, colWidths=[112, 48, 82, 83, 105, 53, 63, 57], repeatRows=1, hAlign="LEFT")
    detail.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), 7), ("LEADING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD5DA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [detail, Spacer(1, 7), paragraph("Les colonnes L1 et L7 sont les sorties internes du modele. Elles ne sont pas des performances cliniques; dans cette entree, l'ordre ne correspond pas a une suite temporelle experimentale.", styles["SmallFR"]), PageBreak()]

    story += [paragraph("4. Resultat scientifique permis et limites", styles["H1FR"]),
              paragraph("Resultat d'execution : le pipeline a termine 17/17 controles, conserve les fichiers attendus pour chaque statut, produit 16 diagnostics de flux par run, et exporte les couches de lecture et de tension. Cela repond a la question : le pipeline peut-il s'executer sur ce CSV multi-flux, avec toutes ses colonnes numeriques comme controles ? Oui, avec les statuts ci-dessus.", styles["BodyFR"]),
              paragraph("Resultat de donnees : chaque controle est non monotone et chaque valeur brute de T0 est marquee ambigue. Le diagnostic bruit n'a aucun score complet (0 au total sur 17 runs). Le test interne de significativite de non-linearite contre le nul est faux dans chacun des 17 dossiers. Les directions L1 ne sont pas stables entre controles; les R2 sont negatifs dans 14 cas. Ces elements sont les sorties effectives, pas une interpretation retrospective.", styles["BodyFR"]),
              paragraph("Interpretation limitee : il n'y a pas de temps dans le CSV; les cellules ont ete echantillonnees puis melangees. Les pourcentages T0 de 13.13 a 96.75 ne sont donc pas une transition dans le temps, une emergence de resistance, ni un seuil therapeutique. Les cellules d'un meme animal ne sont pas des replicats independants. Le resultat ne valide ni une cure, ni l'efficacite de MRTX1133, ni l'universalite du pipeline.", styles["BodyFR"]),
              paragraph("Le regime interne critique (16 controles) ou saturation (GATA6) est a rapporter avec le test nul interne non significatif dans 17/17. Le terme de regime n'est pas une observation physique d'une transition tumorale dans ces donnees.", styles["BodyFR"]),
              paragraph("Les rapports bruts, exports des 29 estimateurs, quatre tests, diagnostics et journaux restent disponibles dans le paquet ZIP attache et separe.", styles["BodyFR"]),
              PageBreak()]

    story += [paragraph("5. Suite therapeutique : hypothese separee des resultats", styles["H1FR"]),
              paragraph("Hypothese de litterature a tester, pas un resultat du run PC69 : un article preclinique 2026 rapporte une vulnerabilite autour de USP20, HMGCR, ULK1 et de l'epuisement des cellules T CD8, et teste l'inhibition de USP20 avec blocage KRAS G12D et anti-PD-1 dans des modeles murins/PDX. Les donnees associees sont incluses dans l'article/supplement ou communiquees sur demande; elles ne sont pas un essai clinique ni une preuve de guerison.", styles["BodyFR"]),
              paragraph("Pourquoi ce run ne teste pas cette hypothese : l'entree PC69 ne contient pas USP20, HMGCR, ULK1, PDCD1, HAVCR2 ou LAG3 comme flux; elle porte sur une seule intervention (MRTX1133 contre vehicule) a un point de collecte. Les colonnes KRAS, STAT3, EGFR/ERBB et les scores cellulaires ne remplacent pas ces mesures manquantes.", styles["BodyFR"]),
              paragraph("Prochaine action techniquement defensible : obtenir un jeu de donnees avec mesures individuelles de volume tumoral/temps et groupes controles et combinaison, ou des donnees moleculaires avec repliques au niveau animal. Verifier l'unite experimentale et l'ordre avant d'executer le pipeline; si seules des moyennes de figures ou des cellules sans repliques sont disponibles, les signaler comme illustration et ne pas les traiter comme donnees experimentales independantes. Ajouter ensuite les flux USP20-HMGCR-ULK1 et marqueurs d'epuisement CD8 si ces variables sont presentes. Gel des choix, seed et commandes avant l'analyse.", styles["BodyFR"]),
              paragraph("Cette piste peut justifier une experience preclinique independante; elle ne permet pas de proposer un traitement a une personne. Le dossier presente ici reste exploratoire.", styles["BodyFR"]),
              paragraph("Sources externes", styles["H2FR"]),
              paragraph("- GEO GSE271300: <link href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300' color='#0C6670'>https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300</link> (plan de l'etude et echantillons).", styles["SmallFR"]),
              paragraph("- Etude originale associee: <link href='https://pmc.ncbi.nlm.nih.gov/articles/PMC11624508/' color='#0C6670'>https://pmc.ncbi.nlm.nih.gov/articles/PMC11624508/</link>.", styles["SmallFR"]),
              paragraph("- Article preclinique USP20 (Gut, 2026, DOI 10.1136/gutjnl-2026-338277): <link href='https://doi.org/10.1136/gutjnl-2026-338277' color='#0C6670'>https://doi.org/10.1136/gutjnl-2026-338277</link>.", styles["SmallFR"]),
              paragraph("- GSE337208, single-cell de modeles avec inhibiteurs KRAS / anti-CTLA4 / anti-PD1; verifier le niveau de replication animal avant une inference: <link href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE337208' color='#0C6670'>https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE337208</link>.", styles["SmallFR"]),
              PageBreak()]

    story += [paragraph("6. Reproduction et environnement", styles["H1FR"]),
              paragraph("Le manifeste d'entree contient la selection exacte, les groupes, le seed d'echantillonnage et les empreintes. Le run a ensuite utilise seed 42 pour le pipeline. Les 17 commandes sont conservees dans run_status.json; elles ne different que par la valeur de --control et le dossier --output.", styles["BodyFR"]),
              paragraph("Commande type exacte (depuis la racine du projet; le chemin de sortie differe par controle)", styles["H2FR"]),
              Preformatted(".venv\\Scripts\\python.exe -u UNIVERSAL_LOG_v5.9.4.py --input\npipeline_inputs_balanced_15\\GSE271300_PC69_balanced15_multiflux.csv\n--target CellState_basal --control <CONTROL> --control-mode single\n--target-mode fixed --domain pdac --mode fast\n--no-l7b --no-harmonic-validation --no-dashboard --no-plots\n--no-telemetry --no-adaptive-walk-forward --no-regime-weights\n--seed 42 --output pipeline_runs_parallel15\\PC69_target_basal\\<CONTROL>", styles["CodeFR"]),
              paragraph("Version locale : " + html.escape(env_description()), styles["SmallFR"]),
              paragraph("Validation automatique : 17 controles demandes; 17 exit codes 0; inventaire de chaque run conforme a run_status; 408 fichiers de run haches; SHA-256 du code, de l'entree, des scripts et des fichiers de synthese dans l'appendice et le manifeste JSON.", styles["BodyFR"]),
              paragraph("Le PDF integre une archive ZIP en piece jointe contenant le pipeline exact, les scripts, les entrees de reproduction, les 17 sorties completes et les journaux. Le ZIP est aussi fourni en fichier separe.", styles["BodyFR"]),
              paragraph("Licence choisie precedemment pour le projet : MIT pour le code; CC BY 4.0 pour documentation/resultats, sous reserve des licences et conditions des donnees source.", styles["SmallFR"]),
              PageBreak()]

    mouse_status = safe_json(MOUSE_FAIL_DIR / "run_status.json")
    story += [paragraph("7. Essai souris independantes : refus par la validation d'entree", styles["H1FR"]),
              paragraph("Un second essai a ete prepare a partir du fichier de resumes au niveau souris. Il conserve 13 souris uniques (PC69: 6; PC106: 7), une par ligne, avec cible basal_fraction et Treatment_code comme controle. Le modele et le traitement sont codes selon le manifeste; l'ordre source est conserve. Aucun point n'a ete duplique ni impute.", styles["BodyFR"]),
              paragraph("Commande testee", styles["H2FR"]),
              Preformatted(".venv\\Scripts\\python.exe -u UNIVERSAL_LOG_v5.9.4.py\n--input mouse_level_pipeline_trial\\GSE271300_PC69_PC106_mouse_level_multiflux.csv\n--target basal_fraction\n--control Treatment_code --control-mode single --target-mode fixed\n--domain pdac --mode fast --no-l7b --no-harmonic-validation\n--no-dashboard --no-plots --no-telemetry --no-adaptive-walk-forward\n--no-regime-weights --seed 42\n--output mouse_level_pipeline_trial\\runs\\Treatment_code_attempt02", styles["CodeFR"]),
              paragraph("Sortie observee, exit code " + str(mouse_status.get("exit_code")) + ": " + html.escape(mouse_status.get("observed_error", "erreur absente du statut")), styles["BodyFR"]),
              paragraph("Le pipeline n'a produit aucun resultat d'estimation pour cet essai. Il ne constitue donc ni un resultat biologique nul, ni une analyse therapeutique. Le seuil minimum est applique dans le code v5.9.4; le rapport garde le refus tel quel. L'entree, le script de preparation, le statut, le journal complet et leurs empreintes sont dans le ZIP.", styles["BodyFR"]),
              PageBreak()]

    # Full console logs: deterministic, unedited except wrapping for page width.
    story += [paragraph("Appendice A. Journaux console complets", styles["H1FR"]),
              paragraph("Les journaux ci-dessous sont des copies textuelles des console.log; les lignes sont repliees visuellement pour le PDF. Les originaux byte-identiques sont dans le ZIP.", styles["SmallFR"])]
    for control in controls:
        log_path = RUN_DIR / control / "console.log"
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        wrapped = "\n".join(piece for line in log_text.splitlines() for piece in (textwrap.wrap(line, width=155, subsequent_indent="  ") or [""]))
        story += [paragraph(f"Controle: {html.escape(control)}", styles["H2FR"]), Preformatted(wrapped, styles["LogFR"]), Spacer(1, 6)]

    story += [PageBreak(), paragraph("Appendice B. Inventaire SHA-256 des sorties", styles["H1FR"]),
              paragraph("Les valeurs du tableau sont calculables sur les fichiers du ZIP. Les huit pieces de preuve supplementaires (scripts, inputs et syntheses) sont inventoriees dans le manifeste JSON joint.", styles["SmallFR"])]
    manifest_rows = [["Controle / fichier relatif", "Octets", "SHA-256"]]
    for item in audit["files"]:
        rel = Path(item["path"]).relative_to(RUN_DIR).as_posix()
        manifest_rows.append([rel, str(item["bytes"]), item["sha256"]])
    hash_table = LongTable(manifest_rows, colWidths=[286, 68, 330], repeatRows=1, hAlign="LEFT")
    hash_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, 0), 7), ("FONTSIZE", (0, 1), (-1, -1), 5.1),
        ("LEADING", (0, 1), (-1, -1), 6.2), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5DA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(hash_table)

    mouse_log_text = (MOUSE_FAIL_DIR / "console.log").read_text(encoding="utf-8", errors="replace")
    wrapped_mouse_log = "\n".join(piece for line in mouse_log_text.splitlines() for piece in (textwrap.wrap(line, width=155, subsequent_indent="  ") or [""]))
    story += [PageBreak(), paragraph("Appendice C. Journal complet de l'essai souris bloque", styles["H1FR"]),
              paragraph("Copie du journal console enregistre; le fichier byte-identique et le statut de sortie sont dans le ZIP.", styles["SmallFR"]),
              Preformatted(wrapped_mouse_log, styles["LogFR"])]

    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    writer = PdfWriter(clone_from=REPORT_PDF)
    writer.add_attachment(BUNDLE_ZIP.name, BUNDLE_ZIP.read_bytes())
    writer.add_metadata({
        "/Title": "Audit execution UNIVERSAL_LOG v5.9.4 - PC69 / GSE271300",
        "/Subject": "Rapport d'audit, 17 controles, sorties en piece jointe",
        "/Author": "Projet UNIVERSAL_LOG",
        "/Keywords": "PDAC, GSE271300, UNIVERSAL_LOG, audit, Cohen-d",
    })
    tmp_pdf = REPORT_PDF.with_name(REPORT_PDF.stem + ".attached.tmp.pdf")
    with tmp_pdf.open("wb") as handle:
        writer.write(handle)
    tmp_pdf.replace(REPORT_PDF)


def main() -> None:
    summary = safe_json(SUMMARY_JSON)
    audit = safe_json(AUDIT_JSON)
    run_summary = safe_json(RUN_DIR / "RUN_SUMMARY.json")
    rows = summary["rows"]
    controls = summary["controls_requested"]
    make_chart(rows)
    create_bundle(summary, audit, safe_json(INPUT_MANIFEST))
    # Refresh bundle fingerprint after bundle creation; the audit manifest remains the hash ledger for run artifacts.
    generate_pdf(summary, audit, run_summary, rows, controls)

    reader = PdfReader(REPORT_PDF)
    attachment_names = list((reader.attachments or {}).keys())
    if BUNDLE_ZIP.name not in attachment_names:
        raise RuntimeError(f"PDF bundle attachment missing: {attachment_names}")
    if len(reader.pages) < 8:
        raise RuntimeError(f"PDF unexpectedly short: {len(reader.pages)} pages")
    print(f"PDF: {REPORT_PDF} ({len(reader.pages)} pages)")
    print(f"PDF embedded attachment: {BUNDLE_ZIP.name} ({BUNDLE_ZIP.stat().st_size} bytes)")
    print(f"ZIP: {BUNDLE_ZIP} ({BUNDLE_ZIP.stat().st_size} bytes; SHA-256 {sha256(BUNDLE_ZIP)})")
    print(f"Chart: {CHART_PNG}")
    print(f"SHA file: {SHA_FILE}")


if __name__ == "__main__":
    main()
