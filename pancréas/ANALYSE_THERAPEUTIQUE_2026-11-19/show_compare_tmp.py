import json
p='pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/pipeline_runs_balanced15/comparison_all_vs_single_Treatment_code.json'
r=json.load(open(p,encoding='utf8'))
for f in r['files']:
 if f.get('first_differences'):
  print('\n',f['file'])
  for d in f['first_differences'][:20]: print(d)
