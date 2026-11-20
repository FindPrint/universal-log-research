# Guide débutant — Universal Log, les 29 estimateurs et `T_log`

**Version décrite :** `UNIVERSAL_LOG_v5_3.py`. Ce guide explique le comportement de cette version. Les catégories « saturation », « criticalité », « divergence » et « référence nulle » sont la taxonomie proposée par le projet; elles ne sont pas, à elles seules, des diagnostics physiques validés.

**Complément v5.8 :** la nouvelle version conserve ces classes et ajoute un `d_kind` sémantique à chaque estimateur, plus des profils `T_log` par type. Voir la [taxonomie d_kind v5.8](D_KIND_TAXONOMIE_V5_8.md). Les changements de version ne modifient pas rétroactivement les rapports v5.3.

Le contrôle de non-régression sur les données synthétiques reproduit les médianes v5.3 à l’identique. La relecture des paysages Ising confirme que les anciennes ancres restent inchangées; elle rend surtout visibles les désaccords entre types de dimension. Voir [les résultats v5.8](calibration_29_v58/RAPPORT_CALIBRATION_V58.md) et [les profils Ising typés](tlog_d_kind_v58_results/RAPPORT_RELECTURE_ISING_V58.md).

## 1. Le pipeline en quelques mots

Le pipeline lit un tableau, choisit un **axe de contrôle** (par exemple la température ou le champ) et mesure comment les autres **flux** (énergie, aimantation, etc.) changent le long de cet axe. Pour chaque flux, il calcule jusqu’à 29 statistiques. Il résume ensuite leurs trajectoires et peut produire des lectures de `T_log`.

Le résultat dépend donc de la coupe choisie : « aimantation en fonction de la température » et « énergie en fonction de la taille du réseau » sont deux analyses différentes du même système. Le code standardise chaque flux avant ces calculs; cela facilite les comparaisons de forme, mais enlève l’unité et l’amplitude absolue du flux.

## 2. `T_log` : la formule et les choix qui l’accompagnent

```text
T_log(n, d) = (d - 4) × ln(n)
```

- **`ln`** est le logarithme naturel; le code exige une échelle `n > 1`.
- **`4`** est la dimension critique de référence postulée dans `TLog.txt` et codée comme constante. Les essais présents ne démontrent pas que cette référence convient à tous les domaines.
- **`n`** est l’échelle de la question. Le code utilise par défaut le nombre de lignes, mais permet plusieurs échelles étiquetées : observations, mesures indépendantes, sites du réseau, etc. Il faut expliquer ce que signifie `n` dans chaque résultat. Le code ne traite pas son incertitude.
- **`d`** est une sortie que l’on choisit explicitement. Elle peut être la valeur d’un estimateur ou une ancre résumant plusieurs estimateurs. Les méthodes ne mesurent pas toutes le même objet.

Pour `n > 1`, `T_log` est négatif si `d < 4`, nul si `d = 4`, et positif si `d > 4`. `n` change l’amplitude, pas le signe lorsque `d` est fixé. Exemple : `d=3`, `n=256` donne `T_log = -ln(256) ≈ -5,545`.

**Attention au nom `d_crit` :** dans le code, il désigne l’ancre de la classe « criticality », calculée à partir de ses estimateurs. Il ne s’agit pas de la constante de référence 4 et il ne vaut pas automatiquement 4.

## 3. Comment le code passe des 29 sorties à `d`

1. Le code calcule les estimateurs sur chaque flux admissible et chaque portion du paysage. Une série de moins de 50 points est exclue par défaut; certains estimateurs peuvent aussi être indisponibles selon les données.
2. Pour un estimateur, il résume ses valeurs finies sur les flux sélectionnés par une médiane.
3. Pour chaque classe, il prend la médiane des sorties des estimateurs que le code a déclarés « dimensionnels ».
4. Il calcule `T_log` séparément pour chaque estimateur dimensionnel et chaque ancre disponible.
5. Il conserve la dispersion entre estimateurs séparément de l’intervalle bootstrap. Le bootstrap mobile porte sur les positions du paysage; il ne couvre pas tous les biais et ne rend pas les estimateurs indépendants.

Dans v5.3, **21 sorties sur 29 entrent actuellement dans la couche géométrique**. Les 8 autres restent dans le tableau des signatures et la couche relative du pipeline; elles ne sont pas mises à zéro ni supprimées. « Entre dans la formule » décrit le branchement actuel du code, pas une validation universelle de la définition de `d`.

## 4. Les 29 estimateurs, en langage simple

« Direct » signifie que v5.3 fait entrer cette sortie dans sa couche géométrique `d`/`T_log`. L’astérisque indique une approximation du code qui demande une validation théorique ou par domaine avant interprétation comme dimension physique.

| Estimateur (nom exact du code) | Classe v5.3 | Direct dans `T_log` | Lecture simple et précaution |
|---|---|:---:|---|
| `Higuchi` | Saturation | Oui | Estime la rugosité d’une courbe en comparant sa longueur à plusieurs échelles. La plage et la stabilité dépendent de la longueur de série et du choix d’échelles. |
| `DFA` | Saturation | Oui* | Mesure comment les fluctuations résiduelles croissent avec l’échelle; le code convertit l’exposant en `2 − α`. Cette conversion vise une dimension de graphe, pas une règle universelle. |
| `Katz` | Saturation | Oui | Compare la longueur du chemin à son étendue globale. Rapide, mais sensible à l’échantillonnage et à la forme globale. |
| `Hurst` | Référence nulle | Non | Estime la persistance à partir de l’échelle R/S. C’est un exposant, pas une dimension directement interchangeable avec `d`. |
| `SampleEn` | Référence nulle | Non | Estime à quelle fréquence des motifs similaires restent similaires quand on ajoute un point. Dépend du seuil de similarité et de la longueur. |
| `Petrosian` | Saturation | Oui | Utilise le nombre de changements de signe de la pente discrète pour approximer la rugosité. Une seule statistique ne décrit pas toutes les échelles. |
| `Sevcik` | Saturation | Oui | Estime la dimension d’une courbe à partir de sa longueur après normalisation des axes. La normalisation influe sur la lecture. |
| `BoxCounting` | Saturation | Oui | Compte les cases occupées pour plusieurs tailles de grille. La pente n’est fiable que s’il existe une vraie plage d’échelles. |
| `PermutationEntropy` | Saturation | Non | Mesure la diversité des motifs d’ordre dans la série; le résultat est une entropie normalisée, pas une dimension. |
| `CorrelationD2` | Criticalité | Oui* | Estime la pente d’une somme de corrélation en fonction du rayon dans un espace reconstruit. Dans le code, cette variante n’applique pas la fenêtre d’exclusion temporelle. |
| `GrassbergerProcaccia` | Criticalité | Oui* | Variante de `D2` qui exclut les voisins trop proches dans le temps (fenêtre de Theiler). Elle partage la même famille et les mêmes limites que `CorrelationD2`; ce ne sont pas deux preuves indépendantes. |
| `InformationD1` | Criticalité | Oui* | Estime la croissance de l’entropie de Shannon quand la résolution des cases augmente dans l’espace reconstruit. Sensible aux échelles et à l’occupation des cases. |
| `VisibilityGraph` | Criticalité | Oui* | Transforme la série en graphe de visibilité, puis déduit une dimension proxy de la distribution des degrés. La relation appliquée suppose une classe de signaux particulière. |
| `TwoNN` | Criticalité | Oui* | Estime la dimension intrinsèque à partir du rapport entre la distance au premier et au deuxième voisin. Le code l’applique à un plongement temporel et peut retourner « indisponible » si le nuage n’est pas identifiable. |
| `DANCo` | Criticalité | Oui* | Combine un estimateur local de voisins avec une information d’angle. La version du code est une approximation allégée, pas l’algorithme DANCo complet publié. |
| `Fisher` | Criticalité | Oui* | Le code calcule une dimension effective par participation des valeurs propres de la covariance inverse. Ce n’est pas directement l’information de Fisher de Frieden. |
| `LevinaBickel` | Divergence | Oui* | Estimateur de dimension intrinsèque par distances aux voisins proches. Sensible au nombre de voisins, au plongement et à la densité d’échantillonnage. |
| `PCAIntrinsic` | Divergence | Oui* | Dans le code, c’est le ratio de participation des valeurs propres d’un plongement PCA. Le code calcule aussi un compte à 95 %, mais la sortie transmise à `T_log` est le ratio de participation. |
| `LocalPCA` | Divergence | Oui* | Compte localement les composantes nécessaires pour expliquer 95 % de la variance. Dépend du voisinage et de la coupure à 95 %. |
| `GraphDimension` | Divergence | Oui* | Mesure la croissance de grappes sur un graphe k plus proches voisins, par nombre de sauts. C’est une pente de graphe, pas la dimension de l’espace d’origine garantie. |
| `PersistentHomology` | Divergence | Oui* | Le code suit la fusion des composantes connexes H0 avec l’échelle et estime une pente. Il s’agit d’un proxy autonome, pas d’un calcul complet de tous les groupes d’homologie. |
| `MFA` | Divergence | Oui* | Le code sépare le nuage en groupes, calcule une PCA locale et garde la dimension locale maximale à 95 %. Cette approximation n’est pas un modèle complet de mixture factor analysis. |
| `KolmogorovLZ` | Divergence | Non | Compte les motifs nouveaux dans une suite discrétisée (proxy LZ76). Ce compte de complexité dépend de la longueur et n’est pas une dimension de Hausdorff. |
| `SpectralBeta` | Référence nulle | Non | Estime la pente du spectre de puissance, souvent décrite par `P(f) ∝ f^-β`. C’est une signature spectrale, pas une dimension. |
| `SpectralDimension` | Référence nulle | Oui* | Le code transforme la pente par `d = (5 − β)/2` et l’admet dans `T_log`. Cette correspondance est un choix du projet à valider pour chaque domaine. |
| `Hurst2mH` | Saturation | Oui* | Calcule `2 − H` à partir de l’exposant R/S. La relation avec une dimension de graphe dépend du type de processus et de ses hypothèses. |
| `Lyapunov` | Référence nulle | Non | Estime la vitesse de séparation de trajectoires voisines reconstruites. C’est un taux de stabilité dynamique, pas une dimension. |
| `MultifractalDeltaAlpha` | Référence nulle | Non | Mesure la largeur du spectre multifractal estimé. Une largeur n’est pas directement un `d` comparable à 4. |
| `SingularityFmax` | Référence nulle | Non | Prend le maximum du spectre `f(α)` estimé. C’est un résumé multifractal, pas une dimension directement branchée sur `T_log`. |

### Pourquoi ne pas moyenner aveuglément les 29 ?

Les sorties ont des définitions, unités mathématiques et sensibilités différentes. Certaines partagent aussi les mêmes données ou familles d’algorithmes : par exemple `CorrelationD2`/`GrassbergerProcaccia`, `Hurst`/`Hurst2mH`, ou les méthodes PCA. Le nombre 29 ne signifie donc ni 29 mesures indépendantes, ni 29 dimensions commensurables. Le pipeline garde des sorties et des classes séparées; une règle de combinaison globale n’est pas encore définie.

## 5. Une analyse reproductible, étape par étape

1. Écrire la question : qu’est-ce qui change et qu’est-ce qui est mesuré ?
2. Nommer exactement l’axe de contrôle et les flux; vérifier leur ordre et leurs unités.
3. Vérifier la quantité de données. Le seuil par défaut est 50 valeurs, mais cela ne garantit pas que chaque estimateur soit fiable.
4. Choisir la signification de `n` et la consigner : nombre de lignes, nombre de blocs indépendants, nombre de sites, etc. Ne pas comparer deux `T_log` sans lire cette étiquette.
5. Choisir la méthode pour `d` : estimateur individuel ou médiane d’une classe. Conserver les valeurs individuelles et la dispersion.
6. Vérifier la stabilité avec plusieurs longueurs, blocs, tailles et graines; comparer à un modèle nul et à une référence connue du domaine.
7. Décrire `T_log` comme un indicateur proposé. Pour affirmer une transition physique, utiliser en parallèle les observables et analyses validées pour ce domaine.

## 6. Ce que les tests actuels disent — et ne disent pas

- Le test Ising classique valide des mesures thermodynamiques dédiées et un ajustement de taille finie Binder autour de la référence connue. Cela valide le simulateur et le protocole physique testés, pas automatiquement `T_log`.
- Les essais de sensibilité montrent que certaines ancres (notamment divergence) dépendent fortement de la longueur bootstrap et des réglages. Une fenêtre plus grande qui donne un intervalle plus étroit n’est pas, à elle seule, un meilleur choix.
- Le nouvel essai d’Ising quantique compare le pipeline à un modèle avec champ transverse et transition quantique. Il vérifie l’intégration sur un second domaine, pas une universalité démontrée.
- Le criblage synthétique des 29 estimateurs montre que plusieurs méthodes suivent des cibles connues dans des cas simples, mais que les dimensions d’attracteur divergent nettement quand la dimension augmente. Il montre aussi qu’une sortie finie n’est pas forcément juste. Voir [le rapport de calibration](calibration_29/RAPPORT_CALIBRATION.md).
- Une correction de méthode a été apportée au criblage : `PCAIntrinsic` et `Fisher` donnent des ratios de participation, et ne peuvent pas être évalués contre le rang `2k` sans autre justification. Les garder séparés évite d’appeler « échec » une comparaison qui ne vise pas la quantité calculée.
- Une lecture unique de `d` masque des objets différents : rugosité du graphe, dimension intrinsèque d’un attracteur, rang effectif ou dimension spectrale. Le [contrat provisoire de `d`](CONTRAT_D_TLOG_ET_CALIBRATION.md) propose de les étiqueter séparément avant de les comparer au seuil 4.
- La règle qui transformerait les quatre ancres en une tension globale unique n’est pas formalisée. Les sorties doivent donc rester un profil avec leurs incertitudes.

## Repères

- Formule théorique source : `TLog.txt`.
- Taxonomie code/théorie et points de désaccord : [MATRICE_29_ESTIMATEURS_TLOG.md](MATRICE_29_ESTIMATEURS_TLOG.md).
- Essais Ising classique : `ising_classique_test/finite_size/`.
- Essai Ising quantique : `ising_quantique_test/`.
- Calibration des 29 estimateurs : [calibration_29/RAPPORT_CALIBRATION.md](calibration_29/RAPPORT_CALIBRATION.md).
- Contrat de travail pour `d` et la référence 4 : [CONTRAT_D_TLOG_ET_CALIBRATION.md](CONTRAT_D_TLOG_ET_CALIBRATION.md).
- Taxonomie exacte `d_kind` de v5.8 : [D_KIND_TAXONOMIE_V5_8.md](D_KIND_TAXONOMIE_V5_8.md).
- Profils TLog typés sur les paysages Ising archivés : [rapport v5.8](tlog_d_kind_v58_results/RAPPORT_RELECTURE_ISING_V58.md).
