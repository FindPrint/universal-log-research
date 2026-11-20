# Scan clinique multiaxial étendu — résistance au daraxonrasib

**Exécution:** 17 novembre 2026 · **patients:** 57 · **flux:** 14 · **contrôles:** 8 · **famille:** BH globale sur tests estimables.

## Résultat

La grille contrôle × flux produit **112 comparaisons prévues**, dont **106 estimables** après gestion explicite des données absentes/censurées. Les associations avec q BH globale < 0,05 sont **7**.

Cette analyse est descriptive/exploratoire et ne donne ni prédicteur validé, ni combinaison thérapeutique, ni preuve de guérison. Elle réunit les 44 patients de la strate 160–300 mg et les 13 patients du tableau supplémentaire à ≤120 mg, tous avec des prélèvements ctDNA prétraitement et fin de traitement; il n’y a pas de groupe comparateur de patients sans progression. Les strates proviennent du même essai et ne sont pas randomisées entre elles. Le test de TP53 contre amplification KRAS fait partie des comparaisons et sa valeur brute connue n’est pas une validation indépendante. Il s’agit d’un module compagnon typé, pas d’une intégration au code universel principal ni d’une démonstration d’universalité du pipeline.

Le contraste déjà rapporté TP53 prétraitement ↔ amplification KRAS acquise retrouve p=0.02216, mais q BH globale=0.1064; il ne franchit pas la grille élargie.

Parmi les 7 associations q<0,05, le lien baseline RAS-VAF ↔ différence prétraitement/sous-traitement est mathématiquement couplé, car la valeur initiale entre dans le calcul du delta (rho=-0.994, q=0.0106); il ne constitue pas une preuve biologique indépendante. Le lien baseline VAF–détection sous traitement est aussi sensible au seuil de détection.

Les associations TP53 qui passent la correction portent sur des flux de détection de ctDNA et de VAF à la fin du traitement/progression. Elles peuvent refléter la quantité de tumeur qui relargue de l'ADN ou le profil génomique, et non une résistance causée par TP53. Dans la strate principale 160–300 mg, la détection RAS sous traitement est observée chez 24/41 TP53-mut contre 2/16 TP53-WT dans l’ensemble des 57 patients; la médiane du VAF génomique maximal à fin de traitement est 17.06% contre 4.58%. Les autres associations significatives de la grille incluent également des statuts de détection dépendants du seuil analytique.

Un contrôle de confusion post-scan, défini après observation de la grille et donc non préenregistré, modélise log1p(VAF génomique maximal fin de traitement) selon TP53, log1p(VAF RAS prétraitement détecté) et dose parmi 44 cas complets. Coefficient TP53 Mut vs WT=0.972 (SE HC3=0.397, IC95% 0.171 à 1.774, p nominale=0.01871). Ce contrôle reste exploratoire, non corrigé pour la sélection du modèle et ne transforme pas cette cohorte en validation prédictive.

## Associations brutes les plus fortes après correction

| Contrôle | Flux | n | Test | Effet (type) | p | q globale |
|---|---|---:|---|---:|---:|---:|
| ras_vaf_pre_status | ras_vaf_on_status | 56 | patient-level permutation Pearson chi-square | Cramers_V=0.5039 | 0.0003 | 0.0106 |
| ras_vaf_pre | ras_vaf_on_status | 44 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.3538 | 0.0002 | 0.0106 |
| ras_vaf_pre | delta_pre_to_on_vaf_pp | 25 | patient-level permutation Spearman | Spearman_rho=-0.9938 | 0.0001 | 0.0106 |
| baseline_tp53 | genomic_max_vaf_eot | 57 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-12.48 | 0.001 | 0.0212 |
| baseline_tp53 | ras_vaf_on_status | 57 | patient-level permutation Pearson chi-square | Cramers_V=0.4779 | 0.0009 | 0.0212 |
| kras_subtype | ras_vaf_eot | 49 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.3339 | 0.0014 | 0.02473 |
| ras_vaf_pre_status | ras_vaf_eot | 48 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-17.66 | 0.0033 | 0.04997 |
| baseline_tp53 | ras_vaf_eot_status | 57 | Fisher exact (patient-level 2x2) | odds_ratio=11.7 | 0.004266 | 0.05652 |
| dose_stratum | delta_pre_to_on_vaf_pp | 25 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=13.72 | 0.0056 | 0.06596 |
| dose_stratum | genomic_max_vaf_eot | 57 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-10.19 | 0.0081 | 0.06605 |
| ras_vaf_pre_status | genomic_max_vaf_eot | 56 | patient-level permutation rank test (2 groups) | median_difference_level1_minus_level0=-11.73 | 0.0081 | 0.06605 |
| kras_subtype | genomic_max_vaf_eot | 57 | patient-level permutation Kruskal-Wallis | rank_H_scaled_exploratory=0.2439 | 0.0065 | 0.06605 |

## Règles de lecture

- Une ligne représente un patient. Les prélèvements prétraitement, sous traitement et fin de traitement restent des flux rattachés au même patient; ils ne sont jamais comptés comme trois patients.
- Les valeurs ‘Not detected’ et ‘Not tested’ restent distinctes et ne sont jamais remplacées par zéro. Les tests sur VAF numérique portent uniquement sur les valeurs détectées; la couverture apparaît dans field_coverage.csv.
- ‘delta’ est une différence entre étapes de prélèvement, pas une pente temporelle : les jours exacts et l’intervalle commun ne sont pas fournis.
- La matrice teste chaque contrôle préspecifié avec chaque flux. Elle mesure des associations simples et ne teste pas des interactions d’ordre supérieur ni la causalité. Les encodages dose continue/catégorielle et les mesures corrélées gonflent le nombre de comparaisons; la correction globale les couvre partiellement, pas le biais de sélection antérieur.
- Aucun T0/TLog n’est calculé : les 57 patients sont des unités indépendantes et les étapes prétraitement/sous-traitement/fin de traitement n’ont pas de temps écoulé commun permettant d’estimer une trajectoire temporelle homogène. La sortie est une cartographie multi-axes; l’abstention sur le seuil temporel est intentionnelle.

Le tableau posthoc_TP53_eot_vaf_adjusted.csv est séparé de la famille primaire des 112 tests; son p nominal ne doit pas être lu comme une confirmation.

## Reproduction

Depuis la racine du projet Windows :

```powershell
.\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\multi_axis_resistance\pdac_multiaxis_resistance_all57.py
```

Entrées sources: tableaux supplémentaires de l’étude Aronchik et al., Nature Medicine 2026, DOI 10.1038/s41591-026-04537-w. Cette étude est l’origine des observations, pas une validation externe.
