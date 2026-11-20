# UNIVERSAL_LOG v5.9.4 — exécution PC69 sur tous les contrôles numériques

Généré UTC : 2026-11-20T02:09:44.660647+00:00

## Protocole exécuté

- Cible fixe : `CellState_basal`.
- Contrôles testés : 17 colonnes numériques, chacune dans un lancement isolé `--control-mode single`.
- Mode : `fast`, avec Cohen-d; cible fixe, domaine `pdac`, seed 42.
- Le code et l’entrée sont identifiés par SHA-256 dans `ALL_CONTROLS_AUDIT_MANIFEST.json`.
- Les sorties complètes du pipeline sont gardées dans un sous-dossier par contrôle.

## Contrôle d’exécution

- Statut global : `completed`.
- Runs terminés avec exit code 0 : 17/17.
- Inventaires déclarés conformes aux fichiers présents : `True`.
- Durée par run (secondes) : min 339.0, médiane 1569.0, moyenne 1402.9, max 2274.1.

## Résumé mécanique des sorties

Le CSV joint donne une ligne par colonne de contrôle, avec les cinq seuils, les métriques de dérivée, les statuts diagnostiques, les champs de prédiction et les avertissements consignés par le pipeline. Ce tableau résume les valeurs logicielles; il ne transforme pas à lui seul les sorties en preuve biologique.

### Résultats logiciels observés

- Contrôles non monotones : 17/17; T0 brut marqué ambigu : 17/17.
- T0 sur l’axe pourcentage interne : 13.13 à 96.75 pour cent.
- Diagnostic bruit : `scores_unavailable` dans 17/17; scores complets cumulés = 0, diagnostics partiels cumulés = 272.
- Monte-Carlo prédictif : complété dans 17/17; scénarios demandés [48], estimateurs demandés [29].
- R2 L1 négatif : 14/17; plage R2 -1.174 à 0.611; précision directionnelle rapportée 16.7 à 50.0 pour cent.
- Régimes internes de tension : {'criticality': 16, 'saturation': 1}; test interne de non-linéarité significative contre le nul : 0/17.
- L7b est désactivé dans 17/17 runs; il n’y a donc pas d’étiquette de robustesse L7b à rapporter.

### Interprétation délimitée

Ces nombres décrivent la sortie du programme sur cet ordre de lignes. Comme l’entrée est une coupe transversale de cellules, échantillonnée puis mélangée, sans colonne de temps/progression, les pourcentages internes ne représentent pas un moment biologique de transition. Les T0 présents ne donnent donc pas un seuil temporel ou thérapeutique du cancer.

| Contrôle | Exit | Durée (s) | Monotonie | T0 (%) | Ambigu T0 brut | Statut diagnostic bruit | Statut tension | L7a | L7b |
|---|---:|---:|---|---:|---|---|---|---|---|
| Treatment_code | 0 | 361.1 | non_monotone | 50.23693110539105 | True | scores_unavailable | ok | ok | disabled |
| CellState_basal | 0 | 356.9 | non_monotone | 58.93775035580122 | True | scores_unavailable | ok | ok | disabled |
| CellState_classical | 0 | 339.0 | non_monotone | 44.73649153043307 | True | scores_unavailable | ok | ok | disabled |
| scBasalScore | 0 | 340.6 | non_monotone | 76.1589247160899 | True | scores_unavailable | ok | ok | disabled |
| scClassicalScore | 0 | 1002.4 | non_monotone | 13.132897709248958 | True | scores_unavailable | ok | ok | disabled |
| EMTScore | 0 | 1017.1 | non_monotone | 88.07946235804496 | True | scores_unavailable | ok | ok | disabled |
| S_score | 0 | 1142.4 | non_monotone | 44.73649153043307 | True | scores_unavailable | ok | ok | disabled |
| G2M_score | 0 | 1135.4 | non_monotone | 22.982570991185693 | True | scores_unavailable | ok | ok | disabled |
| KRAS | 0 | 2066.8 | non_monotone | 75.07523947591214 | True | scores_unavailable | ok | ok | disabled |
| EGFR | 0 | 1997.8 | non_monotone | 85.9120918776895 | True | scores_unavailable | ok | ok | disabled |
| ERBB2 | 0 | 2015.8 | non_monotone | 96.74894427946681 | True | scores_unavailable | ok | ok | disabled |
| ERBB3 | 0 | 2069.8 | non_monotone | 22.982570991185693 | True | scores_unavailable | ok | ok | disabled |
| STAT3 | 0 | 2060.8 | non_monotone | 96.74894427946681 | True | scores_unavailable | ok | ok | disabled |
| GATA6 | 0 | 2274.1 | non_monotone | 19.699346563873448 | True | scores_unavailable | ok | ok | disabled |
| KRT19 | 0 | 2063.2 | non_monotone | 16.416122136561203 | True | scores_unavailable | ok | ok | disabled |
| CEACAM5 | 0 | 2038.0 | non_monotone | 59.93146822467287 | True | scores_unavailable | ok | ok | disabled |
| TP63 | 0 | 1569.0 | non_monotone | 82.6610361571563 | True | scores_unavailable | ok | ok | disabled |

## Portée et limites de cet essai

- Le fichier PC69 contient 90 cellules échantillonnées (15 dans chacun de six groupes animaux); les cellules ne remplacent pas les souris comme unités biologiques indépendantes.
- Les lignes ont été sélectionnées puis mélangées selon le manifeste. Le CSV ne contient ni temps ni progression expérimentale observée.
- L’axe en pourcentage créé par le pipeline ne doit donc pas être présenté ici comme le temps d’apparition d’une résistance ou d’une transition tumorale.
- `T0_ambiguous`, la monotonie du contrôle, les avertissements et les désaccords de couches doivent être consultés avec chaque sortie complète, et non remplacés par un seul score.
- L7b a été désactivé pour ces lancements par `--no-l7b`; L7a seul ne constitue pas une validation robuste.
- Ce test exécute le pipeline; il ne teste pas un traitement sur patients, ne démontre pas une guérison et ne constitue pas une validation indépendante de la théorie.

## Fichiers d’audit

- `ALL_CONTROLS_SUMMARY.csv` — table des 17 contrôles.
- `ALL_CONTROLS_SUMMARY.json` — même synthèse en JSON, avec commandes, statuts et avertissements.
- `ALL_CONTROLS_AUDIT_MANIFEST.json` — SHA-256 de chaque fichier de sortie, ainsi que du code et de l’entrée.
- Chaque dossier de contrôle conserve `master_results.json`, `reading_synthesis.json`, les tables d’estimateurs, diagnostics, rapports et journal de console.
