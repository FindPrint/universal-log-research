# Addendum — correction d'unités de l'analyse Yin Figure 6d

**Date :** 24 novembre 2026
**Statut :** réanalyse exploratoire corrigée; non préenregistrée et non indépendante.

## Vérification de la provenance

Le DOI `10.1038/s41467-025-57520-3` correspond à Yin et al., « Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients », *Nature Communications* 16, 2214 (2025), PMID 40044664 / PMCID PMC11882848. Le résumé PubMed décrit un criblage sur organoïdes dérivés de patients; le texte de l'article précise que la Figure 6d présente des courbes dose-réponse de 15 PDO traités par correcteurs de CFTR. La feuille `Figure 6` du supplément porte l'en-tête `Drug Concentration(Log)` et des colonnes d'organïdes `DAC_...` appariées par composé. L'attribution du jeu au criblage pharmacologique est donc cohérente avec l'article. Le classeur ne suffit toutefois pas à qualifier les deux colonnes comme réplicats biologiques indépendants.

## Motif de la correction

La version initiale de `run_yin2025_full_evaluation.py` transmettait directement les réponses numériques de la feuille `Figure 6` au module dose-réponse. Les valeurs sont exprimées en pourcentage de viabilité (étendue observée : 0,828769 à 140,30742), alors que le module attend une fraction et que les bornes du 4PL sont définies sur cette échelle. L'affirmation initiale « 0/75 ajustements 4PL convergents » est un artefact d'incompatibilité d'unités; elle est retirée.

La source est `41467_2025_57520_MOESM17_ESM.xlsx`, feuille `Figure 6`, lignes 95–103, SHA-256 `917a1011426c5ee749343ccabf8126e35923a65c4719ec929f84aa29a511f7b1`. Le script de reproduction vérifie ce hash et la structure attendue avant analyse.

## Réanalyse corrigée

- Conversion de la réponse : pourcentage / 100, sans troncature.
- Agrégation : moyenne des deux colonnes source disponibles à chaque dose; les doses manquantes dans les deux colonnes sont omises, sans imputation.
- Incertitude : aucun bootstrap, car l'indépendance biologique des colonnes n'est pas établie.
- Couverture : 75 conditions; 60 courbes à 8 doses et 15 à 7 doses.
- Sorties TLog : 75/75 calculées; 75/75 marquées `VALIDE` par les règles logicielles (ce statut n'est pas une garantie d'exactitude).
- Ajustement 4PL : 75/75 convergents et dans la plage mesurée après correction d'échelle.
- Comparaison interne : différence absolue médiane entre les log10-IC50 TLog et 4PL calculées sur les mêmes courbes : 0,190. Ce n'est pas une comparaison à une vérité indépendante.

Les nouveaux fichiers sont nommés `YIN_2025_FIG6D_TLOG_CORRECTED_UNITS_RESULTS.csv` et `.json`. Ils sont des sorties dérivées locales; les anciens résultats ne sont pas écrasés.

## Portée et données indépendantes

Le benchmark initial est post hoc; la source et les sorties avaient déjà été consultées. Cette correction ne transforme donc pas les courbes en jeu de test indépendant. Le tableau Tiriac 2018 disponible dans ce projet ne contient que des AUC résumées, pas les courbes de dose et réplicats nécessaires au protocole. Les colonnes Yin ne constituent pas une référence indépendante complète documentée. Aucune validation indépendante de TLog n'est établie.
