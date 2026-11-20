# Types de mesure `d_kind` — Universal Log v5.8

v5.8 ajoute un type sémantique à chacune des 29 sorties. Cette classification ne change pas les estimateurs ni la formule historique. Elle rend explicite la quantité visée et conserve deux lectures : les médianes de classes existantes, pour compatibilité, et de nouveaux profils `T_log_by_d_kind`, qui ne mélangent pas de types différents.

## Les types utilisés

| `d_kind` | Estimateurs | Ce que le nombre décrit | Rapport au seuil 4 |
|---|---|---|---|
| `graph_dimension_proxy` | `Higuchi`, `Katz`, `Petrosian`, `Sevcik`, `BoxCounting` | Rugosité estimée du graphe temps-signal | Une dimension de graphe scalaire usuelle est entre 1 et 2; 4 n'est pas un seuil générique pour cet objet |
| `process_model_graph_dimension_proxy` | `DFA`, `Hurst2mH` | Transformation en dimension de graphe telle que `2−α` ou `2−H` | La relation dépend du processus et de ses hypothèses |
| `visibility_graph_dimension_proxy` | `VisibilityGraph` | Proxy de rugosité déduit des degrés d'un graphe de visibilité | Relation spécifique à une classe de signaux, à valider |
| `correlation_attractor_dimension` | `CorrelationD2`, `GrassbergerProcaccia` | Dimension D2 d'un nuage reconstruit | Hypothèse de dimension 4 à tester avec reconstruction et plage d'échelle adéquates |
| `information_attractor_dimension` | `InformationD1` | Dimension d'information D1 du nuage reconstruit | D1 peut différer de D2 pour une mesure non uniforme |
| `neighbor_intrinsic_dimension` | `TwoNN`, `DANCo`, `LevinaBickel` | Dimension intrinsèque par distances ou angles de voisins proches | Dépend de l'échantillonnage, de l'embedding et du voisinage |
| `covariance_participation_dimension` | `PCAIntrinsic` | Nombre effectif de directions de covariance | Ratio de participation, pas rang exact ni dimension garantie de variété |
| `inverse_covariance_participation_dimension` | `Fisher` | Nombre effectif selon les valeurs propres inverses | Mesure distincte de la participation PCA et de la dimension d'attracteur |
| `local_pca_dimension_proxy` | `LocalPCA` | Nombre de composantes expliquant 95 % localement | Dépend du voisinage et de la coupure choisie |
| `graph_cluster_scaling_proxy` | `GraphDimension` | Pente de croissance de grappes sur le graphe k-NN | Proxy à calibrer sur des géométries connues |
| `persistent_h0_scaling_proxy` | `PersistentHomology` | Pente de fusion des composantes connexes H0 | Proxy de cette implémentation, à calibrer |
| `mixture_local_pca_proxy` | `MFA` | Maximum de dimensions PCA à 95 % par groupe | Dépend du nombre de groupes et de la procédure locale |
| `spectral_dimension_proxy` | `SpectralDimension` | `(5−β)/2` selon le code v5.8 | Le modèle spectral du domaine doit justifier le seuil |

Les 8 sorties de type `signature`, non branchées directement sur `d`, sont elles aussi typées : `PermutationEntropy` (entropie ordinale), `SampleEn` (entropie échantillonnale), `KolmogorovLZ` (complexité algorithmique proxy), `SpectralBeta` (exposant spectral), `Hurst` (exposant de Hurst), `Lyapunov` (exposant dynamique), `MultifractalDeltaAlpha` (largeur multifractale) et `SingularityFmax` (maximum de `f(α)`). Une signature peut être utile à l'analyse sans être une dimension à comparer à 4.

## Ce qui apparaît dans les sorties

Chaque entrée de `per_estimator` contient maintenant `d_kind`, `quantity_type`, une définition courte, un conseil d'interprétation du seuil 4 et le statut de branchement TLog. Les sorties principales contiennent aussi `estimator_measurement_types` et `measurement_taxonomy_schema_version`.

Dans `geometric_layer` :

- `T_log_by_estimator` donne la lecture méthode par méthode et son type;
- `T_log_by_d_kind` calcule une médiane exploratoire des estimateurs disponibles d'un même type, en gardant leurs valeurs et leur dispersion;
- `T_log_class_median` conserve la lecture historique v5.8. Un avertissement indique si l'ancre de classe combine plusieurs `d_kind`.

Les profils par type gardent la formule `(d−4) ln(n)`, mais leur statut reste `exploratory_requires_domain_calibration`. Les 29 estimateurs ne sont pas supprimés, et les valeurs individuelles restent consultables.

Chaque exécution exporte également `estimator_measurement_types.csv` et `estimator_measurement_types.json`, pour que le lecteur puisse inspecter la taxonomie sans parcourir le code.

## Contrôle ajouté

Le test [test_measurement_taxonomy_v58.py](ising_classique_test/test_measurement_taxonomy_v58.py) vérifie :

1. que chacun des 29 noms apparaît exactement une fois;
2. que les 21 estimateurs branchés sur la couche géométrique ont un `quantity_type` de dimension, et que les 8 autres sont des signatures;
3. que chaque valeur `per_estimator` expose le bon type;
4. que chaque profil `T_log_by_d_kind` ne contient que des estimateurs de son type;
5. que les anciennes médianes de classe signalent leurs mélanges sémantiques.

La classification est un contrat opérationnel versionné, pas une preuve que les estimateurs sont déjà calibrés pour tous les domaines.

## Vérifications réalisées

Le test synthétique v5.8 reproduit les médianes ciblées v5.3 à l'identique sur 85 comparaisons finies; le taux de valeurs finies reste 1 483/1 508. Les 21 tests passent avec le `.venv`, dont le contrôle des exports JSON/CSV contenant les 29 méthodes.

Les paysages Ising archivés ont ensuite été regroupés par `d_kind`. Les anciennes ancres `D_vector` correspondent exactement aux valeurs stockées : les nouvelles métadonnées n'altèrent donc pas les médianes historiques. Les nouveaux profils séparent, par exemple, la dimension de corrélation D2 de D1, des estimateurs par voisins, des ratios de covariance et des proxies de graphes. Les profils sont exploratoires et ne transforment pas le seuil 4 en seuil validé.

Rapports de résultat : [comparaison de calibration v5.8](calibration_29_v58/RAPPORT_CALIBRATION_V58.md) et [relecture typée Ising](tlog_d_kind_v58_results/RAPPORT_RELECTURE_ISING_V58.md). Les fichiers JSON/CSV complets de cette relecture sont conservés à côté du rapport.
