# Protocole du banc d'essai synthétique à vérité connue — v1

**Statut :** plan pré-exécutable. Aucun résultat de ce protocole n'est inclus dans le rapport Ising v6.0.  
**Version évaluée :** geler le fichier pipeline, les paramètres et leurs empreintes avant le lot confirmatoire.  
**But :** caractériser les réponses et limites de la chaîne complète, pas démontrer l'universalité par quelques exemples choisis.

## 1. Questions de validation

1. Le pipeline place-t-il T0 près d'un événement connu quand un événement existe et que l'axe possède une conversion définie?
2. Que renvoie-t-il sur une série stable sans transition, une dérive lente ou un bruit autocorrélé?
3. Quelles couches réagissent aux flux redondants, dérivés, indépendants, décalés ou non liés?
4. Les sorties restent-elles traçables quand le contrôle est non monotone, identique à la cible, constant ou manquant?
5. Comment évoluent la couverture des 29 estimateurs, Q1–Q6, F1/F2, Voie 1/2, TLog, L7a/L7b et les statuts de sortie quand le nombre de lignes diminue?

Le banc teste d'abord l'implémentation. Il ne transforme pas une réponse synthétique en conclusion biologique ou clinique.

## 2. Bibliothèque de générateurs proposée

Chaque générateur reçoit un paramètre de transition ou l'étiquette `aucun`, un niveau de bruit et une graine. Son fichier `truth.json` décrit le point exact de génération, les relations entre flux et les paramètres. Ce fichier reste séparé du CSV donné au pipeline jusqu'à l'étape de notation.

| Famille | Cas à générer | Vérité terrain et but |
|---|---|---|
| Transition abrupte | Marche avec position et amplitude réglables. | Vérifier si T0 se place près du changement imposé. |
| Transition graduelle | Sigmoïde avec position et largeur contrôlées. | Mesurer erreur et effet de la largeur; ne pas exiger un point unique si la transition est diffuse. |
| Changement de dynamique | AR(1) stable puis coefficient qui approche 1 avant/après un point déclaré. | Tester l'autocorrélation et la stabilité, sans appeler chaque hausse d'AR(1) une criticité universelle. |
| Oscillation | Apparition d'une composante oscillatoire ou changement d'amplitude/fréquence. | Vérifier un changement connu d'un autre type que le saut; préciser ce qui constitue l'événement. |
| Nul stationnaire | Bruit blanc, AR(1) stationnaire sans changement, et bruit coloré généré avec paramètres conservés. | Évaluer les seuils que le pipeline produit en absence d'événement et la règle pré-déclarée d'alerte/abstention. |
| Confusion temporelle | Dérive lente sans rupture, changement de variance seul, ou tendance déterministe sans changement de régime. | Tester les faux repérages dus à une tendance ou à l'échelle. |
| Relations de flux | Copie exacte, transformation affine, flux corrélé, flux décalé, bruit indépendant et flux sans relation. | Mesurer les changements de couverture et de sortie; distinguer redondance de réplication indépendante. |
| Axes de contrôle | Axe monotone croissant, décroissant, non monotone, constant et contrôle=cible. | Vérifier rang, valeur brute, conversion ambiguë et statut diagonal. |
| Longueur | N=7, 15, 30 et 76 comme stress de courte série, plus longueurs choisies lors du pilote. | Mesurer calculabilité et abstention. N=7/15 imite le faible nombre de points temporels; ne présume pas une estimation fractale fiable. |

Un plan factoriel complet peut coûter cher. Le protocole doit d'abord couvrir les cas de base et les interactions pré-déclarées, puis ajouter les combinaisons selon un plan documenté. Aucun sous-ensemble choisi après lecture des sorties ne devient confirmatoire.

## 3. Plan de séparation entre développement et confirmation

### Lot pilote technique

- Vérifier que les générateurs produisent bien la vérité décrite dans `truth.json`.
- Vérifier l'import, le schéma, le temps d'exécution, les erreurs et les statuts de sortie.
- Utiliser des graines dédiées au pilote; leurs résultats servent à corriger le banc et ne comptent pas dans les estimations confirmatoires.
- Consigner toute modification du générateur, du pipeline ou du contrat comme une nouvelle version.

### Lot confirmatoire

- Geler code source, protocole, configuration, versions des dépendances et empreintes SHA-256.
- Utiliser des graines réservées, invisibles lors du développement des paramètres.
- Fournir au pipeline le seul CSV d'entrée; garder les étiquettes de transition et relations vraies dans un dossier de notation séparé.
- Choisir le nombre de réplications pour une précision visée des intervalles avant le lot confirmatoire. Ne pas choisir ce nombre après avoir vu les estimations.
- Conserver les succès, échecs, avertissements, NaN et sorties indéterminées. Rapporter les dénominateurs pour chaque statistique.

## 4. Mesures à calculer

### Localisation et faux repérages

- Erreur de localisation sur l'axe déclaré, en rang normalisé et dans l'unité brute seulement si la conversion est monotone et définie.
- Distribution de T0 entre graines, biais, dispersion et intervalles construits à partir des répétitions.
- Taux de détection manquée et faux positifs, **uniquement après définition indépendante d'une règle de détection ou d'abstention**. Le simple fait que le scan choisisse un T0 ne suffit pas si le code renvoie toujours un maximum.
- Couverture des intervalles et stabilité des classements lorsque la vérité terrain est connue.

### Intégrité de la chaîne

- Couverture des estimateurs et raison de chaque valeur absente (`non estimable`, `non calculé`, `erreur`, `hors profil`).
- Sorties brutes et statuts pour chacune de Q1–Q6 et F1/F2; documenter à l'avance quelles transformations sont attendues pour chaque générateur.
- Voie 1 à côté de chaque ancre de Voie 2, sans moyenne qui efface leur désaccord.
- Valeurs TLog, composantes, conventions et effet de n rapportés ensemble; ne pas traiter une valeur finale comme une preuve autonome.
- Verdict L7b-light et chacun de ses checks; si L7b-full est exécuté, séparer graine, fenêtre, mélange et échelle.
- Sensibilité à l'ajout ou au retrait d'un flux, notamment copie affine, flux indépendant, flux corrélé et flux non lié.

### Contrôles négatifs et cas diagonaux

- Sous les scénarios sans transition, appliquer la règle d'alerte pré-déclarée et estimer son taux de faux positifs avec intervalle.
- Pour contrôle=cible, vérifier acceptation, étiquette diagonale, traçabilité, unités et absence d'affirmation automatique de transition. Ne pas noter ce cas comme une localisation indépendante.
- Pour un axe non monotone, comparer les rangs dans l'ordre déclaré et vérifier que le rapport ne fabrique pas une conversion brute unique.

## 5. Séries courtes et pont éventuel vers le scRNA-seq

Les scénarios N=7 et N=15 sont des tests de **comportement avec peu de points**, pas une démonstration de puissance. Ils doivent vérifier que les estimateurs insuffisamment alimentés sont signalés comme tels, que les dénominateurs ne disparaissent pas et qu'une sortie `indéterminée` reste possible.

Pour un futur essai scRNA-seq, l'unité d'analyse et les réplicats biologiques doivent être déclarés avant agrégation. Les cellules ne sont pas automatiquement des réplicats temporels indépendants. Un jeu à sept temps peut tester la manipulation de colonnes et l'abstention; il ne valide pas, à lui seul, une localisation biologique.

## 6. Précautions spécifiques à l'Ising

- Garder séparés les repères physiques (Tc exact infini, pics de susceptibilité/chaleur spécifique, croisements Binder) et les colonnes visibles par le pipeline.
- Préparer un lot confirmatoire où χ/Cv/Binder sont retirés du CSV transmis au pipeline, puis répliquer avec de nouvelles simulations et graines indépendantes.
- Conserver aussi le CSV riche en flux comme scénario d'interaction; déclarer qu'il n'est pas aveugle aux colonnes de repère.
- Tenir compte du décalage de taille finie : ne pas exiger que chaque pic à L fini soit égal à Tc infini.
- Séparer graines de simulation physique, graines de l'optimiseur et graines de bootstrap/permutation.

L'essai L=64 à deux colonnes déjà réalisé donne T0=2,27, comme le run riche en flux. Parce qu'il a été choisi après les résultats principaux, qu'il est unique et qu'il conserve le signal énergie-température, c'est une observation exploratoire; il ne prouve pas l'absence de fuite ni l'universalité.

## 7. Décisions à pré-déclarer avant confirmation

1. Quelle sortie constitue une alerte et quelle sortie autorise l'abstention?
2. Quelle erreur de localisation est acceptable dans chaque scénario, compte tenu de sa largeur et de l'espacement des points?
3. Quelle couverture d'intervalle et quelle précision des taux d'erreur sont visées?
4. Quels rôles, dépendances de flux et politiques de valeurs manquantes seront testés?
5. Quel mode L7b est le résultat principal, et quels modes ne sont que diagnostics complémentaires?
6. Quelles règles d'interprétation sont générales au pipeline et lesquelles sont propres à l'Ising ou au domaine futur?

Les seuils actuels de L7b sont des conventions de code qui doivent être évaluées comme telles. Le banc ne doit pas les déclarer vrais par le fait qu'un cas passe ou échoue.

## 8. État du travail

Ce document définit un protocole proposé; les générateurs, critères chiffrés et exécutions confirmatoires ne sont pas encore réalisés. Les résultats déjà acquis restent ceux des 12 configurations principales et des deux addenda consignés dans `ERRATA_ET_JOURNAL.md`.
