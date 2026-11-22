# AI4I — rotation des contrôles v1

**Statut au 2026-11-22 21:21 UTC :** 12/12 contrôles avec T0 disponible; consultez le manifeste pour distinguer les erreurs, sorties sans seuil et appels en attente.

## Question et portée

Cette campagne mesure comment v6.0.1 réagit à une rotation de chaque colonne numérique comme axe de contrôle. Elle analyse 100 moyennes de blocs consécutifs de 100 lignes. La cible fixe est le taux `Machine failure` dans chaque bloc. Il s’agit d’une étude de comportement du pipeline sur un jeu synthétique; elle ne mesure pas la performance d’un classifieur ni l’efficacité d’une action industrielle.

## Valeurs observées

| Contrôle | Statut | Cible demandée → utilisée | Repli cible | Monotone | T0 (%) | T0 brut dans l’unité du contrôle | T0 ambigu | Flux | Contrôle exclu | Estimateurs | Durée (s) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UDI | complete | Machine failure → Machine failure | False | True | 49.655 | 4950.5 | False | 11 | True | 29 | 225.9 |
| Air temperature [K] | complete | Machine failure → Machine failure | False | False | 97.104 | 303.64 | True | 11 | True | 29 | 181.5 |
| Process temperature [K] | complete | Machine failure → Machine failure | False | False | 70.276 | 310.818 | True | 11 | True | 29 | 211.8 |
| Rotational speed [rpm] | complete | Machine failure → Machine failure | False | False | 87.300 | 1558.38 | True | 11 | True | 29 | 205.8 |
| Torque [Nm] | complete | Machine failure → Machine failure | False | False | 81.948 | 40.74 | True | 11 | True | 29 | 199.6 |
| Tool wear [min] | complete | Machine failure → Machine failure | False | False | 22.540 | 99.53 | True | 11 | True | 29 | 194.4 |
| Machine failure | complete | Machine failure → UDI | True | False | 55.630 | 0.02 | True | 11 | True | 29 | 179.5 |
| TWF | complete | Machine failure → Machine failure | False | False | 72.937 | 0.01 | True | 11 | True | 29 | 266.2 |
| HDF | complete | Machine failure → Machine failure | False | False | 93.307 | 0.06 | True | 11 | True | 29 | 204.5 |
| PWF | complete | Machine failure → Machine failure | False | False | 16.135 | 0 | True | 11 | True | 29 | 219.9 |
| OSF | complete | Machine failure → Machine failure | False | False | 57.507 | 0.01 | True | 11 | True | 29 | 236.7 |
| RNF | complete | Machine failure → Machine failure | False | False | 41.986 | 0 | True | 11 | True | 29 | 231.1 |

## Lecture des valeurs

T0 (%) est une coordonnée de progression calculée pour chaque axe; les colonnes ont des unités et des distributions différentes. Un écart entre contrôles montre une sensibilité de configuration dans cet essai, pas que l’un des contrôles est biologiquement ou causalement correct. Pour un contrôle non monotone, la conversion en valeur brute peut être ambiguë; l’avertissement et l’intervalle sont conservés dans les sorties complètes.

Le contrôle `Machine failure` a été demandé égal à la cible. Le code v6.0.1 applique alors son garde-fou diagonal et substitue la cible par `UDI` pour cet appel; ce run ne conserve donc pas la cible fixe des onze autres axes. Il est rapporté comme repli réellement observé, et ne doit pas être présenté comme une exécution diagonale à cible inchangée. Le contrôle sélectionné est retiré des flux analysés quand il est choisi. Les appels complets, journaux, paramètres, sorties JSON et graines sont conservés dans `runs/`.

## Hypothèses et résultats

**Hypothèses non confirmées ici :** les axes produiront-ils des T0 différents; l’agrégation en blocs lisse-t-elle ou déplace-t-elle les seuils; les drapeaux de panne révèlent-ils une propriété différente des mesures machine? Les résultats ci-dessus répondent uniquement pour cette version, cette transformation et ce jeu synthétique.

Le jeu source est synthétique, UDI est un identifiant ordonné sans statut d’horloge physique, et le choix de 100 blocs est une résolution d’analyse. Une étude de sensibilité à d’autres tailles de blocs est nécessaire avant toute conclusion générale.

## Reproduction

Voir `PROTOCOLE_AI4I_PIPELINE_CONTROLS_V1_FR.md`, `campaign_plan.json` et `campaign_manifest.json`. La rotation peut être reprise en relançant `run_ai4i_pipeline_control_rotation.py`; les appels déjà terminés avec le même hash d’entrée sont ignorés.
