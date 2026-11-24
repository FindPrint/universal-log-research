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

## Ce que l'analyse peut et ne peut pas démontrer

Une réanalyse des mesures GDSC2 brutes serait une évaluation empirique sur des expériences in vitro publiées. Comparer TLog aux estimations de la table ajustée GDSC2 serait toutefois une comparaison à une référence dérivée des mêmes expériences, et non une validation externe indépendante. Un résultat favorable ne démontrerait ni une supériorité générale de TLog, ni une réponse chez un patient, ni un bénéfice clinique.

Le benchmark existant de 25 profils et sa corrélation `r = 0,9911` restent synthétiques : les profils et les IC50 dits de référence sont générés par le code local. Ils ne doivent pas être fusionnés avec une future analyse des mesures Sanger ni présentés comme une analyse GDSC2 observée.

## Protocole minimal avant de calculer des résultats

1. Figer les versions exactes des fichiers bruts, ajustés, du catalogue des composés et des métadonnées de lignées; conserver les URL, dates, tailles et empreintes SHA-256.
2. Vérifier dans le brut si `PANC-1` et `MIA PaCa-2` ont des lectures exploitables malgré l'absence de courbe ajustée correspondante; ne pas les compter comme réplications GDSC2 sans observations confirmées.
3. Identifier les expériences par `CELL_LINE_NAME`, `COSMIC_ID`/`SANGER_MODEL_ID`, `DRUG_ID`, plaque/scan, durée et concentration; documenter les unités et les répétitions réellement indépendantes.
4. Implémenter la transformation des intensités selon la documentation GDSC, avec contrôles par plaque, exclusions justifiées et journalisées, et vérifications des plages, doublons et concentrations.
5. Figer avant l'évaluation les règles d'inclusion, les critères d'abstention TLog et 4PL, et les métriques. Ne pas régler l'algorithme sur les cinq lignées puis présenter ces mêmes lignées comme test indépendant.
6. Présenter les courbes et résultats par expérience, médicament et lignée, avec incertitude et échecs d'ajustement. Distinguer accord avec la table GDSC2 ajustée et validation indépendante.
7. Ne pas ajouter au dépôt le fichier brut de 2,1 Go. Distribuer le code, la provenance, les empreintes des fichiers obtenus et, si la licence le permet, uniquement des sorties dérivées minimales et traçables.

## Sources officielles

- [Index des versions GDSC](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/)
- [Mesures brutes GDSC2, version du 24 juillet 2022](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC2_public_raw_data_24Jul22.csv)
- [Réponses ajustées GDSC2, version du 24 juillet 2022](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC2_fitted_dose_response_24Jul22.csv)
- [Catalogue des composés, release 8.4](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/screened_compounds_rel_8.4.csv)
- [Description officielle des données brutes](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC_Raw_Data_Description.pdf)
- [Description officielle des données ajustées](https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/current_release/GDSC_Fitted_Data_Description.pdf)

## Statut

L'existence, la version, la taille et l'en-tête du fichier brut ont été vérifiés auprès du serveur officiel. La couverture de la table ajustée a été vérifiée : 15 combinaisons pour trois lignées, et aucune courbe ajustée pour `PANC-1` et `MIA PaCa-2` sous ces noms. Cette note ne rapporte pas encore de recalcul sur les intensités brutes, de courbes normalisées ou de comparaison TLog/4PL. Ces étapes restent bloquées jusqu'à validation documentée de la normalisation et de la sélection des expériences.
