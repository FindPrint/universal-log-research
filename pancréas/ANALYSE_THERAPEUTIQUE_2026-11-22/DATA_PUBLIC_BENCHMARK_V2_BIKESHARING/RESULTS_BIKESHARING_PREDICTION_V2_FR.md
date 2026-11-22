# Bike Sharing — benchmark prédictif V2

**Amendement exploratoire postérieur à V1 :** le témoin `weekday × hr` a été ajouté après inspection V1, car la moyenne globale ignore la périodicité connue du jeu. V1 est conservée dans `prediction_benchmark_v1/`; les résultats ci-dessous sont dans `prediction_benchmark_v2/`. Aucun paramètre de modèle n’a été choisi en fonction des cibles de test.

**Source :** `hour.csv`, UCI Bike Sharing, 17 379 lignes, SHA-256 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`. Les deux tests contiennent 4 345 enregistrements chacun; un audit postérieur constate 165 créneaux horaires sans ligne sur l'intervalle complet. Les causes ne sont pas données par le Readme et aucune valeur n'a été imputée. La cible est `cnt`; les prédicteurs restent calendrier + météo mesurée. `instant`, `casual` et `registered` sont exclus; l’identité `casual + registered = cnt` est vérifiée avant calcul.

## Mesures par bloc chronologique

| Bloc | Modèle | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| 50–75 % | Moyenne d’apprentissage | 154,908 | 208,812 | -0,138 |
| 50–75 % | Moyenne entraînée par `weekday × hr` | 92,136 | 138,013 | 0,503 |
| 50–75 % | Ridge standardisée | 120,072 | 176,761 | 0,185 |
| 50–75 % | Forêt aléatoire | 84,564 | 121,549 | 0,614 |
| 50–75 % | HistGradientBoosting | 79,696 | 114,557 | 0,658 |
| 75–100 % | Moyenne d’apprentissage | 177,635 | 236,507 | -0,156 |
| 75–100 % | Moyenne entraînée par `weekday × hr` | 107,718 | 151,501 | 0,526 |
| 75–100 % | Ridge standardisée | 143,120 | 183,509 | 0,304 |
| 75–100 % | Forêt aléatoire | 46,669 | 71,424 | 0,895 |
| 75–100 % | HistGradientBoosting | 44,539 | 67,008 | 0,907 |

## Ce qui est observé et ce qui ne l’est pas

**Observation dans ces plis seulement :** les modèles d’arbres font mieux que le témoin calendaire `weekday × hr` sur les MAE et RMSE rapportées; l’écart est plus marqué sur le dernier bloc. Le témoin calendaire lui-même fait bien mieux que la moyenne globale. Cela montre que la périodicité est un comparateur important et que la référence globale seule était insuffisante.

**Limites :** l’amendement est postérieur à V1; il demeure exploratoire. Deux blocs d’un seul jeu historique ne fournissent ni intervalle d’incertitude ni validation sur d’autres villes/périodes. La météo du même instant est mesurée après l’événement; les résultats décrivent une estimation conditionnelle rétrospective et ne prouvent pas une prévision disponible à l’avance. L’analyse n’évalue aucun T0/TLog ni aucune capacité prédictive du pipeline.

Dans cette V2, les variables codées (`weekday`, `hr`, `season`, `weathersit`, etc.) étaient encore fournies aux modèles comme valeurs numériques. Le protocole V3, ajouté ensuite pour contrôler ce choix de représentation, utilise un encodage one-hot explicite; V2 reste conservée et n’est pas présentée comme comparaison finale de référence.

La source ne documente ni les modèles d'instrument météo, ni leur étalonnage, ni l'incertitude instrumentale. Les plis découpent des lignes ordonnées et non des durées garanties sans lacune. La sensibilité des scores à ces lacunes ou à la chaîne de mesure n'a pas été isolée.
