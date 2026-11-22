# Livre blanc complet UNIVERSAL_LOG — V11

**Date :** 22 novembre 2026  
**Licences :** code du projet MIT; documentation et résultats du projet CC BY 4.0; les sources tierces gardent leurs conditions d’origine.

## Fichiers maîtres

- PDF complet : output/master_whitepaper_v11/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_2026-11-22.pdf
- Empreinte PDF : sidecar .pdf.sha256 dans le même dossier.
- Snapshot complet du projet : output/master_whitepaper_v11/UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip
- Empreinte du snapshot : sidecar .zip.sha256 dans le même dossier.
- Manifeste de l’overlay : PROJECT_SNAPSHOT_V11_OVERLAY_MANIFEST.json.
- Vérification de la sauvegarde D: : D:\UNIVERSAL_LOG_BACKUPS\2026-11-22_V11\BACKUP_MANIFEST_V11.json.

Le PDF V11 généré contient 77 963 pages, fait 359 807 941 octets et porte le SHA-256 `ba8919a9be070dfcbe83b30dce403644e126e05a1aa184bf4bbcf9c156c6359c`. Le PDF n’a aucune pièce jointe. Son sidecar adjacent est l’enregistrement de contrôle de l’empreinte.

Le ZIP demeure distinct du PDF et n’y est pas incorporé. V11 est l’unique livre blanc maître actif dans output/; V10 et les versions précédentes sont archivées sous archive_sources/.

## Ajout V11

V11 ajoute la campagne synthétique V2 terminée au livre blanc V10. Le cœur UNIVERSAL_LOG v6.0.1 reste inchangé. Le PDF comprend le code source intégral du cœur et du harnais, l’inventaire de l’environnement, le protocole et le journal de correction, les sept entrées, les résultats des 35 appels, les dérivées et figures par appel, les journaux d’exécution ainsi que le contenu intégral des fichiers texte JSON/CSV/TXT/HTML/JSONL de chaque appel. Le ZIP compagnon conserve les fichiers sources exacts.

La campagne a terminé 35/35 appels et passé les huit assertions techniques gelées. T0 était disponible dans les 15 appels nuls; sans règle d’alarme préspécifiée, ce décompte n’est pas un taux de fausse alerte. Pour les quatre appels non nuls à axe temporel, l’erreur absolue par rapport au centre injecté de 58 % va de 3,99 à 38,15 points de pourcentage (médiane 28,00), avec une réplication faible et inégale. Sur toute la matrice, T0 varie de 4,73 % à 96,15 %. Ces valeurs décrivent une sensibilité à la configuration dans les cas synthétiques testés; elles ne prouvent ni localisation fiable, ni validité de TLog, ni universalité, ni pertinence clinique ou PDAC.

Quatre appels complets ont dépassé 300 secondes; le maximum est 729,6 secondes. Ces temps mesurent l’appel complet et non chaque estimateur individuellement; ils n’identifient donc pas la cause des ralentissements.

## Portée

Aucune donnée clinique ou patient n’a été chargée. Les résultats décrivent la configuration synthétique testée. Ils n’établissent ni exactitude générale de T0, ni validation de TLog, ni biomarqueur, causalité, traitement, utilité clinique ou universalité.

## Reproduction

Les commandes d’exécution et de reprise sont dans le README du dossier TRANSITION_SENSITIVITY_V2. Les scripts de construction du PDF, du snapshot, du manifeste de publication et de la sauvegarde sont à la racine du projet.
