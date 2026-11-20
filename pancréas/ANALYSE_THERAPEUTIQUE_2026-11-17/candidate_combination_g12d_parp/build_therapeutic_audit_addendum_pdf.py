#!/usr/bin/env python
"""Build and attach a traceable therapeutic PDAC reanalysis addendum."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results_in_vivo_source_data"
GSE = HERE / "results_GSE309596_therapeutic_axes"
OUT_DIR = Path(__file__).resolve().parents[3] / "output" / "pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)
BASE_PDF = OUT_DIR / "_tmp_therapeutic_addendum_base.pdf"
FINAL_PDF = OUT_DIR / "ADDENDUM_AUDIT_THERAPEUTIQUE_PDAC_2026-11-17.pdf"
SUMMARY = json.loads((RESULTS / "primary_cohort_summary.json").read_text(encoding="utf-8"))
PAIRWISE = list(__import__("csv").DictReader((RESULTS / "primary_pairwise_tests.csv").open(encoding="utf-8-sig")))


FONT = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(FONT / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT / "ariali.ttf")))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

NAVY = colors.HexColor("#18324B")
BLUE = colors.HexColor("#2878A5")
TEAL = colors.HexColor("#298C83")
ORANGE = colors.HexColor("#D87927")
PALE = colors.HexColor("#EEF3F7")
GRID = colors.HexColor("#D3DCE4")
INK = colors.HexColor("#1D2933")
MUTED = colors.HexColor("#536574")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleFr", fontName="Arial-Bold", fontSize=25, leading=31,
                          textColor=NAVY, alignment=TA_LEFT, spaceAfter=8))
styles.add(ParagraphStyle(name="Deck", fontName="Arial", fontSize=11.5, leading=16,
                          textColor=MUTED, spaceAfter=12))
styles.add(ParagraphStyle(name="H1Fr", fontName="Arial-Bold", fontSize=16, leading=20,
                          textColor=NAVY, spaceBefore=1, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name="H2Fr", fontName="Arial-Bold", fontSize=11.5, leading=15,
                          textColor=BLUE, spaceBefore=7, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="BodyFr", fontName="Arial", fontSize=9.3, leading=13.1,
                          textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallFr", fontName="Arial", fontSize=7.6, leading=10.1,
                          textColor=MUTED, spaceAfter=4))
styles.add(ParagraphStyle(name="TableFr", fontName="Arial", fontSize=7.5, leading=9.6,
                          textColor=INK))
styles.add(ParagraphStyle(name="TableHeadFr", fontName="Arial-Bold", fontSize=7.5, leading=9.4,
                          textColor=colors.white))
styles.add(ParagraphStyle(name="Callout", fontName="Arial-Bold", fontSize=10.2, leading=14.5,
                          textColor=NAVY, backColor=PALE, borderColor=BLUE, borderWidth=0.6,
                          borderPadding=9, spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="CoverLabel", fontName="Arial-Bold", fontSize=9, leading=12,
                          textColor=TEAL, spaceAfter=14))


def P(text, style="BodyFr"):
    return Paragraph(text, styles[style])


def table(rows, widths, header=True, font=7.5, repeat=1):
    cooked = []
    for r_idx, row in enumerate(rows):
        st = "TableHeadFr" if header and r_idx == 0 else "TableFr"
        cooked.append([x if hasattr(x, "wrap") else Paragraph(str(x), styles[st]) for x in row])
    t = Table(cooked, colWidths=widths, repeatRows=repeat if header else 0, hAlign="LEFT")
    rules = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
    ]
    if header:
        rules += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
        if len(rows) > 1:
            rules += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE])]
    t.setStyle(TableStyle(rules))
    return t


def page_chrome(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    if doc.page > 1:
        canvas.line(17*mm, h-14*mm, w-17*mm, h-14*mm)
        canvas.setFont("Arial-Bold", 7.4)
        canvas.setFillColor(MUTED)
        canvas.drawString(17*mm, h-11*mm, "PDAC | ADDENDUM THERAPEUTIQUE ET PISTE D'AUDIT")
        canvas.drawRightString(w-17*mm, h-11*mm, "17 novembre 2026")
    canvas.line(17*mm, 13*mm, w-17*mm, 13*mm)
    canvas.setFont("Arial", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(17*mm, 8*mm, "Réanalyse exploratoire - données animales publiées, pas une preuve clinique")
    canvas.drawRightString(w-17*mm, 8*mm, f"{doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(str(BASE_PDF), pagesize=A4, leftMargin=17*mm, rightMargin=17*mm,
                      topMargin=20*mm, bottomMargin=19*mm,
                      title="Addendum audit thérapeutique PDAC - 17 novembre 2026",
                      author="Reanalyse reproductible du projet UNIVERSAL_LOG")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="default", frames=[frame], onPage=page_chrome)])

story = []
# 1. Cover
story += [Spacer(1, 20*mm), P("DOSSIER DE RECHERCHE THERAPEUTIQUE", "CoverLabel"),
          P("Cancer du pancréas:<br/>ce que les données soutiennent", "TitleFr"),
          P("Réanalyse multi-flux, mesures tumorales animales individuelles et voie de translation clinique", "Deck"),
          Spacer(1, 5*mm),
          table([["Date", "17 novembre 2026"],
                 ["Objet", "Prioriser une piste thérapeutique préclinique"],
                 ["Périmètre", "Données publiques de l'étude MRTX1133 + olaparib"],
                 ["Statut", "Signal préclinique cohérent; aucun remède démontré"]],
                [34*mm, 134*mm], header=False),
          Spacer(1, 9*mm),
          P("Conclusion mesurée", "H2Fr"),
          P("Dans les valeurs individuelles publiées, l'association d'un inhibiteur KRAS G12D et d'olaparib ralentit davantage la croissance tumorale que chacune des monothérapies dans cinq modèles. La déplétion CD8 atténue une partie de cet effet dans une expérience KPC. Ces données viennent d'un seul article et d'un seul programme expérimental; elles ne montrent pas de guérison, et n'établissent pas de bénéfice humain.", "Callout"),
          P("Le scan du scRNA-seq réalisé avec le pipeline n'a pas produit de nouvelle signature qui survive à la correction des tests multiples. Nous nous concentrons donc sur les critères de réponse tumorale, le mécanisme CD8 et la possibilité de remplacer MRTX1133 par des agents encore étudiés en clinique.", "BodyFr"),
          Spacer(1, 5*mm),
          P("Les mots <b>observé</b>, <b>interprétation</b> et <b>hypothèse</b> sont distingués dans ce dossier. La réanalyse est exploratoire et n'est pas une recommandation médicale.", "SmallFr"),
          PageBreak()]

# 2. The question and evidence chain
story += [P("1. Question et chaîne de preuve", "H1Fr"),
          P("Question thérapeutique: l'association KRAS G12D + PARP a-t-elle un signal suffisamment cohérent pour justifier une expérience de suivi plus proche de la clinique, et quel mécanisme semble contribuer à la réponse? Le pipeline sert ici à organiser les flux cellulaires et les contrôles de traitement. La preuve de réponse est cherchée dans les résultats tumoraux de l'animal, pas dans une formule TLog.", "BodyFr"),
          P("Deux analyses complémentaires", "H2Fr"),
          P("1) GSE309596: 115 664 cellules, 12 spécimens GEO, quatre bras, trois spécimens par bras. L'unité statistique est le spécimen; cellules et champs d'image ne sont pas traités comme des animaux indépendants. 2) Source Data de l'article: volumes tumoraux répétés pour cinq modèles, six animaux par bras, et mesures distinctes de déplétion CD8 et de cytométrie.", "BodyFr"),
          P("Résultat du pipeline", "H2Fr"),
          P("364 comparaisons prévues; 328 estimables; aucune avec q BH < 0,05. Les classements exploratoires CAF/stromal, endothélial et IFN-gamma ne passent pas la correction globale (q minimal 0,237). Cette analyse n'a donc pas révélé une nouvelle cible thérapeutique.", "BodyFr"),
          P("Source principale", "H2Fr"),
          P("Xu et al., Nature Communications 2026, DOI 10.1038/s41467-026-69695-4. L'étude dépose le scRNA-seq sous GSE309596 et le RNA-seq sous GSE279749; son fichier Source Data rassemble les valeurs de figures. Les données HRD brutes sont à accès restreint. L'article indique qu'aucun nouvel algorithme n'a été généré et que les scripts personnalisés sont disponibles sur demande.", "BodyFr"),
          P('Article: <link href="https://pmc.ncbi.nlm.nih.gov/articles/PMC13043926/" color="#2878A5">texte intégral et Source Data</link> | <link href="https://doi.org/10.1038/s41467-026-72371-2" color="#2878A5">correction de l auteur</link>.', "SmallFr"),
          PageBreak()]

# 3. Animal tumor volume results
story += [P("2. Volumes tumoraux: cinq modèles", "H1Fr"),
          P("Le classeur Source Data rapporte huit mesures de volume indexées 0 à 7 dans chaque modèle. Le résultat principal ajuste le volume initial: log(1 + volume final) est expliqué par log(1 + volume initial) et le bras. Le tableau affiche le rapport ajusté de (1 + volume final), association / comparateur; un rapport inférieur à 1 favorise l'association.", "BodyFr")]
model_order = ["SW1990_CDx", "PANC1_CDx", "PDX1", "PDX2", "KPC_subcutaneous"]
rows = [["Modèle", "Vs véhicule", "Vs olaparib", "Vs MRTX1133"]]
name_fr = {"SW1990_CDx":"SW1990 CDX", "PANC1_CDx":"PANC-1 CDX", "PDX1":"PDX-1", "PDX2":"PDX-2", "KPC_subcutaneous":"KPC sous-cutané"}
for name in model_order:
    tests = [x for x in PAIRWISE if x["cohort"] == name]
    row = [name_fr[name]]
    for comp in ["Vehicle", "Olaparib", "MRTX1133"]:
        x = next(t for t in tests if t["contrast"] == f"Combination - {comp}")
        row.append(f"{float(x['ancova_adjusted_1plus_endpoint_ratio']):.3f} "
                   f"({float(x['ancova_ratio_ci95_low']):.3f}-{float(x['ancova_ratio_ci95_high']):.3f})")
    rows.append(row)
story += [table(rows, [34*mm, 44.5*mm, 44.5*mm, 44.5*mm]), Spacer(1, 3*mm),
          P("Les quinze q ANCOVA (BH global sur les 15 contrastes) sont toutes sous 0,01. Les permutations exactes sur le changement log1p donnent aussi q BH entre 0,003 et 0,032. Le signe de l'association par rapport aux deux monothérapies est donc cohérent dans les données publiées, même avec des méthodes de contraste différentes.", "BodyFr"),
          P("Ce ne sont pas quinze expériences indépendantes: il s'agit de cinq modèles et plusieurs contrastes du même article. Les p ANCOVA reposent sur un petit n et une forme de modèle. Les permutations exactes sont une sensibilité conditionnelle à l'échangeabilité des animaux.", "SmallFr")]
plot = RESULTS / "published_in_vivo_trajectories.png"
im = Image(str(plot), width=174*mm, height=105*mm)
im.hAlign = "CENTER"
story += [Spacer(1, 2*mm), im,
          P("Chaque trait pâle correspond à une trajectoire de souris selon la position dans le bloc de colonnes source; les traits épais sont les moyennes. L'identité souris n'est pas nommée dans le classeur et est suivie par position de colonne.", "SmallFr"), PageBreak()]

# 4. Baseline and interaction
story += [P("3. Volumes initiaux et sensibilité de l interaction", "H1Fr"),
          P("L'association n'avait pas toujours la même taille tumorale au départ. L'ajustement sur la valeur initiale est donc essentiel; les différences brutes de volume ne sont pas l'unique lecture.", "BodyFr")]
summary_by = {x["cohort"]:x for x in SUMMARY["primary_cohorts"]}
baseline_rows = [["Modèle", "Moyenne initiale véhicule", "Moyenne initiale combinaison", "Ratio comb./véhicule"]]
for name in model_order:
    s = summary_by[name]
    veh = s["by_arm"]["Vehicle"]["mean_baseline_mm3"]
    combo = s["by_arm"]["Combination"]["mean_baseline_mm3"]
    baseline_rows.append([name_fr[name], f"{veh:.1f} mm3", f"{combo:.1f} mm3", f"{combo/veh:.2f}"])
story += [table(baseline_rows, [42*mm, 48*mm, 49*mm, 28.5*mm]),
          P("À signaler: moyenne initiale SW1990 59,6 mm3 sous association contre 162,9 mm3 sous véhicule; ratio 0,37. Dans PANC-1, un volume initial véhicule est 0. Le log1p gère ce zéro; une analyse naïve en pourcentage l'aurait écarté ou aurait dû inventer une règle.", "SmallFr"),
          P("Supériorité aux monothérapies n égale pas synergie", "H2Fr"),
          P("Le terme interaction dépend de l'échelle d'effet. L'interaction brute (combinaison - MRTX1133 - olaparib + véhicule) et l'interaction ajustée sur log1p n'ont pas une direction/force stable pour tous les modèles. En PDX-2, l'estimation brute est +553 mm3 (IC95 % 246 à 860; p Welch=0,0019), alors que l'interaction log1p ajustée est incertaine (p=0,121; q sur cinq modèles=0,121). Nous ne concluons pas à une synergie in vivo universelle.", "BodyFr")]
int_rows = [["Modèle", "Interaction brute (mm3)", "p brute", "Rapport interaction ajustée log1p", "q sur 5"]]
for x in SUMMARY["factorial_interaction_welch"]:
    name=x["cohort"]
    a=x["baseline_adjusted_ancova_log1p_endpoint"]
    int_rows.append([name_fr[name], f"{x['estimate']:.1f}", f"{x['p_welch_two_sided']:.3g}",
                     f"{a['adjusted_ratio_of_1plus_endpoint']:.3f}",
                     f"{x['q_BH_across_5_model_interaction_tests']:.3g}"])
story += [table(int_rows, [35*mm, 39*mm, 24*mm, 42*mm, 27.5*mm]),
          P("Le rapport d'interaction ajusté est une différence sur l'échelle log transformée; il doit être lu avec son modèle et son intervalle de confiance complet dans le CSV attaché.", "SmallFr"), PageBreak()]

# 5. Immune mechanism
story += [P("4. CD8, cytométrie et imagerie", "H1Fr"),
          P("Déplétion CD8: dans l'expérience KPC1199, la croissance moyenne brute indexée 0-7 est 38 mm3 sous combinaison + IgG, contre 442 mm3 sous combinaison + anti-CD8. Sous véhicule, elle est 764 mm3 avec IgG et 694 mm3 avec anti-CD8. Le modèle factoriel ajusté sur le volume initial donne une interaction de 1,29 sur log1p(volume final), IC95 % 1,02 à 1,56, p=6,2 x 10^-9; le rapport de l'interaction est 3,63 (IC95 % 2,77 à 4,77). Cela va dans le sens d'une contribution CD8 dans ce modèle.", "BodyFr"),
          P("Cytométrie - trois animaux par groupe", "H2Fr")]
flow = SUMMARY["published_flow_cytometry"]["descriptive_summary"]
flow_rows = [["Mesure", "Véhicule", "Olaparib", "MRTX1133", "Association"]]
for item in flow:
    means=item["mean_percent_by_arm"]
    flow_rows.append([item["endpoint"].replace("_", " "), *[f"{means[g]:.2f}%" for g in ["Vehicle","Olaparib","MRTX1133","Combination"]]])
story += [table(flow_rows, [55*mm, 31*mm, 31*mm, 31*mm, 31*mm]),
          P("Les moyennes montrent un profil compatible avec une réponse T plus effectrice sous association, mais les tests exacts ont peu de résolution à n=3: après BH des neuf contrastes, aucun q n'est inférieur à 0,05 (q=0,113 à 0,300). La fraction CD8+/CD3+ ne comporte qu'une valeur par groupe dans la source; elle reste descriptive.", "SmallFr"),
          P("Bioluminescence orthotopique", "H2Fr"),
          P("Trois valeurs par bras seulement sont disponibles pour le jour 0 et le jour 14. Le fold-change géométrique jour14/jour0 est 18,2 véhicule; 1,31 olaparib; 1,00 MRTX1133; 0,0033 association. Les permutations exactes à n=3 ont p minimale 0,10. Le fichier contient des nombres à risque pour la survie mais pas les temps de décès ou de censure; le Kaplan-Meier ne peut pas être recalculé.", "BodyFr"),
          P("Les champs IHC et les cellules scRNA-seq ne sont jamais comptés comme souris. C'est une précaution centrale contre la pseudo-réplication.", "SmallFr"), PageBreak()]

# 6. Translation
story += [P("5. Quelle piste thérapeutique ensuite?", "H1Fr"),
          P("Résultat observé", "H2Fr"),
          P("MRTX1133 + olaparib a un signal de contrôle tumoral cohérent dans les valeurs animales de l'étude. L'expérience CD8 fournit une hypothèse de mécanisme immunitaire. Le scan multi-flux GSE309596 n'identifie pas une cible nouvelle après correction. Ce n'est donc pas une découverte de remède; c'est une piste préclinique à confirmer.", "BodyFr"),
          P("Contrainte de translation", "H2Fr"),
          P("MRTX1133 est l'agent utilisé dans l'article, mais l'essai clinique NCT05737706 est indiqué TERMINATED. Aux États-Unis, daraxonrasib (Rasonque) a reçu une indication FDA précise pour certains adultes avec PDAC métastatique après traitement systémique antérieur ou qui ne sont pas candidats à une thérapie multi-agent. L'essai de phase 3 NCT07805954 compare zoldonrasib + daraxonrasib à gemcitabine + nab-paclitaxel en première ligne pour PDAC métastatique KRAS G12D; le statut est actif et le registre canadien montre son inscription au Canada. Cet essai est expérimental et ses résultats comparatifs ne sont pas encore connus.", "BodyFr"),
          P("Sources réglementaires/essais: <link href=\"https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma\" color=\"#2878A5\">FDA: indication Rasonque</link>; <link href=\"https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2026-06840\" color=\"#2878A5\">NCI: essai G12D phase 3</link>; <link href=\"https://recherche-essais-cliniques.canada.ca/fr/search?field_medical_condition=&field_trial_status=All&page=966&search_api_fulltext=\" color=\"#2878A5\">Santé Canada: registre d'essais</link>; <link href=\"https://clinicaltrials.gov/study/NCT05737706\" color=\"#2878A5\">ClinicalTrials.gov: MRTX1133</link>.", "SmallFr"),
          P("Proposition de recherche", "H2Fr"),
          P("1. Répliquer dans un jeu indépendant et des organoïdes PDAC KRAS G12D. 2. Remplacer MRTX1133 par un inhibiteur G12D/RAS(ON) actuel. 3. Comparer olaparib à un partenaire chimiothérapeutique cliniquement pertinent avec bras monothérapie et combinaison. 4. Geler avant l'expérience le critère tumoral, le modèle d'interaction, la correction multiple, la dose, la toxicité, la durée après arrêt et les biomarqueurs HR/CD8. 5. Confirmer un éventuel prédicteur dans un jeu humain différent du jeu utilisé pour le sélectionner.", "BodyFr"),
          P("Le pipeline peut cartographier des flux et des interactions candidates; la décision thérapeutique vient ensuite d'expériences pharmacologiques et de résultats patients indépendants. Ce dossier priorise ce chemin de traitement sans présenter TLog comme validé.", "Callout"), PageBreak()]

# 7. Reproducibility and limits
story += [P("6. Méthode, limites et reproduction", "H1Fr"),
          P("Limites qui changent l'interprétation", "H2Fr"),
          P("- Un seul article préclinique; pas une réplication indépendante.\n- n=6 animaux par bras dans les cinq courbes; n=3 pour cytométrie et bioluminescence.\n- Pas d'identifiant souris dans le classeur; mesures liées dans le temps par position de colonne.\n- Déséquilibres de volumes initiaux, dont un zéro initial dans PANC-1; ANCOVA utilise log1p.\n- Interaction/synergie dépend de l'échelle; elle n'est pas uniforme.\n- Les nombres à risque ne suffisent pas à reconstruire la survie.\n- Les proxys scRNA-seq sont définis par marqueurs et l'unité biologique reste à clarifier pour certains spécimens.", "BodyFr"),
          P("Reproduction", "H2Fr"),
          P("Depuis la racine du projet, relancer avec le `.venv`:\n<font name='Arial-Bold'>.venv\\Scripts\\python.exe \"pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-17\\candidate_combination_g12d_parp\\reanalyze_published_in_vivo_source_data.py\"</font>", "BodyFr"),
          P("Le script reconstitue les tables de résultats, la source longue par animal, la cytométrie et les graphiques. Le scan GSE309596 se relance avec `analyze_GSE309596_therapeutic_axes.py`. Les 36 matrices GEO (1 123 001 622 octets) restent dans le projet avec leurs SHA256 et le script de téléchargement; le PDF ne duplique pas plus d'un gigaoctet de matrices. Elles sont publiques et peuvent être récupérées avec le manifeste et le script attachés.", "BodyFr"),
          P("Le classeur source original, l'archive complète des suppléments, les XML de l'article et de sa correction, scripts, JSON, CSV, graphique, manifestes et rapport markdown sont attachés à ce PDF. Une copie de l'audit complet précédent (v4) est aussi jointe. Les fichiers source sont embarqués tels quels; l'article indique la licence CC BY-NC-ND 4.0. Cette licence tierce n'est pas remplacée par une licence MIT ou CC BY de projet.", "BodyFr"),
          P("Pièces jointes", "H2Fr")]
attachment_names = [
    "reanalyze_published_in_vivo_source_data.py",
    "primary_cohort_summary.json", "primary_pairwise_tests.csv", "factorial_interactions.csv",
    "individual_animal_tumor_volume_long.csv", "flow_cytometry_mouse_values.csv",
    "flow_cytometry_tests.csv", "published_in_vivo_trajectories.png", "manifest.json",
    "GSE309596_report.md", "GSE309596_manifest.json", "GSE309596_controls_by_flows.csv",
    "GSE309596_sample_level_flows.csv", "GSE309596_qc_by_specimen.csv",
    "analyze_GSE309596_therapeutic_axes.py", "download_GSE309596.py",
    "download_manifest_GSE309596.json", "source_data_download_manifest.json",
    "original_source_data.xlsx", "full_supplementary_archive.zip",
    "article_fullTextXML.xml", "correction_fullTextXML.xml", "source_provenance_manifest.json",
    "full_audit_previous_v4.pdf", "analysis_report.md"
]
story += [P("Les fichiers sont embarqués comme pièces jointes et listés dans le manifeste joint.", "BodyFr"),
          P("Licence et provenance", "H2Fr"),
          P("L'article source et son fichier de données sont tiers. Le fichier xlsx est conservé exactement comme reçu, sans modification; sa licence est CC BY-NC-ND 4.0 selon la notice de l'article. Les scripts de réanalyse sont conservés dans le projet. Les versions du PDF de travail et les empreintes SHA256 sont écrites après génération.", "BodyFr"),
          P("Références", "H2Fr"),
          P("1. Xu et al. Nature Communications (2026), DOI 10.1038/s41467-026-69695-4.\n2. Correction de l'auteur, DOI 10.1038/s41467-026-72371-2.\n3. FDA, approbation daraxonrasib, 26 août 2026.\n4. NCI, RMC-9805-309 / NCT07805954, statut consulté le 17 novembre 2026.\n5. ClinicalTrials.gov, MRTX1133 / NCT05737706, statut TERMINATED; mise à jour 3 avril 2025.", "SmallFr")]

doc.build(story)

# Select existing artifacts, verify every path, and attach each byte-identical file.
files = {
    "reanalyze_published_in_vivo_source_data.py": HERE / "reanalyze_published_in_vivo_source_data.py",
    "primary_cohort_summary.json": RESULTS / "primary_cohort_summary.json",
    "primary_pairwise_tests.csv": RESULTS / "primary_pairwise_tests.csv",
    "factorial_interactions.csv": RESULTS / "factorial_interactions.csv",
    "individual_animal_tumor_volume_long.csv": RESULTS / "individual_animal_tumor_volume_long.csv",
    "flow_cytometry_mouse_values.csv": RESULTS / "flow_cytometry_mouse_values.csv",
    "flow_cytometry_tests.csv": RESULTS / "flow_cytometry_tests.csv",
    "published_in_vivo_trajectories.png": RESULTS / "published_in_vivo_trajectories.png",
    "manifest.json": RESULTS / "manifest.json",
    "GSE309596_report.md": GSE / "REPORT_GSE309596_therapeutic_axes.md",
    "GSE309596_manifest.json": GSE / "manifest.json",
    "GSE309596_controls_by_flows.csv": GSE / "GSE309596_controls_by_flows.csv",
    "GSE309596_sample_level_flows.csv": GSE / "GSE309596_sample_level_flows.csv",
    "GSE309596_qc_by_specimen.csv": GSE / "GSE309596_qc_by_specimen.csv",
    "analyze_GSE309596_therapeutic_axes.py": HERE / "analyze_GSE309596_therapeutic_axes.py",
    "download_GSE309596.py": HERE / "download_GSE309596.py",
    "download_manifest_GSE309596.json": HERE / "source" / "GSE309596_raw_counts" / "download_manifest.json",
    "source_data_download_manifest.json": HERE / "source" / "PMC13043926_source_data_download_manifest.json",
    "source_provenance_manifest.json": HERE / "source" / "PMC13043926_source_provenance_manifest.json",
    "full_supplementary_archive.zip": HERE / "source" / "PMC13043926_supplementaryFiles.zip",
    "article_fullTextXML.xml": HERE / "source" / "PMC13043926_fullTextXML.xml",
    "correction_fullTextXML.xml": HERE / "source" / "PMC13103420_author_correction_fullTextXML.xml",
    "original_source_data.xlsx": HERE / "source" / "41467_2026_69695_MOESM7_source_data.xlsx",
    "analysis_report.md": RESULTS / "RAPPORT_REANALYSE_THERAPEUTIQUE_2026-11-17.md",
}
previous_pdf = OUT_DIR / "ADDENDUM_AUDIT_PDAC_MULTIFLUX_2026-11-17_v4_MAPPING_QA.pdf"
if previous_pdf.exists():
    files["full_audit_previous_v4.pdf"] = previous_pdf
missing = [f"{name}: {path}" for name, path in files.items() if not path.exists()]
if missing:
    raise FileNotFoundError("Missing planned attachments:\n" + "\n".join(missing))

reader = PdfReader(str(BASE_PDF))
writer = PdfWriter()
writer.clone_document_from_reader(reader)
writer.add_metadata({"/Title": "Addendum audit thérapeutique PDAC - 17 novembre 2026",
                     "/Subject": "Réanalyse préclinique; résultats, limites, scripts et sources",
                     "/Keywords": "PDAC, KRAS G12D, PARP, CD8, source data, audit"})
for name, path in files.items():
    writer.add_attachment(name, path.read_bytes())
with FINAL_PDF.open("wb") as f:
    writer.write(f)
BASE_PDF.unlink(missing_ok=True)

final_reader = PdfReader(str(FINAL_PDF))
attached = final_reader.attachments
expected = set(files)
if set(attached) != expected:
    raise RuntimeError(f"Attachment mismatch: expected {len(expected)}, found {len(attached)}")
if len(final_reader.pages) < 6:
    raise RuntimeError(f"Unexpectedly short PDF: {len(final_reader.pages)} pages")

attachment_manifest = {
    "pdf": str(FINAL_PDF.resolve()), "pdf_bytes": FINAL_PDF.stat().st_size,
    "pdf_sha256": sha(FINAL_PDF), "pages": len(final_reader.pages),
    "attachments": [{"name": name, "source": str(path.resolve()),
                     "bytes": path.stat().st_size, "sha256": sha(path)}
                    for name, path in files.items()]
}
(OUT_DIR / "ADDENDUM_AUDIT_THERAPEUTIQUE_PDAC_2026-11-17_manifest.json").write_text(
    json.dumps(attachment_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"pdf": str(FINAL_PDF.resolve()), "bytes": FINAL_PDF.stat().st_size,
                  "sha256": attachment_manifest["pdf_sha256"], "pages": len(final_reader.pages),
                  "attachments": len(attached), "names": sorted(attached)},
                 indent=2, ensure_ascii=False))
