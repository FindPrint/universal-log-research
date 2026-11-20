# UNIVERSAL_LOG - Livre blanc integral V4

Cette edition consolide le livre blanc d'audit V3, l'audit complet Ising v6, les livres blancs PDAC et les analyses therapeutiques jusqu'au 17 novembre 2026. Le PDF incorpore une archive ZIP complete des fichiers de travail reproductibles presentes dans le dossier du projet au 19 novembre 2026.

## Reproduction

Depuis la racine du dossier, avec Python et les dependances documentaires presentes:

```powershell
.\.venv\Scripts\python.exe .\build_complete_whitepaper_v4.py
```

Dependances du generateur PDF: `pypdf` et `reportlab`. `pdfinfo`/Poppler confirme la pagination sans charger le PDF de plusieurs gigaoctets en memoire; `pdftoppm` est recommande pour le controle visuel du rendu. Les analyses du pipeline ont leurs propres guides et fichiers de dependances dans l'archive.

## Contenu

- Livre blanc UNIVERSAL_LOG V3 (2006 pages, 1529 pieces jointes historiques).
- Audit Ising v6 complet.
- Livres blancs PDAC v1, v6 et v6.1.
- Audit PRISM PDAC complet, reanalyse de la resistance au daraxonrasib et quatre versions consecutives des audits multiflux du 17 novembre.
- Reanalyse therapeutique des donnees animales publiees du 17 novembre.
- Archive ZIP du projet comprenant code, theorie, donnees presentes dans le dossier, resultats, figures, configurations, rapports, licences et traces, plus un catalogue et des SHA-256.

## Perimetre et exclusions

Le snapshot exclut `.git`, `.venv`, `tmp`, bytecode Python et caches. `.git` contient les objets et l'historique du depot; les modifications non commitees sont incluses comme fichiers mais l'historique Git ne l'est pas. `.venv` est specifique a la machine. Les dossiers temporaires ne sont pas requis pour reproduire les analyses. Les donnees et publications de tiers gardent leurs propres licences et conditions d'acces.

Les analyses incluses sont des traces de travail, pas une certification d'un remede. Les donnees PDAC therapeutiques du dossier incluent des reanalyses de sources publiees; les resultats cliniques ne sont pas etablis par ce projet.
