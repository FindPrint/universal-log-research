# Audit de disponibilité des mesures de réponse à l’ADC anti-MUC1-C

**Date :** 21 novembre 2026

**Question :** existe-t-il une matrice publique de réponse directe à l’ADC anti-MUC1-C, seul ou combiné à MRTX1133, que l’on puisse soumettre au pipeline v6.0.0 sans inventer de valeurs ni d’ordre?

## Résultat de la recherche

**Oui, des essais directs sont publiés. Non, leurs valeurs brutes par puits ou par animal ne sont pas déposées dans les matrices GEO ni dans les suppléments publics que nous avons inventoriés.** L’article principal présente des mesures de viabilité de cellules et d’organoïdes, des expériences de combinaison M1C ADC + MRTX1133 et des courbes de croissance de xénogreffes. Il indique que les données brutes supplémentaires peuvent être obtenues auprès de l’auteur correspondant sur demande raisonnable. [Article et disponibilité des données](https://aacrjournals.org/clincancerres/article/31/24/5246/770511/Targeting-KRAS-Inhibitor-Resistant-Pancreatic)

L’inventaire de l’API publique Figshare reliée à l’article retourne dix fichiers supplémentaires : figures S1 à S8, table S1 et un document de supplément; les dix fichiers sont des documents `.docx`. Les descriptions comprennent des légendes et des figures, pas une matrice `.csv`/`.xlsx` de mesures individuelles. Le script livré interroge seulement les métadonnées et enregistre chaque réponse API; il ne télécharge ni figures ni données expérimentales. [Inventaire Figshare](ADC_FIGSHARE_SUPPLEMENT_INVENTORY.csv) · [Manifeste de provenance](ADC_SOURCE_DISCOVERY_MANIFEST.json)

## Sources et portée des essais

| Source | Agent et modèle | Mesure directe publiée | Unité/plan visible dans le texte | Donnée numérique par unité disponible publiquement? |
|---|---|---|---|---|
| [Ozawa et al., 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12703357/) | ADC anti-MUC1-C 3D1-MMAE; cellules PDAC, PDO et xénogreffes résistantes à MRTX1133 | Viabilité alamarBlue après 6 jours; combinaison avec MRTX1133 et scores Bliss; viabilité PDO après 6 jours; volumes tumoraux longitudinaux | Légendes : 3 déterminations pour plusieurs essais cellulaires, 5 pour l’essai PDO; xénogreffes citées : 6–7 souris par bras. Les dimensions tumorales étaient relevées tous les 3–4 jours. | **Non trouvé** sous forme de table de mesures individuelles; données brutes annoncées sur demande raisonnable. |
| [Ahmad et al., ASCO 2024](https://ascopubs.org/doi/10.1200/JCO.2024.42.16_suppl.e15025) | 3D1-MMAE et 7B8-MMAE; xénogreffe HPAF-II | Résumé de régression tumorale et tolérance | Résumé de congrès; détails du plan et nombres par souris incomplets dans la notice publique | Pas de matrice individuelle dans le résumé consulté. Réplication indépendante non établie ici. |
| [Li et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9793597/) | HzMUC1-MMAE; Capan-2/CFPAC-1 et xénogreffes | Prolifération/colonies, apoptose et volumes tumoraux | Trois expériences indépendantes rapportées pour la courbe cellulaire; 7 souris par bras pour les xénogreffes décrites | Données annoncées sur demande raisonnable. Cet anticorps reconnaît une autre région de MUC1 que l’ADC 3D1 anti-MUC1-C : c’est une preuve adjacente, pas une réplication du même agent. |
| [GSE181961](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE181961), [GSE293756](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE293756) | Expression RNA-seq, perturbation MUC1/shRNA | Abondance de transcrits | Groupes de bibliothèques RNA-seq | Données d’expression disponibles; **aucune mesure de réponse à l’ADC**. |

Ces publications donnent une hypothèse thérapeutique préclinique et des figures de réponse, mais aucune réplication clinique ni preuve de guérison. Le présent audit de disponibilité n’a pas recalculé les effets biologiques affichés dans les articles.

## Compatibilité avec UNIVERSAL_LOG

Le code v6.0.0 audité impose une longueur minimale de 50 valeurs à l’entrée des estimateurs. Les suppléments accessibles ne livrent pas les valeurs brutes permettant de construire et de vérifier un flux ordonné de cette longueur. Les nombres de déterminations de 3 ou 5 ne sont pas des séries temporelles; les mesures répétées d’une souris ne doivent pas être concaténées avec celles des autres souris pour simuler un seul flux de 50 points. La grille complète des concentrations, les identifiants par puits/animal et les valeurs longitudinale individuelles ne sont pas disponibles dans ces dépôts.

**Décision prise : aucun flux ADC n’a été fabriqué ou envoyé au pipeline. Aucun run complet cible/contrôle, T0 ou TLog n’a été calculé.** C’est une limite d’accès et d’adéquation des données publiques, pas un résultat nul sur l’ADC et pas une validation ou invalidation de la théorie/pipeline.

## Données précises à demander pour un test reproductible

Pour chaque modèle cellulaire ou organoïde, il faudrait les mesures de viabilité par puits, la concentration de chaque agent, la condition véhicule/isotype/anticorps nu/payload, les identifiants de réplicat et les lots. Pour les combinaisons, il faut les deux concentrations (M1C ADC et MRTX1133) avec la mesure correspondante. Pour les animaux, il faut les volumes individuels à chaque date, le bras, la dose, la date d’injection, l’identifiant animal et les exclusions prévues. Il faut aussi la définition de l’unité de réplication et les tableaux qui ont servi aux figures.

Le pipeline devra analyser des flux par modèle/plan avec leurs unités conservées, tester les contrôles réellement présents dans les colonnes et s’abstenir quand la longueur ou l’ordre requis manque. Aucun point ne doit être répété ou interpolé pour atteindre 50. Si les données brutes reçues ne comportent pas 50 points ordonnés pertinents, le pipeline courant ne peut pas produire ce run sans calibration préalable d’un mode de petite taille.

## Reproduction de l’inventaire

Depuis la racine du projet, avec le Python du `.venv` :

```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\MRTX1133_MUC1C_AUDIT\audit_adc_public_data.py
```

Le script interroge l’API metadata publique de Figshare et actualise le CSV d’inventaire et le manifeste JSON. Il ne télécharge pas les documents supplémentaires ni les données expérimentales.
