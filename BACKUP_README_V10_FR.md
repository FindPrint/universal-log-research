# Sauvegarde UNIVERSAL_LOG — V10

**Date :** 22 novembre 2026  
**Racine de sauvegarde :** D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V10\

## Contenu

- master_whitepaper_v10/ : PDF maître V10 et snapshot ZIP complet, séparés, avec empreintes et manifeste d’overlay.
- project_updates_v10/ : protocole, code, données synthétiques, résultats patient/contrôle, rapports, journaux, figures et scripts de reproduction.
- BACKUP_MANIFEST_V10.json : vérification SHA-256 de la copie, du jeu de fichiers du paquet, du PDF sans pièces jointes et du statut de livre blanc maître unique.

Le snapshot V10 prolonge le snapshot V9 dont la sauvegarde D: est vérifiée. Il conserve l’archive complète du projet antérieur et ajoute les nouvelles traces. Il ne contient aucune donnée patient clinique. Le ZIP n’est jamais incorporé au PDF.

Pour reproduire le contrôle de sauvegarde, depuis la racine du projet, lancer avec .venv le script finalize_backup_manifest_v10.py après la création du paquet et sa copie vers D:.
