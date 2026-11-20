# GSE271300 — analyse exploratoire au niveau animal

Date UTC : 2026-11-19T23:00:04.475625+00:00
Source : https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300

## Question
Dans PC69 et PC106, la monothérapie MRTX1133 est-elle associée à un changement de la fraction de cellules tumorales classées basales, en traitant chaque souris comme unité biologique ?

## Résultat principal

Le jeu GSE271300 est le jeu de séquençage unicellulaire de l’article de Singhal et al. (Cancer Discovery, 2024). Cet article rapporte déjà l’enrichissement de l’état classique sous inhibition de KRAS. Les calculs ci-dessous auditent ce même jeu au niveau souris : ils ne constituent ni une réplication expérimentale indépendante ni une validation du pipeline UNIVERSAL_LOG.

| Modèle | n souris MRTX / véhicule | Différence de fraction basale (MRTX − véhicule) | Cohen d entre souris | p exacte bilatérale |
|---|---:|---:|---:|---:|
| PC69 | 3 / 3 | -0.5727 | -12.75 | 0.1 |
| PC106 | 4 / 3 | -0.03322 | -3.986 | 0.02857 |

Les valeurs par souris sont dans `GSE271300_mouse_level_summaries.csv`; l’image montre chaque souris séparément.

## Sensibilité PC106

Les cellules véhicule sont assignées par le plus grand des trois comptes HTO après jointure exacte des barcodes QC/analyse. Une analyse de sensibilité conserve seulement les cellules où le premier tag est au moins deux fois le second. Ce seuil est une règle exploratoire de qualité, pas une règle validée dans l’article.

Résultat primaire de cette sensibilité : {"analysis": "PC106_vehicle_HTO_ratio_ge_2_sensitivity", "model": "PC106", "outcome": "basal_fraction", "primary_endpoint": true, "mouse_values": "{\"PC106-ANS184-VEH-B0252\": 0.060109289617486336, \"PC106-ANS185-VEH-B0253\": 0.03301540719002201, \"PC106-ANS187-VEH-B0254\": 0.042071197411003236, \"PC106-ANS188-MRTX1-B0255\": 0.005434782608695652, \"PC106-ANS189-MRTX2-B0256\": 0.018691588785046728, \"PC106-ANS190-MRTX3-B0257\": 0.011363636363636364, \"PC106-ANS191-MRTX4-B0258\": 0.009549795361527967}", "n_mice": 7, "n_mrtx": 4, "n_vehicle": 3, "difference_mrtx_minus_veh": -0.033805347293110515, "cohens_d_mice": -3.4772120229747965, "p_exact_two_sided": 0.02857142857142857, "permutations": 35, "exchangeability_assumption": "mouse-level treatment labels are exchangeable within this PDX model"}

## Méthode et limites

- PC69 : affectation par la colonne `Classification`; doublets/négatifs exclus.
- PC106 MRTX : affectation par `Classification`; doublets/négatifs exclus.
- PC106 véhicule : jointure exacte des identifiants cellulaires entre H5AD analysé et QC; affectation HTO par argmax; test de sensibilité avec ratio ≥ 2.
- Mesure primaire : part basale parmi cellules basal/classical assignées, d’abord calculée par souris. Chaque souris reçoit le même poids dans la comparaison.
- Test : permutation exacte bilatérale des étiquettes de traitement entre souris au sein de chaque modèle; l’échangeabilité des groupes est une hypothèse.
- Les scores de cellule et le cycle cellulaire sont secondaires et exploratoires. Aucun test cellule par cellule n’est utilisé.
- GA60 est laissé hors de l’inférence animale faute de tags individuels disponibles dans les fichiers inspectés.
- Il s’agit de xénogreffes précliniques et de MRTX1133 seul. Ces données ne démontrent ni efficacité chez l’humain, ni bénéfice d’une combinaison, ni remède.
- Le TLog n’est pas calculé : ces groupes sont des instantanés non ordonnés. Avec seulement 6–7 souris, le minimum standard de série / walk-forward du pipeline ne convient pas; les cellules ne doivent pas être utilisées pour gonfler N.
- Les cibles EGFR/ERBB2/ERBB3/STAT3/KRAS et les marqueurs d’état sont résumés dans `GSE271300_target_expression_by_mouse_state.csv`. La matrice QC est sparse et contient des flottants non entiers sans couche de comptes bruts : ces moyennes ne sont pas des tests de différentiel d’expression de type DESeq2. Une abondance d’ARN ne prouve ni protéine, ni phosphorylation, ni dépendance thérapeutique.
- GA60 est présenté en description agrégée seulement; ses cellules ne remplacent pas des répétitions animales.

## Limite d’interprétation statistique

Le nombre de souris est trop petit pour une validation confirmatoire. Les p exactes ont une résolution très grossière; les différences et les valeurs individuelles sont plus informatives pour planifier une expérience plus large que pour établir un fait clinique.

## Reproduction

Depuis le dossier racine du projet, avec `.venv` actif :
```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-19\analyze_GSE271300_mouse_level.py
```
Les sources H5AD originales restent dans `data_GSE271300`; les SHA-256 et diagnostics de jointure sont dans `GSE271300_ANALYSIS_REPORT.json`.
