"""Create the complete, traceable UNIVERSAL_LOG audit whitepaper PDF."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit_release"
PDF_PATH = ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER.pdf"
CATALOG_PATH = ROOT / "PROJECT_FILE_CATALOG.csv"
ZIP_PATH = ROOT / "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip"
CHECKSUMS_PATH = ROOT / "SHA256SUMS.txt"
QA_DIR = AUDIT / "whitepaper_qa"

EXCLUDED_DIRS = {".venv", ".git", "__pycache__", "node_modules", "whitepaper_qa"}
EXCLUDED_OUTPUTS = {
    "AUDIT_UNIVERSAL_LOG_WHITEPAPER.pdf",
    "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip",
    "SHA256SUMS.txt",
    "UNIVERSAL_LOG_OPEN_SOURCE_AUDIT.zip.sha256",
}
NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#167D8D")
PALE = colors.HexColor("#EAF2F5")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#5B6872")
GRID = colors.HexColor("#D5DEE3")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_records(path: Path) -> int | str:
    try:
        count = 0
        with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as stream:
            for _ in csv.reader(stream):
                count += 1
        return max(0, count - 1)
    except Exception as exc:
        return "unavailable:" + type(exc).__name__


def walk_files(include_catalog: bool = False) -> list[Path]:
    found: list[Path] = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        base_path = Path(base)
        for name in files:
            path = base_path / name
            rel = path.relative_to(ROOT).as_posix()
            if name in EXCLUDED_OUTPUTS:
                continue
            if not include_catalog and rel == CATALOG_PATH.name:
                continue
            if path.suffix.lower() in {".pyc", ".pyo"}:
                continue
            found.append(path)
    return sorted(found, key=lambda p: p.relative_to(ROOT).as_posix().lower())


def create_catalog() -> list[dict[str, object]]:
    rows = []
    for index, path in enumerate(walk_files(include_catalog=False), 1):
        rel = path.relative_to(ROOT).as_posix()
        ext = path.suffix.lower() or "[sans extension]"
        records: int | str = csv_records(path) if ext == ".csv" else ""
        rows.append({
            "path": rel,
            "type": ext,
            "bytes": path.stat().st_size,
            "records": records,
            "sha256": sha256_file(path),
        })
        if index % 100 == 0:
            print(f"[catalogue] {index} fichiers hachés", flush=True)
    with CATALOG_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "type", "bytes", "records", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def register_fonts() -> tuple[str, str]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        (Path(r"C:\Windows\Fonts\arial.ttf"), Path(r"C:\Windows\Fonts\arialbd.ttf"),
         Path(r"C:\Windows\Fonts\consola.ttf")),
        (Path(r"C:\Windows\Fonts\segoeui.ttf"), Path(r"C:\Windows\Fonts\segoeuib.ttf"),
         Path(r"C:\Windows\Fonts\consola.ttf")),
    ]
    for regular, bold, mono in candidates:
        if regular.exists() and bold.exists() and mono.exists():
            pdfmetrics.registerFont(TTFont("AuditSans", str(regular)))
            pdfmetrics.registerFont(TTFont("AuditSans-Bold", str(bold)))
            pdfmetrics.registerFont(TTFont("AuditMono", str(mono)))
            return "AuditSans", "AuditMono"
    return "Helvetica", "Courier"


SANS, MONO = register_fonts()
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="AuditTitle", parent=styles["Title"], fontName="AuditSans-Bold",
    fontSize=28, leading=33, textColor=NAVY, alignment=TA_CENTER, spaceAfter=16,
))
styles.add(ParagraphStyle(
    name="AuditSubtitle", parent=styles["Normal"], fontName="AuditSans",
    fontSize=14, leading=20, textColor=TEAL, alignment=TA_CENTER, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="AuditBody", parent=styles["BodyText"], fontName=SANS, fontSize=9.2,
    leading=13.2, textColor=INK, spaceAfter=7, splitLongWords=True,
))
styles.add(ParagraphStyle(
    name="AuditSmall", parent=styles["BodyText"], fontName=SANS, fontSize=7.4,
    leading=9.4, textColor=INK, spaceAfter=3, splitLongWords=True,
))
styles.add(ParagraphStyle(
    name="AuditH1", parent=styles["Heading1"], fontName="AuditSans-Bold",
    fontSize=18, leading=22, textColor=NAVY, spaceBefore=6, spaceAfter=11,
    keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="AuditH2", parent=styles["Heading2"], fontName="AuditSans-Bold",
    fontSize=12.5, leading=15, textColor=TEAL, spaceBefore=9, spaceAfter=6,
    keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="AuditH3", parent=styles["Heading3"], fontName="AuditSans-Bold",
    fontSize=10, leading=12.5, textColor=NAVY, spaceBefore=7, spaceAfter=4,
    keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="AuditCode", fontName=MONO, fontSize=5.8, leading=7.1,
    textColor=INK, leftIndent=0, rightIndent=0, spaceAfter=0,
))
styles.add(ParagraphStyle(
    name="AuditCaption", fontName=SANS, fontSize=7.5, leading=10,
    textColor=MUTED, alignment=TA_LEFT, spaceBefore=3, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="AuditTable", fontName=SANS, fontSize=7.2, leading=9,
    textColor=INK, splitLongWords=True,
))
styles.add(ParagraphStyle(
    name="AuditTableHead", fontName="AuditSans-Bold", fontSize=7.2, leading=9,
    textColor=colors.white,
))
styles.add(ParagraphStyle(
    name="AuditTOC1", fontName="AuditSans-Bold", fontSize=10, leading=13,
    leftIndent=0, firstLineIndent=0, textColor=NAVY, spaceBefore=4,
))


class WhitepaperDoc(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename, pagesize=A4, leftMargin=48, rightMargin=48,
            topMargin=48, bottomMargin=48, title="UNIVERSAL_LOG — livre blanc d’audit",
            author="UNIVERSAL_LOG project contributors",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self.draw_page)])

    def draw_page(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(48, 34, A4[0] - 48, 34)
        canvas.setFont(SANS, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(48, 22, "UNIVERSAL_LOG  |  Livre blanc d’audit  |  14 novembre 2026")
        canvas.drawRightString(A4[0] - 48, 22, f"Page {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        info = getattr(flowable, "_audit_heading", None)
        if not info:
            return
        level, title = info
        stable = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
        key = f"sec-{self.page}-{stable}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title[:120], key, level=level, closed=(level > 0))
        self.notify("TOCEntry", (level, title, self.page))


def heading(text: str, level: int = 0) -> Paragraph:
    style = {0: "AuditH1", 1: "AuditH2", 2: "AuditH3"}[level]
    para = Paragraph(text, styles[style])
    para._audit_heading = (level, re.sub("<[^>]+>", "", text))
    return para


def p(text: str, small: bool = False) -> Paragraph:
    return Paragraph(text, styles["AuditSmall" if small else "AuditBody"])


def table(data, widths, header=True, repeat=1, font=7.2):
    wrapped = []
    for ri, row in enumerate(data):
        style = styles["AuditTableHead"] if header and ri == 0 else styles["AuditTable"]
        wrapped.append([Paragraph(str(cell), style) if not isinstance(cell, (Image, Table)) else cell for cell in row])
    obj = Table(wrapped, colWidths=widths, repeatRows=(repeat if header else 0), hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
        commands += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE])]
    obj.setStyle(TableStyle(commands))
    return obj


def code_block(text: str, width: int = 112, numbered: bool = False) -> Preformatted:
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.expandtabs(4)
        prefix = f"{n:05d} | " if numbered else ""
        available = max(30, width - len(prefix))
        if not line:
            out.append(prefix.rstrip())
            continue
        chunks = textwrap.wrap(
            line, width=available, replace_whitespace=False, drop_whitespace=False,
            break_long_words=True, break_on_hyphens=False,
        )
        out.append(prefix + chunks[0])
        continuation = " " * len(prefix)
        out.extend(continuation + part for part in chunks[1:])
    return Preformatted("\n".join(out), styles["AuditCode"], maxLineLength=130)


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def load_small_table(path: Path, limit: int = 65536):
    if path.stat().st_size > limit:
        return None
    return path.read_text(encoding="utf-8-sig", errors="replace")


def figure_groups() -> list[tuple[str, list[Path]]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in walk_files(include_catalog=True):
        if path.suffix.lower() == ".png":
            groups[sha256_file(path)].append(path)
    return sorted(
        ((digest, sorted(paths)) for digest, paths in groups.items()),
        key=lambda item: item[1][0].relative_to(ROOT).as_posix().lower(),
    )


def paragraph_story(rows):
    story = []
    for row in rows:
        story.append(p(" • " + html.escape(str(row))))
    return story


def build_story(catalog_rows, embedded_paths):
    story = []
    story += [
        Spacer(1, 0.9 * inch),
        Paragraph("UNIVERSAL_LOG", styles["AuditTitle"]),
        Paragraph("Livre blanc d’audit reproductible", styles["AuditSubtitle"]),
        Spacer(1, 0.18 * inch),
        p("<b>Code, théorie TLog, expériences, résultats, figures, décisions et limites</b>", small=True),
        Spacer(1, 0.32 * inch),
        table([
            ["Édition", "Périmètre", "Licence"],
            ["14 novembre 2026", "Versions v5.3, v5.8, v5.9.0 et copie dérivée v5.9.1; Ising classique/quantique; calibrations.", "Code MIT; documents et résultats CC BY 4.0"],
            [f"{len(catalog_rows)} éléments indexés", f"{len(embedded_paths)} fichiers de projet joints à ce PDF", "Textes de licence et portée à la racine du ZIP"],
        ], [115, 270, 120]),
        Spacer(1, 0.4 * inch),
        p("Document conçu pour permettre à une personne qui découvre le domaine de comprendre le projet, vérifier les choix, retrouver les artefacts et rejouer les contrôles ciblés. Les fichiers attachés au PDF préservent les sources et données exactes; le ZIP compagnon fournit une arborescence pratique.", small=True),
        Spacer(1, 0.2 * inch),
        p("Lecture essentielle : le pipeline est un outil expérimental riche et traçable. Les expériences présentées ne démontrent pas que la formule TLog ni les 29 estimateurs sont universels.", small=True),
        PageBreak(),
        heading("Sommaire", 0),
    ]
    toc = TableOfContents()
    toc.levelStyles = [styles["AuditTOC1"], styles["AuditTOC1"]]
    toc.dotsMinLevel = 0
    story += [toc, PageBreak()]

    story += [
        heading("Résumé exécutif"),
        p("Le projet associe un pipeline Python de séries temporelles, 29 estimateurs, une taxonomie de mesure, la proposition TLog et des expériences de validation. La contribution la plus solide de ce dossier est aujourd’hui la traçabilité et l’étendue des diagnostics. La faiblesse centrale reste la commensurabilité : les 21 sorties connectées à TLog n’estiment pas toutes le même objet mathématique."),
        p("<b>Ce que montrent les données :</b> des observables physiques Ising reproduisent des repères de taille finie; les sorties du pipeline varient avec les axes et flux; dans les essais archivés les labels TLog ne localisent pas de façon fiable la transition thermique ou quantique."),
        p("<b>Ce qui n’est pas établi :</b> une référence d=4 valable pour les 21 estimateurs, des seuils robustes hors échantillon, l’universalité inter-domaines, ou la capacité de L7b à garantir la robustesse d’une conclusion."),
        table([
            ["Niveau de preuve", "Énoncé"],
            ["Résultat reproductible ciblé", "Sur une entrée réelle, v5.9.1 conserve exactement les 29 médianes brutes et D_vector historiques; 10 cas synthétiques L7b et l’aide CLI passent."],
            ["Observation empirique", "Sur le lot MCMC multi-axes: 180 trajectoires, 1 440 000 observations, 178/180 écarts combinés dans ±2; seuil descriptif seulement."],
            ["Résultat négatif utile", "36/36 cellules thermiques configurées avec MC_Update donnent le label divergence."],
            ["Hypothèse ouverte", "Que TLog puisse produire une lecture de régime universelle après typage, calibration et validation indépendante."],
        ], [130, 375]),
        heading("Comment lire les niveaux de preuve", 1),
        p("Dans ce document, <b>hypothèse</b> désigne une question formulée avant l’interprétation; <b>résultat</b> désigne une valeur ou un statut effectivement archivé; <b>interprétation</b> est le sens limité attribué au résultat; <b>proposition</b> désigne une étape future. Les seuils ou paramètres choisis par le code sont signalés comme choix de protocole tant qu’ils n’ont pas été calibrés indépendamment."),
        heading("Le projet en une minute", 1),
        p("Une série est transformée en fenêtres/features; des estimateurs produisent des mesures; le pipeline agrège un profil de géométrie, calcule des scores TLog et des diagnostics de régimes/cohérence/robustesse. La configuration choisit une cible, un ou plusieurs axes de contrôle et éventuellement plusieurs flux. Le résultat n’est interprétable qu’avec ces choix, l’unité de n, le type de chaque estimateur, les données manquantes et l’incertitude."),
        PageBreak(),
    ]

    story += [
        heading("1. Périmètre, histoire et provenance"),
        p("Le dossier est reconstruit à partir des fichiers présents dans le répertoire de projet. Aucun historique Git n’a été trouvé; l’ordre ci-dessous est une chronologie de versions et d’artefacts, pas un historique exact de chaque décision."),
        table([
            ["Étape", "Artefacts représentatifs", "Lecture d’audit"],
            ["Pipeline initial", "UNIVERSAL_LOG_v5_3.py; TLog.txt", "Formulation TLog et 29 sorties; théorie initiale explicitement heuristique."],
            ["Taxonomie et documentation", "v5.8, D_KIND_TAXONOMIE_V5_8.md, guides et contrat de d", "Sépare dimensions-proxy et signatures; la référence d=4 reste à justifier par type."],
            ["v5.9 + robustesse", "source utilisateur v5.9.0, L7a/L7b, campagne MCMC multi-axes", "Ajout des contrôles de cohérence/robustesse; des cas limites et un défaut CLI ont été consignés."],
            ["Validation multi-domaines", "Ising classique et quantique; calibrations synthétiques; audits TLog", "Bonne couverture d’exécution, mais échec de localisation TLog dans les pilotes étudiés."],
            ["Copie d’audit v5.9.1", "audit_release/", "Correction distincte, diff et hash; les sources originales restent inchangées."],
        ], [95, 210, 200]),
        heading("Provenance des sources", 1),
        p("SHA-256 du source utilisateur v5.9.0 : <font name='AuditMono'>4f80f6a7d0809e802cbc9ec30c0bed552c1c8a95eb58687fd78e4ffd8e808260</font>. La taxonomie v5.8 utilisée pour la copie d’audit a le SHA-256 <font name='AuditMono'>4a21809ed263bb743bc8022e88f532a38310b4340c24b4e0def9e517776c65c0</font>. Les sources complètes, le diff et les empreintes sont joints et consignés dans le catalogue."),
        p("Les dates scientifiques historiques ne sont pas déduites des dates de modification locales. Les fichiers ont été conservés dans leurs dossiers; leurs contenus complets sont dans le ZIP et comme pièces jointes PDF."),
        heading("Inventaire du paquet", 1),
        p(f"Au moment de la génération, le catalogue comprend {len(catalog_rows)} fichiers du projet hors environnement .venv, caches Python, métadonnées Git et livrables auto-référentiels. L’inventaire comporte des chemins relatifs, extensions, tailles, lignes de données CSV et SHA-256. Le fichier PROJECT_FILE_CATALOG.csv est joint au PDF; le catalogue final du ZIP inclut aussi le hash du PDF."),
        PageBreak(),
    ]

    story += [
        heading("2. Théorie TLog et sens des 29 estimateurs"),
        p("La formule originale est <b>T_log(n,d) = (d − 4) × ln(n)</b>. À n fixé supérieur à 1, le signe dépend de d−4 et la taille change l’amplitude. Cela rend l’unité de n et la définition de d indispensables. Le document fondateur propose les lectures saturation (d&lt;4), criticité (d≈4) et divergence (d&gt;4), et nomme lui-même l’universalité comme une hypothèse à démontrer."),
        p("Le pipeline ne mesure pas une dimension unique par 29 méthodes interchangeables. Les estimateurs incluent rugosité de graphe, exposants de processus, dimensions d’attracteur, dimensions intrinsèques par voisinage, ratios de participation, proxies de graphes, pente spectrale, entropies et signatures dynamiques. Une sortie numérique finie n’établit ni que l’estimateur vise la quantité attendue ni qu’elle est comparable à d=4."),
        heading("Taxonomie codée", 1),
        p("Le classement historique de v5.3 est 8 méthodes saturation, 7 criticité, 7 divergence et 7 référence nulle. La taxonomie de mesure distingue 21 dimensions-proxy raccordées à la couche géométrique et 8 signatures maintenues hors de cette couche. v5.8 ajoute des d_kind qui décrivent l’objet mesuré; la v5.9 fournie a perdu certains exports/champs typés, restaurés dans la copie v5.9.1."),
        heading("Groupes de mesure", 1),
        p("Les types ci-dessous proviennent de l’export contrôlé des 29 méthodes. Ils ne rendent pas toutes les méthodes d’un groupe équivalentes; ils empêchent surtout de confondre une dimension avec une signature."),
    ]
    taxonomy_path = AUDIT / "validation_exports" / "estimator_measurement_types.csv"
    if taxonomy_path.exists():
        with taxonomy_path.open(encoding="utf-8-sig", newline="") as f:
            tax = list(csv.DictReader(f))
        grouped = defaultdict(list)
        for row in tax:
            grouped[row["d_kind"]].append(row["estimator"])
        rows = [["d_kind", "Nombre", "Estimateurs"]]
        for kind, names in sorted(grouped.items()):
            rows.append([html.escape(kind), str(len(names)), html.escape(", ".join(names))])
        story.append(table(rows, [180, 45, 280]))
    story += [
        heading("Questions de définition non résolues", 1),
        p("Le sens de n peut être nombre de points, nombre d’observations indépendantes, taille physique ou nombre de pas de contrôle; ces unités ne sont pas interchangeables. Le sens de d change lui aussi selon l’estimateur. Le calcul d’une moyenne finale des ancres n’est pas formalisé : les documents théoriques rejettent une moyenne naïve, mais aucune règle géométrique calibrée de triangulation n’est encore démontrée. Le profil vectoriel et les intervalles par estimateur sont donc plus honnêtes qu’un chiffre global forcé."),
        p("Le seuil 4 est proposé dans la théorie et utilisé par le code comme référence; la calibration disponible montre que certains estimateurs mesurent des graphes généralement entre 1 et 2, des signatures hors dimension, ou des proxys spécifiques. Le contrat de d et la taxonomie doivent être traités comme des conventions versionnées à tester, pas comme un théorème acquis."),
        PageBreak(),
    ]

    story += [
        heading("3. Protocole Ising classique : observables physiques"),
        p("Le système de référence est le modèle d’Ising ferromagnétique carré 2D, champ nul, J=kB=1, conditions périodiques et mise à jour de Wolff. Sa température critique thermodynamique est Tc=2/ln(1+√2)≈2,269185314. La validation physique est distincte du calcul TLog : elle vérifie que simulateur et analyse thermodynamique reproduisent les signatures attendues."),
        p("Le calcul de taille finie couvre L=8, 12, 16, 24, 32, 48, 64 et 76 températures. Les moments de blocs reconstruisent Cv, susceptibilité liée à |m|, Binder U4 et |m| pour 532 cellules. L’écart maximal face aux résultats sauvegardés est inférieur à 7,2×10⁻¹⁵."),
        table([
            ["Diagnostic", "Résultat archivé", "Interprétation bornée"],
            ["Croisement Binder L48/L64", "Tc=2,26997; bootstrap hiérarchique 95 % : 2,26320–2,27731", "L’intervalle contient la référence analytique."],
            ["Ajustement Binder avec correction L⁻²", "Tc=2,26937; ν=1,021; intervalles 95 % Tc [2,26773;2,27102], ν [0,945;1,096]", "Compatible avec Tc et ν=1 dans ce modèle d’ajustement."],
            ["Ajustement sans correction", "Tc=2,26823; ν=1,069; intervalle hiérarchique de ν [1,025;1,116]", "Le choix de correction est matériel; le modèle reste une hypothèse."],
            ["Dépendance entre blocs", "Maximum observé 1,49 blocs pour l’énergie L32", "Seulement 50 blocs/chaîne; diagnostic insuffisant pour prouver l’indépendance."],
        ], [105, 190, 210]),
        heading("Sensibilités et incertitude", 1),
        p("Les calculs par chaîne et bootstrap hiérarchique ajoutent l’incertitude inter-chaînes; seulement trois chaînes indépendantes sont disponibles dans le jeu FSS. Le modèle de correction L⁻², la fenêtre de température et la forme polynomiale ont été choisis analytiquement; aucune extrapolation ne doit être lue sans ces choix. Le test initial de pipeline sur un sweep L16, 35 températures et trois répétitions de 30 mesures est un contrôle d’intégration, pas une estimation robuste de Tc."),
        heading("Grille multi-tailles MCMC v5.9", 1),
        p("Une campagne séparée produit 180 trajectoires et 1 440 000 observations Wolff pour L=16,32,48. Chaque ligne correspond à une mise à jour de grappe, pas à une durée physique constante. La grille a un pas thermique de 0,02 et ajoute Tc analytique; les pics reportés sont donc des maxima de grille."),
        table([
            ["Hypothèse", "Résultat observé", "Conclusion permise"],
            ["H1 — observables physiques cohérentes", "178/180 écarts standardisés combinés |z|≤2; maximum 2,338. Pics χ : L16 2,40; L32 2,34; L48 2,30. U4(Tc): 0,6114; 0,6106; 0,6081.", "Cohérence descriptive sur ce lot; ±2 n’est pas un test d’acceptation."],
            ["H4 — label distingue Tc", "36/36 cellules thermiques, axe MC_Update, étiquette divergence.", "La sortie actuelle ne distingue pas Tc de ses voisines dans cette configuration."],
            ["H5 — non-régression brute", "580/580 médianes appariées des 29 estimateurs égales sur 20 CSV v5.8/v5.9.", "Parité des médianes brutes seulement; pas des métadonnées ou sorties typées."],
        ], [100, 250, 155]),
        PageBreak(),
    ]

    story += [
        heading("4. Axes de contrôle, flux et causalité"),
        p("Le pipeline peut examiner plusieurs contrôles ou axes, et plusieurs flux à la fois. Cette possibilité ouvre des interactions masquées, mais elle augmente aussi les choix analytiques. Les contrastes ci-dessous sont des comparaisons de sorties sous configuration; ils ne constituent pas une expérience causale tant que le générateur, les perturbations et les contrôles négatifs ne séparent pas l’effet de chaque variable."),
        table([
            ["Hypothèse H2/H3", "Résultat", "Lecture prudente"],
            ["Changer l’axe peut changer la sortie", "15 contrastes : 12 divergence, 2 saturation, 1 criticality. À Tc, axe aimantation : criticality pour L16, saturation pour L32/L48; quatre autres axes donnent divergence.", "Dépendance manifeste au contrôle choisi; pas de contrôle universel établi."],
            ["Changer la composition des flux agit sur dcrit", "5 chaînes à L16,Tc : all_fluxes 3,415±0,095; ordre |m|,m²,m⁴ 3,444±0,137; sans bruit 3,415±0,087; |m| seul 2,866±0,183.", "L’ajout de flux corrélés déplace peu ces moyennes; |m| seul est inférieur. Les 20 labels restent divergence."],
            ["Les répétitions sont indépendantes", "Spearman(E,corr voisins)=-1; paires |m|,m²,m⁴ rho=1 dans la chaîne retenue.", "Ces colonnes sont redondantes; leur nombre ne doit pas gonfler artificiellement la force de preuve."],
        ], [115, 235, 155]),
        heading("Conception recommandée pour les prochains contrastes", 1),
        p("Pré-définir un tableau facteurs × contrôles × flux : axe physique primaire, flux d’ordre, observable énergétique, flux bruit et leurres. Documenter les identités algébriques, mesurer les corrélations entre flux, garder des séries nulles sans transition et des perturbations connues, puis répéter par graine et taille. Rapporter les cellules toutes ensemble; ne sélectionner après coup que les axes donnant un label favorable."),
        p("Le résultat causal futur nécessiterait une intervention sur un axe à données autrement identiques, une randomisation ou un couplage expérimental justifié, et une règle de décision annoncée avant l’analyse. Le présent audit n’attribue aucune causalité à H2/H3."),
        PageBreak(),
    ]

    story += [
        heading("5. Calibration des 29 estimateurs"),
        p("Le criblage synthétique comporte 52 signaux et 1 508 sorties potentielles; 1 483 sont finies (98,3 %). Les familles comprennent bruit gaussien fractionnaire, graphes fBm et tores quasipériodiques k=1..4. Les tolérances ont été prédéfinies pour ce pilote, mais les répétitions restent peu nombreuses et les seuils ne sont pas des intervalles de confiance."),
        p("Les sorties Hurst, DFA, Hurst2mH et pente spectrale suivent les références des deux fGn testés; Higuchi retrouve les dimensions fBm avec de petites erreurs. Plusieurs méthodes de graphe sont biaisées dans cette implémentation. CorrelationD2/Grassberger-Procaccia approchent les dimensions de tores k=1..3 à une tolérance relativement large; les autres méthodes sous/surestiment selon les cas."),
        p("Le tore k=4 est un stress d’embedding : le code a des plongements plafonnés à 8 coordonnées alors que la reconstruction générique demande typiquement au moins 2k+1=9. Ce cas ne peut pas conclure à l’échec intrinsèque d’un estimateur. PCAIntrinsic et Fisher renvoient des ratios de participation, pas le rang 2k; les comparer à cette cible comme réussite/échec serait une erreur de quantité."),
        p("Disponibilité ≠ exactitude. Lyapunov n’est fini que pour 29/52 signaux et 1/20 tores; TwoNN peut retourner une valeur finie mais fortement biaisée. Les huit signatures sont utiles comme diagnostics, mais n’entrent pas directement dans TLog selon la taxonomie retenue."),
        heading("Audit de détection de transition par type", 1),
        p("Le protocole TLog pré-enregistré n’a trouvé aucun des 13 types d_kind qui respecte simultanément localisation, couverture, fausses alertes et stabilité entre deux fenêtres. Le contrôle nul a un taux familial de faux positifs de 25 % sur 40 balayages lisses. Persistent H0 atteint une bande proche de d=4 dans certains cas mais ne localise le pic de susceptibilité que pour 1 taille sur 6, avec le même taux familial de fausses alertes. Le résultat ne réfute pas la transition Ising; il montre que le détecteur TLog testé ne la retrouve pas de manière fiable."),
        heading("Audit individuel des 29 sorties", 1),
        p("Aucun des 21 candidats dimensionnels ne passe tous les critères pilotes. Le taux familial de faux positifs est 25 %; les huit signatures ont un taux de fausse localisation de pente de 47,5 %. Les signatures ne sont pas comparées à 4. L’analyse z-score les fenêtres locales avant calcul : elle teste leur forme, pas l’amplitude ou la variance des fluctuations thermodynamiques."),
        PageBreak(),
    ]

    story += [
        heading("6. Ising quantique : test de transfert"),
        p("Le modèle est la chaîne d’Ising transverse en anneau à température nulle, H/J = −Σ ZᵢZᵢ₊₁ − gΣXᵢ. La diagonalisation creuse résout les tailles N=8,10,12 sur 81 champs 0,60–1,40. Dans la limite thermodynamique, la référence est gc=1."),
        table([
            ["N", "Pic |d<X>/dg|", "Minimum du gap même parité"],
            ["8", "0,90", "0,92"],
            ["10", "0,93", "0,95"],
            ["12", "0,95", "0,97"],
        ], [60, 170, 190]),
        p("Les marqueurs physiques de taille finie se déplacent vers 1 quand N augmente. Le minimum du gap spectral brut à g=0,60 est un dédoublement tunnel entre états de parité opposée; ce n’est pas le gap pertinent pour la transition. C’est une précaution importante contre le choix d’un marqueur physique arbitraire."),
        p("Le pipeline v5.3 a été exécuté avec le champ g comme contrôle, aimantation transverse comme cible, fenêtre 16 et graine 20261107. Son ancre dcrit reste autour de 0,96, loin de 4, et TLog ne localise pas gc dans ce jeu. L’exécution sur un second domaine vérifie la compatibilité logicielle, pas l’universalité ni la théorie."),
        heading("7. Audit de code v5.9.1", 0),
        p("Le fichier utilisateur v5.9.0 n’a pas été édité. Une copie dérivée restaure les métadonnées d_kind v5.8, conserve les sorties brutes et corrige les cas ci-dessous. Les changements détaillés sont dans le diff et le script de construction."),
        table([
            ["Défaut ou écart observé", "Correction dans la copie dérivée", "Vérification"],
            ["Registre et profils T_log_by_d_kind absents de v5.9", "Restaure le registre et les champs typés; conserve la couche legacy.", "13 profils couvrent 21 estimateurs dimensionnels exactement une fois."],
            ["Exports CSV/JSON de type absents", "Ajoute l’export taxonomique et les colonnes d_kind/quantity_type.", "29 lignes dans CSV et 29 clés dans JSON."],
            ["Données T0/direction manquantes pouvaient devenir FAIL", "Les comparaisons incomplètes rendent INDETERMINE.", "Cas synthétiques manquants contrôlés."],
            ["Delta signé mal interprété; référence absente pouvait produire un faux PASS", "Compare les magnitudes; signe inversé ou référence nulle => INDETERMINE.", "Atténuation par 2 et par 0,4 testée; inversion et valeur absente indéterminées."],
            ["Dossier d’une graine alternative portait un nom trompeur", "Graine 123, ou 42 si la référence vaut 123; dossier nommé par sa vraie graine.", "Inscrit dans le diff/provenance."],
            ["--help échoue sur 80% interpolé par argparse", "Reformule le texte sans le caractère de formatage ambigu.", "Commande --help retourne code 0 et liste les options L7b."],
        ], [155, 205, 125]),
        heading("Résumé de validation de la copie", 1),
        p("11 contrôles ciblés passent. Sur une entrée feature réelle conservée, les 29 médianes sont identiques entre source et copie; D_vector est identique : d_sat=1,679495, d_crit=3,640356, d_div=5,568581, d_null=2,515624. Les 10 cas synthétiques L7b attendent les statuts annoncés. SHA source v5.9.0 inchangé."),
        p("<b>Limite explicite :</b> cette validation n’exécute pas le chemin complet run_full_unified_pipeline en modes L7b light/full et ne calibre pas les seuils 5, 10, 20, 0,50, 0,80 ou l’échelle. La v5.9.1 est une correction d’audit ciblée, pas une version déclarée scientifiquement validée."),
        PageBreak(),
    ]

    story += [
        heading("8. Reproduction et environnement"),
        p("La campagne a été préparée sous Windows avec Python 3.11.9 et le .venv local. Le verrou requirements-lock.txt enregistre les paquets observés. Le dossier .venv n’est pas distribué : il est volumineux et propre à la machine."),
        p("Les commandes du README reproduisent la copie d’audit et montrent le chemin CLI. Le PDF contient la totalité des sources Python et scripts comme code appendice et les joint en fichiers exacts. Les données d’entrée, CSV de sortie, JSON, journaux, NPZ et images sont joints au PDF; le ZIP conserve en parallèle leur arborescence originale."),
        heading("Rejeu des contrôles ciblés", 1),
        code_block(
            ".venv\\Scripts\\python.exe audit_release\\build_v5_9_1_auditfix.py\n"
            ".venv\\Scripts\\python.exe audit_release\\validate_v5_9_1_auditfix.py\n"
            "PowerShell: .\\REPRODUCE_AUDIT.ps1"
        ),
        heading("Rejouer le pipeline", 1),
        code_block(
            ".venv\\Scripts\\python.exe audit_release\\UNIVERSAL_LOG_v5_9_1_AUDITFIX.py "
            "--input chemin\\donnees.csv --target cible --control axe "
            "--control-mode single --output sortie\n"
            "Multi-axes: --controls axe1,axe2,axe3 --control-mode multi"
        ),
        p("Avant le run, relever les colonnes disponibles, la définition cible/axe, l’ordre des observations, les valeurs manquantes, la graine, la fenêtre, le mode de pipeline et la méthode de sélection des flux. Garder les sorties brutes; l’agrégation ne doit pas effacer les différences entre axes."),
        heading("Limites de répétition numérique", 1),
        p("Les versions de bibliothèques, le parallélisme, les générateurs aléatoires et les opérations flottantes peuvent modifier des détails d’une exécution. Une reproduction exacte exige les mêmes entrées, versions, graines et options. Les rapports et empreintes archivés séparent la reproduction du calcul et la reproduction de l’interprétation."),
        heading("Pièces jointes du PDF", 1),
        p(f"Ce document contient {len(embedded_paths)} pièces jointes, soit les fichiers du projet hors .venv, caches, livrables auto-référentiels et exécutables compilés. Chaque nom d’attachement est préfixé par un index; sa description conserve le chemin de projet et le SHA-256. Utiliser le panneau Pièces jointes du lecteur PDF pour extraire les fichiers; utiliser le ZIP pour reconstruire automatiquement les dossiers."),
        PageBreak(),
    ]

    story += [
        heading("9. Interprétation générale et limites"),
        p("Les résultats soutiennent un usage de UNIVERSAL_LOG comme banc exploratoire multi-estimateurs avec contrôle des axes, flux, stabilité et traçabilité. Ils ne soutiennent pas encore la proposition d’un instrument universel qui identifie les régimes physiques à partir de TLog seul."),
        *paragraph_story([
            "Le calcul de TLog est simple; la définition universelle d et de n ne l’est pas.",
            "Les 29 estimateurs incluent des objets mathématiques différents. Une taxonomie d_kind améliore l’audit, sans prouver une comparabilité.",
            "Les contrôles multiples révèlent une sensibilité à la configuration; corrélations entre flux et contrôles négatifs restent déterminants.",
            "Les observables physiques Ising réussissent mieux leur test de repère que le label de régime du pipeline.",
            "Les valeurs de L7b actuelles sont des heuristiques; un statut PASS ne signifie pas que l’hypothèse scientifique est vraie.",
            "Les deux domaines Ising testés ne suffisent pas pour prouver une universalité tous domaines.",
        ]),
        heading("Prochaines étapes recommandées, par ordre", 1),
        table([
            ["Priorité", "Action", "Critère de sortie"],
            ["1", "Intégrer et documenter L7b light/full dans le chemin complet; tests manquants/erreurs/entrées dégénérées.", "Logs complets, verdicts reproductibles, aucun PASS sur preuve absente."],
            ["2", "Fixer contrat d/n par d_kind et produire la matrice estimateur → quantité → unité → incertitude → référence.", "Pas de comparaison à 4 tant que la quantité et son domaine ne sont pas justifiés."],
            ["3", "Calibrer les seuils sur signaux synthétiques et nuls séparés du jeu de test; pré-enregistrer une règle.", "Taux faux positifs/couverture/biais avec intervalles et réplications."],
            ["4", "Répliquer MCMC Ising avec plus de tailles, chaînes, mesures temporelles brutes et autocorrélation.", "Incertitude chaîne/bloc adéquate et maxima/intersections stables."],
            ["5", "Tester axes et flux dans un plan factoriel, dont relations algébriques et leurres.", "Effets séparables, robustesse inter-graine, distinction corrélation/causalité."],
            ["6", "Valider ensuite sur un domaine non Ising avec cibles physiques connues et contrôles nuls.", "Résultats répliqués et critères identiques fixés avant analyse."],
        ], [48, 260, 177]),
        heading("10. Licence, partage et citations", 0),
        p("Licence retenue par le propriétaire : code sous MIT; documentation, figures et résultats sous CC BY 4.0. Les licences complètes/pointeurs, le périmètre et les notices de dépendances sont à la racine du paquet. La licence des logiciels tiers conserve son effet propre."),
        p("Lors du partage, conserver l’attribution UNIVERSAL_LOG project contributors, signaler les modifications, inclure les notices de licence et citer les sources scientifiques des protocoles. Le jeu expérimental doit être décrit comme données générées, avec paramètres, graine et version du générateur."),
        PageBreak(),
    ]

    story += [
        heading("Annexe A — galerie des figures"),
        p("Toutes les figures PNG distinctes du projet sont affichées ci-dessous. Les fichiers octet pour octet identiques ne sont affichés qu’une fois; toutes leurs occurrences restent listées et tous les fichiers exacts sont joints au PDF et au ZIP."),
    ]
    for number, (digest, paths) in enumerate(figure_groups(), 1):
        image_path = paths[0]
        from reportlab.lib.utils import ImageReader
        iw, ih = ImageReader(str(image_path)).getSize()
        maxw, maxh = 495, 455
        scale = min(maxw / iw, maxh / ih, 1.0)
        img = Image(str(image_path), width=iw * scale, height=ih * scale)
        img.hAlign = "CENTER"
        rels = [path.relative_to(ROOT).as_posix() for path in paths]
        caption = (
            f"Figure A.{number} — {html.escape(rels[0])}<br/>"
            f"{iw} × {ih} px; SHA-256 {digest}. Occurrences identiques ({len(rels)}): "
            + "<br/>".join(html.escape(x) for x in rels)
        )
        story.append(KeepTogether([img, Paragraph(caption, styles["AuditCaption"])]))
        story.append(Spacer(1, 5))

    story += [
        PageBreak(),
        heading("Annexe B — tables et petits résumés machine-lisibles"),
        p("Les fichiers CSV jusqu’à 64 Kio et les JSON jusqu’à 128 Kio sont reproduits intégralement en texte monospace. Les fichiers plus grands ne sont pas tronqués dans le projet : ils sont attachés au PDF et présents intégralement dans le ZIP, avec lignes/tailles/empreintes au catalogue."),
    ]
    structured = []
    for path in walk_files(include_catalog=True):
        ext = path.suffix.lower()
        if ext == ".csv" and path.stat().st_size <= 65536:
            structured.append(path)
        elif ext == ".json" and path.stat().st_size <= 131072:
            structured.append(path)
    for path in structured:
        rel = path.relative_to(ROOT).as_posix()
        story += [heading(html.escape(rel), 1), code_block(path.read_text(encoding="utf-8-sig", errors="replace"), width=118)]

    story += [
        PageBreak(),
        heading("Annexe C — rapports et journaux source complets"),
        p("Les fichiers documentaires ci-dessous sont reproduits tels quels après normalisation d’affichage seulement; leurs octets d’origine sont joints et hachés séparément."),
    ]
    text_exts = {".md", ".txt", ".log", ".diff", ".jsonl", ".rst"}
    text_paths = [path for path in walk_files(include_catalog=True) if path.suffix.lower() in text_exts]
    for path in text_paths:
        rel = path.relative_to(ROOT).as_posix()
        story += [heading(html.escape(rel), 1), code_block(path.read_text(encoding="utf-8-sig", errors="replace"), width=118)]

    story += [
        PageBreak(),
        heading("Annexe D — code source complet"),
        p("Les scripts sont transcrits en appendice avec numéros de ligne pour faciliter la revue. Les sauts visuels dans les lignes très longues ne changent pas les fichiers; les octets exacts se trouvent dans les pièces jointes et le ZIP."),
    ]
    code_paths = [path for path in walk_files(include_catalog=True) if path.suffix.lower() in {".py", ".ps1", ".bat", ".sh"}]
    for path in code_paths:
        rel = path.relative_to(ROOT).as_posix()
        story += [
            heading(html.escape(rel), 1),
            p(f"Taille : {path.stat().st_size:,} octets; SHA-256 : {sha256_file(path)}", small=True),
            code_block(path.read_text(encoding="utf-8-sig", errors="replace"), width=118, numbered=True),
        ]

    story += [
        PageBreak(),
        heading("Annexe E — catalogue complet des fichiers"),
        p("Le catalogue inclut les chemins, extensions, octets, nombres de lignes de données CSV et SHA-256. Le fichier final inclus dans le ZIP est recalculé après la création de ce PDF et contient également son empreinte."),
    ]
    records = [["Chemin relatif", "Octets", "Lignes CSV", "SHA-256"]]
    for row in catalog_rows:
        records.append([
            html.escape(str(row["path"])),
            f'{int(row["bytes"]):,}',
            str(row["records"]),
            f"<font name='{MONO}' size='4.7'>{row['sha256']}</font>",
        ])
    widths = [220, 60, 58, 205]
    for start in range(0, len(records), 250):
        chunk = records[start:start + 250]
        story.append(table(chunk, widths, header=True, repeat=1))

    story += [
        PageBreak(),
        heading("Annexe F — pièces jointes intégrales"),
        p("Le panneau Pièces jointes contient les fichiers du projet à leurs octets d’origine : sources, scripts, documents, résultats, journaux, données brutes et images. Le ZIP est l’outil recommandé pour extraire l’arborescence complète. Aucun dossier .venv, bytecode, cache ou outil de génération du runtime n’est distribué."),
        p("Fin du livre blanc. Toute interprétation doit citer le protocole, le fichier source, la version, la graine et les axes/flux utilisés."),
    ]
    return story


def attach_project_files(pdf_path: Path, paths: list[Path]) -> None:
    import fitz

    document = fitz.open(pdf_path)
    document.set_metadata({
        "title": "UNIVERSAL_LOG — livre blanc d’audit reproductible",
        "author": "UNIVERSAL_LOG project contributors",
        "subject": "Code, théorie TLog, résultats Ising, validation et données reproductibles",
        "keywords": "UNIVERSAL_LOG, TLog, audit, Ising, reproducibility, MIT, CC BY 4.0",
        "creator": "ReportLab and PyMuPDF",
    })
    for index, path in enumerate(paths, 1):
        rel = path.relative_to(ROOT).as_posix()
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", rel.replace("/", "__"))
        attachment_name = f"{index:05d}__{safe}"[:220]
        digest = sha256_file(path)
        description = f"Project relative path: {rel}; bytes: {path.stat().st_size}; SHA-256: {digest}"
        document.embfile_add(
            attachment_name, path.read_bytes(),
            filename=attachment_name, ufilename=attachment_name, desc=description,
        )
        if index % 50 == 0:
            print(f"[pièces jointes PDF] {index}/{len(paths)}", flush=True)
    tmp = pdf_path.with_suffix(".with_attachments.pdf")
    document.save(tmp, garbage=3, deflate=True, deflate_fonts=True)
    document.close()
    tmp.replace(pdf_path)


def main():
    QA_DIR.mkdir(parents=True, exist_ok=True)
    print("[catalogue] hash des fichiers du projet…", flush=True)
    catalog_rows = create_catalog()
    embedded_paths = walk_files(include_catalog=True)
    print(f"[livre blanc] {len(catalog_rows)} entrées de catalogue; {len(embedded_paths)} pièces jointes à préparer.", flush=True)
    doc = WhitepaperDoc(str(PDF_PATH))
    doc.multiBuild(build_story(catalog_rows, embedded_paths))
    print(f"[livre blanc] PDF de base : {PDF_PATH.stat().st_size:,} octets", flush=True)
    attach_project_files(PDF_PATH, embedded_paths)
    print(json.dumps({
        "pdf": str(PDF_PATH),
        "pdf_bytes": PDF_PATH.stat().st_size,
        "project_catalog_rows": len(catalog_rows),
        "embedded_files": len(embedded_paths),
        "unique_figures": len(figure_groups()),
        "code_files": sum(p.suffix.lower() in {".py", ".ps1", ".bat", ".sh"} for p in embedded_paths),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
