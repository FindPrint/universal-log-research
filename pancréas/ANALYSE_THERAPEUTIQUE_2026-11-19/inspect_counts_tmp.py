import h5py,numpy as np
from pathlib import Path
base=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/data_GSE271300')
for model in ['PC69','PC106','GA60']:
 p=base/f'GSE271300_PDX_{model}_QC.h5ad'
 with h5py.File(p,'r') as f:
  print('\n',model,'root',list(f.keys()))
  x=f['X']; print('X shape',x.attrs.get('shape'),'keys',list(x.keys()))
  d=x['data']; print('dtype',d.dtype,'stored',len(d),'min max sample',float(np.min(d[:1000000])),float(np.max(d[:1000000])),d[:20])
  var=f['var']; print('var keys',list(var.keys()))
  for k in var.keys():
   if k in ['_index','gene_symbols','feature_name','feature_types','genome']:
    v=var[k]
    if isinstance(v,h5py.Dataset):
     vals=[(bytes(x).decode() if isinstance(x,(bytes,np.bytes_)) else str(x)) for x in v[:5]]
     print(k,'sample',vals,'n',len(v))
  idx=var['_index'][:]; genes={bytes(v).decode() if isinstance(v,(bytes,np.bytes_)) else str(v) for v in idx}
  print('targets', {g:(g in genes) for g in ['EGFR','ERBB2','ERBB3','STAT3','KRAS','CEACAM5','KRT19','GATA6','TP63','KRT5']})
  print('uns keys',list(f['uns'].keys())[:30] if 'uns' in f else None,'layers',list(f['layers'].keys()) if 'layers' in f else None)
