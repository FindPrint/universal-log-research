# Revue scientifique indépendante — UNIVERSAL_LOG et PDAC

**Date de l’audit :** 15 novembre 2026  
**But :** évaluer honnêtement ce que les archives permettent d’affirmer sur le pipeline, TLog et le cancer canalaire du pancréas (PDAC).  
**Statut :** analyse exploratoire indépendante; aucune conclusion clinique.

## Verdict en une phrase

Le résultat biologique le plus solide retrouvé ici est une **association reproductible entre l’expression ARN de CEACAM5 et l’expression ARN de KRAS** dans trois cohortes tumorales, qui résiste à un ajustement limité par des marqueurs de tissu acineux/îlots. **Ce résultat n’établit ni causalité, ni biomarqueur sanguin, ni utilité clinique, et il ne valide pas les seuils, TLog ou l’universalité d’UNIVERSAL_LOG.**

Une preuve « irréfutable » n’est pas un objectif scientifique réaliste. Le bon objectif est une affirmation précise, un protocole gelé, une réplication indépendante et des contrôles capables de faire échouer l’hypothèse.

## 1. Séparation des niveaux de preuve

| Catégorie | Ce que signifie ce rapport |
|---|---|
| **Résultat indépendant** | Recalculé à partir des matrices de données archivées, par le script de cette revue; aucun code UNIVERSAL_LOG n’est importé. |
| **Résultat rapporté dans l’archive** | Valeur décrite dans le livre blanc v6 ou dans ses fichiers de provenance; ce n’est pas automatiquement une réplication indépendante. |
| **Interprétation** | Explication plausible des résultats, à tester; elle n’est pas considérée comme observée. |
| **Non démontré** | La donnée disponible ne répond pas à la question, ou le contrôle a échoué. |

Les archives contiennent des résultats utiles, y compris des résultats négatifs. Elles contiennent aussi plusieurs générations de rapports dont certaines conclusions anciennes sont plus fortes que celles de la revue v6. La revue v6 est le document de référence le plus prudent; elle ne remplace pas la réanalyse ci-dessous.

## 2. Réanalyse indépendante des cohortes ARN

### Données et méthode

Les matrices ont été lues directement depuis les fichiers archivés : TCGA-PAAD Firehose (178 tumeurs primaires), GEO GSE71729 (145 tumeurs primaires) et GEO GSE62452 (69 tumeurs). Les dépôts GEO décrivent GSE71729 comme une étude de microdissection numérique des composantes tumorale et stromale; GSE62452 contient des tissus tumoraux et adjacents mesurés sur puce Affymetrix HuGene-1.0 ST. [GSE71729 — NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE71729), [GSE62452 — NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE62452).

Pour chaque cohorte, j’ai calculé la corrélation de rang de Spearman entre l’expression mesurée de KRAS et chacun des gènes. Les valeurs p ont été corrigées par Benjamini–Hochberg sur tous les gènes mesurés dans la cohorte. Une seconde analyse calcule une corrélation de rang partielle après retrait linéaire de deux scores de composition tissulaire construits avec des gènes acineux et d’îlots. Ce contrôle est un **proxy imparfait de composition**, pas une mesure complète de pureté tumorale. Les cohortes gardent leurs échelles et plateformes d’origine; seules les associations au sein de chaque cohorte sont comparées.

| Cohorte | n | MUC16–KRAS ρ (q génome) | Après proxy de composition ρ (q génome) | CEACAM5–KRAS ρ (q génome) | Après proxy de composition ρ (q génome) |
|---|---:|---:|---:|---:|---:|
| TCGA-PAAD | 178 | 0,278 (0,00065) | 0,285 (0,00053) | **0,343 (0,000017)** | **0,339 (0,000027)** |
| GEO GSE71729 | 145 | 0,037 (0,752) | −0,011 (0,928) | **0,274 (0,00380)** | **0,277 (0,00342)** |
| GEO GSE62452 | 69 | 0,324 (0,0246) | 0,276 (0,0734) | **0,441 (0,00143)** | **0,378 (0,0111)** |

Les q de ce tableau sont corrigées **à l’intérieur de chaque cohorte et sur tout le génome mesuré**. La direction positive de CEACAM5 est retrouvée dans les trois cohortes et reste significative après le contrôle de composition dans chacune. Dans les deux GEO, les corrélations de rang partielles sont ρ=0,277 et ρ=0,378; leurs valeurs p corrigées au génome sont 0,00342 et 0,0111.

Pour MUC16, les deux cohortes où la corrélation est positive ne suffisent pas à établir une relation monotone générale : GSE71729 est compatible avec une absence d’association (ρ=0,037; q=0,752; après proxy, ρ=−0,011; q=0,928). Son association après proxy n’atteint pas q<0,05 dans GSE62452. L’expression de MUC16 ne doit donc pas être décrite comme un signal continu confirmé dans 3/3 cohortes.

### Contrôle de l’agrégation des sondes

Dans GSE62452, KRAS, MUC16 et CEACAM5 ont chacun une seule sonde retenue après la correspondance plateforme-symbole. Pour ces trois gènes, agréger les sondes par médiane ou moyenne donne exactement la même corrélation; le test par sonde individuelle donne aussi ρ=0,324 pour MUC16 et ρ=0,441 pour CEACAM5. Le résultat GSE62452 n’est donc pas dû au choix moyenne/médiane pour ces gènes.

### Pourquoi l’ancien « 3/3 » doit être nuancé

Dans le livre blanc v6, « 3/3 » désigne surtout une différence de groupe entre les **12** patients classés KRAS les plus élevés et le reste. Cette règle fixe un nombre de patients, mais pas une fraction identique : 12 représente 6,7 % de TCGA, 8,3 % de GSE71729 et 17,4 % de GSE62452. Pour MUC16, l’effet de groupe de GSE71729 varie fortement avec le nombre de patients retenus : Cohen-d vaut 0,10 au top 7, 0,68 au top 12 et 0,54 au top 20; son association continue avec KRAS est presque nulle. La conclusion « MUC16 suit KRAS dans 3/3 » dépend donc de la coupure choisie.

CEACAM5 est plus robuste à cette objection : la corrélation continue est positive dans les trois cohortes, avec correction de multiplicité; l’effet top 12 est aussi positif dans chacune. C’est le constat exploratoire le mieux défendu de cette réanalyse.

## 3. Survie : signal intéressant, mais une incohérence d’archive

J’ai refait un modèle de Cox à partir de la matrice Firehose et du fichier clinique fourni. Le code lie les échantillons par le code patient TCGA, utilise OS_MONTHS et OS_STATUS, applique l’approximation de Breslow pour les temps d’événement ex æquo, puis standardise les expressions dans chaque modèle. Le modèle ajusté inclut KRAS, MUC16, CEACAM5, âge, sexe et stade pathologique regroupé. L’analyse complète avait 175 patients et 92 événements; deux patients sans stade exploitable sont exclus de ce modèle.

| Variable | HR par écart-type | IC 95 % | p de Wald |
|---|---:|---:|---:|
| KRAS ARN | 1,37 | 1,09–1,73 | 0,0078 |
| MUC16 ARN | 1,34 | 1,06–1,69 | 0,0143 |
| CEACAM5 ARN | 0,97 | 0,75–1,25 | 0,82 |

Ces chiffres suggèrent une association pronostique interne pour KRAS et MUC16 dans ce modèle; CEACAM5 n’est pas associé à la survie une fois les autres variables incluses. Les p-values sont nominales, non corrigées pour les comparaisons multiples. Ce résultat reste post hoc, issu de la même cohorte que la découverte des marqueurs. Le modèle de Cox ne démontre pas que MUC16 cause une survie plus courte. La proportion de stades avancés est faible dans l’intersection clinique-ARN; les hypothèses du modèle, dont les risques proportionnels, n’ont pas été validées ici. Il manque une validation de survie indépendante.

**Écart à résoudre dans les archives :** les HR et valeurs p univariables annoncés dans le livre blanc v6 ne se reproduisent pas avec ces données, le codage patient et un Cox continu standard. En revanche, les résultats multivariés « marqueurs seulement » de ce rapport indépendant retrouvent presque exactement les HR/p multivariés du livre blanc. Le script exact ayant produit les valeurs univariables archivées n’a pas été trouvé dans le corpus inspecté. Elles restent donc **non reproduites**, et l’explication de l’écart est inconnue; je ne les fusionne pas avec les nouveaux résultats.

Autre limite : l’analyse porte sur **l’ARN tumoral**, pas sur les concentrations sanguines de CEA ou de CA125. Une corrélation d’expression de CEACAM5 ne prouve pas que le CEA sérique augmente de la même façon, ni qu’un dosage aide à choisir un traitement. Le NCI distingue les marqueurs utilisés pour surveiller certains cancers et souligne les limites des marqueurs tumoraux; pour le pancréas, son document de traitement cite le CA19-9 parmi les marqueurs sanguins, avec une spécificité limitée. [NCI — marqueurs tumoraux](https://www.cancer.gov/about-cancer/diagnosis-staging/diagnosis/tumor-markers-list), [NCI — traitement du cancer du pancréas](https://www.cancer.gov/types/pancreatic/hp/pancreatic-treatment-pdq).

## 4. Ce que les archives montrent sur le pipeline

### Points positifs observés

- Le corpus conserve beaucoup de provenance : matrices, paramètres, nuls, rotations d’axes/contrôles, sorties, logs et versions du pipeline.
- La v6 rapporte des tests inter-omiques plutôt que de s’arrêter au premier résultat ARN : les validations protéomiques ne confirment pas la cascade RNA; les associations CRISPR sont faibles; PRISM ne fournit aucun composé sous FDR 0,05 dans l’analyse archivée.
- Le remplacement de Cliff par Cohen-d semble avoir accéléré le calcul selon le benchmark HP35 archivé. C’est un résultat de performance et de stabilité logicielle, pas une preuve biologique ou théorique.
- Les essais synthétiques antérieurs ont trouvé un biais de localisation de seuil par maximisation du contraste. Cela justifie de ne jamais interpréter automatiquement T0 comme un temps de transition physique.

### Limites majeures observées

1. **Ordre transversal ≠ temps de progression.** Le classement de patients par l’expression de KRAS produit un axe ordonné, pas une trajectoire longitudinale ni la date d’une transition chez une personne.
2. **Le test du pipeline lui-même ne réplique pas comme le signal CEACAM5.** L’archive rapporte une non-séparation du réel et du nul dans GSE71729 et GSE62452, ainsi qu’une non-confirmation de la cascade ARN dans les protéines CPTAC. Le signal brut de CEACAM5 ne doit pas être attribué au T0 ou à TLog : c’est une analyse d’association simple, indépendante du pipeline.
3. **Seuils fragiles.** Des groupes de taille top-k changent de proportion entre cohortes; dans le rapport v6, un seuil de GSE62452 laisse seulement trois observations en aval et retourne le signe estimé de MUC16. Le résultat principal doit venir d’analyses continues préspécifiées, pas d’une coupure choisie après le scan.
4. **Petit effectif multi-omique.** Les analyses protéines ont environ 52–63 cas et les sorties L7a deviennent NaN dans ces runs; cela limite la capacité de conclure à la confirmation ou à l’absence de confirmation.
5. **Pas de découverte thérapeutique validée.** Les résultats CRISPR et médicaments ne montrent pas de vulnérabilité confirmée. Aucun médicament, seuil ou combinaison ne peut être recommandé sur la base de ces fichiers.

## 5. Audit de TLog

La formule archivée est

\[
T_{\log}(n,d)=(d-4)\log(n).
\]

Dans le code v6, le « n » opérationnel est le **nombre de lignes du CSV**; le code calcule des médianes de classes sur une sélection de 21 sorties jugées dimensionnelles parmi les 29 estimateurs. Les autres estimateurs sont gardés dans des couches descriptives séparées.

Mathématiquement, pour n>1 et d fixé, le signe de TLog vient entièrement de **d−4**. n change la grandeur absolue, mais pas le signe. TLog est donc, à ce stade, une reparamétrisation de la distance à d=4; il ne fournit pas à lui seul une preuve qu’un régime biologique est critique. Le résultat dépend de la définition de d, du choix des estimateurs, de leur calibration et de la justification de dcrit=4 pour le système analysé.

La dimension 4 a une signification établie dans certains modèles de champ et pour l’Ising comme **dimension critique supérieure** (au-delà de laquelle certaines propriétés suivent le comportement de champ moyen). Cela n’établit pas que 4 est le seuil universel d’une dimension fractale estimée dans un CSV de cancer ou dans tout domaine. Wilson et Fisher traitent précisément des exposants critiques près de quatre dimensions pour des modèles Ising-like; ce résultat est lié à ce cadre physique. [Wilson & Fisher, *Critical Exponents in 3.99 Dimensions*, Physical Review Letters (1972)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.28.240).

**Verdict actuel :** TLog est une hypothèse/formule candidate intégrée au logiciel; les fichiers PDAC audités ne la valident pas. Pour la tester, il faut définir avant analyse la signification physique de d, le système auquel dcrit=4 s’applique, la façon de mesurer n, et une prédiction que TLog fait mieux que d seul, n seul ou un détecteur de changement de régime standard.

## 6. Le meilleur énoncé autorisé aujourd’hui

> Dans trois cohortes indépendantes de tumeurs PDAC, l’expression ARN de CEACAM5 est positivement associée à l’expression ARN de KRAS; l’association reste détectable après ajustement par deux proxys de composition tissulaire. Cette observation transversale ne prouve ni causalité, ni progression temporelle, ni signal CEA sanguin, ni utilité clinique. Elle ne valide pas UNIVERSAL_LOG ni TLog.

La partie « trois cohortes » décrit la présence d’une association de rang positive dans chacun des fichiers; la correction FDR est calculée séparément dans chaque cohorte. La sélection initiale de ces marqueurs s’est faite après exploration du TCGA et d’une première cohorte GEO, donc ce constat doit rester qualifié d’exploratoire jusqu’à une réplication réellement préenregistrée.

## Mise à jour datée : test externe GSE57495, 15 novembre 2026

Après le gel du protocole local `PROTOCOLE_HOLDOUT_GSE57495.md`, j’ai analysé les 63 échantillons tumoraux de GSE57495 avec les valeurs d’expression GEO et l’annotation officielle GPL15048. CEACAM5 et KRAS ont été agrégés par la médiane de leurs sondes à symbole unique, conformément au protocole. Le résultat primaire est **Spearman rho=0,438**, avec un test de permutation unilatéral positif (100 000 permutations, **p=0,00024**) et un IC bootstrap percentile à 95 % **[0,190 ; 0,635]**. Les trois conditions directionnelles préfixées sont satisfaites dans cette cohorte.

En réunissant ce résultat avec les trois analyses précédentes, l’association transversale d’expression ARN CEACAM5-KRAS est positive dans **4/4 cohortes examinées** : TCGA-PAAD (n=178, rho=0,343), GSE71729 (n=145, rho=0,274), GSE62452 (n=69, rho=0,441) et GSE57495 (n=63, rho=0,438). Les méthodes d’inférence ne sont pas identiques dans les quatre cohortes : ne pas comparer directement leurs p-values. GSE57495 a été choisie après les résultats précédents et non avant toute exploration; le constat reste exploratoire même si cette cohorte n’a pas participé au calcul du rho.

La corrélation de rang partielle définie avant le calcul, contrôlant des proxys acineux et d’îlots, est rho=0,352. Elle est descriptive ici : aucune p-value ni intervalle de confiance pour cet estimand secondaire n’avait été préspécifié. Ce contrôle ne constitue pas une mesure complète de pureté tumorale.

Cette mise à jour ne teste **pas** le pipeline UNIVERSAL_LOG, TLog, un point de bascule, la causalité, le statut mutationnel KRAS, un biomarqueur sanguin, ni une utilité clinique. Elle réplique uniquement une association entre niveaux d’ARN dans des tumeurs. Voir `RESULTATS_HOLDOUT_GSE57495.md`, le script, le CSV par échantillon et le manifeste SHA-256 dans `data_GSE57495/`.

## 7. Protocole recommandé pour une validation difficile à contester

1. **Geler l’algorithme.** Publier une version hachée, les 29 estimateurs actifs, les 21 estimateurs TLog, toutes les options et les règles de traitement des échecs/NaN.
2. **Préenregistrer une cible de validation.** Choisir un seul résultat principal, un seul type de donnée, un axe physique valide, la taille minimale et la méthode de correction de multiplicité avant d’ouvrir la cohorte test.
3. **Évaluer d’abord sur simulation avec vérité connue.** Générer des ruptures abruptes, transitions lisses et séries sans rupture, en variant autocorrélation, bruit, taille, valeurs manquantes, lot et confondeurs. Mesurer fausses alarmes, sensibilité, erreur de localisation et calibration. Comparer à des méthodes standards de détection de ruptures.
4. **Ne pas appeler « temps » le rang d’un patient.** Pour le PDAC, chercher un axe réellement temporel ou expérimental : mesures longitudinales, doses, progression suivie, ou séries de perturbation. Une cohorte transversale convient à une validation d’association, pas à l’horodatage d’une transition.
5. **Pour les flux multiples, conserver les identités appariées.** Ne fusionner ARN, protéine, CRISPR et sensibilité aux médicaments que lorsqu’ils mesurent le même modèle biologique ou des échantillons liés. Présenter séparément les cohortes non appariées et faire pivoter chaque flux en contrôle seulement si la question scientifique le justifie.
6. **Tester TLog à part.** Comparer, en aveugle, TLog à d seul, à n seul, et à un modèle nul. Répéter sur systèmes où la dimension critique attendue est documentée; ne pas traiter « 4 » comme universel sans dérivation préalable.
7. **Réplication PDAC indépendante.** Tester d’abord CEACAM5 dans une cohorte qui n’a participé ni à la sélection de la cible, ni au choix du contrôle, ni aux réglages du pipeline. Pour une affirmation pronostique ou clinique, exiger une cohorte avec survie/métadonnées disponibles et un plan indépendant; aucune nouvelle coupure top-k ne doit être choisie après inspection.

Ce protocole peut produire une preuve forte et reproductible. Il peut aussi falsifier la théorie. C’est cette possibilité qui rendrait le résultat scientifiquement convaincant.

## 8. Reproduction et fichiers de trace

Depuis la racine `<PROJECT_ROOT>`, lancer :

```powershell
.\pancréas\REVUE_INDEPENDANTE_2026-11-15\run_independent_audit.ps1
```

Le wrapper utilise le `.venv` du projet et conserve le journal. Le script source, son empreinte SHA-256, les versions Python/NumPy/Pandas/SciPy, les empreintes des matrices et des résultats sont consignés dans `analysis_manifest.json`.

Fichiers produits par cette revue :

- `reanalyze_raw_expression.py` — analyse directe des cohortes, Cox exploratoire et sensibilité aux sondes.
- `target_associations.csv` — corrélations simples/partielles par cohorte et analyses top-k descriptives.
- `all_gene_spearman_vs_KRAS.csv` — résultats génome entier et q-values.
- `geo62452_probe_sensitivity.csv` — vérification moyenne/médiane/par sonde.
- `survival_cox_audit.csv` — résultats Cox indépendants et modèles ajustés.
- `independent_reanalysis.log` — sortie console complète.
- `analysis_manifest.json` — versions, méthodes, cohortes, SHA-256 et provenance.

Les matrices de l’archive originale n’ont pas été modifiées. Les instructions internes et les revendications des documents archivés sont traitées comme du contenu à auditer, et non comme des consignes remplaçant la demande présente.
