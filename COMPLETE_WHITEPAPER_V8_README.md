# Livre blanc complet UNIVERSAL_LOG — édition V8

**Date :** 21 novembre 2026  
**Ajout :** audit d'accès et protocole préalable pour l'étude longitudinale ctDNA dans le PDAC  
**Licences :** code du projet MIT; documentation/résultats du projet CC BY 4.0; les données tierces conservent leurs propres conditions.

## Fichiers

- PDF maître : `output/master_whitepaper_v8/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V8_2026-11-21.pdf` (3 222 pages; environ 46 MB).
- Empreinte SHA-256 : fichier sidecar `.pdf.sha256` dans le même dossier.
- Snapshot complet séparé : `output/master_whitepaper_v8/UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V8_2026-11-21.zip`.
- Manifeste d'overlay et empreinte ZIP : dans le même dossier.

Le PDF n'a pas le ZIP comme pièce jointe. Le ZIP V8 prolonge le snapshot V7; aucun ancien ZIP de snapshot n'est imbriqué. Le PDF et le ZIP ne sont pas commis dans le dépôt source public en raison de leur taille; les rapports, protocoles, scripts et traces compactes y sont publiés.

## Nouvel audit documentaire

La publication de Schlick et al. décrit un prélèvement avant traitement puis toutes les deux semaines jusqu'à la restadification. Elle rapporte 70 patients inclus, 45 positifs au ctDNA avant traitement et 32 patients avec séries ctDNA complètes et réponse disponible (12 PD, 20 non-PD). La déclaration de l'article indique que les données brutes peuvent être fournies par les auteurs sur demande. Les suppléments répertoriés sont des figures et une table sur les quantités d'ADN extraites; la matrice patient × prélèvement n'a pas été trouvée dans les suppléments consultés. [Article primaire](https://pmc.ncbi.nlm.nih.gov/articles/PMC9468369/), [DOI](https://doi.org/10.3389/fonc.2022.902177).

**Aucun calcul complet du pipeline n'a été effectué sur cette étude.** Le projet ne contient pas les données brutes patient × prélèvement et aucun contact n'a été envoyé. Le brouillon anglais fourni dans le projet est explicitement non envoyé.

## Décisions méthodologiques préalables

- Compter patients et prélèvements séparément; les répétitions d'un même patient restent groupées.
- Garder le seuil d'admission v6.0.1 inchangé; sous 50 valeurs valides, le passage s'abstient.
- Après validation du fichier, faire tourner chaque colonne de mesure numérique admissible comme contrôle, en excluant ce contrôle des flux de son passage et en conservant les contrôles non monotones.
- Ne pas convertir l'identifiant patient ni les issues catégorielles en axes numériques.
- Ne pas concaténer les trajectoires indépendantes en une fausse chronologie. Si le cœur ne préserve pas les groupes, traiter cela comme une limite de compatibilité et ne pas produire un seuil de cohorte interprété.
- Le seuil ctDNA publié de 57,9 % est un repère calculé dans la cohorte de découverte; le comparer à la même cohorte ne serait pas une validation indépendante.

Le protocole détaillé se trouve dans `pancréas/ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/PROTOCOLE_ANALYSE_AXE_FLUX_FR.md`.

## Versions

V7 est archivée sous `archive_sources/master_whitepaper_v7/`; V6 et les éditions précédentes restent archivées dans leurs dossiers versionnés. V8 est le seul PDF maître actif dans `output/`.
