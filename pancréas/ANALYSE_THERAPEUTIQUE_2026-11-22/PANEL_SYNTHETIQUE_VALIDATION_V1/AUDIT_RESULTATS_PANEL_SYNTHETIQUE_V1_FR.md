# Rapport V1 — validation synthétique d’un panel groupé

**Date de génération :** 2026-11-22
**Statut de la campagne :** passed
**Données patient :** aucune; panel entièrement généré.
**Cœur :** v6.0.1-control-flux-exclusion-L7aL7b-CohenD

## Résultat mesuré

15 appels complets ont été enregistrés pour trois trajectoires de 64 visites et cinq colonnes numériques candidates comme contrôles. Le tableau détaillé ci-dessous garde une ligne par couple patient/contrôle.

| Patient | Contrôle | N | Contrôle monotone | T0 (%) | Statut cascade | TLog saturation | TLog criticité | TLog divergence | TLog référence nulle | Cible utilisée | Repli diagonal |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---|---|
| SYN-P01 | marker_correlated | 64 | False | 59.48 | ok | -11.26 | -6.401 | -4.708 | -6.35 | signal_primary | False |
| SYN-P01 | marker_oscillatory | 64 | False | 92.07 | ok | -11.05 | -8.201 | -6.238 | -6.32 | signal_primary | False |
| SYN-P01 | noise_independent | 64 | False | 35.55 | ok | -11.76 | -7.619 | -4.806 | -6.696 | signal_primary | False |
| SYN-P01 | signal_primary | 64 | False | 46.07 | ok | -11.46 | -7 | -4.274 | -6.967 | week_from_start | True |
| SYN-P01 | week_from_start | 64 | True | 56.77 | ok | -11.88 | -7.858 | -4.159 | -6.898 | signal_primary | False |
| SYN-P02 | marker_correlated | 64 | False | 62.53 | ok | -11.5 | -6.684 | -4.159 | -6.522 | signal_primary | False |
| SYN-P02 | marker_oscillatory | 64 | False | 93.76 | ok | -10.05 | -8.406 | -5.571 | -5.884 | signal_primary | False |
| SYN-P02 | noise_independent | 64 | False | 75.1 | ok | -10.73 | -8.686 | -6.238 | -6.508 | signal_primary | False |
| SYN-P02 | signal_primary | 64 | False | 41.7 | ok | -11.08 | -7.063 | -4.834 | -6.313 | week_from_start | True |
| SYN-P02 | week_from_start | 64 | True | 61.5 | ok | -12.01 | -8.325 | -4.949 | -7.135 | signal_primary | False |
| SYN-P03 | marker_correlated | 64 | False | 61.7 | ok | -11.14 | -7.505 | -4.493 | -6.262 | signal_primary | False |
| SYN-P03 | marker_oscillatory | 64 | False | 92.39 | ok | -10.75 | -8.629 | -6.238 | -6.308 | signal_primary | False |
| SYN-P03 | noise_independent | 64 | False | 79.47 | ok | -11.07 | -8.557 | -6.238 | -5.855 | signal_primary | False |
| SYN-P03 | signal_primary | 64 | False | 49 | ok | -11.63 | -7.078 | -4.19 | -6.709 | week_from_start | True |
| SYN-P03 | week_from_start | 64 | True | 59.14 | ok | -12 | -7.796 | -5.027 | -7.216 | signal_primary | False |

## Contrôles techniques post-exécution

| Assertion | Résultat observé |
|---|---|
| all_groups_have_one_patient | PASS |
| all_controls_excluded_from_analyzed_fluxes | PASS |
| all_29_estimators_declared | PASS |
| all_29_estimator_flux_columns_emitted | PASS |
| six_conceptual_question_groups_emitted | PASS |
| q5_aliases_identical | PASS |
| q6_aliases_identical | PASS |
| all_requested_controls_covered | PASS |
| all_patient_groups_covered | PASS |
| oscillatory_control_retained | PASS |
| diagonal_target_fallback_explicit | PASS |
| actual_v6_short_series_refusal | PASS |

## Sorties F1/F2 et dérivées

Les maxima F1/F2 de la cascade et le nombre d’entrées estimateur-flux avec dérivées pré/post disponibles sont ci-dessous. Les valeurs détaillées de première et deuxième dérivée avant/après T0 sont reproduites dans l’annexe PDF et dans chaque résultat JSON du snapshot.

| Patient | Contrôle | F1 max | F2 max | dérivées post valides | dérivées pré valides |
|---|---|---:|---:|---:|---:|
| SYN-P01 | marker_correlated | 0.04308 | 0.004563 | 92 | 92 |
| SYN-P01 | marker_oscillatory | 0.0636 | 0.01103 | 92 | 92 |
| SYN-P01 | noise_independent | 0.05324 | 0.01233 | 112 | 111 |
| SYN-P01 | signal_primary | 1.723 | 0.2299 | 92 | 92 |
| SYN-P01 | week_from_start | 0.04077 | 0.004347 | 91 | 91 |
| SYN-P02 | marker_correlated | 0.04635 | 0.00435 | 92 | 92 |
| SYN-P02 | marker_oscillatory | 0.05617 | 0.01002 | 100 | 100 |
| SYN-P02 | noise_independent | 0.04842 | 0.01083 | 92 | 92 |
| SYN-P02 | signal_primary | 1.201 | 0.1421 | 92 | 92 |
| SYN-P02 | week_from_start | 0.04609 | 0.003911 | 91 | 91 |
| SYN-P03 | marker_correlated | 0.04797 | 0.004467 | 92 | 92 |
| SYN-P03 | marker_oscillatory | 0.05353 | 0.01249 | 92 | 92 |
| SYN-P03 | noise_independent | 0.05852 | 0.01679 | 92 | 92 |
| SYN-P03 | signal_primary | 1.768 | 0.2713 | 92 | 92 |
| SYN-P03 | week_from_start | 0.04326 | 0.002961 | 91 | 91 |

Cas court : 96 lignes au total auraient dépassé le garde de 50, mais chaque patient avait 32 visites. Le harnais a enregistré 15 abstentions et 0 appel(s) au moteur.
Un appel direct supplémentaire au cœur v6.0.1 sur SYN-P01 a retourné ValueError : Série trop courte : 32 points valides. Au moins 50 sont requis avec la configuration actuelle.

Dans les CSV df_feat, 141005 cellules numériques finies ont été comptées parmi les colonnes moyennes des estimateurs. Ce décompte décrit les cellules finies présentes; il n’est pas une mesure de justesse.

## Ce que ces résultats établissent

Les sorties documentent l’exécution de v6.0.1 par trajectoire et par contrôle sur des séries construites, ainsi que l’absence de mélange d’identifiants dans chaque CSV transmis au moteur. Le contrôle oscillatoire a été conservé dans le plan. Les valeurs T0 et TLog sont des sorties de la configuration, pas des mesures de précision.

Le générateur place délibérément un changement lisse dans une partie des flux. Il ne s’agit pas d’un test indépendant de localisation : le panel est simulé, la forme du signal est connue par construction, et la configuration n’a pas été calibrée sur des données externes.

## Limites et suites

- Aucune donnée PDAC ou autre donnée patient n’a été chargée.
- Aucun bénéfice thérapeutique, biomarqueur, diagnostic ou résultat clinique n’est évalué.
- Le contrôle diagonal partage son identité avec la cible fixe et le pipeline l’a replié explicitement; ce run n’est pas comparable aux autres contrôles pour les niveaux dépendant de la cible.
- Les résumés restent individuels. Aucun bootstrap ou intervalle inférentiel sur trois sujets synthétiques n’est présenté.
- Le cas court confirme l’abstention du harnais; il ne résout pas le minimum de longueur du cœur pour les trajectoires cliniques courtes.
- Les JSON complets, traces, CSV et images générés sont conservés dans le snapshot séparé du projet.

## Reproduction et empreintes

- Script du banc d’essai SHA-256 : 4463fd028c07de8db6f03be23aabaf951de25f1a361230154c2af46f453e4d10
- Source v6.0.1 SHA-256 : ce0557cb4c44c15a142291e5522b446f7212136686c3035c97f12a3d0e959086
- CSV panel SHA-256 : be05cbc3982b098a9f76d11a9d911395d50c196efbb8ca4a0e5468aac54183fc
- Instructions : README_FR.md et PROTOCOLE_GROUPE_PANEL_V1_FR.md dans ce dossier.

## Question de méthode à garder ouverte

Les paramètres synthétiques, la cible fixe, le mode fast et le budget auxiliaire ont été spécifiés pour tester le câblage, non pour optimiser T0. Toute agrégation cohorte, rééchantillonnage patient, interprétation des flux ou modification du minimum doit faire l’objet d’un protocole distinct avant d’examiner une cohorte réelle.

### Déclaration

Résultats observés et décision de portée sont séparés. Hypothèse d’ingénierie : le wrapper peut préserver des trajectoires si les appels restent isolés. Résultat de cette campagne : critères de câblage listés dans le JSON. Aucun de ces éléments ne prouve la théorie générale ni une application biomédicale.
