import json
from pathlib import Path
p=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/results_mouse_level')
r=json.loads((p/'GSE271300_ANALYSIS_REPORT.json').read_text(encoding='utf8'))
print('scope:',r['scope'])
print('source_relationship:',r['source_relationship'])
print('env:',r['environment'])
print('primary:')
for k,v in r['key_primary_results'].items():
 if v: print(k, v.get('n_mrtx'), v.get('n_vehicle'), v.get('difference_mrtx_minus_veh'), v.get('p_exact_two_sided'))
print('outputs',len(r['outputs']))
print('files',[(x.name,x.stat().st_size) for x in p.iterdir() if x.is_file()])
