# UNIVERSAL_LOG — sorties multi-couches (AI4I)

**Exécutions complètes incluses :** 12. Ce document résume des sorties logicielles; il ne les transforme pas en faits sur le domaine.

## Sorties des six questions

Pour chaque exécution, chaque médiane ci-dessous est calculée sur les cellules finies flux × estimateur de la matrice correspondante; le compte exact est dans le CSV. Les Q ont des définitions et échelles différentes : leurs valeurs ne sont pas comparées entre questions. La figure standardise séparément chaque Q entre axes pour visualiser la sensibilité de configuration; un z-score de figure n’est ni p-value ni significativité.

| Contrôle | Cible utilisée | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q3=Q1 signalé |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| UDI | Machine failure | 0.5196 | 0.7156 | 0.5196 | 0.36693 | 3.3307 | 3.5262 | True |
| Air temperature [K] | Machine failure | 0.31758 | 0.64629 | 0.31758 | 0.58239 | 0.56211 | 2.2184 | True |
| Process temperature [K] | Machine failure | 0.40709 | 0.57684 | 0.40709 | 0.4599 | 2.7293 | 2.7699 | True |
| Rotational speed [rpm] | Machine failure | 0.38421 | 0.76913 | 0.38421 | 0.46791 | 2.671 | 3.2611 | True |
| Torque [Nm] | Machine failure | 0.36421 | 0.84674 | 0.36421 | 0.37201 | 2.7617 | 8.458 | True |
| Tool wear [min] | Machine failure | 0.33565 | 0.78775 | 0.33565 | 0.357 | 3.1087 | 9.6318 | True |
| Machine failure | UDI | 0.39697 | 0.63246 | 0.39697 | 0.53041 | 0.56385 | 2.6797 | True |
| TWF | Machine failure | 0.34182 | 0.6014 | 0.34182 | 0.52962 | 2.9609 | 3.3409 | True |
| HDF | Machine failure | 0.29682 | 0.95877 | 0.29682 | 0.56485 | 0.44327 | 2.971 | True |
| PWF | Machine failure | 0.26186 | 0.45469 | 0.26186 | 0.54176 | 0.55505 | 2.3425 | True |
| OSF | Machine failure | 0.35273 | 0.69151 | 0.35273 | 0.56374 | 2.9056 | 3.6216 | True |
| RNF | Machine failure | 0.32862 | 0.59337 | 0.32862 | 0.51586 | 3.0888 | 2.4783 | True |

## Définitions des six sorties Q inscrites dans le code

- **Q1 calme/chaos :** Taille d’effet entre progression basse et haute, pour une cellule flux × estimateur; le nom ne constitue pas un test du chaos.
- **Q2 tension/seuil :** Même type de taille d’effet dans une marge avant le seuil contre une marge après.
- **Q3 agressivité :** Comparaison Q1 restreinte aux flux dits agressifs; la sortie peut recopier Q1 si la couverture est faible.
- **Q4 persistance :** Séparation intra-fenêtre du flux brut, recopiée sur les colonnes d’estimateurs; ce n’est pas l’estimateur Hurst.
- **Q5 actif/réceptif :** Séparation actifs/réceptifs sur les moyennes brutes; la sortie peut être nulle si les étiquettes sont absentes.
- **Q6 échelle Q5 :** Q5 après division par l’écart-type sans centrage; cette version mise à l’échelle ne remplace pas Q5.

## Cascade et dérivées F1/F2

| Contrôle | T-2 F2 (%) | T-1 F1 (%) | T0 MC (%) | T+1 F1 (%) | T+2 F2 (%) | max F1 velocity | max F2 curvature |
|---|---:|---:|---:|---:|---:|---:|---:|
| UDI | 4.947 | 44.873 | 49.655 | 53.651 | 57.748 | 0.0184166 | 0.00582694 |
| Air temperature [K] | 19.446 | 81.658 | 97.104 | 100.000 | 100.000 | 0.010245 | 0.00320886 |
| Process temperature [K] | 1.869 | 66.992 | 70.276 | 74.543 | 100.000 | 0.00650796 | 0.00229919 |
| Rotational speed [rpm] | 1.930 | 10.612 | 87.300 | 93.162 | 100.000 | 0.00715653 | 0.00285739 |
| Torque [Nm] | 2.969 | 64.460 | 81.948 | 85.749 | 97.150 | 0.00528184 | 0.0023295 |
| Tool wear [min] | 16.507 | 19.422 | 22.540 | 25.566 | 41.742 | 0.00912213 | 0.00267501 |
| Machine failure | 0.000 | 26.635 | 55.630 | 59.408 | 72.882 | 964.653 | 267.783 |
| TWF | 3.994 | 27.284 | 72.937 | 76.803 | 86.044 | 0.0156016 | 0.0065609 |
| HDF | 0.000 | 89.482 | 93.307 | 96.307 | 99.307 | 0.0153268 | 0.00270602 |
| PWF | 4.034 | 13.110 | 16.135 | 93.192 | 93.192 | 0.0116186 | 0.00533826 |
| OSF | 6.933 | 53.768 | 57.507 | 84.510 | 84.510 | 0.0126795 | 0.00613304 |
| RNF | 3.750 | 36.840 | 41.986 | 45.669 | 48.530 | 0.0160015 | 0.00480208 |

## TLog et états calculés

La formule inscrite par v6.0.1 dans ces sorties est `(d-4)*log(n)`; l’échelle `n` est le nombre d’échantillons. Le code lui-même précise qu’il s’agit d’un indicateur de coupe sur les dimensions géométriques, pas de l’hologramme entier. Les médianes de classe ci-dessous restent des sorties du modèle et ne valident aucune transition dans le domaine.

| Contrôle | T_log saturation | T_log criticality | T_log divergence | T_log null | Delta tension | étiquette de régime | état L7a / sens / confiance | L7b verdict |
|---|---:|---:|---:|---:|---:|---|---|---|
| UDI | -11.622 | -5.6372 | -1.4642 | -6.7694 | 2.2058 | criticality | ok / down / 0.12952204859161906 | FRAGILE |
| Air temperature [K] | -11.175 | -7.3791 | -5.2515 | -6.9485 | 1.2863 | criticality | ok / up / 0.2440039524117562 | FRAGILE |
| Process temperature [K] | -11.315 | -6.1402 | -5.7718 | -6.6026 | 1.2036 | criticality | ok / up / 0.4062604559899172 | FRAGILE |
| Rotational speed [rpm] | -11.478 | -7.2332 | -5.6079 | -6.6555 | 1.2746 | criticality | ok / up / 0.5 | FRAGILE |
| Torque [Nm] | -11.43 | -6.9771 | -4.4337 | -6.9078 | 1.5193 | criticality | ok / up / 0.3808605604596322 | FRAGILE |
| Tool wear [min] | -11.27 | -5.9744 | -4.6052 | -6.5798 | 1.4473 | criticality | ok / up / 0.3407990379232954 | FRAGILE |
| Machine failure | -11.377 | -7.1169 | -5.2515 | -6.9973 | 1.3302 | criticality | ok / down / 0.44736027486468666 | FRAGILE |
| TWF | -11.667 | -7.7216 | -5.9521 | -6.9538 | 1.241 | criticality | ok / up / 0.38329782976134597 | FRAGILE |
| HDF | -11.1 | -6.7055 | -5.1303 | -6.9254 | 1.2964 | criticality | ok / up / 0.39376175596988605 | FRAGILE |
| PWF | -11.451 | -7.6092 | -5.34 | -7.1074 | 1.3271 | criticality | ok / up / 0.401871745156325 | FRAGILE |
| OSF | -12.101 | -7.1589 | -6.0079 | -7.157 | 1.3231 | criticality | ok / up / 0.4130382663626008 | FRAGILE |
| RNF | -11.375 | -7.0028 | -5.6644 | -6.948 | 1.2399 | criticality | ok / down / 0.3970995238683006 | FRAGILE |

## États prédictifs internes, bruit et robustesse

Les niveaux `L1_L2_target` et `L7a/L7b` sont les diagnostics internes du pipeline. Ils sont publiés comme tels, sans être mélangés au benchmark prédictif indépendant. Pour cet axe `L1`, le CSV conserve aussi MAE/RMSE, exactitude directionnelle et stabilité T0 du walk-forward interne; le test conventionnel hors-échantillon est un autre objet.

| Contrôle | L1 statut/sens | RMSE interne | exactitude directionnelle | stabilité T0 | alerte | bruit | empreinte outil | L7b horizon / walk-forward / cohérence |
|---|---|---:|---:|---:|---|---|---|---|
| UDI | ok / up | 0.0385 | 75% | FAIL | NORMAL | MEDIUM_HIGH | True | FAIL/FAIL/FAIL |
| Air temperature [K] | ok / down | 0.0329 | 75% | FAIL | PRECURSOR_ALERT | MEDIUM | True | FAIL/FAIL/FAIL |
| Process temperature [K] | ok / up | 0.0214 | 100% | FAIL | PRECURSOR_ALERT | MEDIUM_HIGH | True | FAIL/FAIL/PASS |
| Rotational speed [rpm] | ok / up | 0.0382 | 50% | FAIL | PRECURSOR_ALERT | MEDIUM | True | FAIL/FAIL/PASS |
| Torque [Nm] | ok / up | 0.0392 | 50% | FAIL | PRECURSOR_ALERT | MEDIUM_HIGH | True | FAIL/FAIL/PASS |
| Tool wear [min] | ok / up | 0.0225 | 75% | FAIL | NORMAL | MEDIUM | True | PASS/FAIL/PASS |
| Machine failure | ok / down | 365.12 | 100% | FAIL | PRECURSOR_ALERT | MEDIUM_HIGH | False | PASS/FAIL/PASS |
| TWF | ok / up | 0.0429 | 75% | FAIL | PRECURSOR_ALERT | MEDIUM_HIGH | True | FAIL/FAIL/PASS |
| HDF | ok / up | 0.0159 | 100% | FAIL | PRECURSOR_ALERT | MEDIUM_HIGH | True | PASS/FAIL/PASS |
| PWF | ok / up | 0.0414 | 50% | FAIL | NORMAL | MEDIUM_HIGH | True | FAIL/FAIL/PASS |
| OSF | ok / up | 0.0425 | 50% | FAIL | NORMAL | MEDIUM_HIGH | True | PASS/FAIL/PASS |
| RNF | ok / down | 0.0375 | 50% | FAIL | NORMAL | MEDIUM_HIGH | True | FAIL/FAIL/PASS |

## Portée des images et des sorties

- Cascade : affiche les positions de T-2 à T+2; les axes ont des unités et ordres différents.
- Heatmap Q : z-score descriptif séparé par question entre les contrôles; aucun seuil de significativité n’est appliqué.
- TLog par classe : reproduit les médianes enregistrées, sans conclure que la classe est une propriété physique du système.
- Les sorties complètes par axe contiennent les 29 estimateurs, matrices des six questions, diagnostics de bruit/CSD, analyse instrumentale, seuils, états L1-L7 et journaux. Elles sont conservées dans `runs/` et reproduites dans l’archive complète.
- Quand `target_requested` et `target_used` diffèrent, le repli est un changement effectif de configuration. Ne pas comparer ce run comme si la cible restait constante.
