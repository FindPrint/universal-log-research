# UCI Air Quality — essai centré sur la mesure

Ce dossier prépare un test de v6.0.1 sur des flux issus d'un dispositif multicapteur et d'un analyseur de référence colocalisé. La page UCI décrit cinq capteurs, des dérives, des sensibilités croisées et la sentinelle manquante `-200`. Les détails et le périmètre sont dans le protocole et son amendement.

## Données et conditions

La source brute se télécharge dans `source/` avec `fetch_air_quality_dataset.py`. Le jeu est gardé localement : la page UCI indique un usage réservé à la recherche et exclut l'usage commercial tout en affichant CC BY 4.0. Le manifeste consigne cette tension et l'empreinte SHA-256. Les scripts de publication et le livre blanc excluent les fichiers bruts de ce dossier tant que les conditions ne sont pas clarifiées.

## Reproduction de l'audit et de la préparation

À partir de la racine du projet, dans son `.venv` :

```powershell
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V3_AIR_QUALITY\fetch_air_quality_dataset.py"
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V3_AIR_QUALITY\audit_air_quality_source_v1.py"
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\DATA_PUBLIC_BENCHMARK_V3_AIR_QUALITY\run_air_quality_pipeline_control_rotation.py" --prepare-only
```

La préparation masque `-200` en `NaN` sans interpolation, conserve l'ordre horaire et agrège en 100 blocs consécutifs. Elle inclut les 13 colonnes numériques source et deux diagnostics construits (`time_index_hours`, `missing_fraction_numeric`). Le manifeste du plan conserve l'empreinte de chaque entrée et du pipeline. À ce stade, aucun appel pipeline Air Quality n'a été exécuté.

## Résultat d'audit déjà observé

L'import contient 114 lignes terminales entièrement vides, puis 9 357 enregistrements datés et ordonnés; UCI annonce 9 358 instances. La page situe les données de mars 2004 à février 2005, alors que le fichier téléchargé s'étend au 4 avril 2005. Le `-200` apparaît 8 443 fois dans `NMHC(GT)`. Les 827 lignes complètes communes s'arrêtent au 1er mai 2004, tandis que les autres canaux s'étendent au 4 avril 2005. Les 100 bins ont seulement 12 valeurs disponibles pour l'axe `NMHC(GT)`, sous le minimum fast-mode de 50; ce contrôle doit donc être signalé comme insuffisant si le garde-fou du pipeline le confirme.

Ces constats décrivent l'archive et ses données. Ils ne démontrent pas une défaillance de l'instrument, une cause physique, un seuil du pipeline ou une prédiction de pollution.

Le cadre commun d’interprétation est dans `PROTOCOLE_TRIAGE_SEUILS_ET_ORIGINE_V1_FR.md` à la racine : il traite séparément phénomène visé, chaîne de mesure/collecte et préparation/calcul. Pour cet essai, la présence d’un analyseur de référence permet une comparaison de mesure, mais ne suffit pas à attribuer automatiquement un seuil à une cause physique ou au capteur.

Un second volet, distinct de la rotation descriptive UNIVERSAL_LOG, est préenregistré dans `PROTOCOLE_CALIBRATION_REFERENCE_AIR_QUALITY_V1_FR.md`. Il estime les lectures de référence CO(GT) à partir de cinq canaux capteurs et des trois variables météo, sur trois fenêtres chronologiques fixes. C’est une tâche d’estimation de la lecture de référence, pas de la concentration vraie sans incertitude. Le script offre `--prepare-only`; les comparateurs n’ont pas encore été exécutés.
