# Protocole V1 — prévision de demande et rotation UNIVERSAL_LOG

**Statut :** plan préparé avant les appels pipeline; audit des horodatages ajouté ensuite et signalé comme constat postérieur.

## Domaine et source

Mobilité urbaine, location de vélos Capital Bikeshare, 2011–2012. Source officielle : UCI Bike Sharing, DOI `10.24432/C5W894`, licence CC BY 4.0. Le fichier horaire contient 17 379 enregistrements ordonnés. Un audit postérieur a compté 17 544 créneaux horaires entre les deux extrémités incluses, dont 165 sans ligne dans le CSV. Les documents sources consultés ne précisent pas pourquoi ces créneaux manquent. Ils ne sont ni remplacés par zéro ni imputés. L'heure et la date sont conservées pour un découpage chronologique.

## Niveau 1 — tâche prédictive explicite

Estimer le nombre de locations `cnt` pour une heure future dans deux blocs chronologiques successifs. Prédicteurs utilisés : calendrier (`season`, `yr`, `mnth`, `hr`, `holiday`, `weekday`, `workingday`) et météo enregistrée (`weathersit`, `temp`, `atemp`, `hum`, `windspeed`). L'indice `instant` et les composantes `casual`/`registered` sont exclus. En particulier, `casual + registered = cnt` dans les données sources : les inclure serait une fuite directe de la cible.

La météo est observée dans le jeu après l'heure considérée. Ce protocole évalue donc une estimation rétrospective conditionnée par la météo mesurée, pas une prévision opérationnelle disponible avant l'heure. Comparateurs : prédicteur de moyenne, régression Ridge, Random Forest et HistGradientBoosting, sans réglage sur les blocs test. Mesures : MAE, RMSE, R²; deux découpages expansifs et strictement chronologiques (50 % d'apprentissage puis bloc suivant de 25 %, ensuite 75 % puis dernier 25 %).

## Niveau 2 — comportement du pipeline

Garder l'ordre horaire et agréger toutes les colonnes numériques en 100 blocs consécutifs aussi égaux que possible (moyenne par bloc). `cnt` est la cible fixe descriptive; chaque colonne numérique, y compris `cnt`, est proposée tour à tour comme contrôle. Quand le contrôle demandé égale la cible, consigner la substitution de cible appliquée par v6.0.1 et ne pas mélanger ce cas aux contrôles à cible constante. Le contrôle sélectionné doit être absent des flux analysés. Les colonnes `casual` et `registered` sont gardées ici comme flux liés à la cible, mais identifiées comme composantes de `cnt`.

Paramètres : v6.0.1 gelé par SHA-256, `mode=fast`, 8 scénarios, une graine déterministe par axe, un worker, graphiques désactivés uniquement par monkeypatch des fonctions de rendu. Conserver l'entrée, le plan, les journaux, les sorties complètes, les erreurs et durées.

## Niveau 3 — instrumentation, ordre et artefacts

L'ordre temporel est une propriété observée du jeu, mais l'agrégation en 100 blocs est une décision d'analyse. Elle lisse les variations horaires et peut déplacer les repères. Le CSV contient moins de lignes que de créneaux horaires possibles; l'origine et le mécanisme des 165 créneaux sans ligne ne sont pas documentés dans le Readme fourni. Le Readme attribue les informations météo à Freemeteo et décrit les locations comme un journal historique agrégé. Les valeurs météo sont normalisées; les fichiers ne donnent ni modèle de capteur, ni étalonnage, ni incertitude de mesure. Le système de réservation/retour peut lui-même limiter les locations observées selon la disponibilité des vélos; les données par station et les journaux de disponibilité ne sont pas fournis pour le vérifier. L'indice `instant` est une séquence d'enregistrement, pas une mesure physique indépendante du temps.

**Hypothèse à examiner, pas résultat :** un repère détecté par le pipeline pourrait provenir du phénomène étudié, d'une limite ou transformation de mesure, d'une agrégation, d'un changement de collecte, ou de plusieurs de ces causes. La rotation des contrôles ne permet pas, à elle seule, d'identifier laquelle. Le niveau 3 doit donc rapprocher les sorties de la provenance, des unités, de la quantification, des valeurs extrêmes, des périodes absentes et des informations d'instrument disponibles. Si ces informations manquent, l'attribution à l'instrument reste indéterminée.

## Statut épistémique

Avant les exécutions, toute relation attendue reste une hypothèse. Les métriques des modèles et les sorties v6.0.1 seront rapportées séparément. Les lacunes temporelles sont un constat de structure du fichier; elles ne démontrent pas un défaut du système de collecte. Un T0 descriptif n'est ni une prédiction en soi, ni une cause, ni un seuil opérationnel. Cette étude ne prouve ni universalité du pipeline ni validité pour un autre système de vélos.
