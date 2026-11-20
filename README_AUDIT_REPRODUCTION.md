# UNIVERSAL_LOG — paquet d’audit reproductible

Ce paquet rassemble les versions du pipeline, la théorie TLog disponible, les protocoles, les simulations Ising classiques et quantiques, les campagnes de calibration, leurs résultats bruts, les figures, les journaux, les audits de code et le livre blanc.

## Lire le projet

1. Commencer par AUDIT_UNIVERSAL_LOG_WHITEPAPER.pdf.
2. Lire FICHE_TLOG_DEBUTANT.md, puis GUIDE_DEBUTANT_UNIVERSAL_LOG.md et MATRICE_29_ESTIMATEURS_TLOG.md.
3. Consulter LICENSES.md, AUDIT_DECISION_LOG.md, les rapports d’expérience et PROJECT_FILE_CATALOG.csv.
4. Les CSV/JSON/NPZ complets, les journaux, le code et les figures sont conservés dans leurs dossiers d’origine; les empreintes sont dans SHA256SUMS.txt.

## Environnement vérifié

Le développement et les vérifications du paquet ont utilisé Python 3.11.9 sous Windows. audit_release/requirements-lock.txt enregistre les versions observées dans l’environnement .venv utilisé. L’environnement n’est volontairement pas redistribué.

Depuis la racine décompressée, dans PowerShell :

    py -3.11 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r audit_release\requirements-lock.txt

L’installation peut être adaptée à une autre plateforme si une dépendance verrouillée est propre à Windows; conserver alors le nouveau manifeste d’environnement avec le résultat.

## Rejouer l’audit v5.9.1

    .\.venv\Scripts\python.exe audit_release\build_v5_9_1_auditfix.py
    .\.venv\Scripts\python.exe audit_release\validate_v5_9_1_auditfix.py

Ou lancer REPRODUCE_AUDIT.ps1. La validation compare les 29 estimateurs, une entrée réelle archivée, les exports typés, les cas limites L7b et l’aide CLI. Elle ne relance pas la campagne physique complète de 1,44 million de lignes.

## Lancer le pipeline sur ses propres données

    .\.venv\Scripts\python.exe audit_release\UNIVERSAL_LOG_v5_9_1_AUDITFIX.py --input chemin\vers\mes_donnees.csv --target nom_de_la_cible --control nom_du_controle --control-mode single --output sortie

Pour plusieurs contrôles, fournir --controls "axe1,axe2,axe3" --control-mode multi; --control-mode all demande l’inspection des contrôles disponibles selon le comportement du pipeline. Vérifier d’abord que les colonnes existent et que la cible/les contrôles sont adaptés au problème. Les colonnes doivent être temporellement ordonnées si l’analyse interprète une séquence. Les résultats dépendent du mode, des paramètres, des données et des dépendances.

La version utilisateur v5.9.0 reste à la racine, inchangée. La v5.9.1 est une copie dérivée pour audit; le diff et la provenance sont dans audit_release/.

## Résultats et limites de reproductibilité

- Les fichiers de résultats existants sont conservés; l’archive inclut les mesures ligne par ligne, trajectoires et exports intermédiaires.
- Les exécutions Monte Carlo exactes peuvent varier selon plateforme, bibliothèques, parallélisme et état aléatoire. Les graines et paramètres archivés doivent être conservés pour comparaison.
- Le protocole v5.9 multi-axes utilise 180 trajectoires (1 440 000 observations), tailles L=16, 32, 48 et cinq chaînes dans l’ablation ciblée. Un enregistrement Wolff représente une mise à jour de grappe, pas une unité de temps physique.
- Une incohérence de métadonnée 120/24 est rapportée : le source indique 120 points de scan, l’entrée dérivée de l’étude en contient 24. Les résultats historiques ne sont pas réécrits silencieusement.
- Les seuils de L7b restent des heuristiques non calibrées. L’intégration complète L7b à run_full_unified_pipeline n’est pas attestée par les contrôles ciblés.
- Les résultats Ising ne démontrent pas l’universalité sur d’autres domaines. Les labels du pipeline sont exploratoires et sensibles au contrôle choisi.

## Licence

Code : MIT (LICENSE). Documents, résultats et figures : CC BY 4.0 (LICENSE-CC-BY-4.0.txt). Voir LICENSES.md pour les limites de périmètre et les contenus tiers.
