# SPDX-License-Identifier: MIT
"""Build the V2 whitepaper by appending the dated replay/L7b supplement.

The original V1 PDF is never modified. The builder also embeds the complete
new trace folders and adds a path/hash attachment index.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit_release"
REPLAY = AUDIT / "2026-11-14_matched_v59_v591_replay_run03"
LIGHT = AUDIT / "2026-11-14_l7b_integration_fast"
FULL = AUDIT / "2026-11-14_l7b_full_reduced"
SOURCE_V590 = ROOT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py"
SOURCE_V591 = AUDIT / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
V1_PDF = ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER.pdf"
V2_PDF = ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER_V2.pdf"
APPENDIX_PDF = ROOT / "tmp" / "pdfs" / "UNIVERSAL_LOG_SUPPLEMENT_2026-11-14.pdf"
ADDENDUM_MD = ROOT / "AUDIT_SUPPLEMENT_2026-11-14.md"
ATTACHMENT_INDEX = ROOT / "SUPPLEMENT_ATTACHMENT_INDEX.csv"
QA_DIR = AUDIT / "whitepaper_qa" / "supplement_2026-11-14"
QA_JSON = QA_DIR / "v2_whitepaper_qa.json"

TRACE_DIRS = [
    AUDIT / "2026-11-14_matched_v59_v591_replay",
    AUDIT / "2026-11-14_matched_v59_v591_replay_run02",
    REPLAY,
    AUDIT / "2026-11-14_l7b_integration",
    LIGHT,
    FULL,
]
ROOT_TRACE_FILES = [
    AUDIT / "run_matched_v59_v591_replay.py",
    AUDIT / "run_l7b_integration.py",
    AUDIT / "run_l7b_full_reduced.py",
    AUDIT / "summarize_l7b_light.py",
    AUDIT / "build_v2_whitepaper_supplement.py",
    AUDIT / "finalize_v2_package.py",
    ROOT / "README_AUDIT_REPRODUCTION_V2.md",
    ROOT / "REPRODUCE_SUPPLEMENT_V2.ps1",
    ADDENDUM_MD,
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_text(value) -> str:
    return html.escape("" if value is None else str(value), quote=False)


def write_folder_manifest(folder: Path) -> None:
    if not folder.exists():
        return
    rows = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.name not in {"file_manifest.json", "folder_manifest.json"}:
            rows.append({
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    (folder / "file_manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def ensure_fonts() -> tuple[str, str]:
    regular = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("AuditArial", str(regular)))
        pdfmetrics.registerFont(TTFont("AuditArial-Bold", str(bold)))
        pdfmetrics.registerFontFamily("AuditArial", normal="AuditArial", bold="AuditArial-Bold", italic="AuditArial", boldItalic="AuditArial-Bold")
        return "AuditArial", "AuditArial-Bold"
    return "Helvetica", "Helvetica-Bold"


def paragraph(text, style):
    return Paragraph(text, style)


def make_styles(font: str, font_bold: str):
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("AuditTitle", parent=sample["Title"], fontName=font_bold, fontSize=21, leading=25, alignment=TA_CENTER, textColor=colors.HexColor("#15334B"), spaceAfter=12),
        "subtitle": ParagraphStyle("AuditSubtitle", parent=sample["Normal"], fontName=font, fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#52697A"), spaceAfter=8),
        "h1": ParagraphStyle("AuditH1", parent=sample["Heading1"], fontName=font_bold, fontSize=15, leading=19, textColor=colors.HexColor("#15334B"), spaceBefore=8, spaceAfter=8),
        "h2": ParagraphStyle("AuditH2", parent=sample["Heading2"], fontName=font_bold, fontSize=10.5, leading=13, textColor=colors.HexColor("#15607A"), spaceBefore=7, spaceAfter=5),
        "body": ParagraphStyle("AuditBody", parent=sample["BodyText"], fontName=font, fontSize=8.4, leading=11.1, alignment=TA_LEFT, textColor=colors.HexColor("#172B3A"), spaceAfter=6),
        "small": ParagraphStyle("AuditSmall", parent=sample["BodyText"], fontName=font, fontSize=6.8, leading=8.3, textColor=colors.HexColor("#314758"), spaceAfter=2),
        "table": ParagraphStyle("AuditTable", parent=sample["BodyText"], fontName=font, fontSize=6.5, leading=8, textColor=colors.HexColor("#172B3A")),
        "table_head": ParagraphStyle("AuditTableHead", parent=sample["BodyText"], fontName=font_bold, fontSize=6.6, leading=8, textColor=colors.white),
        "callout": ParagraphStyle("AuditCallout", parent=sample["BodyText"], fontName=font_bold, fontSize=9.5, leading=13, alignment=TA_CENTER, textColor=colors.HexColor("#7D2A2A"), borderColor=colors.HexColor("#D6A3A3"), borderWidth=0.8, borderPadding=8, backColor=colors.HexColor("#FFF4F1"), spaceBefore=8, spaceAfter=10),
    }


class HorizontalBars(Flowable):
    """Small vector chart for internal T0 sensitivity; no raster dependency."""
    def __init__(self, values, width=720, height=145, font="Helvetica"):
        super().__init__()
        self.values = values
        self.width = width
        self.height = height
        self.font = font

    def draw(self):
        c = self.canv
        left, right = 158, self.width - 40
        plot_w = right - left
        top, bottom = self.height - 10, 14
        for tick in (0, 25, 50, 75, 100):
            x = left + plot_w * tick / 100
            c.setStrokeColor(colors.HexColor("#D7E0E5"))
            c.setLineWidth(0.4)
            c.line(x, bottom, x, top)
            c.setFillColor(colors.HexColor("#52697A"))
            c.setFont(self.font, 6.8)
            c.drawCentredString(x, 2, str(tick))
        colors_by_key = {
            "Reference": "#244F73", "Seed 123": "#2F855A",
            "Window 80%": "#C05621", "Shuffled target": "#B83232",
            "Log target": "#718096",
        }
        row_h = (top - bottom) / len(self.values)
        for index, (label, value) in enumerate(self.values):
            y = top - (index + 1) * row_h + row_h * 0.28
            bar_h = row_h * 0.48
            c.setFillColor(colors.HexColor("#243B53"))
            c.setFont(self.font, 7.2)
            c.drawRightString(left - 8, y + bar_h * 0.24, label)
            value_clamped = max(0, min(100, float(value)))
            c.setFillColor(colors.HexColor(colors_by_key.get(label, "#4C6B80")))
            c.rect(left, y, plot_w * value_clamped / 100, bar_h, stroke=0, fill=1)
            c.setFillColor(colors.HexColor("#172B3A"))
            c.drawString(left + plot_w * value_clamped / 100 + 4, y + bar_h * 0.24, f"{float(value):.2f}%")
        c.setFillColor(colors.HexColor("#52697A"))
        c.setFont(self.font, 6.8)
        c.drawString(left, top + 1, "T0 interne du pipeline (%) - non assimilable a Tc")


def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#617787"))
    canvas.setFont("AuditArial" if "AuditArial" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 7)
    canvas.drawString(28, 18, "UNIVERSAL_LOG - supplement d'audit 2026-11-14 - CC BY 4.0")
    canvas.drawRightString(doc.pagesize[0] - 28, 18, f"Appendice - page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#D7E0E5"))
    canvas.line(28, 26, doc.pagesize[0] - 28, 26)
    canvas.restoreState()


def read_results():
    protocol = json_load(REPLAY / "protocol_predeclared.json")
    replay_summary = json_load(REPLAY / "replay_summary.json")
    runs = csv_rows(REPLAY / "v591_run_summaries.csv")
    tlog_rows = csv_rows(REPLAY / "v591_tlog_by_kind.csv")
    summary_cmp = csv_rows(REPLAY / "v590_v591_summary_comparison.csv")
    median_cmp = csv_rows(REPLAY / "v590_v591_estimator_comparison.csv")
    light_summary = json_load(LIGHT / "light_axis_summary.json")
    full_result = json_load(FULL / "result.json")
    light_attempt = json_load(LIGHT / "light_result.json")
    return protocol, replay_summary, runs, tlog_rows, summary_cmp, median_cmp, light_summary, full_result, light_attempt


def make_markdown(protocol, replay_summary, runs, tlog_rows, summary_cmp, median_cmp, light_summary, full_result):
    path = ADDENDUM_MD
    lines = [
        "<!-- SPDX-License-Identifier: CC-BY-4.0 -->",
        "# Supplement d'audit UNIVERSAL_LOG - 2026-11-14",
        "",
        "Ce supplement ajoute un replay apparié v5.9.0/v5.9.1 sur les configurations multi-axes et une integration réelle de L7b-light/full. Les protocoles, scripts exacts, données d'entrée, sorties, journaux, figures et empreintes sont conservés dans les répertoires `audit_release/2026-11-14_*` et intégrés aux pièces jointes du PDF V2.",
        "",
        "## Hypothèses et observations",
        "",
        "| Hypothèse pré-déclarée | Observation | Portée |",
        "|---|---|---|",
        "| H1 - a configuration égale, les médianes brutes devraient rester égales si les estimateurs n'ont pas changé. | 580/580 médianes identiques exactement; écart absolu maximal 0. | Non-régression sur les 20 cas appariés. |",
        "| H2 - le registre réparé devrait typer les estimateurs et exporter TLog par type. | 580/580 lignes avec `d_kind`, `quantity_type`, membership TLog; 260 lignes TLog groupées sur 13 types. | Export typé restauré dans ce jeu. |",
        "| H3 - les correctifs pourraient modifier les labels d'état. | 20/20 vecteurs D et 20/20 labels de régime identiques à v5.9.0. | Aucune modification d'état observée dans ces cas. |",
        "",
        "Aucune de ces observations ne calibre les seuils L7b, ne localise Tc ou ne prouve l'universalité.",
        "",
        "## Replay apparié",
        "",
        f"- Configurations: {replay_summary['configurations_ok']}/{replay_summary['configurations_planned']} réussies; {len({r['input'] for r in protocol['configurations']})} CSV distincts réutilisés sur 20 configurations; 200 lignes par CSV.",
        f"- Médianes: {replay_summary['raw_median_exact_equal_rows']}/{replay_summary['matched_estimator_rows']} exactement égales; différence maximale {replay_summary['raw_median_max_abs_difference']:.1f}.",
        f"- Sorties typed/TLog: {replay_summary['v591_native_d_kind_populated_rows']} estimateurs typés; {replay_summary['v591_tlog_by_kind_rows']} lignes TLog par type; {len(replay_summary['v591_tlog_d_kinds'])} types.",
        f"- D-vector: {sum(1 for r in summary_cmp if all(float(r[f'{k}_v590']) == float(r[f'{k}_v591']) for k in ('d_sat','d_crit','d_div','d_null')) )}/{len(summary_cmp)} vecteurs égaux composante par composante.",
        f"- Régimes v5.9.1: {dict(Counter(r['dominant_regime'] for r in runs))}.",
        "- Paramètres: seed=20261108; fenêtre demandée=40 lignes; scan paysage=24 points (copie dérivée pour égaler la résolution du run v5.9.0); 29 méthodes; optimisations automatiques désactivées; max_workers=1.",
        "",
        "### Matrice des 20 configurations",
        "",
        "| L | T | Chaîne | Contrôle | Flux | n flux | Régime | d_crit |",
        "|---:|---:|---:|---|---|---:|---|---:|",
    ]
    for r in runs:
        lines.append(f"| {r['L']} | {float(r['T']):.9f} | {r['Chain']} | {r['control']} | {r['flux_set']} | {r['n_fluxes']} | {r['dominant_regime']} | {float(r['d_crit']):.6f} |")
    lines += [
        "",
        "Contrôles utilisés: `MC_Update`, `Energy_per_spin`, `Magnetization`, `Nearest_neighbor_correlation`, `Noise_axis` et `Abs_magnetization_shuffled`. Flux sets: common, all_fluxes, target_absM_only, order_parameter_family, physical_without_noise. Les configurations exactes, hashes d'entrée et noms de colonnes sont dans le protocole JSON embarqué.",
        "",
        "### TLog par type",
        "",
        "Chaque type ci-dessous apparaît dans les 20 configurations; le CSV embarqué conserve toutes les valeurs `d_median` et `T_log` par configuration.",
        "",
        "| d_kind | Configurations |",
        "|---|---:|",
    ]
    kind_counts = Counter(r["d_kind"] for r in tlog_rows)
    for kind, count in sorted(kind_counts.items()):
        lines.append(f"| `{kind}` | {count} |")
    lines += [
        "",
        "## Integration L7b-light multi-contrôle",
        "",
        "Entrée: CSV archivé L16,Tc,chaîne 0, 200 lignes. Cible fixe `Abs_magnetization`; contrôles `MC_Update` et `Noise_axis`; outer mode `fast`; seed=20261108. Le wrapper a terminé en 900.79 s au total. Les verdicts sont internes aux heuristiques, pas des phases physiques.",
        "",
        "| Contrôle | Verdict | Horizon | Walk-forward | Cohérence cible/régime |",
        "|---|---|---|---|---|",
    ]
    for control, item in light_summary["axes"].items():
        checks = item["checks"]
        horizon = checks["stabilite_horizon"].get("statut")
        walk = checks["stabilite_walkforward"].get("statut")
        coherence = checks["coherence_interne"].get("statut")
        lines.append(f"| {control} | {item['verdict']} | {horizon} | {walk} | {coherence} |")
    lines += [
        "",
        "Les deux axes renvoient `FRAGILE`. MC_Update échoue sur la stabilité d'horizon (min=0.417) et le walk-forward (écart-type T0=40.501); sa cohérence interne passe. Noise_axis échoue sur l'horizon (0.667, zone fragile), le walk-forward (21.806) et une divergence de direction cible/régime (down contre up; pénalité 0.12).",
        "",
        "Le premier essai avec outer mode par défaut `full` n'a rien rendu après 15 minutes et a été arrêté; ce délai est conservé dans le dossier de trace. Il s'agit d'un résultat de coût d'exécution, pas d'un échec L7b.",
        "",
        "## Integration L7b-full bornée",
        "",
        "Entrée: les 80 premières lignes du même CSV, cible fixe `Abs_magnetization`, contrôle `MC_Update`, outer mode `fast`, `l7b_mode=full`, seed=20261108, n_scenarios=48 par défaut. Durée de l'appel: 1688.987 s. Cette tranche borne le test logiciel; elle ne fonde aucune inférence physique.",
        "",
        "| Check | Valeur | Statut | Lecture du code |",
        "|---|---:|---|---|",
    ]
    checks = full_result["persisted_l7b"]["checks"]
    check_rows = [
        ("Graine alternative 123", checks["graine"].get("ecart_T0"), checks["graine"]["statut"], f"T0 {checks['graine'].get('T0_ref'):.3f}% -> {checks['graine'].get('T0_graine_alt'):.3f}%; même direction."),
        ("Fenêtre 80%", checks["fenetre"].get("ecart_T0"), checks["fenetre"]["statut"], f"T0 {checks['fenetre'].get('T0_ref'):.3f}% -> {checks['fenetre'].get('T0_fenetre_80'):.3f}%; direction inchangée mais grand déplacement."),
        ("Cible mélangée", checks["melange"].get("rapport_magnitudes"), checks["melange"]["statut"], f"Magnitude Delta conservée (ratio {checks['melange'].get('rapport_magnitudes'):.3f}); le code signale une persistance sans ordre temporel."),
        ("Cible logarithmique", checks["echelle"].get("ecart_T0"), checks["echelle"]["sensibilite"], f"T0 {checks['echelle'].get('T0_ref'):.3f}% -> {checks['echelle'].get('T0_log'):.3f}%; check informatif."),
    ]
    for label, value, status, interpretation in check_rows:
        shown = "-" if value is None else f"{float(value):.3f}"
        lines.append(f"| {label} | {shown} | {status} | {interpretation} |")
    lines += [
        "",
        "Verdict full: `FRAGILE`. La transformation logarithmique est informative et ne fait pas échouer le verdict. Le T0 de référence (89.291%) est la sortie interne de ce pipeline sur cette tranche, et n'est pas Tc.",
        "",
        "### Défaut de traçabilité repéré",
        "",
        "Le check graine affiche `graine_alternative: null` alors que le source choisit explicitement 123. `_l7b_extract_summary` ne transporte pas la graine, puis le formateur lit la clé absente. Le calcul numérique et son statut PASS existent; l'export manque l'identifiant de graine. Le source testé reste inchangé. Détails dans `PROTOCOL_ERRATUM.md`.",
        "",
        "## Reproduction et empreintes",
        "",
        "Commandes complètes dans `README_AUDIT_REPRODUCTION_V2.md` et `REPRODUCE_SUPPLEMENT_V2.ps1`. Principaux scripts: `audit_release/run_matched_v59_v591_replay.py`, `audit_release/run_l7b_integration.py`, `audit_release/run_l7b_full_reduced.py`. Le PDF V2 joint les sorties complètes et un index des pièces jointes avec hashes SHA-256.",
        "",
        f"SHA-256 v5.9.0 source: `{protocol['source_hashes']['v5.9.0_derived_runtime_24']['sha256']}` (runtime dérivé à 24 points); SHA-256 source v5.9.1: `{protocol['source_hashes']['v5.9.1_release_source']['sha256']}`; runtime v5.9.1 dérivé 24 points: `{protocol['source_hashes']['v5.9.1_derived_runtime_24']['sha256']}`.",
        "",
        "Code MIT; documents, données et résultats CC BY 4.0, sous réserve des notices tierces d'origine.",
        "",
        "## Conclusion limitée",
        "",
        "Ce replay apporte une preuve de non-régression des médianes, vecteurs D et labels pour les 20 cas retenus, et confirme la restauration des exports typés. L7b s'exécute en light/full, mais retourne FRAGILE sur ces axes/tests. Le pipeline n'a pas localisé de manière fiable la transition d'Ising dans ces essais, et ceux-ci ne démontrent pas son universalité.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_appendix(protocol, replay_summary, runs, tlog_rows, summary_cmp, median_cmp, light_summary, full_result):
    regular, bold = ensure_fonts()
    styles = make_styles(regular, bold)
    page = landscape(letter)
    APPENDIX_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(APPENDIX_PDF), pagesize=page,
        rightMargin=28, leftMargin=28, topMargin=30, bottomMargin=38,
        title="Supplement d'audit UNIVERSAL_LOG - 2026-11-14",
        author="UNIVERSAL_LOG audit",
    )
    story = []
    checks = full_result["persisted_l7b"]["checks"]
    full_duration = full_result["elapsed_seconds"]
    light_duration = light_summary["elapsed_seconds_for_two_controls"]

    story += [Spacer(1, 0.35 * inch), paragraph("SUPPLEMENT D'AUDIT UNIVERSAL_LOG", styles["title"]),
              paragraph("Replay apparié v5.9.0/v5.9.1 et intégration L7b - 14 novembre 2026", styles["subtitle"]),
              Spacer(1, 0.12 * inch),
              paragraph("RÉSULTATS OBSERVÉS", styles["callout"]),
              paragraph("20/20 configurations exécutées. 580/580 médianes d'estimateur identiques exactement; 20/20 vecteurs D et labels d'état identiques. v5.9.1 restaure les exports typés: 580 lignes estimateur et 260 lignes TLog par type.", styles["body"]),
              paragraph("L7b-light et L7b-full ont tous deux terminé. Les verdicts observés sont FRAGILE selon les contrôles heuristiques implémentés; ils n'identifient pas Tc et ne démontrent pas l'universalité.", styles["body"]),
              Spacer(1, 0.12 * inch),
              paragraph("Contexte: deux versions comparées sur des CSV MCMC Ising archivés; aucune donnée historique n'a été remplacée. Les pré-déclarations, logs, sorties brutes, scripts et empreintes sont joints à ce PDF.", styles["small"]),
              PageBreak()]

    story += [paragraph("1. Question, protocole et hypothèses", styles["h1"]),
              paragraph("Question auditée: les correctifs de v5.9.1 préservent-ils les médianes et les états observés sur les mêmes entrées que le replay v5.9.0, tout en restaurant le registre typé et les exports TLog? L'intégration L7b est-elle réellement exécutée à travers run_full_unified_pipeline?", styles["body"])]
    hdata = [
        [paragraph("Hypothèse pré-déclarée", styles["table_head"]), paragraph("Résultat observé", styles["table_head"]), paragraph("Portée", styles["table_head"])],
        [paragraph("H1 - médianes préservées si la logique estimateur n'a pas changé.", styles["table"]), paragraph("580/580 médianes égales; maximum absolu = 0.", styles["table"]), paragraph("Non-régression de ces cas, pas validation de l'estimateur.", styles["table"])],
        [paragraph("H2 - registre de types et TLog-by-kind disponibles.", styles["table"]), paragraph("580/580 lignes typées; 260 lignes TLog groupées sur 13 types.", styles["table"]), paragraph("Restauration des exports observée.", styles["table"])],
        [paragraph("H3 - les correctifs peuvent changer les labels d'état.", styles["table"]), paragraph("20/20 vecteurs D et labels identiques à v5.9.0.", styles["table"]), paragraph("Aucun changement d'état dans le lot retenu.", styles["table"])],
    ]
    ht = Table(hdata, colWidths=[220, 240, 250], repeatRows=1, hAlign="LEFT")
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#244F73")),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#CBD6DC")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [ht, Spacer(1, 7),
              paragraph(f"20 configurations, 8 CSV distincts, 200 lignes par entrée. Seed=20261108; fenêtre historique=40 lignes; résolution paysage=24 points pour garder les deux versions comparables; 29 méthodes par configuration; optimisations automatiques désactivées; workers=1. Durée replay: {replay_summary['started_wall_seconds']:.1f} s.", styles["body"]),
              paragraph("Choix pré-déclaré, pas résultat: utiliser la résolution 24 points reproduit la copie dérivée du replay historique. La source v5.9.0 mentionne 120 points; cette divergence historique est conservée dans les métadonnées. Les contrôles changent entre axes; les comparaisons ne sont pas causales.", styles["body"]),
              PageBreak()]

    story += [paragraph("2. Résultats des 20 configurations", styles["h1"]),
              paragraph("Tous les appels v5.9.1 ont retourné status=ok. Les vecteurs d_sat/d_crit/d_div/d_null et le dominant_regime sont identiques au baseline v5.9.0 dans les 20 paires. Le tableau garde les axes et les ablations de flux visibles.", styles["body"])]
    data = [[paragraph(s, styles["table_head"]) for s in ("L", "T", "Chain", "Contrôle", "Flux", "n flux", "Régime", "d_crit")]]
    for r in runs:
        data.append([paragraph(safe_text(v), styles["table"]) for v in (
            r["L"], f"{float(r['T']):.9f}", r["Chain"], r["control"], r["flux_set"], r["n_fluxes"], r["dominant_regime"], f"{float(r['d_crit']):.6f}")])
    rt = Table(data, colWidths=[28, 66, 34, 155, 135, 34, 108, 65], repeatRows=1, hAlign="LEFT")
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#244F73")),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#CBD6DC")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F7F9")]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story += [rt, Spacer(1, 7), paragraph("La matrice complète inclut les identifiants historiques, hashes des entrées, status et mesures détaillées dans les CSV joints.", styles["small"]), PageBreak()]

    story += [paragraph("3. Registre des 29 estimateurs et TLog", styles["h1"]),
              paragraph("Le replay a retourné 29 méthodes par run, soit 580 lignes estimateur. La sortie v5.9.0 appariée n'avait pas de d_kind, quantity_type ni tlog_membership renseignés nativement; la v5.9.1 fournit ces 580 champs. La couche TLog contient 13 types par run, soit 260 lignes au total.", styles["body"])]
    kind_counts = Counter(r["d_kind"] for r in tlog_rows)
    agg = {}
    for r in tlog_rows:
        agg.setdefault(r["d_kind"], []).append(float(r["T_log"]))
    tdata = [[paragraph(s, styles["table_head"]) for s in ("d_kind", "Runs", "T_log médian", "Min", "Max")]]
    for kind in sorted(agg):
        vals = sorted(agg[kind])
        n = len(vals)
        med = (vals[(n-1)//2] + vals[n//2]) / 2
        tdata.append([paragraph(safe_text(kind), styles["table"]), paragraph(str(kind_counts[kind]), styles["table"]), paragraph(f"{med:.5f}", styles["table"]), paragraph(f"{vals[0]:.5f}", styles["table"]), paragraph(f"{vals[-1]:.5f}", styles["table"])])
    tt = Table(tdata, colWidths=[310, 60, 95, 95, 95], repeatRows=1, hAlign="LEFT")
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#15607A")),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#CBD6DC")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F7F9")]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story += [tt, Spacer(1, 8),
              paragraph("Tous les T_log détaillés et les estimateurs contributeurs sont dans `v591_tlog_by_kind.csv`; les 580 médianes appariées sont dans `v590_v591_estimator_comparison.csv`.", styles["small"]),
              PageBreak()]

    story += [paragraph("4. L7b-light - contrôle multi-axes", styles["h1"]),
              paragraph(f"L'appel multi-contrôle a terminé en {light_duration:.2f} s sur 200 lignes, cible fixe Abs_magnetization, seed=20261108, outer mode fast. Les deux runs ont status=ok. Les labels FRAGILE sont des résultats des règles internes, pas des verdicts sur une phase d'Ising.", styles["body"])]
    ldata = [[paragraph(s, styles["table_head"]) for s in ("Contrôle", "Verdict", "Stabilité horizon", "Walk-forward", "Cohérence interne", "T0 std")]]
    for control, item in light_summary["axes"].items():
        checks_l = item["checks"]
        ldata.append([paragraph(safe_text(v), styles["table"]) for v in (
            control, item["verdict"], checks_l["stabilite_horizon"]["statut"], checks_l["stabilite_walkforward"]["statut"],
            checks_l["coherence_interne"]["statut"], f"{checks_l['stabilite_walkforward'].get('t0_std', float('nan')):.3f}")])
    lt = Table(ldata, colWidths=[150, 72, 120, 102, 115, 70], repeatRows=1, hAlign="LEFT")
    lt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#244F73")), ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#CBD6DC")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F7F9")]), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [lt, Spacer(1, 9),
              paragraph("MC_Update: stabilité horizon min=0.417 (FAIL), T0 walk-forward std=40.501 (FAIL), cohérence interne PASS. Noise_axis: stabilité=0.667 (zone fragile, FAIL), T0 std=21.806 (FAIL), cible down contre régime up (FAIL, pénalité 0.12). Les deux verdicts globaux sont FRAGILE.", styles["body"]),
              paragraph("Le test a d'abord été essayé avec le outer mode par défaut full. Aucun résultat n'est sorti en 15 minutes; l'exécution a été arrêtée et conservée. Le test light achevé et le test L7b-full ci-dessous utilisent outer mode fast.", styles["small"]),
              PageBreak()]

    ref = checks["graine"]["T0_ref"]
    t0_chart = [("Reference", ref), ("Seed 123", checks["graine"]["T0_graine_alt"]),
                ("Window 80%", checks["fenetre"]["T0_fenetre_80"]),
                ("Shuffled target", checks["melange"]["T0_melange"]),
                ("Log target", checks["echelle"]["T0_log"])]
    story += [paragraph("5. L7b-full - intégration bornée sur 80 lignes", styles["h1"]),
              paragraph(f"run_full_unified_pipeline a terminé en {full_duration:.3f} s. Mode L7b=full, outer mode=fast, contrôle MC_Update, cible fixe Abs_magnetization, seed=20261108. La tranche de 80 lignes est un choix d'exécution logiciel; les fenêtres effectives ont été optimisées automatiquement.", styles["body"]),
              HorizontalBars(t0_chart, font=regular), Spacer(1, 7)]
    fdata = [[paragraph(s, styles["table_head"]) for s in ("Check", "Mesure", "Statut", "Observation")],
             [paragraph("Graine 123", styles["table"]), paragraph(f"écart T0={checks['graine']['ecart_T0']:.3f}", styles["table"]), paragraph("PASS", styles["table"]), paragraph("Référence 89.291%; graine 123: 88.571%; direction identique.", styles["table"])],
             [paragraph("Fenêtre 80%", styles["table"]), paragraph(f"écart T0={checks['fenetre']['ecart_T0']:.3f}", styles["table"]), paragraph("FAIL", styles["table"]), paragraph("T0 passe de 89.291% à 9.414%; grande sensibilité à la fenêtre.", styles["table"])],
             [paragraph("Cible mélangée", styles["table"]), paragraph(f"ratio |Delta|={checks['melange']['rapport_magnitudes']:.3f}", styles["table"]), paragraph("FAIL", styles["table"]), paragraph("Magnitude de Delta et direction persistent après mélange; attribution temporelle non soutenue par ce check.", styles["table"])],
             [paragraph("Cible log", styles["table"]), paragraph(f"écart T0={checks['echelle']['ecart_T0']:.3f}", styles["table"]), paragraph("INFORMATIF", styles["table"]), paragraph("T0 et direction invariants; ce check ne contribue pas au verdict décisif.", styles["table"])]]
    ft = Table(fdata, colWidths=[105, 118, 80, 400], repeatRows=1, hAlign="LEFT")
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#244F73")), ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#CBD6DC")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F7F9")]), ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [ft, Spacer(1, 6), paragraph("Verdict global: FRAGILE. T0 est un indicateur interne en pourcentage du contrôle, pas une estimation de Tc. Le flux spectral a produit des erreurs `Spectre nul/insuffisant`; elles sont conservées dans les journaux.", styles["small"]), PageBreak()]

    story += [paragraph("6. Défauts, limites et reproduction", styles["h1"]),
              paragraph("Défaut concret repéré: le check graine L7b-full affiche graine_alternative=null alors que le source choisit seed=123. Le résumé extrait par `_l7b_extract_summary` perd la graine et le formateur lit ensuite la clé absente. Le calcul T0 et PASS sont présents. Le code v5.9.1 testé n'a pas été réécrit après cette observation.", styles["body"]),
              paragraph("Warnings observés: précision de moment statistique réduite pour valeurs presque identiques; échecs locaux de `noise_step4_spectral` avec spectre nul/insuffisant; avertissement de dépréciation Matplotlib. Ils sont dans console.log; aucun n'a été converti en PASS par l'audit.", styles["body"]),
              paragraph(f"Durées: replay 20 configurations {replay_summary['started_wall_seconds']:.1f}s; L7b-light multi-control {light_duration:.2f}s; L7b-full borné {full_duration:.3f}s; essai outer full arrêté après 15min sans résultat. La configuration exacte, les sous-runs et les hashes sont joints.", styles["body"]),
              paragraph("Reproduction: voir README_AUDIT_REPRODUCTION_V2.md et REPRODUCE_SUPPLEMENT_V2.ps1. Les runners acceptent un nouveau --output-dir et refusent d'écraser les sorties existantes. Environnement historique: Python .venv Windows; code MIT, documents/résultats CC BY 4.0.", styles["body"]),
              paragraph("Conclusion: non-régression observée sur 20 cas et exports typés restaurés; L7b s'intègre mais signale FRAGILE sur les essais archivés. Le pipeline n'a pas localisé de manière fiable la transition Ising dans ces essais, et ceux-ci ne démontrent pas son universalité.", styles["callout"]),
              paragraph("Les résultats et les seuils L7b restent exploratoires. Les 20 configurations partagent des données et ne représentent pas 20 validations indépendantes.", styles["small"])]
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def collect_attachments():
    for d in TRACE_DIRS:
        write_folder_manifest(d)
    files = []
    for folder in TRACE_DIRS:
        if folder.exists():
            files.extend(p for p in folder.rglob("*") if p.is_file())
    files.extend(p for p in ROOT_TRACE_FILES if p.is_file())
    unique = {p.resolve() for p in files}
    return sorted(unique, key=lambda p: str(p).casefold())


def write_attachment_index(paths):
    rows = []
    with ATTACHMENT_INDEX.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["embedded_name", "source_path", "bytes", "sha256"])
        for index, path in enumerate(paths, 1):
            rel = str(path.relative_to(ROOT)).replace("/", "__").replace("\\", "__")
            stem = f"SUPP{index:04d}__{rel}"
            if len(stem) > 190:
                suffix = path.suffix
                stem = f"SUPP{index:04d}__{sha256(path)[:12]}__{path.stem[:120]}{suffix}"
            rows.append((stem, str(path.relative_to(ROOT)), path.stat().st_size, sha256(path)))
            writer.writerow(rows[-1])
    return rows


def build_v2_pdf(paths, embedded_rows):
    reader = PdfReader(str(V1_PDF))
    base_pages = len(reader.pages)
    base_attachment_count = len(reader.attachments)
    supplement = PdfReader(str(APPENDIX_PDF))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    for page in supplement.pages:
        writer.add_page(page)
    writer.add_outline_item("Supplement 2026-11-14 - replay v5.9.1 et L7b", base_pages)
    writer.add_metadata({
        "/Title": "UNIVERSAL_LOG - livre blanc d'audit V2 (supplement 2026-11-14)",
        "/Subject": "Replay apparié v5.9.0/v5.9.1 et intégration L7b",
        "/Author": "UNIVERSAL_LOG audit",
        "/Keywords": "audit, Ising, TLog, L7b, reproductibilité",
    })
    for embedded_name, source_path, size, digest in embedded_rows:
        path = ROOT / Path(source_path)
        with path.open("rb") as f:
            writer.add_attachment(embedded_name, f.read())
    APPENDIX_PDF.parent.mkdir(parents=True, exist_ok=True)
    V2_PDF.parent.mkdir(parents=True, exist_ok=True)
    temp_out = V2_PDF.with_suffix(".pdf.tmp")
    with temp_out.open("wb") as f:
        writer.write(f)
    os.replace(temp_out, V2_PDF)
    check = PdfReader(str(V2_PDF))
    qa = {
        "source_pdf": str(V1_PDF.relative_to(ROOT)),
        "source_pdf_sha256": sha256(V1_PDF),
        "source_pages": base_pages,
        "source_attachments": base_attachment_count,
        "supplement_pages": len(supplement.pages),
        "final_pages": len(check.pages),
        "expected_final_pages": base_pages + len(supplement.pages),
        "final_attachments": len(check.attachments),
        "expected_attachments": base_attachment_count + len(embedded_rows),
        "embedded_supplement_files": len(embedded_rows),
        "pdf_bytes": V2_PDF.stat().st_size,
        "pdf_sha256": sha256(V2_PDF),
        "attachment_index": str(ATTACHMENT_INDEX.relative_to(ROOT)),
        "attachment_index_sha256": sha256(ATTACHMENT_INDEX),
        "status": "pass" if len(check.pages) == base_pages + len(supplement.pages) and len(check.attachments) == base_attachment_count + len(embedded_rows) else "check_mismatch",
    }
    QA_DIR.mkdir(parents=True, exist_ok=True)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if qa["status"] != "pass":
        raise AssertionError(qa)
    return qa


def main():
    if not V1_PDF.is_file():
        raise FileNotFoundError(V1_PDF)
    protocol, replay_summary, runs, tlog_rows, summary_cmp, median_cmp, light_summary, full_result, light_attempt = read_results()
    if replay_summary["status"] != "completed" or replay_summary["configurations_ok"] != 20 or replay_summary["raw_median_exact_equal_rows"] != 580:
        raise AssertionError("Replay results are incomplete or differ from predeclared audit evidence")
    if full_result["status"] != "returned" or full_result["persisted_l7b"]["verdict"] != "FRAGILE":
        raise AssertionError("L7b-full evidence is missing")
    make_markdown(protocol, replay_summary, runs, tlog_rows, summary_cmp, median_cmp, light_summary, full_result)
    build_appendix(protocol, replay_summary, runs, tlog_rows, summary_cmp, median_cmp, light_summary, full_result)
    attachment_paths = collect_attachments()
    attachment_rows = write_attachment_index(attachment_paths)
    # The attachment index is itself embedded after it has indexed all other
    # traces. Its own SHA is recorded in PDF QA metadata.
    attachment_rows.append(("SUPPLEMENT_ATTACHMENT_INDEX.csv", str(ATTACHMENT_INDEX.relative_to(ROOT)), ATTACHMENT_INDEX.stat().st_size, sha256(ATTACHMENT_INDEX)))
    qa = build_v2_pdf(attachment_paths, attachment_rows)
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
