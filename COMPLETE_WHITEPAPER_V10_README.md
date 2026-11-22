# Livre blanc complet UNIVERSAL_LOG — V10

**Date :** 22 novembre 2026  
**Licences :** code du projet MIT; documentation et résultats du projet CC BY 4.0; les données tierces conservent leurs conditions d’origine.

## Fichiers maîtres

- PDF complet : output/master_whitepaper_v10/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V10_2026-11-22.pdf
- Empreinte SHA-256 : sidecar .pdf.sha256 dans le même dossier.
- Snapshot complet du projet : output/master_whitepaper_v10/UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V10_2026-11-22.zip
- Manifeste d’overlay du snapshot : PROJECT_SNAPSHOT_V10_OVERLAY_MANIFEST.json.
- Vérification de la copie sur D: : D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V10\BACKUP_MANIFEST_V10.json.

Le ZIP complet est conservé à part et n’est pas incorporé au PDF. L’édition V9 demeure archivée sous archive_sources/master_whitepaper_v9; V10 est le seul livre blanc actif sous output/.

**Contrôle PDF final :** 3 523 pages; 103 346 981 octets; SHA-256 `9eb11d6d6de648aefb1c3e7cd819bb135dcac99e31c0c02e120ef0589afa4931`; aucune pièce jointe. L’annexe V10 contient 210 figures et 16 journaux complets.

## Ajout V10

V10 ajoute un essai d’intégration de panel longitudinal synthétique, avec un adaptateur qui conserve les frontières patient et appelle le cœur v6.0.1 séparément pour chaque couple patient/contrôle. Le protocole fait tourner toutes les colonnes numériques synthétiques en contrôle, y compris un contrôle non monotone. Le cœur archivé n’est pas modifié.

Le cas court distingue trois trajectoires de 32 observations (96 lignes au total) et garde le minimum de 50 par trajectoire. Un script distinct appelle aussi directement v6.0.1 sur une série de 32 lignes pour enregistrer son exception de longueur.

Le rapport présente les résultats et limites observés; le PDF ajoute le protocole, le code du harnais, l’entrée synthétique, les tableaux patient/contrôle, les sorties F1/F2 et dérivées avant/après, TLog par classe, les graphiques et les journaux d’exécution.

## Portée

Aucune donnée clinique ou patient n’est incluse dans le test. Il ne mesure ni justesse de T0, ni utilité clinique, ni biomarqueur, ni effet thérapeutique. Toute conclusion au-delà du câblage logiciel testé nécessiterait une étude distincte.

## Reproduction et vérification

Depuis la racine du projet, exécuter les commandes du README du banc d’essai avec .venv. La génération et la vérification du PDF, du snapshot, du manifeste de publication et de la sauvegarde D: sont décrites par les scripts build_grouped_panel_appendix_v10.py, build_snapshot_v10.py, build_publication_manifest_v10.py et finalize_backup_manifest_v10.py.

Le manifeste de sauvegarde doit indiquer verified=true. Le PDF maître ne doit contenir aucune pièce jointe et output/ ne doit contenir qu’un seul PDF maître actif.
