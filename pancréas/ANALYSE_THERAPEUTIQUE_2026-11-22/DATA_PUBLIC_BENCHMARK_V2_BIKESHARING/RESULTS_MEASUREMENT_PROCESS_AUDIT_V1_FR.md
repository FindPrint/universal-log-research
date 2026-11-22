# Audit descriptif de la chaîne de mesure — Bike Sharing V1

## Portée et source

Analyse descriptive de `source/hour.csv` (17,379 lignes), sans correction des données. Empreinte SHA-256 : `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`. Le Readme UCI décrit un journal historique de Capital Bikeshare agrégé à l'heure; il attribue l'information météo à Freemeteo et indique une normalisation par les facteurs 41 (`temp`), 50 (`atemp`), 100 (`hum`) et 67 (`windspeed`). Il ne fournit pas de modèle d'instrument, de certificat d'étalonnage, d'incertitude instrumentale ou de série de disponibilité/capacité des stations.

## Constats mesurés dans le fichier

- 17 379 lignes couvrent du 2011-01-01 00:00 au 2012-12-31 23:00. L'intervalle inclusif comporte 17 544 heures; 165 heures n'ont pas de ligne, distribuées sur 75 intervalles. Le Readme ne donne pas leur mécanisme. Elles ne sont pas imputées.
- `casual + registered = cnt` pour toutes les lignes (contrôle d'intégrité du fichier).
- Parmi les valeurs météo normalisées, `hum` vaut exactement 1,00 dans 270 lignes; `windspeed` vaut 0 dans 2180 lignes. Le maximum observé de `temp` et `atemp` apparaît chacun une fois.
- Les plus grandes différences absolues entre deux lignes consécutives de `cnt` sont conservées dans le JSON associé. Ce sont des changements de comptage observés; aucune cause n'est attribuée.

| Flux | Valeurs distinctes | Minimum | Maximum | Occurrences du minimum | Occurrences du maximum | Plus petit pas distinct observé |
|---|---:|---:|---:|---:|---:|---:|
| `temp` | 50 | 0.02 | 1 | 17 | 1 | 0.02 |
| `atemp` | 65 | 0 | 1 | 2 | 1 | 0.0151 |
| `hum` | 89 | 0 | 1 | 22 | 270 | 0.01 |
| `windspeed` | 30 | 0 | 0.8507 | 2180 | 2 | 0.0149 |
| `cnt` | 869 | 1 | 977 | 158 | 1 | 1 |
| `casual` | 322 | 0 | 367 | 1581 | 1 | 1 |
| `registered` | 776 | 0 | 886 | 24 | 1 | 1 |

## Hypothèses instrumentales à tester, sans conclusion

La concentration de `hum` à la borne supérieure et les nombreux zéros de `windspeed` peuvent justifier une vérification de résolution, d'arrondi, de limite de mesure ou de codage. Ils peuvent aussi avoir une explication physique. Le fichier et son Readme ne permettent pas de départager ces possibilités. Les catégories `weathersit`, la normalisation météo, l'agrégation horaire, les heures manquantes et la disponibilité des vélos sont des parties distinctes de la chaîne de production des données.

Un repère UNIVERSAL_LOG proche d'une borne, d'une transition catégorielle ou d'une lacune serait donc un candidat à examiner avec les métadonnées de collecte et des données indépendantes; ce rapprochement ne suffit pas à prouver que l'outil a créé le seuil. Il faut aussi préserver l'hypothèse inverse : un changement du phénomène peut être réel et capté correctement par l'instrument.

## Suite discriminante proposée

1. Chercher la documentation de collecte des données météo et les journaux de disponibilité/capacité par station; si ces sources n'existent pas dans l'archive publique, noter cette absence comme limite.
2. Comparer les champs météo à une source météorologique indépendante alignée par heure, en rapportant les écarts et les heures absentes sans les combler silencieusement.
3. Comparer l'analyse sur les enregistrements horaires et le fichier journalier fourni, en gelant les paramètres et en traitant l'agrégation comme facteur expérimental. Ne pas appeler les deux jeux des répétitions indépendantes.
4. Relier chaque sortie de seuil aux valeurs et changements observés dans tous les flux autour de T0, en excluant le contrôle choisi des flux analysés; rapporter séparément les cas où le contrôle demandé égale la cible et où le code substitue la cible.

Ces étapes séparent les observations du fichier, les hypothèses d'instrument et les résultats du pipeline. Elles ne présupposent pas que le seuil soit instrumental ou biologique/opérationnel.
