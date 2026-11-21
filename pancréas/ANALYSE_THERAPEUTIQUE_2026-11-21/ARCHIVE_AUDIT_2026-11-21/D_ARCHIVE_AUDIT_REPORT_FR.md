# Revue des archives de recherche sur D:

**Date de l'audit :** 21 novembre 2026  
**Statut :** rapport de travail; les observations et les interprétations sont
séparées. Les chemins complets du disque restent dans les manifestes privés,
pas dans cette synthèse destinée au projet.

## Règle d'analyse retenue

Le pipeline est traité ici comme un **pipeline d'analyse**. Un résultat décrit
ce que donnent un axe de contrôle, des flux, des estimateurs et une
configuration déterminés. Un seuil n'est pas automatiquement une prédiction,
un diagnostic biologique ou une transition physique.

Pour une exécution donnée, la colonne choisie comme contrôle est un axe; elle
est exclue des flux analysés de cette même exécution. Les autres colonnes
peuvent ensuite être testées comme axe de contrôle lors d'exécutions distinctes.
La monotonie n'est pas un critère d'admissibilité : un axe non monotone demeure
une configuration informative. Les résultats obtenus selon différents axes
sont conservés séparément.

## 1. Couverture de l'inventaire

### Fichiers repérés dans les dossiers de recherche examinés

L'inventaire ciblé a couvert neuf emplacements de recherche, totalisant 2 848
entrées de fichiers sélectionnées par extension. L'audit statique a analysé
186 scripts Python sans erreur de syntaxe. Il a rencontré 157 notebooks : 155
sont du JSON valide et deux sont vides. Ces vérifications ne constituent pas
une revue sémantique exhaustive de chaque fichier.

Un inventaire par noms/extensions sur tout le disque a repéré 2 048 fichiers
candidats : 198 scripts Python, 222 notebooks, 209 PDF, 19 ZIP, 675 CSV,
292 TXT, 369 JSON, 60 Markdown, 2 DOCX, 1 MP4 et 1 YAML. Les empreintes
SHA-256 ont permis d'identifier 324 groupes de doublons parmi les fichiers
hachés. Un catalogue plus ciblé de `downloads` et `Data_raw` a repéré 452
fichiers candidats (819 623 158 octets); 447 ont reçu une empreinte
SHA-256. La sélection sur le disque entier est faite par noms et extensions,
puis l'inspection du contenu est sélective : ce n'est pas une lecture intégrale
des 2 048 fichiers. Seize chemins ressemblant à des fichiers sensibles ont
été exclus de l'inspection; ils n'ont pas été ouverts. Les catalogues privés
conservent les chemins relatifs et les empreintes pour reprise ultérieure.

### Documents théoriques anciens

- Une note ancienne présente plusieurs variantes statiques, temporelles et
  multidimensionnelles de TLog, avec `T_log = (d - 4) ln(n)` et `dcrit = 4`.
  Elle indique aussi que cette constante n'est pas dérivée comme principe
  valable dans tous les domaines et demande une validation empirique par
  application.
- Une copie ancienne de `TLog.txt` diffère de la copie actuelle. La version
  ancienne formule l'idée que plusieurs ancres peuvent rester distinctes et
  que leur écart pourrait décrire une structure. C'est une hypothèse à tester,
  pas un résultat démontré par le présent audit.
- Les archives sur le cycle croyance-réalité et sur les lois d'échelle
  gravitationnelles sont conservées comme travaux connexes. Leur relation à
  TLog n'est pas établie ici.

## 2. Ising classique — balayage des colonnes de contrôle

### Données et protocole archivé

Le CSV historique contient 200 points et vient d'un générateur 2D Ising avec
`L=32`, températures réparties entre 1 et 4, 2 000 balayages de
thermalisation et 200 mesures. Le générateur ajoute du bruit à plusieurs
observables; il ne fixe pas de graine dans sa version archivée. Le balayage
comparable effectué pour cet audit a utilisé Cohen-d, fenêtre 80, optimisation
automatique désactivée et les mêmes paramètres rapides pour chacun des neuf
axes numériques. La colonne de contrôle a été retirée de la liste des flux à
chaque passage.

### Résultat observé

Les nombres ci-dessous sont des positions de seuil en pourcentage de l'axe de
progression produit par cette configuration. Ils ne sont pas les valeurs
physiques brutes de chaque contrôle.

| Colonne choisie comme contrôle | Seuil de rang (%) | Spearman avec l'ordre des lignes |
|---|---:|---:|
| Progress | 25,3 | 1,000 |
| Temperature | 25,3 | 1,000 |
| Magnetization | 76,3 | −0,788 |
| Energy | 24,3 | 0,997 |
| Abs_Magnetization | 53,8 | −0,968 |
| Magnetization_Squared | 53,8 | −0,974 |
| Energy_Squared | 53,8 | −0,997 |
| Magnetization_Diff | 23,8 | −0,063 |
| Energy_Diff | 67,8 | 0,041 |

Les deux différences sont de faibles corrélations de rang avec l'ordre du CSV;
elles ont été conservées comme axes, plutôt qu'écartées pour non-monotonie.
Les observations avant seuil peuvent être dispersées dans l'ordre initial;
un rang de seuil ne doit donc pas être lu comme une valeur de température sans
vérifier le mappage rang-température de cette exécution.

### Interprétation à retenir

Le résultat établi est une **sensibilité du seuil à la colonne servant
d'axe**, dans ce protocole précis. Le seuil obtenu avec Temperature est à
25,3 % de progression. L'attente physique pour `Tc` dans l'intervalle de
température [1, 4] correspond à environ 42,3 % de l'intervalle. Ce protocole
rapide n'a donc pas localisé `Tc` à cette position attendue. Les essais
historiques qui s'en approchent utilisaient d'autres fenêtres et réglages; ils
ne sont pas une comparaison à paramètres égaux.

Le balayage n'établit ni que les autres seuils sont erronés, ni que les axes
sont interchangeables. Il montre précisément qu'il faut garder les rôles
d'axe, les flux, la configuration et la correspondance au contrôle brut dans
chaque journal de résultat.

## 3. Archives PDAC — balayage des axes et provenance des sorties

### Données et définition de Progression

Le CSV PDAC commun aux archives examinées contient 99 lignes et 19 colonnes.
Sa colonne `Progression` est construite en triant les cas selon `OS_MONTHS`,
puis en attribuant une progression de 0 à 100. C'est un rang transversal de
survie, pas une série longitudinale mesurée dans le temps.

Le passage fixe rapide de l'ancienne pipeline v3 a testé chacune des 15
colonnes numériques comme contrôle, en excluant à chaque fois la colonne
choisie des flux. Les résultats suivants sont des positions de seuil selon
cette analyse, non des estimations d'efficacité thérapeutique.

| Axe de contrôle | Seuil (%) | Axe de contrôle | Seuil (%) |
|---|---:|---|---:|
| KRAS_Oncogenic | 31,4 | Apoptosis | 66,7 |
| EMT | 71,8 | Metabolic | 73,8 |
| Immune | 26,3 | DNA_repair | 27,3 |
| Stroma | 61,7 | Drug_Resistance | 68,7 |
| Stemness | 26,3 | Hypoxia | 46,5 |
| OS_MONTHS | 46,5 | AGE | 26,3 |
| Progression | 50,6 | Progression_Stroma | 61,7 |
| Progression_Resistance | 68,7 |  |  |

`OS_STATUS` est du texte dans le CSV d'origine et ne fait pas partie de ces 15
colonnes numériques. Un essai exploratoire l'a recodé explicitement
(`LIVING=0`, `DECEASED=1`) puis l'a testé comme contrôle : seuil 60,0 % sur 99
cas. Cette transformation doit rester visible comme choix d'encodage; le
résultat n'est pas une prédiction de survie.

### Incompatibilité de rapports anciens

La reproduction a isolé deux moteurs qui écrivent dans un même répertoire de
résultats : un moteur de modules qui reproduit le JSON archivé au seuil
7,2613 %, et un moteur autonome Monte Carlo dont les rapports texte donnent
14,1735 % dans une archive et 30,8166 % dans d'autres. Les archives tlog25 et
tlog28 sont identiques fichier par fichier; la sortie texte varie toutefois
entre anciens paquets. Le lancement simultané écrase le même nom de JSON.

Pour le moteur autonome, deux exécutions contrôlées avec la graine Python 42
ont reproduit exactement le JSON, avec `T0=10,6151 %`. Une exécution avec la
graine 43 a donné `T0=22,4228 %`. Cela montre une dépendance à l'aléa dans ces
exécutions, mais deux graines ne suffisent pas à caractériser sa distribution.
La valeur 30,8166 % n'a pas été reproduite par ces essais. Cette différence
reste ouverte.

## 4. Contrôle et flux dans v6

### Observation sur v6.0.0

Le balayage automatique retire déjà la colonne choisie comme contrôle de la
liste des flux. Un test synthétique à 120 lignes a confirmé cette voie. Le
même test a aussi confirmé une exception : un mappage explicite pouvait
réintroduire la colonne de contrôle comme flux sous un alias. Ce comportement
était reproductible et pouvait créer une analyse diagonale de la même série.

### Version candidate v6.0.1

Une copie séparée de v6.0.0 ajoute un filtre dans tous les chemins du mappage
explicite. Si un flux composite comprend le contrôle, seule cette colonne est
retirée; les autres sources demeurent. La suppression est signalée dans les
métadonnées `control_flux_exclusions`. Le caractère non monotone du contrôle
n'est pas bloquant.

Le contrôle d'intégration exécuté avec le `.venv` a utilisé un contrôle
synthétique non monotone (54 pas descendants et 65 ascendants), le mappage
explicite `Control_as_flux -> Control`, et un flux `FluxA`. La pipeline a
terminé avec succès; `Control_as_flux` était absent et `FluxA` présent. Le
journal et les métadonnées consignaient l'exclusion. Des cas unitaires
supplémentaires couvrent le mappage vide, un alias direct, un composite qui
contient le contrôle et un flux indépendant.

Cette vérification valide seulement la règle de rôle contrôle/flux sur données
synthétiques. Elle ne valide pas les estimateurs, TLog ou une application
scientifique.

## 5. Ising quantique — état de la vérification

Une archive notebook contient un code path-integral Monte Carlo pour le modèle
Ising transverse, avec `L_tau=8`, `beta=2`, 26 valeurs de Gamma, `L=24` et
`L=32`. Les sorties cachées du notebook indiquent le mode robuste, cinq
réalisations et 15 000 étapes; les durées affichées sont d'environ 69 minutes
pour L=24 et 115 minutes pour L=32.

**Observation de code :** le notebook calcule 30 caractéristiques et des
scores Q1-Q4. Ses bornes Q2 comprennent des intervalles choisis autour de la
valeur de référence `Gamma_c=3,044`; elles ne constituent donc pas une
localisation aveugle de seuil. L'inspection n'a pas trouvé de calcul final de
la formule TLog dans ce notebook. Les sorties cachées restent des résultats
archivés, pas une reproduction indépendante. Le notebook n'a pas été relancé;
sa cellule d'installation est une commande notebook et les dépendances
`antropy`/`nolds` ne faisaient pas partie de l'environnement utilisé ici.

## 6. Autres domaines repérés

- **Taches solaires :** les formules enregistrées respectent l'arithmétique
  TLog à l'arrondi. Le signe varie avec la méthode utilisée pour estimer d;
  les résultats bootstrap toutes méthodes sont négatifs aux fenêtres
  examinées, alors que M2 seul devient positif aux fenêtres plus larges.
- **Finance S&P 500 :** certains rapports ne concordent pas avec leurs propres
  d/TLog; un R² rapporté égal à 1 peut provenir d'une construction tautologique.
  Les notebooks vides restent vides.
- **Climat urbain / PM2.5 :** les rapports existants sont des analyses
  exploratoires sans seuil de transition de référence; la série climat mêle
  plusieurs villes et doit être segmentée avant toute nouvelle analyse.
- **Autres archives physiques et géophysiques :** elles sont répertoriées;
  les scripts susceptibles d'écrire des sorties n'ont pas tous été exécutés.

Ces points constituent des pistes d'audit, pas une validation transversale.

## 7. Conclusion provisoire et questions ouvertes

### Résultats établis dans cet audit

1. Les seuils changent selon la colonne choisie comme axe de contrôle dans les
   deux CSV historiques examinés.
2. Le protocole fixe Ising n'a pas placé son seuil Temperature à la position
   attendue pour `Tc`.
3. Les archives PDAC mélangent deux moteurs et contiennent une variabilité
   Monte Carlo qui n'est pas encore caractérisée.
4. v6.0.0 exclut correctement le contrôle sur la voie automatique, mais pas
   dans un mappage manuel sous alias; la version candidate v6.0.1 corrige ce
   cas sur l'essai synthétique.
5. Les sorties Ising quantique archivées ne sont pas une reproduction TLog.

### Hypothèses à retester, sans les conclure

- Les écarts entre axes pourraient refléter des propriétés différentes des
  variables contrôles et méritent d'être analysés comme interactions
  configuration-axe-flux.
- Plusieurs ancres ou seuils pourraient conserver de l'information. Cette
  proposition exige une règle préalable pour les comparer sans choisir le
  résultat après l'observation.
- La sensibilité du PDAC aux graines pourrait être quantifiée avec un ensemble
  de graines et des sorties distinctes par moteur.

### Prochaine séquence reproductible

1. Geler v6.0.1 comme candidate distincte et recalculer son empreinte.
2. Appliquer la même grille de paramètres à chaque colonne de contrôle
   numérique, tout en excluant l'axe sélectionné des flux; conserver les axes
   non monotones et reporter leur diagnostic séparément.
3. Refaire le balayage Ising avec plusieurs tailles et convertir chaque seuil
   vers la valeur brute de température selon le mappage exact de chaque run.
4. Pour PDAC, produire un manifeste par moteur, graine, axe, flux, paramètres
   et sortie; ne pas fusionner les JSON et rapports de moteurs distincts.
5. Traiter l'analyse quantique et les autres domaines comme des reproductions
   séparées, avec dépendances fixées et distinction claire entre résultats
   cachés d'archives et nouveaux calculs.

## Traçabilité des artefacts

Les catalogues contenant les chemins locaux complets, les empreintes des
fichiers, les reproductions, les journaux de paramètres et les sorties JSON
sont conservés dans le dossier privé de l'audit D:. La version candidate du
code est distribuée dans le projet sous le nom
`UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py`. La version précédente et
les résultats historiques ne sont pas écrasés.
