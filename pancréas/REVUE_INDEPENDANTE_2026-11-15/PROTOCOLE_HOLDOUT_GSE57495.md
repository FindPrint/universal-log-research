# Protocole gelé — validation externe CEACAM5/KRAS dans GSE57495

**Pré-enregistrement local :** 15 novembre 2026, avant téléchargement/inspection des valeurs d’expression de GSE57495.  
**Question unique :** dans cette nouvelle cohorte de PDAC, l’expression ARN de CEACAM5 augmente-t-elle avec l’expression ARN de KRAS ?  
**Dépôt :** NCBI GEO GSE57495, étude de 63 tumeurs microdisséquées congelées sur plateforme GPL15048; le jeu est distinct des trois matrices déjà analysées dans la revue. Source primaire : https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE57495.

## Hypothèse et critère primaire

- H1 directionnelle : la corrélation de Spearman entre l’expression de KRAS et celle de CEACAM5 est positive.
- Unité : un échantillon tumoral/patient, jamais une sonde ni une cellule.
- Inclusion : les 63 échantillons tumoraux de la série GEO; aucune exclusion à partir des valeurs de CEACAM5, KRAS, survie ou résultat du pipeline.
- Expression : valeurs traitées par les auteurs dans la matrice GEO. Les sondes seront annotées avec la plateforme GPL15048; si plusieurs sondes sont associées à un symbole, la médiane par symbole sera utilisée. Les lignes sans symbole non ambigu seront exclues du calcul génique. Les valeurs manquantes des deux gènes sont exclues par paire et leur nombre sera rapporté.
- Test primaire : Spearman unilatéral positif, 100 000 permutations de l’appariement des patients, graine 20261115, seuil descriptif préfixé α=0,05. Effet rapporté comme ρ avec IC bootstrap percentile 95 % sur 10 000 rééchantillonnages de patients, graine 20261115.
- Décision : réplication directionnelle uniquement si ρ>0, p permutation <0,05 et l’IC 95 % bootstrap exclut 0. Sinon, le résultat est soit non répliqué, soit imprécis selon l’IC; aucune autre coupure ne sera substituée.

## Analyse secondaire préfixée

Corrélation de rang partielle après retrait linéaire de deux scores préfixés, médianes des gènes acineux `PNLIP, CTRB2, CELA3A, CTRB1, CPA1, CELA2A, CPB1, CELA3B, CLPS, CTRC, CPA2` et des gènes d’îlots `INS, GCG, PPY, SST`. Les gènes absents de la plateforme seront signalés; l’analyse est omise si moins de 3 gènes acineux ou moins de 2 gènes d’îlots sont mesurés. Elle ne remplace pas le critère primaire et n’est pas présentée comme un ajustement complet de pureté.

## Garde-fous et portée

- Aucun scan de seuil, top-k, choix de flux après examen, changement de signe, recherche d’un sous-groupe ni entraînement sur GSE57495.
- Aucun résultat de cette association ne sera décrit comme preuve d’un changement de régime, de TLog, de causalité, de statut mutationnel KRAS, d’un dosage sanguin CEA, d’une réponse thérapeutique ou d’une utilité clinique.
- GSE57495 a été choisie parmi les options publiques après les résultats antérieurs; cette validation est donc indépendante par cohortes, mais pas une étude confirmatoire préenregistrée avant toute exploration du projet. L’éventuel chevauchement de patients avec les séries antérieures n’est pas vérifiable à partir des identifiants anonymisés disponibles.
- Le script, les empreintes des sources, les sorties complètes et les écarts au protocole seront conservés. Tout écart sera daté et rapporté sans effacer ce protocole.

## Clarification préanalyse (15 novembre 2026, avant calcul des associations)

La spécification de la corrélation partielle ne définissait pas l'opération « retrait linéaire » sur des rangs. Pour la rendre reproductible sans consulter le résultat cible, la procédure secondaire est fixée ainsi : (1) calculer la médiane des sondes non ambiguës de chaque gène; (2) calculer le score acineux et le score d'îlots comme médiane des expressions de leurs gènes disponibles; (3) convertir CEACAM5, KRAS et chacun des deux scores en rangs moyens; (4) régresser séparément les rangs de CEACAM5 et de KRAS sur une constante et les deux scores classés; (5) calculer la corrélation de Pearson des deux vecteurs résiduels. Aucun autre ajustement n'est autorisé dans cette analyse secondaire. La permutation primaire emploie `p=(1 + nombre de ρ_permuté ≥ ρ_observé)/(100000 + 1)`, après permutation des étiquettes d'échantillon de KRAS. Le bootstrap rééchantillonne 10 000 fois les paires patient avec remise et prend les quantiles 2,5 % et 97,5 % de Spearman.

