# T_log — fiche théorie courte

*Version de travail destinée à des lecteurs qui découvrent le sujet. Elle résume `TLog.txt` et distingue les propositions théoriques de ce que calcule actuellement le code v5.3.*

## 1. L’idée en une phrase

T_log est proposé comme un indicateur de régime : il compare une dimension effective estimée `d` à une dimension de référence `d_crit = 4`, en tenant compte de la taille `n` des données.

## 2. La formule

```text
T_log(n, d) = (d - 4) × ln(n)
```

- `n` : l’échelle choisie pour la question. Cela peut être le nombre d’observations, le nombre d’observations indépendantes estimé, ou la taille physique du système. Il faut nommer cette échelle avec chaque résultat.
- `d` : la dimension choisie pour cette lecture. Elle peut venir d’un estimateur précis ou d’une ancre définie à partir de plusieurs estimateurs. Il faut indiquer la méthode et la règle d’agrégation; les 29 méthodes ne sont pas interchangeables.
- `4` : la dimension critique de référence proposée par la théorie.
- `ln` : le logarithme naturel, comme dans le code.

Pour un `d` fixé et `n > 1`, le signe vient de `d - 4`: négatif si `d < 4`, nul si `d = 4`, positif si `d > 4`. `n` modifie l’amplitude. Exemple : avec `d = 3,5`, `T_log ≈ -2,30` pour `n = 100` et `≈ -4,61` pour `n = 10 000`. En pratique, l’estimation de `d` peut elle-même changer quand on change la taille ou la longueur des données; il faut donc préciser les deux choix.

## 3. Les 29 estimateurs : plusieurs instruments, pas 29 vérités identiques

Un estimateur est une méthode de mesure. Les 29 méthodes sont des « loupes » différentes : elles peuvent être en désaccord parce qu’elles ne mesurent pas exactement la même propriété. La théorie propose de conserver cet écart et de l’étudier au lieu de le réduire automatiquement à une moyenne.

Dans le code v5.3, les 29 estimateurs sont répartis en quatre classes : saturation (8), criticité (7), divergence (7) et référence nulle (7). Le code branche 21 sorties sur la couche géométrique de T_log. Cela décrit son implémentation actuelle : plusieurs sorties sont des approximations ou des proxys dont l’interprétation comme dimension doit encore être validée par domaine. Les 8 autres — par exemple l’entropie, l’exposant de Lyapunov ou la pente spectrale — restent des signatures dans la couche relative; elles ne sont pas traitées comme des dimensions dans la formule.

La référence nulle est proposée comme un contrepoids indépendant. Cette indépendance est une hypothèse à vérifier sur les données, pas une garantie donnée par son nom.

## 4. Ce que les régimes veulent dire — et ce qu’il reste à démontrer

- **Saturation (`d < 4`, T_log négatif)** : régime de structure plus stable ou contrainte.
- **Criticité (`d ≈ 4`, T_log près de zéro)** : régime de transition proposé.
- **Divergence (`d > 4`, T_log positif)** : régime de complexité croissante ou d’instabilité proposée.

Les mots « énergie confinée », « libérée » ou « chaos » sont des interprétations théoriques. La formule seule ne mesure ni l’énergie ni le chaos et ne prouve pas qu’une transition physique a eu lieu.

La triangulation doit conserver les ancres de saturation, criticité, divergence et référence nulle, avec leurs incertitudes. `TLog.txt` décrit une tension vectorielle plutôt qu’une moyenne, mais ne donne pas encore une règle mathématique unique pour convertir ce vecteur en tension globale finale.

## 5. Ce que les tests ont établi jusqu’ici

Le test Ising classique confirme que le simulateur et les mesures thermodynamiques de taille finie sont cohérents avec leurs références sur le jeu étudié. C’est un bon contrôle physique. Il ne démontre pas encore que T_log, la référence `4` ou les 29 estimateurs ont la même interprétation dans tous les domaines.

La chaîne d’Ising quantique transverse a aussi été simulée par diagonalisation exacte pour `N=8, 10, 12`. Les pics physiques se rapprochent de `g_c=1`, tandis que l’ancre `criticality` de `T_log` reste autour de `d≈0,96`; le pipeline s’exécute sur ce second domaine, mais ne détecte pas `g_c` avec cette lecture. C’est un test d’intégration, pas une preuve d’universalité. Voir [le rapport Ising quantique](ising_quantique_test/RAPPORT_ISING_QUANTIQUE.md).

Pour chaque estimateur et pour T_log, il faut vérifier la stabilité quand on change la longueur des séries, le bruit, les unités, l’échantillonnage et les paramètres. Les résultats doivent aussi être comparés à des données de référence et à des modèles nuls.

## 6. Rendre chaque calcul comparable

Une analyse peut produire plusieurs lectures de T_log, par exemple une par échelle `n` et par définition de `d`. Il faut garder ces résultats étiquetés séparément; on ne les mélange pas et on ne les moyenne pas sans règle théorique explicite.

Pour chaque résultat, noter : le type et la valeur de `n`, l’estimateur ou l’ancre définissant `d`, la règle d’agrégation s’il y en a une, les flux analysés, et l’incertitude. Pour comparer deux domaines, comparer des lectures ayant la même définition, ou expliquer explicitement pourquoi des définitions différentes sont mises en regard.

Dans le code v5.3, `n` vaut par défaut le nombre de lignes du tableau. On peut fournir plusieurs échelles étiquetées dans la même analyse, par exemple `--tlog-scale observations=105 --tlog-scale system_size=4096`. La couche géométrique utilise les estimateurs définis comme dimensionnels et forme des ancres par classe. C’est une configuration concrète du cadre; la théorie peut en autoriser d’autres si elles sont nommées et testées. Ces médianes résument chaque classe; le pipeline affiche donc aussi la dispersion entre estimateurs. Il calcule un intervalle bootstrap par blocs sur les positions de progression, avec une longueur de bloc dérivée de la fenêtre d’analyse. Cet intervalle décrit la variabilité du paysage observé; il ne couvre pas tous les biais des estimateurs, et `n` est traité comme une valeur fixe.

La règle mathématique finale qui transformerait le vecteur des ancres en une tension globale unique reste à formaliser. La fiche conserve donc le vecteur et les écarts observés sans inventer de formule de combinaison.

Il existe un écart de nomenclature à arbitrer entre `TLog.txt` et le code : le document source cite `Hurst` dans deux classes et ne cite pas `SpectralDimension`; le code distingue `Hurst` de `Hurst2mH` et classe `SpectralDimension` séparément. Le guide décrit les noms exacts de la version v5.3 et garde cette décision théorique ouverte.

Pour une explication accessible des 29 estimateurs, de leurs limites et d’un protocole d’analyse, voir le [guide débutant Universal Log](GUIDE_DEBUTANT_UNIVERSAL_LOG.md). Pour le détail des rôles et des écarts entre la théorie écrite et le code, voir [la matrice des 29 estimateurs](MATRICE_29_ESTIMATEURS_TLOG.md).
