# Audit exploratoire des 29 estimateurs individuels

Extension exploratoire du pilote `d_kind`; plan d'analyse : [INDIVIDUAL_ESTIMATOR_EXTENSION_PLAN.md](../../../INDIVIDUAL_ESTIMATOR_EXTENSION_PLAN.md).

Valeurs calculées séparément pour 21 dimensions TLog admissibles et 8 signatures non dimensionnelles, sans agrégation par `d_kind`.

## Sorties dimensionnelles : convention `d=4` actuelle

Taux familial de fausses alertes parmi les 21 sorties dimensionnelles : **25.0%** sur 40 balayages nuls.

| Estimateur | d_kind | Localisés / 6 (w=31) | Localisés / 6 (w=41) | Couverture min. | Meilleur écart à 4 | Faux alertes individuelles (31 / 41) | Dérive médiane T | Candidat pilote |
|---|---|---:|---:|---:|---:|---:|---:|---|
| BoxCounting | graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 2.918 | 0.0% / 0.0% | n/a | non |
| CorrelationD2 | correlation_attractor_dimension | 0 / 6 | 0 / 6 | 100% | 2.809 | 0.0% / 0.0% | n/a | non |
| DANCo | neighbor_intrinsic_dimension | 0 / 6 | 0 / 6 | 100% | 2.413 | 0.0% / 0.0% | n/a | non |
| DFA | process_model_graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 3.759 | 0.0% / 0.0% | n/a | non |
| Fisher | inverse_covariance_participation_dimension | 0 / 6 | 0 / 6 | 100% | 3.000 | 0.0% / 0.0% | n/a | non |
| GraphDimension | graph_cluster_scaling_proxy | 0 / 6 | 0 / 6 | 100% | 3.189 | 0.0% / 0.0% | n/a | non |
| GrassbergerProcaccia | correlation_attractor_dimension | 0 / 6 | 0 / 6 | 100% | 2.506 | 0.0% / 0.0% | n/a | non |
| Higuchi | graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 2.930 | 0.0% / 0.0% | n/a | non |
| Hurst2mH | process_model_graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 3.002 | 0.0% / 0.0% | n/a | non |
| InformationD1 | information_attractor_dimension | 0 / 6 | 0 / 6 | 100% | 2.614 | 0.0% / 0.0% | n/a | non |
| Katz | graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 2.999 | 0.0% / 0.0% | n/a | non |
| LevinaBickel | neighbor_intrinsic_dimension | 0 / 6 | 0 / 6 | 0% | 2.150 | 0.0% / 0.0% | n/a | non |
| LocalPCA | local_pca_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 3.000 | 0.0% / 0.0% | n/a | non |
| MFA | mixture_local_pca_proxy | 0 / 6 | 0 / 6 | 100% | 2.000 | 0.0% / 0.0% | n/a | non |
| PCAIntrinsic | covariance_participation_dimension | 0 / 6 | 0 / 6 | 100% | 2.990 | 0.0% / 0.0% | n/a | non |
| PersistentHomology | persistent_h0_scaling_proxy | 1 / 6 | 1 / 6 | 97% | 0.010 | 25.0% / 25.0% | 0.160 | non |
| Petrosian | graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 2.974 | 0.0% / 0.0% | n/a | non |
| Sevcik | graph_dimension_proxy | 0 / 6 | 0 / 6 | 100% | 2.894 | 0.0% / 0.0% | n/a | non |
| SpectralDimension | spectral_dimension_proxy | 0 / 6 | 0 / 6 | 0% | 2.341 | 0.0% / 0.0% | n/a | non |
| TwoNN | neighbor_intrinsic_dimension | 0 / 6 | 0 / 6 | 0% | n/a | 0.0% / 0.0% | n/a | non |
| VisibilityGraph | visibility_graph_dimension_proxy | 0 / 6 | 0 / 6 | 0% | 1.692 | 0.0% / 0.0% | n/a | non |

Le statut candidat conserve les critères de répétabilité, couverture, stabilité et taux familial du pilote. Le seuil `d=4` est la convention TLog actuelle, pas une référence universelle garantie pour chaque algorithme.

Parmi les résultats finis, `PersistentHomology` est le seul estimateur régulièrement proche de 4 (13 combinaisons taille-fenêtre sur 14), mais il ne localise le pic physique que pour 1 taille sur 6 et déclenche 25 % de fausses alertes individuelles. `TwoNN` n'a aucune valeur finie sur ces courbes; la couverture minimale signale aussi les limites de `VisibilityGraph`, `SpectralDimension` et `LevinaBickel` dans ce régime.

## Signatures non dimensionnelles : localisation descriptive

Taux familial de fausse localisation de la pente maximale parmi les huit signatures : **47.5%** sur les contrôles nuls.

| Estimateur | Localisés / 6 (w=31) | Localisés / 6 (w=41) | Faux alignements (31 / 41) | Dérive médiane du centre de pente | Interprétation TLog |
|---|---:|---:|---:|---:|---|
| Hurst | 1 / 6 | 0 / 6 | 25.0% / 10.0% | 0.125 | hors couche TLog |
| SampleEn | 0 / 6 | 1 / 6 | 20.0% / 30.0% | 0.110 | hors couche TLog |
| PermutationEntropy | 1 / 6 | 1 / 6 | 5.0% / 0.0% | 0.068 | hors couche TLog |
| KolmogorovLZ | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | hors couche TLog |
| SpectralBeta | 0 / 6 | 0 / 6 | 0.0% / 25.0% | n/a | hors couche TLog |
| Lyapunov | 0 / 6 | 2 / 6 | 5.0% / 20.0% | 0.163 | hors couche TLog |
| MultifractalDeltaAlpha | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | hors couche TLog |
| SingularityFmax | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | hors couche TLog |

Ces huit valeurs n'ont pas été comparées à 4 et aucun `T_log` n'a été calculé pour elles : ce sont des signatures, conformément à la taxonomie v5.8. La localisation de la pente maximale est descriptive et n'établit pas à elle seule une transition.

## Conclusion

Candidats dimensionnels satisfaisant l'ensemble des seuils : **0 / 21**. Les signatures sont conservées comme diagnostics séparés et ne peuvent pas devenir des candidats TLog sans définition dimensionnelle et justification théorique.

L'analyse porte uniquement sur les courbes d'énergie d'équilibre, avec 40 contrôles nuls. Elle est exploratoire, les taux de fausses alertes sont grossiers, et l'incertitude Monte Carlo des dimensions n'est pas propagée.

`apply_complexity` z-score chaque fenêtre locale avant de calculer les estimateurs : cette analyse suit donc la forme locale, pas l'amplitude absolue ni la variance des fluctuations thermodynamiques.

## Fichiers

- [Plan de cette extension](../../../INDIVIDUAL_ESTIMATOR_EXTENSION_PLAN.md)
- [Résultats JSON](individual_estimator_transition_audit.json)
- [Profils individuels des 29 estimateurs](individual_local_profiles.csv)
- [Détections individuelles dimensionnelles](individual_dimension_detection.csv)
- [Localisation descriptive des signatures](signature_shape_localization.csv)
- [Contrôles nuls individuels](individual_smooth_null_results.csv)
