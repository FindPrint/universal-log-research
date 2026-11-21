# UNIVERSAL_LOG — livre blanc complet, édition maître V5

Le PDF maître actif est produit par `build_complete_whitepaper_v5.py` et comprend :

- le livre blanc d'audit V3 en ouverture documentaire;
- l'audit complet Ising v6 et les principaux audits PDAC retenus jusqu'au 21 novembre 2026;
- l'addendum récent sur la calibration synthétique de courbes courtes et la prudence pharmacologique KCNN4;
- un ZIP compagnon séparé du PDF, avec les fichiers de projet courants, les scripts, entrées disponibles, résultats, rapports, licences, inventaire et SHA-256. Le PDF ne contient aucun ZIP ni pièce jointe.

## Livrables construits le 21 novembre 2026

- PDF V5 : 3 207 pages et environ 45,5 MB.
- ZIP compagnon : 6 260 fichiers, environ 13,6 GB avant compression et 8,7 GiB sur disque.
- Contrôle du PDF : 0 fichier incorporé, 0 annotation de pièce jointe; le ZIP est livré à côté du PDF et jamais inclus dans celui-ci.
- Le catalogue et les sommes SHA-256 du ZIP permettent de vérifier les 6 260 fichiers. L'archive a passé le contrôle CRC ZIP intégré au générateur. Les empreintes exactes figurent dans le manifeste de build et les fichiers `.sha256` livrés à côté du PDF et du ZIP.

Les anciennes éditions autonomes sont rangées dans `archive_sources/whitepapers_legacy/`. Le paquet complet V4, qui contient déjà un snapshot de 7,78 Go, est conservé dans `archive_sources/master_v4/` et exclu du ZIP V5 pour éviter d'imbriquer un deuxième snapshot complet. L'édition V5 est le seul livre blanc maître actif; les anciens documents restent disponibles comme archives.

## Reproduire l'édition V5

Depuis la racine du projet, avec le `.venv` et les dépendances de `REQUIREMENTS_WHITEPAPER_V5.txt` :

```powershell
.\.venv\Scripts\python.exe .\build_complete_whitepaper_v5.py
```

Le générateur recompose l'appendice courant, crée le catalogue et les empreintes, construit le ZIP du projet comme fichier compagnon externe, assemble le PDF sans pièce jointe et contrôle la pagination avec `pdfinfo` lorsqu'il est disponible. Le PDF, le ZIP externe, les fichiers SHA-256 et le manifeste de build sont dans `output/master_whitepaper_v5/`. Les grands fichiers générés ne sont pas suivis dans le dépôt GitHub; ce README et le code de génération y sont publiés.

L'environnement `.venv`, `.git`, `tmp`, caches et bytecode restent exclus du snapshot. Le dossier V4 archivé est listé dans les exclusions. Les données et publications de tiers gardent leurs conditions et licences propres; le code du projet est sous MIT et les documents/résultats du projet sous CC BY 4.0.
