# Livre blanc complet UNIVERSAL_LOG - V9

**Date :** 22 novembre 2026  
**Licences :** code du projet MIT; documentation et résultats du projet CC BY 4.0; les données tierces conservent leurs conditions d'origine.

## Livrables

- PDF maître actif : `output/master_whitepaper_v9/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V9_2026-11-22.pdf`.
- Empreinte SHA-256 : sidecar `.pdf.sha256` dans le même dossier.
- Snapshot complet : `output/master_whitepaper_v9/UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V9_2026-11-22.zip`, séparé du PDF.
- Manifeste de snapshot : `PROJECT_SNAPSHOT_V9_OVERLAY_MANIFEST.json`.

Le PDF ne contient pas le ZIP comme pièce jointe. Le dépôt GitHub conserve les sources documentaires et traces compactes; les gros fichiers PDF et ZIP restent en local et sur D:. Les détails du ZIP V9 et de sa vérification seront consignés dans son manifeste d'overlay et le manifeste de sauvegarde V9.

## Ajouts V9

V9 prolonge le livre blanc V8. Il ajoute une inspection statique du cœur v6.0.1 pour savoir si les séries patient sont groupées, un inventaire de quatre publications/dépôts ctDNA, deux brouillons de demandes de données marqués non envoyés, et un erratum bibliographique.

L'erratum corrige V8 : l'étude de 70 patients associée au DOI `10.3389/fonc.2022.902177` est celle de Kirchweger et al. (2022), pas Schlick. Schlick et al. ont une publication distincte en 2021 (DOI `10.1016/j.pan.2021.09.004`). V8 reste dans les archives inchangée; V9 porte la correction et ses sources.

L'audit v6.0.1 trouve que `run_pipeline` ne reçoit pas d'identifiant patient/groupe et construit une série unique à partir des lignes conservées. Le seuil `fast` de 50 compte ces lignes, pas des patients indépendants. Aucune donnée clinique de ctDNA n'a été obtenue ni exécutée dans le pipeline au cours de V9.

## Reproduction

Les scripts de génération du supplément PDF et du snapshot V9 sont `build_ctdna_group_audit_appendix_v9.py` et `build_snapshot_v9.py`. La vérification de sauvegarde est consignée dans `finalize_backup_manifest_v9.py` et `D:\UNIVERSAL_LOG_BACKUPS\2026-11-21_V5\BACKUP_MANIFEST_V9.json`.

## Historique

V8 et les éditions antérieures restent archivées sous `archive_sources/`. V9 est le seul livre blanc actif sous `output/`. Le snapshot ZIP est un fichier compagnon indépendant; il n'est jamais incorporé au PDF.
