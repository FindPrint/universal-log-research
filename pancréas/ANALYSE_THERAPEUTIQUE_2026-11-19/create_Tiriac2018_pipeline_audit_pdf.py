from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = HERE / "candidate_Tiriac2018"
RUN = HERE / "Tiriac2018_Gemcitabine_all_controls_PDACDomain"
SUMMARY_JSON = RUN / "PIPELINE_OUTPUT_SUMMARY.json"
SUMMARY_CSV = RUN / "PIPELINE_OUTPUT_SUMMARY.csv"
SUMMARY_MD = RUN / "PIPELINE_OUTPUT_SUMMARY.md"
CHART = RUN / "GEMCITABINE_T0_BY_CONTROL.png"
INPUT_MANIFEST = DATA / "PIPELINE_INPUT_MANIFEST.json"
RUN_MANIFEST = RUN / "RUN_MATRIX_MANIFEST.json"
RUN_STATUS = RUN / "RUN_MATRIX_STATUS.json"
PIPELINE = ROOT / "UNIVERSAL_LOG_v5.9.4.py"
BUNDLE = ROOT / "output" / "pdac_pipeline_audit_2026-11-19" / "TIRIAC2018_GEMCITABINE_ALL_CONTROLS_PDAC_AUDIT_BUNDLE.zip"
OUTPUT_DIR = ROOT / "output" / "pdac_pipeline_audit_2026-11-19"
TEMP_PDF = OUTPUT_DIR / "TIRIAC2018_PDCAUDIT_WORKING.pdf"
OUTPUT_PDF = OUTPUT_DIR / "UNIVERSAL_LOG_TIRIAC2018_PDCAUDIT_ADDENDUM_2026-11-19.pdf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def register_fonts() -> None:
    regular = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    italic = Path(r"C:\Windows\Fonts\ariali.ttf")
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("AuditArial", str(regular)))
        pdfmetrics.registerFont(TTFont("AuditArial-Bold", str(bold)))
        if italic.is_file():
            pdfmetrics.registerFont(TTFont("AuditArial-Italic", str(italic)))
        pdfmetrics.registerFontFamily(
            "AuditArial", normal="AuditArial", bold="AuditArial-Bold", italic="AuditArial-Italic", boldItalic="AuditArial-Bold"
        )
        return
    fallback = Path(r"C:\Windows\Fonts\calibri.ttf")
    fallback_bold = Path(r"C:\Windows\Fonts\calibrib.ttf")
    if fallback.is_file() and fallback_bold.is_file():
        pdfmetrics.registerFont(TTFont("AuditArial", str(fallback)))
        pdfmetrics.registerFont(TTFont("AuditArial-Bold", str(fallback_bold)))
        pdfmetrics.registerFontFamily("AuditArial", normal="AuditArial", bold="AuditArial-Bold")
        return
    raise FileNotFoundError("No TrueType font covering French text was found in C:\\Windows\\Fonts")


def on_page(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.setLineWidth(0.5)
        canvas.line(0.55 * inch, height - 0.42 * inch, width - 0.55 * inch, height - 0.42 * inch)
        canvas.setFont("AuditArial", 7.6)
        canvas.setFillColor(colors.HexColor("#334155"))
        canvas.drawString(0.55 * inch, height - 0.30 * inch, "UNIVERSAL_LOG | AUDIT PDAC | TIRIAC 2018")
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(0.55 * inch, 0.46 * inch, width - 0.55 * inch, 0.46 * inch)
    canvas.setFont("AuditArial", 7.4)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(0.55 * inch, 0.28 * inch, "Annexe d'audit - résultats bruts et reproductibilité")
    canvas.drawRightString(width - 0.55 * inch, 0.28 * inch, f"Page {doc.page}")
    canvas.restoreState()


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def build_pdf() -> None:
    for path in (SUMMARY_JSON, SUMMARY_CSV, SUMMARY_MD, CHART, INPUT_MANIFEST, RUN_MANIFEST, RUN_STATUS, PIPELINE, BUNDLE):
        if not path.is_file():
            raise FileNotFoundError(path)

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    inp = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
    run = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
    status = json.loads(RUN_STATUS.read_text(encoding="utf-8"))
    if summary["completed_exit_zero"] != 25 or summary["errors_or_missing"] != 0:
        raise ValueError("PDF is created only after all 25 controls finish successfully")
    if any(row.get("domain_used") != "pdac" or row.get("target_used") != "Gemcitabine" for row in summary["results"]):
        raise ValueError("Unexpected domain or target in an output; refusing to create the audit PDF")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "AuditTitle", parent=base["Title"], fontName="AuditArial-Bold", fontSize=24, leading=30,
        textColor=colors.HexColor("#102A43"), alignment=TA_LEFT, spaceAfter=12,
    )
    subtitle = ParagraphStyle(
        "AuditSubtitle", parent=base["Normal"], fontName="AuditArial", fontSize=11.5, leading=16,
        textColor=colors.HexColor("#486581"), spaceAfter=8,
    )
    h1 = ParagraphStyle(
        "AuditH1", parent=base["Heading1"], fontName="AuditArial-Bold", fontSize=15, leading=19,
        textColor=colors.HexColor("#102A43"), spaceBefore=6, spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "AuditH2", parent=base["Heading2"], fontName="AuditArial-Bold", fontSize=10.5, leading=14,
        textColor=colors.HexColor("#1F4E79"), spaceBefore=7, spaceAfter=4,
    )
    body = ParagraphStyle(
        "AuditBody", parent=base["BodyText"], fontName="AuditArial", fontSize=9.1, leading=13.3,
        textColor=colors.HexColor("#243B53"), spaceAfter=6,
    )
    small = ParagraphStyle(
        "AuditSmall", parent=body, fontSize=7.8, leading=10.4, spaceAfter=3,
    )
    small_bold = ParagraphStyle("AuditSmallBold", parent=small, fontName="AuditArial-Bold")
    cover_kicker = ParagraphStyle(
        "CoverKicker", parent=body, fontName="AuditArial-Bold", fontSize=9.3, leading=13,
        textColor=colors.HexColor("#0F766E"), spaceAfter=10,
    )
    center = ParagraphStyle("Center", parent=body, alignment=TA_CENTER)

    doc = SimpleDocTemplate(
        str(TEMP_PDF), pagesize=letter,
        leftMargin=0.62 * inch, rightMargin=0.62 * inch,
        topMargin=0.66 * inch, bottomMargin=0.62 * inch,
        title="UNIVERSAL_LOG PDAC Tiriac 2018 Audit Addendum",
        author="UNIVERSAL_LOG pipeline audit",
        subject="Reproducible all-control-column run on PDAC PDO AUC profiles",
    )
    story = []
    story.extend([
        Spacer(1, 0.75 * inch),
        para("AUDIT D'EXÉCUTION | 19 NOVEMBRE 2026", cover_kicker),
        para("UNIVERSAL_LOG sur des profils d'organoïdes PDAC", title),
        para("Annexe reproductible - Tiriac et al. 2018, Tables S4A/S4B", subtitle),
        Spacer(1, 0.18 * inch),
    ])
    cover_box = [
        [para("Données", small_bold), para("60 PDO complets; 26 profils AUC; 5 chimiothérapies et 21 agents ciblés.", body)],
        [para("Lancement", small_bold), para("UNIVERSAL_LOG v5.9.4; domaine PDAC; mode fast; 25 contrôles; graine 42.", body)],
        [para("Cible fixe", small_bold), para("Gemcitabine AUC, choisie comme ancre de la première passe de contrôle.", body)],
        [para("Statut", small_bold), para("25/25 contrôles terminés avec code de sortie 0.", body)],
    ]
    cover_table = Table(cover_box, colWidths=[1.2 * inch, 5.9 * inch])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.extend([
        cover_table, Spacer(1, 0.28 * inch),
        para("Ce document rapporte les entrées, réglages et sorties effectivement produits. Il sépare les choix de conception des résultats exportés et ne transforme pas une mesure in vitro en recommandation clinique.", body),
        Spacer(1, 0.18 * inch),
        para("Source principale : <link href='https://doi.org/10.1158/2159-8290.CD-18-0349' color='#1D4ED8'>Tiriac et al., Cancer Discovery, 2018</link>.", small),
        PageBreak(),
    ])

    story.extend([
        para("1. Résumé de l'exécution", h1),
        para(
            f"Le pipeline a exécuté la cible fixe <b>Gemcitabine</b> contre chacun des {status['n_controls_requested']} autres profils AUC. "
            f"Les {status['n_completed']} contrôles ont retourné le code 0; le résumé compte {summary['t0_ambiguous_count']} sorties T0 ambiguës "
            f"et {summary['t0_nonambiguous_count']} non ambiguës, selon le drapeau écrit par le pipeline.", body,
        ),
        para("Ces nombres décrivent uniquement les fichiers de sortie. Ils ne sont ni des tests d'efficacité thérapeutique ni des résultats de survie patient.", body),
        para("Données de l'étude", h2),
        para(
            "Les Tables S4A et S4B contiennent chacune 66 lignes de PDO. Après normalisation de l'espace de l'identifiant, "
            "65 identifiants sont présents dans les deux tables. Les lignes sans essai apparié (<b>hT83</b> côté chimiothérapie et "
            "<b>hT96</b> côté agents ciblés) ont été exclues. Cinq PDO ayant une AUC manquante ont ensuite été retirés sans imputation; "
            "l'entrée commune finale contient <b>60 PDO</b> et <b>26 flux numériques</b>.", body,
        ),
        para("Les AUC ont été copiées sans transformation. La colonne catégorielle `Insensitive` n'est pas incluse dans le CSV numérique, car elle n'est pas une AUC et son seuil de codage n'est pas défini par la clé conservée.", body),
        para("Provenance locale", h2),
        para(f"CSV d'entrée SHA-256 : <font name='Courier'>{run['input_sha256']}</font>.<br/>Pipeline SHA-256 : <font name='Courier'>{run['pipeline_sha256']}</font>.", small),
        PageBreak(),
    ])

    story.extend([
        para("2. Protocole et choix de conception", h1),
        para("Les points ci-dessous distinguent le choix de configuration de ce que la sortie peut établir.", body),
    ])
    design_rows = [
        [para("Élément", small_bold), para("Configuration utilisée", small_bold), para("Portée", small_bold)],
        [para("Unité", small_bold), para("Un PDO par ligne; 60 lignes complètes.", small), para("L'unité n'est ni une cellule ni un patient indépendant supplémentaire.", small)],
        [para("Cible", small_bold), para("Gemcitabine AUC fixe.", small), para("Ancre opérationnelle issue du panneau de chimiothérapie; pas un résultat choisi après examen du pipeline.", small)],
        [para("Contrôles", small_bold), para("Les 25 autres colonnes AUC, une par exécution.", small), para("Tous les profils non cibles du CSV ont joué le rôle de contrôle.", small)],
        [para("Flux", small_bold), para("Les autres colonnes numériques restent dans l'entrée multiflux.", small), para("Le pipeline conserve les interactions entre les flux selon sa logique interne.", small)],
        [para("Axe", small_bold), para("AUC du contrôle sélectionné; lignes conservées dans l'ordre de la Table S4A.", small), para("Aucune date, durée de maladie ou trajectoire temporelle n'est fournie par ce jeu.", small)],
        [para("Exécution", small_bold), para("Domaine `pdac`; mode `fast`; Cohen-d; graine 42; L7b light; sans graphiques pipeline.", small), para("Les exports numériques et journaux ont été gardés; quatre processus simultanés, un worker interne par processus.", small)],
        [para("Seuils", small_bold), para("Aucun seuil de sensibilité ou de réponse clinique ajouté.", small), para("Aucune conversion AUC vers réponse patient n'a été faite.", small)],
    ]
    design_table = Table(design_rows, colWidths=[0.9 * inch, 2.8 * inch, 3.45 * inch], repeatRows=1)
    design_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F1F5F9")),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        design_table,
        Spacer(1, 10),
        para("Choix distincts du résultat", h2),
        para("Gemcitabine comme cible fixe et les autres profils comme contrôles sont des décisions de protocole enregistrées dans le manifeste. Elles ne sont pas une conclusion tirée des sorties. L'axe pipeline est exploratoire pour ces données transversales; aucun T0 ne sera décrit comme l'apparition d'un cancer ou un seuil de traitement.", body),
        PageBreak(),
    ])

    story.extend([
        para("3. Sorties brutes du pipeline", h1),
        para("Le tableau respecte l'ordre des colonnes source. Les contrôles ne sont pas classés par T0. La valeur T0 est rapportée dans l'unité de progression du pipeline; l'ambiguïté est le champ exporté par le pipeline.", body),
    ])
    table_data = [[
        para("Contrôle AUC", small_bold), para("Statut", small_bold), para("N", small_bold),
        para("T0 (%)", small_bold), para("Ambigu", small_bold), para("Monotone", small_bold),
    ]]
    for row in summary["results"]:
        value = row.get("t0_pct")
        table_data.append([
            para(str(row["control"]), small),
            para(str(row.get("status", "missing")), small),
            para(str(row.get("n_samples", "-")), small),
            para(f"{float(value):.5f}" if isinstance(value, (int, float)) else "-", small),
            para(str(row.get("t0_ambiguous", "-")), small),
            para(str(row.get("control_monotone", "-")), small),
        ])
    results_table = Table(table_data, colWidths=[1.9 * inch, 0.7 * inch, 0.45 * inch, 0.82 * inch, 0.85 * inch, 0.9 * inch], repeatRows=1)
    results_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([results_table, PageBreak()])

    story.extend([
        para("4. Vue des T0 exportés", h1),
        para("Le graphique visualise uniquement les valeurs T0 présentes dans les fichiers du pipeline. L'ambre signifie que le pipeline a lui-même marqué T0 ambigu. Aucun tri de médicament ni classement d'efficacité n'est appliqué.", body),
    ])
    chart = Image(str(CHART))
    max_w, max_h = 7.1 * inch, 7.5 * inch
    scale = min(max_w / chart.imageWidth, max_h / chart.imageHeight)
    chart.drawWidth = chart.imageWidth * scale
    chart.drawHeight = chart.imageHeight * scale
    story.extend([chart, PageBreak()])

    story.extend([
        para("5. Observations, limites et portée thérapeutique", h1),
        para("Observations", h2),
        para(
            f"- Entrée finale: {inp['observations']} PDO et {inp['n_fluxes']} mesures AUC numériques.<br/>"
            f"- Contrôles terminés: {status['n_completed']}/{status['n_controls_requested']}; erreurs: {status['n_error']}.<br/>"
            f"- T0 ambigu selon l'export: {summary['t0_ambiguous_count']}/{status['n_controls_requested']}.<br/>"
            "- Pour chaque contrôle, le bundle conserve `master_results.json`, les CSV/JSON/TXT annexes, la commande et le journal console.", body,
        ),
        para("Ce que ces sorties ne démontrent pas", h2),
        para("Le CSV ne contient pas un résultat clinique patient pour ces 60 lignes, ni une étude randomisée de traitement, ni un suivi de guérison. Un T0 issu d'un profil d'AUC transversal n'est pas une preuve de transition tumorale, de causalité, d'efficacité, de dose ou de remède. Ces sorties ne doivent pas guider le traitement d'une personne.", body),
        para("Étape de recherche qui suit", h2),
        para("Après cet audit d'exécution, la suite utile est une validation indépendante contre une cible clinique préspécifiée (réponse RECIST, progression-free survival ou autre endpoint défini dans la cohorte), avec le patient comme unité et séparation stricte entraînement/test. Les agents ciblés restent des profils expérimentaux ici; la table ne permet pas de proposer un traitement.", body),
        PageBreak(),
    ])

    story.extend([
        para("6. Reproduction et empreintes", h1),
        para("Depuis la racine `<PROJECT_ROOT>`, avec l'environnement `.venv` fourni:", body),
    ])
    commands = [
        r".venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-19\prepare_Tiriac2018_pipeline_data.py",
        r".venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-19\run_Tiriac2018_gemcitabine_all_controls.py",
        r".venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-19\summarize_Tiriac2018_pipeline_run.py",
        r".venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-19\package_Tiriac2018_pipeline_audit.py",
    ]
    cmd_table = Table([[para(cmd.replace("&", "&amp;"), small)] for cmd in commands], colWidths=[7.05 * inch])
    cmd_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    hashes = [
        [para("Fichier", small_bold), para("SHA-256", small_bold)],
        [para("UNIVERSAL_LOG_v5.9.4.py", small), para(f"<font name='Courier'>{run['pipeline_sha256']}</font>", small)],
        [para("CSV complet-case", small), para(f"<font name='Courier'>{run['input_sha256']}</font>", small)],
        [para("Bundle joint", small), para(f"<font name='Courier'>{sha256(BUNDLE)}</font>", small)],
        [para("Source S4A/S4B", small), para(f"<font name='Courier'>{inp['source_files'][0]['sha256']}</font>", small)],
    ]
    hash_table = Table(hashes, colWidths=[1.7 * inch, 5.35 * inch], repeatRows=1)
    hash_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        cmd_table, Spacer(1, 8), hash_table, Spacer(1, 10),
        para("Le PDF contient le bundle ZIP complet comme pièce jointe intégrée. Le ZIP contient le code pipeline exact, les sources, le CSV, la liste des dépendances, les manifests, les journaux et les exports des 25 contrôles.", body),
        para("Essai de cadrage interrompu", h2),
        para("Une première matrice sans `--domain pdac` a inscrit `domain=generic`. Quatre sorties terminées sont conservées dans le bundle sous `aborted_generic_attempt/`, avec leur note d'arrêt; elles ne sont pas mélangées aux 25 sorties PDAC.", small),
        para("Les fichiers sources d'article gardent leurs droits et attributions d'origine. La licence du projet ne leur est pas appliquée.", small),
    ])

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    # Embed the complete run bundle so the PDF and the archive can be archived together.
    reader = PdfReader(str(TEMP_PDF))
    writer = PdfWriter()
    writer.append(reader)
    writer.add_attachment(BUNDLE.name, BUNDLE.read_bytes())
    with OUTPUT_PDF.open("wb") as stream:
        writer.write(stream)
    TEMP_PDF.unlink(missing_ok=True)

    final_reader = PdfReader(str(OUTPUT_PDF))
    root = final_reader.trailer["/Root"]
    embedded_names = root.get("/Names", {}).get("/EmbeddedFiles", {}).get("/Names", [])
    attached = [str(embedded_names[i]) for i in range(0, len(embedded_names), 2)]
    if BUNDLE.name not in attached:
        raise RuntimeError(f"PDF attachment is missing: {attached}")
    print(json.dumps({
        "pdf": str(OUTPUT_PDF),
        "bytes": OUTPUT_PDF.stat().st_size,
        "pages": len(final_reader.pages),
        "embedded_files": attached,
        "pdf_sha256": sha256(OUTPUT_PDF),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    build_pdf()
