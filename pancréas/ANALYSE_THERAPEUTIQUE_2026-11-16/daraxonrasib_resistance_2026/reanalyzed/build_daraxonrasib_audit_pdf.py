#!/usr/bin/env python3
"""Build a printable audit addendum from the reanalysis artifacts."""
from __future__ import annotations
import csv, hashlib, json, re, textwrap
from pathlib import Path
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A3
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak, Spacer, Image, LongTable, TableStyle

ROOT = Path(__file__).resolve().parent
PDF = ROOT / "AUDIT_ADDENDUM_RESISTANCE_DARAXONRASIB_PDACS_v1.pdf"
REPORT = ROOT / "RAPPORT_REANALYSE_DARAXONRASIB.md"
ANALYSIS = ROOT.parent / "reanalyze_daraxonrasib_source_data.py"
FIGURE = ROOT / "figure5d_pfs_km.png"
MANIFEST = ROOT / "manifest.json"
PAGE = landscape(A3)
WIDTH, HEIGHT = PAGE
LEFT = RIGHT = 20 * mm
TOP = 22 * mm
BOTTOM = 18 * mm
USABLE = WIDTH - LEFT - RIGHT

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitleX", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=27, leading=33, textColor=colors.HexColor("#14324A"), alignment=0, spaceAfter=10))
styles.add(ParagraphStyle(name="CoverSubX", parent=styles["Normal"], fontSize=15, leading=21,
    textColor=colors.HexColor("#36576E"), spaceAfter=18))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=19, leading=24, textColor=colors.HexColor("#14324A"), spaceBefore=8, spaceAfter=10))
styles.add(ParagraphStyle(name="H2X", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=13.5, leading=17, textColor=colors.HexColor("#1D5877"), spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name="H3X", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=10.5, leading=13, textColor=colors.HexColor("#287C87"), spaceBefore=6, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9, leading=12.5, spaceAfter=5, splitLongWords=1))
styles.add(ParagraphStyle(name="BulletX", parent=styles["BodyX"], leftIndent=12, firstLineIndent=-8, spaceAfter=3))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=7, leading=9, textColor=colors.HexColor("#455A64"), splitLongWords=1))
styles.add(ParagraphStyle(name="CellX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=4.6, leading=5.6, splitLongWords=1, wordWrap="CJK"))
styles.add(ParagraphStyle(name="CellHeadX", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=4.8, leading=5.8, textColor=colors.white, splitLongWords=1, wordWrap="CJK"))
styles.add(ParagraphStyle(name="CodeX", parent=styles["BodyText"], fontName="Courier",
    fontSize=5.1, leading=6.3, splitLongWords=1, wordWrap="CJK", leftIndent=1.5))

class AuditDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename,pagesize=PAGE,leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM)
        frame=Frame(LEFT,BOTTOM,USABLE,HEIGHT-TOP-BOTTOM,id="main",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="audit",frames=[frame],onPage=self.paint_page)])
    def paint_page(self,canvas,doc):
        canvas.saveState()
        if doc.page>1:
            canvas.setStrokeColor(colors.HexColor("#D7E1E6"))
            canvas.line(LEFT,HEIGHT-13*mm,WIDTH-RIGHT,HEIGHT-13*mm)
            canvas.setFont("Helvetica",7);canvas.setFillColor(colors.HexColor("#607D8B"))
            canvas.drawString(LEFT,HEIGHT-10*mm,"UNIVERSAL LOG — audit PDAC / résistance au daraxonrasib")
            canvas.drawRightString(WIDTH-RIGHT,HEIGHT-10*mm,"v1 • 16 novembre 2026")
            canvas.line(LEFT,10*mm,WIDTH-RIGHT,10*mm)
            canvas.drawString(LEFT,6*mm,"Données publiées réanalysées; pas une validation indépendante ni une recommandation clinique.")
            canvas.drawRightString(WIDTH-RIGHT,6*mm,f"Page {doc.page}")
        canvas.restoreState()

def inline_markup(text):
    x=escape(text,quote=False)
    return re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",x)

def markdown_story(path):
    story=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        s=line.strip()
        if not s:story.append(Spacer(1,2));continue
        if s.startswith("# "):story.append(Paragraph(inline_markup(s[2:]),styles["H1X"]))
        elif s.startswith("## "):story.append(Paragraph(inline_markup(s[3:]),styles["H2X"]))
        elif s.startswith("### "):story.append(Paragraph(inline_markup(s[4:]),styles["H3X"]))
        elif s.startswith("- "):story.append(Paragraph(inline_markup(s[2:]),styles["BulletX"],bulletText="•"))
        elif re.match(r"^\d+\.\s",s):story.append(Paragraph(inline_markup(s),styles["BulletX"]))
        else:story.append(Paragraph(inline_markup(s),styles["BodyX"]))
    return story

def read_table_csv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:rows=list(csv.reader(f))
    rows=[r for r in rows if any(x.strip() for x in r)]
    if not rows:return [],[]
    if path.name.startswith("clinical_") or path.name=="preclinical_model_inventory.csv":
        if len(rows)>1:rows=rows[1:]
    header=rows[0];data=rows[1:]
    if path.name.startswith("clinical_") and path.name not in ("clinical_replication_metrics.csv","clinical_replication_tests.csv"):
        data=[r for r in data if r and r[0].startswith("Patient ")]
    if path.name=="preclinical_model_inventory.csv":data=[r for r in data if r and r[0]]
    return header,data

def make_data_table(header,rows):
    if not header:return []
    n=len(header);widths=[USABLE/n]*n
    matrix=[[Paragraph(inline_markup(str(x)),styles["CellHeadX"]) for x in header]]
    for row in rows:
        row=row+[""]*max(0,n-len(row))
        matrix.append([Paragraph(inline_markup(str(x)),styles["CellX"]) for x in row[:n]])
    table=LongTable(matrix,colWidths=widths,repeatRows=1,hAlign="LEFT",splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#214B63")),
        ("GRID",(0,0),(-1,-1),0.25,colors.HexColor("#B9C8CE")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F2F6F8")]),
    ]))
    return [table]

def code_story(path):
    story=[PageBreak(),Paragraph("Appendice — code d’analyse reproductible",styles["H1X"]),
           Paragraph("Le script source exact est également livré séparément. Les numéros indiquent les lignes du fichier; les lignes longues sont renvoyées visuellement.",styles["SmallX"]),Spacer(1,5)]
    for i,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        chunks=textwrap.wrap(line,150,replace_whitespace=False,drop_whitespace=False) or [""]
        for k,chunk in enumerate(chunks):
            prefix=f"{i:04d} " if k==0 else "     "
            story.append(Paragraph(escape(prefix+chunk,quote=False),styles["CodeX"]))
    return story

def main():
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    story=[Spacer(1,30*mm),Paragraph("UNIVERSAL LOG",styles["CoverTitleX"]),
      Paragraph("Audit addendum — résistance au daraxonrasib dans l’adénocarcinome canalaire pancréatique",styles["CoverSubX"]),
      Paragraph("Recalcul des suppléments cliniques et des données précliniques source • version 1 • 16 novembre 2026",styles["BodyX"]),
      Spacer(1,10*mm),Paragraph("<b>Classement des affirmations</b>",styles["H2X"]),
      Paragraph("<b>Résultat recalculé:</b> chiffres extraits/recalculés des fichiers source; non indépendants de l’étude publiée.",styles["BodyX"]),
      Paragraph("<b>Constat d’étude:</b> résultats précliniques/ctDNA rapportés par les auteurs.",styles["BodyX"]),
      Paragraph("<b>Hypothèse suivante:</b> piste à évaluer dans des données et modèles externes.",styles["BodyX"]),
      Paragraph("<b>Non démontré:</b> aucune guérison ni combinaison efficace chez l’humain n’est établie par cette réanalyse.",styles["BodyX"]),
      Spacer(1,7*mm),Paragraph("Article primaire: Aronchik et al., Nature Medicine (2026), DOI 10.1038/s41591-026-04537-w.",styles["BodyX"]),
      Paragraph("Entrées: tableaux supplémentaires MOESM3; source data Figures 4–5 MOESM7/MOESM8. Empreintes SHA-256 dans manifest.json.",styles["BodyX"]),
      Paragraph("Réexécution: utiliser l’environnement .venv du projet et lancer reanalyze_daraxonrasib_source_data.py. Le code n’installe rien.",styles["BodyX"]),
      PageBreak()]
    story.extend(markdown_story(REPORT))
    story.extend([PageBreak(),Paragraph("Figure — PFS préclinique, Figure 5d",styles["H1X"]),
      Paragraph("Reconstruction Kaplan–Meier à partir des 108 lignes individuelles du fichier GraphPad source. Les marqueurs + indiquent les observations censurées.",styles["BodyX"]),
      Spacer(1,5),Image(str(FIGURE),width=USABLE*0.88,height=USABLE*0.52,kind="proportional"),
      Paragraph("Codes du fichier Prism: 1=progression, 0=censure. Le log-rank recalculé retrouve p=0,046684 entre monothérapies; doublet contre chacune des monothérapies p<0,0001. Contrôle de cohérence, pas réplication indépendante.",styles["SmallX"])])
    csv_paths=sorted(p for p in ROOT.glob("*.csv") if p.name not in ("fig4_amivantamab_endpoint_comparisons_initial.csv",))
    story.extend([PageBreak(),Paragraph("Appendice — toutes les tables CSV extraites ou calculées",styles["H1X"]),
      Paragraph("Les tableaux conservent les valeurs à la précision source. Les CSV séparés restent la référence pour une lecture plein texte.",styles["SmallX"])])
    for index,path in enumerate(csv_paths):
        if index>0:story.append(PageBreak())
        header,rows=read_table_csv(path)
        story.extend([Paragraph(path.name,styles["H2X"]),Paragraph(f"{len(rows)} lignes de données; {len(header)} colonnes.",styles["SmallX"])])
        story.extend(make_data_table(header,rows))
    story.extend(code_story(ANALYSIS))
    story.extend([PageBreak(),Paragraph("Appendice — manifeste et empreintes SHA-256",styles["H1X"]),
      Paragraph("Les empreintes identifient les fichiers d’entrée et les produits listés à la date de génération du manifeste. Le PDF final est accompagné d’un fichier .sha256 séparé.",styles["BodyX"])])
    for section in ("inputs","runtime","outputs"):
        story.append(Paragraph(section,styles["H2X"]))
        val=manifest.get(section,{})
        if isinstance(val,dict):
            for name,item in val.items():
                if isinstance(item,dict):
                    info="; ".join(f"{k}={v}" for k,v in item.items())
                    story.append(Paragraph(inline_markup(f"{name}: {info}"),styles["SmallX"]))
                else:story.append(Paragraph(inline_markup(f"{name}: {item}"),styles["SmallX"]))
    story.append(Paragraph(inline_markup("Script: "+json.dumps(manifest.get("script",{}),ensure_ascii=False)),styles["SmallX"]))
    story.append(Paragraph(inline_markup("Interprétation: "+manifest.get("interpretation","")),styles["SmallX"]))
    doc=AuditDoc(str(PDF))
    doc.title="Audit addendum — résistance au daraxonrasib dans le PDAC"
    doc.author="UNIVERSAL LOG — réanalyse traçable"
    doc.subject="Réanalyse des données publiques de résistance PDAC"
    doc.build(story)
    digest=hashlib.sha256(PDF.read_bytes()).hexdigest()
    (ROOT/(PDF.name+".sha256")).write_text(f"{digest}  {PDF.name}\n",encoding="ascii")
    print(json.dumps({"pdf":str(PDF),"bytes":PDF.stat().st_size,"sha256":digest,
                      "csv_appendices":len(csv_paths)},ensure_ascii=False))

if __name__=="__main__":main()
