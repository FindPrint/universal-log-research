import h5py,numpy as np
from pathlib import Path
b=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/data_GSE271300')
panel=['KRAS','EGFR','ERBB2','ERBB3','STAT3','GATA6','KRT19','CEACAM5','KRT5','TP63']
for model in ['PC69','PC106','GA60']:
 with h5py.File(b/f'GSE271300_PDX_{model}_analyzed.h5ad','r') as f:
  g={bytes(v).decode() if isinstance(v,(bytes,np.bytes_)) else str(v) for v in f['var']['_index'][:]}
  print(model,[x for x in panel if x in g])
