from __future__ import annotations
import csv, json, re, textwrap, hashlib
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

OUT=Path(r'''pancréas\ANALYSE_THERAPEUTIQUE_2026-11-16''')
REPORT=OUT/'AUDIT_PRISM_PDACS_v1.md'; GRID=OUT/'pdac_prism_control_by_drug_fluxes.csv'
MANIFEST=OUT/'analysis_manifest.json'; CODE=OUT/'analyze_pdac_prism_multicontrol.py'
PIPE=Path(r'''pancréas\Archive complète PDAC v6 — ZIP\universal_v6.0.0_cohen.py''')
PDF=OUT/'AUDIT_PRISM_PDACS_v1_COMPLET.pdf'; PAGE=landscape(A3)
fonts=[(r'C:\Windows\Fonts\arial.ttf','AuditSans'),(r'C:\Windows\Fonts\arialbd.ttf','AuditSans-Bold'),(r'C:\Windows\Fonts\consola.ttf','AuditMono')]
for path,name in fonts:
    p=Path(path)
    if p.exists(): pdfmetrics.registerFont(TTFont(name,str(p)))
BASE='AuditSans' if Path(fonts[0][0]).exists() else 'Helvetica'
BOLD='AuditSans-Bold' if Path(fonts[1][0]).exists() else 'Helvetica-Bold'
MONO='AuditMono' if Path(fonts[2][0]).exists() else 'Courier'
NAVY=colors.HexColor('#12344A'); BLUE=colors.HexColor('#24617B')
LIGHT=colors.HexColor('#EAF1F4'); GRIDC=colors.HexColor('#C9D4DA'); INK=colors.HexColor('#1D2935')

styles={
 'title':ParagraphStyle('title',fontName=BOLD,fontSize=24,leading=29,textColor=NAVY,spaceAfter=14),
 'h1':ParagraphStyle('h1',fontName=BOLD,fontSize=16,leading=20,textColor=NAVY,spaceBefore=10,spaceAfter=6),
 'h2':ParagraphStyle('h2',fontName=BOLD,fontSize=11,leading=14,textColor=BLUE,spaceBefore=8,spaceAfter=5),
 'body':ParagraphStyle('body',fontName=BASE,fontSize=9,leading=12.5,textColor=INK,spaceAfter=5),
 'bullet':ParagraphStyle('bullet',fontName=BASE,fontSize=8.6,leading=11.5,textColor=INK,leftIndent=13,firstLineIndent=-9,spaceAfter=3),
 'small':ParagraphStyle('small',fontName=BASE,fontSize=7,leading=9,textColor=colors.HexColor('#475569')),
 'cell':ParagraphStyle('cell',fontName=BASE,fontSize=7,leading=8.5,textColor=INK),
 'head':ParagraphStyle('head',fontName=BOLD,fontSize=7,leading=8.5,textColor=colors.white),
}

def dash(s): return str(s).replace('\u2010','-').replace('\u2011','-').replace('\u2012','-').replace('\u2013','-').replace('\u2014','-').replace('\u2212','-').replace('\u2192',' to ')
def inline(s):
    s=dash(s); links=[]
    def save_link(m): links.append((m.group(1),m.group(2))); return f'ZZLINK{len(links)-1}ZZ'
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',save_link,s)
    s=escape(s)
    s=re.sub(r'`([^`]+)`',lambda m:f'<font name="{MONO}" color="#334155">{m.group(1)}</font>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    for i,(label,url) in enumerate(links): s=s.replace(f'ZZLINK{i}ZZ',f'<link href="{escape(url)}" color="#175b85"><u>{escape(label)}</u></link>')
    return s

c=canvas.Canvas(str(PDF),pagesize=PAGE,pageCompression=1)
c.setTitle('Audit therapeutique PDAC - PRISM v1 complet')
c.setAuthor('Audit reproductible UNIVERSAL_LOG')
W,H=PAGE; L=20*mm; R=W-20*mm; TOP=H-24*mm; BOTTOM=24*mm; y=TOP
page_num=0; page_open=False

def start_page(section='Audit therapeutique PDAC'):
    global y,page_num,page_open
    if page_open:
        footer(); c.showPage()
    page_num+=1; page_open=True; y=TOP
    c.setFillColor(NAVY); c.rect(0,H-12*mm,W,12*mm,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont(BOLD,7.5); c.drawString(L,H-8*mm,dash(section))
    c.setStrokeColor(GRIDC); c.setLineWidth(.35); c.line(L,16*mm,R,16*mm)

def footer():
    c.saveState(); c.setFillColor(colors.HexColor('#52616B')); c.setFont(BASE,6.8)
    c.drawString(L,10*mm,'Audit exploratoire PDAC - UNIVERSAL_LOG v6.0.0 / PRISM 24Q2')
    c.drawRightString(R,10*mm,f'Page {page_num}')
    c.restoreState()

def ensure(h):
    global y
    if y-h < BOTTOM: start_page('Audit therapeutique PDAC - suite')

def draw_p(text,style='body',gap=4):
    global y
    p=Paragraph(inline(text),styles[style]); w=R-L; _,h=p.wrap(w,y-BOTTOM)
    ensure(h+gap); _,h=p.wrap(w,y-BOTTOM); p.drawOn(c,L,y-h); y-=h+gap

def draw_table(rows,widths=None,fs=7):
    global y
    data=[]
    for ri,row in enumerate(rows):
        sty=styles['head'] if ri==0 else styles['cell']
        data.append([Paragraph(inline(str(v)),sty) for v in row])
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('GRID',(0,0),(-1,-1),.35,GRIDC),
       ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),
       ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
       ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    _,h=t.wrap(R-L,H); ensure(h+6); t.drawOn(c,L,y-h); y-=h+7

def begin(title,subtitle=None):
    start_page(title)
    if subtitle: draw_p(subtitle,'small',8)

# Cover page.
begin('PANCREATIC CANCER - THERAPEUTIC SCREEN AUDIT','Correction du criblage PRISM, analyse multi-controles, graphiques, resultats complets et code reproductible.')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
counts=manifest['sample_counts']; axes=len(manifest['selection']['control_genes']); flux=counts['prism_compound_rows']
draw_p('Dossier preclinique exploratoire - 16 novembre 2026','h1')
draw_p('Version d’analyse: v1 | Pipeline examine: UNIVERSAL_LOG v6.0.0 Cohen-d | Calculs executes avec le .venv local.','body')
draw_table([['Repere','Valeur'],['Flux PRISM',f'{flux:,}'],['Modeles PDAC dans PRISM',str(counts['exact_pdac_models_in_prism_matrix'])],['Modeles avec CRISPR associe',str(counts['models_used_for_gene_control_grid'])],['Axes moleculaires',str(axes)],['Comparaisons statistiques CRISPR x PRISM',f'{flux*axes:,}']],widths=[85*mm,70*mm])
draw_p('Conclusion de lecture: AS-77 presente une association preclinique a verifier. Elle ne passe pas la correction familiale sur les 13 axes et tous les flux; aucun remede n’est demontre. Le pipeline ne produit pas de T0/TLog interpretable sur cet echantillon transversal.','h2')
start_page('Audit therapeutique PDAC - rapport')

# Render the complete written report, including its short tables and methods.
lines=REPORT.read_text(encoding='utf-8').splitlines(); i=0; in_code=False
while i<len(lines):
    line=lines[i]
    if not line.strip(): i+=1; continue
    if line.strip().startswith('```'):
        i+=1; block=[]
        while i<len(lines) and not lines[i].strip().startswith('```'):
            block.append(dash(lines[i])); i+=1
        i+=1
        for code_line in block:
            wrapped=textwrap.wrap(code_line,width=170,replace_whitespace=False,drop_whitespace=False,break_long_words=True,break_on_hyphens=False) or ['']
            for part in wrapped:
                ensure(10); c.setFillColor(INK); c.setFont(MONO,6.5); c.drawString(L,y,part); y-=8
        y-=5; continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-{2,}:?',x or '-') for x in cells): rows.append(cells)
            i+=1
        if rows:
            widths=[(R-L)/len(rows[0])]*len(rows[0]); draw_table(rows,widths)
        continue
    if line.startswith('# '): draw_p(line[2:],'title',7)
    elif line.startswith('## '): draw_p(line[3:],'h1',5)
    elif line.startswith('### '): draw_p(line[4:],'h2',4)
    elif line.startswith('- '): draw_p('• '+line[2:],'bullet',2)
    elif line.startswith('> '): draw_p(line[2:],'small',4)
    else:
        parts=[line.strip()]; i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','- ','```','> ')):
            parts.append(lines[i].strip()); i+=1
        draw_p(' '.join(parts),'body',4); continue
    i+=1

# Figures.
for image_name,caption in [('krasscore_selected_drug_response.png','Dependance KRAS contre LFC PRISM pour AS-77, MRTX1133 et gemcitabine; LFC basse = baisse de viabilite.'),('krasscore_top15_descriptive.png','Quinze correlations descriptives les plus negatives pour KRAS. Un rang n’est pas une validation.')]:
    start_page('Figures de synthese')
    img=OUT/image_name
    if img.exists():
        iw,ih=__import__('PIL.Image',fromlist=['Image']).open(img).size
        scale=min((R-L)/iw,(H-75*mm)/ih)
        c.drawImage(str(img),L,(H+15*mm)-ih*scale,width=iw*scale,height=ih*scale, preserveAspectRatio=True,anchor='n')
        y=40*mm; draw_p(caption,'body',4)

# Compact complete summary table.
start_page('Resume des axes de controle')
draw_p('Nombre de tests a q<0,05 selon la famille de correction. Un resultat « q global » corrige les 13 controles x 6 790 flux.','body')
s=pd.read_csv(OUT/'pdac_prism_control_summary.csv')
rows=[['Controle','Flux','Tests','q<.05 axe','q<.05 ecran','q<.05 global','rho min','rho max']]
for _,r in s.iterrows(): rows.append([str(r.control_gene),str(int(r.n_drug_fluxes)),str(int(r.tests_estimable)),str(int(r.q05_within_control)),str(int(r.q05_within_control_screen)),str(int(r.q05_global)),f'{r.strongest_negative_rho:.3f}',f'{r.strongest_positive_rho:.3f}'])
draw_table(rows,widths=[45*mm,30*mm,30*mm,35*mm,38*mm,35*mm,32*mm,32*mm])

# Full statistical appendix. Stream rows directly to Canvas to avoid a large layout-engine table.
start_page('Appendice A - Resultats complets controle x flux')
draw_p('Toutes les paires CRISPR-control x reponse medicamenteuse PRISM sont imprimees ci-dessous. 88 270 lignes. Les q values: axe = tous les composes de l’axe; ecran = controle x ecran; global = 13 axes x tous les composes. Les metadonnees detaillees et moyennes de groupe restent dans le CSV associe.','small',6)
colspec=[('control_gene',8),('compound_id',29),('drug_name',24),('screen',11),('dose_uM',8),('n_cell_lines',4),('spearman_dependency_vs_LFC',8),('p_spearman_two_sided',10),('q_BH_within_control_all_screens',10),('q_BH_within_control_and_screen',10),('q_BH_global_all_controls_and_drugs',10),('delta_LFC_high_dependency_minus_low_dependency',10)]
headers=[('Control',8),('Compound ID',29),('Drug',24),('Screen',11),('Dose',8),('n',4),('rho',8),('p',10),('q_axis',10),('q_screen',10),('q_global',10),('Delta',10)]
font_size=6.2; lead=7.2; max_rows=int((H-48*mm)/lead)-3

def fmt(v,width,isnum=False):
    if v is None or v=='': s=''
    else:
        try:
            x=float(v)
            if isnum: s=f'{x:.3g}'
            else: s=str(v)
        except Exception: s=str(v)
    if len(s)>width: s=s[:width-1]+'~'
    return s.ljust(width)

def draw_grid_header():
    global y
    c.setFillColor(NAVY); c.rect(L,y-lead,R-L,lead,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont(BOLD,font_size)
    line=' '.join(fmt(label,w) for label,w in headers)
    c.drawString(L+2,y-lead+1,line); y-=lead+1

draw_grid_header(); idx=0
with GRID.open('r',encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    for row in reader:
        if y-lead < BOTTOM:
            c.setFillColor(colors.HexColor('#52616B')); c.setFont(BASE,6); c.drawRightString(R,BOTTOM-8,f'Rows {idx-max_rows+1:,} - {idx:,}')
            start_page('Appendice A - Resultats complets controle x flux'); draw_grid_header()
        pieces=[]
        for key,width in colspec:
            numeric=key not in ('control_gene','compound_id','drug_name','screen')
            pieces.append(fmt(row.get(key,''),width,numeric))
        c.setFont(MONO,font_size); c.setFillColor(INK)
        if idx%2==1:
            c.setFillColor(colors.HexColor('#F3F6F8')); c.rect(L,y-lead,R-L,lead,fill=1,stroke=0); c.setFillColor(INK)
        c.drawString(L+2,y-lead+1,' '.join(pieces)); y-=lead; idx+=1
c.setFillColor(colors.HexColor('#52616B')); c.setFont(BASE,6); c.drawRightString(R,BOTTOM-8,f'Rows {idx-max_rows+1:,} - {idx:,} | Total {idx:,}')

# Full analysis script appendix.
start_page('Appendice B - Code d’analyse integral')
draw_p('Code statistique execute. Le pipeline UNIVERSAL_LOG v6.0.0 est identifie dans le manifeste par version et empreinte SHA-256; il n’a pas ete lance pour produire T0/TLog, car les echantillons sont non ordonnes et n=38 < minimum fast=50.','small',6)
for ln,line in enumerate(CODE.read_text(encoding='utf-8-sig').splitlines(),1):
    text=f'{ln:04d}  {dash(line)}'
    chunks=textwrap.wrap(text,width=215,replace_whitespace=False,drop_whitespace=False,break_long_words=True,break_on_hyphens=False) or ['']
    for chunk in chunks:
        if y-8<BOTTOM: start_page('Appendice B - Code d’analyse integral - suite')
        c.setFillColor(INK); c.setFont(MONO,5.2); c.drawString(L,y,chunk); y-=6.8

# Machine-readable manifest reproduced as legible text lines.
start_page('Appendice C - Manifeste, versions et empreintes')
pipe_hash=hashlib.sha256(PIPE.read_bytes()).hexdigest() if PIPE.exists() else 'missing'
manifest['pipeline_source']={'path':str(PIPE.resolve()),'bytes':PIPE.stat().st_size if PIPE.exists() else None,'sha256':pipe_hash}
for name in ['analyze_pdac_prism_multicontrol.py','build_prism_audit_pdf.py','regenerate_krasscore_selected_plot.py','AUDIT_PRISM_PDACS_v1.md','krasscore_selected_drug_response.png']:
    fp=OUT/name
    if fp.exists(): manifest['outputs'][name]={'bytes':fp.stat().st_size,'sha256':hashlib.sha256(fp.read_bytes()).hexdigest()}
for ln in json.dumps(manifest,indent=2,ensure_ascii=False).splitlines():
    for chunk in textwrap.wrap(dash(ln),width=220,replace_whitespace=False,drop_whitespace=False,break_long_words=True,break_on_hyphens=False) or ['']:
        if y-8<BOTTOM: start_page('Appendice C - Manifeste, versions et empreintes - suite')
        c.setFillColor(INK); c.setFont(MONO,5.4); c.drawString(L,y,chunk); y-=7

if page_open: footer()
c.save()
# Persist versioned hashes and PDF digest sidecar; the manifest is kept outside the PDF to avoid circular hashing.
MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
h=hashlib.sha256(PDF.read_bytes()).hexdigest()
(OUT/'AUDIT_PRISM_PDACS_v1_COMPLET.pdf.sha256').write_text(f'{h}  {PDF.name}\n',encoding='utf-8')
print(json.dumps({'pdf':str(PDF.resolve()),'bytes':PDF.stat().st_size,'pages':page_num,'rows_in_appendix':idx,'pipeline_sha256':pipe_hash,'sha256':h},ensure_ascii=False))

