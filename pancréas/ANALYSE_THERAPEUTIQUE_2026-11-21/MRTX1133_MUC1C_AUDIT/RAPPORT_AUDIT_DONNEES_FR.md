# Audit de faisabilité — MRTX1133 et MUC1-C dans le PDAC

**Date :** 21 novembre 2026  
**Statut :** inventaire des sources terminé; aucune exécution biologique de UNIVERSAL_LOG n’a été lancée.  
**Question :** les jeux GEO publics repérés permettent-ils de tester avec le pipeline la réponse thérapeutique à MRTX1133 associé à une intervention sur MUC1-C?

## Résultat en une phrase

Les données GEO auditées documentent la résistance à MRTX1133 et une expérience d’extinction de MUC1, mais elles ne fournissent pas une trajectoire de réponse thérapeutique ordonnée et suffisamment échantillonnée pour une exécution défendable du pipeline v6.0.0 dans sa configuration actuelle. Aucun T0, TLog ou résultat d’estimateur n’a donc été produit pour cette hypothèse.

## Hypothèse et résultat observé

- **Hypothèse issue de la littérature :** MUC1-C pourrait contribuer à la résistance à l’inhibition de KRAS G12D; un ADC anti-MUC1-C associé à MRTX1133 a montré une activité préclinique dans les modèles étudiés. Cela motive un test, sans établir un traitement validé chez l’humain. [Article primaire, *Clinical Cancer Research*](https://aacrjournals.org/clincancerres/article/31/24/5246/770511/Targeting-KRAS-Inhibitor-Resistant-Pancreatic)
- **Résultat de cet audit :** les séries GEO correspondantes ne contiennent pas, dans leurs matrices publiques, le jeu d’essais quantitatifs de réponse à l’ADC nécessaire à ce test. La fiche de l’article indique que les données RNA-seq sont déposées dans GSE181961 et GSE293756 et que les autres données brutes sont disponibles sur demande auprès des auteurs.
- **Résultat du pipeline :** aucun. Les estimateurs ne sont pas interprétés parce qu’aucune exécution biologique appropriée n’a eu lieu.

## Inventaire vérifié

| Série | Unités et contenu vérifiés | Limite pour le test proposé |
|---|---|---|
| [GSE269985](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE269985) | 30 bibliothèques RNA-seq : cinq modèles, chacun avec trois échantillons parentaux et trois échantillons du modèle résistant. L’archive GEO contient 30 fichiers de comptages individuels; un fichier inspecté comprend 58 175 lignes géniques et une colonne de comptages. | N=30, sous le minimum de 50 de la configuration rapide actuelle. Les lignes parentales/résistantes sont des groupes répliqués, pas une série temporelle avec un ordre naturel. Aucune réponse à l’ADC n’est mesurée dans cette série. |
| [GSE269313](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE269313) | 17 spécimens snRNA-seq de tumeurs KPC : 9 associés à MRTX1133 et 8 au véhicule; les jours consignés vont de 3 à 224. | N=17 bibliothèques, avec dépendance possible entre spécimens portant le même identifiant animal. Les prélèvements sont des observations transversales à des moments différents, pas des mesures répétées d’une même tumeur. Le nombre de cellules ne remplace pas le nombre d’animaux. |
| [GSE293756](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE293756) | 6 bibliothèques RNA-seq provenant d’un seul modèle AsPC-1/MR avec MUC1-shRNA inductible : 3 DOX+ et 3 DOX−/DMSO. La matrice contient 28 008 lignes de comptages géniques et 6 colonnes d’échantillons; la matrice TPM contient 25 545 lignes géniques et 6 colonnes d’échantillons. | N=6. Il s’agit d’un contraste d’expression après induction de shRNA, pas d’une réponse à un ADC anti-MUC1-C ou d’une comparaison d’efficacité MRTX1133 contre combinaison. Pas d’axe temporel documenté dans la matrice. |

Les comptes portent sur les échantillons/bibliothèques décrits par GEO, non sur le nombre de cellules ni de gènes. Le couple de titres KPC_3421L/KPC_3421S dans GSE269313 est conservé tel quel; son indépendance biologique n’est pas présumée.

## Règle de décision pour UNIVERSAL_LOG

Le code v6.0.0 Cohen-D examiné est conservé dans le dépôt sous [`universal_v6.0.0_cohen - Copie.py.txt`](../../universal_v6.0.0_cohen%20-%20Copie.py.txt); son SHA-256 exact est consigné dans le manifeste. Dans la configuration rapide du projet, la longueur minimale effective est de 50 points valides. Le code rejette les entrées plus courtes avant de construire l’analyse. La présence de milliers de lignes de gènes ou de milliers de cellules ne peut pas légitimement transformer 6, 17 ou 30 bibliothèques en autant de mesures indépendantes d’une trajectoire.

De plus, les matrices retenues décrivent des contrastes de groupes ou des prélèvements transversaux. Les réordonner en une suite `temps` fabriquerait un axe. Lancer chaque gène comme contrôle dans cette configuration produirait un rejet répété au seuil N, sans estimateurs. Ce lot n’a donc généré **aucun** résultat pipeline et **aucun** classement de contrôles.

Cette décision distingue deux questions :

1. **Éligibilité actuelle :** les jeux examinés ne franchissent pas le seuil N et ne fournissent pas une trajectoire ordonnée adaptée.
2. **Validité du seuil N=50 :** elle reste à calibrer; cette limite logicielle n’est pas, à elle seule, une preuve qu’un échantillon de taille inférieure serait scientifiquement inutilisable.

## Protocole proposé pour le prochain test thérapeutique

1. Obtenir un tableau quantitatif public ou autorisé de réponse aux conditions véhicule, MRTX1133, anti-MUC1-C ADC et combinaison, avec valeurs mesurées par dose ou au cours du temps. Les données RNA-seq seules ne remplacent pas ce critère de réponse.
2. Conserver les identifiants de modèle, de réplicat biologique, de lot, de dose et de temps. Ne pas compter les cellules, les gènes ou les puits techniques comme des patients/modèles indépendants.
3. Avant l’analyse, fixer l’axe physique ou expérimental, la cible, l’ensemble des flux numériques, les contrôles, les règles de valeurs manquantes, les comparaisons de référence, les permutations et les critères d’abstention.
4. Tester toutes les colonnes de flux préspécifiées comme contrôles, une à une, et conserver les interactions mult flux prévues par la configuration. Enregistrer les rejets aussi bien que les exécutions réussies.
5. Calibrer les tailles d’échantillon pertinentes à partir de nulls et d’alternatives simulés sous le même plan expérimental. Garder le minimum actuel tant qu’un mode de petite taille n’a pas de taux de fausse alerte, puissance et stabilité mesurés.
6. Traiter le premier jeu comme exploration. Réserver un autre modèle/cohorte, non utilisé pour choisir les paramètres, à la réplication externe. Une validation préclinique requiert ensuite des mesures de réponse fonctionnelle et de toxicité; une analyse informatique ne démontre pas un remède.

## Fichiers et reproduction

- Script d’inventaire : [`audit_geo_inputs.py`](audit_geo_inputs.py)
- Inventaire ligne par échantillon : [`GEO_SAMPLE_INVENTORY.csv`](GEO_SAMPLE_INVENTORY.csv)
- Manifestes, dimensions, téléchargements et SHA-256 : [`GEO_DATA_FIT_MANIFEST.json`](GEO_DATA_FIT_MANIFEST.json)
- Les fichiers de données GEO téléchargés restent dans `source/`, ignoré par Git; ils ne sont pas inclus dans le dépôt.

À partir de la racine du projet, avec Python du `.venv` :

```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\MRTX1133_MUC1C_AUDIT\audit_geo_inputs.py
```

Le script ne transforme pas les matrices et ne lance pas le pipeline. Il télécharge les métadonnées GEO et les fichiers de comptages nécessaires à l’inventaire, recalcule les SHA-256, les nombres de lignes/colonnes et les caractéristiques d’échantillons.
