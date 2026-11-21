# Revue des archives et règle axe/flux — 21 novembre 2026

Ce dossier rassemble le rapport, les tests reproductibles et les sorties
correspondantes. Les catalogues contenant des chemins locaux complets restent
sur le disque de sauvegarde; ils ne sont pas nécessaires pour reproduire les
tests synthétiques.

## Règle appliquée

Pour chaque exécution, une colonne a le rôle d'axe de contrôle et ne fait pas
partie des flux analysés lors de cette exécution. Chaque autre colonne peut
être testée comme contrôle au cours d'une exécution distincte. Un axe non
monotone est conservé et documenté; il n'est pas rejeté par défaut. Les
résultats décrivent la configuration analysée et ne sont pas automatiquement
des prédictions.

## Reproduire les contrôles synthétiques

Depuis la racine du projet, avec l'environnement `.venv` :

```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\ARCHIVE_AUDIT_2026-11-21\test_control_flux_exclusion.py
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\ARCHIVE_AUDIT_2026-11-21\test_mapping_edge_cases.py
```

Le test d'intégration exécute le pipeline en mode rapide sur 120 lignes
synthétiques; il confirme que le contrôle non monotone reste accepté, que son
alias ne devient pas un flux et que `FluxA` est conservé. Les cas directs
couvrent aussi un flux composite. Ils vérifient le contrat de rôle; ils ne
valident pas TLog ni une hypothèse scientifique.

## Rapport

`D_ARCHIVE_AUDIT_REPORT_FR.md` sépare observations, résultats reproduits,
hypothèses à retester et questions ouvertes. Les catalogues privés de D:
conservent les empreintes et les chemins relatifs de l'inventaire plus large.
