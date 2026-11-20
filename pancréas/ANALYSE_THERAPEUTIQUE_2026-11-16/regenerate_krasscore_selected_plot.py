import csv, hashlib, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
root=Path(r'''pancréas\Archive complète PDAC v6 — ZIP\pdac-v6-archive-complete-2026-11-15\03_runs-pdac-v6-2026-11-15\data''')
out=Path(r'''pancréas\ANALYSE_THERAPEUTIQUE_2026-11-16''')
model=pd.read_csv(root/'Model.csv',usecols=['ModelID','OncotreePrimaryDisease'])
ids=set(model.loc[model.OncotreePrimaryDisease.eq('Pancreatic Adenocarcinoma'),'ModelID'].astype(str))
mat=pd.read_csv(root/'Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv',index_col=0,low_memory=False)
with open(root/'CRISPRGeneEffect.csv',encoding='utf-8-sig',newline='') as f: hdr=next(csv.reader(f))
first=hdr[0] if hdr[0] else 'Unnamed: 0'; kc=next(c for c in hdr if c.startswith('KRAS ('))
ge=pd.read_csv(root/'CRISPRGeneEffect.csv',usecols=[first,kc],low_memory=False).rename(columns={first:'ModelID'}).set_index('ModelID')
ge.index=ge.index.astype(str)
ids=sorted(ids & set(mat.columns.astype(str)) & set(ge.index))
dep=-pd.to_numeric(ge.loc[ids,kc],errors='coerce')
comp=pd.read_csv(root/'Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv')
names=['AS-77','MRTX1133','GEMCITABINE','PACLITAXEL']
fig,axes=plt.subplots(1,len(names),figsize=(19,4.8),sharex=True)
for ax,name in zip(axes,names):
    rows=comp[comp['Drug.Name'].fillna('').str.upper().str.contains(name,regex=False)]
    if rows.empty:
        ax.text(.5,.5,'not present',ha='center',va='center'); ax.set_title(name); continue
    cid=rows.iloc[0]['IDs']; y=pd.to_numeric(mat.loc[cid,ids],errors='coerce')
    d=pd.concat([dep.rename('dependency'),y.rename('LFC')],axis=1).dropna()
    r=spearmanr(d.dependency,d.LFC)
    ax.scatter(d.dependency,d.LFC,s=27,alpha=.82,color='#2d6a9f',edgecolor='white',linewidth=.35)
    ax.axhline(0,color='gray',lw=.8,ls=':'); ax.grid(alpha=.15)
    qrow=pd.read_csv(out/'pdac_prism_KRAS_corrected_all_compounds.csv')
    res=qrow.loc[qrow.compound_id.eq(cid)].iloc[0]
    ax.set_title(f'{name}\nρ={r.statistic:.2f}; q={res.q_BH_within_control_all_screens:.3g}; n={len(d)}',fontsize=10)
    ax.set_xlabel('KRAS dependency = −Chronos\n(higher = stronger dependency)')
axes[0].set_ylabel('PRISM log2 fold change (lower = lower viability)')
fig.suptitle('PRISM 24Q2: KRAS dependency vs drug response\nexploratory, cross-sectional PDAC models',fontsize=12)
fig.tight_layout(); fig.savefig(out/'krasscore_selected_drug_response.png',dpi=180,bbox_inches='tight'); plt.close(fig)
mp=out/'analysis_manifest.json'; m=json.loads(mp.read_text(encoding='utf-8'))
for name in ['krasscore_selected_drug_response.png','analyze_pdac_prism_multicontrol.py','AUDIT_PRISM_PDACS_v1.md']:
 p=out/name; m['outputs'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
mp.write_text(json.dumps(m,indent=2,ensure_ascii=False),encoding='utf-8')
print('updated plot AS77/MRTX/gemcitabine/paclitaxel; n',len(ids))
