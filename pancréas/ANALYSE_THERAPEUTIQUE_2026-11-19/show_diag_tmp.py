import json
p='pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/results_mouse_level/GSE271300_ANALYSIS_REPORT.json'
r=json.load(open(p,encoding='utf8'))
for d in r['diagnostics']:
 if d['model']=='PC106': print(json.dumps(d,indent=2))
