# Bike Sharing — résultat prédictif V1 (comparaison initiale)

Cette comparaison initiale utilisait une moyenne d’apprentissage globale, Ridge, forêt aléatoire et HistGradientBoosting. Elle est conservée intégralement dans `prediction_benchmark_v1/` après l’ajout d’un témoin cyclique plus pertinent en V2.

**Source :** UCI Bike Sharing `hour.csv`, 17 379 lignes, SHA-256 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`. Deux blocs chronologiques de test, 4 345 enregistrements chacun (ce ne sont pas nécessairement 4 345 heures sans interruption). Un audit postérieur trouve 165 créneaux horaires sans ligne sur la période couverte; leur cause n'est pas indiquée dans le Readme. Aucune imputation n'a été faite. Variables : calendrier et météo mesurée. `instant`, `casual` et `registered` exclus; `casual + registered = cnt`.

| Bloc de test | Modèle | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| 50–75 % | Moyenne d’apprentissage | 154,908 | 208,812 | -0,138 |
| 50–75 % | Ridge standardisée | 120,072 | 176,761 | 0,185 |
| 50–75 % | Forêt aléatoire | 84,564 | 121,549 | 0,614 |
| 50–75 % | HistGradientBoosting | 79,696 | 114,557 | 0,658 |
| 75–100 % | Moyenne d’apprentissage | 177,635 | 236,507 | -0,156 |
| 75–100 % | Ridge standardisée | 143,120 | 183,509 | 0,304 |
| 75–100 % | Forêt aléatoire | 46,669 | 71,424 | 0,895 |
| 75–100 % | HistGradientBoosting | 44,539 | 67,008 | 0,907 |

Ces résultats V1 ne sont pas comparés à un témoin calendaire. Voir `PROTOCOLE_BENCHMARK_PREDICTION_V2_FR.md` et le rapport V2 pour l’amendement postérieur. Aucune sortie T0/TLog n’est évaluée par ce benchmark; aucune conclusion de prévision future opérationnelle ou de généralisation n’en découle.

**Limite de mesure constatée après V1 :** les covariables météo sont normalisées et la documentation disponible attribue leur provenance à Freemeteo, sans modèle d'instrument ni relevé d'étalonnage. Les deux plis sont des blocs de lignes ordonnées; les intervalles sans enregistrement signifient que leur durée calendaire peut dépasser le nombre de lignes. L'effet de ces lacunes sur les métriques n'a pas été isolé.
