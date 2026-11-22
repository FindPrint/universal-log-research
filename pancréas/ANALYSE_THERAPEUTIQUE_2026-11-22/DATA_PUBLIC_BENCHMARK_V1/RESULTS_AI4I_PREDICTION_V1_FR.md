# AI4I 2020 — benchmark prédictif exploratoire V1

**Date d’exécution :** 2026-11-22  
**Nature :** résultat mesuré sur un jeu synthétique; le pipeline UNIVERSAL_LOG n’a pas encore été exécuté sur ce jeu.

## Question testée — Niveau 1

Peut-on prédire l’étiquette `Machine failure` dans des blocs futurs du jeu AI4I à partir des variables machine disponibles avant la panne?

Cette question est indépendante de la question « où le pipeline place-t-il T0? ». Les résultats ci-dessous ne valident ni T0, ni TLog, ni la théorie complète.

## Données et prétraitement

- Miroir Kaggle téléchargé auprès de l’auteur du jeu; source primaire : UCI Machine Learning Repository, DOI `10.24432/C5HS5C`.
- 10 000 lignes, 14 colonnes, 339 étiquettes de panne, soit **3,39 %**.
- Le jeu UCI est explicitement décrit comme synthétique. `UDI` est utilisé uniquement pour préserver l’ordre et construire les blocs; il n’est pas une variable prédictive.
- Variables utilisées : type de produit, températures air/processus, vitesse de rotation, torque et usure de l’outil.
- Colonnes exclues de l’apprentissage : identifiant `UDI` et les étiquettes `Machine failure`, `TWF`, `HDF`, `PWF`, `OSF`, `RNF` sauf la cible `Machine failure`. Les sous-types sont des dérivés de panne et constitueraient une fuite d’information.
- Prétraitement appris sur chaque bloc d’entraînement : médiane + standardisation des colonnes numériques; imputation modale + one-hot pour `Type`.
- Séparation chronologique à fenêtres croissantes : train 1–4 000 / test 4 001–6 000; train 1–6 000 / test 6 001–8 000; train 1–8 000 / test 8 001–10 000. Aucun mélange aléatoire.
- Modèles : classifieur majoritaire, régression logistique équilibrée, forêt aléatoire équilibrée (300 arbres, graine 20261122). Les métriques à seuil utilisent 0,5; AUROC et average precision utilisent les probabilités.

## Résultats observés

| Modèle | AUROC moyen (min–max) | Average precision moyen (min–max) | Précision moyenne à 0,5 | Rappel moyen à 0,5 | F1 moyen à 0,5 |
|---|---:|---:|---:|---:|---:|
| Majoritaire | 0,500 (0,500–0,500) | 0,040 (0,020–0,077) | 0,000 | 0,000 | 0,000 |
| Régression logistique équilibrée | 0,854 (0,764–0,902) | 0,393 (0,369–0,424) | 0,204 | 0,660 | 0,307 |
| Forêt aléatoire équilibrée | 0,922 (0,859–0,961) | 0,589 (0,450–0,684) | 0,627 | 0,504 | 0,531 |

La prévalence de panne varie fortement entre les tests successifs : **7,70 %**, **2,25 %**, puis **1,95 %**. La forêt aléatoire a un rappel de **0,227** dans le premier bloc test et **0,644** dans le deuxième. Cela montre que la moyenne seule masque une variation substantielle selon le bloc. Le test est prédictif sur ce jeu synthétique, mais il n’établit aucune performance en usine.

## Interprétation limitée

Dans cette configuration précise, les deux modèles dépassent le classifieur majoritaire sur AUROC et average precision. La forêt aléatoire a la meilleure moyenne AUROC/AP; la régression logistique a un rappel moyen plus élevé au seuil fixe de 0,5 mais une précision beaucoup plus basse. Aucune conclusion de sélection de modèle n’est prise sans protocole de seuil, calibration, coûts d’erreurs et réplication externe.

Ce résultat ne démontre pas que UNIVERSAL_LOG prédit les pannes : le code UNIVERSAL_LOG n’a pas entraîné ces classifieurs et sa sortie `T0` n’est pas évaluée ici comme une prédiction. La prochaine étape est un essai de faisabilité du pipeline sur une petite entrée ordonnée, puis une rotation préspécifiée des colonnes de contrôle si le coût mesuré le permet.

## Traces

- Programme : `run_ai4i_prediction_benchmark.py`
- Source brute : `source/ai4i2020.csv`
- Manifest source et empreintes : `dataset_manifest.json`
- Manifest exécution : `prediction_benchmark_v1/benchmark_manifest.json`
- Mesures par bloc : `prediction_benchmark_v1/fold_metrics.csv`
- Probabilités hors-échantillon : `prediction_benchmark_v1/holdout_predictions.csv`
- Exécution : `.venv`, Python et scikit-learn version enregistrés dans le manifeste.
