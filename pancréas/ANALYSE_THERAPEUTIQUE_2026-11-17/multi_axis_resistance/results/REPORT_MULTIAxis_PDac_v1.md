# Scan clinique multiaxial — résistance au daraxonrasib

**Exécution:** 17 novembre 2026 · **patients:** 44 · **flux:** 14 · **contrôles:** 7 · **famille:** BH globale sur tests estimables.

## Résultat

La grille contrôle × flux produit **98 comparaisons prévues**, dont **91 estimables** après gestion explicite des données absentes/censurées. Les associations avec q BH globale < 0,05 sont **4**.

Cette analyse est descriptive/exploratoire et ne donne ni prédicteur validé, ni combinaison thérapeutique, ni preuve de guérison. Les 44 patients ont tous été sélectionnés parce qu’ils avaient eu un bénéfice initial puis une progression; il n’y a pas de groupe de patients durablement sans progression. Le test de TP53 contre amplification KRAS fait partie des comparaisons et sa valeur brute connue n’est pas une validation indépendante.

Le contraste déjà rapporté TP53 prétraitement ↔ amplification KRAS acquise retrouve p=0.03215, mais q BH globale=0.2044; il ne franchit pas la grille élargie.

Parmi les quatre q<0,05, le lien baseline RAS-VAF ↔ différence prétraitement/sous-traitement est mathématiquement couplé, car la valeur initiale entre dans le calcul du delta (rho=-0.992, q=0.00455); il ne constitue pas une preuve biologique indépendante. Le lien baseline VAF–détection sous traitement est aussi sensible au seuil de détection.

Les deux associations non directement couplées au calcul d'un delta concernent TP53: la détection RAS sous traitement est observée chez 19/32 TP53-mut contre 1/12 TP53-WT; la médiane du VAF génomique maximal à fin de traitement est 20.38% contre 6.25%. Ces mesures à progression peuvent refléter la quantité de tumeur qui relargue de l'ADN ou le profil génomique, et non une résistance causée par TP53.

Un contrôle de confusion post-scan, défini après observation de la grille et donc non préenregistré, modélise log1p(VAF génomique maximal fin de traitement) selon TP53, log1p(VAF RAS prétraitement détecté) et dose parmi 37 cas complets. Coefficient TP53 Mut vs WT=1.132 (SE HC3=0.420, IC95% 0.278 à 1.985, p nominale=0.01091). Ce contrôle reste exploratoire, non corrigé pour la sélection du modèle et ne transforme pas cette cohorte en validation prédictive.

## Associations brutes les plus fortes après correction

| Contrôle | Flux | n | Test | Effet (type) | p | q globale |
|---|---|---:|---|---:|---:|---:|
| ras_vaf_pre | delta_pre_to_on_vaf_pp | 20 | patient-level permutation Spearman | Spearman_rho=-0.9925 | 0.0001 | 0.00455 |
| ras_vaf_pre | ras_vaf_on_status | 37 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.4235 | 0.0001 | 0.00455 |
| baseline_tp53 | ras_vaf_on_status | 44 | patient-level permutation Pearson chi-square | Cramers_V=0.5308 | 0.0011 | 0.03337 |
| baseline_tp53 | genomic_max_vaf_eot | 44 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-14.12 | 0.0016 | 0.0364 |
| ras_vaf_pre_status | ras_vaf_eot | 41 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-20.46 | 0.0048 | 0.0624 |
| kras_subtype | genomic_max_vaf_eot | 44 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.3261 | 0.0048 | 0.0624 |
| kras_subtype | ras_vaf_eot | 41 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.369 | 0.0038 | 0.0624 |
| baseline_tp53 | ras_vaf_eot | 41 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-19.59 | 0.0088 | 0.1001 |
| kras_subtype | acquired_kras_amp | 44 | patient-level permutation Pearson chi-square | Cramers_V=0.54 | 0.0106 | 0.1072 |
| baseline_tp53 | ras_vaf_eot_status | 44 | Fisher exact (patient-level 2x2) | odds_ratio=inf | 0.01661 | 0.1512 |
| best_response | acquired_myc_amp | 44 | patient-level permutation Pearson chi-square | Cramers_V=1 | 0.0224 | 0.1853 |
| kras_subtype | acquired_ras_cna | 44 | patient-level permutation Pearson chi-square | Cramers_V=0.503 | 0.0262 | 0.1987 |

## Règles de lecture

- Une ligne représente un patient. Les prélèvements prétraitement, sous traitement et fin de traitement restent des flux rattachés au même patient; ils ne sont jamais comptés comme trois patients.
- Les valeurs ‘Not detected’ et ‘Not tested’ restent distinctes et ne sont jamais remplacées par zéro. Les tests sur VAF numérique portent uniquement sur les valeurs détectées; la couverture apparaît dans field_coverage.csv.
- ‘delta’ est une différence entre étapes de prélèvement, pas une pente temporelle : les jours exacts et l’intervalle commun ne sont pas fournis.
- La matrice teste chaque contrôle préspecifié avec chaque flux. Elle mesure des associations simples et ne teste pas des interactions d’ordre supérieur ni la causalité. Les encodages dose continue/catégorielle et les mesures corrélées gonflent le nombre de comparaisons; la correction globale les couvre partiellement, pas le biais de sélection antérieur.
- Aucun T0/TLog n’est calculé : N=44 est inférieur au seuil séquentiel courant N≥50, et la cohorte est sélectionnée sur progression. Ici, la sortie honnête du pipeline est une cartographie multi-axes avec abstention sur le seuil.

Le tableau posthoc_TP53_eot_vaf_adjusted.csv est séparé de la famille primaire des 98 tests; son p nominal ne doit pas être lu comme une confirmation.

## Reproduction

Depuis la racine du projet Windows :

```powershell
.\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\multi_axis_resistance\pdac_multiaxis_resistance.py
```

Entrée source: table clinique supplémentaire de l’étude Aronchik et al., Nature Medicine 2026, DOI 10.1038/s41591-026-04537-w. Cette étude est l’origine des observations, pas une validation externe.
