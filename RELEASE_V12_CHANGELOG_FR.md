# Journal de travail V12 — 2026-11-22 (provisoire)

V12 n'est pas encore finalisée. Les entrées ci-dessous distinguent les éléments achevés et ceux qui restent en cours.

## Ajouts

- Cadre explicite séparant la tâche prédictive, le comportement complet du pipeline et les effets d’instrumentation/mesure.
- Audit en lecture seule de la couverture des snapshots V4–V11 et publication publique expurgée des chemins locaux.
- Profilage v6.0.1 avec timings et comparaison de sortie avec/sans rendu graphique dans un cas apparié.
- Benchmark prédictif AI4I 2020, Kaggle comparé octet pour octet à UCI; rotation complète des 12 colonnes numériques comme axe de contrôle.
- Benchmark Bike Sharing V1/V2 et protocole V3; résultats V3 à produire et rotation des 16 contrôles encore en cours.
- Audit de mesure Bike : 165 heures sans ligne et absence de métadonnées de capteurs dans le Readme; l'interprétation reste ouverte.
- Audit local UCI Air Quality : 9 357 enregistrements datés (114 lignes terminales vides), 827 lignes complètes communes avant le 1er mai 2004 et 8 443 sentinelles `-200` dans `NMHC(GT)`. Rotation 15 axes préparée; aucun appel pipeline effectué.
- Règle de rapport séparant cible demandée, cible réellement utilisée et motif de repli pour le cas contrôle=cible.
- Guide delta et reconstructeur intègre, y compris ajout PDF incrémental et déplacements de fichiers sans recopier leur contenu.
- Journal d’activité avec décisions, erreurs de préparation corrigées, empreintes, hypothèses et résultats.

## Limites publiées

- AI4I est synthétique et ne permet pas d’inférer une performance industrielle.
- Bike Sharing porte sur un seul réseau historique; la météo observée à l’heure cible ne rend pas le test opérationnel à l’avance.
- Les rotations T0 sont des observations de configuration et ne valident pas une prédiction ni une universalité.
- L’audit a identifié des différences historiques; aucun ZIP V4–V10 n’a été purgé.
- Le delta ne peut pas être promis à 5–30 Mo tant que le PDF incrémental et les résultats nouveaux n’ont pas été mesurés.
- Les fichiers Air Quality bruts restent exclus de GitHub/PDF en attendant la clarification des conditions de partage UCI.
