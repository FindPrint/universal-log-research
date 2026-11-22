# Protocole gelé — AI4I et UNIVERSAL_LOG, rotation des contrôles

**Date :** 2026-11-22  
**Statut :** défini avant les appels du pipeline; l’exécution n’est pas encore terminée.

## Question

Comment v6.0.1 réagit-il quand chaque colonne numérique de l’AI4I est utilisée à tour de rôle comme axe de contrôle, tandis que la cible reste la proportion de pannes par bloc?

Cette expérience évalue le comportement et la sensibilité du pipeline (niveau 2). Elle n’évalue pas un classifieur, et le jeu est synthétique.

## Source et transformation

- 10 000 lignes ordonnées par UDI dans le CSV original; CSV identique octet pour octet au téléchargement UCI officiel.
- Regrouper les lignes consécutives en **100 blocs égaux de 100 observations**; prendre la moyenne de chaque variable numérique dans chaque bloc.
- La moyenne d’une colonne binaire de panne correspond ici au taux de panne observé dans le bloc.
- Garder toutes les 12 colonnes numériques issues du CSV : UDI, cinq mesures machine, Machine failure et cinq étiquettes de type de panne. Les colonnes catégorielles `Type` et `Product ID` ne sont pas des flux numériques et ne sont pas incluses.
- Cible fixe : `Machine failure` agrégé en proportion (0 à 1).
- Faire une exécution indépendante pour chaque colonne numérique comme contrôle, soit 12 axes, y compris `Machine failure` comme axe diagonal. Le pipeline doit exclure le contrôle sélectionné de ses flux analysés conformément à son comportement documenté.
- L’ordre des blocs est conservé. Les contrôles non monotones restent admissibles et leur statut est rapporté.

## Paramètres et traçabilité

- Code : v6.0.1 `control_flux_exclusion`, SHA-256 consigné au manifeste.
- `mode=fast`, `n_scenarios=8`, `harmonic_validation=False`, `l7b_mode=light`, `target_policy=fixed`, un worker.
- Graine par axe : `20261122 + 100 × index_de_l_axe`.
- Essai sans graphiques par monkeypatch de fonctions de rendu uniquement. Aucune fonction numérique d’analyse n’est modifiée. Sur le jeu synthétique V2 et la même graine, les sorties analytiques ont été comparées récursivement à la sortie complète; elles sont identiques après exclusion des champs d’emplacement et de durée. Cette validation du rendu est limitée au cas comparé.
- Sauvegarder l’entrée agrégée, son hash, le plan des 12 axes, l’état de reprise, les journaux, toutes les sorties JSON de chaque axe, les erreurs et les durées.

## Hypothèses à ne pas confondre avec les résultats

- **Hypothèse H1 :** la rotation peut faire apparaître des seuils descriptifs différents selon le contrôle.
- **Hypothèse H2 :** si les résultats changent quand le contrôle change, cette dépendance peut refléter la construction des axes, les étiquettes de panne agrégées, ou la méthode; elle n’indique pas à elle seule un mécanisme causal.
- **Hypothèse H3 :** l’agrégation par blocs de 100 réduit une partie du bruit individuel mais peut aussi lisser ou déplacer des transitions. Une sensibilité à la taille des blocs serait nécessaire avant toute interprétation.

## Limites

Le jeu AI4I est synthétique et UDI est un identifiant ordonné, pas une horloge validée. L’agrégation réduit 10 000 observations à 100 points et peut modifier les distributions. Une sortie `T0` est descriptive dans cette expérience; elle n’est pas une prédiction d’arrêt machine, un seuil opérationnel ni une preuve de validité universelle. Aucun résultat n’est transposé au cancer du pancréas.
