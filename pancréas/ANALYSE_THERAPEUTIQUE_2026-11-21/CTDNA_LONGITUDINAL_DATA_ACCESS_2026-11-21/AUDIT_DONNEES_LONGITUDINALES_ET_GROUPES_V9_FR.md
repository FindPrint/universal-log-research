# Audit V9 — données ctDNA longitudinales et traitement des groupes

**Date de l'audit :** 21 novembre 2026  
**Type :** revue documentaire de sources primaires et inspection statique du code v6.0.1  
**Données patient acquises :** aucune  
**Exécution biologique du pipeline :** aucune

## 1. Question vérifiée

Peut-on transmettre directement au cœur v6.0.1 une table longitudinale contenant plusieurs prélèvements par patient, en gardant les identifiants de patients, puis interpréter les lignes comme des observations d'une même trajectoire?

## 2. Résultat observé dans le code v6.0.1

Le fichier vérifié est `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py`. Le script `audit_v6_0_1_grouped_input.py` parse le code avec l'AST de Python et enregistre ses contrôles dans `V6_0_1_GROUPED_INPUT_AUDIT.json`, avec le SHA-256 du script analysé.

La fonction `run_pipeline(data_source, custom_file_path, mapping, mode, opt_cfg)` (ligne 6688; SHA-256 du script `ce0557cb4c44c15a142291e5522b446f7212136686c3035c97f12a3d0e959086`) :

- lit la table CSV et conserve son ordre de lignes;
- convertit la colonne de contrôle sélectionnée en valeurs numériques;
- retire les lignes sans valeur de contrôle et remet l'index à zéro (ligne 6793);
- forme `control_series` avec toutes les lignes retenues (ligne 6794);
- applique le seuil d'admission du mode à cette longueur globale (ligne 6795);
- construit l'axe MC avec le contrôle et les flux, sans identifiant ni frontière de patient (ligne 6861).

L'entrée de cette fonction ne possède pas de paramètre de patient/groupe. Dans son corps, l'audit ne trouve ni `groupby`, ni référence à une clé de patient. Un identifiant patient textuel n'est donc pas utilisé par le cœur pour préserver les trajectoires. L'ordre du CSV devient l'ordre de la série. Si le CSV concatène les patients, la dernière ligne d'un patient et la première ligne du suivant sont traitées dans une seule série.

Le mode `fast` fixe `min_len=50` et `w_size=80` (configuration ligne 246); le garde d'entrée exige donc 50 valeurs valides. Cela compte les lignes retenues, pas le nombre de patients indépendants. Obtenir 50 lignes en empilant les prélèvements de plusieurs personnes ne rend pas ces prélèvements indépendants et ne rend pas l'appel conscient des groupes.

## 3. Conséquence pour une cohorte longitudinale

**Résultat de compatibilité :** le cœur v6.0.1 tel qu'inspecté ne préserve pas les groupes patients. Le lancer sur un tableau empilé pourrait franchir le seuil technique tout en reliant artificiellement les trajectoires. Ce serait une entrée inadéquate pour interpréter une transition temporelle de cohorte.

Le calcul patient par patient préserverait l'ordre des prélèvements, mais les séries de la plupart des cohortes publiées sont bien plus courtes que 50 observations. Pour ces séries, le comportement attendu avec le minimum inchangé est l'abstention. Il faut vérifier les nombres réels par patient après obtention des données, sans les présumer.

La prochaine adaptation logicielle à évaluer est un mode panel explicite : frontière de groupe obligatoire; calcul indépendant dans chaque trajectoire; aucun flux de différences à travers les frontières; compte séparé de patients et prélèvements; rééchantillonnage au niveau patient; et conservation des 29 estimateurs, six groupes de questions, F1/F2 et sorties TLog. Pour chaque passage admissible, chaque colonne de mesure numérique pourra prendre son tour comme contrôle, en excluant le contrôle choisi de ses propres flux et en gardant les contrôles non monotones; les identifiants patient et issues catégorielles resteront des métadonnées. Ce mode ne doit pas abaisser implicitement le minimum de 50. Sa spécification et ses essais synthétiques doivent précéder tout résultat clinique.

## 4. Erratum bibliographique à V8

Le V8 a attribué l'étude de 70 patients au nom de Schlick. Le DOI `10.3389/fonc.2022.902177` est en réalité l'article de **Kirchweger et al. (2022)**, intitulé *Prediction of response to systemic treatment by kinetics of circulating tumor DNA in metastatic pancreatic cancer*. C'est cette étude qui rapporte 70 patients, 45 positifs au départ et 32 dossiers sériels avec réponse (12 PD, 20 non-PD), ainsi qu'une collecte toutes les deux semaines jusqu'à la restadification. La déclaration de disponibilité indique que les données brutes seront fournies par les auteurs sans restriction indue.

**Schlick et al.** est une publication distincte de 2021, *Evaluation of circulating cell-free KRAS mutational status as a molecular monitoring tool in patients with pancreatic cancer*, DOI `10.1016/j.pan.2021.09.004`. Les effectifs de Kirchweger et ses résultats ne lui sont pas attribués dans cette édition. V8 reste archivée sans modification pour préserver l'historique; V9 corrige la référence.

## 5. Inventaire documentaire de sources

| Source | Données annoncées | Accès observé | Compatibilité immédiate |
|---|---|---|---|
| Kirchweger et al., 2022, *Frontiers in Oncology*, DOI 10.3389/fonc.2022.902177 | 70 patients; 45 positifs au départ; 32 dossiers sériels avec réponse (PD 12, non-PD 20); prélèvements toutes les deux semaines jusqu'à restadification | Article et supplément consultés; aucune matrice individuelle téléchargée. La déclaration indique que les auteurs fourniront les données brutes sans restriction indue | Demande prioritaire. Même enjeu de groupes et séries courtes; aucun run clinique avant réception et audit du schéma. |
| Edland et al., 2023, *Molecular Oncology*, DOI 10.1002/1878-0261.13472 | 81 patients, 425 prélèvements; avant traitement puis toutes les 4 semaines; 298 observations ctDNA dans le modèle longitudinal | Article et éléments supplémentaires consultés; aucune matrice patient × prélèvement téléchargeable identifiée dans ces éléments | Deuxième piste de demande, retenue pour son effectif publié plus grand; accès individuel à confirmer auprès des auteurs. |
| Cock et al., 2022, *BMC Cancer*, DOI 10.1186/s12885-022-09387-6; EGA EGAD00001008593 | 7 patients PDAC suivis; 1 à 5 temps selon la description de l'archive; 34 fichiers BAM, environ 2,9 To | Accès contrôlé par EGA/DAC; les fichiers sont des données de séquençage, pas un tableau ctDNA prêt à analyser | Pas une entrée directe pour le cœur v6.0.1; chaque trajectoire décrite est sous le minimum fast de 50. |

## 6. Décision et limites

La cohorte Kirchweger est retenue comme première cible de demande parce que la publication contient une déclaration explicite de mise à disposition des données brutes sans restriction indue. La cohorte Edland reste une deuxième piste intéressante en raison de son effectif publié plus grand et de son calendrier mensuel documenté. Aucune matrice individuelle n'a été obtenue. Les deux brouillons de demande sont conservés séparément et n'ont pas été envoyés.

Les nombres rapportés ci-dessus proviennent des publications et de la page EGA; ils ne sont pas des sorties UNIVERSAL_LOG. Aucun traitement, remède, biomarqueur prédictif ou seuil thérapeutique n'est conclu par ce travail.

## 7. Références primaires

- Edland et al. 2023: [article éditeur](https://febs.onlinelibrary.wiley.com/doi/full/10.1002/1878-0261.13472), [DOI](https://doi.org/10.1002/1878-0261.13472).
- Kirchweger et al. 2022: [article Frontiers](https://www.frontiersin.org/journals/oncology/articles/10.3389/fonc.2022.902177/full), [DOI](https://doi.org/10.3389/fonc.2022.902177).
- Schlick et al. 2021 (publication distincte): [PubMed](https://pubmed.ncbi.nlm.nih.gov/34511398/), [DOI](https://doi.org/10.1016/j.pan.2021.09.004).
- Cock et al. 2022: [article](https://link.springer.com/article/10.1186/s12885-022-09387-6), [dépôt EGA EGAD00001008593](https://ega-archive.org/datasets/EGAD00001008593).
