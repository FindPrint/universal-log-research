# AI4I 2020 — benchmark public et traçabilité

## Source, licence et attribution

Le fichier est un miroir Kaggle publié par son auteur, Stephan Matzka. Le CSV extrait a été téléchargé séparément depuis UCI et comparé octet pour octet : les deux fichiers sont identiques. La page UCI décrit le jeu comme synthétique et l’indique sous licence **CC BY 4.0**.

Citation : Stephan Matzka. *AI4I 2020 Predictive Maintenance Dataset* (2020), UCI Machine Learning Repository, DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C). Le fichier source Kaggle est référencé dans `dataset_manifest.json`.

Les données brutes ont été copiées sans transformation dans `source/ai4i2020.csv`. Le jeu n’est pas une cohorte d’usine réelle; les résultats ne démontrent pas de performance dans une installation industrielle.

## Reproduire

Dans le dossier du projet, avec Python 3.11 :

```powershell
.\.venv\Scripts\python.exe -m pip install -r "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V1\requirements-ai4i-benchmark.txt"
.\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V1\run_ai4i_prediction_benchmark.py"
.\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V1\run_ai4i_pipeline_control_rotation.py" --prepare-only
.\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V1\run_ai4i_pipeline_control_rotation.py"
```

Le dernier appel exécute une rotation reprenable sur les 12 colonnes numériques, sur 100 blocs consécutifs. Il désactive uniquement le rendu des graphiques pendant la boucle afin de réduire le coût; les fonctions analytiques et leurs paramètres ne sont pas modifiés. Le protocole, les graines, les contrôles et les sorties sont enregistrés dans `pipeline_control_rotation_v1/`.

Le benchmark prédictif et l’analyse T0 sont deux expériences distinctes. Les classifieurs du benchmark ne proviennent pas de UNIVERSAL_LOG; T0 n’est pas une métrique prédictive.
