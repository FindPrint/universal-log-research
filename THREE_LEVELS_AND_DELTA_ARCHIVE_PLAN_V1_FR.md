# Cadre de travail : trois niveaux d’analyse et snapshots différentiels

**Version :** 1.0  
**Date :** 2026-11-22  
**Statut :** protocole de travail; ce document ne présente pas de validation scientifique nouvelle.

## 1. Séparer trois questions

Les mêmes colonnes peuvent servir à plusieurs questions, mais leurs conclusions doivent rester distinctes.

### Niveau 1 — La tâche visée

**Question :** que cherche-t-on à estimer ou à prédire dans le domaine étudié?

Avant le calcul, consigner la population, l’unité d’observation, la cible, l’horizon ou l’axe demandé, la règle de séparation des données, les métriques de référence et les limites d’usage. Une valeur de seuil `T0` produite par le pipeline n’est pas, à elle seule, une prédiction correcte. Une affirmation prédictive exige une cible observée et une évaluation hors échantillon contre un ou plusieurs baselines adaptés.

### Niveau 2 — Le comportement du pipeline

**Question :** que renvoie le pipeline lorsque les colonnes, l’axe de contrôle, le mode et les paramètres changent?

La théorie de travail du projet est le **pipeline complet d’analyse** : préparation des données, choix des axes et flux, interactions, 29 estimateurs, règles de seuil, diagnostics, sorties et TLog. La formule TLog seule n’épuise donc pas la théorie; chaque conclusion doit préciser quelle partie du pipeline l’a produite.

Consigner la version et le hash du code, les paramètres, les 29 estimateurs disponibles, les sorties complètes, les avertissements, les échecs et le temps d’exécution. Pour un CSV donné, faire tourner chaque colonne numérique admissible comme contrôle selon un plan annoncé. Distinguer le **contrôle=cible demandé** du **contrôle=cible réellement exécuté** : le pipeline peut refuser cette diagonale ou substituer une autre cible. Enregistrer la cible demandée, la cible utilisée et la raison de tout repli; ne pas comparer un repli comme s’il avait gardé la cible fixe. Le contrôle choisi doit être absent des flux analysés lorsque c’est le comportement attendu, et cette exclusion doit être vérifiée dans les sorties. Un contrôle non monotone n’est pas rejeté par défaut : sa forme constitue une propriété mesurée du flux.

Les résultats décrivent d’abord le comportement du logiciel et la sensibilité à la configuration. Ils ne démontrent pas automatiquement l’universalité, la causalité ou la performance prédictive.

### Niveau 3 — Le processus de mesure et la qualité des données

**Question :** un signal apparent vient-il du phénomène visé, de l’instrument, de la collecte, du traitement ou de leur interaction?

Documenter l’instrument et sa version quand ils sont connus, les lots, l’ordre d’acquisition, les calibrations, les répétitions, les valeurs manquantes, les limites de détection et les transformations. Tester des hypothèses de dérive, de bruit, d’effet de lot et de données manquantes séparément lorsque les métadonnées le permettent. Le pipeline peut repérer un seuil critique du système de mesure plutôt que de la cible scientifique; inversement, une lecture du phénomène peut faire manquer un seuil propre à l’instrument. Il faut garder les deux hypothèses ouvertes et comparer les flux d’instrument, de contrôle et de résultat avant d’attribuer le signal.

## 2. Règle de lecture des conclusions

Chaque énoncé de résultat est étiqueté comme l’un des suivants :

- **Hypothèse :** raison de tester une relation; non établie.
- **Observation :** sortie effectivement mesurée dans un jeu et une configuration précis.
- **Résultat robuste :** observation répétée sous des variantes préspécifiées, avec incertitude et contrôles rapportés.
- **Interprétation :** explication possible, séparée des observations.
- **Conclusion de domaine :** n’est formulée que si le plan d’évaluation et les données la justifient.

Une analyse de données tumorales, par exemple, ne constitue pas une preuve de traitement efficace. La recherche thérapeutique exige des validations expérimentales et cliniques appropriées, indépendantes du simple repérage d’un seuil.

## 3. Plan de benchmark multi-domaines

Ordre proposé, sous réserve de profilage des coûts et d’une vérification de la structure des fichiers :

1. **Essai d’ingénierie/prédiction :** AI4I 2020 a été obtenu depuis le miroir Kaggle de son auteur, puis vérifié octet pour octet contre le CSV UCI. Ce jeu est explicitement synthétique. Le benchmark prédictif indépendant est terminé; la rotation des contrôles du pipeline est documentée à part.
2. **Essai de série temporelle/mobilité :** Bike Sharing UCI, 2011–2012, avec heures ordonnées et météo observée. Il permet de séparer un benchmark d’estimation de demande de la rotation v6.0.1 sur 16 flux numériques. L’agrégation par blocs est une résolution testée, pas l’ordre naturel lui-même.
3. **Essai d’instrumentation :** un jeu de capteurs avec lots chronologiques et dérive documentée. Garder les identifiants de lot/temps distincts des mesures de capteur et faire tourner les contrôles numériques admissibles. Un candidat UCI comporte une note de licence restrictive ambiguë; ne pas le redistribuer avant clarification.
4. **Essai biomédical :** seulement après validation des métadonnées et du plan de séparation par patient, cohorte ou temps. Aucun résultat exploratoire ne sera présenté comme remède ou recommandation clinique.

Une analyse exhaustive de toutes les colonnes peut être coûteuse. Avant d’élargir un jeu à des dizaines ou centaines de flux, mesurer le coût réel d’un appel représentatif et publier le nombre d’essais exécutés, omis ou non terminés. Une réduction exploratoire est permise uniquement si les colonnes retenues et les exclusions sont annoncées avant l’analyse et si elle n’est pas décrite comme un balayage exhaustif.

## 4. Audit des snapshots V4–V11 effectué le 2026-11-22

### Observations mesurées

- Huit ZIP historiques de projet sont présents sous `archive_sources/`; leur taille cumulée est **74 574 947 273 octets** (74,57 GB décimaux; environ 69,45 GiB).
- Les ZIP portant les mêmes noms sur D: représentent **93 469 569 080 octets** (93,47 GB décimaux), car certaines variantes V6 existent en double.
- Un audit en lecture seule a comparé les chemins, tailles décompressées et CRC de chaque membre. Il trouve au moins une copie D: avec les mêmes membres et métadonnées pour chacun des huit ZIP C:. Les ZIP C: et D: ne sont donc pas tous des copies redondantes inutiles : certaines variantes V6 sont différentes.
- Les contenus de V5, V6 courant, V7, V8, V9 et V10 sont couverts par V11 avec les mêmes chemins, tailles et CRC de membres.
- La comparaison V4/V11 trouve **13 membres absents et 1 membre dont le CRC ou la taille diffère**. La variante V6 initiale trouve **4 membres différents** de V11.
- Le ZIP V11 contient 19 autres ZIP liés aux données et audits du projet; il ne contient pas les ZIP complets des snapshots V4 à V10 comme membres imbriqués.
- Les disques indiquaient environ **234,9 GB libres sur C:** et **133,4 GB libres sur D:** lors de l’inventaire. Aucun fichier n’a été supprimé, déplacé ou purgé.

### Portée et limite de cet audit

Les tailles et CRC des membres servent à comparer rapidement des contenus d’archive; cette vérification n’établit pas que les ZIP externes ont un encodage binaire identique, ni que V11 préserve la signification historique de chaque version. Les exclusions V4 et V6 sont listées dans `archive_sources/SNAPSHOT_OVERLAP_AUDIT_2026-11-22.json`. Il serait donc inexact d’affirmer sans réserve que V11 contient chaque élément de chaque version historique.

### Décision de conservation

Les archives sont conservées. Toute récupération éventuelle d’espace devra d’abord produire et vérifier une archive de récupération pour les membres manquants/différents, garder une copie historique intègre sur D:, confirmer les manifestes de sauvegarde, puis documenter précisément les fichiers retirés. Cette étape ne fait pas partie du présent audit.

## 5. Proposition d’archive différentielle

Conserver le snapshot complet V11 comme base immuable, puis créer pour chaque version ultérieure un delta comprenant :

- les fichiers ajoutés ou modifiés, avec chemin relatif, taille et SHA-256;
- la liste explicite des fichiers supprimés;
- le nom et le SHA-256 de la base requise;
- la version de l’outil de création et les instructions de reconstruction;
- une vérification des chemins afin d’interdire les écritures hors du dossier de destination.

La reconstruction se fait en extrayant la base, en appliquant les ajouts/remplacements et enfin les suppressions. Elle doit vérifier l’identité de la base et les empreintes des fichiers appliqués. Les archives historiques V4–V10 restent un lot de conservation distinct; elles ne sont pas remplacées par le mécanisme delta.

La taille d’un delta n’est pas garantie à 5–30 Mo : un PDF complet mis à jour, des figures haute résolution, des données brutes ou des résultats volumineux peuvent produire un delta de plusieurs centaines de Mo. La mesure utile est la taille réelle du delta comparée à celle d’un nouveau snapshot complet, après génération.

## 6. Sources de données candidates vérifiées

- **AI4I 2020 Predictive Maintenance (Kaggle original-author mirror; UCI DOI 10.24432/C5HS5C)** : 10 000 lignes, jeu explicitement synthétique, mesures machine et étiquettes de panne; licence UCI indiquée CC BY 4.0. Le CSV Kaggle a été comparé octet pour octet au fichier officiel UCI avant le benchmark.
- **Gas Sensor Array Drift at Different Concentrations (UCI, DOI 10.24432/C5MK6M)** : 13 910 mesures, 16 capteurs, 128 descripteurs, 10 lots couvrant des mois chronologiques; source utile pour étudier l’axe mesure/lot et la dérive. La page indique CC BY 4.0 mais mentionne également une restriction d’usage exclusivement scientifique et l’exclusion commerciale. Le jeu ne sera pas redistribué publiquement avant résolution de cette tension de licence; toute utilisation publiée devra citer la source et l’article requis.
- Une page Kaggle repérée pour une compétition sur la dérive des capteurs indique un accès sur invitation et une licence CC BY-NC-SA 4.0. Elle n’est pas retenue comme dépendance tant que l’accès et les conditions ne sont pas vérifiés. Les sources UCI ci-dessus ont été consultées le 2026-11-22.

## 7. Références / traçabilité

- AI4I 2020 UCI: https://archive.ics.uci.edu/dataset/601/ai4i%2B2020%2Bpredictive%2Bmainten
- Bike Sharing UCI: https://archive.ics.uci.edu/dataset/275/bike%2Bsharing%2Bdataset
- UCI Gas Sensor Array Drift at Different Concentrations: https://archive.ics.uci.edu/dataset/270/gas%2Bsensor%2Barray%2Bdrift%2Bdataset
- Kaggle Inter-uni Datathon gas sensor drift: https://www.kaggle.com/competitions/inter-uni-datathon-stream-3-gas-sensor-array-drift-dataset/data
- Audit ZIPs: `archive_sources/SNAPSHOT_OVERLAP_AUDIT_2026-11-22.json`
- Profilage exploratoire: `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/TRANSITION_SENSITIVITY_V2/RUNTIME_PROFILE_V1/`

## 8. Premier résultat prédictif indépendant

Le benchmark AI4I a utilisé trois blocs chronologiques futurs de 2 000 lignes chacun; les étiquettes de panne et les identifiants n’ont pas été injectés comme variables explicatives. La prévalence de panne observée était de 7,70 %, 2,25 % puis 1,95 % selon le bloc. En moyenne sur ces trois tests, la régression logistique équilibrée a donné AUROC 0,854, average precision 0,393, précision 0,204 et rappel 0,660 au seuil 0,5; la forêt aléatoire équilibrée a donné respectivement 0,922, 0,589, 0,627 et 0,504. Les métriques de forêt varient beaucoup entre blocs, notamment rappel 0,227 à 0,644.

Ce sont les performances de modèles de classification conventionnels sur des données **synthétiques**. Aucune sortie T0/TLog du pipeline n’a été évaluée comme classifieur; le résultat n’est donc pas une validation du pipeline ni une preuve industrielle. Le détail est dans `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-22/DATA_PUBLIC_BENCHMARK_V1/RESULTS_AI4I_PREDICTION_V1_FR.md`.

## 9. Profilage observé du pipeline

Sur un cas synthétique V2 de 64 points, les sorties analytiques sont identiques pour quatre exécutions comparées : V2 antérieure, répétition complète, répétition profilée et rendu désactivé. Les temps observés sont 729,6 s, 157,25 s, 260,67 s et 84,27 s respectivement. Dans une paire récente, couper le rendu a économisé 72,98 s (46,4 %) tout en gardant des sorties analytiques identiques. Cette comparaison est exploratoire et unique; les durées totales varient considérablement.

Le profil indique plusieurs coûts cumulés importants : `apply_complexity` (74,90 s / 672 appels), `_compute_extra_estimators` (61,84 s / 616 appels), rendu `pyplot.savefig` (68,43 s) et diagnostics bruit/CSD (41,68 s et 32,58 s). Ces durées s’emboîtent; ne pas les additionner. La source v6.0.1 est restée inchangée. Le rapport complet distingue les observations, hypothèses d’optimisation et limites dans `RUNTIME_PROFILE_V1/RUNTIME_PROFILE_REPORT_V1_FR.md`.

La rotation des 12 axes sur l’entrée AI4I agrégée en 100 blocs est maintenant en cours. Aucun T0 de cette campagne n’est inclus ici avant la fin et le contrôle de ses 12 journaux et sorties.
