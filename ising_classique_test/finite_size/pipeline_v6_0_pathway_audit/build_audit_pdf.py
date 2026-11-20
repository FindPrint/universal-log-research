#!/usr/bin/env python
"""Build the reader-oriented Ising v6 audit PDF and attach the full ZIP bundle."""
from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd
import pymupdf as fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OUT = HERE / "LECTURE_GUIDEE_V6"
FIG = OUT / "figures"
PDF = PROJECT / "AUDIT_COMPLET_PIPELINE_V6_ISING_2026-11-15.pdf"
BASE = PROJECT / "AUDIT_COMPLET_PIPELINE_V6_ISING_2026-11-15_base.pdf"
BUNDLE = PROJECT / "pipeline_v6_ising_audit_bundle.zip"
SUMMARY = pd.read_csv(OUT / "resultats_synthese_lisible.csv")
PEAKS = pd.read_csv(PROJECT / "ising_classique_test" / "finite_size" / "finite_size_peaks.csv")
BINDER = pd.read_csv(PROJECT / "ising_classique_test" / "finite_size" / "binder_crossings.csv")
RUN_STATE = json.loads((HERE / "run_state.json").read_text(encoding="utf-8"))
RUNS = RUN_STATE.get("runs", {})

PAGE = landscape(A4)
WIDTH, HEIGHT = PAGE
NAVY = colors.HexColor("#17324d")
BLUE = colors.HexColor("#0072B2")
PALE = colors.HexColor("#edf3f7")
MID = colors.HexColor("#d7e0e8")
INK = colors.HexColor("#18212b")
ORANGE = colors.HexColor("#D55E00")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                          fontSize=26, leading=31, textColor=NAVY, alignment=TA_CENTER, spaceAfter=14))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=13, leading=19, textColor=INK, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
                          fontSize=19, leading=23, textColor=NAVY, spaceBefore=2, spaceAfter=10,
                          keepWithNext=True))
styles.add(ParagraphStyle(name="SubSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
                          fontSize=12, leading=15, textColor=NAVY, spaceBefore=6, spaceAfter=5,
                          keepWithNext=True))
styles.add(ParagraphStyle(name="BodyFR", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=9.2, leading=13.2, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallFR", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=7.2, leading=9.4, textColor=INK, spaceAfter=2))
styles.add(ParagraphStyle(name="TinyFR", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=5.8, leading=7.2, textColor=INK))
styles.add(ParagraphStyle(name="SmallHeaderFR", parent=styles["BodyText"], fontName="Helvetica-Bold",
                          fontSize=7.2, leading=9.4, textColor=colors.white))
styles.add(ParagraphStyle(name="TinyHeaderFR", parent=styles["BodyText"], fontName="Helvetica-Bold",
                          fontSize=5.8, leading=7.2, textColor=colors.white))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold",
                          fontSize=10, leading=14, textColor=NAVY, backColor=PALE,
                          borderColor=BLUE, borderWidth=1, borderPadding=8, spaceBefore=5, spaceAfter=8))
styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=7, leading=8, textColor=colors.HexColor("#536170")))


def esc(value):
    if value is None or pd.isna(value):
        return "—"
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return html.escape(str(value))


def para(value, style="BodyFR"):
    return Paragraph(str(value), styles[style])


def draw_page(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(MID)
        canvas.setLineWidth(.5)
        canvas.line(18 * mm, HEIGHT - 14 * mm, WIDTH - 18 * mm, HEIGHT - 14 * mm)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(18 * mm, HEIGHT - 10 * mm, "UNIVERSAL_LOG v6 · Audit Ising classique")
    canvas.setStrokeColor(MID)
    canvas.line(18 * mm, 12 * mm, WIDTH - 18 * mm, 12 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#536170"))
    canvas.drawString(18 * mm, 8 * mm, "Rapport lisible · données et code complets dans le ZIP joint")
    canvas.drawRightString(WIDTH - 18 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def table(data, widths, font=7, repeat=1, header=True, padding=3):
    cooked = []
    for row_index, row in enumerate(data):
        cell_style = ("TinyHeaderFR" if font <= 6 else "SmallHeaderFR") if header and row_index == 0 else ("TinyFR" if font <= 6 else "SmallFR")
        cooked.append([x if isinstance(x, (Paragraph, Image)) else para(esc(x), cell_style) for x in row])
    t = Table(cooked, colWidths=widths, repeatRows=repeat if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("LEADING", (0, 0), (-1, -1), font + 1.3),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("GRID", (0, 0), (-1, -1), .35, MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if header and data:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                     ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                     ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    for i in range(2 if header else 1, len(data)):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f7f9fb")))
    t.setStyle(TableStyle(commands))
    return t


def add_image(story, filename, maxw=WIDTH - 42 * mm, maxh=HEIGHT - 70 * mm):
    path = FIG / filename
    if not path.exists():
        story.append(para(f"Figure absente au moment de la génération : {filename}", "SmallFR"))
        return
    img = Image(str(path))
    scale = min(maxw / img.imageWidth, maxh / img.imageHeight)
    img.drawWidth = img.imageWidth * scale
    img.drawHeight = img.imageHeight * scale
    story.append(img)


def section(story, title, text=None):
    story.append(para(title, "Section"))
    if text:
        story.append(para(text))


def main_temperature_rows():
    rows = SUMMARY[SUMMARY["controle"].eq("Temperature") & SUMMARY["run_id"].str.startswith("primary_L")].copy()
    multi = SUMMARY[SUMMARY["run_id"].eq("sensitivity_L16_multiple_physical_controls") & SUMMARY["controle"].eq("Temperature")]
    rows = pd.concat([rows, multi], ignore_index=True).sort_values("L")
    return rows


def build_story():
    story = []
    # Cover
    story += [Spacer(1, 22 * mm), para("AUDIT COMPLET", "CoverTitle"),
              para("Ising classique · pipeline UNIVERSAL_LOG v6.0 · voies 1 et 2", "CoverSub"),
              Spacer(1, 6 * mm),
              para("29 estimateurs · Q1–Q6 · F1/F2 avant/après · trois Monte-Carlo · multi-contrôles · flux ajoutés",
                   "CoverSub"),
              Spacer(1, 12 * mm),
              para("Rapport de lecture, de reproduction et de critique scientifique", "CoverSub"),
              Spacer(1, 8 * mm),
              para("15 novembre 2026 · code Cohen-d v6.0.0-L7aL7b · Python 3.11.9 (.venv)", "CoverSub"),
              Spacer(1, 14 * mm),
              para("Ce test montre ce que cette version du pipeline fait sur une référence simulée connue. Il n’établit pas l’universalité du pipeline, la causalité d’un signal ni une preuve médicale.", "Callout"),
              Spacer(1, 4 * mm),
              para("Une archive ZIP complète est intégrée à ce PDF comme pièce jointe : code v6.0 utilisé, TLog, entrées CSV, résultats JSON/CSV, figures originales, journaux, addenda, licences et scripts de reproduction.", "BodyFR"),
              PageBreak()]

    # Executive summary
    section(story, "1. Résumé pour débuter")
    temp_rows = main_temperature_rows()
    t0_exact = pd.to_numeric(temp_rows["T0_axe_brut"], errors="coerce")
    near_count = int((t0_exact - 2.269185314213022).abs().le(.005).sum())
    fragile = int(temp_rows["L7b_robustesse"].eq("FRAGILE").sum())
    total_temp = int(temp_rows["L7b_robustesse"].notna().sum())
    rows = [
        ["Constat observé", "Lecture prudente"],
        ["T0 rejoint 2,27 pour L=32, 48, 64", "La valeur est proche de Tc analytique sur la grille 0,01; T0 reste une estimation unique sans IC."],
        ["Pics χ finis : 2,47 → 2,30 selon L", "Ils se déplacent vers Tc quand L augmente; T0 est sous les pics χ à toutes les tailles principales."],
        [f"L7b FRAGILE : {fragile}/{total_temp} tailles", "Un L7a ‘up’ n’est pas à lui seul une prédiction robuste; L12 est le seul cas robuste parmi ces lignes."],
        ["Voie 2: Levina–Bickel absent à L=16, 24, 32", "Le trio de trois ancres n’est pas complet pour toutes les tailles; aucune imputation n’est faite."],
        ["L16 : cinq axes donnent des T0 différents", "Les axes non monotones ont des conversions ambiguës; leurs valeurs brutes ne sont pas des températures."],
        ["Graine : T0=2,34 / 2,37 / 2,38", "Sensibilité modérée à la graine; l’ordre inversé et le bruit blanc laissent T0=2,34 dans ce run."],
    ]
    story.append(table(rows, [63 * mm, 196 * mm], font=8))
    story.append(Spacer(1, 5 * mm))
    story.append(para("Repère important : les séries χ, Cv et Binder sont présentes comme flux dans le CSV. Les positions de leurs pics/croisements sont des comparaisons de diagnostic, pas des validations aveugles indépendantes. Le contrôle à deux colonnes et le cas contrôle=cible sont des addenda exploratoires séparés.", "Callout"))
    story.append(PageBreak())

    # Method / data
    section(story, "2. Données, cible et protocole")
    story.append(para("Le modèle est le réseau carré 2D d’Ising sans champ, J=kB=1. Tc exact pour le réseau infini isotrope : 2/ln(1+√2)=2,269185314…; la relation critique exacte vient d’Onsager (Physical Review 65, 117–149, 1944), DOI 10.1103/PhysRev.65.117. Les simulations utilisent des mises à jour de grappes Wolff; 3 chaînes, 4 000 mesures et 500 mises à jour de chauffe par chaîne/température; les intervalles physiques utilisent 500 réplications bootstrap en blocs de 80 mesures."))
    story.append(para("Entrée de chaque run de taille L : 76 températures de 1,90 à 2,65 par pas de 0,01; une ligne par T et les colonnes énergie, aimantation absolue, χ, Cv et Binder. Ce ne sont pas des trajectoires brutes de spins. Le pipeline reçoit la cible fixe Energy_per_spin; les observables χ/Cv/Binder restent néanmoins disponibles comme flux dans le CSV."))
    protocol_rows = [
        ["Étape", "Configuration conservée"],
        ["Tailles", "L = 8, 12, 16, 24, 32, 48, 64; runs séparés, pas de fausse série concaténée."],
        ["Pipeline", "Version v6.0.0 Cohen-d, mode fast, 12 itérations MC internes, graine principale 20261115, 1 worker, trio default, L7b light."],
        ["Axes L16", "Temperature, abs_magnetization, chi_abs_per_spin, Cv_per_spin, Binder_U4; cible énergie fixe."],
        ["Flux L16 ajoutés", "Bruit gaussien indépendant; copie affine exacte de l’énergie; renversement de l’ordre des lignes."],
        ["Repères physiques", "Pics Cv/χ, croisements Binder et Tc exact. Le pipeline n’est pas recalibré avec ces marqueurs."],
    ]
    story.append(table(protocol_rows, [45 * mm, 214 * mm], font=7.5))
    story.append(Spacer(1, 5 * mm))
    story.append(para("La théorie opérationnelle évaluée est la chaîne complète : flux/axes, scan et MC de seuil, 29 estimateurs, questions Q1–Q6, cascade T−2…T+2, dérivées F1/F2, Voie 1/Voie 2, TLog et L1–L7a/L7b. La formule TLog seule ne remplace pas l’audit de la chaîne.", "Callout"))
    story.append(PageBreak())

    # Thermal localization
    section(story, "3. T0 et repères thermiques connus")
    story.append(para("Le graphique place T0 brut sur l’axe température lorsque l’axe est monotone. Les bandes χ/Cv sont les IC bootstrap physiques du CSV source; les petits traits autour de T0 sont l’étendue des cinq lignes les plus proches, pas un intervalle de confiance de T0."))
    add_image(story, "localisation_t0_et_reperes.png")
    story.append(PageBreak())

    marker_rows = [["L", "pic Cv T", "pic χ T", "IC χ 95 %", "T0 pipeline", "T0−Tc", "T0−pic χ", "L7b", "Voie 2"]]
    for _, r in temp_rows.iterrows():
        peak = PEAKS[PEAKS["L"].eq(int(r["L"]))].iloc[0]
        ci = f"[{peak['T_chi_abs_peak_boot_low']:.3f}, {peak['T_chi_abs_peak_boot_high']:.3f}]"
        marker_rows.append([int(r["L"]), f"{peak['T_Cv_peak']:.3f}", f"{peak['T_chi_abs_peak']:.3f}", ci,
                            esc(r["T0_axe_brut"]), esc(r["T0_moins_Tc_exact"]), esc(r["T0_moins_pic_chi"]),
                            esc(r["L7b_robustesse"]), esc(r["voie2_statut"])])
    story.append(table(marker_rows, [13 * mm, 23 * mm, 23 * mm, 39 * mm, 25 * mm, 24 * mm, 25 * mm, 26 * mm, 40 * mm], font=6.5))
    story.append(Spacer(1, 4 * mm))
    story.append(para("Résultat : T0 se rapproche de Tc sur L=32–64 mais se répète au même cran 2,27; cette proximité au Tc analytique est sensible à la résolution de la grille. En même temps, T0 reste en-dessous des pics χ finis (sauf recouvrement de l’IC à L=24) et la robustesse L7b est le plus souvent FRAGILE. Aucun seuil de réussite général n’a été pré-déclaré pour transformer cela en ‘détection réussie’."))
    story.append(PageBreak())

    section(story, "4. Croisements Binder : repère de transition")
    story.append(para("Les croisements U4 restent séparés de la sortie du pipeline. Chaque barre verticale est l’IC bootstrap à 95 % du croisement entre deux tailles. Les colonnes U4 sont aussi présentes comme flux; ces comparaisons ne sont donc pas aveugles."))
    add_image(story, "croisements_binder_et_Tc.png")
    bdata = [["Paires L", "T croisement", "IC bootstrap 95 %", "ΔTc"]]
    for _, r in BINDER.iterrows():
        bdata.append([f"{int(r['L1'])}–{int(r['L2'])}", f"{r['T_cross']:.4f}",
                      f"[{r['T_cross_ci95_low']:.4f}, {r['T_cross_ci95_high']:.4f}]", f"{r['delta_Tc']:+.4f}"])
    story.append(table(bdata, [48 * mm, 48 * mm, 78 * mm, 40 * mm], font=7))
    story.append(PageBreak())

    section(story, "5. Voie 1 et Voie 2 : garder les ancres visibles")
    story.append(para("Voie 1 est Higuchi seul. Voie 2 garde saturation, transition et divergence séparées (trio v6 Higuchi, InformationD1, LevinaBickel). Les échelles des estimateurs diffèrent; leurs valeurs ne se réduisent pas à un score commun. Une ancre absente reste manquante."))
    add_image(story, "voies_1_2_ancres_par_taille.png")
    story.append(para("Pour ce benchmark, Higuchi est disponible et voisin de 1,38–1,42 sur les tailles principales. Levina–Bickel manque pour L=16, 24 et 32; il est disponible pour L=8, 12, 48 et 64. La triangulation n’est donc pas uniformément complète. Le contrepoids nul/spectral, les médianes des 29 estimateurs et TLog restent dans les JSON maîtres/CSV joints."))
    story.append(PageBreak())

    # Controls and questions
    section(story, "6. Axes de contrôle et interactions de flux à L=16")
    story.append(para("Cible fixe : énergie. Les 5 contrôles sont différents; un rang (%) est une position sur l’axe choisi, pas une température partagée. Pour les axes non monotones, la conversion brute est marquée ambiguë."))
    add_image(story, "seuil_par_controle_L16.png")
    ctrl = SUMMARY[SUMMARY["run_id"].eq("sensitivity_L16_multiple_physical_controls")]
    control_table = [["Contrôle", "T0 rang %", "T0 brut", "Monotone", "Ambigu", "L7a", "L7b", "Voie2"]]
    for _, r in ctrl.iterrows():
        control_table.append([r["controle"], esc(r["T0_rang_pct"]), esc(r["T0_axe_brut"]),
                              esc(r["axe_monotone"]), esc(r["T0_conversion_ambigue"]),
                              esc(r["L7a_vote"]), esc(r["L7b_robustesse"]), esc(r["voie2_statut"])])
    story.append(table(control_table, [37 * mm, 27 * mm, 32 * mm, 25 * mm, 25 * mm, 21 * mm, 25 * mm, 45 * mm], font=6.7))
    story.append(Spacer(1, 3 * mm))
    add_image(story, "couverture_Q1_Q6_par_controle_L16.png", maxh=60 * mm)
    story.append(PageBreak())

    section(story, "7. Q1–Q6 : valeurs, couverture et particularités")
    story.append(para("Q1 à Q6 ne représentent pas six preuves indépendantes. Dans le run L=24, le diagnostic du pipeline dit que Q3 est identique à Q1; Q4 retourne des valeurs uniformes entre les estimateurs. Pour L=24, Q1–Q5 couvrent 29/29 scores pour l’énergie; Q6 en couvre 24/29. Les rangs des figures sont calculés dans chaque question uniquement pour le profil visuel; les CSV conservent les scores bruts."))
    add_image(story, "questions_Q1_Q6_rangs_29_estimateurs.png", maxh=132 * mm)
    story.append(PageBreak())
    add_image(story, "profils_Q1_Q6_par_controle_L16.png", maxh=124 * mm)
    story.append(para("Annexe des sorties Q1–Q6 complètes, toutes questions/estimateurs/flux/contrôles : `scores_Q1_Q6_*.csv` dans le ZIP; le JSON maître conserve aussi les états et métadonnées.", "SmallFR"))
    story.append(PageBreak())

    # F derivatives / MC
    section(story, "8. Dérivées F1/F2 avant et après T0")
    story.append(para("Le graphique ci-dessous détaille Higuchi sur les flux de L=24. F1 est la pente locale du fit quadratique; F2 est deux fois son coefficient quadratique. Chaque paire avant/après se compare au même flux. Les unités dépendent du flux et il n’y a pas d’IC pour ces coefficients dans ce run."))
    add_image(story, "derivees_F1_F2_avant_apres_L24.png", maxh=116 * mm)
    story.append(para("La table longue `derivees_F1_F2_multi_controle_L16_long.csv` contient tous les estimateurs, flux, fenêtres, effectifs et statuts pour les cinq axes de contrôle. Les fenêtres exactes et les valeurs restent dans les sorties JSON."))
    story.append(PageBreak())

    section(story, "9. Monte-Carlo : trois rôles distincts")
    add_image(story, "scan_monte_carlo_interne_L24.png", maxh=75 * mm)
    mc_rows = [["Rôle", "Ce que cela produit", "Ce que cela ne démontre pas"]]
    mc_rows += [
        ["Simulation physique Ising", "CSV énergie, m, χ, Cv, Binder; Wolff, 3 chaînes", "Ce n’est pas le MC interne du pipeline."],
        ["Optimisation MC du pipeline", "Essais de seuil (12 itérations dans le mode fast) et scan", "Le seuil optimisé n’est pas Tc en soi."],
        ["Bootstrap/permutation", "Intervalles ou scénarios nuls des audits", "Ce n’est pas la simulation physique ni l’optimiseur."],
    ]
    story.append(table(mc_rows, [53 * mm, 105 * mm, 102 * mm], font=7))
    story.append(Spacer(1, 5 * mm))
    story.append(PageBreak())
    story.append(para("Durées et sorties de chaque configuration principale", "SubSection"))
    story.append(para("Les durées dépendent de la machine et de la charge du système; elles servent ici à décrire cette campagne, pas à comparer des algorithmes sur un banc de performance.", "SmallFR"))
    runtime_rows = [["Run", "Durée (s)", "T0 brut", "L7b"]]
    for rid, run in RUNS.items():
        if run.get("status") == "complete":
            runtime_rows.append([rid, esc(run.get("elapsed_seconds")), esc(run.get("t0_control_value_raw")),
                                 esc(run.get("l7b_verdict"))])
    story.append(table(runtime_rows, [132 * mm, 40 * mm, 40 * mm, 48 * mm], font=7))
    story.append(PageBreak())

    section(story, "10. Sensibilités : graines, ordre, bruit et duplication")
    story.append(para("L16 à contrôle Temperature : la référence T0 vaut 2,34; les graines 42 et 123 donnent respectivement 2,37 et 2,38. Le renversement d’ordre, le flux de bruit indépendant et le flux énergie affine redondant donnent chacun 2,34. Dans ce dernier cas, l’ancre Levina–Bickel devient manquante. Ces essais ne sont pas des réplications indépendantes."))
    add_image(story, "sensibilite_T0_graines_flux_L16.png")
    story.append(PageBreak())

    section(story, "11. Addenda séparés")
    story.append(para("Flux réduits (L64) : comparaison exploratoire décidée après avoir vu les résultats principaux. L’entrée conserve seulement Temperature et Energy_per_spin; χ/Cv/Binder ne sont alors plus fournis comme flux. Un résultat proche de Tc réduirait une explication par accès direct aux colonnes de marqueur, sans démontrer l’universalité."))
    add_image(story, "comparaison_flux_complets_deux_colonnes_L64.png", maxh=92 * mm)
    story.append(para("Résultat L64 : T0 reste à 2,27 (50,064 %) avec les deux colonnes, soit la même valeur que le run principal à flux complet. L7b est FRAGILE et Levina–Bickel reste manquant. Comme cet addendum a été choisi après les résultats principaux et n’est exécuté qu’une fois, il s’agit d’un contrôle exploratoire, pas d’une validation aveugle."))
    story.append(PageBreak())
    story.append(para("Contrôle identique à la cible (L16) : cas d’usage valide possible pour un pipeline universel, distinct de la localisation de Tc. Le code doit signaler ce cas diagonal; certains contrastes peuvent devenir tautologiques. Les rangs du graphique sont internes à deux axes différents."))
    add_image(story, "controle_diagonal_cible_L16.png", maxh=102 * mm)
    diagonal = SUMMARY[SUMMARY["run_id"].eq("diagonal_L16_energy_as_target_and_control")]
    if not diagonal.empty:
        r = diagonal.iloc[0]
        story.append(para(f"Résultat diagonal L16 : T0 = {float(r['T0_rang_pct']):.3f} % du parcours énergie, valeur brute {float(r['T0_axe_brut']):.6f}; la conversion est marquée ambiguë. L7b = {html.escape(str(r['L7b_robustesse']))}. Ce statut décrit cette configuration pipeline; il ne localise pas une transition thermique."))
    story.append(para("Les deux configurations restent permises dans le pipeline : l’interprétation dépend de l’intention de l’analyse. Pour les analyses de transition Ising de ce rapport, température est le contrôle pertinent; le cas énergie=cible/contrôle est conservé comme test de comportement universel.", "Callout"))
    story.append(PageBreak())

    # Main summary table and Q exact values
    section(story, "12. Tableau de synthèse des configurations principales")
    data = [["Run", "Contrôle", "L", "T0 %", "T0 brut", "MC s", "L7a", "L7b", "Voie2"]]
    for _, r in SUMMARY.iterrows():
        if r["run_id"] in ("blind_flux_L64_temperature_energy", "diagonal_L16_energy_as_target_and_control"):
            continue
        data.append([r["run_id"], r["controle"], esc(r["L"]), esc(r["T0_rang_pct"]), esc(r["T0_axe_brut"]),
                     esc(RUNS.get(r["run_id"], {}).get("elapsed_seconds")), esc(r["L7a_vote"]),
                     esc(r["L7b_robustesse"]), esc(r["voie2_statut"])])
    story.append(table(data, [68 * mm, 36 * mm, 13 * mm, 25 * mm, 27 * mm, 22 * mm, 20 * mm, 24 * mm, 48 * mm], font=5.8))
    story.append(Spacer(1, 4 * mm))
    qpath = OUT / "scores_Q1_Q6_L24_long.csv"
    if qpath.exists():
        q = pd.read_csv(qpath)
        pivot = q.pivot(index="estimateur", columns="question", values="score_brut")
        qrows = [["Estimateur", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]]
        for estimator, vals in pivot.iterrows():
            qrows.append([estimator] + ["ND" if pd.isna(vals.get(k)) else f"{float(vals.get(k)):.3f}" for k in
                                        ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]])
        story.append(para("Annexe courte — scores bruts par estimateur, L=24, flux cible énergie", "SubSection"))
        story.append(table(qrows, [51 * mm, 31 * mm, 31 * mm, 31 * mm, 31 * mm, 31 * mm, 31 * mm], font=5.7, padding=2))
    story.append(PageBreak())

    # Limits / reproducibility
    section(story, "13. Ce que les résultats permettent de dire")
    limits = [
        ["Niveau", "Constat"],
        ["Observé", "Les grandes tailles donnent 2,27. À L=16, ordre inversé, bruit indépendant et copie affine gardent T0=2,34 au même seed; ce sont des variantes, pas des réplications exactes. Les cinq axes ont L7a=up, L7b=FRAGILE; les axes non monotones sont ambigus."],
        ["Soutien limité", "La position T0 est proche de Tc exact pour L=32–64 à la résolution du pas de température; le T0 de L=64 tombe dans l'IC du croisement Binder 48–64. Ces repères proviennent toutefois du même CSV que les flux pipeline."],
        ["Non démontré", "Universalité, seuil universel, mécanisme causal, performance sur données réelles, validité cancer, diagnostic médical ou supériorité à des méthodes de référence."],
        ["À améliorer", "Réplications/IC de T0, résultat avant/après flux réduit, robustesse par tailles et données externes; calibration de Q1–Q6/F1/F2 et règles de triage des valeurs manquantes."],
    ]
    story.append(table(limits, [45 * mm, 214 * mm], font=7.4))
    story.append(Spacer(1, 6 * mm))
    story.append(para("Le protocole original contenait une note indiquant une censure du pic χ de L=8. Vérification : le CSV source donne le pic 2,47, sa borne bootstrap haute 2,58 et une grille qui monte à 2,65. Aucun indicateur de censure n’est présent; l’erratum joint retire cette affirmation non confirmée.", "Callout"))
    story.append(PageBreak())

    section(story, "14. Pourquoi L7b est-il FRAGILE ?")
    story.append(para("L7b utilisé ici est le mode light. Son code lit trois checks : stabilité entre horizons, dispersion de T0 en walk-forward et cohérence directionnelle interne. Levina–Bickel n'est pas une entrée de cette fonction; son absence dans Voie 2 ne cause donc pas directement le verdict L7b-light. Les seuils sont des conventions codées à évaluer, pas des théorèmes."))
    l7b_rows = [["L", "Stabilité horizon", "T0 std walk-forward", "Cohérence", "Verdict"]]
    for L, rid in [(8, "primary_L8_temperature"), (12, "primary_L12_temperature"),
                   (16, "sensitivity_L16_multiple_physical_controls"), (24, "primary_L24_temperature"),
                   (32, "primary_L32_temperature"), (48, "primary_L48_temperature"),
                   (64, "primary_L64_temperature")]:
        run = RUNS.get(rid, {})
        output_dir = Path(run.get("output_path", ""))
        if L == 16:
            output_dir = output_dir / "Temperature"
        source = output_dir / "master_results.json"
        if not source.exists():
            continue
        result = json.loads(source.read_text(encoding="utf-8"))
        checks = result.get("prediction_levels", {}).get("L7b_robustesse", {}).get("checks", {})
        horizon = checks.get("stabilite_horizon", {})
        walk = checks.get("stabilite_walkforward", {})
        coherence = checks.get("coherence_interne", {})
        hval = horizon.get("min_stabilite_horizon")
        wval = walk.get("t0_std")
        l7b_rows.append([str(L),
                         f"{horizon.get('statut', 'ND')} · min={float(hval):.3f}" if hval is not None else horizon.get("statut", "ND"),
                         f"{walk.get('statut', 'ND')} · {float(wval):.3f}" if wval is not None else walk.get("statut", "ND"),
                         coherence.get("statut", "ND"),
                         result.get("prediction_levels", {}).get("L7b_robustesse", {}).get("verdict", "ND")])
    story.append(table(l7b_rows, [22 * mm, 58 * mm, 62 * mm, 48 * mm, 44 * mm], font=6.8))
    story.append(Spacer(1, 4 * mm))
    diagnostic_path = HERE / "DIAGNOSTIC_LEVINA_SUPPORT.json"
    if diagnostic_path.exists():
        diag = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        levina_rows = [["L", "Levina standalone (76 lignes)", "Valeurs paysage", "w", "Raison reconstruite / 120"]]
        for r in diag.get("records", []):
            reasons = r.get("reconstructed_landscape_reason_counts", {})
            reason_text = f"<40 points : {reasons.get('input_length_below_40', 'ND')}; <12 voisins valides : {reasons.get('fewer_than_12_valid_local_dimensions', 'ND')}"
            levina_rows.append([str(r.get("L")), esc(r.get("standalone_full_series_levina_bickel")),
                                f"{r.get('landscape_finite_levina_rows')}/{r.get('landscape_rows')}",
                                str(r.get("selected_window_size")), reason_text])
        story.append(para("Levina–Bickel : diagnostic en lecture seule des sorties gelées", "SubSection"))
        story.append(table(levina_rows, [14 * mm, 48 * mm, 36 * mm, 14 * mm, 122 * mm], font=6.5))
        story.append(Spacer(1, 3 * mm))
        story.append(para("Pour toutes les tailles, le paysage reconstruit reproduit 0/120 valeurs finies. 20 fenêtres restent sous 40 points; les 100 autres échouent au filtre des 12 dimensions locales valides (maximum observé : 8), même si l'entrée contient au moins 40 points. L'estimation standalone complète est finie. Cela relie la disponibilité de Levina au support local de ces fenêtres; élargir les fenêtres ou substituer une estimation globale changerait la définition. Tester séparément l'effet sur les sorties avant de modifier Voie 2.", "SmallFR"))
    story.append(PageBreak())

    section(story, "15. Contrat universel et banc de validation")
    story.append(para("Le contrat proposé autorise contrôle=cible, multi-contrôles et recouvrement contrôle/flux. Il marque le cas diagonal, conserve rang et valeur brute, documente les dépendances entre flux et distingue résultat calculé, indisponible, non exécuté et erreur."))
    bench_rows = [
        ["Famille", "Scénarios planifiés", "Mesure principale"],
        ["Événements connus", "Marche, sigmoïde, changement AR(1), apparition oscillatoire", "Erreur de localisation et variabilité entre graines"],
        ["Nuls et confusions", "Bruit blanc/coloré, AR(1) stable, dérive sans rupture, variance seule", "Faux repérage selon une règle d'alerte pré-déclarée"],
        ["Interactions", "Copie, affine, corrélé, décalé, indépendant, non lié", "Sensibilité des sorties et couverture des estimateurs"],
        ["Axes/configurations", "Monotone, décroissant, non monotone, constant, diagonal", "Conversion, avertissements, traçabilité, abstention"],
        ["Longueur", "N=7, 15, 30, 76 et suites du pilote", "Estimabilité, statuts absents, faux niveau de confiance"],
    ]
    story.append(table(bench_rows, [42 * mm, 111 * mm, 81 * mm], font=6.8))
    story.append(Spacer(1, 4 * mm))
    story.append(para("Séparer un pilote technique d'un lot confirmatoire à graines réservées; la vérité terrain reste hors du CSV analysé. L'audit courant fournit un T0 de scan. Le pilote doit d'abord déterminer si et quand le pipeline peut s'abstenir; si un T0 est produit aussi sous les nuls, sa seule existence ne définit pas une détection. Une règle d'alerte/abstention et ses marges doivent être écrites avant le lot confirmatoire. Les séries N=7/15 servent d'abord à tester le comportement avec peu de points, pas à réclamer 29 estimations fiables."))
    story.append(para("Le pilote synthétique v1 est exécuté et consigné; ses quatre runs terminés et trois refus N<50 sont des résultats pilotes, pas des résultats confirmatoires. Le prochain lot devra avoir des critères d'alerte/abstention et des graines réservées. Détails : `CONTRAT_CONFIGURATION_UNIVERSEL_V1.md`, `PROTOCOLE_BANC_ESSAI_SYNTHETIQUE_V1.md` et `synthetic_pilot_v1/` dans l'archive.", "Callout"))
    story.append(PageBreak())

    section(story, "16. Résultats du pilote synthétique v1")
    pilot_path = HERE / "synthetic_pilot_v1" / "scored_pilot_results.json"
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    pilot_rows = [["Cas", "N", "Vérité", "Run", "T0 rang %", "Erreur normalisée", "Estimateurs success / configurés", "L7b"]]
    for r in pilot.get("case_results", []):
        truth_label = "marche" if r.get("event_present") is True else "aucun événement" if r.get("event_present") is False else "—"
        counts = r.get("estimator_status_counts", {}) or {}
        success = counts.get("success", 0)
        total = r.get("estimator_count") or (29 if r.get("status") == "complete" else 0)
        t0v = r.get("t0_rank_pct")
        errv = r.get("location_error_normalized")
        pilot_rows.append([r.get("case_id"), str(r.get("n_rows", "—")), truth_label,
                           "terminé" if r.get("status") == "complete" else "rejeté",
                           f"{float(t0v):.2f}" if t0v is not None else "—",
                           f"{float(errv):.4f}" if errv is not None else "—",
                           f"{success}/{total}" if total else "0/non calculés",
                           (r.get("l7b") or {}).get("verdict", "—")])
    story.append(table(pilot_rows, [22 * mm, 12 * mm, 31 * mm, 20 * mm, 22 * mm, 28 * mm, 48 * mm, 24 * mm], font=6.4))
    story.append(Spacer(1, 4 * mm))
    tlog_delta = pilot.get("case01_minus_case02_tlog_class_median_delta", {})
    case01 = next((r for r in pilot.get("case_results", []) if r.get("case_id") == "case_01"), {})
    case02 = next((r for r in pilot.get("case_results", []) if r.get("case_id") == "case_02"), {})
    q01 = ((case01.get("q_finite_counts") or {}).get("Q1_Calme_vs_Chaos") or {}).get("finite")
    q02 = ((case02.get("q_finite_counts") or {}).get("Q1_Calme_vs_Chaos") or {}).get("finite")
    rounded_tlog_delta = {k: round(float(v), 3) for k, v in tlog_delta.items()}
    story.append(para(f"Sur la marche N=76, case_01 (flux additionnels) et case_02 (cible seule) ont exactement le même T0 ({float(case01.get('t0_rank_pct')):.3f} %) et 26/29 estimateurs `success`. Q1 a {q01} valeurs finies contre {q02}; les deltas des médianes géométriques TLog (flux riches moins cible seule) sont {html.escape(json.dumps(rounded_tlog_delta, ensure_ascii=False))}. Une paire unique montre une stabilité de T0 accompagnée de différences dans d'autres couches; elle ne quantifie pas un effet général des flux."))
    no_event = [r for r in pilot.get("case_results", []) if r.get("event_present") is False]
    no_event_text = "; ".join(f"{r.get('case_id')} : T0={float(r['t0_rank_pct']):.2f} %" for r in no_event if r.get("t0_rank_pct") is not None)
    story.append(para(f"Les cas sans événement généré renvoient eux aussi une position ({html.escape(no_event_text)}). Sans règle d'alerte pré-déclarée, ces résultats ne sont pas comptés comme faux positifs. Les cas N=7, 15 et 30 sont refusés avec le message `Au moins 50 sont requis`; le pipeline n'émet pas ici un objet d'abstention `indéterminée`.", "SmallFR"))
    story.append(para("Une réalisation par cas; pas d'intervalles de confiance, de taux de détection ni de confirmation. Les sorties Q1–Q6, F1/F2, TLog, Voie 1/2, L7a/L7b, les journaux et les valeurs exactes sont dans `synthetic_pilot_v1/`.", "Callout"))
    story.append(PageBreak())

    section(story, "17. Disponibilité des questions Q1–Q6")
    qkeys = ["Q1_Calme_vs_Chaos", "Q2_Tension_Seuil", "Q3_Agressivite", "Q4_Persistence", "Q5_Actif_Receptif", "Q6_Actif_Receptif_Echelle"]
    q_table = [["Cas", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]]
    for r in pilot.get("case_results", []):
        qdata = r.get("q_finite_counts", {}) or {}
        q_table.append([r.get("case_id")] + [
            f"{(qdata.get(k) or {}).get('finite')}/{(qdata.get(k) or {}).get('numeric')}" if r.get("status") == "complete" else "—"
            for k in qkeys
        ])
    story.append(para("Valeurs finies / valeurs numériques présentes dans les sorties de chaque question. Les comptes augmentent avec le nombre de flux; ils ne sont pas des scores de performance.", "SmallFR"))
    story.append(table(q_table, [23 * mm, 38 * mm, 38 * mm, 38 * mm, 38 * mm, 38 * mm, 38 * mm], font=6.2, padding=2))
    story.append(PageBreak())

    section(story, "18. Dérivées F1/F2 et cascade")
    f_table = [["Cas", "F1 avant (T−1)", "T0", "F1 après (T+1)", "max F1 velocity", "max F2 curvature", "Statut"]]
    for r in pilot.get("case_results", []):
        f = r.get("f1_f2", {}) or {}
        if r.get("status") != "complete":
            f_table.append([r.get("case_id"), "—", "—", "—", "—", "—", "non calculé"])
        else:
            vals = [f.get("T_-1_F1_pre_inflection"), f.get("T_0_Monte_Carlo_Central"), f.get("T_+1_F1_post_deceleration"), f.get("max_F1_velocity"), f.get("max_F2_curvature")]
            f_table.append([r.get("case_id")] + [f"{float(v):.3f}" if v is not None else "—" for v in vals] + [f.get("status", "—")])
    story.append(para("Cascade F1/F2 rapportée par le code; aucune incertitude de ces quantités n'est estimée dans ce lot à une réalisation.", "SmallFR"))
    story.append(table(f_table, [21 * mm, 37 * mm, 26 * mm, 37 * mm, 39 * mm, 39 * mm, 34 * mm], font=6.0, padding=2))
    story.append(PageBreak())

    section(story, "19. TLog et voies 1/2")
    t_table = [["Cas", "TLog saturation", "TLog criticality", "TLog divergence", "TLog null", "Higuchi V1", "Voie 2"]]
    for r in pilot.get("case_results", []):
        if r.get("status") != "complete":
            t_table.append([r.get("case_id"), "—", "—", "—", "—", "—", "non calculé"])
            continue
        t = ((r.get("tlog") or {}).get("class_median") or {})
        vals = [t.get(k) for k in ("saturation", "criticality", "divergence", "null_reference")]
        t_table.append([r.get("case_id")] + [f"{float(v):.3f}" if v is not None else "—" for v in vals] +
                       [f"{float((r.get('voie1') or {}).get('higuchi')):.3f}" if (r.get("voie1") or {}).get("higuchi") is not None else "—",
                        "heuristique"])
    story.append(para("TLog est rapporté avec ses médianes géométriques par classe; la formule indiquée par v6.0 est `(d−4)·log(n)`, une couche de la chaîne. Voie 1 est Higuchi seul; le statut de Voie 2 rappelle qu'il s'agit d'une triangulation heuristique, pas d'une preuve.", "SmallFR"))
    story.append(table(t_table, [21 * mm, 34 * mm, 34 * mm, 34 * mm, 28 * mm, 27 * mm, 30 * mm], font=5.9, padding=2))
    story.append(PageBreak())

    section(story, "20. Figure du pilote : position et calculabilité")
    pilot_figure = HERE / "synthetic_pilot_v1" / "pilot_overview.png"
    if pilot_figure.exists():
        img = Image(str(pilot_figure))
        maxw, maxh = WIDTH - 42 * mm, HEIGHT - 75 * mm
        scale = min(maxw / img.imageWidth, maxh / img.imageHeight)
        img.drawWidth = img.imageWidth * scale
        img.drawHeight = img.imageHeight * scale
        story.append(img)
    story.append(para("Le haut compare T0 au milieu de la frontière réellement générée pour les marches. Les triangles orange sont des T0 renvoyés quand aucun événement ponctuel n'a été généré. Les mentions rouges montrent les tailles rejetées avant calcul des estimateurs.", "SmallFR"))
    story.append(PageBreak())

    section(story, "21. Reproduire et auditer")
    story.append(para("Depuis la racine du projet sous PowerShell :"))
    story.append(para(".\\.venv\\Scripts\\python.exe .\\ising_classique_test\\finite_size\\pipeline_v6_0_pathway_audit\\run_pipeline_v6_ising.py", "BodyFR"))
    story.append(para("Puis générer le guide : .\\.venv\\Scripts\\python.exe .\\ising_classique_test\\finite_size\\pipeline_v6_0_pathway_audit\\build_reader_report.py. Les scripts des deux addenda sont séparés et marqués exploratoires."))
    story.append(para("Pilote synthétique : dans une copie vierge/versionnée de `synthetic_pilot_v1`, exécuter `run_synthetic_pilot.py prepare`, puis `run_synthetic_pilot.py run`, puis `score_synthetic_pilot.py`. Cela préserve les entrées et sorties archivées; la vérité de génération est lue seulement par le dernier script."))
    manifest = json.loads((HERE / "pipeline_v6_ising_manifest.json").read_text(encoding="utf-8"))
    story.append(para(f"Version pipeline : {html.escape(str(manifest.get('pipeline_version')))} · SHA-256 source : <font name='Courier'>{manifest.get('pipeline_sha256')}</font>", "SmallFR"))
    story.append(para(f"Script de lancement utilisé : <font name='Courier'>{manifest.get('script_sha256')}</font> · entrée Ising : <font name='Courier'>{manifest.get('source_csv_sha256')}</font> · protocole : <font name='Courier'>{manifest.get('protocol_sha256')}</font>", "SmallFR"))
    story.append(para(f"Archive jointe : {BUNDLE.name}; {BUNDLE.stat().st_size / 1_000_000:.1f} MB. Elle conserve le code v6.0, TLog.txt, l’archive PDAC antérieure, les CSV, JSON/CSV de résultats, figures brutes, logs, licences et scripts. `AUDIT_BUNDLE_MANIFEST.json` liste taille et hash SHA-256 de chaque membre."))
    story.append(para("Référence théorique : Lars Onsager, ‘Crystal Statistics. I. A Two-Dimensional Model with an Order-Disorder Transition’, Physical Review 65, 117–149 (1944), DOI 10.1103/PhysRev.65.117. https://journals.aps.org/pr/abstract/10.1103/PhysRev.65.117", "SmallFR"))
    story.append(para("Licence retenue pour la distribution : code MIT; documents/résultats CC BY 4.0; licences incluses dans le ZIP.", "SmallFR"))
    story.append(PageBreak())

    section(story, "22. Glossaire express")
    gloss = [
        ["Terme", "Lecture courte"],
        ["Contrôle", "Colonne utilisée comme axe d'ordre ou d'observation."],
        ["Flux", "Colonne mesurée que le pipeline analyse; tous les axes de contrôle peuvent également être flux selon configuration."],
        ["T0", "Position centrale du seuil Monte-Carlo du code, parfois convertie vers la valeur brute du contrôle."],
        ["Voie 1", "Lecture Higuchi seul; utile comme loupe, insuffisante pour le spectre complet."],
        ["Voie 2", "Triangulation des classes saturation/transition/divergence; les ancres restent séparées."],
        ["L7a / L7b", "L7a vote de cohérence; L7b vérification distincte de robustesse."],
        ["TLog", "Couche géométrique de la chaîne, à lire avec les 29 estimateurs, seuils, Q, F, contrôles et sorties globales."],
        ["Reverse Monte Carlo", "Aucun algorithme de ce nom n'a été trouvé dans v6.0; le test exécuté inverse l'ordre des lignes."],
    ]
    story.append(table(gloss, [48 * mm, 211 * mm], font=7.5))
    story.append(PageBreak())

    section(story, "23. Revue des recommandations externes · 16 novembre 2026")
    story.append(para("Cette page résume l’audit détaillé REVUE_RECOMMANDATIONS_IA_2026-11-16.md, inclus dans l’archive jointe. Elle sépare les observations vérifiées des propositions encore à tester."))
    recs = [
        ["Sujet", "Constat vérifié", "Étape proposée"],
        ["Abstention T0", "Le scan Cohen principal choisit toujours son argmax. Le pilote retourne aussi T0=77,31 % sur le nul AR(1) et 90,66 % sur une dérive lisse. Un test de permutation existe dans le module harmonique, mais il ne teste pas le scan Cohen principal complet.", "Conserver T0 candidat à titre descriptif et séparer le statut de détection. Calibrer une règle sur des nuls autocorrélés en répétant toute la sélection sous permutation."],
        ["GSE141017", "41 139 cellules proviennent de neuf souris; les préfixes de barcode gardent les échantillons. En retirant X/padding et en harmonisant les suffixes, une collision WT5M2 apparaît dans la matrice et les annotations, liée aux clusters 12 et 15. Cette normalisation reste à confirmer depuis la source. Le pseudotemps est un axe d’état inféré, pas le temps PTI.", "Préserver les barcodes bruts, résoudre la collision à partir de la source, définir la lignée et valider par souris. Traiter RNA velocity séparément après retraitement des lectures SRA en comptes épissés/non épissés."],
        ["Stabilité L7b", "t0_std est l’écart-type des seuils sur l’axe de rang en pourcentage. Les 4 cas du pilote donnent 24,73; 24,73; 32,05; 21,81; ils dépassent tous la limite PASS de 10. Un contrôle d’horizon échoue aussi sur le cas de dérive.", "Ne pas diviser mécaniquement par N. Comparer la métrique actuelle et d’éventuelles normalisations sur un banc multi-tailles, événements et nuls, sans remplacer le seuil avant calibration."],
    ]
    story.append(table(recs, [31 * mm, 117 * mm, 111 * mm], font=6.5, padding=3))
    story.append(Spacer(1, 7 * mm))
    story.append(para("Conséquence pour l’interprétation : ces résultats justifient une meilleure calibration et une analyse pancréatique tenant compte des souris; ils ne démontrent ni l’universalité du pipeline, ni une transition cancéreuse détectée par celui-ci, ni une causalité clinique.", "Callout"))
    story.append(para("Sources primaires : GSE141017 / SRA SRP247080 (NCBI GEO); Schlesinger et al., Nature Communications (2020), DOI 10.1038/s41467-020-18207-z; La Manno et al., Nature (2018), DOI 10.1038/s41586-018-0414-6. Le détail de méthode, les limites et les chemins de code sont consignés dans le fichier Markdown inclus au ZIP.", "SmallFR"))
    return story


def main():
    if not BUNDLE.exists():
        raise FileNotFoundError(f"Archive complète requise avant génération du PDF : {BUNDLE}")
    frame = Frame(18 * mm, 18 * mm, WIDTH - 36 * mm, HEIGHT - 36 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="normal")
    doc = BaseDocTemplate(str(BASE), pagesize=PAGE, leftMargin=18 * mm, rightMargin=18 * mm,
                          topMargin=19 * mm, bottomMargin=17 * mm, title="Audit complet UNIVERSAL_LOG v6 — Ising",
                          author="UNIVERSAL_LOG project audit")
    doc.addPageTemplates([PageTemplate(id="audit", frames=[frame], onPage=draw_page)])
    doc.build(build_story())
    pdf = fitz.open(BASE)
    pdf.set_metadata({"title": "Audit complet UNIVERSAL_LOG v6 — Ising classique",
                      "author": "Audit de reproduction du projet UNIVERSAL_LOG",
                      "subject": "Benchmark Ising, voies 1/2, Q1-Q6, F1/F2, Monte-Carlo et multi-contrôles",
                      "keywords": "UNIVERSAL_LOG, Ising, audit, Cohen-d, reproducibility"})
    pdf.embfile_add(BUNDLE.name, BUNDLE.read_bytes(), filename=BUNDLE.name,
                    desc="Archive complète : pipeline, TLog, données, résultats, logs, figures et licences")
    pdf.save(PDF, garbage=4, deflate=True)
    pdf.close()
    BASE.unlink(missing_ok=True)
    check = fitz.open(PDF)
    names = check.embfile_names()
    if BUNDLE.name not in names:
        raise RuntimeError("La pièce jointe ZIP n'a pas été conservée dans le PDF final.")
    print(f"PDF : {PDF}")
    print(f"Pages : {check.page_count}; ZIP joint : {', '.join(names)}")
    print(f"Taille : {PDF.stat().st_size:,} octets")
    check.close()


if __name__ == "__main__":
    main()
