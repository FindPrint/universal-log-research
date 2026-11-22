# Banc d’essai panel groupé — V1

## Objet

Ce dossier vérifie le comportement logiciel d’un adaptateur expérimental pour des mesures répétées par patient. L’adaptateur sépare les patients avant l’appel à UNIVERSAL_LOG v6.0.1 et ne concatène pas leurs trajectoires. Le code du pipeline archivé n’est pas modifié.

Ce banc d’essai utilise exclusivement des données synthétiques. Il ne teste ni un biomarqueur réel, ni le cancer du pancréas, ni la précision clinique d’un seuil.

## Reproduction

Depuis la racine du projet, avec l’environnement .venv :

    .\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\PANEL_SYNTHETIQUE_VALIDATION_V1\run_grouped_panel_validation.py"
    .\.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-22\PANEL_SYNTHETIQUE_VALIDATION_V1\verify_short_core_gate.py"

Le script est reprenable : chaque couple patient/contrôle terminé est enregistré dans run_state.json; les entrées et sorties sont conservées sous inputs/ et runs/; les journaux d’exécution sont sous logs/.

## Fichiers attendus

- PROTOCOLE_GROUPE_PANEL_V1_FR.md — question, décisions de configuration et critères techniques.
- run_grouped_panel_validation.py — génération déterministe, adaptateur panel, appels v6.0.1 et contrôles qualité.
- verify_short_core_gate.py — appel direct v6.0.1 confirmant le refus d’une série patient de 32 lignes.
- inputs/synthetic_longitudinal_panel_v1.csv et inputs/SYN-P*.csv — panel complet et trajectoires isolées.
- runs/<patient>/<contrôle>/ — sorties natives du pipeline et résumé JSON du run.
- patient_control_summary.csv — une ligne par patient et contrôle; pas de lignes patient regroupées comme observations indépendantes.
- validation_results.json — résultats agrégés des tests techniques et limites.
- short_core_gate_check.json — résultat de l’appel direct v6.0.1 sur une trajectoire de 32 lignes.
- run_manifest.json, run_state.json, logs/ — empreintes, environnement, état et traces.

## Lecture prudente

Un test réussi signifie seulement que les règles de séparation, de répartition des colonnes numériques en contrôles, d’admission de longueur, et les appels à la version de pipeline identifiée ont fonctionné sur ce panel construit. Il ne constitue pas une validation de TLog, de la théorie complète, d’un seuil biologique, d’un traitement, ni d’une hypothèse clinique.

Le minimum de 50 est conservé par trajectoire. Si un patient a moins de 50 valeurs valides pour le contrôle du run, le harnais s’abstient pour ce couple patient/contrôle, même si la somme des lignes de plusieurs patients dépasse 50.
