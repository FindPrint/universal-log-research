# Contrat de lecture de `d` dans T_log

**Statut : contrat opérationnel de travail.** Les principes valent pour le pipeline; la taxonomie précise mise en œuvre dans v5.8 est détaillée dans [D_KIND_TAXONOMIE_V5_8.md](D_KIND_TAXONOMIE_V5_8.md). Elle clarifie les sorties sans modifier la formule ni la théorie source.

## 1. Ne pas appeler toutes les sorties « la dimension »

Le symbole `d` n'a de sens qu'avec l'objet mesuré. Pour éviter de comparer des quantités différentes sous le même nom, chaque résultat devrait enregistrer un `d_kind`, une méthode, son domaine d'application, ses paramètres et son incertitude.

| Type conseillé | Objet mesuré | Méthodes v5.3 concernées | Référence possible |
|---|---|---|---|
| `D_graph` | Rugosité de la courbe `(temps, signal)`; souvent liée à `2-H` pour un mouvement fractionnaire | `Higuchi`, `Katz`, `Petrosian`, `Sevcik`, `BoxCounting`; `DFA` et `Hurst2mH` après transformation; `VisibilityGraph` seulement sous son modèle de signal | Dimension du graphe de la trajectoire génératrice, avec hypothèses explicites; pour un fBm, `2-H` |
| `D_attractor` | Dimension d'un attracteur reconstruit par plongement retardé | `CorrelationD2`, `GrassbergerProcaccia`, `InformationD1`, `TwoNN`, `DANCo`, `LevinaBickel`; parfois `LocalPCA` sous forme locale | Dimension latente connue du système et plongement assez grand, assez dense et validé |
| `D_linear_eff` | Nombre effectif de directions de variance dans un nuage plongé | `PCAIntrinsic`, `Fisher`, `LocalPCA`; `MFA` pour son maximum par groupe | Participation des valeurs propres ou nombre de composantes selon la règle exacte; ce n'est pas automatiquement une dimension de variété |
| `D_scaling_proxy` | Pente d'une relation d'échelle construite par l'algorithme | `GraphDimension`, `PersistentHomology`; certains `D2` et `D1` selon leurs plages d'échelle | Données simulées dont la géométrie et les plages d'échelle sont connues |
| `D_spectral` | Dimension déduite d'une loi spectrale spécifique au domaine | `SpectralDimension = (5-β)/2` dans le code | Modèle spectral du domaine qui justifie précisément cette transformation |
| `signature` | Entropie, persistance, complexité, exposant dynamique ou largeur multifractale | `Hurst`, `SpectralBeta`, `SampleEn`, `PermutationEntropy`, `Lyapunov`, `KolmogorovLZ`, `MultifractalDeltaAlpha`, `SingularityFmax` | Référence propre à la signature; ne pas injecter directement dans `d` sans nouvelle définition |

Cette table est une classification pratique, pas une déclaration que chaque méthode d'une ligne estime correctement la quantité. Par exemple, `DANCo` et `MFA` sont des approximations simplifiées dans le code; `Fisher` et `PCAIntrinsic` sont des ratios de participation; `PersistentHomology` est un proxy H0; `VisibilityGraph` suppose une relation reliant exposant de degré et rugosité. Il faut calibrer ces versions exactes, pas seulement le nom d'une méthode publiée.

## 2. Quand la référence 4 est-elle interprétable ?

La formule reste `T_log=(d-4) ln(n)`, mais `4` doit être comparé à un `d` d'un type défini. Un passage par zéro est interprétable seulement si le même `d_kind`, la même procédure et la même convention de `n` sont conservés.

- Pour un `D_graph` de série scalaire, la dimension attendue est habituellement entre 1 et 2. Avec la référence 4, T_log restera alors négatif; cette lecture ne peut pas fournir une transition à `d=4`.
- Pour un `D_attractor`, une référence de 4 peut être testée sur un attracteur de dimension connue 4. Le résultat dépend de l'observation, de l'échantillonnage et d'un plongement suffisant. La borne générique d'embedding par retards est de l'ordre de `2k+1`; le test `k=4` demande donc au moins 9 coordonnées dans le cadre générique, alors que plusieurs estimateurs du code plafonnent à 8.
- Pour `D_linear_eff`, comparer à 4 répond à une question de rang/variance effective; ce n'est pas la même affirmation que « l'attracteur est de dimension 4 ».
- Pour `D_spectral`, la valeur 4 n'est pertinente que si le modèle spectral du domaine donne ce seuil.

La constante 4 est donc une **hypothèse théorique à tester par type et par domaine**, et non une valeur calibrée par les essais effectués ici. Le pipeline devrait conserver des profils séparés, par exemple `T_log(D_graph)`, `T_log(D_attractor)` et `T_log(D_spectral)`, jusqu'à ce qu'une règle de combinaison soit démontrée.

## 3. Contrat minimal pour un résultat reproductible

Chaque profil devrait enregistrer :

1. `d_kind`, méthode exacte et version de l'algorithme;
2. cible ou interprétation théorique de cette méthode;
3. définition de `n` (observations, blocs indépendants, taille physique, etc.);
4. valeur brute de chaque estimateur, valeurs manquantes, paramètres d'échelle/plongement et prétraitement;
5. incertitude d'échantillonnage, biais de calibration connu et dispersion entre méthodes;
6. référence `d_ref=4` comme hypothèse explicite, ou une référence propre au domaine si la théorie la spécifie;
7. résultat des contrôles synthétiques et physiques pour la même version de l'estimateur.

Une médiane de classe peut rester utile comme résumé, mais elle ne rend pas commensurables des estimandes différentes. La médiane ne doit pas effacer les mesures individuelles ni leur type.

## 4. Lecture des tests déjà réalisés

La calibration synthétique de novembre 2026 soutient l'exécution et quelques cas d'usage précis : `Hurst`, la transformation de `DFA`, `Hurst2mH` et `SpectralBeta` suivent assez bien les références fGn testées; `Higuchi` suit les deux dimensions de graphe fBm testées. Plusieurs autres méthodes montrent des biais, des limites de plongement ou une forte dépendance à la série.

Le test Ising classique est un contrôle pertinent des observables physiques et de la mise à l'échelle de taille finie. Le test quantique confirme que le pipeline peut traiter un second problème, mais son ancre de criticité ne repère pas `g_c`. Ces essais vérifient des intégrations séparées; ils ne valident pas encore une valeur universelle de `d=4` ni un détecteur T_log universel.

Les détails, tableaux complets et limites sont dans [le rapport de calibration des 29 estimateurs](calibration_29/RAPPORT_CALIBRATION.md). Les méthodes de dimension intrinsèque par voisins se fondent sur des hypothèses locales de géométrie et d'échantillonnage, comme l'exposent les articles de [Levina et Bickel](https://papers.nips.cc/paper_files/paper/2004/hash/74934548253bcab8490ebd74afed7031-Abstract.html) et de [Facco et al.](https://www.nature.com/articles/s41598-017-11873-y). La relation `D_graph=2-H` est celle du graphe du mouvement fractionnaire sous ses hypothèses, pas un convertisseur universel pour toute série ([référence mathématique](https://www.numdam.org/articles/10.1016/S1631-073X%2803%2900015-3/)).
