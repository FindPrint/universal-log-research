# Journal des changements V9 - 22 novembre 2026

## Travail effectué

- Recherché trois cohortes ctDNA longitudinales PDAC et une publication distincte de Schlick dans la littérature et le dépôt EGA.
- Inspecté le source v6.0.1 `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py` par AST avec l'environnement `.venv`.
- Confirmé que l'entrée `run_pipeline` ne reçoit pas de clé patient/groupe et que le mode `fast` applique son minimum de 50 aux lignes de la série.
- Préparé deux brouillons de demande de données, Kirchweger 2022 (priorité) et Edland 2023 (seconde piste); aucun n'a été envoyé.
- Corrigé une erreur de citation dans V8 : le DOI 10.3389/fonc.2022.902177 est Kirchweger et al. 2022; Schlick et al. 2021 est une étude distincte.
- Aucun fichier patient n'a été obtenu; aucun run clinique ctDNA n'a été produit.

## Distinction des niveaux d'énoncé

- **Observé dans une source :** effectifs, calendriers et déclaration de disponibilité tels que publiés.
- **Observé dans le code :** absence de paramètre de groupe et construction d'une série de contrôle à partir des lignes retenues.
- **Inférence de compatibilité :** un tableau patient empilé ne doit pas être traité comme une seule trajectoire avec cette entrée.
- **Hypothèse logicielle à tester :** un mode panel explicite pourrait préserver les groupes, mais il doit être spécifié et évalué sur données synthétiques avant les données cliniques.
