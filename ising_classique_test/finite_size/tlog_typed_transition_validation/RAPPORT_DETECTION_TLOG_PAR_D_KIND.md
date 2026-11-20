# Criblage de détection de transition TLog par d_kind

Protocole préenregistré : [TLOG_TRANSITION_VALIDATION_PROTOCOL.md](../../../TLOG_TRANSITION_VALIDATION_PROTOCOL.md).

Contrôles nuls : taux familial de fausses alertes = 25.0% sur 40 balayages lisses.

| d_kind | Localisés / 6 à w=31 | Localisés / 6 à w=41 | Faux positifs par type (w=31 / 41) | Dérive médiane entre fenêtres | Statut pilote |
|---|---:|---:|---:|---:|---|
| correlation_attractor_dimension | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| covariance_participation_dimension | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| graph_cluster_scaling_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| graph_dimension_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| information_attractor_dimension | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| inverse_covariance_participation_dimension | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| local_pca_dimension_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| mixture_local_pca_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| neighbor_intrinsic_dimension | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| persistent_h0_scaling_proxy | 1 / 6 | 1 / 6 | 25.0% / 25.0% | 0.160 | does_not_meet_predeclared_pilot_criteria |
| process_model_graph_dimension_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| spectral_dimension_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |
| visibility_graph_dimension_proxy | 0 / 6 | 0 / 6 | 0.0% / 0.0% | n/a | does_not_meet_predeclared_pilot_criteria |

## Lecture

Un type ne devient candidat pilote que s'il respecte simultanément la localisation, la couverture, le contrôle des fausses alertes et la stabilité entre les deux fenêtres. Les taux sont des criblages à petit effectif, pas des probabilités définitives.

## Conclusion du pilote

Aucun des 13 types ne satisfait les critères préétablis. Le taux familial de fausses alertes atteint 25.0%, au-dessus du plafond de 10%.

Le proxy de persistance H0 est le seul à entrer dans la bande candidate |d−4|≤0,5. Il localise le pic de susceptibilité dans seulement 1 taille sur 6 pour chacune des fenêtres, avec 25 % de fausses alertes par type et une dérive médiane de prédiction de 0,160 en température. Il ne constitue donc pas un détecteur fiable dans ce pilote.

Cette conclusion porte sur ces profils TLog, calculés à partir de la courbe d'énergie d'équilibre et selon ce protocole. Elle ne réfute ni la transition Ising (confirmée ici par les observables thermodynamiques/Binder), ni la validité d'autres types de données ou d'autres constructions TLog.

## Fichiers

- [Protocole préenregistré](../../../TLOG_TRANSITION_VALIDATION_PROTOCOL.md)
- [Résultats détaillés JSON](typed_tlog_transition_validation.json) et [résumé par d_kind](typed_tlog_detection_by_kind.json)
- [Profils locaux par température](positive_local_profiles.csv) et [résumé des détections](positive_detection_summary.csv)
- [Résultats des contrôles nuls](smooth_null_detection.csv)
- [Courbes d'énergie et marqueurs physiques](physical_energy_curves_and_markers.png)
- [Rapport de validation physique Ising](../physical_validation_report.md)
