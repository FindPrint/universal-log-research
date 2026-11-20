# Résultats du test externe GSE57495

**Statut :** analyse exploratoire de cohorte tenue à l'écart des trois cohortes antérieures; cible choisie après exploration du projet. Elle ne constitue pas une confirmation préenregistrée avant toute analyse.

## Résultat primaire

- Cohorte : 63 échantillons GEO; paires CEACAM5/KRAS complètes : **n=63**.
- Expression : matrice GEO déposée; sondes réunies par médiane, uniquement quand l'annotation officielle GPL15048 donne un symbole unique.
- Sondes retenues : CEACAM5 `merck2-NM_004363_at, merck2-NM_004363_x_at, merck-M29540_a_at`; KRAS `merck2-AI554920_at, merck2-AI554920_x_at, merck-AU134294_a_at, merck-BC013572_a_at, merck-BE869335_a_at, merck-NM_033360_s_at`.
- Spearman : **ρ=0.4377**; test de permutation unilatéral positif, **B=100,000, p=0.000239998**.
- IC percentile bootstrap 95 % (**10,000** rééchantillonnages finis) : **[0.1901, 0.6352]**.
- Décision préfixée : **critère satisfait** (ρ>0, p<0,05 et borne basse IC>0).

**Conclusion mesurée :** Le critère directionnel préfixé est satisfait dans cette cohorte pour l'association d'expression ARN.

Cette association entre deux niveaux d'expression ARN ne montre ni mutation KRAS, ni relation causale, ni transition temporelle, ni performance de TLog/pipeline, ni utilité clinique.

## Analyse secondaire de composition

- Statut : **computed**.
- Score acineux mesuré : PNLIP, CTRB2, CELA3A, CPA1, CELA2A, CPB1, CLPS, CTRC, CPA2; absent : CTRB1, CELA3B.
- Score d'îlots mesuré : INS, GCG, PPY, SST; absent : aucun.
- Corrélation de rang partielle selon la définition préfixée : **0.35209778083403437**.

Ce contrôle de composition est un proxy grossier, et non un ajustement complet de pureté tumorale. Il ne remplace pas le résultat primaire.

## Reproductibilité et périmètre

- Graine : `20261115`; permutation : `100,000`; bootstrap : `10,000` demandé.
- Script : `analyze_gse57495_holdout.py`; environnement : `.venv` du projet.
- Données source et annotation officielles conservées dans `data_GSE57495/`; empreintes SHA-256 dans `data_GSE57495/GSE57495_holdout_manifest.json`.
- Table d'analyse par échantillon : `data_GSE57495/GSE57495_holdout_sample_data.csv`.
- Distributions de rééchantillonnage : `data_GSE57495/GSE57495_permutation_rho.npz`, `data_GSE57495/GSE57495_bootstrap_rho.csv`.
- Figure : `data_GSE57495/GSE57495_holdout_results.png`.
- Pas d'import ni d'appel à UNIVERSAL_LOG/TLog dans cette analyse.

## Limites préfixées

Cette étude est une cohorte publique de tumeurs congelées mesurées par microarray. Elle ne teste qu'une association transversale RNA/RNA. La sélection de CEACAM5/KRAS a été motivée par les analyses antérieures; les données ne sont donc pas totalement indépendantes du processus de sélection. Les chevauchements éventuels de patients entre GEO sont non vérifiés. L'annotation GPL15048 est celle fournie par GEO et sa nomenclature historique peut être imparfaite. Aucun résultat ne permet d'inférer l'état mutationnel de KRAS.

Source primaire : [GEO GSE57495](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE57495); annotation : [GEO GPL15048](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15048).
