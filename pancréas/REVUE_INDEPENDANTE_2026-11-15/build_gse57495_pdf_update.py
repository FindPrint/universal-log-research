"""Append a traceable GSE57495 update to the existing PDAC white paper."""

from __future__ import annotations

import io
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
SOURCE_PDF = PROJECT / "pancréas" / "livre-blanc-pdac-v6.pdf"
OUTPUT_PDF = PROJECT / "pancréas" / "livre-blanc-pdac-v6.1-2026-11-15.pdf"
RESULTS = ROOT / "data_GSE57495" / "GSE57495_holdout_results.json"
MANIFEST = ROOT / "data_GSE57495" / "GSE57495_holdout_manifest.json"
FIGURE = ROOT / "data_GSE57495" / "GSE57495_holdout_results.png"
SUMMARY = ROOT / "cohort_replication_summary.csv"

BLUE = colors.HexColor("#163B63")
BLUE_LIGHT = colors.HexColor("#E9F1F8")
TEAL = colors.HexColor("#1D756E")
GREY = colors.HexColor("#5B6570")
PALE = colors.HexColor("#F5F7FA")


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=21, leading=26, textColor=BLUE, alignment=TA_LEFT, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=15, leading=19, textColor=BLUE, spaceBefore=1, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SubTitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10.5, leading=15, textColor=GREY, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="BodyAudit", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.1, leading=13.1, spaceAfter=7, textColor=colors.HexColor("#202830"),
    ))
    styles.add(ParagraphStyle(
        name="SmallAudit", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.4, leading=9.7, textColor=GREY, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="TableHeadAudit", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=8.4, leading=10, textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="TableCellAudit", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.3, leading=10.2, textColor=colors.HexColor("#202830"),
    ))
    styles.add(ParagraphStyle(
        name="CalloutAudit", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=10.2, leading=15, textColor=BLUE, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="CenterSmallAudit", parent=styles["SmallAudit"], alignment=TA_CENTER,
    ))
    return styles


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def header_footer(canvas, document):
    canvas.saveState()
    width, height = letter
    canvas.setStrokeColor(colors.HexColor("#D7DEE7"))
    canvas.setLineWidth(0.55)
    canvas.line(44, height - 31, width - 44, height - 31)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(BLUE)
    canvas.drawString(44, height - 24, "UNIVERSAL_LOG x PDAC | Mise a jour d'audit")
    canvas.setStrokeColor(colors.HexColor("#D7DEE7"))
    canvas.line(44, 31, width - 44, 31)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(44, 19, "Addendum GSE57495 | 15 novembre 2026")
    canvas.drawRightString(width - 44, 19, f"Page {document.page} de l'appendice")
    canvas.restoreState()


def make_appendix() -> bytes:
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    styles = build_styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, leftMargin=44, rightMargin=44,
        topMargin=48, bottomMargin=44, title="Mise a jour audit GSE57495",
        author="Audit de reproductibilite UNIVERSAL_LOG x PDAC",
    )
    story = []

    # Page 1: headline result and place it beside the previous cohort results.
    story += [
        Spacer(1, 8),
        paragraph("ADDENDUM D'AUDIT", styles["SmallAudit"]),
        paragraph("Validation externe dans GSE57495", styles["CoverTitle"]),
        paragraph("Livre blanc PDAC v6.1 | 15 novembre 2026 | Analyse du signal d'expression ARN CEACAM5-KRAS", styles["SubTitle"]),
    ]
    primary = result["primary"]
    rho = primary["rho"]
    ci_low, ci_high = primary["bootstrap_ci_95_percentile"]
    pvalue = primary["permutation_p_one_sided_positive"]
    n = result["n_complete_pairs"]
    callout = Table([[paragraph(
        f"<b>Resultat primaire.</b> Sur {n} echantillons, CEACAM5 et KRAS sont positivement associes : "
        f"Spearman rho={rho:.3f}; p de permutation unilateral={pvalue:.5f}; "
        f"IC bootstrap 95 % [{ci_low:.3f}, {ci_high:.3f}]. Le critere directionnel gele est satisfait.",
        styles["CalloutAudit"],
    )]], colWidths=[7.28 * inch])
    callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#B9CDDF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story += [callout, Spacer(1, 13), paragraph("Comparaison avec les cohortes precedentes", styles["SectionTitle"])]

    rows = [
        [paragraph("Cohorte", styles["TableHeadAudit"]), paragraph("n", styles["TableHeadAudit"]), paragraph("Spearman rho", styles["TableHeadAudit"])],
        [paragraph("TCGA-PAAD", styles["TableCellAudit"]), "178", "0.343"],
        [paragraph("GEO GSE71729", styles["TableCellAudit"]), "145", "0.274"],
        [paragraph("GEO GSE62452", styles["TableCellAudit"]), "69", "0.441"],
        [paragraph("GEO GSE57495 - test externe", styles["TableCellAudit"]), "63", f"{rho:.3f}"],
    ]
    table = Table(rows, colWidths=[3.8 * inch, 0.8 * inch, 1.6 * inch], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("BACKGROUND", (0, 4), (-1, 4), BLUE_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7DEE7")),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [table, Spacer(1, 8), paragraph(
        "L'association est positive dans les quatre cohortes examinees. GSE57495 n'a pas participe au calcul des trois estimations precedentes, mais la cible CEACAM5-KRAS a ete retenue apres les resultats anterieurs. Il s'agit donc d'une replication de cohorte exploratoire, pas d'un test confirmatoire preregistre avant le projet. Les p-values des quatre analyses ne sont pas directement comparables, car leurs procedures d'inference different.",
        styles["BodyAudit"],
    ), paragraph(
        "Portee : ces donnees montrent une association transversale entre deux mesures d'ARN dans des tumeurs. Elles ne montrent pas une causalite, une mutation KRAS, une evolution temporelle, un biomarqueur sanguin, un benefice therapeutique, ni la validite de TLog ou d'UNIVERSAL_LOG.",
        styles["BodyAudit"],
    ), paragraph(
        "Erratum editorial sur l'edition v6 : sa page 2 dit que le pipeline reste prive. Cette phrase contredit le choix de licence consigne dans LICENSE_STATUS.md et LICENSES.md : code du projet sous MIT, documents et resultats sous CC BY 4.0, sous reserve des droits et notices des sources tierces. La phrase de v6 ne decrit donc pas le statut actuel.",
        styles["SmallAudit"],
    ), PageBreak()]

    # Page 2: complete primary result and its fixed method.
    story += [
        paragraph("Methode et resultat de GSE57495", styles["SectionTitle"]),
        paragraph(
            "GSE57495 comprend 63 echantillons de tissu pancreatique tumoral congeles sur la plateforme microarray GPL15048. Les valeurs d'expression du depot GEO ont ete jointes a la table officielle de la plateforme. Les sondes associees a un symbole unique ont ete agregees par mediane; les lignes sans symbole ou avec plusieurs symboles ont ete exclues. Les 63 paires CEACAM5-KRAS etaient disponibles.",
            styles["BodyAudit"],
        ),
        paragraph(
            f"Sondes CEACAM5 : {', '.join(result['probe_ids_by_target_symbol']['CEACAM5'])}.<br/>"
            f"Sondes KRAS : {', '.join(result['probe_ids_by_target_symbol']['KRAS'])}.",
            styles["SmallAudit"],
        ),
        paragraph(
            f"Test primaire : Spearman rho={rho:.4f}; permutation des etiquettes d'echantillon KRAS, "
            f"B={primary['permutation_count']:,}, graine={result['method']['seed']}, "
            f"p unilaterale={(pvalue):.8f}. IC percentile bootstrap 95 % sur "
            f"{primary['bootstrap_count_requested']:,} reechantillonnages de paires : "
            f"[{ci_low:.4f}, {ci_high:.4f}]. Aucun patient n'a ete filtre selon l'expression ou le resultat.",
            styles["BodyAudit"],
        ),
        Image(str(FIGURE), width=7.25 * inch, height=2.42 * inch),
        Spacer(1, 3),
        paragraph(
            "Figure A1. Nuage des 63 paires d'expression et distribution nulle de 100 000 permutations. Le trait rouge marque rho observe. La position de ce trait ne constitue pas un seuil biologique.",
            styles["SmallAudit"],
        ),
        paragraph("Controle secondaire de composition", styles["SectionTitle"]),
        paragraph(
            "Une correlation partielle de rang, definie avant lecture des valeurs cibles, a controle les medians des genes acineux disponibles et des genes d'ilots. Neuf des onze genes acineux et quatre des quatre genes d'ilots etaient mesures. La correlation partielle estimee est rho=0.352. Le protocole ne fixait pas de test d'inference pour cette analyse secondaire : le coefficient est descriptif et ne doit pas etre interprete comme une nouvelle preuve statistique. Ces marqueurs ne mesurent pas la purete tumorale complete.",
            styles["BodyAudit"],
        ),
        PageBreak(),
    ]

    # Page 3: source trail, reproducible command and future falsifiable work.
    story += [
        paragraph("Traces, reproduction et suite du programme", styles["SectionTitle"]),
        paragraph(
            "Le protocole primaire a ete consigne avant le telechargement et la lecture des valeurs d'expression de GSE57495, puis une clarification de calcul de la correlation partielle a ete ajoutee avant l'analyse. Le marqueur et la question avaient toutefois ete choisis apres les cohortes precedentes; ce choix est conserve comme limite explicite.",
            styles["BodyAudit"],
        ),
        paragraph("Reproduction depuis le dossier racine du projet", styles["SectionTitle"]),
        Table([[paragraph(
            'powershell -ExecutionPolicy Bypass -File "pancréas\\REVUE_INDEPENDANTE_2026-11-15\\run_gse57495_holdout.ps1"',
            styles["SmallAudit"],
        )]], colWidths=[7.28 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7DEE7")),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])),
        Spacer(1, 5),
        paragraph(
            "Le script reutilise les fichiers locaux; s'ils sont absents, le lanceur les recupere depuis NCBI GEO. Dependances exactes : requirements_gse57495.txt. Le script ne charge ni le pipeline ni TLog.",
            styles["BodyAudit"],
        ),
    ]

    files = [
        ("PROTOCOLE_HOLDOUT_GSE57495.md", "Question, inclusion, test, controles, seuil et limites fixes."),
        ("analyze_gse57495_holdout.py", "Calculs, permutations, bootstrap, table patient, figure et JSON."),
        ("data_GSE57495/GSE57495_holdout_sample_data.csv", "Valeurs d'analyse par echantillon public GEO."),
        ("data_GSE57495/GSE57495_permutation_rho.npz", "Distribution complete des 100 000 correlations permutees."),
        ("data_GSE57495/GSE57495_bootstrap_rho.csv", "Distribution complete des coefficients bootstrap finis."),
        ("data_GSE57495/GSE57495_holdout_manifest.json", "URLs, versions logicielles et empreintes SHA-256."),
        ("REVUE_SCIENTIFIQUE_PDACS.md", "Revue precedente plus mise a jour datee de ce resultat."),
    ]
    file_rows = [[paragraph("Fichier", styles["TableHeadAudit"]), paragraph("Contenu", styles["TableHeadAudit"])]]
    file_rows.extend([[paragraph(a, styles["SmallAudit"]), paragraph(b, styles["SmallAudit"])] for a, b in files])
    file_table = Table(file_rows, colWidths=[3.45 * inch, 3.83 * inch], repeatRows=1)
    file_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D7DEE7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [file_table, Spacer(1, 7), paragraph("Sources et empreintes essentielles", styles["SectionTitle"])]

    source_matrix = manifest["series_matrix"]
    source_platform = manifest["official_platform_annotation"]
    hash_rows = [
        [paragraph("Objet", styles["TableHeadAudit"]), paragraph("SHA-256", styles["TableHeadAudit"])],
        [paragraph("Matrice GEO", styles["SmallAudit"]), paragraph(source_matrix["sha256"], styles["SmallAudit"])],
        [paragraph("Annotation GPL15048", styles["SmallAudit"]), paragraph(source_platform["sha256"], styles["SmallAudit"])],
        [paragraph("Script d'analyse", styles["SmallAudit"]), paragraph(manifest["script_sha256"], styles["SmallAudit"])],
        [paragraph("Protocole", styles["SmallAudit"]), paragraph(manifest["protocol_sha256"], styles["SmallAudit"])],
    ]
    hash_table = Table(hash_rows, colWidths=[1.85 * inch, 5.43 * inch], repeatRows=1)
    hash_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D7DEE7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [hash_table, Spacer(1, 4), paragraph(
        'Donnees primaires : <link href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE57495" color="#163B63">GEO GSE57495</link>. '
        'Annotation : <link href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15048" color="#163B63">GEO GPL15048</link>.',
        styles["SmallAudit"],
    ), PageBreak()]

    # The previous flow may expand to more than one page. This explicit final
    # page is the forward-looking falsification plan, not a claim of results.
    story += [
        paragraph("Ce qui reste a demontrer", styles["SectionTitle"]),
        paragraph(
            "Ce test est une avancee de replication biologique, pas une preuve en faveur de la theorie universelle. Pour faire progresser le projet, il faut garder deux objectifs separes :",
            styles["BodyAudit"],
        ),
        paragraph(
            "1. En cancer du pancreas : confirmer CEACAM5-KRAS dans une cohorte independante avec donnees de mutation KRAS explicites, sans reutiliser cette cohorte pour choisir marqueur, seuil ou ajustement. Tester l'expression ARN et le statut mutationnel comme variables distinctes. Toute analyse de survie ou d'utilite clinique doit avoir son propre protocole et ses propres donnees externes.",
            styles["BodyAudit"],
        ),
        paragraph(
            "2. Pour UNIVERSAL_LOG et TLog : mener un benchmark aveugle sur donnees synthetiques a transition connue et sur series nulles, avec plusieurs formes de rupture, bruit, tailles et controles. Comparer TLog aux methodes de detection de rupture de reference et mesurer faux positifs, localisation de la transition et calibration. Publier les echecs et figer les regles avant de regarder les sorties.",
            styles["BodyAudit"],
        ),
        paragraph(
            "La coherence mathematique de TLog doit etre traitee separement de son nom et de son application. Si TLog=(d-4) log(n) avec n>1, le signe depend de d-4; une correlation avec un seuil dimensionnel connu ne suffit donc pas a montrer qu'il detecte une transition. Il faut etablir une prediction qui differe des baselines et peut echouer.",
            styles["BodyAudit"],
        ),
        Spacer(1, 10),
    ]
    closing = Table([[paragraph(
        "Conclusion d'audit : signal CEACAM5-KRAS soutenu dans une quatrieme cohorte; validation de TLog, mecanisme causal et valeur therapeutique encore non etablis.",
        styles["CalloutAudit"],
    )]], colWidths=[7.28 * inch])
    closing.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF5F3")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#A8CFC8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.append(closing)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return buffer.getvalue()


def main() -> None:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(f"Base PDF non trouve : {SOURCE_PDF}")
    appendix_bytes = make_appendix()
    source_reader = PdfReader(str(SOURCE_PDF))
    appendix_reader = PdfReader(io.BytesIO(appendix_bytes))
    writer = PdfWriter()
    writer.append(source_reader)
    writer.append(appendix_reader)
    writer.add_metadata({
        "/Title": "Livre blanc PDAC v6.1 - audit complete et mise a jour GSE57495",
        "/Author": "Audit de reproductibilite UNIVERSAL_LOG x PDAC",
        "/Subject": "Ajout date du test externe GEO GSE57495 au livre blanc PDAC v6",
    })
    with OUTPUT_PDF.open("wb") as handle:
        writer.write(handle)
    final = PdfReader(str(OUTPUT_PDF))
    print(json.dumps({
        "output": str(OUTPUT_PDF),
        "base_pages": len(source_reader.pages),
        "appendix_pages": len(appendix_reader.pages),
        "total_pages": len(final.pages),
        "bytes": OUTPUT_PDF.stat().st_size,
    }, indent=2))


if __name__ == "__main__":
    main()
