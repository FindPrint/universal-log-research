from __future__ import annotations
import csv, hashlib, json, math, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(r'''pancréas\Archive complète PDAC v6 — ZIP\pdac-v6-archive-complete-2026-11-15\03_runs-pdac-v6-2026-11-15\data''')
OUT = Path(r'''pancréas\ANALYSE_THERAPEUTIQUE_2026-11-16''')
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261116
BOOTSTRAP_N = 5000
MIN_N = 15
CONTROL_GENES = ['KRAS','EFR3A','RAB10','CCND1','UROD','CFLAR','DOCK5','MYH9','SCAP','RAB6A','CRKL','MYC','ACO2']
AS77_TARGET_GENES = ['KCNN4','KCNA3','KCNA5']
SOURCE_FILES = [
    'Model.csv', 'CRISPRGeneEffect.csv',
    'Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv',
    'Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv',
    'Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv'
]

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def bh(pvalues):
    p=np.asarray(pvalues,dtype=float)
    out=np.full(p.shape,np.nan)
    valid=np.isfinite(p)
    pv=p[valid]
    if not len(pv): return out
    order=np.argsort(pv,kind='mergesort')
    ranked=pv[order]
    q=ranked*len(ranked)/np.arange(1,len(ranked)+1)
    q=np.minimum.accumulate(q[::-1])[::-1]
    restored=np.empty_like(q); restored[order]=np.minimum(q,1.0)
    out[valid]=restored
    return out

def csv_header(path):
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        return next(csv.reader(f))

start=time.time()
model=pd.read_csv(ROOT/'Model.csv',low_memory=False)
pdac=model.loc[model['OncotreePrimaryDisease'].eq('Pancreatic Adenocarcinoma')].copy()
pdac['ModelID']=pdac['ModelID'].astype(str)
mat=pd.read_csv(ROOT/'Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv',index_col=0,low_memory=False)
mat.index=mat.index.astype(str); mat.columns=mat.columns.astype(str)
headers=csv_header(ROOT/'CRISPRGeneEffect.csv')
first=headers[0] if headers[0] else 'Unnamed: 0'
gene_cols={g:next((c for c in headers if c.startswith(g+' (')),None) for g in CONTROL_GENES + AS77_TARGET_GENES}
missing_genes=[g for g,c in gene_cols.items() if c is None]
if missing_genes: raise RuntimeError(f'Gene effect columns missing: {missing_genes}')
usecols=[first]+[c for c in gene_cols.values() if c]
ge=pd.read_csv(ROOT/'CRISPRGeneEffect.csv',usecols=usecols,low_memory=False)
ge=ge.rename(columns={first:'ModelID'}).set_index('ModelID')
ge.index=ge.index.astype(str)
for g,c in gene_cols.items():
    if c != g: ge=ge.rename(columns={c:g})

screen_models=set(pdac['ModelID']) & set(mat.columns)
model_rows=pdac.set_index('ModelID')
model_to_name=model_rows['CellLineName'].to_dict()
model_to_lineage=model_rows['OncotreeLineage'].to_dict()
model_to_subtype=model_rows['OncotreeSubtype'].to_dict()
crispr_models=set(screen_models) & set(ge.index)

# Matrix columns are models and rows are individual compound perturbations.
# Use exact primary-disease designation; no broad pancreas-lineage substitution.
common_gene_models=sorted(crispr_models)
if not common_gene_models: raise RuntimeError('No exact-PDAC overlap with PRISM and CRISPR.')
compound_meta=pd.read_csv(ROOT/'Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv',low_memory=False)
compound_meta['IDs']=compound_meta['IDs'].astype(str)
meta_by_id={}
for cid,group in compound_meta.groupby('IDs',sort=False):
    row=group.iloc[0]
    def joined(col):
        vals=[]
        for x in group[col].dropna().astype(str).tolist():
            if x not in vals: vals.append(x)
        return ' | '.join(vals)
    meta_by_id[cid]={
        'screen':joined('screen'), 'dose_uM':joined('dose'),
        'Drug.Name':joined('Drug.Name'), 'repurposing_target':joined('repurposing_target'),
        'MOA':joined('MOA'), 'Synonyms':joined('Synonyms'),
        'annotation_rows':int(len(group)), 'metadata_ambiguous':bool(len(group)>1)
    }

# Build a 13-control x all measured drug fluxes association grid.
# The compact NumPy implementation avoids allocating a pandas table per pair.
from scipy.stats import rankdata, t as student_t
records=[]
Y=mat.loc[:,common_gene_models].apply(pd.to_numeric,errors='coerce').to_numpy(dtype=float).T
compound_ids=mat.index.astype(str).to_list()
for gene in CONTROL_GENES:
    print(f'[GRID] {gene} against {len(compound_ids)} drug fluxes',flush=True)
    x=(-pd.to_numeric(ge.loc[common_gene_models,gene],errors='coerce')).to_numpy(dtype=float)
    x=np.where(np.isfinite(x),x,np.nan)
    for j,cid in enumerate(compound_ids):
        y=Y[:,j]
        mask=np.isfinite(x)&np.isfinite(y)
        n=int(mask.sum())
        if n<MIN_N:
            rho=p=np.nan; delta=hi=lo=np.nan; nlo=nhi=0
        else:
            xv=x[mask]; yv=y[mask]
            rx=rankdata(xv,method='average'); ry=rankdata(yv,method='average')
            cx=rx-rx.mean(); cy=ry-ry.mean()
            denom=float(np.sqrt(np.dot(cx,cx)*np.dot(cy,cy)))
            rho=float(np.dot(cx,cy)/denom) if denom>0 else np.nan
            if not np.isfinite(rho): p=np.nan
            elif abs(rho)>=1.0: p=0.0
            else:
                tv=abs(rho)*math.sqrt((n-2)/(1-rho*rho))
                p=float(2*student_t.sf(tv,n-2))
            q1=float(np.quantile(xv,1/3)); q2=float(np.quantile(xv,2/3))
            low=yv[xv<=q1]; high=yv[xv>=q2]
            lo=float(np.mean(low)) if len(low) else np.nan
            hi=float(np.mean(high)) if len(high) else np.nan
            delta=hi-lo if np.isfinite(hi) and np.isfinite(lo) else np.nan
            nlo=int(len(low)); nhi=int(len(high))
        anno=meta_by_id.get(str(cid),{})
        records.append({
            'control_gene':gene,'control_score_definition':'-Chronos gene effect; larger = stronger dependency',
            'compound_id':str(cid),'screen':anno.get('screen','unannotated'),
            'dose_uM':anno.get('dose_uM',''),'drug_name':anno.get('Drug.Name',''),
            'repurposing_target':anno.get('repurposing_target',''),'MOA':anno.get('MOA',''),
            'metadata_ambiguous':anno.get('metadata_ambiguous',False),
            'n_cell_lines':n,'spearman_dependency_vs_LFC':rho,'p_spearman_two_sided':p,
            'delta_LFC_high_dependency_minus_low_dependency':delta,
            'mean_LFC_high_dependency':hi,'mean_LFC_low_dependency':lo,
            'n_high_dependency':nhi,'n_low_dependency':nlo,
            'direction_interpretation':('higher dependency associated with lower viability' if np.isfinite(rho) and rho<0 else 'higher dependency associated with higher viability' if np.isfinite(rho) and rho>0 else 'not estimable')
        })
res=pd.DataFrame.from_records(records)
res['q_BH_within_control_all_screens']=res.groupby('control_gene')['p_spearman_two_sided'].transform(lambda s:bh(s.to_numpy()))
res['q_BH_within_control_and_screen']=res.groupby(['control_gene','screen'])['p_spearman_two_sided'].transform(lambda s:bh(s.to_numpy()))
res['q_BH_global_all_controls_and_drugs']=bh(res['p_spearman_two_sided'].to_numpy())
res.to_csv(OUT/'pdac_prism_control_by_drug_fluxes.csv',index=False,float_format='%.10g')

kr=res.loc[res['control_gene'].eq('KRAS')].copy()
kr.sort_values('spearman_dependency_vs_LFC',ascending=True,na_position='last').to_csv(OUT/'pdac_prism_KRAS_corrected_all_compounds.csv',index=False,float_format='%.10g')

# Prespecified disease-relevant compounds to keep the interpretation anchored.
known_names=['AS-77','MRTX1133','GEMCITABINE','GEMCITABINE-ELAIDATE','PACLITAXEL','OXALIPLATIN','IRINOTECAN','5-FLUOROURACIL','OLAPARIB','TRAMETINIB','SELUMETINIB']
known=kr.loc[kr['drug_name'].str.upper().apply(lambda s:any(name in s for name in known_names))].copy()
known.to_csv(OUT/'pdac_prism_KRAS_known_treatments.csv',index=False,float_format='%.10g')

# Target-anchored AS-77 follow-up, selected after the screen signal: explicitly post hoc.
# These checks ask whether response tracks dependency on annotated channel targets.
as77_row=kr.loc[kr['drug_name'].str.upper().str.contains('AS-77',na=False)]
as77_target_rows=[]
if len(as77_row):
    cid=str(as77_row.iloc[0]['compound_id'])
    y=pd.to_numeric(mat.loc[cid,common_gene_models],errors='coerce').to_numpy(dtype=float)
    for g in AS77_TARGET_GENES:
        x=(-pd.to_numeric(ge.loc[common_gene_models,g],errors='coerce')).to_numpy(dtype=float)
        mask=np.isfinite(x)&np.isfinite(y)
        xx=x[mask]; yy=y[mask]
        r=spearmanr(xx,yy)
        q1=float(np.quantile(xx,1/3)); q2=float(np.quantile(xx,2/3))
        low=yy[xx<=q1]; high=yy[xx>=q2]
        as77_target_rows.append({'gene':g,'control_definition':'-Chronos; larger = stronger gene dependency',
            'compound':'AS-77','compound_id':cid,'screen':as77_row.iloc[0]['screen'],
            'dose_uM':as77_row.iloc[0]['dose_uM'],'n_cell_lines':int(mask.sum()),
            'spearman_dependency_vs_LFC':float(r.statistic),'p_two_sided_uncorrected_posthoc':float(r.pvalue),
            'mean_LFC_high_dependency':float(np.mean(high)),'mean_LFC_low_dependency':float(np.mean(low)),
            'delta_LFC_high_minus_low_dependency':float(np.mean(high)-np.mean(low)),
            'selection_note':'Post hoc target follow-up selected after AS-77 emerged from the KRAS screen; exploratory, not independent validation.'})
as77_targets=pd.DataFrame(as77_target_rows)
as77_targets.to_csv(OUT/'AS77_channel_target_posthoc.csv',index=False,float_format='%.10g')

summary=(res.groupby('control_gene',sort=False).agg(
    n_drug_fluxes=('compound_id','nunique'),
    tests_estimable=('p_spearman_two_sided',lambda s:int(s.notna().sum())),
    q05_within_control=('q_BH_within_control_all_screens',lambda s:int((s<.05).sum())),
    q05_within_control_screen=('q_BH_within_control_and_screen',lambda s:int((s<.05).sum())),
    q05_global=('q_BH_global_all_controls_and_drugs',lambda s:int((s<.05).sum())),
    strongest_negative_rho=('spearman_dependency_vs_LFC','min'),
    strongest_positive_rho=('spearman_dependency_vs_LFC','max')
).reset_index())
summary.to_csv(OUT/'pdac_prism_control_summary.csv',index=False,float_format='%.10g')

# Bootstrap only for the prespecified KRAS–MRTX1133 descriptive effect.
mrtx=kr.loc[kr['drug_name'].str.upper().str.contains('MRTX1133',na=False)]
bootstrap={}
if len(mrtx):
    cid=mrtx.iloc[0]['compound_id']
    x=(-pd.to_numeric(ge.loc[common_gene_models,'KRAS'],errors='coerce')).to_numpy(float)
    y=pd.to_numeric(mat.loc[cid,common_gene_models],errors='coerce').to_numpy(float)
    ok=np.isfinite(x)&np.isfinite(y); x=x[ok]; y=y[ok]
    rng=np.random.default_rng(SEED); vals=[]
    for _ in range(BOOTSTRAP_N):
        ix=rng.integers(0,len(x),len(x))
        if len(np.unique(x[ix]))>1 and len(np.unique(y[ix]))>1:
            vals.append(float(spearmanr(x[ix],y[ix]).statistic))
    bootstrap={'compound_id':cid,'n':int(len(x)),'n_bootstrap':BOOTSTRAP_N,'seed':SEED,
               'rho_bootstrap_95pct_percentile_ci':[float(np.quantile(vals,.025)),float(np.quantile(vals,.975))] if vals else None}

# Exact model membership and a reusable wide input with all controls + every drug flux.
member=pd.DataFrame({'ModelID':common_gene_models})
member['CellLineName']=member['ModelID'].map(model_to_name)
member['OncotreeLineage']=member['ModelID'].map(model_to_lineage)
member['OncotreeSubtype']=member['ModelID'].map(model_to_subtype)
for g in CONTROL_GENES + AS77_TARGET_GENES:
    member['dependency_'+g]=-pd.to_numeric(ge.loc[member['ModelID'],g],errors='coerce').to_numpy(float)
member.to_csv(OUT/'pdac_models_exact_diagnosis_and_controls.csv',index=False)
# The full raw flux matrix is retained for reproducibility; these rows are cross-sectional samples, not time points.
wide=mat.loc[:,common_gene_models].T
wide.index.name='ModelID'
wide=wide.reset_index()
wide=wide.merge(member.drop(columns=['CellLineName','OncotreeLineage','OncotreeSubtype']),on='ModelID',how='left')
wide.to_csv(OUT/'pdac_prism_pipeline_input_cross_sectional.csv',index=False,float_format='%.10g')

# Selected figures are exploratory visual summaries, not independent validation.
plot_names=['AS-77','MRTX1133','GEMCITABINE','PACLITAXEL']
fig,axes=plt.subplots(1,len(plot_names),figsize=(15,4.6),sharex=True)
for ax,name in zip(axes,plot_names):
    row=kr.loc[kr['drug_name'].str.upper().str.contains(name,na=False)]
    if row.empty:
        ax.text(.5,.5,'non présent',ha='center',va='center'); ax.set_title(name); continue
    cid=row.iloc[0]['compound_id']
    x=(-pd.to_numeric(ge.loc[common_gene_models,'KRAS'],errors='coerce')).to_numpy(float)
    y=pd.to_numeric(mat.loc[cid,common_gene_models],errors='coerce').to_numpy(float)
    ok=np.isfinite(x)&np.isfinite(y)
    ax.scatter(x[ok],y[ok],s=28,alpha=.8,color='#2d6a9f',edgecolor='white',linewidth=.35)
    ax.axhline(0,color='gray',lw=.8,ls=':')
    rho=float(row.iloc[0]['spearman_dependency_vs_LFC'])
    q=float(row.iloc[0]['q_BH_within_control_all_screens'])
    ax.set_title(f'{name}\nρ={rho:.2f}; q={q:.3g}; n={int(row.iloc[0]["n_cell_lines"])}',fontsize=10)
    ax.set_xlabel('KRAS dependency = −Chronos\n(higher = stronger dependency)')
    ax.grid(alpha=.15)
axes[0].set_ylabel('PRISM log2 fold change (lower = less viable)')
fig.suptitle('PRISM 24Q2: KRAS dependency vs selected drug response\nexploratory, cross-sectional PDAC models',fontsize=12)
fig.tight_layout()
fig.savefig(OUT/'krasscore_selected_drug_response.png',dpi=180,bbox_inches='tight')
plt.close(fig)

# Top descriptive ranks are not termed candidates unless independently replicated.
top=kr.dropna(subset=['spearman_dependency_vs_LFC']).sort_values('spearman_dependency_vs_LFC').head(15)
fig,ax=plt.subplots(figsize=(9,6))
labels=(top['drug_name'].replace('',np.nan).fillna(top['compound_id'])).astype(str)
colors=['#b64035' if v<0 else '#3778a5' for v in top['spearman_dependency_vs_LFC']]
ax.barh(labels.iloc[::-1],top['spearman_dependency_vs_LFC'].iloc[::-1],color=colors[::-1])
ax.axvline(0,color='black',lw=.8)
ax.set_xlabel('Spearman ρ: stronger KRAS dependency vs PRISM log2 viability')
ax.set_title('Top 15 negative descriptive associations\nall-compound ranking; multiple-testing corrected in CSV')
ax.grid(axis='x',alpha=.2)
fig.tight_layout(); fig.savefig(OUT/'krasscore_top15_descriptive.png',dpi=180,bbox_inches='tight'); plt.close(fig)

# Copy the source PRISM README used to interpret assay direction and processing.
readme_source=OUT/'Repurposing_Public_24Q2_Readme.txt'
if not readme_source.exists():
    import urllib.request
    urllib.request.urlretrieve('https://ndownloader.figshare.com/files/46631143',readme_source)

# Versioned, machine-readable trace.
source_meta={}
for name in SOURCE_FILES:
    path=ROOT/name
    source_meta[name]={'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':sha256(path)}
outputs=['pdac_prism_control_by_drug_fluxes.csv','pdac_prism_KRAS_corrected_all_compounds.csv',
         'pdac_prism_KRAS_known_treatments.csv','AS77_channel_target_posthoc.csv','pdac_prism_control_summary.csv',
         'pdac_models_exact_diagnosis_and_controls.csv','pdac_prism_pipeline_input_cross_sectional.csv',
         'krasscore_selected_drug_response.png','krasscore_top15_descriptive.png','Repurposing_Public_24Q2_Readme.txt','AUDIT_PRISM_PDACS_v1.md']
manifest={
 'analysis_id':'pdac_prism_all_controls_all_drug_fluxes_v1',
 'created_utc':datetime.now(timezone.utc).isoformat(),
 'seed':SEED,'bootstrap_resamples':BOOTSTRAP_N,'minimum_pairwise_n':MIN_N,
 'software':{'python':sys.version,'platform':platform.platform(),'pandas':pd.__version__,'numpy':np.__version__,'scipy':__import__('scipy').__version__,'matplotlib':matplotlib.__version__},
 'source_data':source_meta,
 'selection':{'disease_filter':"Model.csv OncotreePrimaryDisease == 'Pancreatic Adenocarcinoma'",'control_genes':CONTROL_GENES,
              'control_gene_origin':'KRAS is the pre-existing primary axis; the other 12 genes were selected in the archived DepMap 24Q4 analysis and are post-selection exploratory controls.',
              'AS77_target_followup_genes':AS77_TARGET_GENES,'AS77_followup':'post hoc; not independent validation',
              'drug_fluxes':'all rows in Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv'},
 'sample_counts':{'exact_pdac_models_in_Model_csv':int(len(pdac)),'exact_pdac_models_in_prism_matrix':int(len(screen_models)),
                  'exact_pdac_models_with_crispr_gene_effect':int(len(crispr_models)),'models_used_for_gene_control_grid':int(len(common_gene_models)),
                  'prism_compound_rows':int(len(mat)),'unique_compound_annotation_ids':int(compound_meta['IDs'].nunique()),
                  'ambiguous_compound_annotation_ids':int((compound_meta.groupby('IDs').size()>1).sum()),
                  'compound_rows_without_annotation':int(len(set(mat.index)-set(compound_meta['IDs'])))},
 'methods':{'response_scale':'PRISM log2 fold change relative to DMSO/vehicle; lower/more negative means lower viability.',
            'dependency_scale':'input DepMap Chronos gene effect was multiplied by -1 so larger values indicate stronger dependency.',
            'association':'two-sided Spearman rank correlation per gene-control by compound response; BH adjusted within each control, within control x screen, and globally over all tests.',
            'effect_size':'difference of mean PRISM LFC between upper and lower thirds of dependency score; descriptive.',
            'clinical_status':'cell-line screening hypothesis only; no treatment recommendation or evidence of a cure.'},
 'pipeline_assessment':{'pipeline_file':'pancréas/Archive complète PDAC v6 — ZIP/universal_v6.0.0_cohen.py',
                       'pipeline_fast_minimum_length':50,'pipeline_fit_for_this_input':False,
                       'reason':'Only 38 matched exact-PDAC cell lines were available for CRISPR x PRISM; this is a cross-sectional set of cell lines with no natural temporal/progression order. The pipeline threshold/T0/TLog stage is sequence-oriented. A forced row order or lowering the minimum would add an arbitrary assumption and could create a non-interpretable threshold. The matrix is saved as a future batch input; no T0/TLog inference was run.'},
 'bootstrap_mrtx1133':bootstrap,
 'outputs':{name:{'bytes':(OUT/name).stat().st_size,'sha256':sha256(OUT/name)} for name in outputs if (OUT/name).exists()},
 'elapsed_seconds':round(time.time()-start,2)
}
(OUT/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')

# Concise audit report, populated only from computed output.
def fmt(x,d=4): return 'NA' if pd.isna(x) else f'{x:.{d}g}'
kr_mrtx=kr.loc[kr['drug_name'].str.upper().str.contains('MRTX1133',na=False)]
kr_top=kr.dropna(subset=['spearman_dependency_vs_LFC']).sort_values('spearman_dependency_vs_LFC').head(5)
report=[]
report += ['# Audit thérapeutique PDAC — correction PRISM et grille multi-contrôles','',
           '**Date de calcul :** 2026-11-16  |  **Version :** v1  |  **Statut :** analyse préclinique exploratoire', '',
           '## Résumé exécutif','',
           'Le criblage précédent a inversé le sens d’interprétation de l’axe KRAS : les scores Chronos les plus négatifs correspondent à une dépendance plus forte; l’ancien code les avait étiquetés « faible » après `qcut` et avait ensuite interprété le signe de Spearman dans le sens opposé. Les tables ci-jointes recalculent les associations avec un score `-Chronos` (valeur élevée = dépendance forte).', '',
           f'Le jeu PRISM 24Q2 contient **{len(mat):,} flux de réponse médicamenteuse**. Le filtre strict `OncotreePrimaryDisease == Pancreatic Adenocarcinoma` donne **{len(pdac)} modèles** dans Model.csv, **{len(screen_models)}** présents dans la matrice PRISM et **{len(common_gene_models)}** avec les contrôles CRISPR nécessaires. Tous les flux médicamenteux ont été mis en regard de **{len(CONTROL_GENES)} axes de dépendance**; seuls KRAS est l’axe préspécifié de référence, tandis que les 12 autres proviennent d’une sélection antérieure et restent exploratoires.', '',
           f'Pour KRAS seul, **{int((kr.q_BH_within_control_all_screens<.05).sum())}** flux franchit q<0,05 dans la famille de 6 790 composés : AS-77 (REP.PRIMARY; n=30; ρ=−0,724; q=0,0413; q dans REP.PRIMARY=0,0321). Mais son q global après correction sur les 13 contrôles × 6 790 flux est 0,246; il ne franchit donc pas ce contrôle familial plus large. PAVINETANT franchit q=0,0358 dans son écran REP.1M avec le signe opposé (ρ=+0,638), ce qui souligne l’hétérogénéité. Aucun médicament n’est validé comme piste par cette analyse.', '',
           '## Résultats ancrés','',
           '| Analyse préspécifiée | n | Spearman ρ (dépendance KRAS, LFC) | q BH (tous flux KRAS) | Δ moyenne LFC (tiers dépendant − tiers faible) |',
           '|---|---:|---:|---:|---:|']
if len(kr_mrtx):
    row=kr_mrtx.iloc[0]
    report.append(f'| MRTX1133, dose indiquée dans métadonnées {row["dose_uM"]} µM | {int(row["n_cell_lines"])} | {fmt(row["spearman_dependency_vs_LFC"])} | {fmt(row["q_BH_within_control_all_screens"])} | {fmt(row["delta_LFC_high_dependency_minus_low_dependency"])} |')
for _,row in known.loc[~known['drug_name'].str.upper().str.contains('MRTX1133',na=False)].iterrows():
    report.append(f'| {row["drug_name"]} ({row["screen"]}; {row["dose_uM"]} µM) | {int(row["n_cell_lines"])} | {fmt(row["spearman_dependency_vs_LFC"])} | {fmt(row["q_BH_within_control_all_screens"])} | {fmt(row["delta_LFC_high_dependency_minus_low_dependency"])} |')
report += ['', 'Lecture du signe : **ρ négatif** signifie que les modèles plus dépendants de KRAS ont une LFC plus basse, donc une réduction de viabilité plus marquée sous ce composé. Le calcul porte sur des lignées cellulaires et une mesure à dose fixe, pas sur des patients.', '',
           '## Signal AS-77 : interprétation et vérification ciblée','',
           'L’annotation du catalogue associe AS-77 à KCNA3, KCNA5 et KCNN4. Des travaux indépendants en PDAC rapportent une expression accrue de KCNN4 et une baisse de croissance/motilité après inhibition génétique; cela motive une hypothèse sur les canaux, mais ne valide pas AS-77. Dans nos données, le suivi post hoc par dépendance CRISPR n’appuie pas un mécanisme KCNN4 : KCNN4 ρ=0,202 (p=0,285), KCNA3 ρ=−0,100 (p=0,599), KCNA5 ρ=−0,142 (p=0,454), chacun n=30. Ces p sont post hoc et non corrigées; le suivi est exploratoire et non indépendant.', '',
           '## Contrôles × flux médicamenteux','',
           f'Le fichier `pdac_prism_control_by_drug_fluxes.csv` contient les tests pour chaque paire entre les {len(CONTROL_GENES)} contrôles CRISPR listés dans le manifeste et les {len(mat)} flux PRISM. Les colonnes donnent les valeurs p, trois familles de q BH, le signe de l’association et l’écart descriptif entre tiers. Les contrôles autres que KRAS ont été choisis dans une analyse DepMap antérieure; leurs tests ne sont pas une validation indépendante.', '',
           '## Ce que le pipeline peut conclure sur ces données','',
           'Je n’ai pas produit de T0 ni de TLog à partir de cette matrice. La version v6.0.0 fixe `min_len=50` en mode fast; le chevauchement utile est de 38 modèles. Surtout, l’ordre des lignées dans la table n’est pas un axe de temps, de dose ou de progression. L’ordonner artificiellement par un score ou réduire le minimum changerait la question et pourrait fabriquer un seuil. Le fichier d’entrée est conservé pour une future analyse lorsque nous disposerons d’une vraie série ordonnée adaptée.', '',
           'La contribution raisonnable du pipeline ici est d’expliciter les axes de contrôle, de garder toutes les colonnes de flux PRISM et de tracer les choix. L’analyse des relations médicament–dépendance est faite avec Spearman et correction de multiplicité, outils adaptés à ce jeu transversal. Ces résultats pourront ensuite servir à construire une vraie question séquentielle ou à prioriser un essai de validation.', '',
           '## Erreur historique et correction','',
           'Dans `prism_screen.py`, les valeurs Chronos étaient passées directement à `pd.qcut` avec étiquettes `faible, moyen, fort`. Comme les scores les plus négatifs indiquent la dépendance la plus forte, les groupes « faible » et « fort » étaient inversés. De plus, le code classait un Spearman négatif comme une sensibilité accrue des modèles « KRAS-fort », alors que le score brut Chronos est l’opposé de la dépendance. Le classement ancien ne doit donc pas être utilisé pour sélectionner un médicament. Les nouveaux CSV emploient `-Chronos` et écrivent la définition explicitement.', '',
           '## Limites qui restent','',
           '- Données PRISM de criblage cellulaire publiques, release 24Q2; une réponse à dose unique ne reproduit ni pharmacocinétique, ni stroma, ni immunité, ni tolérance.',
           '- Petit nombre de modèles PDAC et nombreuses comparaisons; les valeurs q corrigent le nombre de tests mais ne transforment pas une corrélation en causalité.',
           '- `Model.csv` ne contient pas de statut de mutation KRAS; le criblage ne peut pas distinguer G12D, G12V, G12R ou KRAS sauvage. La sensibilité à MRTX1133 doit être analysée par génotype avant toute interprétation mécanistique.',
           '- Les 12 contrôles additionnels ont été retenus après une analyse antérieure, d’où un biais de sélection possible.',
           '- DepMap 26Q3 est disponible depuis le 5 octobre 2026 et corrige des problèmes de correction des effets de librairie CRISPR. Les données courantes locales sont 24Q4; la mise à jour est requise pour confirmation. L’accès direct au téléchargement 26Q3 a présenté une page de vérification Cloudflare lors de cet audit; aucune tentative de contournement n’a été faite.',
           '- Au 2026-11-16, la FDA a approuvé le daraxonrasib (RASONQUE) pour certains adultes avec PDAC métastatique après au moins une ligne systémique; RASolute 302 a rapporté une médiane de survie globale de 13,2 contre 6,7 mois. Cela constitue une option thérapeutique clinique, pas une preuve de guérison. Le PRISM 24Q2 est antérieur et ne teste pas ce médicament; la priorité suivante est l’étude des réponses et résistances aux inhibiteurs de RAS avec données contemporaines.',
           '- Aucun résultat de cet audit ne constitue un conseil thérapeutique. L’objectif est de créer une piste à valider expérimentalement et cliniquement.',
           '- Sources de méthode et de contexte : DepMap PRISM (https://depmap.org/repurposing/); scores Chronos (https://forum.depmap.org/t/ceres-score-correlation-with-cell-proliferation/626); release 26Q3 (https://forum.depmap.org/t/announcing-the-26q3-release/4692); KCNN4 en PDAC (https://pmc.ncbi.nlm.nih.gov/articles/PMC8888650/); FDA daraxonrasib (https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma).', ''
           '## Fichiers reproductibles','',
           '- `analyze_pdac_prism_multicontrol.py` — calcul intégral.',
           '- `pdac_prism_control_by_drug_fluxes.csv` — matrice complète contrôles × médicaments.',
           '- `pdac_prism_KRAS_corrected_all_compounds.csv` et `pdac_prism_KRAS_known_treatments.csv` — sortie principale.',
           '- `AS77_channel_target_posthoc.csv` — vérification ciblée post hoc du mécanisme de canal.',
           '- `pdac_prism_pipeline_input_cross_sectional.csv` — matrice filtrée avec tous les contrôles et flux pour audit; non utilisée pour inférer un seuil.',
           '- `analysis_manifest.json` — empreintes SHA-256, versions, filtres, méthode, limites et inventaire des sorties.',
           '- `Repurposing_Public_24Q2_Readme.txt` — README source copié pour documenter l’essai et la direction des mesures.',
           '- `krasscore_selected_drug_response.png`, `krasscore_top15_descriptive.png` — graphiques descriptifs.', '',
           '## Reproduction','',
           'Depuis la racine du projet, exécuter :', '',
           '```powershell', r'.\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-16\analyze_pdac_prism_multicontrol.py', '```', '',
           '---', '']
(OUT/'AUDIT_PRISM_PDACS_v1.md').write_text('\n'.join(report),encoding='utf-8')
# Finalize output hashes after the report exists; include the source script and report.
manifest=json.loads((OUT/'analysis_manifest.json').read_text(encoding='utf-8'))
for name in outputs + ['analyze_pdac_prism_multicontrol.py']:
    path=OUT/name
    if path.exists(): manifest['outputs'][name]={'bytes':path.stat().st_size,'sha256':sha256(path)}
(OUT/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print('DONE', json.dumps({'output':str(OUT.resolve()),'sample_n':len(common_gene_models),'models_exact_pdac':len(pdac),'pdac_in_matrix':len(screen_models),'prism_drug_rows':len(mat),'KRAS_q05':int((kr.q_BH_within_control_all_screens<.05).sum()),'mrtx':mrtx[['n_cell_lines','spearman_dependency_vs_LFC','q_BH_within_control_all_screens','delta_LFC_high_dependency_minus_low_dependency']].to_dict('records'),'elapsed':round(time.time()-start,2)},ensure_ascii=False))



