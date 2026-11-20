# Réanalyse exploratoire scRNA-seq pour prioriser des pistes thérapeutiques PDAC

**Date UTC:** 2026-11-17T22:14:48+00:00. **Données:** GEO GSE309596, 12 échantillons KPC1199, 115 664 cellules, quatre bras (véhicule, MRTX1133, olaparib, combinaison), trois échantillons GEO par bras. Le nombre de cellules reproduit le nombre publié.

## Question thérapeutique

Quelles populations cellulaires et voies moléculaires montrent une réponse spécifique à la combinaison, et quels axes immunitaires ou tumoraux pourraient expliquer une réponse durable ou une résistance? Les contrôles sont les facteurs MRTX1133, olaparib, leur interaction factorielle, et combinaison versus véhicule. Les flux sont les panneaux de marqueurs de populations et de mécanismes listés dans le script et les tables jointes.

## Mesures et calculs

Les UMI ont été agrégés au niveau de chaque spécimen GSM. Aucun test ne traite une cellule comme une réplication. Pour chaque panneau, le flux exprime la moyenne cellulaire log1p(CPM par 10 000) et, pour les panneaux d’identité, la fraction de cellules où au moins un ou au moins deux marqueurs sont détectés. Ces fractions se chevauchent et ne somment pas à 100 %. Des scores restreints aux cellules positives pour des marqueurs tumoraux, T ou myéloïdes sont également fournis avec seuils >=1 et >=2 marqueurs et au moins 10 cellules; ces identités sont des proxys de marqueurs, car aucune annotation par cellule n’est jointe. Les effets sont résumés par contraste, Cohen d descriptif pour les contrastes à deux groupes et effet d’interaction standardisé par l’écart-type résiduel intra-bras; les p sont des permutations exactes des 12 étiquettes d’armement équilibrées (369 600 allocations). La correction BH couvre tous les contrastes × flux × métriques prévus.

## Résultats observés

La grille contient 364 comparaisons planifiées; 328 sont estimables et 0 passent q BH < 0,05. Cette valeur q est conditionnelle à l’échangeabilité des spécimens et au caractère approprié des proxys de marqueurs.

Pour le contraste d’interaction sur les scores all-cellules, le plus petit q est 0.2367 pour CAF_stromal_identity, avec interaction standardisée d=-6.05, p exacte=0.002165. Il s’agit d’un classement exploratoire de réponses cellulaires, pas d’une preuve que ce flux est une cible thérapeutique.

Les tailles des échantillons par bras varient fortement en nombre de cellules (1 281 à 13 625; voir QC par spécimen); les statistiques sont donc réalisées sur 12 spécimens, pas pondérées par le nombre de cellules. Sous le seuil de deux marqueurs T détectés, les spécimens avec moins de 10 cellules positives sont: GSM9270219, GSM9270220, GSM9270226. Les scores restreints aux compartiments T et myéloïdes sont donc non estimables sous ce seuil pour certains bras; les versions avec au moins un marqueur sont fournies comme sensibilité et ne remplacent pas les cellules annotées. Les identifiants GSM/BioSample sont distincts et les titres indiquent des réplicats, mais les métadonnées n’exposent pas d’identifiant souris individuel. L’indépendance entre souris doit être confirmée par les auteurs; les p et q restent conditionnelles. Les scores pan-cellules mélangent expression intrinsèque et composition cellulaire.

## Limites et portée thérapeutique

Cette cohorte est la même étude qui décrit la combinaison MRTX1133 + olaparib; elle ne constitue pas une validation indépendante. Les panels sont des choix mécanistiques documentés, pas des résultats sélectionnés après lecture des p-values. Les définitions de marqueurs, les seuils ≥1/≥2, les flux manquants et chaque spécimen sont conservés dans les sorties. Un jeu ponctuel ne permet pas de seuil T0/TLog ou de dynamique de résistance. Les données peuvent aider à prioriser un test préclinique (par exemple une association spécifique avec activation CD8, suppression myéloïde, persistance MAPK/cycle ou déficit HR) mais ne démontrent ni guérison ni efficacité chez des patients.

**Étape qui peut réellement rapprocher d’un traitement:** prendre le ou les effets les plus solides et leurs cellules porteuses, vérifier la direction dans les comptages et un jeu indépendant; puis les tester dans des organoïdes et modèles immunocompétents avec véhicule, chaque monothérapie et combinaison, mesure de croissance tumorale, survie, toxicité, dose-réponse et marqueurs mécanistiques.
