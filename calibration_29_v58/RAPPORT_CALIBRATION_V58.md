# Calibration des estimateurs — Universal Log v5.8

Cette exécution reprend les 52 signaux synthétiques du [criblage initial v5.3](../calibration_29/RAPPORT_CALIBRATION.md), mais charge UNIVERSAL_LOG_v5.8.py et écrit ses résultats dans un dossier séparé.

## Résultat de comparaison

- Les 29 méthodes ont été exécutées sur les mêmes 52 signaux, soit 1 508 sorties.
- v5.8 fournit 1 483 valeurs finies sur 1 508 (98,3 %), comme v5.3.
- Pour les 85 lignes ciblées disposant de valeurs finies, les médianes par méthode et famille sont identiques entre v5.3 et v5.8; l'écart maximal mesuré est 0.
- Trois lignes ciblées de Lyapunov sont indisponibles dans les deux versions sur les tores de dimension 1 à 3.

Cela confirme que la classification ajoutée à v5.8 n'a pas modifié les estimations observées sur ce criblage. C'est un contrôle de non-régression sur ces signaux, pas une validation générale.

## Fichiers

- [Script commun, configurable par variables d'environnement](../calibration_29/calibrate_29_estimators.py)
- [Sorties brutes v5.8](estimator_outputs.csv)
- [Cibles et médianes v5.8](targeted_calibration.csv), [résumé](targeted_calibration_summary.csv)
- [Résumé de comparaison machine-lisible](calibration_29_results.json)
- [Carte des erreurs](calibration_error_heatmap.png)
- [Taxonomie d_kind implémentée](../D_KIND_TAXONOMIE_V5_8.md)

Les résultats numériques détaillés étant identiques à ceux décrits dans le rapport initial, ce rapport conserve une comparaison compacte plutôt que de dupliquer ses tableaux.
