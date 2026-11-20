# Revue des recommandations externes — 2026-11-16

## Objet et périmètre

Cette note évalue les trois recommandations reçues sur l’abstention de `T0`, l’analyse de GSE141017 et le seuil de stabilité L7b. Elle s’appuie sur le code v6.0.0-CohenD présent dans l’archive, les sorties du pilote synthétique `synthetic_pilot_v1`, les fichiers GSE141017 déjà présents localement et les sources primaires citées à la fin.

Les statuts sont distingués : **observé** = directement présent dans le code, les données ou les sorties; **interprétation** = conclusion limitée tirée de ces observations; **proposition** = prochaine expérience, pas un résultat acquis. Aucun seuil du pipeline n’a été modifié et aucun run du pipeline ni analyse biologique d’expression n’a été exécuté dans le cadre de cette revue; le contrôle technique des métadonnées et des barcodes a, lui, été effectué.

## 1. Abstention pour le seuil T0

### Observé

- Le scan principal calcule, pour chaque coupure candidate, la moyenne des séparations `abs(Cohen's d)` sur les flux, puis choisit `argmax(scores)` (`universal_v6.0.0_cohen.py`, lignes 3070–3090). Il produit donc une position même quand les données ne contiennent pas de transition connue.
- Le pilote a trouvé `T0 = 77,31 %` sur le nul AR(1) stationnaire et `T0 = 90,66 %` sur le nul à dérive lisse. Les résultats du pilote précisent explicitement qu’aucune règle d’alerte n’était gelée : ces positions ne sont pas comptées comme des faux positifs.
- Le fichier possède déjà `permutation_test_threshold_significance` (lignes 1503–1573), mais ce test porte sur le score de la cascade harmonique, pas sur le maximum Cohen du scan principal. Dans le chemin harmonique, l’axe peut être calculé à partir du contrôle **et** de la cible (lignes 11284–11286), puis reste fixe pendant les permutations (lignes 11304–11306). L’inférence d’un test global intégrant toute la sélection est donc limitée par cette sélection préalable.

### Interprétation

La recommandation d’ajouter une abstention vise un défaut réel du scan principal. Elle n’est toutefois pas satisfaite par l’existence du test harmonique, et un `p < 0,05` naïf sur la série déjà sélectionnée ne suffit pas : il faut reproduire sous le nul l’ensemble des choix qui ont produit le score observé (coupures, flux retenus et, si elle dépend de la cible, sélection de l’axe).

### Proposition

Séparer explicitement deux sorties : **position candidate** (`T0_candidat`, toujours rapportée comme diagnostic) et **détection** (`T0_detecte` ou `None`, avec statut et incertitude). Geler le statisticien de détection et son protocole avant calibration. La calibration doit répéter toute la procédure de sélection sur des séries nulles autocorrélées et à dérive, puis mesurer le taux d’alertes et la sensibilité sur plusieurs tailles d’effet, longueurs, flux liés/non liés et graines. Le niveau 5 % peut être un objectif expérimental préspécifié, mais ne doit pas être présenté comme une propriété universelle du pipeline.

## 2. GSE141017 : pseudotemps, réplications et RNA velocity

### Observé

- Les fichiers locaux comprennent une matrice de comptages à 41 139 colonnes cellulaires et une table d’identités cellulaires/barcodes à 41 139 lignes; les étiquettes couvrent CTRL, 17 jours, 6 semaines, 3, 5, 9 et 15 mois.
- Les préfixes des barcodes permettent de retrouver les neuf identifiants d’échantillon/souris et leurs effectifs : CTRL2 5 406; PRT17 4 095; WT6W 4 088; F20_3M 1 944; FI_3M 6 855; WT5M1 5 718; WT5M2 4 420; WT9M 1 500; WT15M 7 113 cellules.
- Les fichiers ont chacun 41 139 identifiants bruts. Une normalisation exploratoire qui enlève le `X`/padding de soulignés et harmonise le suffixe `.n`/`-n` crée une collision d’identifiant WT5M2/5M, observée dans l’en-tête de matrice comme dans l’annotation; les deux lignes d’annotation associent cet identifiant normalisé à `ident` 12 et 15. Il n’est pas établi que ce padding soit purement cosmétique : conserver les identifiants originaux et vérifier le conflit contre GEO/SRA avant toute fusion ou attribution de cluster.
- L’étude originale rapporte 41 139 cellules provenant de **neuf souris**. Elle indique deux souris à 3 mois, deux à 5 mois et une souris pour chacun des autres temps; l’échantillon à 15 mois comprend la souris avec PDAC invasif. Les cellules ne sont donc pas 41 139 répétitions biologiques indépendantes.
- Le GEO relie GSE141017 au projet SRA SRP247080 et indique que les données de séquençage brutes sont disponibles dans SRA. Les fichiers actuellement présents localement ne sont pas des matrices séparées d’ARN épissé/non épissé.
- L’article décrit des bibliothèques 10x Chromium V2/V3 et un traitement Cell Ranger. La RNA velocity estime une dynamique de l’expression à partir de comptes épissés et non épissés; elle ne transforme pas les cellules d’une coupe transversale en observations longitudinales mesurées sur plusieurs mois.

### Interprétation

Les préfixes des barcodes semblent conserver une clé d’échantillon utile pour agréger ou valider par souris, mais toute normalisation ou fusion des identifiants doit d’abord résoudre la collision apparente depuis la source. Le pseudotemps peut fournir un **axe d’état cellulaire exploratoire** pour une lignée définie, par exemple les cellules acinaires et dérivées acinaires. Il ne doit pas être renommé temps biologique, ni servir à contourner mécaniquement le minimum `N >= 50` en comptant chaque cellule comme une répétition indépendante. La petite réplication par souris, en particulier aux temps tardifs, limite fortement les affirmations populationnelles et toute conclusion sur l’apparition d’un cancer.

La RNA velocity reste envisageable après récupération et retraitement des lectures SRA, sous réserve de vérifier la qualité des lectures et la possibilité d’obtenir des couches épissées/non épissées adaptées. C’est un chantier distinct, plus lourd, et son échelle dynamique (état transcriptionnel à court terme) n’est pas identique à la progression expérimentale en mois.

### Proposition

Commencer par un inventaire réplicable des échantillons, souris, bibliothèques, temps PTI, clusters et marqueurs; définir ensuite une population cellulaire avant de calculer un pseudotemps. Pour toute inférence, conserver la souris comme unité de rééchantillonnage (validation leave-one-mouse-out ou bootstrap/permutation par souris), éviter que les mêmes gènes définissent l’axe et constituent seuls la preuve de transition, et comparer l’axe inféré aux temps PTI et marqueurs/pathologies observés. Ajouter la RNA velocity uniquement comme flux secondaire si le retraitement SRA la rend techniquement défendable.

## 3. L7b-light et `t0_std`

### Observé

- Le walk-forward calcule `t0_std = std(t0s, ddof=1)` (lignes 9905–9907). Les `t0s` sont les estimations `T_0_Monte_Carlo_Central` sur l’axe de progression en rang, rapporté en pourcentage; ce ne sont pas des nombres de lignes déplacées.
- L7b attribue PASS seulement si `t0_std <= 10`; il classe les valeurs de 10 à 20 comme FAIL « moyennement variable » et celles au-dessus de 20 comme FAIL « très variable » (lignes 10779–10788).
- Dans les quatre cas complets du pilote, les écarts-types walk-forward sont 24,73; 24,73; 32,05; et 21,81. Les quatre verdicts sont FRAGILE. Dans le cas de dérive lisse sans rupture, la stabilité minimale des horizons est aussi FAIL à 0,75.

### Interprétation

La description « échec uniquement à cause de valeurs autour de 19–22 » est inexacte pour ces sorties : trois valeurs sont au-dessus de 20, et le cas de dérive échoue aussi au contrôle d’horizon. La proposition `t0_std / N` ne suit pas les unités du calcul actuel : `t0_std` est déjà mesuré en points de pourcentage du rang. Une normalisation différente pourrait être étudiée, mais elle constituerait une nouvelle métrique à valider, pas une correction démontrée.

### Proposition

Geler le seuil actuel pendant un banc de calibration séparé. Rejouer des événements et des nuls sur plusieurs longueurs, résolutions d’axe, autocorrélations, fenêtres walk-forward et graines; rapporter la distribution brute de `t0_std` et ses causes (horizon, bruit, longueur, densité de grille). Comparer ensuite, sans remplacer l’original, la stabilité en points de rang à des métriques explicitement normalisées et évaluer si elles prédisent une erreur de localisation réelle.

## Étape suivante recommandée

1. **Priorité immédiate :** rédiger et geler le protocole synthétique d’abstention + calibration L7b, en distinguant position candidate et détection; tester d’abord les nuls AR(1) et dérive lisse déjà identifiés, puis élargir aux autres structures et interactions de flux.
2. **En parallèle, sans lancer encore le retraitement lourd :** établir le tableau de provenance GSE141017 au niveau souris/échantillon/bibliothèque et confirmer quelles données SRA sont disponibles pour les aliquotes d’intérêt.
3. **Après cette porte d’entrée :** analyser le pseudotemps comme axe d’état exploratoire avec validation par souris; lancer RNA velocity seulement si la reconstitution des comptes épissés/non épissés est faisable et si elle répond à une question distincte.

Ces étapes peuvent renforcer la validation du pipeline. Elles ne constituent pas encore une preuve d’universalité, une validation clinique, ni une démonstration causale du cancer du pancréas.

## Sources

- Code audité : `pancréas/Archive complète PDAC v6 — ZIP/universal_v6.0.0_cohen.py`.
- Pilote audité : `ising_classique_test/finite_size/pipeline_v6_0_pathway_audit/synthetic_pilot_v1/scored_pilot_results.json` (empreinte du code : `bb8bbdba4eb1f8c55b49748274ae8fbfef8a43f6c1b890964f18ba77960c0773`).
- Données locales : `pancréas/VALIDATION_TEMPORELLE_GSE141017/data/GSE141017_README.txt` et `GSE141017_ALL_barcode_ident.csv.gz`.
- GEO, GSE141017 / SRA SRP247080 : https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE141017
- Schlesinger et al., étude originale et plan d’échantillonnage : https://doi.org/10.1038/s41467-020-18207-z
- La Manno et al., RNA velocity et distinction épissé/non épissé : https://doi.org/10.1038/s41586-018-0414-6
