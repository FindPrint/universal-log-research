# Rapport V2 — sensibilité synthétique aux transitions

**Date de génération :** 2026-11-22 17:06 UTC
**Statut technique :** passed
**Appels complets :** 35 sur 35
**Cœur :** v6.0.1-control-flux-exclusion-L7aL7b-CohenD
**Données :** synthétiques uniquement; aucune donnée patient, clinique ou biologique.

## Portée et lecture

Le protocole gelé couvrait des signaux nuls, faibles et forts, deux longueurs, plusieurs graines et cinq axes numériques. Les sorties ci-dessous décrivent les conditions testées. Le statut passed concerne les critères d’intégrité technique, pas l’exactitude des seuils.

## T0 et TLog par exécution

| N | Condition | Graine | Contrôle | Monotone | T0 (%) | Statut seuil | TLog sat. | TLog crit. | TLog div. | TLog nul | Repli cible |
|---:|---|---:|---|---|---:|---|---:|---:|---:|---:|---|
| 64 | null | 20261123 | time_index | True | 29.997 | available | -11.5657 | -6.2806 | -3.2534 | -6.4643 | False |
| 64 | null | 20261123 | signal_primary | False | 95.261 | available | -11.2697 | -5.6478 | -4.1589 | -6.5266 | True |
| 64 | null | 20261123 | marker_correlated | False | 95.039 | available | -11.5204 | -6.1367 | -4.1589 | -6.2506 | False |
| 64 | null | 20261123 | marker_oscillatory | False | 51.853 | available | -10.5823 | -6.4328 | -4.5740 | -6.5618 | False |
| 64 | null | 20261123 | noise_independent | False | 95.224 | available | -10.9764 | -5.5214 | -4.1589 | -6.1928 | False |
| 64 | null | 20261124 | time_index | True | 31.484 | available | -11.0024 | -7.7088 | -3.7090 | -6.5624 | False |
| 64 | null | 20261124 | signal_primary | False | 33.747 | available | -10.5749 | -6.2550 | -4.1589 | -6.2865 | True |
| 64 | null | 20261124 | marker_correlated | False | 29.125 | available | -10.8239 | -5.8105 | -4.1589 | -5.7990 | False |
| 64 | null | 20261124 | marker_oscillatory | False | 4.725 | available | -10.7524 | -6.2042 | -4.3608 | -6.1761 | False |
| 64 | null | 20261124 | noise_independent | False | 30.284 | available | -10.9650 | -5.9911 | -4.3673 | -6.0841 | False |
| 64 | weak | 20261123 | time_index | True | 29.997 | available | -11.4143 | -6.2296 | -3.3032 | -6.4259 | False |
| 64 | weak | 20261123 | signal_primary | False | 36.991 | available | -11.0424 | -6.1598 | -4.1589 | -6.4415 | True |
| 64 | weak | 20261123 | marker_correlated | False | 18.394 | available | -11.1009 | -5.7725 | -4.1589 | -6.7574 | False |
| 64 | weak | 20261123 | marker_oscillatory | False | 50.490 | available | -10.7825 | -5.7559 | -4.2964 | -7.0000 | False |
| 64 | weak | 20261123 | noise_independent | False | 95.224 | available | -10.6374 | -6.0270 | -4.3673 | -5.8571 | False |
| 64 | strong | 20261123 | time_index | True | 29.997 | available | -11.6060 | -6.3862 | -2.9311 | -6.4257 | False |
| 64 | strong | 20261123 | signal_primary | False | 38.304 | available | -11.2392 | -5.2728 | -3.9200 | -6.3569 | True |
| 64 | strong | 20261123 | marker_correlated | False | 7.664 | available | -10.5442 | -6.9322 | -4.1589 | -5.7425 | False |
| 64 | strong | 20261123 | marker_oscillatory | False | 47.480 | available | -10.6975 | -5.3720 | -4.1589 | -6.7182 | False |
| 64 | strong | 20261123 | noise_independent | False | 49.015 | available | -10.6609 | -6.5238 | -4.4338 | -6.1643 | False |
| 64 | strong | 20261124 | time_index | True | 61.988 | available | -11.4119 | -7.1260 | -3.2202 | -6.5810 | False |
| 64 | strong | 20261124 | signal_primary | False | 58.935 | available | -10.5737 | -6.6140 | -4.1589 | -6.2085 | True |
| 64 | strong | 20261124 | marker_correlated | False | 16.862 | available | -10.3094 | -6.7813 | -4.3804 | -5.5420 | False |
| 64 | strong | 20261124 | marker_oscillatory | False | 66.656 | available | -10.9118 | -6.3103 | -4.6696 | -6.3470 | False |
| 64 | strong | 20261124 | noise_independent | False | 66.567 | available | -10.7948 | -5.4744 | -4.4143 | -5.9801 | False |
| 100 | null | 20261125 | time_index | True | 73.176 | available | -11.3048 | -6.8892 | -5.1303 | -7.0889 | False |
| 100 | null | 20261125 | signal_primary | False | 32.318 | available | -11.2339 | -7.4123 | -5.1303 | -6.9892 | True |
| 100 | null | 20261125 | marker_correlated | False | 10.277 | available | -11.0950 | -6.7555 | -5.6829 | -6.6216 | False |
| 100 | null | 20261125 | marker_oscillatory | False | 86.323 | available | -11.4729 | -6.4749 | -5.6499 | -7.1999 | False |
| 100 | null | 20261125 | noise_independent | False | 14.843 | available | -11.3456 | -7.0760 | -4.6052 | -6.3851 | False |
| 100 | strong | 20261125 | time_index | True | 96.152 | available | -11.2966 | -6.8892 | -5.1078 | -7.1511 | False |
| 100 | strong | 20261125 | signal_primary | False | 53.357 | available | -10.9936 | -6.6060 | -5.0680 | -6.8675 | True |
| 100 | strong | 20261125 | marker_correlated | False | 70.276 | available | -11.6759 | -6.8441 | -5.7027 | -6.8212 | False |
| 100 | strong | 20261125 | marker_oscillatory | False | 88.277 | available | -11.9871 | -2.0339 | 5.6249 | -6.9800 | False |
| 100 | strong | 20261125 | noise_independent | False | 29.863 | available | -11.1940 | -6.6711 | -4.6052 | -6.2939 | False |

## Résumés descriptifs par N, condition et contrôle

| N | Condition | Contrôle | Runs | T0 disponibles | T0 médian (%) | T0 min–max (%) |
|---:|---|---|---:|---:|---:|---|
| 64 | null | marker_correlated | 2 | 2 | 62.082 | 29.125–95.039 |
| 64 | null | marker_oscillatory | 2 | 2 | 28.289 | 4.725–51.853 |
| 64 | null | noise_independent | 2 | 2 | 62.754 | 30.284–95.224 |
| 64 | null | signal_primary | 2 | 2 | 64.504 | 33.747–95.261 |
| 64 | null | time_index | 2 | 2 | 30.740 | 29.997–31.484 |
| 64 | strong | marker_correlated | 2 | 2 | 12.263 | 7.664–16.862 |
| 64 | strong | marker_oscillatory | 2 | 2 | 57.068 | 47.480–66.656 |
| 64 | strong | noise_independent | 2 | 2 | 57.791 | 49.015–66.567 |
| 64 | strong | signal_primary | 2 | 2 | 48.619 | 38.304–58.935 |
| 64 | strong | time_index | 2 | 2 | 45.993 | 29.997–61.988 |
| 64 | weak | marker_correlated | 1 | 1 | 18.394 | 18.394–18.394 |
| 64 | weak | marker_oscillatory | 1 | 1 | 50.490 | 50.490–50.490 |
| 64 | weak | noise_independent | 1 | 1 | 95.224 | 95.224–95.224 |
| 64 | weak | signal_primary | 1 | 1 | 36.991 | 36.991–36.991 |
| 64 | weak | time_index | 1 | 1 | 29.997 | 29.997–29.997 |
| 100 | null | marker_correlated | 1 | 1 | 10.277 | 10.277–10.277 |
| 100 | null | marker_oscillatory | 1 | 1 | 86.323 | 86.323–86.323 |
| 100 | null | noise_independent | 1 | 1 | 14.843 | 14.843–14.843 |
| 100 | null | signal_primary | 1 | 1 | 32.318 | 32.318–32.318 |
| 100 | null | time_index | 1 | 1 | 73.176 | 73.176–73.176 |
| 100 | strong | marker_correlated | 1 | 1 | 70.276 | 70.276–70.276 |
| 100 | strong | marker_oscillatory | 1 | 1 | 88.277 | 88.277–88.277 |
| 100 | strong | noise_independent | 1 | 1 | 29.863 | 29.863–29.863 |
| 100 | strong | signal_primary | 1 | 1 | 53.357 | 53.357–53.357 |
| 100 | strong | time_index | 1 | 1 | 96.152 | 96.152–96.152 |

## Localisation sur l’axe temporel

L’erreur absolue par rapport au centre injecté de 58 % est calculée uniquement pour le contrôle time_index dans les cas avec transition. Le cas nul n’a pas de position vraie.

| N | Condition | Runs | T0 dispo. | T0 médian (%) | Erreur absolue médiane (points %) | Étendue d’erreur (points %) |
|---:|---|---:|---:|---:|---:|---|
| 64 | null | 2 | 2 | 30.740 | non définie | non définie |
| 64 | strong | 2 | 2 | 45.993 | 15.996 | 3.988–28.003 |
| 64 | weak | 1 | 1 | 29.997 | 28.003 | 28.003–28.003 |
| 100 | null | 1 | 1 | 73.176 | non définie | non définie |
| 100 | strong | 1 | 1 | 96.152 | 38.152 | 38.152–38.152 |

Sur les 15 appels de condition nulle, T0 est disponible dans 15 cas. Ce décompte n’est pas un taux de fausses alertes : aucune règle d’alarme n’a été préspécifiée.

## Contrôles techniques

| Assertion | Résultat |
|---|---|
| seven_deterministic_input_datasets | PASS |
| all_35_pipeline_runs_complete | PASS |
| every_input_rotated_over_all_five_numeric_controls | PASS |
| selected_control_excluded_from_analyzed_fluxes | PASS |
| all_runs_declare_29_estimators | PASS |
| diagonal_target_control_fallback_explicit | PASS |
| oscillatory_control_retained_for_every_dataset | PASS |
| each_pipeline_input_individually_meets_minimum | PASS |

## Temps d’exécution observés

Temps mural par appel du pipeline, rapporté par le harnais; les mesures comprennent le travail complet de l’appel dans la configuration gelée. Ce tableau n’est pas un profil par estimateur.

| Contrôle | Appels | Médiane (s) | P90 (s) | Min–max (s) |
|---|---:|---:|---:|---:|
| marker_correlated | 7 | 148.1 | 398.3 | 145.8–729.6 |
| marker_oscillatory | 7 | 159.2 | 355.0 | 144.1–622.3 |
| noise_independent | 7 | 148.0 | 249.7 | 145.7–371.8 |
| signal_primary | 7 | 159.6 | 301.6 | 145.5–499.5 |
| time_index | 7 | 161.9 | 177.4 | 158.8–177.4 |

Cinq appels les plus longs (description de cette campagne uniquement) :

| N | Condition | Graine | Contrôle | Temps (s) |
|---:|---|---:|---|---:|
| 64 | strong | 20261124 | marker_correlated | 729.6 |
| 64 | null | 20261124 | marker_oscillatory | 622.3 |
| 64 | strong | 20261124 | signal_primary | 499.5 |
| 64 | null | 20261124 | noise_independent | 371.8 |
| 64 | null | 20261123 | time_index | 177.4 |

## Limites et interprétation

- Les niveaux d’amplitude, tailles, graines et formes de flux sont des paramètres synthétiques de conception.
- Le nombre de réplicats reste faible; les tableaux sont descriptifs et aucun test statistique ni intervalle inférentiel n’est présenté.
- Une vérité de transition n’est définie que sur l’axe temporel et pour les signaux non nuls.
- Le contrôle diagonal avec la cible est signalé; le contrôle oscillatoire est conservé.
- Les résultats ne valident ni TLog, ni la théorie générale, ni une application PDAC, ni un biomarqueur, ni un traitement.

## Empreintes

- Protocole SHA-256 : 694442710711cafc4df4c61b974ac174a6e3391f097f9291d1ef4cdeb74639b1
- Harnais SHA-256 : cef978539ec549aa32a8de4194135a03984d3dad3b86a1d949451b25a3809afd
- Pipeline v6.0.1 SHA-256 : ce0557cb4c44c15a142291e5522b446f7212136686c3035c97f12a3d0e959086
- Plan SHA-256 : f7f1d80fcd7a0cee0fb363b8f82f7644de483538a1a7fa02ab8c80b389a5cb17

Les sorties natives par contrôle, leurs figures et journaux sont conservés dans le snapshot complet V11, à part du PDF.
