# Audit de source GDSC2 et plan de réanalyse PDAC

## Conclusion de l'audit de source

La source officielle Sanger contient bien un fichier de mesures GDSC2 brutes, mais son nom est versionné :

- Fichier : `GDSC2_public_raw_data_24Jul22.csv`
- Répertoire officiel : [releases/current_release](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/)
- URL directe : [GDSC2_public_raw_data_24Jul22.csv](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC2_public_raw_data_24Jul22.csv)
- Taille annoncée par HTTP : 2 112 924 313 octets
- Dernière modification annoncée par le serveur : 26 juillet 2022

L'en-tête du fichier, vérifié par lecture partielle HTTP, est :

```text
RESEARCH_PROJECT,BARCODE,SCAN_ID,DATE_CREATED,SCAN_DATE,CELL_ID,MASTER_CELL_ID,COSMIC_ID,CELL_LINE_NAME,SANGER_MODEL_ID,SEEDING_DENSITY,DRUGSET_ID,ASSAY,DURATION,POSITION,TAG,DRUG_ID,CONC,INTENSITY
```

Il s'agit de mesures d'intensité associées à des positions de plaques et à des métadonnées d'expérience. Ce fichier ne contient pas une table prête à l'emploi de viabilités normalisées ni des courbes dose-réponse indépendantes. Les transformations, unités de concentration, contrôles et critères de qualité doivent être établis à partir de la documentation officielle et des métadonnées de plaque avant de construire les courbes.

## Normalisation prescrite par Sanger

La notice officielle indique que chaque plaque reçoit une seule lignée, que `SCAN_ID` identifie le scan retenu après contrôle qualité interne, et que `CONC` est en micromolaire. Les tags sont importants : `NC-1` désigne le contrôle négatif avec DMSO, `B` le blanc sans cellules, `UN-USED` les puits exclus et `FAIL` les positions exclues. Un même puits peut apparaître plusieurs fois si plusieurs tags lui sont associés; on ne doit donc pas traiter chaque ligne CSV comme un puits indépendant sans examiner `POSITION` et `TAG`.

La procédure publiée dans le paquet R officiel [`CancerRxGene/gdscIC50`](https://github.com/CancerRxGene/gdscIC50) retire les positions `FAIL` et les positions de médicaments de bibliothèque sans `DRUG_ID`, calcule par scan les moyennes des intensités `NC-1` et `B`, puis normalise les traitements par :

```text
viabilité normalisée = (INTENSITY - moyenne(B)) / (moyenne(NC-1) - moyenne(B))
```

Le paquet tronque ensuite les valeurs à `[0, 1]`. Il extrait les tags de traitements et de doses; dans sa préparation pour l'ajustement, l'axe de dose est `log2(CONC / concentration_maximale) + 9`, et la réponse du modèle est inversée (`1 - viabilité`). Cette normalisation ne remplace pas l'ajustement non linéaire à effets mixtes décrit par GDSC : le dépôt Sanger recommande `gdscIC50` pour reproduire cet ajustement. Le nouveau script d'extraction publié applique uniquement le nettoyage des positions, la normalisation par contrôles et l'agrégation des puits techniques; il ne prétend pas réimplémenter le modèle statistique GDSC.

La notice avertit également que certains traitements/puits ne sont pas publiés en raison de collaborations privées. L'absence d'une combinaison dans les fichiers publics ne signifie donc pas nécessairement qu'aucune expérience n'a été effectuée.

Le nom `GDSC2_public_raw_data.csv` sans date/version n'est pas le nom observé dans l'index officiel consulté. Le catalogue des composés comprend plusieurs identifiants pour certains médicaments et sites de criblage; il ne faut donc pas apparier seulement sur le nom du médicament :

| Médicament | Identifiants trouvés dans `screened_compounds_rel_8.4.csv` |
|---|---|
| Paclitaxel | 11, 1080 |
| Gemcitabine | 135, 1190, 1393 |
| 5-Fluorouracile | 179, 1073 |
| Cisplatine | 1005, 1496 |
| Olaparib | 1017, 1495 |

Ces identifiants sont un inventaire du catalogue, pas encore la sélection vérifiée des expériences GDSC2 correspondant aux cinq lignées PDAC. La sélection doit être recoupée avec les lignes du fichier brut, les identifiants de modèles cellulaires et les données ajustées de la même version.

## Vérification de couverture dans la table GDSC2 ajustée

La table officielle `GDSC2_fitted_dose_response_24Jul22.csv` a été téléchargée (39 834 719 octets) et filtrée par nom de médicament et nom de lignée. Elle contient les cinq médicaments visés pour trois des cinq lignées proposées :

| Lignée dans le fichier officiel | COSMIC ID | SANGER_MODEL_ID | Nombre de combinaisons médicament-lignée |
|---|---:|---|---:|
| `CAPAN-1` | 753624 | SIDM00934 | 5 |
| `BxPC-3` | 906693 | SIDM00132 | 5 |
| `AsPC-1` | 910702 | SIDM00899 | 5 |
| `PANC-1` | — | — | 0 |
| `MIA PaCa-2` | — | — | 0 |

Les identifiants des médicaments qui apparaissent dans ces 15 combinaisons GDSC2 ajustées sont : cisplatine `1005`, olaparib `1017`, 5-fluorouracile `1073`, paclitaxel `1080` et gemcitabine `1190`. Ces observations vérifient la couverture de la table ajustée; elles ne confirment pas encore que les deux lignées sans courbe ajustée sont absentes du fichier de mesures brutes.

La table ajustée fournit notamment `LN_IC50`, `AUC` et `RMSE`; `LN_IC50` est une valeur logarithmique et ne doit pas être interprétée directement comme une concentration en µM. Cette table sert de référence de comparaison dérivée, pas de remplacement des intensités brutes ni de validation indépendante.

## Résultats de l'extraction des mesures brutes

L'extracteur a été exécuté sur le fichier officiel complet. Le fichier reçu fait 2 112 924 313 octets et son SHA-256 est `e915be2948b174982a9b64bea5fab00f6ec8c15f7baa76bc7e2f7a7df295500e`. Le script a lu 15 069 449 lignes source et produit 1 708 puits normalisés, regroupés en 637 points dose-réponse. Les 101 scans examinés sont marqués valides par les contrôles de l'extracteur; aucun scan n'a été exclu et l'audit rapporte zéro position `FAIL` et zéro position de médicament sans `DRUG_ID`. Les valeurs normalisées observées restent dans `[0, 1]`, conformément à la troncature prescrite.

| Lignée | Lignes source correspondantes | Scans | Puits normalisés | Points dose-réponse |
|---|---:|---:|---:|---:|
| `AsPC-1` | 29 333 | 30 | 504 | 196 |
| `BxPC-3` | 34 029 | 34 | 560 | 210 |
| `CAPAN-1` | 37 229 | 37 | 644 | 231 |
| `PANC-1` | 0 | 0 | 0 | 0 |
| `MIA PaCa-2` | 0 | 0 | 0 | 0 |

Les 637 points couvrent les 15 combinaisons des trois lignées observées avec les cinq médicaments retenus : cisplatine `1005` (175 points), olaparib `1017` (63), 5-fluorouracile `1073` (154), paclitaxel `1080` (112) et gemcitabine `1190` (133). Les sorties détaillées (puits, points et audit par scan) ainsi que le manifeste ont été conservés hors du dépôt; le CSV brut de 2,1 Go n'a pas été ajouté à Git.

Un contrôle ponctuel indépendant a ensuite repris les intensités brutes des scans `6570` (AsPC-1), `8831` (BxPC-3) et `9849` (CAPAN-1), appliqué les étapes de filtrage et la formule publiées dans `gdscIC50/R/nlme_fit_prep.R`, puis comparé les valeurs aux puits exportés. Les 21 puits monothérapie ciblés (7 par scan) correspondent exactement dans ce contrôle (`écart absolu maximal : 0`). Il s'agit d'une vérification indépendante de la préparation décrite par le code source, pas de l'exécution du paquet R lui-même.

## Comparaison descriptive à la table ajustée officielle

La table officielle `GDSC2_fitted_dose_response_24Jul22.csv` a été retéléchargée (39 834 719 octets; SHA-256 `9d6dc82b9a072bb00b6139dcd6c4c11de1e047f210382fb726e92ab8dd0eae2a`). Pour examiner si les courbes extraites permettent une IC50 observée sans extrapolation, les doses ont été placées sur l'échelle décrite par `gdscIC50` (`x = log2(CONC / maxc) + 9`) et la réponse inversée (`y = 1 - viabilité`). Une courbe par scan est considérée comme encadrant le seuil seulement si des mesures observées se trouvent des deux côtés de `y = 0,5`; ce contrôle n'ajuste pas un modèle.

| Lignée | Médicament | Scans | Scans encadrant 50 % de mortalité | LN_IC50 officiel |
|---|---|---:|---:|---:|
| AsPC-1 | Cisplatine | 8 | 0 | 8,919883 |
| AsPC-1 | Olaparib | 3 | 0 | 9,058758 |
| AsPC-1 | 5-Fluorouracile | 7 | 0 | 8,834030 |
| AsPC-1 | Paclitaxel | 4 | 0 | 0,186190 |
| AsPC-1 | Gemcitabine | 6 | 0 | 3,818700 |
| BxPC-3 | Cisplatine | 8 | 0 | 4,090629 |
| BxPC-3 | Olaparib | 3 | 0 | 4,814604 |
| BxPC-3 | 5-Fluorouracile | 7 | 0 | 4,955439 |
| BxPC-3 | Paclitaxel | 6 | 2 | -2,698514 |
| BxPC-3 | Gemcitabine | 6 | 2 | -0,676434 |
| CAPAN-1 | Cisplatine | 9 | 0 | 2,931975 |
| CAPAN-1 | Olaparib | 3 | 0 | 3,362376 |
| CAPAN-1 | 5-Fluorouracile | 8 | 0 | 5,552256 |
| CAPAN-1 | Paclitaxel | 6 | 2 | -2,846612 |
| CAPAN-1 | Gemcitabine | 7 | 2 | -1,649532 |

Au total, seules **8 des 91 courbes par scan** encadrent ce seuil dans les doses mesurées; 83 ne l'encadrent pas et ne permettent donc pas d'estimer leur IC50 à partir de la seule courbe observée sans extrapolation. Les `LN_IC50` affichés sont les références historiques du jeu GDSC2, pas des valeurs recalculées ici. Cet écart de couverture ne démontre ni une erreur de GDSC ni une performance de TLog : la table ajustée utilise le modèle mixte et ses règles de préparation, alors que le contrôle ci-dessus est un simple constat sur les mesures par scan. Il explique pourquoi ajuster systématiquement des IC50 aux courbes extraites puis les présenter comme validation serait trompeur.

## Essai du modèle non linéaire à effets mixtes

R `4.6.2` et `gdscIC50 0.99.4` ont été installés dans le profil utilisateur. Le code `CancerRxGene/gdscIC50` a été figé au commit `34d842254a33bd04f318449969ff9976237c9295`. La préparation historique du paquet (`removeFailedDrugs`, `normalizeData`, etc.) ne s'exécute pas avec `dplyr 1.2.1`, car elle appelle `select_()` devenu une erreur définitive. La normalisation reste contrôlée séparément sur 21 puits bruts; l'échelle de dose et l'inversion de réponse ont été appliquées conformément au code source.

La fonction officielle `fitModelNlmeData` a été essayée sur les 637 points, les trois lignées observées et les cinq médicaments, avec une concentration maximale harmonisée par médicament (les maxima concordent avec la colonne `MAX_CONC` officielle). Le modèle par défaut (`isLargeData=TRUE`) atteint `maxIter=50` sans convergence. L'option petite cohorte (`isLargeData=FALSE`), que le paquet recommande pour les écrans ciblés, ne fournit pas non plus un ajustement acceptable : avertissement de limite d'itérations et covariance approximative non définie positive. En conséquence, **aucun coefficient ni écart d'IC50 issu de ces ajustements n'est rapporté comme résultat valide**. Il serait trompeur de réutiliser les coefficients retournés malgré ces diagnostics.

Le script `PIPELINES_ET_CODE_SOURCE/compare_gdsc2_pdac_subset_gdscic50.R` reproduit cette tentative sur les fichiers locaux et s'arrête explicitement sans écrire de tableau si la convergence n'est pas valide. Il ne rend pas le sous-ensemble de trois lignées équivalent au modèle GDSC2 global, qui utilise une couverture beaucoup plus large de lignées et de médicaments. La comparaison des 15 valeurs ajustées officielles demeure descriptive; aucune validation de TLog n'est établie.

Ces nombres décrivent le résultat de l'extraction et non 1 708 répétitions biologiques : les puits et scans ne constituent pas automatiquement des réplicats biologiques indépendants. L'extracteur ne calcule toujours ni TLog, ni IC50, ni ajustement GDSC à effets mixtes. L'absence de `PANC-1` et de `MIA PaCa-2` vaut pour les noms exacts recherchés dans ce fichier et ne permet pas de conclure sur d'éventuels alias.

## Ce que l'analyse peut et ne peut pas démontrer

Une réanalyse des mesures GDSC2 brutes serait une évaluation empirique sur des expériences in vitro publiées. Comparer TLog aux estimations de la table ajustée GDSC2 serait toutefois une comparaison à une référence dérivée des mêmes expériences, et non une validation externe indépendante. Un résultat favorable ne démontrerait ni une supériorité générale de TLog, ni une réponse chez un patient, ni un bénéfice clinique.

Le benchmark existant de 25 profils et sa corrélation `r = 0,9911` restent synthétiques : les profils et les IC50 dits de référence sont générés par le code local. Ils ne doivent pas être fusionnés avec une future analyse des mesures Sanger ni présentés comme une analyse GDSC2 observée.

## Protocole minimal avant de calculer des résultats

1. Figer les versions exactes des fichiers bruts, ajustés, du catalogue des composés et des métadonnées de lignées; conserver les URL, dates, tailles et empreintes SHA-256.
2. Vérifier dans le brut si `PANC-1` et `MIA PaCa-2` ont des lectures exploitables malgré l'absence de courbe ajustée correspondante; cette vérification est faite pour les noms exacts recherchés, sans exclure d'éventuels alias.
3. Identifier les expériences par `CELL_LINE_NAME`, `COSMIC_ID`/`SANGER_MODEL_ID`, `DRUG_ID`, plaque/scan, durée et concentration; documenter les unités et les répétitions réellement indépendantes.
4. Exécuter l'extracteur avec le CSV officiel complet; l'extraction, les statuts de scans et les décomptes d'exclusion sont vérifiés. Examiner les séries de doses avant toute interprétation.
5. Le contrôle ponctuel des intensités par rapport aux étapes du code source est fait sur trois scans; la couverture du seuil observé a été comptée. Le modèle officiel a été essayé sur le sous-ensemble, mais n'a pas passé les diagnostics de convergence. Une reproduction du modèle GDSC2 global reste à faire sur un environnement et un jeu de données permettant d'inclure toute la couverture de lignées et de médicaments.
6. Figer avant l'évaluation les règles d'inclusion, les critères d'abstention TLog et 4PL, et les métriques. Ne pas régler l'algorithme sur les cinq lignées puis présenter ces mêmes lignées comme test indépendant.
7. Présenter les courbes et résultats par expérience, médicament et lignée, avec incertitude et échecs d'ajustement. Distinguer accord avec la table GDSC2 ajustée et validation indépendante.
8. Ne pas ajouter au dépôt le fichier brut de 2,1 Go. Distribuer le code, la provenance, les empreintes des fichiers obtenus et, si la licence le permet, uniquement des sorties dérivées minimales et traçables.

## Sources officielles

- [Index des versions GDSC](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/)
- [Mesures brutes GDSC2, version du 24 juillet 2022](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC2_public_raw_data_24Jul22.csv)
- [Réponses ajustées GDSC2, version du 24 juillet 2022](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC2_fitted_dose_response_24Jul22.csv)
- [Catalogue des composés, release 8.4](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/screened_compounds_rel_8.4.csv)
- [Description officielle des données brutes](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC_Raw_Data_Description.pdf)
- [Description officielle des données ajustées](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC_Fitted_Data_Description.pdf)
- [Code source de normalisation et ajustement, CancerRxGene/gdscIC50](https://github.com/CancerRxGene/gdscIC50/blob/master/R/nlme_fit_prep.R)
- [Notice du paquet gdscIC50](https://github.com/CancerRxGene/gdscIC50)

## Statut

L'existence, la version, la taille, l'en-tête et l'empreinte du fichier brut ont été vérifiés. La couverture de la table ajustée et celle des mesures brutes extraites sont documentées ci-dessus. L'extracteur implémente la normalisation publiée par Sanger; ses tests synthétiques couvrent le calcul et les exclusions, et un contrôle de 21 puits sur trois scans concorde avec le code source de préparation. Seules 8 des 91 courbes par scan encadrent 50 % de mortalité dans les doses mesurées. Le modèle `gdscIC50` a été exécuté sur le sous-ensemble mais n'a pas passé les critères de convergence; aucune estimation modèle n'est retenue. La reproduction du modèle global reste à faire. Les résultats d'extraction réels sont des points de données in vitro, pas des résultats TLog.

### Exécuter l'extracteur

Télécharger la version officielle de 2,1 Go depuis l'URL ci-dessus, puis lancer depuis `PIPELINES_ET_CODE_SOURCE` :

```powershell
python .\extract_gdsc2_pdac_raw_curves.py `
  --raw-csv "C:\chemin\GDSC2_public_raw_data_24Jul22.csv" `
  --output-dir "C:\chemin\gdsc2_pdac_extracted"
```

Le script lit le grand CSV en flux, ne conserve que les lignes des cinq noms de lignées et des cinq identifiants de médicaments retenus, calcule et écrit le SHA-256 du fichier source, puis produit les puits normalisés, les moyennes par concentration et un audit par scan. Il ne télécharge pas le CSV, ne l'inclut pas au dépôt et ne calcule pas de métrique TLog. Les tests unitaires peuvent être lancés avec `python -m unittest -v test_extract_gdsc2_pdac_raw_curves` depuis ce répertoire.
