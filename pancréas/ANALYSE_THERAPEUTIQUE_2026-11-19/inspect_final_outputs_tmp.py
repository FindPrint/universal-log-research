import csv,json
from pathlib import Path
base=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/results_mouse_level')
for fn in ['GSE271300_classical_state_target_expression_contrasts.csv','GSE271300_GA60_pooled_descriptive.csv']:
 print('\n###',fn)
 with (base/fn).open(encoding='utf-8-sig',newline='') as h:
  for r in csv.DictReader(h):
   if fn.endswith('contrasts.csv'):
    print(r['model'],r['gene'],'diff',r['difference_mrtx_minus_veh'],'p',r['p_exact_two_sided'],'d',r['cohens_d_mice'])
   else: print(r)
print('\nMatrix audits:')
r=json.loads((base/'GSE271300_ANALYSIS_REPORT.json').read_text(encoding='utf8'))
for x in r['candidate_target_expression_matrix_audits']: print(x['model'],x['matrix_dtype'],x['sampled_values_are_integer_counts'],x['raw_counts_layer_present'],x['target_panel_available'])
