#!/usr/bin/env python3
"""Build the dated GDSC2 all-lineage white-paper supplement PDF."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_pdf(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#14324A"),
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subheading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#185B76"),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCompact",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallNote",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#4A5560"),
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["TableCell"],
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=21 * mm,
        bottomMargin=19 * mm,
        title="Supplément au livre blanc - analyse GDSC2 toutes lignées",
        author="FindPrint / Universal Log research",
        subject="Résultats et limites de l'analyse GDSC2 toutes lignées",
    )

    def page_frame(canvas, document) -> None:
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor("#C7D7DF"))
        canvas.line(20 * mm, height - 14 * mm, width - 20 * mm, height - 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#4A5560"))
        canvas.drawString(20 * mm, 10 * mm, "Supplément GDSC2 - 24 novembre 2026")
        canvas.drawRightString(width - 20 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    story = [
        Spacer(1, 13 * mm),
        Paragraph(
            "SUPPLÉMENT AU LIVRE BLANC<br/>ANALYSE GDSC2 TOUTES LIGNÉES",
            styles["CoverTitle"],
        ),
        Paragraph(
            "<b>Édition datée du 24 novembre 2026</b><br/>"
            "Résultats de l'extraction brute et de l'essai du modèle mixte",
            ParagraphStyle(
                "CoverSubtitle",
                parent=styles["BodyCompact"],
                alignment=TA_CENTER,
                fontSize=11,
                leading=15,
            ),
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Document compagnon de "
            "<i>UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_INTEGRAL_V12.pdf</i> "
            "et de <i>DOSSIER_SCIENTIFIQUE_PREUVES_ET_PROTOCOLE_PDAC_TLOG.pdf</i>. "
            "Les PDF archivés du 23 novembre restent inchangés; joindre ce supplément "
            "à leur partage.",
            styles["BodyCompact"],
        ),
        Paragraph("Synthèse", styles["Subheading"]),
        Paragraph(
            "L'analyse porte sur cinq médicaments GDSC2 et 968 lignées. "
            "L'ajustement officiel à covariance diagonale converge, mais la "
            "comparaison aux valeurs de référence montre un biais notable et "
            "ne constitue pas une validation indépendante de TLog.",
            styles["BodyCompact"],
        ),
        Paragraph("Extraction et couverture", styles["Subheading"]),
        Paragraph(
            "Le fichier brut GDSC2 public (version du 24 juillet 2022) a été "
            "traité. L'extracteur a retenu 7 327 scans contrôlés, normalisé "
            "179 515 puits et produit 125 230 points dose-réponse pour "
            "968 lignées. La normalisation a été vérifiée indépendamment sur "
            "21 puits de trois scans.",
            styles["BodyCompact"],
        ),
    ]

    table_rows = [
        [
            Paragraph("Médicament", styles["TableHeader"]),
            Paragraph("DRUG_ID", styles["TableHeader"]),
            Paragraph("Combinaisons<br/>avec référence", styles["TableHeader"]),
            Paragraph("Au moins un scan<br/>franchit 50 %", styles["TableHeader"]),
        ],
        ["Cisplatine", "1005", "760", "264"],
        ["Olaparib", "1017", "967", "122"],
        ["5-Fluorouracile", "1073", "968", "274"],
        ["Paclitaxel", "1080", "958", "445"],
        ["Gemcitabine", "1190", "960", "664"],
        ["Total", "", "4 613", "1 769"],
    ]
    table = Table(
        table_rows,
        colWidths=[43 * mm, 24 * mm, 50 * mm, 53 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#185B76")),
                ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#F2F6F8")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DCE9EE")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C7CF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            table,
            Spacer(1, 2 * mm),
            Paragraph(
                "Les mesures recoupent les 4 613 combinaisons de la table "
                "ajustée officielle pour ces médicaments. Six combinaisons "
                "brutes sans référence ajustée ont été exclues.",
                styles["SmallNote"],
            ),
            Paragraph("Essai du modèle gdscIC50 0.99.4", styles["Subheading"]),
            Paragraph(
                "Les puits ont été moyennés par lignée, médicament et dose, "
                "comme dans le prétraitement officiel groupNlmeData; "
                "56 332 observations moyennes sont entrées dans l'ajustement.",
                styles["BodyCompact"],
            ),
            Paragraph(
                "<b>isLargeData=TRUE :</b> matrice de précision singulière; "
                "l'ajustement échoue au contrôle et ses coefficients ne sont "
                "pas interprétés.<br/>"
                "<b>isLargeData=FALSE :</b> convergence en 3 itérations, "
                "covariance approximative définie positive, sans avertissement; "
                "4 613 comparaisons produites.",
                styles["BodyCompact"],
            ),
            PageBreak(),
            KeepTogether(
                [
                    Paragraph(
                        "Accord descriptif avec les références",
                        styles["Subheading"],
                    ),
                    Paragraph(
                        "La corrélation de Pearson est de <b>0,953</b>, mais la "
                        "différence signée moyenne (modèle moins référence) est de "
                        "<b>+1,201 LN_IC50</b>, soit un facteur géométrique d'environ "
                        "<b>3,32</b>. La différence absolue médiane est de "
                        "<b>0,922 LN_IC50</b>. La corrélation seule masquerait ce biais.",
                        styles["BodyCompact"],
                    ),
                ]
            ),
            Paragraph("Limites et interprétation", styles["Subheading"]),
            Paragraph(
                "La référence officielle et la nouvelle estimation utilisent "
                "les mêmes expériences GDSC2 : la comparaison n'est pas "
                "indépendante. Le modèle testé couvre cinq médicaments, et "
                "ne reproduit pas l'ajustement GDSC2 global, qui couvre plus "
                "de médicaments.",
                styles["BodyCompact"],
            ),
            Paragraph(
                "Sur 17 555 courbes scan-médicament, 4 580 franchissent 50 % "
                "de viabilité. Seules 1 769 des 4 613 combinaisons ont au moins "
                "un scan avec ce franchissement; pour 2 844 combinaisons, "
                "aucune courbe ne franchit le seuil dans la plage testée. "
                "La différence absolue médiane est de 0,223 log avec "
                "franchissement contre 1,652 sans franchissement. Ces dernières "
                "estimations dépendent davantage de l'extrapolation.",
                styles["BodyCompact"],
            ),
            Paragraph(
                "Les données sont des essais in vitro sur lignées cellulaires. "
                "Les puits et scans ne sont pas automatiquement des réplicats "
                "biologiques indépendants. Cette analyse ne teste pas TLog, "
                "ne valide aucun biomarqueur clinique et ne permet pas de "
                "prédire la réponse d'un patient ni un bénéfice thérapeutique.",
                styles["BodyCompact"],
            ),
            Paragraph(
                "Le modèle testé antérieurement sur le sous-ensemble PDAC "
                "(AsPC-1, BxPC-3 et CAPAN-1) n'a pas passé les contrôles de "
                "convergence; aucun coefficient de ce sous-ensemble n'est retenu.",
                styles["BodyCompact"],
            ),
            Paragraph("Où en est le projet ?", styles["Subheading"]),
            Paragraph(
                "Le projet a une extraction brute reproductible, une "
                "normalisation contrôlée sur un échantillon, une comparaison "
                "descriptive à la référence ajustée et une documentation des "
                "limites. Il n'a pas encore de validation expérimentale de TLog "
                "sur ces données et encore moins de validation clinique.",
                styles["BodyCompact"],
            ),
            Paragraph("Prochaine étape recommandée", styles["Subheading"]),
            Paragraph(
                "Prédéfinir une évaluation de TLog sur des courbes observables; "
                "séparer les expériences avec et sans franchissement du seuil; "
                "réserver des lignées de test avant tout réglage; publier les "
                "échecs, abstentions et incertitudes. Toute future évaluation "
                "clinique exigera une cohorte indépendante, un protocole "
                "préenregistré et une gouvernance clinique.",
                styles["BodyCompact"],
            ),
            Spacer(1, 3 * mm),
            KeepTogether(
                [
                    Paragraph("Reproduction et fichiers", styles["Subheading"]),
                    Paragraph(
                        "Les scripts, les commandes, les sources et les "
                        "diagnostics complets sont documentés dans "
                        "<i>GDSC2_AUDIT_SOURCE_ET_PLAN_REANALYSE.md</i> et "
                        "<i>PIPELINES_ET_CODE_SOURCE/LISEZMOI_PIPELINES_ET_REPRODUCTION.md</i>, "
                        "sur la branche GitHub "
                        "<i>publication/pdac-pipeline-caveats</i>. Les fichiers "
                        "bruts de 2,1 Go et les CSV détaillés restent hors du dépôt.",
                        styles["BodyCompact"],
                    ),
                ]
            ),
        ]
    )
    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.pdf",
    )
    args = parser.parse_args()
    build_pdf(args.output)
    print(f"PDF supplement ecrit: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
