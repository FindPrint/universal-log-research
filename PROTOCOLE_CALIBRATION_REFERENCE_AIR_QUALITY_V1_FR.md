# Protocole V1 — calibration temporelle Air Quality

**Statut :** protocole figé après l’audit des données et avant l’ajustement des modèles. Les effectifs admissibles par fenêtre sont documentés; aucun score de modèle n’a été consulté pour choisir les dates.

## Question et limites de la cible

Estimer les valeurs de `CO(GT)` rapportées par l’analyseur de référence colocalisé à partir des cinq réponses de capteurs `PT08.*` et des trois mesures météorologiques `T`, `RH`, `AH`. La cible est une mesure de référence documentée par la source, pas une observation parfaite de la concentration réelle. Ce test porte sur la reproduction hors période de cette mesure.

Il s’agit d’un test de prédiction/calibration classique distinct de la rotation descriptive UNIVERSAL_LOG. Les sorties d’un test ne valident ni n’invalident à elles seules l’ensemble du pipeline ou sa théorie. Les résultats ne doivent pas être décrits comme seuils de pollution, effets causaux ou preuves concernant le cancer.

## Données et admissibilité

- Source UCI Air Quality locale; SHA-256 et provenance dans `source_manifest.json`.
- `-200` est masqué comme valeur manquante. Aucune interpolation, imputation ou réordonnancement.
- Une ligne entre dans un pli uniquement si la cible et les huit entrées prévues sont présentes. Les lignes exclues et les effectifs par fenêtre sont rapportés.
- Pas de date, d’heure, d’autres lectures `*_GT`, ni de sortie du pipeline parmi les caractéristiques. Cela évite d’apprendre directement la saison ou une autre référence chimique.
- Les séparations sont chronologiques. Aucun mélange aléatoire des heures.

## Fenêtres fixes

| Pli | Entraînement | Test futur | Lignes complètes constatées pendant l’audit de couverture |
|---|---|---|---:|
| 1 | 10 mars–31 août 2004 | 1 septembre–31 octobre 2004 | 3 145 train; 947 test |
| 2 | 10 mars–31 octobre 2004 | 1 novembre–31 décembre 2004 | 4 092 train; 1 240 test |
| 3 | 10 mars–31 décembre 2004 | 1 janvier–4 avril 2005 | 5 332 train; 2 012 test |

Les bornes suivent les tranches calendaires retenues avant tout score. Le premier test commence après l’été; les tests suivants avancent le temps. Ils ne sont pas indépendants les uns des autres, puisque les périodes de test diffèrent et les entraînements s’agrandissent.

## Comparateurs gelés

1. `DummyRegressor(strategy="median")`, niveau de référence calculé sur l’entraînement du pli.
2. `StandardScaler` ajusté sur le seul entraînement puis `Ridge(alpha=1.0)`.
3. `HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, max_leaf_nodes=15, early_stopping=False, random_state=20261124)`.

Aucun réglage d’hyperparamètres n’est effectué sur les périodes test. Paramètres, graines et fenêtres sont des choix de protocole fixés, pas des constantes universelles. Les résultats doivent être rapportés par pli et modèle.

## Mesures et interprétation

Rapporter MAE, RMSE et R² sur les lectures `CO(GT)` de chaque période test; donner également le nombre de lignes évaluées et la MAE du comparateur médian dans le même pli. Une dégradation chronologique indique une difficulté de transport dans le temps sur ce fichier; elle ne prouve pas une dérive instrumentale. Pour parler de dérive de capteur, comparer ensuite les changements de performance aux réponses des capteurs, aux lacunes et à la référence, en gardant les causes concurrentes ouvertes.

Les sorties T0/TLog de la rotation restent une analyse distincte. Leur rapprochement aux dates et aux erreurs de calibration sera exploratoire, sans déplacer les plis ni choisir des fenêtres après lecture des résultats. Les explications « évolution de la cible », « chaîne de mesure/collecte » et « préparation/calcul » demeurent concurrentes; si elles ne peuvent être départagées, écrire **origine indéterminée**.

## Reproduction

Couverture seule : `python run_air_quality_reference_calibration_v1.py --prepare-only`. Exécution des comparateurs : `python run_air_quality_reference_calibration_v1.py`, avec le `.venv` du projet. Le CSV brut est local et ne doit pas être redistribué tant que la formulation de licence UCI notée dans le README n’est pas clarifiée.
