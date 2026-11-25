#!/usr/bin/env python3
"""Build a one-page units and provenance correction for Yin Figure 6d."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing PDF: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CorrectionTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#14324A"),
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CorrectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#185B76"),
            spaceBefore=2.5 * mm,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CorrectionBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CorrectionCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CorrectionHeader",
            parent=styles["CorrectionCell"],
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title="Erratum d'unités et de provenance - Yin Figure 6d",
        author="FindPrint / Universal Log research",
        subject="Correction exploratoire des unités et vérification de la provenance",
    )
    story = [
        Paragraph(
            "ERRATUM — ANALYSE YIN FIGURE 6d<br/>"
            "Unités et provenance",
            styles["CorrectionTitle"],
        ),
        Paragraph("Source et provenance vérifiées", styles["CorrectionHeading"]),
        Paragraph(
            "Le DOI 10.1038/s41467-025-57520-3 correspond à Yin et al., "
            "<i>Pathogenic germline variants in Chinese pancreatic adenocarcinoma "
            "patients</i>, Nature Communications 16, 2214 (2025), PMID 40044664, "
            "PMCID PMC11882848. L'article décrit un criblage pharmacologique sur "
            "organoïdes dérivés de patients; la Figure 6d présente des courbes "
            "dose-réponse de 15 PDO traités par correcteurs de CFTR. La feuille "
            "source porte l'en-tête « Drug Concentration(Log) » et des colonnes "
            "DAC par composé.",
            styles["CorrectionBody"],
        ),
        Paragraph(
            "<b>24 novembre 2026 · Réanalyse exploratoire, post hoc et non indépendante</b>",
            ParagraphStyle(
                "CorrectionSubtitle",
                parent=styles["CorrectionBody"],
                alignment=TA_CENTER,
                fontSize=10,
            ),
        ),
        Paragraph("Erreur identifiée", styles["CorrectionHeading"]),
        Paragraph(
            "L'exécution initiale a transmis des pourcentages de viabilité "
            "(valeurs source 0,83–140,31) au module dose-réponse comme s'il "
            "s'agissait de fractions. Le résultat « 0/75 4PL convergent » "
            "est invalide et est retiré.",
            styles["CorrectionBody"],
        ),
        Paragraph("Réanalyse après conversion en fractions", styles["CorrectionHeading"]),
    ]

    rows = [
        [
            Paragraph("Mesure", styles["CorrectionHeader"]),
            Paragraph("Résultat", styles["CorrectionHeader"]),
            Paragraph("Interprétation", styles["CorrectionHeader"]),
        ],
        [
            "Courbes analysées",
            "75/75",
            "60 avec 8 doses; 15 avec 7 doses",
        ],
        [
            "Sorties TLog",
            "75/75",
            "Statut logiciel, pas une garantie d'exactitude",
        ],
        [
            "Ajustements 4PL",
            "75/75 convergents et en plage",
            "Après division de la réponse par 100",
        ],
        [
            "Différence absolue médiane TLog–4PL",
            "0,190 log10",
            "Même courbe; pas une référence indépendante",
        ],
    ]
    table = Table(rows, colWidths=[49 * mm, 43 * mm, 76 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#185B76")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F2F6F8")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C7CF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
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
                "Les deux colonnes source par condition sont agrégées par dose "
                "sans imputation. Leur indépendance biologique n'est pas établie; "
                "aucun bootstrap n'est appliqué. La comparaison TLog–4PL porte "
                "sur les mêmes observations et ne mesure pas l'exactitude "
                "prédictive.",
                styles["CorrectionBody"],
            ),
            Paragraph("Portée", styles["CorrectionHeading"]),
            Paragraph(
                "Ces données ont déjà été consultées et analysées; cette "
                "correction est post hoc et ne constitue pas une validation "
                "indépendante. Les deux colonnes source par condition ne sont "
                "pas établies comme réplicats biologiques indépendants. Le jeu "
                "Tiriac 2018 disponible ici ne contient que des AUC résumées. "
                "Aucune validation indépendante de TLog n'est établie. La source "
                "et la reproduction sont décrites dans "
                "ADDENDUM_YIN_2025_CORRECTION_UNITES_2026-11-24.md.",
                styles["CorrectionBody"],
            ),
            Paragraph(
                "Le protocole d'évaluation V1.0 est préspécifié mais non "
                "enregistré; l'audit n'a identifié aucun jeu local admissible "
                "comme test indépendant. Aucune demande externe de données "
                "n'a été envoyée.",
                styles["CorrectionBody"],
            ),
        ]
    )

    def page_footer(canvas, _document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C7D7DF"))
        canvas.line(19 * mm, 12 * mm, A4[0] - 19 * mm, 12 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#4A5560"))
        canvas.drawString(19 * mm, 8 * mm, "Erratum de recherche · Yin Figure 6d")
        canvas.drawRightString(A4[0] - 19 * mm, 8 * mm, "24 novembre 2026")
        canvas.restoreState()

    document.build(story, onFirstPage=page_footer)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-pdf", type=Path, required=True)
    args = parser.parse_args()
    build_pdf(args.output_pdf)
    print(args.output_pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
