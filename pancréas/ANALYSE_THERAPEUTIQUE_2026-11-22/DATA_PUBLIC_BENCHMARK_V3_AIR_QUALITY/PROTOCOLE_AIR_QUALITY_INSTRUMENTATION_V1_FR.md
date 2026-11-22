# Protocole V1 — capteurs, référence et dérive

**Statut :** plan exploratoire préparé avant le téléchargement et l'exécution du pipeline; la préparation exacte est précisée par l'amendement post-audit V1a. Les hypothèses ci-dessous ne sont pas des résultats.

## Pourquoi ce jeu

UCI Air Quality contient des réponses horaires d'un dispositif multicapteur déployé sur le terrain et des concentrations horaires provenant d'un analyseur certifié colocalisé. La page de l'UCI indique 9 358 lignes, cinq capteurs à oxyde métallique, des dérives de capteur et de concept, des sensibilités croisées et des valeurs manquantes codées `-200`. La page situe les données de mars 2004 à février 2005; l'archive téléchargée s'étend jusqu'au 4 avril 2005. Cet écart de métadonnées sera rapporté plutôt que corrigé par supposition. Ces propriétés en font un test direct de l'hypothèse selon laquelle un repère peut être associé à la chaîne de mesure plutôt qu'au seul phénomène.

Source : [UCI Air Quality, DOI 10.24432/C59K5F](https://archive.ics.uci.edu/dataset/360/air%2Bquality). La page précise que les données sont destinées à la recherche, exclut l'usage commercial, puis affiche une licence CC BY 4.0 générale. Cette tension est documentée : les fichiers bruts restent locaux et ne sont pas inclus dans l'archive publique tant que les conditions applicables ne sont pas clarifiées. Le code et les rapports publics devront citer la source et ne pas redistribuer la matrice brute.

## Niveau 1 — tâche de calibration distincte

Tâche principale : estimer une concentration de référence (par défaut `CO(GT)`) à partir des réponses capteurs et des variables météo disponibles, avec séparation chronologique. `-200` est traité comme code de donnée manquante documenté, jamais comme une concentration physique. Aucun remplissage artificiel n'est appliqué. Le rapport précisera combien d'observations sont conservées, perdues ou non admissibles dans chaque pli. Les comparateurs et métriques seront gelés avant calcul; ce benchmark conventionnel n'est pas une sortie prédictive d'UNIVERSAL_LOG.

## Niveau 2 — rotation descriptive du pipeline

Après audit et transformation documentée, toutes les colonnes numériques d'origine admissibles seront présentées tour à tour comme axe de contrôle. Un index temporel dérivé sera séparé et étiqueté comme variable construite, pas comme mesure source. Le contrôle sélectionné sera vérifié absent des flux analysés. La cible demandée (`CO(GT)`), la cible utilisée, et tout repli logiciel seront conservés et comparés séparément.

Les seuils T0, TLog, les estimateurs, les questions et les diagnostics sont décrits comme sorties de la configuration. Aucun seuil ne sera attribué à un capteur parce qu'il coïncide avec un changement de lot ou une borne sans contrôle indépendant.

## Niveau 3 — hypothèses sur le processus de mesure

Avant de relier un seuil à un phénomène, inspecter séparément :

- le code sentinelle `-200`, les lacunes d'horodatage et l'ordre d'acquisition;
- les bornes, répétitions, plateaux, pas numériques et changements de distribution des canaux capteurs;
- les écarts entre réponses capteurs et références certifiées, par gaz et par période;
- les changements de calendrier, température et humidité pouvant affecter les mesures;
- la description disponible du dispositif, des unités, des canaux et des limites de la documentation.

La comparaison capteur–analyseur est un contrôle utile, mais elle ne prouve pas à elle seule qu'un seuil du pipeline vient de l'instrument. Un phénomène réel, une dérive, une transformation, des données absentes et leurs interactions restent des explications concurrentes. Si une information nécessaire manque, l'attribution reste indéterminée.

## Règles de traçabilité

Geler avant l'exécution les empreintes source et code, la transformation du `-200`, le traitement des lacunes, l'ordre, le choix de cible, les paramètres, les graines et la liste des flux. Conserver les sorties complètes et les erreurs. Ne pas ajuster une règle de seuil après consultation des mêmes données sans étiqueter l'analyse comme post hoc. Publier les hypothèses et observations dans des sections distinctes.

## Mesures anti-interprétation

Un repère T0 n'est pas automatiquement un seuil instrumental, une concentration toxique, un point causal ou une prédiction. Une dérive documentée dans le jeu n'implique pas que le pipeline la détecte correctement. Le succès ou l'échec d'une prédiction conventionnelle ne valide ni ne réfute, à lui seul, la théorie complète du pipeline.
