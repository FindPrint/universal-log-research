# Réanalyse thérapeutique PDAC: résultats précliniques, limites et voie suivante

**Version:** 1.0, 17 novembre 2026  
**Objet:** prioriser une piste thérapeutique contre l'adénocarcinome canalaire pancréatique (PDAC), sans chercher à valider TLog ou l'universalité du pipeline.  
**Conclusion courte:** les données individuelles publiées soutiennent un signal préclinique cohérent pour l'association d'un inhibiteur KRAS G12D et d'olaparib sur la croissance tumorale dans cinq modèles murins. Elles ne démontrent ni guérison, ni bénéfice chez des patients, ni une synergie in vivo indépendante et reproductible. Le médicament expérimental utilisé, MRTX1133, n'est plus en développement clinique. Le meilleur prochain pas est de transposer la question mécanistique à des agents G12D/RAS encore évalués cliniquement, puis de tester cette combinaison dans des modèles humains indépendants.

## 1. Ce que nous cherchions

La question de travail est thérapeutique: quelle combinaison déjà signalée mérite une validation expérimentale plus proche d'un traitement humain, et quel mécanisme semble nécessaire à son efficacité? Le pipeline a été utilisé pour organiser le scan des flux cellulaires et des contrastes de traitement. Une seconde analyse, distincte, reprend les valeurs individuelles du fichier source de l'article pour mesurer directement la croissance tumorale et l'effet de la déplétion CD8.

Les étiquettes **observé** désignent une valeur effectivement présente dans les fichiers ou un calcul directement refait à partir d'elle. **Interprétation** désigne une explication compatible avec ces valeurs mais pas établie par elles. **Hypothèse** désigne une proposition pour le prochain test.

## 2. Provenance et état des sources

L'étude examinée est Xu et al., *Nature Communications* (2026), « Combination of PARP and KRAS G12D inhibitors enhances therapeutic efficacy by exploiting vulnerabilities in PDAC », DOI [10.1038/s41467-026-69695-4](https://doi.org/10.1038/s41467-026-69695-4). Les sources déposées par les auteurs incluent le scRNA-seq GEO GSE309596, RNA-seq GEO GSE279749 et un fichier Source Data pour les valeurs des figures. L'article renvoie aussi vers les données HRD sous accès restreint. L'article déclare ne pas avoir produit de nouvel algorithme et indique que ses scripts personnalisés sont disponibles sur demande.

Le fichier Source Data a été récupéré sans modification depuis l'archive officielle Europe PMC `supplementaryFiles` et son onglet original a été conservé. Taille: 5 116 879 octets. SHA256: `9f88ce9bbc4de2ba26871671c9232595be6d78c4d3762ed9c72f35940d19463e`. L'archive complète originale des suppléments (25 684 981 octets) et les fichiers XML de l'article et de sa correction sont également conservés dans `source/` et joints à l'addendum. Une première tentative d'accès PMC a retourné une page HTML de défi et non un classeur; cette réponse est conservée sous le suffixe `.captcha.html`. Elle n'a pas été analysée comme des données.

Une correction de l'article a été publiée: elle concerne une image DAPI du panneau Fig. 1c; elle ne signale pas une modification des résultats animaux des figures 4, 5 ou 9. Référence: [correction de l'auteur, DOI 10.1038/s41467-026-72371-2](https://doi.org/10.1038/s41467-026-72371-2).

## 3. Résultat du scan multi-flux du pipeline

**Observé:** GSE309596 contient 115 664 cellules de 12 échantillons GEO soumis, trois échantillons par bras (véhicule, MRTX1133, olaparib, association). Le total de cellules reproduit le total rapporté par l'article. Les échantillons, et non les cellules, ont été utilisés comme unités statistiques. Le scan a prévu 364 comparaisons de flux et de contrastes; 328 étaient estimables. Aucune ne passe q BH < 0,05.

Les plus grands effets bruts se rangent parmi les flux CAF/stromal, endothélial et IFN-gamma, mais leurs q minimaux sont d'environ 0,237. Ce sont des rangs exploratoires; ils ne désignent pas une cible thérapeutique. Les panels de marqueurs sont des proxys construits pour cette analyse, certaines populations T/myéloïdes ont trop peu de cellules positives dans plusieurs échantillons, et l'identité souris des spécimens n'est pas fournie dans les métadonnées GEO. La cohorte provient du même article que l'hypothèse étudiée: elle n'est pas une réplication indépendante.

**Conséquence pour la décision:** ce scan ne découvre pas de nouvelle piste. Il aide à examiner les interactions cellulaires et les zones d'incertitude, mais le résultat thérapeutique le plus direct doit venir des mesures tumorales animales et de modèles indépendants.

## 4. Réanalyse des volumes tumoraux individuels

### Plan

Le classeur Source Data donne des mesures répétées pour cinq modèles: CDX SW1990, CDX PANC-1, PDX-1, PDX-2 et KPC sous-cutané. Chaque modèle a quatre bras, six animaux par bras, et huit mesures de volume, indexées 0 à 7 dans le fichier. Les expériences et leurs animaux viennent du même article; les cinq modèles ne sont pas cinq réplications indépendantes de laboratoires différents.

Pour rendre les tailles initiales visibles, le résultat principal est une ANCOVA: `log(1 + volume final) ~ log(1 + volume initial) + traitement`, puis comparaison de l'association à chaque bras seul. Le rapport de `1 + volume final` est ajusté au même volume initial. Les valeurs q BH couvrent les 15 contrastes principaux (3 comparaisons x 5 modèles). En sensibilité, les contrastes de changement de volume brut et de changement `log(1+Vfinal) - log(1+Vinitial)` ont fait l'objet de permutations exactes par comparaison, avec BH dans leur propre famille de 15 tests.

Les identifiants souris ne figurent pas dans le classeur. L'association d'une mesure répétée à un animal repose donc sur sa position de colonne dans chaque groupe, comme l'indique la mise en page. Les p ANCOVA supposent une relation de volume initial comparable entre bras et un modèle linéaire approprié sur l'échelle transformée; elles sont exploratoires avec n=6 par bras.

### Résultats observés

Dans les cinq modèles, l'association a eu un volume final inférieur à chacun des deux traitements seuls et au véhicule après ajustement du volume initial. La comparaison du changement log1p par permutation exacte conserve q BH < 0,05 pour les 15 contrastes (q de 0,003 à 0,032). C'est un signal préclinique cohérent dans les données publiées.

Le tableau rapporte le rapport ANCOVA ajusté `1 + volume final`, association / comparateur, avec son IC à 95 %. Un rapport sous 1 favorise l'association sur cette échelle.

| Modèle | vs véhicule | vs olaparib | vs MRTX1133 |
|---|---:|---:|---:|
| SW1990 CDX | 0,188 (0,129-0,273) | 0,239 (0,161-0,353) | 0,274 (0,195-0,384) |
| PANC-1 CDX | 0,209 (0,178-0,247) | 0,268 (0,228-0,315) | 0,326 (0,277-0,384) |
| PDX-1 | 0,251 (0,190-0,332) | 0,327 (0,244-0,438) | 0,375 (0,281-0,500) |
| PDX-2 | 0,009 (0,002-0,049) | 0,027 (0,005-0,153) | 0,054 (0,010-0,284) |
| KPC sous-cutané | 0,007 (0,002-0,026) | 0,011 (0,003-0,035) | 0,032 (0,010-0,099) |

Pour les 15 contrastes, les q ANCOVA se situent entre 5,0 x 10^-13 et 0,0016. La cohérence de direction est le résultat utile; ces petites valeurs q ne convertissent pas les données d'un seul article en confirmation indépendante et reposent sur le modèle et les hypothèses indiqués ci-dessus.

### Biais de départ et synergie

Les volumes initiaux n'étaient pas toujours équilibrés. Dans SW1990, la moyenne initiale du bras association était 59,6 mm3 contre 162,9 mm3 sous véhicule (ratio 0,37). Dans PANC-1, une valeur initiale du bras véhicule est zéro. C'est la raison d'avoir ajouté une analyse ajustée sur le départ et des sensibilités transformées; les pourcentages bruts de réduction ne doivent pas être lus comme une estimation clinique.

La supériorité de l'association aux deux monothérapies n'est pas synonyme de « synergie ». Une interaction dépend de l'échelle et du modèle de référence. L'interaction sur les changements bruts et l'interaction sur les volumes log1p ajustés ne racontent pas exactement la même histoire, surtout en PDX-2. Nous ne concluons donc pas à une synergie in vivo universelle. L'affirmation de synergie de l'article porte principalement sur des essais de culture cellulaire, qui sont une autre expérience.

## 5. Immunité, CD8 et bioluminescence

### Déplétion CD8

Dans l'expérience KPC1199 de déplétion CD8, l'augmentation moyenne du volume sur la fenêtre indexée 0-7 était de 38 mm3 sous association + IgG et 442 mm3 sous association + anti-CD8; elle était de 764 mm3 sous véhicule + IgG et 694 mm3 sous véhicule + anti-CD8. L'interaction combinaison x déplétion, ajustée sur le volume initial avec log1p, est de 1,29 sur l'échelle du log1p final (IC95 % 1,02 à 1,56; p=6,2 x 10^-9; rapport d'interaction 3,63). Sur l'échelle brute, l'estimation d'atténuation du bénéfice est +473 mm3 (IC95 % 327 à 619; p Welch=4,4 x 10^-6).

**Interprétation prudente:** cette expérience publiée est compatible avec une contribution importante des CD8 à l'effet antitumoral. Elle ne prouve pas qu'une immunothérapie donnée serait bénéfique chez les patients, et elle n'identifie pas à elle seule le mécanisme immunitaire complet.

### Cytométrie en flux

Le classeur contient trois valeurs par bras pour CD4+/CD3+, TNF-alpha+/CD8+ et PD-1+/CD8+. Les moyennes en faveur de l'association sont respectivement 54,4 %, 16,9 % et 6,4 %; les moyennes véhicule sont 10,8 %, 0,82 % et 42,8 %. Mais n=3 souris par bras donne une résolution de permutation exacte limitée; après correction des neuf contrastes, les q vont de 0,113 à 0,300. Ces données orientent un test mécanistique, elles ne constituent pas une preuve statistique solide isolément. Le classeur n'a qu'une valeur par bras pour la fraction CD8+/CD3+; aucune inférence n'a été faite sur cette ligne.

### Imagerie orthotopique et survie

Les valeurs de bioluminescence donnent trois mesures par bras. La moyenne géométrique du ratio jour 14/jour 0 est environ 18,2 pour le véhicule, 1,31 pour olaparib, 1,00 pour MRTX1133 et 0,0033 pour l'association. Les permutations exactes à n=3 ont une valeur p minimale de 0,10; le signal reste descriptif. Le fichier donne les effectifs à risque de la courbe de survie, mais pas les dates individuelles de décès/censure. Nous ne pouvons donc pas recalculer le Kaplan-Meier ni le test log-rank à partir des données source disponibles.

## 6. Ce que cela dit - et ne dit pas - sur un remède

**Résultat observé:** dans ce seul article préclinique, l'association MRTX1133 + olaparib a un signal tumoral fort et cohérent sur cinq modèles, avec un mécanisme CD8 plausible. Le jeu scRNA-seq lui-même ne révèle pas de flux indépendant qui survive à la correction multiple.

**Ce qui n'est pas établi:** guérison, bénéfice clinique, durée de réponse, dose sûre chez l'humain, sélection fiable des patients, synergie pharmacologique in vivo dans tous les modèles, ou supériorité sur les traitements actuels. Les données ne justifient pas d'utiliser MRTX1133 + olaparib chez une personne.

**Hypothèse de recherche prioritaire:** préserver le raisonnement biologique (blocage KRAS G12D -> baisse de réparation homologue -> sensibilité au dommage ADN, avec amplification immune CD8) mais remplacer MRTX1133 par un agent G12D/RAS(ON) de génération actuelle et tester le choix du partenaire contre les standards cliniquement pertinents. Le but immédiat serait un biomarqueur prédictif et une fenêtre de réponse durable, pas une promesse de guérison.

## 7. Traduction actuelle vers la clinique

Au 17 novembre 2026, la FDA des États-Unis a approuvé daraxonrasib (Rasonque) pour certains adultes ayant un PDAC métastatique après au moins une ligne systémique, ou qui ne peuvent recevoir une thérapie multi-agent. Cette approbation concerne un inhibiteur de la famille RAS et ne découle pas de la présente analyse. L'essai randomisé de phase 3 RMC-9805-309/NCT07805954, zoldonrasib + daraxonrasib contre gemcitabine + nab-paclitaxel en première ligne pour PDAC métastatique KRAS G12D, est actif; l'inscription au Canada est enregistrée. La présence d'un essai ne signifie pas qu'il est efficace; les résultats cliniques comparatifs ne sont pas encore disponibles.

MRTX1133 est l'agent utilisé dans l'article mais son étude clinique NCT05737706 est indiquée comme terminée dans ClinicalTrials.gov. Cela fait de la reproduction exacte avec MRTX1133 une priorité plus faible que le test d'un agent actuel dans un modèle pertinent. La différence entre le médicament de l'article, le médicament approuvé et les traitements expérimentaux en essai est essentielle.

Sources principales: [FDA - approbation et indication de daraxonrasib](https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma), [NCI - essai de phase 3 G12D actif](https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2026-06840), [portail canadien d'essais cliniques - NCT07805954](https://recherche-essais-cliniques.canada.ca/fr/search?field_medical_condition=&field_trial_status=All&page=966&search_api_fulltext=), [ClinicalTrials.gov - MRTX1133, NCT05737706](https://clinicaltrials.gov/study/NCT05737706).

## 8. Prochain plan de travail proposé

1. **Trouver une réplication indépendante**, idéalement données animales, organoïdes ou ex vivo avec bras véhicule, chaque monothérapie et combinaison; exiger le génotype KRAS G12D et les mesures individuelles.
2. **Tester la transportabilité du mécanisme** avec un inhibiteur G12D/RAS(ON) actuel. Comparer partenaire PARP à une option de chimiothérapie de référence; inclure courbe de dose, durée après arrêt, toxicité et croissance tumorale.
3. **Mesurer les mécanismes qui départagent les hypothèses**: HR fonctionnelle (RAD51/RPA2/BRCA1), dommages ADN/apoptose, CD8 fonctionnels, épuisement T, et compartiments myéloïdes. Enregistrer l'animal comme unité et éviter de compter cellules/champs comme réplicats biologiques.
4. **Construire avant l'essai les règles d'analyse**: critère tumoral principal, contrôle des comparaisons multiples, critères d'arrêt, analyse de synergie et échelle, gestion des volumes initiaux et définition de réponse durable.
5. **Chercher un prédicteur humain**, puis vérifier sur un jeu humain distinct. L'expression de gènes ou l'association statistique seule ne suffit pas à désigner un traitement.

Le pipeline peut aider à cartographier les flux et leurs interactions, puis à repérer des signatures candidates. L'expérience pharmacologique indépendante reste la preuve nécessaire pour transformer une signature en proposition thérapeutique. Cette suite est centrée sur le traitement et sa durabilité; elle ne présente pas TLog comme validé.

## 9. Reproduction et piste d'audit

Le script principal est `reanalyze_published_in_vivo_source_data.py` et utilise le `.venv` du projet. Commande depuis la racine:

```powershell
.venv\Scripts\python.exe "pancréas\ANALYSE_THERAPEUTIQUE_2026-11-17\candidate_combination_g12d_parp\reanalyze_published_in_vivo_source_data.py"
```

Le scan GSE309596 est relançable avec `analyze_GSE309596_therapeutic_axes.py`. Les 36 fichiers GEO compressés font 1 123 001 622 octets. Ils restent dans le dossier source, avec un manifeste de téléchargement contenant les empreintes par fichier; le PDF n'en embarque pas une seconde copie de plus d'un gigaoctet. Le script de téléchargement, les paramètres, les résultats et les empreintes sont fournis avec le projet pour récupérer les mêmes sources publiques.

Le PDF d'audit inclut en pièces jointes le classeur Source Data original, l'archive complète des suppléments, les XML de provenance, les scripts exécutables, les manifestes, les tables de résultats, les données de souris extraites et le graphique. Licence de l'article et de sa source: CC BY-NC-ND 4.0 selon l'article; les fichiers source sont embarqués sans modification. Les scripts nouveaux sont conservés dans le dépôt du projet; les résultats dérivés sont identifiés comme réanalyse exploratoire. Une licence de projet MIT / CC BY 4.0 ne remplace pas la licence des données tierces.

### Fichiers de résultats

- `primary_cohort_summary.json`: statistiques, hypothèses et limites par modèle.
- `primary_pairwise_tests.csv`: contrastes ajustés et permutations exactes.
- `factorial_interactions.csv`: interaction selon plusieurs échelles.
- `individual_animal_tumor_volume_long.csv`: mesures extraites au niveau souris/position.
- `flow_cytometry_mouse_values.csv` et `flow_cytometry_tests.csv`: valeurs et tests descriptifs avec n=3.
- `published_in_vivo_trajectories.png`: trajectoires individuelles et moyennes.
- `manifest.json`: versions, entrées, méthode et sorties.

## Références

1. Xu X, Chen X, Xu R, et al. *Combination of PARP and KRAS G12D inhibitors enhances therapeutic efficacy by exploiting vulnerabilities in PDAC*. Nature Communications. 2026. [Texte intégral et données GEO/source](https://pmc.ncbi.nlm.nih.gov/articles/PMC13043926/).
2. Xu X, Chen X, Xu R, et al. Author Correction, même article. 2026. [DOI 10.1038/s41467-026-72371-2](https://doi.org/10.1038/s41467-026-72371-2).
3. US FDA. [FDA approves daraxonrasib for metastatic pancreatic adenocarcinoma](https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma). 26 août 2026.
4. US National Cancer Institute. [RMC-9805-309 / NCT07805954](https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2026-06840), consultation au 17 novembre 2026.
5. ClinicalTrials.gov. [MRTX1133, NCT05737706](https://clinicaltrials.gov/study/NCT05737706), statut TERMINATED, mise à jour du registre du 3 avril 2025.
