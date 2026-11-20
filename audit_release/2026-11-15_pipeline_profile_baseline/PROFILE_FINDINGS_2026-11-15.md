# Rapport de profilage et d'optimisation — UNIVERSAL_LOG

**Date d'exécution :** 2026-11-15  
**Dépôt de départ :** `15908de1d8dc57d084c494a0f3ddcd1dc0b41a92`  
**Version de référence :** `UNIVERSAL_LOG_v5.9.2.py`  
**Objet :** identifier les coûts logiciels, tester des modifications réversibles, et séparer les observations des hypothèses.

## 1. Conclusion exécutive

Le profil montre plusieurs coûts élevés dans les estimateurs, le calcul des diagnostics et le rendu graphique. Deux pistes ont été testées sur la même petite entrée : une branche scalaire optimisée de division (`v5.9.3`) et un mode CLI sans figures (`v5.9.4 --no-plots`). Une troisième configuration a limité la liste d'horizons à `1,3,6,12`.

**Aucun gain de temps de bout en bout n'est démontré.** Les exécutions complètes donnent 430 à 777 secondes selon la variante et le run; il n'y a qu'un run complet par configuration pertinente, sans plan de répétition assez stable pour attribuer l'écart au code. L'option sans figures a bien supprimé les PNG et conservé les sorties numériques comparées, mais son exécution observée a duré davantage que l'unique référence complète.

Ces essais ne valident pas la théorie TLog, ne démontrent pas l'universalité scientifique du pipeline et ne mesurent pas ses performances sur des données empiriques réelles ou dans un autre domaine. Le CSV de ce profil est une simulation d'Ising classique.

## 2. Environnement, entrée et commande

- Python : 3.11.9 du `.venv` du projet.
- Entrée : `audit_release/2026-11-14_l7b_full_reduced/data/L16_T2.269185_chain0_first80.csv`.
- Données : 80 lignes, 15 colonnes; trajectoire Ising classique simulée, `L=16`, `T=2.269185`, chaîne 0.
- SHA-256 entrée : `b76a2ef1ddc50855baa8959714744e0764304bbe9408c6842c5596530ad9c216`.
- Cible/contrôle : `Abs_magnetization` / `MC_Update`.
- Mode `fast`, un worker, L7b désactivé, graine `20261108`, `PYTHONHASHSEED=0`; flux par défaut du pipeline conservés.
- Configuration utilisée pour la référence : source v5.9.2, SHA-256 `c02d7e1a4081fcdcb2ccaa9acb17f3818e9950d297cb262ec5da63ca2695dedd`.

L'entrée est un test logiciel très court. Elle ne constitue pas un jeu empirique, un échantillon de systèmes physiques indépendants, ni une preuve de mise à l'échelle.

## 3. Toutes les tentatives de durée consignées

| Essai | Source/configuration | Durée (s) | Code de sortie | Interprétation |
|---|---|---:|---:|---|
| 8 000 lignes | v5.9.2, simulation Ising complète | 373,048 | -1 | Interrompu avant résultat; pas de durée complète |
| 1 024 lignes | v5.9.2, préfixe déterministe | 320,184 | -1 | Interrompu; mémoire observée par échantillonnage jusqu'à environ 1,545 Go, ce n'est pas une mesure de pic continue |
| 80 lignes — référence | v5.9.2, 12 horizons par défaut | 441,265 | 0 | Un run complet |
| 80 lignes — répétition | même commande | 49,472 | -1 | Interrompue; ne compte pas comme répétition complète |
| 80 lignes — cProfile | v5.9.2, même entrée/config | 817,810 | 0 | Profil complet; l'instrumentation augmente le temps, comparaison directe invalide |
| 80 lignes — division scalaire | candidate v5.9.3 | 482,658 | 0 | Un run complet; pas de gain démontré |
| 80 lignes — horizons limités | v5.9.2, `--horizons 1,3,6,12` | 430,380 | 0 | Un run complet; configuration de sortie différente pour les résultats dépendant des horizons |
| 80 lignes — sans figures | candidate v5.9.4, `--no-plots` | 776,502 | 0 | Un run complet; aucun PNG; accélération non démontrée |

Les journaux JSON, sorties console, scripts et, le cas échéant, fichiers de profil se trouvent dans les sous-dossiers `baseline_run_01/`, `sample_1024/` et `sample_80/`. Les temps interrompus sont conservés pour qu'ils ne soient pas confondus avec des runs réussis.

## 4. Résultats cProfile

Le run instrumenté comptabilise 262 471 313 appels de fonctions (239 383 812 primitifs); temps interne total rapporté : 813,663 s. Les premières fonctions par temps cumulé incluent :

| Fonction / famille | Appels | Temps cumulé (s) |
|---|---:|---:|
| `apply_complexity` | 2 670 | 414,595 |
| `_compute_extra_estimators` | 2 516 | 368,570 |
| `run_pipeline` | — | 331,468 |
| `_safe_call` | 52 836 | 313,267 |
| `level_target_universal` | — | 152,301 |
| `pyplot.savefig` et rendu associé | 14 sauvegardes | environ 152,301 |
| `local_pca_dimension` | 2 516 | 65,983 |
| `compute_noise_diagnostic` | — | 60,951 |
| `plot_separation_heatmap` | — | 59,009 |
| `compute_estimator_redundancy` | — | 57,866 |
| `mfdfa_spectrum` | — | 54,593 |
| `hurst_rs` | — | 46,082 |
| `danco_dimension` | — | 45,824 |
| `levina_bickel` | — | 40,224 |
| `graph_cluster_dimension` | — | 35,020 |

Les temps cumulés parent/enfant se recouvrent : il ne faut pas les additionner. Le cProfile a ralenti l'exécution; ses temps localisent des pistes, mais ne donnent pas un chronométrage neutre. Le fichier complet est `sample_80/cprofile_top_cumulative.txt` et le binaire associé `sample_80/cprofile_run/pipeline.pstats`.

### Hypothèse de coût scalaire

`_safe_divide` a été appelé 1 236 943 fois dans le profil (55,612 s cumulées); `_safe_log` environ 870 000 fois. Un microbenchmark isolé de 50 000 divisions scalaires répétées cinq fois a mesuré un médian environ 5,1 fois plus rapide pour une branche scalaire spécialisée, avec sept cas limites identiques.

**Limite du résultat :** ce microbenchmark est un résultat local de code, pas une preuve que la pipeline entière accélère. La candidate v5.9.3 (SHA-256 `4176e5406657fc59d16d532efb91512c2cd5d6dbf09c80770f376d64295ab20f`) a pris 482,658 s contre 441,265 s pour la référence dans deux runs uniques. La variante ne doit donc pas être annoncée comme « plus rapide » sur cette base.

## 5. Test `--no-plots` — candidate v5.9.4

### Modification

Le run chronométré a utilisé le snapshot exact `UNIVERSAL_LOG_v5.9.4_profiled.py`, SHA-256 `25122d29573fcacb7c12d7e6ef2919a022d79235f7214fcdc03ad488a717185b`. Il est conservé à la racine du projet et le `run_record.json` le référence. Le fichier utilisable/maintenu est `UNIVERSAL_LOG_v5.9.4.py`, SHA-256 actuel `72fd242c4cb26e5663fa40f1b4998de60c63e2aebbae2773d0d34d904152001b`.

Ajout d'un argument CLI opt-in `--no-plots` et d'un argument de fonction `generate_plots=True`. La valeur par défaut garde le rendu normal. Quand l'option est activée, le pipeline saute les appels Matplotlib mais continue le calcul des diagnostics et les exports CSV/JSON; le tableau `dashboard.html` reste séparément piloté par `--no-dashboard`. Le flag `plots_generated` est inscrit dans le bloc runtime des résultats.

La branche sans graphiques a été exécutée avec le même CSV, la même graine et les mêmes colonnes que la référence. Résultat : 776,502 s, code 0. Le test compile et termine normalement.

### Parité vérifiée

SHA-256 exact identique entre référence et `--no-plots` pour chacun de ces fichiers :

- `df_feat.csv`
- `scores.json`
- `transition_analysis.json`
- `estimator_redundancy.csv` et `estimator_redundancy.json`
- `estimator_four_tests.csv`
- `estimator_measurement_types.csv` et `estimator_measurement_types.json`
- `csd_consensus.csv` et `csd_consensus.json`
- `csd_fractal_estimators.csv` et `csd_fractal_estimators.json`
- `noise_diagnostic.json`
- `scan_curve.json`
- `csd_correlation.json`
- `fluxes_raw.csv`

La mesure/export de redondance contient 29 estimateurs. Les arbres `T_log_by_estimator` sont exactement égaux dans les deux sections correspondantes de `master_results.json`; chacun contient 21 estimateurs éligibles à cette mesure TLog. Cela contrôle la préservation logicielle pour ce cas, pas la validité théorique de TLog.

Le `master_results.json` complet diffère sur six chemins attendus : trois versions inscrites dans les sorties, deux chemins absolus vers les journaux/dashboard, et `runtime.plots_generated`. Après traitement correct des valeurs NaN, aucune autre différence n'est relevée par `compare_output_modes.py`. Cette comparaison est enregistrée et reproductible.

La sortie de référence contient 14 PNG; la sortie `--no-plots` en contient zéro. Le HTML de dashboard/table reste généré indépendamment.

Après le run, l'inspection du journal a révélé un message de console trompeur quand l'état holographique était valide et que les figures étaient désactivées. Le fichier maintenu corrige uniquement cette branche d'affichage du message; il a passé `py_compile`. Le fichier exact exécuté reste disponible sous `UNIVERSAL_LOG_v5.9.4_profiled.py`, de sorte que le chronométrage et les résultats cités conservent un hash reproductible. La correction de message n'a pas été suivie d'un second run complet.

### Interprétation du temps

Le run `--no-plots` a duré 335,238 s de plus (environ 76 %) que l'unique run complet de référence. Cette différence n'établit pas une régression attribuable au flag : le nombre de répétitions est insuffisant et les durées précédentes varient largement. Elle signifie cependant que **l'expérience n'apporte aucune preuve d'accélération**. À ce stade, `--no-plots` peut servir à éviter des fichiers et coûts de rendu selon l'environnement, mais il n'est pas démontré qu'il réduise le temps mur total de cette tâche.

## 6. Test de réduction des horizons

Le run à quatre horizons garde la source de référence v5.9.2 et modifie seulement la configuration CLI (`--horizons 1,3,6,12`). Il a pris 430,380 s, soit 10,885 s de moins que l'unique run de référence (environ 2,46 %).

Les mêmes exports numériques sélectionnés et les 21 valeurs TLog ont été observés. Les résultats associés aux horizons omis sont naturellement absents ou réduits dans les sections `prediction_levels`, `run_pipeline` et `runtime`. Le délai observé est trop proche et les répétitions trop peu nombreuses pour conclure à un gain mesuré. Cette option est un compromis de couverture des horizons, pas une accélération prouvée.

## 7. Ce que ces expériences disent du pipeline

### Résultat établi sur le cas testé

- La pipeline exécute ici un grand nombre de calculateurs pour chaque flux/estimateur et paie un coût important dans les chemins d'estimation, de diagnostic, de normalisation/division et de rendu.
- Le mode sans figures préserve les exports numériques comparés sur ce cas et supprime les PNG.
- Les exports TLog et estimateurs inspectés sont reproductibles entre la référence et le mode sans figures avec ces entrées/options.

### Ce qui demeure hypothèse ou inconnu

- Le classement cProfile sera-t-il le même avec plus de lignes, moins de flux, d'autres axes/contrôles ou un autre domaine?
- Le gain local de division scalaire subsistera-t-il sur des runs contrôlés et répétés?
- Le rendu est-il un poste dominant en temps mur sur une machine moins chargée?
- Les valeurs/estimateurs sont-ils valides sur des mesures empiriques et transférables d'un domaine à l'autre?
- Les résultats Ising identifient-ils correctement une transition et une universalité? Ce profil logiciel ne répond pas à ces questions.

Les termes « résultat » et « hypothèse » dans ce rapport distinguent les sorties directement mesurées des propositions à tester.

## 8. Modifications, préservation et état Git

- Le dépôt local a été initialisé comme demandé et le premier commit `15908de1d8dc57d084c494a0f3ddcd1dc0b41a92` conserve l'état initial du dossier.
- `UNIVERSAL_LOG_v5.9.2.py` n'a pas été modifié.
- `UNIVERSAL_LOG_v5.9.3.py`, `UNIVERSAL_LOG_v5.9.4.py` et le snapshot testé `UNIVERSAL_LOG_v5.9.4_profiled.py` sont des candidates distinctes, non promues comme versions supérieures confirmées.
- Les scripts de lancement, paramètres, hash d'entrée/source, versions Python, durées, journaux, profil, comparaisons et README sont gardés dans ce dossier.

## 9. Proposition pour la suite

Pour rendre les prochaines avancées plus rapides **et** probantes :

1. Ajouter une mesure de temps par étape (estimateurs, diagnostics, sorties, plots) qui n'enregistre que des durées et reste désactivée par défaut; cProfile a trop d'overhead pour une mesure de performance neutre.
2. Sélectionner un sous-ensemble d'estimateurs/flux seulement après une mesure par composant; conserver un profil `full` identique à la référence et inscrire chaque sous-ensemble dans le manifeste.
3. Faire des runs appariés et alternés référence/candidate sur la même entrée, par exemple cinq paires, et publier médiane, dispersion, hashes des sorties, version et charge/configuration machine. Aucun changement de vitesse ne devrait être annoncé sur un seul run.
4. Inclure au moins un CSV de mesures empiriques documenté et un CSV indépendant d'un autre domaine; comparer les mêmes axes, contrôles et flux déclarés, sans présenter des générateurs synthétiques comme données réelles.
5. Séparer ces tests logiciels des tests scientifiques : pour Ising, documenter tailles, graines, thermalisation, échantillonnage, calcul de susceptibilité/chaleur/Binder et incertitudes avant d'évaluer une transition critique.

Ces étapes sont des recommandations à vérifier, non des résultats déjà acquis.

## 10. Inventaire local des entrées CSV

Après le profilage, le projet a été parcouru avec `rg --files -g '*.csv' -g '!**/.venv/**' -g '!**/node_modules/**'`. La liste horodatée contient 765 chemins. Une recherche de noms évoquant des observations empiriques, des mesures, des expériences ou des domaines indépendants a surtout relevé des CSV Ising simulés, des exports de pipeline, des résultats d'audit et des catalogues de fichiers. Je n'ai pas identifié de CSV documenté comme jeu empirique externe et non-Ising dans cet inventaire.

Cette recherche par noms n'est pas une preuve que le dossier ne contient aucune donnée réelle sous un nom inattendu; elle indique qu'aucun jeu empirique exploitable n'est actuellement identifié et décrit comme tel. La liste est conservée dans `dataset_csv_inventory_2026-11-15.txt`. Pour un test réel multi-domaine, le rapport doit enregistrer pour chaque jeu sa source, sa licence, son unité d'observation, l'axe temporel ou de progression, le contrôle, la cible, les flux candidats et leur dépendance éventuelle.
