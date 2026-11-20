import csv
p='pancréas/ANALYSE_THERAPEUTIQUE_2026-11-19/results_mouse_level/GSE271300_mouse_level_summaries.csv'
rows=list(csv.DictReader(open(p,encoding='utf-8-sig')))
for model in ['PC69','PC106']:
 a=[r for r in rows if r['model']==model]
 v=[float(r['basal_fraction']) for r in a if r['treatment']=='veh']
 m=[float(r['basal_fraction']) for r in a if r['treatment']=='mrtx']
 print(model,'means vehicle',sum(v)/len(v),'mrtx',sum(m)/len(m),'relative reduction',(1-(sum(m)/len(m))/(sum(v)/len(v)))*100)
