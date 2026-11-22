# Protocole gelé — sensibilité synthétique aux transitions V2

**Version :** 1.0  
**Date :** 22 novembre 2026  
**Statut :** expérience logicielle synthétique; aucune donnée clinique  
**Cœur prévu :** UNIVERSAL_LOG v6.0.1, inchangé  
**Cible fixe :** `signal_primary`  
**Contrôles :** chaque colonne numérique de mesure, exécutée séparément

## 1. Question

Comment les sorties du pipeline complet changent-elles lorsque le même plan de mesures simulé contient un signal nul, faible ou fort, lorsque le nombre de points varie, et lorsque différentes colonnes numériques sont choisies comme contrôle?

Cette campagne teste le comportement analytique du pipeline sous des conditions construites. Elle ne cherche pas à prédire une maladie ni à sélectionner un traitement.

## 2. Hypothèses de travail — avant exécution

- **H1, comportement du signal :** les sorties continues du pipeline sur l’axe temporel peuvent différer entre les conditions nulles, faibles et fortes. Aucune relation monotone entre amplitude injectée et sortie n’est présumée.
- **H2, choix d’axe :** les sorties peuvent varier avec le contrôle choisi. Les cinq axes restent séparés dans les résultats; une différence entre axes ne sera pas qualifiée d’erreur sans vérité de référence définie pour cet axe.
- **H3, données nulles :** le pipeline peut encore produire une position T0 sans transition injectée. La disponibilité d’un T0 sera rapportée comme disponibilité de sortie, sans la convertir en taux de fausses alertes, car aucune règle d’alarme n’est préspécifiée.
- **H4, taille de série :** les résultats à 64 et 100 points documenteront la configuration présente; ce plan ne suppose pas que 100 points donnent une meilleure estimation.

Ces énoncés sont des hypothèses exploratoires, pas des résultats.

## 3. Générateur et plan fixé

Le signal latent est une logistique centrée à 58 % de la série. Le bruit indépendant du flux cible a un écart-type de 1. Les amplitudes de plateau choisies sont 0, 0,5 et 1,5 écart-type de bruit : `null`, `weak` et `strong`. Les amplitudes sont des niveaux d’essai synthétiques, sans calibration biologique.

Le plan complet comprend **7 entrées** et **35 appels de pipeline** :

| Longueur | Amplitude | Graines | Réplicats d’entrée | Contrôles par entrée | Appels |
|---:|---|---|---:|---:|---:|
| 64 | nulle (0) | 20261123, 20261124 | 2 | 5 | 10 |
| 64 | faible (0,5) | 20261123 | 1 | 5 | 5 |
| 64 | forte (1,5) | 20261123, 20261124 | 2 | 5 | 10 |
| 100 | nulle (0) | 20261125 | 1 | 5 | 5 |
| 100 | forte (1,5) | 20261125 | 1 | 5 | 5 |

Les cinq colonnes numériques tournées en contrôle sont `time_index`, `signal_primary`, `marker_correlated`, `marker_oscillatory` et `noise_independent`. `case_id`, `sample_key` et `condition_label` sont catégoriels; l’étiquette de la condition est relue depuis le CSV pour vérifier qu’elle ne devient pas une colonne numérique vide. Chaque appel reçoit un seul CSV, une seule trajectoire et un contrôle; aucune ligne de plusieurs trajectoires n’est concaténée.

`marker_correlated` est construit à partir du flux cible et d’un bruit résiduel. Cela crée une dépendance statistique par construction; cela ne représente ni causalité ni biomarqueur. `marker_oscillatory` combine une sinusoïde et une petite composante latente puis du bruit. Il est conservé comme contrôle candidat même s’il n’est pas monotone. `noise_independent` est généré séparément.

## 4. Configuration du cœur

- Entrée complète `run_full_unified_pipeline` de v6.0.1; le fichier source du cœur reste inchangé et son SHA-256 est enregistré.
- Mode `fast`, `n_scenarios=8`, un worker, validation harmonique désactivée, L7b `light`, contrôle `single`, cible fixe `signal_primary`, domaine `generic`.
- Graine de calcul du cœur déterminée par la graine de l’entrée et l’index du contrôle; chaque graine est inscrite au manifeste d’exécution.
- Le contrôle sélectionné doit être absent des flux analysés de son appel.
- Quand `signal_primary` est le contrôle, le repli diagonal déclaré par v6.0.1 est conservé et signalé; ces sorties ne sont pas traitées comme comparables aux autres contrôles pour les champs dépendant de la cible.

## 5. Mesures rapportées

Pour chaque appel, le harnais conserve l’état d’axe et de monotonie, T0, les sorties de cascade, les groupes Q, les valeurs TLog par classe, les sorties de dérivées et F1/F2, les 29 estimateurs déclarés, les figures et les journaux natifs du pipeline.

L’écart absolu entre T0 retourné et le centre injecté de 58 % est calculé **uniquement pour `time_index` et les conditions avec transition**. Il est rapporté de façon descriptive, sans seuil de réussite arbitraire. Les axes mesurés ont leurs propres propriétés; aucune valeur vraie de T0 commune à ces axes n’est postulée.

Pour la condition nulle, le harnais rapporte si une sortie T0 est disponible et son statut. Il ne calcule pas de taux de faux positifs. Aucun critère d’alarme, p-value ou règle d’abstention n’est ajouté à la théorie dans cette campagne.

## 6. Critères d’intégrité technique préétablis

Le statut technique `passed` exige : (1) sept CSV attendus et déterministes; (2) 35 appels prévus terminés sans exception; (3) chaque entrée exécutée avec les cinq contrôles; (4) contrôle exclu des flux analysés; (5) 29 estimateurs déclarés dans chaque sortie complète; (6) contrôle cible diagonal explicitement replié; (7) contrôle oscillatoire exécuté et conservé; (8) entrées de 64 ou 100 lignes transmises individuellement au cœur. Ces critères vérifient le protocole et le câblage; ils ne notent pas l’exactitude des estimations.

## 7. Limites préétablies

- Les niveaux d’amplitude, graines, longueurs et formes de flux sont des choix de conception synthétique.
- Les réplicats sont trop peu nombreux pour une estimation fiable de distributions ou une généralisation statistique.
- Il n’existe pas de vérité de transition unique pour le contrôle oscillatoire ou pour chaque flux pris comme axe.
- Le test ne valide pas TLog, la théorie générale, une relation causale, une application PDAC ou une utilité clinique.
- Les données cliniques, biologiques et patient sont exclues.

Tout écart de couverture ou résultat inattendu sera consigné avant interprétation. Les observations resteront séparées des hypothèses et des décisions de portée.
