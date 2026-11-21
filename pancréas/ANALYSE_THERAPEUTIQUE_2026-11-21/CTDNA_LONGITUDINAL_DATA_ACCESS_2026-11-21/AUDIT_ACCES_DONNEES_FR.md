# Audit documentaire — données longitudinales ctDNA dans le PDAC

**Date de l'audit :** 21 novembre 2026  
**Statut :** source repérée; données brutes non obtenues; aucune analyse UNIVERSAL_LOG exécutée sur cette étude.

## Résultat documentaire établi

L'étude prospective de Schlick et al. a inclus 70 personnes atteintes d'un cancer pancréatique métastatique recevant une nouvelle ligne de chimiothérapie. Le prélèvement initial était la veille du traitement, puis des prélèvements plasmatiques étaient prévus toutes les deux semaines jusqu'à la restadification. L'étude rapporte 45 cas positifs au ctDNA au départ et des mesures sérielles complètes avec réponse connue pour 32 patients positifs : 12 avec progression radiologique et 20 sans progression. Le nombre de mesures par patient et leur structure exacte doivent être confirmés dans la table brute et son dictionnaire.

Les auteurs rapportent une baisse de ctDNA à deux semaines et un seuil relatif de 57,9 % de la valeur initiale; le seuil a été choisi dans la même cohorte qui sert à rapporter ses performances. Il sera traité comme **repère publié de comparaison**, pas comme résultat du pipeline ni comme validation indépendante.

Les patients recevaient plusieurs régimes et lignes de traitement; l'étude est observationnelle. La réponse radiologique et les changements de ctDNA peuvent servir d'issues descriptives disponibles, mais les données ne constituent pas une comparaison randomisée de traitements ni une preuve de remède.

Sources primaires : [article complet, méthodes et résultats](https://pmc.ncbi.nlm.nih.gov/articles/PMC9468369/), [DOI](https://doi.org/10.3389/fonc.2022.902177). La publication décrit des prélèvements toutes les deux semaines et rapporte les 32 séries complètes avec groupes PD/non-PD. La déclaration de disponibilité indique que les données brutes seront fournies par les auteurs sur demande. Les éléments supplémentaires publics listés sont des figures et une table sur les quantités d'ADN extraites; ils ne sont pas présentés comme un fichier brut longitudinal patient × prélèvement.

## Vérification d'accès effectuée

- Le texte intégral et les liens vers les suppléments ont été consultés.
- Le lien public du supplément est intitulé « Quantity of extracted DNA using liquid biopsy » et pointe vers un document DOCX de 20,7 kB. Il ne fournit pas dans son titre une matrice de trajectoires ctDNA et réponse.
- Une tentative de récupération automatisée de ce lien a renvoyé une page HTML d'interposition plutôt que le DOCX; le HTML n'est pas traité comme donnée. Aucune valeur n'a été extraite de graphiques.
- Aucun fichier de données patient × prélèvement provenant de cette étude n'a été trouvé dans le dossier local du projet.
- La publication indique que les données brutes peuvent être fournies par les auteurs sur demande. Aucune demande ou communication n'a été envoyée; le modèle de demande dans ce dossier reste un brouillon.

## Décision de compatibilité avec UNIVERSAL_LOG

La publication décrit au plus 32 trajectoires complètes de patients ctDNA-positifs; chaque trajectoire comporte des prélèvements répétés. Le compte de mesures peut donc dépasser 50 alors que le nombre de patients complets reste 32. Il faut conserver ces deux nombres distincts : des prélèvements répétés chez un même patient ne deviennent pas autant de patients indépendants.

Le cœur v6.0.1 reçoit une table tabulaire ordonnée. Avant tout calcul, il faut vérifier comment représenter plusieurs trajectoires sans relier artificiellement la fin d'un patient au début du suivant. Si le pipeline ne sait pas préserver des groupes patients, aucune concaténation globale ne sera présentée comme une trajectoire biologique. Les options sûres sont alors : appliquer le cœur par patient et documenter l'abstention si chaque série reste sous 50 valeurs, ou développer et tester un mode panel/groupé séparé qui conserve les frontières de patient.

**Décision :** pas de run complet maintenant. La prochaine porte d'entrée est d'obtenir le fichier brut et le dictionnaire, d'inspecter les identifiants, unités, dates relatives, valeurs manquantes et structure de groupes, puis de faire un essai d'admission qui n'abaisse pas le minimum de 50.

## Hypothèses à tester ensuite

1. Les mesures sérielles et les issues cliniques pourraient permettre une analyse multi-flux ordonnée si les données brutes et les limites de confidentialité le permettent.
2. Les résultats du pipeline pourraient dépendre de la façon dont les trajectoires des patients sont représentées; cette possibilité doit être testée avant d'interpréter un `T0`.
3. Une cohorte indépendante serait nécessaire pour examiner la reproductibilité du repère ctDNA publié; la cohorte de découverte ne peut pas jouer ce rôle.
