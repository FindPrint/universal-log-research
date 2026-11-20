import csv
from pathlib import Path
p=Path('pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/results_mouse_level')
for fn in ['GSE271300_exact_mouse_permutation_contrasts.csv','GSE271300_HTO_ratio_ge_2_sensitivity_contrasts.csv']:
 print('\n',fn)
 with (p/fn).open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   if r['outcome'] in ['basal_fraction','mean_scBasalScore','mean_scClassicalScore','mean_S_score','mean_G2M_score']:
    print(r['analysis'],r['model'],r['outcome'],'diff',r['difference_mrtx_minus_veh'],'d',r['cohens_d_mice'],'p',r['p_exact_two_sided'],'n',r['n_mrtx'],r['n_vehicle'])
