# Calibration contrôlée des 29 estimateurs v5.3

**Date d'exécution :** 7 novembre 2026  
**Nature :** criblage de calibration synthétique, pas validation statistique complète.

## Résumé

Le pipeline calcule presque toutes les sorties sur les signaux testés : 1 483 valeurs finies sur 1 508 (98,3 %). Cette bonne couverture numérique ne garantit pas que les nombres mesurent la quantité voulue. Le test a surtout trouvé des comportements sélectifs : quelques estimateurs suivent bien des références connues; d'autres sont biaisés, non identifiables ou sensibles à l'échantillonnage et au plongement.

Les résultats les plus nets sont les suivants :

- Sur le bruit gaussien fractionnaire (fGn), les 4 sorties ciblées — Hurst, DFA transformé, `2-H` et pente spectrale — passent les tolérances de ce criblage aux deux valeurs de H testées.
- Sur les graphes de trajectoires fractionnaires intégrées (fBm), `Higuchi` suit les deux dimensions de référence; `Sevcik` et `BoxCounting` passent de justesse/avec marge selon la tolérance choisie. `Katz`, `Petrosian` et `VisibilityGraph` sont nettement biaisés dans cette implémentation et ce réglage.
- Sur les attracteurs quasipériodiques de dimension 1 à 3, les estimateurs de dimension intrinsèque ne se comportent pas de façon uniforme. `CorrelationD2` et `GrassbergerProcaccia` restent à moins de 0,5 de la référence dans les trois cas, mais cette tolérance est large; les autres méthodes peuvent fortement sous-estimer ou surestimer.
- Le cas de dimension 4 est un test de stress : plusieurs plongements du code ont au plus 8 coordonnées, tandis qu'une reconstruction générique par retards demande typiquement au moins `2k+1=9`. On ne peut donc pas conclure que les estimateurs échouent intrinsèquement en dimension 4; le code courant ne permet pas une calibration décisive de ce cas.
- Une première version du criblage comparait `PCAIntrinsic` et `Fisher` à `2k`. Cette cible est incorrecte pour les sorties actuelles : ce sont des ratios de participation de covariance, pas des rangs. Ils sont conservés comme résultats descriptifs dans les fichiers bruts et ne sont plus notés « réussis/échoués » contre `2k`.

**Avis général :** le pipeline est un banc de mesures expérimental riche et traçable; il n'est pas encore un instrument universel de dimension. Son point fort est de conserver des profils, plusieurs estimateurs et des contrôles; son point faible théorique est de brancher 21 sorties de natures différentes sur une même référence `d=4` avant d'avoir établi qu'elles sont commensurables.

## Protocole exécuté

Le script [calibrate_29_estimators.py](calibrate_29_estimators.py) appelle la fonction `apply_complexity` de `UNIVERSAL_LOG_v5_3.py`, avec le `.venv` du projet.

| Famille | Construction | Référence connue | Répétitions |
|---|---|---|---:|
| fGn | Bruit gaussien fractionnaire, `N=1024`, `H=0,50` ou `0,75` | Hurst `H`; pente spectrale `β=2H−1`; transformation `2−H` | 8 par H |
| Graphe fBm | Cumul des mêmes incréments fGn | Dimension du graphe `2−H` | 8 par H |
| Tore quasipériodique | Observation scalaire d'un tore de dimension `k=1,2,3,4`, `N=1024` | Dimension intrinsèque `k`; graphe continu lisse de l'observation = 1 | 5 par k |

Il y a 52 signaux synthétiques au total et chaque signal passe par les 29 sorties. Les seuils d'erreur absolue (0,10 à 0,75 selon la cible) sont des seuils exploratoires prédéclarés; ils ne sont pas des tests d'hypothèse ni des intervalles de confiance.

## Résultats ciblés

### Exposants connus

| Signal | Référence | Médiane Hurst | Médiane DFA (`2−α`) | Médiane `Hurst2mH` | Médiane β spectral |
|---|---:|---:|---:|---:|---:|
| fGn, H=0,50 | H=0,50; β=0 | 0,586 | 1,481 | 1,414 | 0,033 |
| fGn, H=0,75 | H=0,75; β=0,50 | 0,763 | 1,251 | 1,237 | 0,585 |

Toutes ces erreurs médianes sont dans les seuils de criblage définis. L'estimation `Hurst` à H=0,50 a un biais médian d'environ 0,086; le résultat reste un pilote sur 8 réalisations de longueur 1024. `Hurst2mH` et `DFA` mesurent ici des transformations liées au modèle fGn; cela ne justifie pas de les lire comme dimension pour n'importe quelle série.

### Dimension de graphe fBm

| H | Référence `2−H` | Higuchi | Sevcik | BoxCounting | Katz | Petrosian | VisibilityGraph |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0,50 | 1,50 | 1,485 | 1,359 | 1,381 | 1,000 | 1,027 | 1,993 |
| 0,75 | 1,25 | 1,243 | 1,190 | 1,187 | 1,000 | 1,019 | 1,856 |

Le résultat appuie `Higuchi` pour ces deux cas précis. `Sevcik` et `BoxCounting` satisfont le seuil fixé de 0,15; leur réussite n'est pas une preuve sur d'autres tailles, plages d'échelle, bruits ou familles de signaux. Les trois autres méthodes ne suivent pas `2−H` ici.

### Dimensions intrinsèques des tores

| Dimension vraie k | CorrelationD2 / GrassbergerProcaccia | InformationD1 | TwoNN | DANCo allégé | Levina–Bickel | LocalPCA | GraphDimension | PersistentHomology | MFA |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,196 | 1,000 | 2,346 | 1,189 | 1,378 | 1,000 | 0,916 | 0,376 | 2,000 |
| 2 | 2,466 | 1,732 | 5,640 | 1,700 | 1,855 | 3,167 | 0,929 | 2,082 | 4,000 |
| 3 | 3,233 | 1,728 | 1,395 | 5,462 | 4,746 | 4,821 | 1,319 | 2,356 | 4,000 |
| 4* | 3,324 | 1,777 | 1,068 | 7,113 | 8,201 | 5,571 | 1,176 | 2,811 | 6,000 |

Valeurs : médianes des 5 réalisations. `*` Dimension 4 est le stress d'embedding, pas un verdict de calibration. Les valeurs `D2` proches de la cible à k=1–3 sont encourageantes mais la tolérance de 0,5 est permissive. La dispersion entre méthodes est le constat central : elles ne forment pas encore un estimateur interchangeable unique.

### Valeurs descriptives hors cible

`PCAIntrinsic` renvoie un ratio de participation de covariance, et `Fisher` un ratio de participation de covariance inverse. Ils ne valent pas nécessairement `2k`, même quand le rang linéaire maximal du signal retardé est `2k`. À titre descriptif, les médianes PCAIntrinsic pour k=1–4 sont 1,97; 2,48; 3,80; 4,73; celles de Fisher sont 1,97; 2,44; 1,70; 3,12. Aucune ne doit être interprétée ici comme estimation directe de la variété k-torique.

Les méthodes évaluées contre le graphe lisse d'une observation scalaire de tore ont des résultats mitigés : `Katz` et `Petrosian` sont proches de 1; `Higuchi`, `Sevcik`, `BoxCounting` et `Hurst2mH` sont souvent proches de 1,7–2. Cette cible suppose que les échantillons résolvent bien le graphe continu sous-jacent; c'est une limite d'échantillonnage à tester en faisant varier la résolution temporelle.

## Couverture et indisponibilités

- Ensemble des sorties : 1 483/1 508 valeurs finies, soit 98,3 %.
- `Lyapunov` : 29/52 sorties finies (55,8 %); seulement 1/20 sur les quatre familles de tores. Sur ces séries quasipériodiques, l'estimateur est donc généralement indisponible et ne récupère pas l'exposant nul attendu.
- `TwoNN` : 50/52 valeurs finies, mais une valeur finie peut être fortement biaisée (ex. tore k=2).

La disponibilité est à distinguer de l'exactitude. Les 8 sorties sans interprétation directe comme `d` restent utiles comme signatures, mais leur simple présence ne valide pas leurs définitions.

## Conséquence pour T_log et Ising

Le calcul `(d−4) ln(n)` est arithmétiquement bien défini; sa lecture physique ne l'est pas tant que `d_kind` n'est pas spécifié. Pour un graphe de série, `d` reste typiquement sous 2, et le seuil 4 ne sera jamais franchi. Pour un attracteur intrinsèque, 4 peut être testé directement, mais le cas de stress montre que les plafonds d'embedding actuels empêchent une conclusion. Pour les dimensions spectrales ou effectives, le sens de 4 doit provenir d'un modèle correspondant.

Les essais Ising antérieurs apportent des contrôles physiques utiles : le Binder et les observables thermodynamiques du modèle classique donnent des résultats cohérents avec la référence de taille finie; l'Ising transverse quantique montre des pics physiques qui se rapprochent de `g_c=1`, tandis que l'ancre de criticité du pipeline ne localise pas ce point. Cela vérifie l'exécution sur deux domaines, et met aussi en évidence que `T_log` n'a pas encore détecté les transitions physiques dans la lecture testée.

## Limites et suite recommandée

1. Refaire la calibration sur plusieurs `N` (par exemple 256, 512, 1024, 2048, 4096), avec davantage de graines et des intervalles de confiance par bootstrap.
2. Ajouter bruit, dérive, données manquantes, pas d'échantillonnage variable et décalage d'unités; mesurer biais, variance, disponibilité et robustesse séparément.
3. Pour les tores, enregistrer la dimension et le délai effectifs de chaque embedding; inclure un plongement d'au moins 9 pour le stress k=4 et faire une étude de convergence en N.
4. Corriger ou justifier les sorties qui échouent; en particulier `Katz`, `Petrosian`, `VisibilityGraph`, `TwoNN`, `Lyapunov` et les approximations `DANCo`/`MFA`.
5. Tester la formule T_log elle-même avec des prédictions et critères fixés avant l'analyse : localisation de transition, taux de faux positifs sur des données sans transition, dérive de taille finie et stabilité inter-domaine.
6. Versionner les catégories `d_kind`; ne pas agréger graphes, attracteurs, rangs effectifs et dimensions spectrales dans une médiane unique sans justification.

## Fichiers produits

- [Script de calibration](calibrate_29_estimators.py)
- [Sorties des 29 estimateurs, par signal](estimator_outputs.csv)
- [Cibles par réalisation](targeted_calibration.csv)
- [Résumé par méthode et famille](targeted_calibration_summary.csv)
- [Résultats et configuration JSON](calibration_29_results.json)
- [Carte des erreurs médianes](calibration_error_heatmap.png)
- [Contrat de lecture de `d`](../CONTRAT_D_TLOG_ET_CALIBRATION.md)

## Références de méthode

- Higuchi, « Approach to an irregular time series on the basis of the fractal theory » (1988), [Physica D](https://www.sciencedirect.com/science/article/pii/0167278988900814).
- Levina & Bickel, « Maximum Likelihood Estimation of Intrinsic Dimension » (2004), [NeurIPS](https://papers.nips.cc/paper_files/paper/2004/hash/74934548253bcab8490ebd74afed7031-Abstract.html).
- Facco et al., « Estimating the intrinsic dimension of datasets by a minimal neighborhood information » (2017), [Scientific Reports](https://www.nature.com/articles/s41598-017-11873-y).
- Dimension du graphe d'un mouvement fractionnaire, [article mathématique](https://www.numdam.org/articles/10.1016/S1631-073X%2803%2900015-3/).
- Théorème de plongement par retards, Takens, [DOI 10.1007/BFb0091924](https://doi.org/10.1007/BFb0091924).
