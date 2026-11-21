# Réanalyse exploratoire RNA-seq — MUC1-C et résistance à MRTX1133

**Date :** 21 novembre 2026

**Version du pipeline auditée :** UNIVERSAL_LOG v6.0.0 Cohen-D

**Statut :** inventaire et réanalyse indépendante d’un panel ciblé terminés; exécution exacte du script R publié non disponible dans l’environnement; aucun run complet target/contrôle du pipeline n’a été lancé.

**Question :** les données RNA-seq publiques soutiennent-elles une réponse cohérente de MUC1 et de marqueurs NFκB/interféron/EMT à l’inhibition de KRAS ou à l’extinction de MUC1, et ces matrices sont-elles utilisables par la configuration v6.0.0?

## Résumé des résultats

- L’analyse a couvert **78 bibliothèques** dans quatre GEO : GSE181961 (12), GSE293756 (6), GSE269985 (30) et GSE279749 (30). Elle a produit 13 contrastes descriptifs et 234 lignes de résultats pour un panel préspécifié de 15 gènes et trois moyennes de panels.
- Le transcrit **MUC1 baisse après induction du shRNA** dans les trois contrastes de perturbation ciblant MUC1 étudiés : −4,06 log2 dans AsPC-1, −3,92 dans HPAF-II et −2,75 dans AsPC-1/MR. C’est un contrôle de manipulation de l’expression, pas une mesure de protéine MUC1-C ni de réponse à un ADC.
- Dans GSE279749, le signal MUC1 sous MRTX1133 varie selon la lignée : +1,97 log2 dans AsPC-1, +0,19 dans PANC-1 (intervalle compatible avec zéro) et +1,43 dans SW1990. Les panels interféron et EMT ne changent pas dans une direction commune entre ces lignées.
- Dans GSE269985, le transcrit MUC1 est plus bas dans les cinq modèles résistants que dans leur modèle parental; l’amplitude et l’incertitude varient. Cela ne mesure pas la protéine MUC1-C et ne teste pas l’ADC.
- **Aucun des résultats ci-dessus ne mesure l’efficacité de l’ADC anti-MUC1-C.** Les matrices RNA-seq publiques ne contiennent pas les valeurs de réponse à l’ADC nécessaires à une réplication indépendante de l’efficacité.
- Les 13 contrastes ont 3 échantillons par bras, sans axe ordonné unique. Sur les 234 vérifications de flux candidates, 218 flux complets ont été soumis à `apply_complexity`; chacun a rendu 29 estimateurs non finis au seuil minimum de 50. Seize vérifications ont été écartées parce qu’au moins une valeur de flux manquait. **Aucun T0/TLog ni run complet target/contrôle n’a été produit.**

## Hypothèse publiée et résultats de cette réanalyse

### Hypothèse provenant de la littérature

Une étude préclinique rapporte que MUC1-C contribue à la résistance de modèles PDAC KRAS G12D à MRTX1133 et que l’ADC anti-MUC1-C a une activité dans certaines lignées, certains organoïdes et xénogreffes, seul ou associé à MRTX1133. L’étude rapporte également une hétérogénéité de sensibilité parmi les organoïdes. Cette preuve est préclinique; elle ne démontre ni efficacité chez les patients ni guérison. Les auteurs déposent les RNA-seq dans GSE181961 et GSE293756, publient leurs scripts R et indiquent que des données brutes supplémentaires sont disponibles sur demande raisonnable. [Article primaire et disponibilité des données](https://pmc.ncbi.nlm.nih.gov/articles/PMC12703357/)

### Observations produites ici

Les résultats numériques de ce rapport proviennent du script Python livré avec celui-ci. Ils sont des différences de niveau d’expression à l’intérieur de chaque étude et contraste, pas des résultats publiés par les auteurs et pas des prédictions cliniques.

## Jeux analysés et unités expérimentales

| Série | Bibliothèques et groupes consignés | Matrice analysée | Limite principale |
|---|---|---|---|
| [GSE181961](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE181961) | 12 : AsPC-1 et HPAF-II, chacun avec 3 DMSO et 3 DOX | Valeurs « Cuff gene counts »; normalisation descriptive log2(CPM+1) | DOX induit un shRNA MUC1; ce n’est pas un essai ADC. |
| [GSE293756](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE293756) | 6 : AsPC-1/MR, 3 DMSO et 3 DOX | Comptages STAR par gène; log2(CPM+1) | Un seul modèle cellulaire résistant; DOX déclenche le shRNA, sans réponse ADC mesurée. |
| [GSE269985](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE269985) | 30 : cinq modèles, chacun avec 3 parentaux et 3 résistants | Fichiers de comptages par échantillon; log2(CPM+1) | Comparaison résistance/parental, pas une trajectoire temporelle ou un test ADC. |
| [GSE279749](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279749) | 24 lignées : 4 modèles × 3 véhicule + 3 médicament; 6 échantillons PDX : 3 véhicule + 3 MRTX1133+olaparib | Tables d’expression nommées `gene_fpkm`; les métadonnées GEO décrivent les valeurs comme RPKM; log2(RPKM+1) | Le bras PDX est une combinaison MRTX1133+olaparib. Aucun bras ADC ni mesure d’efficacité ADC. |

Les réplicats sont ceux déclarés dans GEO. Leur indépendance biologique au-delà des métadonnées publiques n’a pas été vérifiée. Les gènes et cellules ne sont jamais comptés comme des patients ou des modèles indépendants.

## Méthodes et provenance

### Méthode de l’article et limite de reproduction exacte

Le dépôt des auteurs contient `R/multiple_comparison_test.R` au commit `a5eabf881688a4405fed9556f13b5c7042e3fcb0`, SHA-256 `96cd42d0173edf302f005dcdc21cce1b2f4df6ffc50f3483aaa6edae0f81f8a7`. Le script décrit un filtre de somme >10, une correction ComBat-seq, une normalisation TMM par TCC (trois itérations) et une comparaison edgeR multigroupe à FDR 0,05. [Code RNA-seq publié par les auteurs](https://github.com/TomokiMotegi/PDAC_MUC1)

**Ce workflow R n’a pas été exécuté ici : R/Rscript n’est pas installé ou détectable dans `.venv`/PATH.** Le présent rapport ne prétend donc pas reproduire les sorties edgeR/TCC de l’article. Les données ouvertes ont plutôt été analysées dans Python par des transformations et tests descriptifs indépendants, explicitement listés ci-dessous.

### Réanalyse indépendante dans Python

- Comptages : log2(CPM+1), sans combiner les études ni corriger leurs lots entre elles.
- GSE279749 : log2(RPKM+1), d’après la description GEO des matrices; le nom de fichier contient toutefois `fpkm`, écart conservé dans l’inventaire.
- 15 gènes préspécifiés : MUC1; RELA, NFKB1, NFKBIA, TNFAIP3; ISG15, IFIT1, STAT1, IRF7, IFI44L; CDH1, EPCAM, VIM, ZEB1, CDH2.
- Trois scores descriptifs : moyenne des gènes présents dans les panels NFκB, interféron et EMT. Ces petites listes ne sont pas des signatures enrichies ni validées.
- Pour chaque contraste : différences de moyennes sur l’échelle transformée, intervalles de Welch à 95 %, test de Welch et BH sur les 18 caractéristiques de ce seul contraste. Les valeurs p/q sont **exploratoires** : n=3 par bras, caractéristiques corrélées et 9 lignes sur 234 ont une variance exactement nulle dans au moins un bras. Elles ne servent pas à déclarer une cible thérapeutique.

Le script conserve chaque flux par échantillon, les 13 contrastes, les valeurs manquantes, les intervalles, les paramètres et les empreintes des sources téléchargées. Les sources GEO brutes restent sous `source/`, exclu par `.gitignore`.

## Résultats descriptifs par contraste

### Extinction inductible de MUC1

Dans les trois contrastes avec shRNA, le signal MUC1 baisse fortement dans les valeurs RNA-seq : AsPC-1 −4,06; HPAF-II −3,92; AsPC-1/MR −2,75 log2. Le panel interféron baisse aussi dans ces trois contrastes (−0,41; −2,34; −0,21), tandis que le panel EMT change de direction selon le modèle (−0,25; +0,17; +0,24). Ce résultat appuie uniquement le fait que l’induction du shRNA s’accompagne d’une réduction de MUC1 transcrit dans ces matrices; il ne mesure pas une sensibilisation à l’ADC.

### MRTX1133 ou autre inhibiteur de KRAS dans GSE279749

Les différences de transcrit MUC1 sous MRTX1133 sont +1,97 log2 dans AsPC-1, +0,19 dans PANC-1 (IC95 % −0,36 à +0,73) et +1,43 dans SW1990. L’interféron augmente dans AsPC-1 (+0,78) et baisse dans SW1990 (−0,90); l’EMT baisse dans SW1990 (−0,68). CFPAC-1 reçoit BI-2865, pas MRTX1133, et est gardé comme contraste distinct.

Dans les échantillons PDX, le contraste véhicule contre MRTX1133+olaparib donne −0,49 log2 pour MUC1 (IC95 % −0,72 à −0,25; q exploratoire au sein du panel ≈0,079). Il ne permet pas d’isoler l’effet de MRTX1133 de celui de l’olaparib et ne porte pas sur l’ADC.

### Résistance acquise dans GSE269985

Le transcrit MUC1 est inférieur dans les cinq contrastes résistants/parentaux : −0,73, −0,41, −2,55, −0,17 et −3,42 log2 pour Panc 02.03, PANC-1, 6694C2, 6499C4 et 6419C5. L’amplitude est hétérogène; l’intervalle du contraste 6499C4 inclut zéro. Le panel interféron varie aussi selon le modèle. Cette observation d’ARNm n’invalide ni ne confirme l’expression ou l’activité de la protéine MUC1-C : ARN, protéine, contexte de sélection de résistance et temps d’exposition sont des mesures différentes.

## Confrontation au pipeline v6.0.0

Le fichier audité est `pancréas/universal_v6.0.0_cohen - Copie.py.txt`, SHA-256 `bb8bbdba4eb1f8c55b49748274ae8fbfef8a43f6c1b890964f18ba77960c0773`. Le script appelle réellement `apply_complexity` du fichier de pipeline pour chaque flux complet d’un contraste, uniquement pour contrôler l’entrée des 29 estimateurs. Dans les 13 contrastes, il y a 6 échantillons par contraste (3 + 3), sous le minimum rapide de 50. **218 flux complets ont retourné 0/29 valeurs finies; 16 flux avaient au moins une valeur manquante et n’ont pas franchi ce contrôle.**

Ce test de porte d’entrée n’est pas un run complet target/contrôle : l’axe est un groupe binaire, pas un ordre expérimental continu; aucune mesure de réponse ADC n’est disponible dans les matrices. Aucune cible globale biologique, aucun seuil T0 et aucun TLog n’ont donc été calculés. Les lignes de contrôle dans `PIPELINE_CONTROL_GATE_AUDIT.csv` sont des abstentions, pas des résultats négatifs.

## Conclusion limitée

**Observation :** le panel RNA est cohérent avec l’extinction de MUC1 après DOX/shRNA, mais les changements MUC1/interféron/EMT sous traitement ou résistance varient entre les modèles et les jeux.

**Hypothèse à tester :** l’activation de MUC1-C protéique peut jouer un rôle contextuel dans certains modèles KRAS G12D résistants et être ciblable par un ADC; les niveaux d’ARN seuls ne répondent pas à cette hypothèse.

**Non établi :** aucun effet thérapeutique de l’ADC n’a été estimé par cette réanalyse, aucun run complet UNIVERSAL_LOG n’a été réalisé et aucune conclusion de guérison, d’efficacité clinique ou d’universalité ne suit de ces données.

## Suite expérimentale recommandée

La prochaine preuve utile est une matrice d’efficacité directement mesurée, idéalement dans plusieurs PDO résistants et sensibles : véhicule, MRTX1133 seul, ADC anti-MUC1-C seul et combinaison; courbes de dose et de temps; réplicats de modèle biologiquement indépendants; mesure de viabilité/apoptose et de MUC1-C protéique; témoin isotype/payload et contrôle non tumoral; puis validation indépendante. L’axe d’analyse devra être fixé avant d’insérer les données dans UNIVERSAL_LOG. Sans tableau de réponse à l’ADC, poursuivre l’interprétation thérapeutique à partir des seuls flux d’ARN serait spéculatif.

## Fichiers reproductibles

- Script : [`reanalyze_public_rnaseq.py`](reanalyze_public_rnaseq.py)
- Flux marqueurs par échantillon : [`RNASEQ_MARKER_FLUXES_PER_SAMPLE.csv`](RNASEQ_MARKER_FLUXES_PER_SAMPLE.csv)
- Contrastes et intervalles : [`RNASEQ_MARKER_CONTRASTS.csv`](RNASEQ_MARKER_CONTRASTS.csv)
- Vérifications de porte d’entrée de 29 estimateurs : [`PIPELINE_CONTROL_GATE_AUDIT.csv`](PIPELINE_CONTROL_GATE_AUDIT.csv)
- Inventaire étendu : [`RNASEQ_SAMPLE_INVENTORY_EXTENDED.csv`](RNASEQ_SAMPLE_INVENTORY_EXTENDED.csv)
- Décisions de compatibilité : [`RNASEQ_DATASET_FIT_DECISIONS.csv`](RNASEQ_DATASET_FIT_DECISIONS.csv)
- Graphique : [`RNASEQ_MARKER_EFFECTS.png`](RNASEQ_MARKER_EFFECTS.png)
- Empreintes, versions, sources et méthodes : [`RNASEQ_REANALYSIS_MANIFEST.json`](RNASEQ_REANALYSIS_MANIFEST.json)

Reproduction depuis la racine du projet avec l’environnement utilisé :

```powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\MRTX1133_MUC1C_AUDIT\reanalyze_public_rnaseq.py
```
