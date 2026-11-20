import json
from pathlib import Path
p=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/GSE271300_H5AD_METADATA_AUDIT.json')
r=json.loads(p.read_text(encoding='utf-8'))
for f in r['files']:
 print('\n###',f['file'],f['X'])
 for k,v in f.get('obs',{}).get('columns',{}).items():
  if any(t in k.lower() for t in ['class','hypoth','treat','cellstate','score','cluster','gmm','zsig','ora','mrtx','b025','ans','hto']):
   print(k, 'n=',v.get('n'),'unique=',v.get('n_unique'),'top=',v.get('top_counts',[])[:12])
