<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Supplement d'audit UNIVERSAL_LOG - 2026-11-14

Ce supplement ajoute un replay apparié v5.9.0/v5.9.1 sur les configurations multi-axes et une integration réelle de L7b-light/full. Les protocoles, scripts exacts, données d'entrée, sorties, journaux, figures et empreintes sont conservés dans les répertoires `audit_release/2026-11-14_*` et intégrés aux pièces jointes du PDF V2.

## Hypothèses et observations

| Hypothèse pré-déclarée | Observation | Portée |
|---|---|---|
| H1 - a configuration égale, les médianes brutes devraient rester égales si les estimateurs n'ont pas changé. | 580/580 médianes identiques exactement; écart absolu maximal 0. | Non-régression sur les 20 cas appariés. |
| H2 - le registre réparé devrait typer les estimateurs et exporter TLog par type. | 580/580 lignes avec `d_kind`, `quantity_type`, membership TLog; 260 lignes TLog groupées sur 13 types. | Export typé restauré dans ce jeu. |
| H3 - les correctifs pourraient modifier les labels d'état. | 20/20 vecteurs D et 20/20 labels de régime identiques à v5.9.0. | Aucune modification d'état observée dans ces cas. |

Aucune de ces observations ne calibre les seuils L7b, ne localise Tc ou ne prouve l'universalité.

## Replay apparié

- Configurations: 20/20 réussies; 8 CSV distincts réutilisés sur 20 configurations; 200 lignes par CSV.
- Médianes: 580/580 exactement égales; différence maximale 0.0.
- Sorties typed/TLog: 580 estimateurs typés; 260 lignes TLog par type; 13 types.
- D-vector: 20/20 vecteurs égaux composante par composante.
- Régimes v5.9.1: {'criticality': 18, 'divergence': 1, 'saturation': 1}.
- Paramètres: seed=20261108; fenêtre demandée=40 lignes; scan paysage=24 points (copie dérivée pour égaler la résolution du run v5.9.0); 29 méthodes; optimisations automatiques désactivées; max_workers=1.

### Matrice des 20 configurations

| L | T | Chaîne | Contrôle | Flux | n flux | Régime | d_crit |
|---:|---:|---:|---|---|---:|---|---:|
| 16 | 2.000000000 | 0 | MC_Update | common | 5 | criticality | 3.417265 |
| 16 | 2.269185314 | 0 | MC_Update | common | 5 | criticality | 3.262546 |
| 16 | 2.500000000 | 0 | MC_Update | common | 5 | criticality | 3.182688 |
| 32 | 2.000000000 | 0 | MC_Update | common | 5 | criticality | 3.513099 |
| 32 | 2.269185314 | 0 | MC_Update | common | 5 | criticality | 3.819868 |
| 32 | 2.500000000 | 0 | MC_Update | common | 5 | criticality | 2.952332 |
| 16 | 2.269185314 | 0 | MC_Update | all_fluxes | 10 | criticality | 3.259650 |
| 32 | 2.269185314 | 0 | MC_Update | all_fluxes | 10 | criticality | 3.657882 |
| 16 | 2.269185314 | 0 | Energy_per_spin | common | 5 | divergence | 3.261281 |
| 16 | 2.269185314 | 0 | Magnetization | common | 5 | saturation | 1.862405 |
| 16 | 2.269185314 | 0 | Nearest_neighbor_correlation | common | 5 | criticality | 3.308967 |
| 16 | 2.269185314 | 0 | Noise_axis | common | 5 | criticality | 3.671941 |
| 16 | 2.269185314 | 0 | Abs_magnetization_shuffled | common | 5 | criticality | 3.285983 |
| 32 | 2.269185314 | 0 | Energy_per_spin | common | 5 | criticality | 3.115017 |
| 32 | 2.269185314 | 0 | Noise_axis | common | 5 | criticality | 3.011272 |
| 16 | 2.269185314 | 0 | MC_Update | target_absM_only | 1 | criticality | 2.729004 |
| 16 | 2.269185314 | 0 | MC_Update | order_parameter_family | 3 | criticality | 3.262546 |
| 16 | 2.269185314 | 0 | MC_Update | physical_without_noise | 4 | criticality | 3.194999 |
| 16 | 2.269185314 | 1 | MC_Update | common | 5 | criticality | 3.258662 |
| 32 | 2.269185314 | 1 | MC_Update | common | 5 | criticality | 3.760901 |

Contrôles utilisés: `MC_Update`, `Energy_per_spin`, `Magnetization`, `Nearest_neighbor_correlation`, `Noise_axis` et `Abs_magnetization_shuffled`. Flux sets: common, all_fluxes, target_absM_only, order_parameter_family, physical_without_noise. Les configurations exactes, hashes d'entrée et noms de colonnes sont dans le protocole JSON embarqué.

### TLog par type

Chaque type ci-dessous apparaît dans les 20 configurations; le CSV embarqué conserve toutes les valeurs `d_median` et `T_log` par configuration.

| d_kind | Configurations |
|---|---:|
| `correlation_attractor_dimension` | 20 |
| `covariance_participation_dimension` | 20 |
| `graph_cluster_scaling_proxy` | 20 |
| `graph_dimension_proxy` | 20 |
| `information_attractor_dimension` | 20 |
| `inverse_covariance_participation_dimension` | 20 |
| `local_pca_dimension_proxy` | 20 |
| `mixture_local_pca_proxy` | 20 |
| `neighbor_intrinsic_dimension` | 20 |
| `persistent_h0_scaling_proxy` | 20 |
| `process_model_graph_dimension_proxy` | 20 |
| `spectral_dimension_proxy` | 20 |
| `visibility_graph_dimension_proxy` | 20 |

## Integration L7b-light multi-contrôle

Entrée: CSV archivé L16,Tc,chaîne 0, 200 lignes. Cible fixe `Abs_magnetization`; contrôles `MC_Update` et `Noise_axis`; outer mode `fast`; seed=20261108. Le wrapper a terminé en 900.79 s au total. Les verdicts sont internes aux heuristiques, pas des phases physiques.

| Contrôle | Verdict | Horizon | Walk-forward | Cohérence cible/régime |
|---|---|---|---|---|
| MC_Update | FRAGILE | FAIL | FAIL | PASS |
| Noise_axis | FRAGILE | FAIL | FAIL | FAIL |

Les deux axes renvoient `FRAGILE`. MC_Update échoue sur la stabilité d'horizon (min=0.417) et le walk-forward (écart-type T0=40.501); sa cohérence interne passe. Noise_axis échoue sur l'horizon (0.667, zone fragile), le walk-forward (21.806) et une divergence de direction cible/régime (down contre up; pénalité 0.12).

Le premier essai avec outer mode par défaut `full` n'a rien rendu après 15 minutes et a été arrêté; ce délai est conservé dans le dossier de trace. Il s'agit d'un résultat de coût d'exécution, pas d'un échec L7b.

## Integration L7b-full bornée

Entrée: les 80 premières lignes du même CSV, cible fixe `Abs_magnetization`, contrôle `MC_Update`, outer mode `fast`, `l7b_mode=full`, seed=20261108, n_scenarios=48 par défaut. Durée de l'appel: 1688.987 s. Cette tranche borne le test logiciel; elle ne fonde aucune inférence physique.

| Check | Valeur | Statut | Lecture du code |
|---|---:|---|---|
| Graine alternative 123 | 0.720 | PASS | T0 89.291% -> 88.571%; même direction. |
| Fenêtre 80% | 79.877 | FAIL | T0 89.291% -> 9.414%; direction inchangée mais grand déplacement. |
| Cible mélangée | 1.014 | FAIL | Magnitude Delta conservée (ratio 1.014); le code signale une persistance sans ordre temporel. |
| Cible logarithmique | 0.000 | INVARIANT | T0 89.291% -> 89.291%; check informatif. |

Verdict full: `FRAGILE`. La transformation logarithmique est informative et ne fait pas échouer le verdict. Le T0 de référence (89.291%) est la sortie interne de ce pipeline sur cette tranche, et n'est pas Tc.

### Défaut de traçabilité repéré

Le check graine affiche `graine_alternative: null` alors que le source choisit explicitement 123. `_l7b_extract_summary` ne transporte pas la graine, puis le formateur lit la clé absente. Le calcul numérique et son statut PASS existent; l'export manque l'identifiant de graine. Le source testé reste inchangé. Détails dans `PROTOCOL_ERRATUM.md`.

## Reproduction et empreintes

Commandes complètes dans `README_AUDIT_REPRODUCTION_V2.md` et `REPRODUCE_SUPPLEMENT_V2.ps1`. Principaux scripts: `audit_release/run_matched_v59_v591_replay.py`, `audit_release/run_l7b_integration.py`, `audit_release/run_l7b_full_reduced.py`. Le PDF V2 joint les sorties complètes et un index des pièces jointes avec hashes SHA-256.

SHA-256 v5.9.0 source: `a9ed57bb35bac39b9a0be3fd2fc2db027e1257690fe2ba64acd169d044eb2e97` (runtime dérivé à 24 points); SHA-256 source v5.9.1: `a2173839b8ebfcf3dfcf0ee809c5d0a7b2cb1fd34bcaa1199175fa6b23aa2ef8`; runtime v5.9.1 dérivé 24 points: `14683cb310691301f85062ffd275dc38236fd7117dde2a16865a13d89382ebd6`.

Code MIT; documents, données et résultats CC BY 4.0, sous réserve des notices tierces d'origine.

## Conclusion limitée

Ce replay apporte une preuve de non-régression des médianes, vecteurs D et labels pour les 20 cas retenus, et confirme la restauration des exports typés. L7b s'exécute en light/full, mais retourne FRAGILE sur ces axes/tests. Le pipeline n'a pas localisé de manière fiable la transition d'Ising dans ces essais, et ceux-ci ne démontrent pas son universalité.
