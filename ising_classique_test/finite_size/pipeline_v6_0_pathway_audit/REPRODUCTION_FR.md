# Reproduire l'audit Ising v6

Ce dossier conserve un protocole gelé, un lanceur, les entrées CSV préparées, les résultats complets de chaque exécution et une page de lecture. Le code source v6.0 utilisé est conservé à part dans l'archive du projet sous `pancréas/Archive complète PDAC v6 — ZIP/universal_v6.0.0_cohen.py`.

## Environnement

Sur la machine de l'audit, les runs ont utilisé Python 3.11.9 dans le `.venv` du projet, NumPy 1.26.4 et pandas 3.0.6. Les autres dépendances sont celles requises par le pipeline v6.0; elles doivent être installées dans le nouvel environnement si le dépôt est cloné sur une autre machine. Le manifeste enregistre les versions et empreintes disponibles.

## Relancer les analyses

Depuis la racine du projet sous PowerShell :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\run_pipeline_v6_ising.py
```

Le lanceur reprend les runs déjà terminés et n'écrase pas les données complètes. Pour exécuter un seul run :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\run_pipeline_v6_ising.py --only primary_L24_temperature
```

`--force` régénère les entrées synthétiques et relance les runs terminés; ne l'ajouter que si l'objectif est une nouvelle exécution.

Après les runs, construire/actualiser le guide visuel :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\build_reader_report.py
```

Pour produire les livrables d'audit complets, dans cet ordre :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\build_audit_bundle.py
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\build_audit_pdf.py
```

Le PDF final intègre `pipeline_v6_ising_audit_bundle.zip` comme pièce jointe afin de conserver les fichiers sources, sorties, journaux, figures, TLog et licences dans un livrable unique. Si le contenu du dossier change, reconstruire d'abord le ZIP puis le PDF.

Deux scripts secondaires examinent des configurations particulières décidées dans des addenda distincts du protocole principal :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\run_blind_flux_sensitivity.py
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\run_diagonal_control_sensitivity.py
```

Le premier retire χ/Cv/Binder des flux fournis au run L=64; le second pose `control == target` à L=16. Les deux sont des sensibilités exploratoires, documentées séparément et non ajoutées aux critères du benchmark principal.

Pour reproduire le diagnostic ciblé de disponibilité de Levina–Bickel sans relancer les pipelines complets :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\diagnose_levina_support.py
```

Ce script lit les entrées et sorties archivées, appelle l'estimateur standalone sur chaque série complète, reconstruit les 120 positions de fenêtres à partir de l'axe enregistré, compte la disponibilité dans le paysage et classe la raison de retour NaN selon les garde-fous de Levina–Bickel. Il écrit `DIAGNOSTIC_LEVINA_SUPPORT.json` et ne modifie pas les sorties maîtres.

## Reproduire le pilote synthétique à vérité connue

Le pilote v1 est isolé dans `synthetic_pilot_v1/`; il ne modifie ni le code du pipeline ni les runs Ising. Les commandes `prepare` puis `run` sont à exécuter dans une copie de travail vierge/versionnée du dossier pilote (par exemple `synthetic_pilot_v2/`). Elles n'écrasent pas les entrées ni les sorties v1 archivées. Depuis la racine, exécuter dans l'ordre :

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\synthetic_pilot_v1\run_synthetic_pilot.py prepare
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\synthetic_pilot_v1\run_synthetic_pilot.py run
.\.venv\Scripts\python.exe .\ising_classique_test\finite_size\pipeline_v6_0_pathway_audit\synthetic_pilot_v1\score_synthetic_pilot.py
```

`prepare` fige les CSV, le protocole et leurs empreintes. `run` ne lit pas `truth_private/truth.json`; il passe uniquement un CSV, le contrôle, la cible et les paramètres consignés. `score_synthetic_pilot.py` lit la vérité après les runs pour mesurer les écarts et produire le rapport/figure. Le pilote v1 a terminé 4 calculs et enregistré 3 refus de séries N<50. Pour une nouvelle exécution complète après cette exécution, créer une nouvelle version de pilote plutôt que remplacer les traces existantes.

## Où lire les résultats

- `PROTOCOL_PIPELINE_COMPLET_V6.md` : question, données et choix gelés avant l'analyse.
- `GUIDE_LECTURE_PIPELINE_FR.md` : définitions opérationnelles pour débutants.
- `CONTRAT_CONFIGURATION_UNIVERSEL_V1.md` : proposition de schéma pour flux, cible, contrôle, dépendances et cas diagonal; statut proposition, pas API intégralement implémentée.
- `PROTOCOLE_BANC_ESSAI_SYNTHETIQUE_V1.md` : scénarios générateurs, séparation pilote/confirmation et métriques à pré-déclarer; aucune exécution confirmatoire n'est incluse.
- `REVUE_AVIS_AUTRE_IA_2026-11-15.md` : vérification des affirmations de l'avis externe et diagnostic précis de L7b/Levina–Bickel.
- `DIAGNOSTIC_LEVINA_SUPPORT.json` : résultat du probe standalone contre les valeurs locales des paysages, avec empreintes des entrées et du code.
- `synthetic_pilot_v1/PILOT_PROTOCOL_FR.md`, `pilot_spec.json`, `PILOT_REPORT_FR.md` : protocole, paramètres gelés et résultats du pilote; `truth_private/` contient les vérités séparées des CSV; `runs/case_XX/` conserve les sorties maîtres intégrales.
- `ERRATA_ET_JOURNAL.md` : écarts repérés, décisions et observations consignées.
- `LECTURE_GUIDEE_V6/index.html` : graphiques et résumé en langage courant.
- `LECTURE_GUIDEE_V6/resultats_synthese_lisible.csv` : une ligne par run/contrôle, colonnes aplaties.
- `run_state.json` et `pipeline_v6_ising_manifest.json` : statut, réglages, version, empreintes des entrées/code/protocole.
- `runs/<run_id>/` : sortie maître JSON, exports détaillés, figures, CSV réellement lus et journal de cette exécution.

Chaque valeur présentée dans la page visuelle doit pouvoir être remontée à son JSON/CSV source. Les figures de lecture ne remplacent pas les données brutes.
