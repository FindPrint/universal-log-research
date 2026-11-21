# UNIVERSAL_LOG — livre blanc complet, édition maître V6

## Livrable maître

Le seul livre blanc actif se trouve dans `output/master_whitepaper_v6/`.
L'édition V6 ajoute une annexe de quatre pages qui consigne l'audit des
archives, le balayage des colonnes de contrôle Ising et PDAC, la distinction
entre analyse et prédiction, et le correctif candidat v6.0.1 sur le rôle
contrôle/flux.

Le PDF final compte 3 211 pages et environ 45,6 MB. Il ne contient aucun
fichier incorporé ni archive ZIP. Les éditions précédentes sont conservées
dans `archive_sources/` pour la traçabilité.

## Archive complète du projet

Le ZIP V6 est livré à côté du PDF. Il reprend le snapshot complet V5 puis y
ajoute les artefacts nouveaux de V6 : livre blanc, pipeline candidat,
documentation, rapport d'audit et contrôles synthétiques. Les catalogues
locaux détaillés du disque D: restent dans la sauvegarde privée et ne sont pas
inclus dans le paquet public.

Le ZIP est indépendant du PDF. Son manifeste V6 et son fichier `.sha256`
permettent de contrôler les ajouts et l'archive finale.
Il contient aussi `README_V6_CURRENT.md`, le résumé racine V6 qui complète le
README V5 conservé dans le snapshot de base.

## Reproduire les changements V6

Depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe .\build_archive_audit_appendix_v6.py
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\ARCHIVE_AUDIT_2026-11-21\test_mapping_edge_cases.py
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\ARCHIVE_AUDIT_2026-11-21\test_control_flux_exclusion.py
```

La génération V6 repart du PDF V5 archivé, ajoute le rapport d'audit rendu,
puis vérifie le nombre de pages. La vérification visuelle des nouvelles pages
est faite séparément avec Poppler. Le ZIP précédent reste conservé dans
`archive_sources/master_whitepaper_v5/`.

La construction du PDF V6 nécessite donc le PDF V5 archivé et les dépendances
de génération. Le dépôt GitHub publie le PDF final, le code candidat et les
rapports reproductibles; le grand ZIP complet reste dans la distribution
locale et sa sauvegarde D:.

Les seuils présentés dans l'annexe sont des résultats d'analyse sous des
configurations déclarées. Ils ne sont pas présentés comme prédictions,
diagnostics ni recommandations thérapeutiques.
