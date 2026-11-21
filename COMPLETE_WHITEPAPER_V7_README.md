# Livre blanc complet UNIVERSAL_LOG — édition V7

**Date de l'édition :** 21 novembre 2026  
**Périmètre ajouté :** audit descriptif contrôle × flux sur le tableau patient PDAC de daraxonrasib  
**Licence :** code MIT; documentation et résultats du projet CC BY 4.0. Les données tierces gardent leurs licences propres.

## Documents de l'édition

- PDF maître : `output/master_whitepaper_v7/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V7_2026-11-21.pdf` (3 216 pages; environ 46 MB).
- Empreinte SHA-256 du PDF : `output/master_whitepaper_v7/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V7_2026-11-21.pdf.sha256`.
- Archive complète du projet : `output/master_whitepaper_v7/UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V7_2026-11-21.zip`.
- Empreinte SHA-256 et manifeste de l'overlay : dans le même dossier de sortie.

Le PDF contient le texte et les graphiques du livre blanc. Il ne contient pas l'archive ZIP comme pièce jointe. Le ZIP séparé contient le snapshot V6 plus les nouveaux fichiers de l'audit multi-axes; l'archive V6 n'est pas imbriquée dans le ZIP V7.

## Ajout PDAC V7 : ce qui a été exécuté

Le cœur de `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py` a été appliqué au tableau patient public de 57 lignes. Chaque colonne numérique a servi, tour à tour, d'axe de contrôle. À chaque passage, la colonne choisie a été exclue des flux analysés; les axes non monotones ont été conservés. Les 15 autres colonnes numériques ont été conservées comme flux dans les passages admissibles. Les colonnes catégorielles textuelles ne sont pas converties arbitrairement en nombres.

Trois dispositions des lignes ont été comparées : ordre source, ordre inversé et mélange déterministe (graine `20261121`). Ce protocole a produit 48 passages : 30 réussites, 18 abstentions dues au seuil d'entrée inchangé de 50 valeurs valides et aucune erreur. L'annexe V7 inclut le tableau de chacun des 48 passages, les seuils internes, deux graphiques, les limites, les empreintes des données et du code, ainsi que les commandes de reproduction.

## Observations et limites d'interprétation

- Plusieurs axes binaires ont un rang `T0` variable selon l'ordre des lignes. Les axes `acquired_other`, `multiple_ras_pathway_classes` et `acquired_any_listed` ont les plus grandes étendues observées dans les trois dispositions de ce tableau.
- `dose_mg` présente une étendue plus faible dans ces essais; cela ne transforme pas son `T0` interne en seuil de dose clinique.
- Les VAF et deltas incomplets ont peu ou pas de sorties d'estimateurs finies. Aucun remplissage statistique des valeurs manquantes n'a été introduit.
- Chaque ligne est un patient dans une table transversale; l'ordre des lignes n'est pas un temps biologique. L'inversion et le mélange évaluent la sensibilité à la présentation des lignes, pas l'évolution tumorale.
- Ces essais n'établissent ni mécanisme causal, ni biomarqueur prédictif validé, ni réponse individuelle, ni efficacité comparative d'un traitement.

Le tableau et sa sélection de patients sont décrits dans l'article primaire d'Aronchik et al., *Nature Medicine* (2026), [article et données supplémentaires](https://doi.org/10.1038/s41591-026-04537-w). L'étude publiée n'est pas réinterprétée ici comme un essai comparatif randomisé par dose.

## Reproduire l'audit ajouté

À partir de la racine du projet et avec l'environnement Python configuré :

```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21\run_patient_axis_flux_sweep.py
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21\summarize_patient_axis_flux_sweep.py
```

Le protocole, les sorties résumées et les traces détaillées se trouvent dans :
`pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/UNIVERSAL_LOG_PDACPATIENT_AXE_FLUX_2026-11-21/`.

Les empreintes de l'entrée et du code pipeline sont enregistrées dans le rapport et le manifeste du balayage. Les journaux originaux demeurent inchangés dans le dossier de travail; leurs copies de diffusion remplacent les chemins locaux par un marqueur neutre.

## Versions archivées

V6 est conservée sous `archive_sources/master_whitepaper_v6/`; V5 sous `archive_sources/master_whitepaper_v5/`. Les versions antérieures sont archivées séparément. L'édition V7 est le seul PDF maître actif dans `output/`.
