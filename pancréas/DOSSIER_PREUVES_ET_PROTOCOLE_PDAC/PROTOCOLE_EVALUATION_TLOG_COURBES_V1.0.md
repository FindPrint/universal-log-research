# Protocole d'évaluation de TLog sur courbes dose-réponse

**Version :** 1.0 — 24 novembre 2026
**Statut :** critères préspécifiés et versionnés; non enregistré; aucun test indépendant sélectionné ou analysé.
**Portée :** évaluation analytique in vitro. Ce protocole ne constitue ni une validation clinique ni un protocole de traitement.

## 1. Question et estimand

Chez des modèles humains de PDAC, quelle est l'erreur de l'estimation TLog d'un point médian de réponse, à partir d'une courbe dose-réponse courte, par rapport au point médian estimé sur une courbe de référence complète acquise lors d'une expérience indépendante, pour le même modèle et le même composé?

L'estimand TLog est la concentration médiane de transition retournée par la version figée de `UNIVERSAL_LOG_dose_response_v1.py`, exprimée en `log10(concentration)`. Elle n'est pas assimilée à la concentration correspondant à 50 % de viabilité absolue, à une `LN_IC50`, ni à une réponse clinique. Ces valeurs ne sont comparables que si leur définition et leurs unités sont harmonisées avant l'accès au test.

Un couple modèle–composé est une unité de comparaison, pas une répétition biologique. Les modèles PDO issus d'un même donneur, les expériences répétées d'un même modèle et les composés testés sur un même modèle sont dépendants; l'inférence et le rééchantillonnage en tiendront compte.

## 2. Population, unité expérimentale et admissibilité

- Modèles d'organoïdes humains de PDAC (PDO) ou lignées PDAC dont l'identité, le donneur ou le modèle, le composé et les conditions sont traçables. Un résultat sur lignées cellulaires sera rapporté séparément des résultats PDO.
- Les données doivent contenir les mesures par dose, et non seulement des AUC, IC50, classements, graphes ou résumés.
- Chaque paire modèle–composé doit comporter une courbe courte et une courbe de référence obtenues dans des expériences distinctes, sur des cultures/plaques indépendantes. Au moins trois cultures ou expériences biologiques indépendantes sont requises pour chaque volet. Les puits techniques ne comptent pas comme répétitions biologiques.
- Les données doivent distinguer les identifiants de donneur, modèle, expérience biologique, plaque, puits technique, lot, dose, unité, réponse, contrôle de véhicule et motif d'exclusion. Si cette structure ou l'indépendance biologique ne peut pas être établie, le jeu n'est pas admissible à l'analyse confirmatoire.
- Les réponses doivent être normalisées par rapport au contrôle de véhicule de la plaque, avec méthode documentée, et fournies en fraction de viabilité. Ne pas tronquer les valeurs supérieures à 1 ni transformer les réponses après consultation du test. Les bornes de qualité, la plage dynamique et le traitement des contrôles sont à figer sur des données de développement avant le test.
- La courbe courte doit contenir 7 à 20 concentrations distinctes, strictement positives, avec doses et unités vérifiées, conformément à l'interface du module. La courbe de référence doit contenir au moins 12 concentrations distinctes couvrant la région de transition et le point médian estimé; au moins deux concentrations observées doivent se trouver de chaque côté de ce point. Les critères de qualité et diagnostics d'identifiabilité de la référence sont appliqués selon la section 4.
- Les répétitions techniques sont agrégées par dose à l'intérieur de chaque répétition biologique selon une règle figée avant le test. Aucune imputation, interpolation de dose, suppression sélective de points ni winsorisation n'est autorisée. Les exclusions sont limitées aux critères de qualité documentés à l'avance et sont journalisées.

## 3. Indépendance, séparation et verrouillage

1. Avant tout accès aux réponses du test, archiver le présent protocole, le code, l'environnement, les dépendances, les règles de contrôle qualité, les métriques et les commandes; publier leurs empreintes SHA-256 et enregistrer le protocole dans un registre public horodaté.
2. Le test doit être conservé par un dépositaire indépendant ou dans un espace dont les réponses ne sont pas accessibles à l'équipe d'analyse avant le verrouillage. Le dépositaire fournit d'abord un dictionnaire et un manifeste non révélateurs des réponses pour statuer sur l'admissibilité.
3. Ni une courbe, ni un puits, ni une expérience, ni un lot, ni un modèle d'un même donneur ne peuvent être répartis entre développement et test. Les courbes courte et référence restent elles-mêmes issues d'expériences distinctes.
4. Les sources Yin Figure 6d, Tiriac 2018, les tables AUC Nature Communications 2025 et GDSC2 déjà examinées sont exclues du test final. Leurs données et résultats ont été consultés ou utilisés dans le développement; aucune nouvelle séparation a posteriori ne les rend indépendants.
5. Toute modification du code, du prétraitement, des critères d'admissibilité, de la référence ou des analyses après accès au test invalide le verrouillage pour ce jeu et nécessite un nouveau test intact, avec une nouvelle version du protocole.
6. La taille d'échantillon et la précision statistique visée doivent être approuvées par un biostatisticien indépendant et documentées dans un amendement avant l'ouverture du test. Le nombre de puits ou de courbes répétées d'un même modèle ne remplace pas le nombre de donneurs/modèles indépendants.

## 4. Méthodes figées et définition de la référence

- **Méthode testée :** `UNIVERSAL_LOG_dose_response_v1.py`; figer commit/version, SHA-256, environnement et paramètres avant le test. Conserver la règle actuelle de 3 estimateurs finis sur 5 et la plage de 7 à 20 doses. Aucun seuil ni algorithme n'est ajusté sur le test. Le seuil `N >= 50` du pipeline général ne s'applique pas au nombre de doses de ce module.
- **Courbe courte :** calculer TLog sur les réponses à chaque dose, après agrégation des seuls puits techniques au sein de chaque répétition biologique, puis sur l'agrégat défini à l'avance des répétitions biologiques. Conserver les sorties et abstentions par répétition; ne pas les compter comme autant de modèles indépendants.
- **Référence complète :** ajuster une fonction sigmoïde 4PL à la réponse moyenne par dose de l'expérience indépendante, avec la même version figée de `fit_4pl_sigmoid`. La référence est le milieu entre les plateaux supérieur et inférieur ajustés, et non nécessairement une viabilité absolue de 0,5.
- Une référence est **identifiable et admissible** seulement si l'ajustement converge, le diagnostic de plage est satisfait, son point médian est dans la gamme effectivement testée, les réponses observées couvrent ce point de part et d'autre avec au moins deux doses de chaque côté, et l'incertitude estimée est calculable. Les références qui échouent restent dans les comptes d'admissibilité et de couverture; elles ne reçoivent pas d'erreur numérique artificielle.
- **Comparateur court :** ajuster le même 4PL uniquement aux mesures de la courbe courte. Il est comparé à la même référence complète et aux mêmes paires que TLog. Un échec ou un résultat hors gamme est rapporté comme échec/abstention, pas retiré du dénominateur.
- L'incertitude de la référence et des estimations est calculée en rééchantillonnant des cultures/expériences biologiques entières; jamais des puits techniques ou des doses isolées. L'unité de bootstrap est le donneur, ou à défaut le modèle PDO indépendant, en conservant ensemble tous ses couples modèle–composé.

## 5. Encadrement, extrapolation et abstention

Pour chaque paire, rapporter séparément :

1. si la courbe courte observée encadre le point médian de la référence;
2. si elle encadre une viabilité absolue de 0,5;
3. si la sortie TLog tombe dans la gamme des doses courtes;
4. la convergence, l'identifiabilité et l'abstention de TLog et du comparateur 4PL court.

Les indicateurs d'encadrement ne sont pas interchangeables. Les paires sont présentées dans les strates « médian de référence encadré par les observations courtes », « non encadré » et « référence non identifiable/invalide ». Une estimation hors gamme courte est marquée comme extrapolation; elle ne compte pas comme un point médian directement observé. Aucune paire ne disparaît des dénominateurs de couverture en raison d'un échec.

## 6. Critères et plan statistique

**Critère principal :** erreur absolue en `log10(concentration)` entre l'estimation TLog courte et le point médian de la référence complète, sur les paires dont la référence est admissible. Rapporter l'effectif de paires, de modèles et de donneurs, MAE, médiane de l'erreur absolue, biais signé et intervalle de confiance à 95 %.

**Comparaison appariée :** différence d'erreur absolue TLog moins 4PL court sur les mêmes paires et face à la même référence complète. Valeur négative : erreur absolue plus faible pour TLog. Rapporter la différence moyenne et médiane, ainsi qu'un intervalle de confiance à 95 % obtenu par bootstrap en grappes au niveau donneur/modèle indépendant.

**Couverture et sécurité analytique :** dénominateur total admissible; références identifiables/non identifiables; sorties TLog et 4PL court valides; abstentions, échecs numériques et extrapolations. Présenter ces nombres globalement et par donneur, modèle, composé et strate d'encadrement. Rapporter aussi l'erreur sans masquer les échecs par une analyse « réussites seulement ».

**Secondaires descriptifs :** AUC, T0 et métriques de forme peuvent être rapportés séparément, sans inférence confirmatoire ni classement thérapeutique. Aucun résultat in vitro ne sera interprété comme bénéfice patient ou recommandation de traitement.

Aucun seuil de succès, de supériorité ou d'équivalence n'est fixé dans V1.0. Il ne sera proposé qu'après estimation de la variabilité sur un jeu de développement distinct et approbation par le biostatisticien indépendant, puis avant l'ouverture du test. Sans calcul de taille d'échantillon et seuils d'interprétation préapprouvés, les résultats restent descriptifs, même si les intervalles sont étroits.

## 7. Provenance, reproductibilité et rapport

Archiver, avec accès contrôlé aux données sensibles : provenance et licence; manifeste des fichiers et SHA-256; dictionnaire des variables; versions et empreintes de code/environnement; paramètres et commandes; diagramme d'inclusion; registre de toutes les exclusions et leur motif; tous les résultats par paire anonymisée; diagnostics de référence; abstentions, échecs, extrapolations et analyses préspécifiées. Publier le protocole et le plan statistique avant le déverrouillage. Ne jamais ne rapporter que les courbes ayant réussi.

## 8. État de préparation et portes de passage

- La V1.0 fixe les critères analytiques, mais **n'est pas enregistrée**. Son empreinte doit être calculée et déposée dans un registre public avant toute demande d'accès aux réponses du test.
- Aucun candidat local examiné à ce jour ne satisfait simultanément l'indépendance, la disponibilité des courbes brutes, les identifiants biologiques et les répétitions requises. Le dépistage documentaire et les motifs d'exclusion figurent dans [`AUDIT_JEUX_CANDIDATS_COURBES_INDEPENDANTES_2026-11-24.md`](./AUDIT_JEUX_CANDIDATS_COURBES_INDEPENDANTES_2026-11-24.md).
- Les réponses ctDNA (Linz, Stavanger, Changhai ou autres cohortes) ne sont pas des courbes pharmacologiques. Aucune réponse brute n'est enregistrée comme reçue dans le projet et aucune demande n'est envoyée par ce protocole; toute analyse ctDNA fera l'objet d'un protocole longitudinal distinct, avec l'accord et la gouvernance nécessaires.
- Prochaine porte : choisir un détenteur de données, obtenir d'abord le dictionnaire et la documentation de réplication sans les réponses, vérifier les droits et la possibilité d'un test intact, calculer la taille d'échantillon avec un biostatisticien, enregistrer le protocole et les empreintes, puis seulement déverrouiller et exécuter le test.

## Historique

- **V0.1 (24 novembre 2026)** : brouillon initial, remplacé par la version 1.0.
- **V1.0 (24 novembre 2026)** : critères préspécifiés opérationnels; pas de jeu de test sélectionné ou ouvert; pas de pré-enregistrement externe effectué.
