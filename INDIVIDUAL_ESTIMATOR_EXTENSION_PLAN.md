# Extension exploratoire : analyse individuelle des 29 estimateurs

Cette analyse est une extension décidée après lecture du pilote agrégé par `d_kind`; elle est donc exploratoire et ne remplace pas le protocole préenregistré `TLOG_TRANSITION_VALIDATION_PROTOCOL.md`.

## Entrée commune

- Même courbe physique d'énergie par spin en fonction de la température, mêmes tailles `L`, fenêtres de 31 et 41 points et mêmes pics de susceptibilité avec intervalles bootstrap.
- Même contrôle nul quadratique bruité, tailles de référence `L=16` et `L=64`, dix réplications et neuf centres par fenêtre.
- Les valeurs d'estimateurs sont calculées directement par `apply_complexity` dans v5.8, sans agrégation par `d_kind`.
- `apply_complexity` normalise chaque fenêtre locale par son z-score avant le calcul. Les profils testent donc surtout la forme locale, pas l'amplitude absolue ni la variance thermodynamique des fluctuations.

## Les 21 sorties dimensionnelles admissibles à la couche TLog

Pour chacune des 21 sorties présentes dans `DIMENSION_FOR_TLOG`, on teste séparément la convention actuelle `T_log=(d-4) ln(n)`, donc la proximité `|d-4| <= 0,5`, la localisation du centre le plus proche à l'intervalle physique, la couverture, la stabilité entre fenêtres et le taux de fausses alertes parmi les contrôles nuls. Les taux familiaux regroupent les 21 estimateurs dimensionnels et les centres parcourus d'une fenêtre.

Le seuil 4 reste une hypothèse de la couche géométrique, pas une référence universelle démontrée pour chacun de ces estimateurs. Le criblage ne transforme pas en fait physique les guides de sémantique v5.8 qui demandent une calibration par domaine.

## Les 8 signatures hors de la couche TLog

`PermutationEntropy`, `KolmogorovLZ`, `SpectralBeta`, `Hurst`, `SampleEn`, `Lyapunov`, `MultifractalDeltaAlpha` et `SingularityFmax` ne sont pas des dimensions dans la théorie v5.8. Elles ne sont donc pas comparées à 4 et aucun `T_log` ne leur est attribué. À titre descriptif, on mesure où la plus forte variation absolue entre centres adjacents apparaît sur neuf centres échantillonnés, puis on compte si ce centre est dans l'intervalle du pic physique. Les contrôles nuls donnent un taux de fausse localisation; cette mesure de forme ne constitue pas un détecteur TLog validé.

## Règle de lecture

Une sortie dimensionnelle n'est qu'un candidat de pilote si elle atteint au moins 4 localisations sur 6 tailles éligibles à chacune des deux fenêtres, si la couverture est d'au moins 80 %, si le taux familial de fausses alertes reste au plus à 10 % et si la dérive médiane des températures prédites ne dépasse pas 0,05. Pour les huit signatures, le même seuil de répétabilité et de stabilité est descriptif; l'absence d'une définition dimensionnelle reste déterminante : elles ne peuvent pas être déclarées candidates TLog par cette procédure.

Les contrôles sont peu nombreux (40 balayages lisses au total). Les taux sont des estimations pilotes grossières, sans propagation de l'incertitude Monte Carlo des courbes physiques aux valeurs des estimateurs.
