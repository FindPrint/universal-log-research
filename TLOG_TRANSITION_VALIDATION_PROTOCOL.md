# Protocole pilote — pouvoir de détection de TLog v5.8

**Version figée avant calcul :** 1.0 — 8 novembre 2026.  
**Objet :** tester si les profils par d_kind signalent un voisinage de la transition d'Ising 2D. Ce pilote ne constitue pas une validation universelle.

## Données positives

- Mesures de taille finie archivées dans ising_classique_test/finite_size/finite_size_results.csv : L=8,12,16,24,32,48,64, T=1.90..2.65, pas 0.01.
- Entrée TLog : courbe d'énergie par spin en fonction de T, sans injecter la susceptibilité utilisée pour définir le marqueur cible.
- Marqueur physique principal : température du pic de susceptibilité connectée à |m| pour chaque L; comparer la localisation à son intervalle bootstrap à 95 %, élargi d'un pas de grille de chaque côté.
- L=8 est exclu du décompte de localisation : son intervalle de pic touche la limite supérieure de la plage étudiée. Sa sortie reste dans les données descriptives.
- Référence secondaire commune : Tc=2.269185314...; le décalage des pics avec L est un effet de taille finie.

## Fenêtres et règle TLog

- Deux fenêtres centrées, impaires, de w=31 et w=41 points; elles couvrent respectivement 0.30 et 0.40 en température.
- Toutes les fenêtres intérieures au balayage sont évaluées. L'analyse de référence utilise la valeur par défaut du chemin NumPy de v5.8 et la graine fixe des contrôles nuls 20261108.
- Dans chaque fenêtre, d_kind est la médiane des estimateurs disponibles de ce type, pour la courbe énergie seule. n=w; T_log=(d−4) ln(w).
- Un type a un candidat TLog si au moins un centre atteint |d−4|≤0.5 (bande [3.5, 4.5]). L'estimation de T est le centre où |d−4| est minimal, sans utiliser le marqueur physique pour choisir ce centre.
- Un candidat est localisé si son centre est dans l'intervalle bootstrap du pic de susceptibilité élargi de ±0.01.
- Chaque d_kind reste évalué séparément. Une valeur absente est indisponible; aucun repli n'est utilisé. Couverture minimale d'un type : 80 % des centres.

## Contrôles négatifs sans transition

- Deux niveaux de bruit sont pris des erreurs-types d'énergie archivées pour L=16 et L=64.
- Pour chaque niveau, 10 courbes quadratiques lisses sont générées sur le même axe T, ajustées au balayage énergétique observé, puis perturbées par un bruit gaussien indépendant avec l'erreur-type ponctuelle fournie.
- Ces courbes n'ont ni cuspide ni point critique. Neuf fenêtres réparties sur l'axe sont évaluées pour chaque réalisation et chaque largeur; une fausse alerte survient si un type atteint la bande [3.5,4.5] dans au moins une de ces fenêtres.
- Il y a 40 balayages nuls au total (2 niveaux de bruit × 10 réalisations × 2 fenêtres). Le taux familial compte une alerte si au moins un type la déclenche.

## Critère de criblage annoncé

Un d_kind ne sera qualifié de **candidat pilote** que s'il satisfait toutes les conditions :

1. couverture d'au moins 80 %;
2. localisation dans l'intervalle physique pour au moins 4 des 6 tailles évaluables (L=12..64), pour chacune des deux largeurs;
3. taux familial de fausses alertes ≤10 % sur les 40 balayages nuls;
4. écart médian entre les T prédites par w=31 et w=41 ≤0.05 sur les tailles détectées.

Le seuil 0.5, la tolérance de localisation et ces critères sont des seuils de criblage choisis avant le calcul; ils ne sont pas des résultats théoriques. Les taux nuls (40 réalisations) sont exploratoires et n'offrent pas une borne précise sur les probabilités très faibles.

## Limites

Le signal fourni à ces estimateurs est une courbe quasi-statique d'équilibre en fonction de la température, pas une trajectoire temporelle. Les d_kind de dimension d'attracteur, de voisinage ou de dynamique sont donc inclus dans le test de transfert de TLog, mais une valeur produite ne suffit pas à établir qu'ils sont applicables à cette question. La simulation fournit trois chaînes regroupées par température; l'incertitude des courbes physiques n'est pas propagée aux estimations dimensionnelles locales dans cette version du pilote.

Le rapport final doit séparer : (a) résultats physiques, (b) détection TLog par type, (c) fausses alertes sur les courbes lisses, (d) indisponibilités et limites d'applicabilité.
