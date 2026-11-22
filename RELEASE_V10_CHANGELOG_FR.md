# Notes de version V10 — panel synthétique groupé

**Date :** 22 novembre 2026

## Ajouts

- Banc d’essai reproductible pour un adaptateur qui découpe d’abord les trajectoires par patient puis appelle le cœur v6.0.1 séparément.
- Rotation de toutes les colonnes numériques synthétiques comme contrôles, incluant un flux oscillatoire non monotone; les identifiants et classes restent catégoriels.
- Cas de série courte séparé : le wrapper ne concatène pas des trajectoires pour franchir le seuil; un script distinct vérifie directement le refus du cœur sur 32 lignes.
- Rapport et annexe du livre blanc qui conservent les 29 sorties d’estimateurs, les groupes de questions, F1/F2, les dérivées pré/post-seuil, les médianes TLog par classe, les figures et les traces.
- Snapshot complet local séparé du PDF et sauvegardé sur D:; l’archive n’est pas incorporée au PDF.

## Portée

Les entrées sont simulées. Aucun jeu de données clinique ou patient n’a été utilisé; aucun résultat biomédical ou thérapeutique n’est avancé. Le cœur de pipeline v6.0.1 demeure inchangé.
