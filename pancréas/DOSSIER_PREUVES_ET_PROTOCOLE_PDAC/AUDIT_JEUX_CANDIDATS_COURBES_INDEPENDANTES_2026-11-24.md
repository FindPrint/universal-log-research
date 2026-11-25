# Audit des candidats pour une évaluation indépendante de courbes PDAC

**Date :** 24 novembre 2026
**Objet :** admissibilité documentaire pour le protocole V1.0; aucune performance n'est calculée dans cet audit.
**Conclusion :** aucun jeu actuellement accessible dans le projet ne peut servir de test indépendant intact.

## Règles d'audit

Le dépistage porte sur le type de mesure, les unités, les identifiants, les métadonnées de réplication, les droits d'accès et l'historique d'exposition. Une table d'AUC, une figure, un ajustement recalculé sur la courbe d'entrée ou des puits techniques ne remplacent pas une courbe de référence acquise indépendamment. Les sources déjà consultées dans les analyses du projet sont exclues d'un test aveugle, même si leur structure est autrement utile.

Le contrôle local des classeurs a examiné les manifestes, feuilles, dimensions, titres, en-têtes et quelques lignes de structure afin de distinguer les tables AUC des données par dose; aucun score de performance ni comparaison entre méthodes n'a été recalculé. Ces sources ont toutefois été consultées antérieurement et ne sont donc pas aveugles; elles sont explicitement exclues du test final.

## Résultats

| Candidat | Ce qui est localement établi | Décision pour V1.0 | Prochaine action possible |
|---|---|---|---|
| Yin et al. 2025, Figure 6d — `NatureComm2025_SourceData.xlsx` | Source locale SHA-256 `917a1011426c5ee749343ccabf8126e35923a65c4719ec929f84aa29a511f7b1`; feuille `Figure 6`, lignes de dose/réponse; 8 concentrations, 150 colonnes source correspondant à 75 paires modèle–composé. La provenance du criblage PDO et des courbes Figure 6d est vérifiée dans l'article, DOI `10.1038/s41467-025-57520-3`, PMID 40044664, PMCID PMC11882848. L'analyse a déjà été exécutée et corrigée dans ce projet; le statut biologique des deux colonnes n'est pas établi par le seul classeur. | **Exclu du test indépendant** : déjà consulté et analysé; la relation entre les colonnes ne satisfait pas le plan des répétitions. | Conserver seulement comme test logiciel exploratoire et exemple de provenance/contrôle d'unités. |
| Yin et al. 2025, Supplément Data 10 — `NatureComm2025_Supplementary_Data10.xlsx` | SHA-256 `0e009cd56d2f6c25b0b355590becc4abfee3e1080633173bc33606d1bf325340`; feuille `All Drugs AUC` (63 médicaments × 46 PDO), feuille `CFTR Drugs AUC` (15 médicaments × 15 PDO); mesures résumées AUC, pas les réponses par dose. Même étude et cohorte que la Figure 6d; table déjà utilisée dans le pilote local. | **Exclu** : AUC uniquement, petit effectif et même étude déjà consultée. | Aucun recalcul de courbe à partir des AUC; ne pas considérer des colonnes de médicaments comme des réplications. |
| Tiriac et al. 2018, Table S4A/S4B — `supplement_4775187.xlsx` | Source SHA-256 `d80eb561b653f9a2c78d7db79e9c9220a105d3c8bbe8ece700a7698ed0abc8c8`; feuilles « Chemo » et « Targeted » contiennent les profils PDO sous forme d'AUC (5 et 21 médicaments). Les suppléments S1 décrivent la cohorte, mais ne fournissent pas, dans les classeurs locaux, de série réponse-par-dose avec réplicats et plaques appariées. L'AUC Tiriac a déjà servi à des analyses du projet. DOI `10.1158/2159-8290.CD-18-0349`. | **Exclu** : résumé AUC, courbes brutes et plan de réplicats requis absents du matériel local; déjà consulté. | Demander aux auteurs le fichier brut par dose, le dictionnaire, les identifiants d'expérience/puits et la définition des répétitions. Demande non envoyée. |
| GDSC2 / Sanger | Données publiques d'activité pharmacologique déjà utilisées par le projet. Le benchmark PDAC antérieur incluait des références intégrées au générateur synthétique; les données et le sous-ensemble PDAC ont déjà été inspectés. Les répétitions documentées dans les fichiers disponibles ne satisfont pas l'exigence de cultures biologiques indépendantes appariées pour TLog et référence complète. | **Développement seulement**, pas un test externe intact. | Ne pas requalifier le benchmark synthétique ou une réanalyse de la même campagne en validation indépendante. Chercher un nouveau laboratoire/campagne avec réplicats biologiques documentés. |
| Nicholson et al. 2024 | L'article rapporte 95 PDO et profils IC50 pour cinq agents; l'audit local des fichiers supplémentaires accessibles n'a pas trouvé de matrice PDO × médicament avec valeurs brutes par dose. DOI `10.1097/SLA.0000000000006517`. | **Non exécutable avec les fichiers examinés**; ne pas numériser des figures ni reconstruire des courbes depuis des résumés. | Demande d'accès ciblée aux auteurs, en vérifiant d'abord existence des mesures brutes, répétitions et licence. Non envoyée. |
| Feizi et al., résumé AACR 2025 | Le résumé mentionne un dépistage de PDO PDAC, notamment des séries multi-doses; aucun fichier ligne-par-ligne et dictionnaire de réplicats n'a été identifié dans les ressources locales ou le dépistage antérieur. | **Piste d'accès, pas un jeu admissible**. | Contacter le dépositaire/auteurs pour le jeu dé-identifié et le plan expérimental; ne pas exploiter les chiffres publiés comme données individuelles. Non envoyé. |

Les audits antérieurs de disponibilité indiquent aussi que la publication ctDNA de Schlick ne fournit pas localement la matrice patient × prélèvement; les données brutes sont annoncées sur demande. Les études de Linz, Stavanger et Changhai ne sont pas documentées dans ce dossier comme ayant fourni des réponses brutes. Le ctDNA est une voie longitudinale distincte, pas un substitut à la validation dose-réponse. Aucune demande externe ni transfert de données n'a été effectué dans ce travail.

## Décision de verrouillage

La V1.0 du [`protocole de courbes`](./PROTOCOLE_EVALUATION_TLOG_COURBES_V1.0.md) est spécifiée mais n'est pas préenregistrée et aucun jeu de test indépendant n'est disponible ici. La recherche doit se poursuivre par **accès aux métadonnées sans réponses**, puis vérification des droits, des identifiants biologiques, de l'indépendance des expériences et de l'intégrité de la référence. Un biostatisticien indépendant doit approuver la taille d'échantillon avant l'enregistrement. Si les auteurs ne peuvent fournir ces éléments, le candidat ne franchit pas la porte d'admissibilité.

## Sources et enregistrements locaux

- Yin et al. 2025 : [DOI](https://doi.org/10.1038/s41467-025-57520-3); [PubMed](https://pubmed.ncbi.nlm.nih.gov/40044664/). Manifestes/hash et classeurs cités ci-dessus.
- Tiriac et al. 2018 : [DOI](https://doi.org/10.1158/2159-8290.CD-18-0349); audit local `ANALYSE_THERAPEUTIQUE_2026-11-19/candidate_Tiriac2018/DATASET_AUDIT.md`.
- Nicholson et al. 2024 : [DOI](https://doi.org/10.1097/SLA.0000000000006517); dépistage antérieur `ANALYSE_THERAPEUTIQUE_2026-11-20/EXTERNAL_REPLICATION_SCREEN_REPORT_2026-11-20.md`.
- Feizi et al. AACR 2025 : [actes du congrès](https://www.aacr.org/wp-content/uploads/2025/05/AACR2025_Proceedings_050725.pdf); dépistage antérieur au même rapport.
- ctDNA Schlick et al. 2022 : [article complet](https://pmc.ncbi.nlm.nih.gov/articles/PMC9468369/); audit d'accès local `ANALYSE_THERAPEUTIQUE_2026-11-21/CTDNA_LONGITUDINAL_DATA_ACCESS_2026-11-21/AUDIT_ACCES_DONNEES_FR.md`.
