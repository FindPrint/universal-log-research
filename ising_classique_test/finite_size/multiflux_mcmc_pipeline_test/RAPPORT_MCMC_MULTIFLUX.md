# Ising classique : trajectoires MCMC et interactions multi-flux

Protocole : [ISING_MCMC_MULTIFLUX_PROTOCOL.md](../../../ISING_MCMC_MULTIFLUX_PROTOCOL.md).

Simulation : Wolff 2D, `H=0`, `L=(16, 32)`, `T=2.0, Tc=2.269185314, 2.5`, 3 chaînes par cellule, 500 mises à jour de chauffe et 4000 observations par chaîne.
Une observation est une mise à jour de grappe Wolff; elle n'est pas une unité de temps physique.

Le CSV de température historique contient 3 observations par température (petites réplications indépendantes), pas une trajectoire temporelle longue. Les nouveaux CSV bruts conservent les 4 000 mesures; les appels au pipeline utilisent 1 mesure sur 20 (200 lignes), choisie régulièrement, pour garder les fenêtres chevauchantes du cœur v5.8 calculables.

## Contrôle de cohérence physique

Les moments calculés sur les nouvelles trajectoires sont comparés à `finite_size_results.csv` au point de température le plus proche. Le tableau donne les écarts standardisés par l'erreur combinée; avec seulement trois chaînes, ils restent diagnostiques.

| L | T simulée | T référence | z(E) | z(Cv) | z(chi_abs) | z(Binder) | z(|m|) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 2.000000 | 2.00 | 0.70 | 2.43 | 1.03 | -0.90 | -0.47 |
| 16 | 2.269185 | 2.27 | 0.05 | 0.82 | 0.23 | -0.56 | -0.06 |
| 16 | 2.500000 | 2.50 | 1.53 | 0.17 | -1.37 | -0.75 | -1.59 |
| 32 | 2.000000 | 2.00 | -0.56 | -0.23 | -1.04 | 1.03 | 0.82 |
| 32 | 2.269185 | 2.27 | -0.18 | 1.19 | -0.50 | 0.23 | 0.49 |
| 32 | 2.500000 | 2.50 | 0.97 | 1.40 | -0.38 | -0.64 | -1.01 |

## Résultats du pipeline

Le cœur `run_pipeline` v5.8 a été lancé 20 fois sur les trajectoires échantillonnées (1 ligne sur 20) avec une fenêtre fixe de 40 lignes et 24 positions de paysage; 20 runs ont abouti.
Les runs utilisent les 29 estimateurs et désactivent seulement l'optimisation Monte Carlo du seuil. Chaque appel reçoit un axe et une liste de flux explicitement nommés.

### Comparaison des axes au voisinage de Tc

| L | Contrôle | Flux utilisés | monotone ? | rho ordre/valeur | d_crit | Régime calculé | statut |
|---:|---|---|---|---:|---:|---|---|
| 16 | MC_Update | jeu commun (5 flux) | True | 1.00 | 3.263 | criticality | ok |
| 32 | MC_Update | jeu commun (5 flux) | True | 1.00 | 3.820 | criticality | ok |
| 16 | Energy_per_spin | jeu commun (5 flux) | False | 0.04 | 3.261 | divergence | ok |
| 16 | Magnetization | jeu commun (5 flux) | False | 0.03 | 1.862 | saturation | ok |
| 16 | Nearest_neighbor_correlation | jeu commun (5 flux) | False | -0.04 | 3.309 | criticality | ok |
| 16 | Noise_axis | jeu commun (5 flux) | False | -0.00 | 3.672 | criticality | ok |
| 16 | Abs_magnetization_shuffled | jeu commun (5 flux) | False | -0.04 | 3.286 | criticality | ok |
| 32 | Energy_per_spin | jeu commun (5 flux) | False | 0.00 | 3.115 | criticality | ok |
| 32 | Noise_axis | jeu commun (5 flux) | False | 0.05 | 3.011 | criticality | ok |

### Comparaison des configurations de flux à L=16, Tc, contrôle MC_Update

| Jeu de flux | n flux | d_sat | d_crit | d_div | régime |
|---|---:|---:|---:|---:|---|
| common | 5 | 1.634 | 3.263 | 3.981 | criticality |
| all_fluxes | 10 | 1.626 | 3.260 | 4.021 | criticality |
| target_absM_only | 1 | 1.609 | 2.729 | 3.906 | criticality |
| order_parameter_family | 3 | 1.643 | 3.263 | 4.005 | criticality |
| physical_without_noise | 4 | 1.605 | 3.195 | 3.955 | criticality |

## Lecture des résultats

Les moments thermodynamiques des nouvelles chaînes concordent avec le balayage de taille finie : 29 des 30 écarts comparés sont dans ±2 erreurs combinées (l'exception est Cv à L=16, T=2.0, à 2.43). Les trajectoires semblent donc physiquement plausibles pour ce pilote.

Le régime nommé `criticality` n'est pas un détecteur de transition ici : il apparaît dans les 6 cellules (L,T) avec contrôle temporel, y compris à T=2.0 et T=2.5, et apparaît aussi sous le contrôle négatif `Noise_axis`. Seul L=32 montre un maximum de d_crit parmi les trois températures testées à Tc; L=16 n'en montre pas. Ce petit nombre de températures ne localise pas Tc avec précision.

La sensibilité à l'orientation de l'axe est nette : `Nearest_neighbor_correlation = -Energy_per_spin/2` (corrélation de rang −1), mais à L=16, Tc, le contrôle énergie donne le régime `divergence`, tandis que la corrélation de voisins donne `criticality`. L'axe `Magnetization` donne `saturation`. Ces contrôles sont non monotones dans l'ordre de la chaîne; il s'agit de coupes triées, pas de temps ni de causalité.

La composition des flux compte aussi : à L=16, Tc, d_crit passe de 2.729 avec |m| seul à 3.263 avec la famille corrélée |m|, m², m⁴; ajouter Cluster_fraction change peu (3.195) et ajouter le bruit indépendant revient à 3.263. Les liens de rang |m|↔m² et |m|↔m⁴ sont exactement 1 dans ces données. Une moyenne qui compte ces flux comme observations indépendantes peut donc surpondérer une seule famille physique.

`Noise_axis` et `Abs_magnetization_shuffled` sont des contrôles négatifs : un profil géométrique stable autour de ces axes serait un signe de sensibilité aux tris/à la configuration, pas une découverte physique. `Noise_flux` est un flux indépendant conservé dans le jeu commun; le jeu complet ajoute des flux redondants (`E`/corrélation de voisins, `|m|`/m²/m⁴) et un flux mélangé.

Les axes énergie et aimantation ne sont généralement pas monotones au fil des mises à jour. Le pipeline les ordonne pour construire une coupe; leur seuil ne doit pas être lu comme une date ou une température critique. La comparaison utile est la variation des mêmes flux sous des axes différents et les alertes produites par les axes négatifs.

Les moments physiques restent le contrôle de référence. La dépendance aux axes/flux est un diagnostic de la représentation CSV; un changement de `d_crit` ou de régime n'est pas à lui seul une confirmation de transition.

## Fichiers

- [CSV brut représentatif, L16 à Tc](raw_trajectories/L16_T2.269185_chain0.csv)
- [Entrée échantillonnée remise au pipeline](pipeline_inputs/L16_T2.269185_chain0.csv)
- [Matrice axe × flux du pipeline](pipeline_axis_flux_matrix.csv)
- [Sorties des 29 estimateurs par run](pipeline_estimator_outputs.csv)
- [Profils TLog par d_kind](pipeline_tlog_by_d_kind.csv)
- [Diagnostics physiques et autocorrélations](mcmc_chain_physics.csv), [comparaison à l'étude finie](mcmc_physical_checks_vs_finite_size.csv)
- [Corrélations des flux critiques](critical_flux_spearman_matrix_L16.csv) et [figure](critical_flux_spearman_matrix_L16.png)
- [Sensibilité de d_crit au contrôle à Tc](pipeline_axis_sensitivity_at_Tc.png)
- [Journaux complets](pipeline_logs/)
