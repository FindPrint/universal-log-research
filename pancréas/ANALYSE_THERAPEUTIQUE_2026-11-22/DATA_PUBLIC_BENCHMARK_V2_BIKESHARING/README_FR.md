# Bike Sharing — domaine mobilité et série temporelle

Jeu horaire Capital Bikeshare 2011–2012, téléchargé depuis l’archive officielle UCI. Il est publié sous CC BY 4.0; voir `dataset_manifest.json` pour l’attribution et les empreintes des fichiers.

Ce dossier sépare trois objets :

1. une tâche d’estimation horaire de `cnt`, sans `casual`/`registered` qui reconstituent exactement la cible; le benchmark V1 initial est conservé et la V2 ajoute un témoin d’apprentissage `weekday × hr` plus adapté à la périodicité;
2. le comportement descriptif de v6.0.1 quand chaque flux numérique est proposé comme axe de contrôle sur 100 blocs temporels;
3. les effets de mesure, d’agrégation, d’ordre et de météo observée.

La météo mesurée à l’heure cible rend le benchmark rétrospectif conditionnel à l’observation météo; il ne s’agit pas d’une prévision future opérationnelle. Le T0 du pipeline reste un repère descriptif et ne remplace pas les métriques de prédiction.

L'audit postérieur des horodatages compte 165 créneaux sans ligne entre les deux extrémités du CSV; le Readme ne documente pas leur cause et aucune valeur n'a été imputée. Il constate aussi que `hum` vaut 1 dans 270 lignes et `windspeed` vaut 0 dans 2 180 lignes. Ces accumulations motivent une piste de vérification de la normalisation et de la collecte; elles ne prouvent ni écrêtage ni seuil de capteur. Les fichiers fournis n'indiquent pas le modèle des capteurs météo, leur étalonnage, l'incertitude instrumentale ou la disponibilité des vélos par station. Voir `RESULTS_MEASUREMENT_PROCESS_AUDIT_V1_FR.md` et `measurement_process_audit_v1.json`.

Reproduction dans le `.venv` du projet :

```powershell
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V2_BIKESHARING\fetch_bike_sharing_dataset.py"
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V2_BIKESHARING\run_bike_prediction_benchmark_v1.py" --output-dir "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V2_BIKESHARING\prediction_benchmark_v1_reproduction"
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V2_BIKESHARING\run_bike_prediction_benchmark_v2.py"
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V2_BIKESHARING\run_bike_prediction_benchmark.py"
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V2_BIKESHARING\run_bike_pipeline_control_rotation.py" --prepare-only
```

Après vérification du plan gelé, lancer la rotation complète en retirant `--prepare-only`. Un seul axe contrôle peut prendre plusieurs dizaines de minutes; `season` a duré 2 334 s lors de la campagne V1. Le protocole prédictif V1 et ses amendements V2/V3 sont séparés dans leurs fichiers dédiés; la rotation du pipeline suit son propre protocole.
