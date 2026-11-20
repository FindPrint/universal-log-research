from __future__ import annotations

import hashlib
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from pypdf import PdfReader, PdfWriter


PROJECT = Path(__file__).resolve().parents[2]
ANALYSIS = PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20"
OUTDIR = Path(__file__).resolve().parent
BASE_PDF = OUTDIR / "PDAC_EXTERNAL_REPLICATION_SCREEN_ADDENDUM_2026-11-20_base.pdf"
FINAL_PDF = OUTDIR / "PDAC_EXTERNAL_REPLICATION_SCREEN_ADDENDUM_2026-11-20.pdf"
BUNDLE = OUTDIR / "PDAC_EXTERNAL_REPLICATION_SCREEN_AUDIT_2026-11-20.zip"

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#167C80")
PALE = colors.HexColor("#EAF1F5")
PALE_TEAL = colors.HexColor("#E7F3F2")
PALE_GOLD = colors.HexColor("#FFF3D6")
INK = colors.HexColor("#24323D")
MUTED = colors.HexColor("#62727E")
LINE = colors.HexColor("#C9D4DC")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=5))
styles.add(ParagraphStyle(name="SubTitleX", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=15, textColor=MUTED, spaceAfter=13))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=7, spaceAfter=8))
styles.add(ParagraphStyle(name="H2X", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=13.1, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9.5, textColor=INK, spaceAfter=0))
styles.add(ParagraphStyle(name="TinyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=6.9, leading=9, textColor=INK, spaceAfter=0))
styles.add(ParagraphStyle(name="TableHeadX", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.4, leading=9.5, textColor=colors.white, spaceAfter=0))
styles.add(ParagraphStyle(name="CalloutX", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10.2, leading=14, textColor=NAVY, spaceAfter=0))
styles.add(ParagraphStyle(name="CodeX", parent=styles["Code"], fontName="Courier", fontSize=8, leading=11, textColor=INK, leftIndent=4, rightIndent=4, spaceAfter=0))
styles.add(ParagraphStyle(name="CenterSmallX", parent=styles["SmallX"], alignment=TA_CENTER))


def para(text: str, style: str = "BodyX") -> Paragraph:
    return Paragraph(text, styles[style])


def decorate(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 7 * mm, width, 7 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "UNIVERSAL_LOG | Audit de réplication PDAC | 2026-11-20")
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_base_pdf() -> None:
    doc = SimpleDocTemplate(
        str(BASE_PDF), pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=21 * mm,
        title="PDAC external-data screen and pipeline gate",
        author="UNIVERSAL_LOG audit",
        subject="External PDAC drug-response dataset screen and N=46 pipeline rejection",
    )
    story = []
    story += [
        Spacer(1, 4 * mm),
        para("Réplication externe PDAC", "TitleX"),
        para("Audit de disponibilité des données et essai pilote du pipeline | 20 novembre 2026", "SubTitleX"),
    ]
    gate = Table([[para("PILOTE REFUSÉ PAR LE SEUIL D’ENTRÉE", "CalloutX"), para("46 modèles PDO observés; le pipeline exige au moins 50 points valides.", "BodyX")]], colWidths=[58 * mm, 112 * mm])
    gate.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_GOLD),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D7B35A")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [gate, Spacer(1, 4 * mm)]
    story += [
        para("Ce document consigne la recherche d’une cohorte PDAC externe et le premier appel au pipeline sur le meilleur tableau public trouvé. L’appel a été arrêté avant le calcul des estimateurs par le contrôle d’effectif interne au pipeline. Aucun résultat biologique ou thérapeutique n’en découle.", "BodyX"),
        para("Candidats examinés", "H1X"),
    ]
    rows = [
        [para("Source", "TableHeadX"), para("Données observées", "TableHeadX"), para("Décision", "TableHeadX")],
        [para("Chen et al., Nature Communications 2025", "SmallX"), para("AUC de 63 médicaments sur 46 PDO; tableau par modèle accessible.", "SmallX"), para("Pilote uniquement; N=46 sous le minimum.", "SmallX")],
        [para("Nicholson et al., Annals of Surgery 2024", "SmallX"), para("Article: 95 PDO, IC50 pour 5 agents. Le supplément accessible contient code et résultats agrégés, pas la matrice IC50 par PDO.", "SmallX"), para("Non exécutable avec les fichiers publics consultés.", "SmallX")],
        [para("Feizi et al., AACR 2025", "SmallX"), para("Résumé: 120 PDO PDAC et criblage de milliers de composés; matrice ligne par ligne non jointe au résumé consulté.", "SmallX"), para("Piste d’accès aux données, pas un jeu public exécutable.", "SmallX")],
        [para("GSE271300", "SmallX"), para("Données unicellulaires de PDX; 3/3 et 4/3 souris par groupe dans les deux modèles analysés localement.", "SmallX"), para("Pas une cohorte pharmacotypée par PDO; N souris insuffisant.", "SmallX")],
        [para("Zhu et al., prépublication 2026", "SmallX"), para("57 PDO dans colorectal, tête-cou et sarcome; aucun modèle PDAC décrit.", "SmallX"), para("Hors domaine PDAC.", "SmallX")],
    ]
    table = Table(rows, colWidths=[42 * mm, 82 * mm, 46 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [table, Spacer(1, 3 * mm)]
    story += [
        para("Le meilleur tableau public contient des valeurs AUC par modèle et par médicament, mais son effectif n’atteint pas le minimum du pipeline. Les modèles restent à N=46; aucune cellule ni répétition technique n’a été utilisée pour gonfler N.", "BodyX"),
        PageBreak(),
        para("Essai pilote : configuration et observation", "H1X"),
    ]
    config_rows = [
        [para("Élément", "TableHeadX"), para("Choix consigné", "TableHeadX")],
        [para("Entrée", "SmallX"), para("NatureComm2025_Supplementary_Data10.xlsx, onglet All Drugs AUC; 46 PDO × 63 médicaments; aucune valeur manquante.", "SmallX")],
        [para("Préparation", "SmallX"), para("Transposition seulement; ordre des PDO source conservé; AUC non transformées; aucune imputation, agrégation ou réorganisation.", "SmallX")],
        [para("Cible et contrôles", "SmallX"), para("Gemcitabine cible fixe, choisie pour comparer à l’essai Tiriac précédent; 62 autres flux prévus comme contrôles individuels.", "SmallX")],
        [para("Pipeline", "SmallX"), para("v5.9.4, .venv, domaine pdac, mode fast, seed 42, L7b-light; un worker par appel.", "SmallX")],
        [para("Appel effectivement lancé", "SmallX"), para("Contrôle APR-246, premier médicament après Gemcitabine dans l’ordre source. Durée: 12,153 s.", "SmallX")],
    ]
    config = Table(config_rows, colWidths=[43 * mm, 127 * mm], repeatRows=1)
    config.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_TEAL]),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [config, Spacer(1, 4 * mm), para("Sortie exacte du pipeline", "H2X")]
    error_box = Table([[para("Série trop courte : 46 points valides. Au moins 50 sont requis avec la configuration actuelle.", "CodeX")]], colWidths=[170 * mm])
    error_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [error_box, Spacer(1, 3 * mm)]
    story += [
        para("Conséquence observée", "H2X"),
        para("Le pipeline s’est arrêté avant le calcul des estimateurs. Il n’y a ni T0, ni comparaison de médicaments, ni résultat de traitement à rapporter pour cette cohorte. Les 61 autres appels auraient rencontré le même refus d’entrée; ils n’ont pas été lancés.", "BodyX"),
        para("Prochaine donnée requise", "H2X"),
        para("Pour une réplication valide: une matrice de réponses médicamenteuses par PDO PDAC avec au moins 50 modèles indépendants et des valeurs numériques disponibles. La série de criblage de Toronto (58 modèles dans un résumé 2022; 120 modèles dans le résumé AACR 2025) est une piste d’accès aux données, mais aucun contact n’a été envoyé et les matrices brutes ne sont pas jointes aux résumés publics consultés.", "BodyX"),
        para("Sources consultées", "H2X"),
        para('<link href="https://doi.org/10.1038/s41467-025-57520-3" color="#167C80">Chen et al., Nature Communications 2025, DOI 10.1038/s41467-025-57520-3</link>  |  <link href="https://doi.org/10.1097/SLA.0000000000006517" color="#167C80">Nicholson et al., Annals of Surgery 2024, DOI 10.1097/SLA.0000000000006517</link>', "TinyX"),
        para('<link href="https://www.aacr.org/wp-content/uploads/2025/05/AACR2025_Proceedings_050725.pdf" color="#167C80">Feizi et al., AACR 2025 abstract 3161</link>  |  <link href="https://arxiv.org/abs/2611.15769" color="#167C80">Zhu et al., arXiv 2611.15769</link>  |  <link href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300" color="#167C80">GEO GSE271300</link>', "TinyX"),
        Spacer(1, 2 * mm),
        para("L’archive ZIP complète est jointe à ce PDF : sources téléchargées, empreintes, entrée transposée, protocole verrouillé, scripts, rapport de tri, environnement, sortie et journal exacts.", "SmallX"),
    ]
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)


def attach_audit_bundle() -> None:
    reader = PdfReader(str(BASE_PDF))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.add_attachment(BUNDLE.name, BUNDLE.read_bytes())
    writer.add_metadata({
        "/Title": "PDAC external-data screen and pipeline gate - 2026-11-20",
        "/Author": "UNIVERSAL_LOG audit",
        "/Subject": "Exploratory N=46 dataset rejected by the pipeline minimum; complete audit attached.",
    })
    with FINAL_PDF.open("wb") as stream:
        writer.write(stream)
    reopened = PdfReader(str(FINAL_PDF), strict=False)
    with reader_context():
        attachments = reopened.attachments
        names = list(attachments.keys())
        if BUNDLE.name not in names:
            raise RuntimeError(f"Audit archive missing from PDF attachment names: {names}")
        data = attachments[BUNDLE.name][0]
    if hashlib.sha256(data).hexdigest() != sha256(BUNDLE):
        raise RuntimeError("Embedded audit archive hash does not match external ZIP")
    print(f"pages={len(reopened.pages)}")
    print(f"embedded={BUNDLE.name} bytes={len(data)} sha256={sha256(BUNDLE)}")
    print(f"pdf_sha256={sha256(FINAL_PDF)}")


def reader_context():
    from pypdf._configuration import apply_configuration

    return apply_configuration(maximum_declared_stream_length=50_000_000)


def main() -> None:
    if not BUNDLE.is_file():
        raise FileNotFoundError(BUNDLE)
    build_base_pdf()
    attach_audit_bundle()
    digest_path = OUTDIR / "PDAC_EXTERNAL_REPLICATION_SCREEN_ADDENDUM_2026-11-20_SHA256.txt"
    digest_path.write_text(f"{sha256(FINAL_PDF)}  {FINAL_PDF.name}\n", encoding="ascii")


if __name__ == "__main__":
    main()
