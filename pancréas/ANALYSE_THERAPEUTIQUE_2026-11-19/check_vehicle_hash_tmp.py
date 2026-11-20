from pathlib import Path
import h5py,numpy as np
base=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/data_GSE271300')
def txt(x): return bytes(x).decode() if isinstance(x,(bytes,np.bytes_)) else str(x)
def arr(g,k):
 o=g[k]
 if isinstance(o,h5py.Group):
  codes=np.asarray(o['codes']); cats=[txt(v) for v in o['categories']]
  return np.array([cats[i] if i>=0 else '' for i in codes],object)
 return np.array([txt(v) for v in np.asarray(o)],object)
for model in ['PC69','PC106']:
 q=base/f'GSE271300_PDX_{model}_QC.h5ad'; a=base/f'GSE271300_PDX_{model}_analyzed.h5ad'
 with h5py.File(q,'r') as fq, h5py.File(a,'r') as fa:
  qi=arr(fq['obs'],'_index'); ai=arr(fa['obs'],'_index'); qidx={s:i for i,s in enumerate(qi)}
  ix=np.array([qidx[s] for s in ai]); treatment=arr(fa['obs'],'treatment'); print('\n',model,'analysis rows',len(ai),'overlap',len(ix))
  tagcols=[k for k in fq['obs'].keys() if 'VEH' in k.upper() or 'VEHICLE' in k.upper()]
  if not tagcols: tagcols=[k for k in fq['obs'].keys() if 'B025' in k]
  names=[k for k in tagcols if k in fq['obs']]
  print('tags',names)
  mat=np.column_stack([np.asarray(arr(fq['obs'],k),float)[ix] for k in names])
  for tr in np.unique(treatment):
   sel=(treatment==tr)&np.all(np.isfinite(mat),axis=1)
   if not np.any(sel): continue
   v=mat[sel]; order=np.argsort(v,axis=1); maxv=v[np.arange(len(v)),order[:,-1]]; sec=v[np.arange(len(v)),order[:,-2]]
   winner=order[:,-1]; print(tr,'n',len(v),'argmax',dict(zip(*np.unique(winner,return_counts=True))),'max>=2xsecond',int(np.sum(maxv>=2*np.maximum(1,sec))),'median top',np.median(maxv),'med ratio',np.median(maxv/(sec+1)))
   print('example top rows',[(names[winner[i]],v[i].round(1).tolist()) for i in np.linspace(0,len(v)-1,min(8,len(v)),dtype=int)])
