# Profil de performance UNIVERSAL_LOG — 2026-11-15

Ce dossier contient le profil cProfile, les traces de lancement, les comparaisons de sorties et deux copies de travail expérimentales. La version de référence `UNIVERSAL_LOG_v5.9.2.py` n'a pas été modifiée.

## Résumé factuel

- L'entrée de profilage est une trajectoire **simulée** Ising classique de 80 lignes et 15 colonnes, `L16_T2.269185_chain0_first80.csv` (SHA-256 `b76a2ef1ddc50855baa8959714744e0764304bbe9408c6842c5596530ad9c216`). Ce n'est pas une mesure expérimentale réelle.
- Une exécution de référence a réussi en 441,265 s. Une répétition a été interrompue à 49,472 s; elle n'est pas une observation de durée complète. Le run cProfile a réussi en 817,810 s, mais son temps est instrumenté et ne se compare pas directement au temps normal.
- Les plus gros coûts cumulés observés incluent `apply_complexity` (414,6 s), `_compute_extra_estimators` (368,6 s), `level_target_universal` (152,3 s), l'ensemble des rendus `savefig` (environ 152,3 s), `local_pca_dimension` (66,0 s), le diagnostic de bruit (61,0 s), et le calcul de redondance (57,9 s). Les temps cumulés cProfile se recouvrent et ne s'additionnent pas.
- La candidate v5.9.3 réduit fortement le temps d'un microbenchmark isolé de division scalaire, mais n'a pas démontré de gain de bout en bout sur un run unique (482,658 s contre 441,265 s). Ne pas la considérer comme une optimisation confirmée.
- La candidate v5.9.4 ajoute `--no-plots`. Elle a produit les mêmes exports numériques sélectionnés et le même TLog que la référence, et zéro PNG au lieu des 14 PNG de la référence. Son temps mesuré (776,502 s) est supérieur à celui de l'unique référence complète; aucune accélération n'est démontrée.
- La configuration `--horizons 1,3,6,12` a conservé les mêmes exports numériques/TLog et a terminé en 430,380 s, mais un écart de 2,5 % sur un seul run ne prouve pas de gain. Elle retire des résultats dépendant des horizons exclus.
- Les essais de 8 000 et 1 024 lignes n'ont pas achevé le pipeline; ils ne fournissent aucun résultat de durée complète. Aucun benchmark de performance sur un jeu empirique réel ou autre domaine n'est inclus ici.

Les observations, les limites et les recommandations sont consignées dans [PROFILE_FINDINGS_2026-11-15.md](PROFILE_FINDINGS_2026-11-15.md). Les procédures et journaux individuels figurent dans `sample_80/`, `sample_1024/` et `baseline_run_01/`.

## Reproduction

Depuis la racine du projet, avec le `.venv` du projet :

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_80\run_no_plots_v5_9_4.ps1
```

Les autres scripts enregistrent les essais de référence, l'exécution cProfile, le test à quatre horizons et la candidate v5.9.3. Consultez chaque `run_record.json` avant d'interpréter une durée : les exécutions interrompues y sont marquées par un code de sortie non nul.

## Limite de portée

Ce profil identifie des coûts logiciels sur un petit cas simulé et une configuration précise. Il ne valide ni l'universalité scientifique de TLog, ni le pipeline sur des observations empiriques, ni ses performances sur d'autres domaines ou tailles représentatives.
