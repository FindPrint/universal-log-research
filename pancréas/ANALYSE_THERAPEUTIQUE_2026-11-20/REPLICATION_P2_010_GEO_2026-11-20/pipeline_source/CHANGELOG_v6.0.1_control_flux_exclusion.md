# v6.0.1 — Exclusion du contrôle des flux

## Motif

Le balayage par contrôle utilise deux rôles pour une même colonne : axe de
contrôle d'un côté, flux analysé de l'autre. Le chemin automatique de v6.0.0
retirait déjà le contrôle des flux. Un mappage manuel pouvait toutefois
réintroduire cette colonne sous un alias ou comme membre d'un flux composite.
Un essai synthétique l'a reproduit.

## Règle implémentée

- La colonne choisie comme contrôle est exclue des flux de cette exécution,
  même si un mappage manuel la désigne.
- Dans un flux composite, seul le contrôle est retiré; les autres colonnes
  mappées sont conservées.
- Chaque retrait est signalé à l'écran et inscrit dans
  `result.metadata.control_flux_exclusions`.
- Le caractère monotone ou non monotone du contrôle n'est pas un motif de rejet.
  Il est conservé comme information diagnostique de l'axe.
- Pour tester une autre colonne comme contrôle, il faut relancer avec ce
  contrôle sélectionné et la laisser hors des flux pendant cette exécution.

## Fichiers et statut

- `UNIVERSAL_LOG_v6.0.0_cohen_audit.py` demeure la référence intacte.
- `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py` est une version candidate
  distincte qui contient le garde-fou.
- Le test synthétique d'intégration et les cas de mappage sont archivés dans
  `D:\UNIVERSAL_LOG_ARCHIVE_AUDIT_2026-11-21` avec leurs entrées, sorties,
  paramètres et empreintes SHA-256.

## Portée

Le test vérifie une règle de configuration et l'exclusion d'une colonne; il ne
valide ni le TLog, ni une transition physique, ni une propriété universelle.
Les seuils restent des résultats d'analyse conditionnels à l'axe, aux flux,
aux estimateurs et aux paramètres utilisés.
