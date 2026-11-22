# Notes de version V11 — campagne synthétique de sensibilité

**Date :** 22 novembre 2026

## Ajouts

- Protocole gelé pour comparer des flux nuls, faibles et forts à deux longueurs et plusieurs graines.
- Rotation des cinq colonnes numériques comme contrôle pour chacune des sept entrées.
- Appels complets du pipeline v6.0.1 par entrée et contrôle; cœur non modifié.
- Résumés descriptifs de T0/TLog, localisation sur l’axe temporel, dérivées avant/après, F1/F2, figures et journaux.
- 35 appels complétés; huit assertions d’intégrité passées. Le statut porte sur l’exécution et la structure, pas sur une validation statistique ou clinique.
- Rapport V2 corrigé après découverte d’une lecture pandas qui transformait l’étiquette catégorielle `null` en cellule vide; première version conservée dans `logs/` et correction documentée.
- Temps d’exécution mural par appel et appels longs conservés; aucun profil par estimateur ni cause de ralentissement affirmée.
- PDF enrichi avec les artefacts textuels natifs complets de chaque appel. Le ZIP de projet demeure séparé et exclu du PDF.
- Livre blanc maître V11 et snapshot de projet séparé, avec sauvegarde vérifiée sur D:.

## Portée

Les données sont synthétiques. T0 est disponible dans 15/15 appels nuls, ce qui n’est pas un taux de fausse alerte faute de règle d’alarme. Les quatre erreurs d’axe temporel non nul vont de 3,99 à 38,15 points de pourcentage (médiane 28,00), avec peu de répétitions. Aucun résultat PDAC, biomarqueur ou thérapeutique n’est évalué.
