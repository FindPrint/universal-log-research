# Sensibilité interne par niveau de dose — TP53 et amplification KRAS

**Date d’exécution:** 2026-11-17. **Analyse ciblée exploratoire**, ajoutée après la grille principale.

## Question

L’association prétraitement TP53 ↔ amplification KRAS acquise observée dans la cohorte 160–300 mg est-elle directionnellement compatible avec la cohorte publiée à ≤120 mg? Le contraste porte sur le statut TP53 prétraitement et l’amplification KRAS acquise reportée à la progression.

## Résultats descriptifs et tests exacts

| Strate | TP53 mut avec KRAS AMP | TP53 mut total | TP53 WT avec KRAS AMP | TP53 WT total | OR | p Fisher bilatérale nominale |
|---|---:|---:|---:|---:|---:|---:|
| 160-300 mg | 15 | 32 | 1 | 12 | 9.706 | 0.03215 |
| <=120 mg | 1 | 9 | 0 | 4 | inf | 1 |
| pooled 20-300 mg; descriptive only | 16 | 41 | 1 | 16 | 9.6 | 0.02216 |

Dans la petite strate ≤120 mg, les proportions observées sont 11.1% pour TP53-mut (1/9) et 0.0% pour TP53-WT (0/4). Dans la strate 160–300 mg, elles sont 46.9% et 8.3%.

L’OR infini de la petite strate est dû à une cellule nulle (0/4 TP53-WT avec KRAS AMP); le test exact donne p=1. Ce n’est pas une estimation stable d’un effet très grand. Le résultat regroupé 57-patients (p=0.02216) est nominal, inclut la cohorte principale et ne fournit aucune réplication indépendante.

## Interprétation permise

Cette analyse ne constitue pas une réplication indépendante: les deux strates proviennent du même essai de phase 1/2 et sont des cohortes appariées prétraitement/fin de traitement publiées dans le même article. La strate ≤120 mg est petite; son test exact peu puissant et son OR à cellule nulle sont fragiles. La comparaison par dose est descriptive, car dose, époque d’inclusion, durée d’exposition et sélection clinique ne sont pas randomisées ici. Les p sont nominales et ne valent pas validation après la sélection postérieure de cette question. Dans le scan multiaxial complet des 57 patients, le lien TP53–KRAS AMP ne passe pas la correction BH globale (voir rapport principal).

Aucune conclusion de causalité, de prédiction avant traitement, de choix de combinaison, d’efficacité clinique ou de guérison n’en découle. Le signal de la cohorte principale reste une hypothèse à tester dans une cohorte indépendante incluant aussi les patients sans progression.

## Reproduction

Depuis la racine du projet, exécuter:

```powershell
.\.venv\Scripts\python.exe pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\multi_axis_resistance\analyze_low_dose_internal_sensitivity.py
```

Entrées: `clinical_high_dose_44.csv` et `clinical_lower_dose_13.csv`, extraites des tableaux supplémentaires de l’article cité dans le manifeste. Le script conserve une ligne par patient et utilise Fisher exact bilatéral pour le seul contraste défini dans cet addendum après la grille principale.
