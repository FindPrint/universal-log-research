# Analyse exploratoire externe PDAC — inhibiteurs KRAS G12C

**Date d’exécution:** 17 novembre 2026. **Cohorte:** 22 patients PDAC issus de la cohorte clinique publiée sous adagrasib (patients 1–8) ou sotorasib (patients 9–22). **Unité:** patient. **Plan:** 6 contrôles candidats × 11 flux candidats; correction BH globale sur les comparaisons estimables.

## Question et constat principal

Question de transférabilité: le signal TP53 prétraitement ↔ événement KRAS acquis observé dans l’analyse daraxonrasib apparaît-il aussi dans cette cohorte, exposée à des inhibiteurs KRAS G12C différents? La publication rapporte des gains/amplifications KRAS G12C émergents chez les patients 6, 9, 13 et 22; le supplément permet de repérer ces événements à partir des colonnes prétraitement/fin de traitement. Les trois événements classés Amp sont distingués du cas Gain.

La grille compte **66 comparaisons prévues**, **65 estimables** et **0 q<0,05**. Pour le contraste ciblé TP53 prétraitement × KRAS CN Gain/Amp, 3/18 patients avec variant TP53 prétraitement listé et 1/4 sans variant prétraitement listé ont un Gain/Amp KRAS listé; OR=0.6, test Fisher exact (patient-level 2x2), p nominale=1, q globale=1. La liste des patients avec Gain/Amp est Patient 6, Patient 9, Patient 13, Patient 22; Amplification seule: Patient 6, Patient 13, Patient 22.

**Interprétation:** ce résultat est un test exploratoire de portabilité entre mécanismes médicamenteux et ne valide pas un biomarqueur. L’absence d’un événement dans le supplément est codée ‘non listé’, jamais ‘confirmé absent’. Le tableau ne garantit pas une couverture identique pour chaque altération et les plateformes diffèrent. Les réponses sont celles d’une petite cohorte déjà sélectionnée pour maladie KRAS G12C et les patients PR/SD ont ensuite progressé.

## Couverture de la cohorte

Réponses consignées: {'PD': 4, 'PR': 7, 'SD': 11}. Statut TP53 prétraitement (‘variant TP53 avec VAF numérique listé’ vs ‘aucun variant TP53 prétraitement listé’): {'no_pretherapy_variant_listed': 4, 'yes': 18}. Le second libellé ne signifie pas TP53 sauvage. Le supplément contient 196 lignes de variants au total, dont 148 lignes PDAC, agrégées en 22 patients.

## Contrôles × flux

Les contrôles candidats couvrent traitement, réponse, preuve listée d’un variant TP53 prétraitement, disponibilité/VAF KRAS G12C initiale et plateforme. Les flux comprennent nouveaux événements copy-number, mutations listées, événements RAS/PI3K/RTK, KRAS G12C fin de traitement et différence VAF prétraitement–fin. Tous les tests sont patient-level; les prélèvements ne sont pas traités comme des observations indépendantes. Les mesures dérivées partagent des colonnes sources et ne sont pas des preuves biologiques indépendantes.

| Contrôle | Flux | n patients | Test | Effet | p | q globale |
|---|---|---:|---|---:|---:|---:|
| baseline_kras_g12c_vaf_pct | eot_kras_g12c_vaf_pct | 18 | patient-level permutation Spearman | Spearman_rho=0.6512 | 0.005 | 0.2275 |
| technology_profile | n_new_mutation_rows_listed | 22 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.335 | 0.007 | 0.2275 |
| baseline_kras_g12c_detection | n_new_mutation_rows_listed | 22 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=4 | 0.0127 | 0.2503 |
| baseline_kras_g12c_vaf_pct | new_kras_cn_gain_or_amp_listed | 20 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=12.05 | 0.0154 | 0.2503 |
| tp53_baseline_variant_listed | n_new_mutation_rows_listed | 22 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-2.5 | 0.02 | 0.26 |
| technology_profile | new_ras_pi3k_rtk_mutation_listed | 22 | patient-level permutation Pearson chi-square | Cramers_V=0.5714 | 0.032 | 0.2722 |
| baseline_kras_g12c_vaf_pct | n_new_copy_number_rows_listed | 20 | patient-level permutation Spearman | Spearman_rho=0.4851 | 0.0317 | 0.2722 |
| baseline_kras_g12c_vaf_pct | new_ras_pi3k_rtk_mutation_listed | 20 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=12.05 | 0.0335 | 0.2722 |
| baseline_kras_g12c_vaf_pct | new_kras_cn_amp_listed | 20 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=15.81 | 0.0384 | 0.2773 |
| baseline_kras_g12c_vaf_pct | new_any_cn_listed | 20 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=7.32 | 0.0432 | 0.2808 |
| baseline_kras_g12c_vaf_pct | new_pik3ca_mutation_listed | 20 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=27.08 | 0.0652 | 0.3853 |
| technology_profile | new_any_mutation_listed | 22 | patient-level permutation Pearson chi-square | Cramers_V=0.4745 | 0.0844 | 0.4511 |
| tp53_baseline_variant_listed | new_any_mutation_listed | 22 | Fisher exact (patient-level 2x2) | odds_ratio=0 | 0.09023 | 0.4511 |
| baseline_kras_g12c_detection | new_ras_pi3k_rtk_mutation_listed | 22 | Fisher exact (patient-level 2x2) | odds_ratio=inf | 0.1212 | 0.5253 |
| tp53_baseline_variant_listed | new_any_event_listed | 22 | Fisher exact (patient-level 2x2) | odds_ratio=0 | 0.115 | 0.5253 |

## Champ d’application et limites

- Ce supplément fournit des prélèvements prétraitement et fin de traitement; il ne constitue pas une série temporelle régulière. Aucun T₀, dérivée temporelle, seuil TLog ou conclusion de transition n’est calculé.
- N=22 et les variables sont clairsemées. Cette analyse applique les tests patient-level de la suite multiaxiale compagnon, mais ne lance pas le cœur universel complet, les 29 estimateurs ni la formule finale TLog. Elle ne prouve donc ni la théorie entière ni son universalité.
- La grille et la question ciblée sont exploratoires et définies après publication/inspection du supplément; la correction BH ne supprime pas ce biais de sélection.
- Aucun contrôle × flux ne franchit q<0,05 dans cette grille. Avec seulement 22 patients, cela ne démontre pas l’absence d’effet; tout signal nominal reste à répliquer dans une cohorte indépendante avec les mêmes médicaments, des mesures appariées, une définition préenregistrée du contrôle/flux et une validation fonctionnelle.
- Rien ici ne démontre un remède, une efficacité thérapeutique nouvelle, une causalité TP53, ni une recommandation pour une personne. Les modèles organoïdes/PDX ou expériences contrôlées sont l’étape suivante pour tester une intervention.

## Reproduction

Depuis la racine du dépôt Windows: `\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\external_validation_g12c\analyze_g12c_external.py`. Le script réutilise le moteur patient-level déclaré dans le manifeste.

Sources: article principal [doi:10.1158/2159-8290.CD-24-0177] (https://doi.org/10.1158/2159-8290.CD-24-0177); supplément CC BY [doi:10.1158/2159-8290.32699721] (https://doi.org/10.1158/2159-8290.32699721); API publique Figshare (https://api.figshare.com/v2/articles/32699721).
