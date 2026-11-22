# Protocole V1 — distinguer phénomène, mesure et calcul

**Statut :** règle méthodologique proposée pour les prochains essais V12. Elle n’a pas encore été validée par des tests comparatifs sur plusieurs domaines.

## Question posée avant l’analyse

Déclarer le but avant de regarder le résultat :

- **Analyse descriptive :** décrire la structure d’un ensemble de flux et l’effet du choix d’axe/contrôle. Une sortie T0/TLog est une propriété de cette configuration tant que son origine n’est pas établie.
- **Prédiction :** estimer une cible définie indépendamment, avec séparation temporelle ou par groupe, référence de comparaison et métriques fixées avant calcul. Les flux qui ne seraient pas disponibles au moment réel de la prédiction sont exclus ou signalés.

Ces deux questions ont des entrées, comparateurs et critères distincts; une bonne prédiction classique ne valide pas à elle seule la théorie complète du pipeline, et une structure descriptive ne prouve pas une capacité prédictive.

## Trois explications concurrentes pour un seuil

Pour chaque seuil ou changement candidat, examiner au minimum :

1. **Phénomène visé :** changement de la cible ou du système d’intérêt.
2. **Mesure et collecte :** capteur, analyseur de référence, unité, étalonnage, limite physique, saturation, changement d’appareil/de lot, disponibilité, horodatage, agrégation ou journal de collecte.
3. **Préparation et calcul :** sentinelles manquantes, transformations, choix de flux, axe/contrôle, binning, estimateurs, version, graines et règles de décision.

Ces explications peuvent coexister. Si les métadonnées ou contrôles ne permettent pas de les séparer, inscrire **origine indéterminée**; ne pas attribuer automatiquement le seuil au phénomène, au capteur, ni à une cause biologique. Un coïncidence temporelle ou une valeur à la borne n’identifie pas sa cause.

## Plan minimal de contrôles

- Dresser le schéma des flux : cible, mesures instrumentales, références indépendantes, covariables, journaux de collecte et variables construites. Étiqueter les variables construites comme telles.
- Faire tourner chacun des axes/contrôles admissibles selon un plan gelé; enregistrer aussi les axes non monotones, refusés ou insuffisamment couverts. Vérifier à chaque fois que le contrôle est retiré des flux analysés et consigner tout repli de cible.
- Auditer avant interprétation les unités, bornes, valeurs répétées, sentinelles, lacunes, doublons, changements de protocole et disponibilité par flux. Comparer capteurs entre eux et à la référence indépendante lorsque ces données existent.
- Utiliser des contrôles négatifs, permutations ou simulations correspondant à la question, et répéter sous des préparations raisonnables préspécifiées. Une différence entre contrôles est un résultat à rapporter, pas une permission de ne retenir que le contrôle favorable.
- Conserver empreintes des sources, entrées, code, configuration, journaux, résultats et raisons des changements. Séparer résultats préspécifiés et explorations post hoc.

## Vocabulaire de compte rendu

Employer des étiquettes distinctes : **observation des données**, **sortie du logiciel**, **hypothèse explicative**, **résultat robuste aux contrôles prévus**, **interprétation de domaine**. Ne promouvoir une hypothèse au statut de résultat que si le test correspondant a été effectivement exécuté et si les explications concurrentes ont été examinées.

