# Erratum de génération du rapport V2

**Date :** 2026-11-22  
**Campagne concernée :** sensibilité synthétique V2, 35 appels v6.0.1

## Défaut observé

Lors de la première génération du rapport, pandas a interprété l’étiquette littérale `null` comme une valeur manquante lors de la relecture des deux tableaux CSV descriptifs. Les cellules « Condition » correspondantes apparaissaient donc vides dans ces tableaux du Markdown.

Les enregistrements de la campagne (`run_state.json`, résultats par appel et `patient_control_summary.csv`) contenaient bien l’étiquette `null`. Le défaut concernait la présentation de deux tableaux du rapport; il n’a pas changé les sorties du pipeline, les résultats par appel, les figures calculées directement depuis les enregistrements JSON, ni les assertions QA.

## Correction appliquée

Le générateur `build_sensitivity_report_v2.py` relit désormais les tableaux avec `keep_default_na=False`, afin de préserver les étiquettes catégorielles `null`. Le rapport et les deux figures ont été régénérés depuis les mêmes résultats gelés. Le générateur ajoute aussi un résumé des temps muraux récupérés dans les journaux déjà produits; cela ne profile pas individuellement les estimateurs. Aucun appel au pipeline n’a été relancé et aucune donnée source n’a été modifiée.

La première version du rapport est conservée sous `logs/AUDIT_RESULTATS_SENSIBILITE_V2_FR_PRE_CORRECTION.md` pour la traçabilité. Elle est supersédée par `AUDIT_RESULTATS_SENSIBILITE_V2_FR.md`.
