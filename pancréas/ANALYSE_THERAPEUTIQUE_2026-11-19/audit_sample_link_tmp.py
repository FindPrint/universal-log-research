from __future__ import annotations
import h5py, numpy as np, json
from pathlib import Path
ROOT=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/data_GSE271300')
def dec(x):
 if isinstance(x,(bytes,np.bytes_)): return bytes(x).decode('utf8','replace')
 return str(x)
def col(g,key):
 o=g[key]
 if isinstance(o,h5py.Group) and 'codes' in o:
  c=np.asarray(o['codes']); cats=[dec(x) for x in o['categories']]
  return np.array([cats[i] if i>=0 else '' for i in c],dtype=object)
 return np.array([dec(x) for x in np.asarray(o)],dtype=object)
def report(prefix):
 p=ROOT/f'GSE271300_PDX_PC106_{prefix}.h5ad'
 with h5py.File(p,'r') as f:
  obs=f['obs']; idx=col(obs,'_index') if '_index' in obs else None
  print('\n',prefix,'n',len(idx) if idx is not None else None,'first',idx[:5] if idx is not None else None,'last',idx[-5:] if idx is not None else None)
  print('obs keys',list(obs.keys()))
  for k in ['treatment','Classification','GMM','PC106-ANS184-VEH-B0252','PC106-ANS185-VEH-B0253','PC106-ANS187-VEH-B0254','PC106-ANS188-MRTX1-B0255','cellState']:
   if k in obs:
    v=col(obs,k); print(k,'head',v[:3],'counts',dict(zip(*np.unique(v,return_counts=True))))
for p in ['analyzed','QC']: report(p)
with h5py.File(ROOT/'GSE271300_PDX_PC106_analyzed.h5ad','r') as a, h5py.File(ROOT/'GSE271300_PDX_PC106_QC.h5ad','r') as q:
 ai=col(a['obs'],'_index'); qi=col(q['obs'],'_index'); print('\nINDEX OVERLAP',len(set(ai)&set(qi)),'of',len(ai),'analysis; qc',len(qi),'exact unique',len(set(ai))==len(ai),len(set(qi))==len(qi))
 mapq={v:i for i,v in enumerate(qi)}
 print('First aligned',[(s,mapq.get(s)) for s in ai[:10]])
 if len(set(ai)&set(qi)):
  al=col(a['obs'],'treatment'); ac=col(a['obs'],'Classification'); qt=col(q['obs'],'treatment'); qc=col(q['obs'],'Classification')
  tags=[k for k in q['obs'] if k.endswith(('B0252','B0253','B0254','B0255','B0256','B0257','B0258'))]
  for tag in tags:
   xv=col(q['obs'],tag)
   rows=[i for i,s in enumerate(ai) if s in mapq]
   ix=np.array([mapq[ai[i]] for i in rows]); vals=xv[ix]
   print('joined tag',tag,'nonnull aligned',np.sum(vals!='nan'),'nonzero',np.sum((vals!='nan')&(vals!='0.0')),'n',len(vals),'treatment counts',dict(zip(*np.unique(al[rows],return_counts=True))))
