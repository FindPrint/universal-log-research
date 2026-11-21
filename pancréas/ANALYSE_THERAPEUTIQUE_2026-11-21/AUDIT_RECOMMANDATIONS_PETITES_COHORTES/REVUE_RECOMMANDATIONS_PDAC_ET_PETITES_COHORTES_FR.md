# Audit des recommandations : petites cohortes, trithérapie et courbes de dose

**Date :** 21 novembre 2026

**Périmètre :** audit des trois recommandations reçues, inventaire d’un jeu public de PDO, et contrôle de compatibilité avec les 29 estimateurs réels d’UNIVERSAL_LOG v6.0.0.

**Statut :** audit exploratoire reproductible. Aucun changement du code v6.0.0, aucune analyse clinique et aucune demande de données aux auteurs.

## Résumé

Les recommandations repèrent une vraie occasion : un jeu public d’organoïdes pancréatiques et des jeux de réponse dose-réponse peuvent servir à éprouver une future configuration biomédicale du pipeline. Mais les seuils et conclusions proposés ne sont pas encore justifiés.

Le jeu décrit par [Yin et al. (Nature Communications, 2025)](https://www.nature.com/articles/s41467-025-57520-3) contient 46 PDO, 63 composés et plus de 7 000 mesures d’interaction. Ce nombre de modèles ne signifie pas qu’une courbe individuelle a 46 points ordonnés : la méthode publiée utilise sept concentrations, des mesures en double et deux expériences indépendantes. Le tableau supplémentaire public fournit principalement des AUC résumées; le tableau Source Data livre certaines courbes de dose détaillées, mais celles de la Figure 6d n’ont que 7 ou 8 niveaux. Le mode rapide de v6.0.0 exige 50 points.

Le contrôle effectué ici a transmis **150 colonnes de mesure** de la Figure 6d, séparément et sans concaténer les colonnes appariées, à la fonction apply_complexity de v6.0.0. **150/150 sont rejetées par la limite de longueur; aucune ne produit d’estimateur fini (0/29).** Ce résultat est une incompatibilité d’entrée pour ce mode, pas un résultat biologique et pas un test complet cible/contrôle.

La paire **MRTX1133 + olaparib** dispose maintenant de preuves précliniques directes publiées, y compris une dépendance à CD8 dans un modèle murin. Cela ne valide pas la trithérapie avec un ADC anti-MUC1-C ou un modulateur KCNN4. Le chiffre « 87 % » n’a pas été retrouvé dans l’article primaire MRTX1133–olaparib consulté; il ne faut pas le reprendre sans préciser l’étude, le modèle, le bras et le critère.

## Tableau de décision

| Recommandation reçue | Évaluation | Décision méthodologique |
|---|---|---|
| Activer un mode petites séries entre N=20 et 49 et valider un estimateur s’il persiste dans 95 % de 1 000 bootstraps. | Le problème du seuil fixe mérite une étude. En revanche, le nombre de tirages et 95 % sont des paramètres de décision proposés, pas des seuils étalonnés. Les PDO ont des unités hiérarchiques : organoïde, composé, dose, puits et expérience ne sont pas interchangeables. | Ne pas ajouter cette règle telle quelle. Concevoir une calibration séparée, avec abstention, cas nuls, transitions synthétiques connues, données groupées et unités de rééchantillonnage déclarées. |
| Formaliser MRTX1133 + olaparib + ADC anti-MUC1-C ou AS-77/KCNN4 comme trithérapie optimale. | La combinaison MRTX1133–olaparib est directement étudiée; l’ADC anti-MUC1-C avec MRTX1133 est une piste distincte. La combinaison à trois agents n’est pas établie par le fait de juxtaposer ces études. AS-77 est en outre ambigu. | Garder la trithérapie comme hypothèse de recherche. Ne pas la qualifier d’optimale ni de remède. Vérifier l’identité chimique exacte et le mécanisme avant toute analyse KCNN4. Tester d’abord les associations directement mesurées et leurs contrôles. |
| Utiliser DepMap/GDSC comme courbes dose-réponse et interpréter T₀ comme IC50. | Les données dose-réponse sont bien disponibles. PRISM secondaire comporte 8 doses; GDSC1 utilise selon les essais 9 ou 5 points; GDSC2 utilise 7 points. Les producteurs ajustent des modèles dose-réponse, notamment mixtes pour GDSC. | Bonne piste de benchmark externe. Comparer les sorties UNIVERSAL_LOG aux ajustements dose-réponse/AUC/IC50 conventionnels. T₀ n’est pas assimilé à l’IC50 tant que cette équivalence n’a pas été testée et validée. Garder ensemble les mesures d’un même modèle, composé, expérience et courbe. |

## 1. Petites cohortes : l’effectif du projet n’est pas la longueur de chaque flux

### Faits trouvés dans l’article et les fichiers publics

Yin et al. rapportent 46 PDO évalués contre une bibliothèque de 63 composés, avec plus de 7 000 mesures d’interaction. Leur méthode mentionne des puits en double, deux expériences indépendantes, sept concentrations pour le criblage et cinq jours d’exposition. Le fichier Supplementary Data 10 comprend des matrices AUC pour les médicaments; il ne s’agit pas d’une table brute générale de chaque puits à chaque dose.

Le fichier Source Data contient une feuille Figure 6 avec 75 en-têtes PDO–médicament pour la Figure 6d et deux colonnes de mesures par en-tête, soit 150 colonnes. Ces colonnes représentent les valeurs conservées dans la feuille; leur relation exacte aux répétitions techniques et aux deux expériences n’est pas explicitée par l’en-tête, donc elles n’ont pas été regroupées. Les séries visibles ont 7 ou 8 doses, avec quelques mesures manquantes.

Les empreintes SHA-256 et dimensions de toutes les feuilles inspectées sont dans [PDO_SOURCE_WORKBOOK_INVENTORY.json](PDO_SOURCE_WORKBOOK_INVENTORY.json). Les classeurs sources restent sous source/ et ne sont pas publiés dans ce dépôt; le script les télécharge depuis Nature au moment de la reproduction.

### Résultat obtenu avec le code du pipeline

- Pipeline testé : [universal_v6.0.0_cohen - Copie.py.txt](../../universal_v6.0.0_cohen%20-%20Copie.py.txt), version v6.0.0, SHA-256 bb8bbdba4eb1f8c55b49748274ae8fbfef8a43f6c1b890964f18ba77960c0773.
- Mode : fast; Cohen-d; longueur minimale configurée = 50.
- Entrée : 150 colonnes de mesure Figure 6d, chacune transmise séparément à la fonction réelle apply_complexity.
- Résultat : 30 colonnes ont 7 doses et 120 en ont 8; 150/150 sont rejetées par la limite, et le total est 0/29 estimateurs finis.
- Sorties : [PDO_FIG6D_PIPELINE_GATE.csv](PDO_FIG6D_PIPELINE_GATE.csv) et [PDO_FIG6D_PIPELINE_GATE_SUMMARY.json](PDO_FIG6D_PIPELINE_GATE_SUMMARY.json).

**Interprétation permise :** la version v6.0.0 actuelle ne calcule pas ses estimateurs sur les séries de dose publiées dans cette feuille. Ce résultat n’évalue ni l’effet du médicament ni la pertinence biologique des courbes.

### Pourquoi la règle bootstrap 1 000 / 95 % n’est pas encore une validation

Le nombre de rééchantillonnages ne crée pas de nouvelles expériences indépendantes. Rééchantillonner les doses comme si elles étaient des observations interchangeables détruirait l’ordre et l’espacement de l’axe concentration. Rééchantillonner les deux expériences indépendantes comme des unités groupées donne peu d’unités et ne justifie pas, à lui seul, un seuil de persistance à 95 %.

Il faut distinguer deux problèmes :

1. **Cohorte de modèles :** les PDO sont des modèles biologiques indépendants pour une comparaison inter-organoïdes, mais aucune permutation de leur ordre arbitraire ne crée une trajectoire temporelle.
2. **Courbe de dose d’un PDO :** la concentration est un axe ordonné, mais la courbe possède seulement 7–8 niveaux dans les données vérifiées ici. Les répétitions restent imbriquées dans le modèle et l’expérience.

Une éventuelle fonction petites séries doit donc avoir un protocole et un usage explicites : comparer des trajectoires ordonnées courtes n’est pas le même problème que comparer des groupes biologiques de petite taille.

## 2. Trithérapie : séparer les résultats publiés des hypothèses combinées

### Ce que l’article MRTX1133–olaparib rapporte

L’article primaire 2026 [Combination of PARP and KRASG12D inhibitors enhances therapeutic efficacy by exploiting vulnerabilities in PDAC](https://www.nature.com/articles/s41467-026-69695-4) teste la **combinaison à deux agents** MRTX1133 + olaparib. Il rapporte des interactions in vitro dans quatre modèles, des réponses supérieures aux monothérapies dans des modèles CDX/PDX, et une diminution de l’effet antitumoral combiné après déplétion des CD8 dans un modèle murin. La figure 3 rapporte une inhibition de croissance cellulaire d’au moins 50 % pour les conditions indiquées et des scores Bliss au-dessus du seuil choisi par les auteurs. Ce sont des résultats précliniques dans les modèles et conditions rapportés, pas une preuve clinique.

Le texte primaire consulté ne donne pas le chiffre de 87 % avancé dans la recommandation. **À clarifier avant de le citer :** est-ce une inhibition de volume tumoral, un taux de contrôle, une réponse par modèle, ou une mesure sur une autre thérapie? En attendant, ce chiffre ne figure pas dans la présente synthèse comme résultat vérifié de MRTX1133 + olaparib.

### Pourquoi l’ADC anti-MUC1-C ne complète pas automatiquement le triplet

L’étude Ozawa et al. 2025 auditée dans le projet teste séparément un ADC anti-MUC1-C avec MRTX1133 dans certains modèles. Le rapport local [AUDIT_DISPONIBILITE_REPONSE_ADC_FR.md](../MRTX1133_MUC1C_AUDIT/AUDIT_DISPONIBILITE_REPONSE_ADC_FR.md) décrit l’accès aux mesures brutes. Aucune des sources vérifiées ici n’établit l’effet du triplet MRTX1133 + olaparib + ADC anti-MUC1-C. Il faut mesurer ce triplet avec ses monothérapies, paires, contrôles isotype/payload et doses avant de parler de synergie à trois.

CEACAM5 et MUC1 peuvent être conservés comme marqueurs exploratoires si la question les concerne. Les sources citées ne valident pas CEACAM5 comme biomarqueur prédictif de cette trithérapie. Pour un ADC, l’ARN MUC1 seul ne remplace pas la mesure de l’épitope/protéine de surface et de son hétérogénéité.

### Vérification de AS-77 / KCNN4

KCNN4 code KCa3.1, et une étude primaire décrit un axe KCNN4/Ca²⁺/MET/AKT comme piste dans le PDAC ([étude](https://www.nature.com/articles/s41401-021-00688-3)). Mais les recherches sur le libellé exact AS-77 renvoient aussi à PAP-1, présenté comme inhibiteur de Kv1.3/KCNA3 dans des sources pharmacologiques; Kv1.3 et KCNN4/KCa3.1 sont des canaux distincts ([étude primaire PAP-1/Kv1.3](https://pmc.ncbi.nlm.nih.gov/articles/PMC3407946/), [notice de composé AS-77/PAP-1](https://www.medkoo.com/products/12722)).

Cette correspondance peut être un homonyme ou une confusion de nom. **Aucun composé AS-77 n’est assigné à KCNN4 dans cet audit.** Il faut une référence primaire ou le nom chimique/CAS/catalogue exact avant de construire la piste de traitement.

## 3. DepMap et GDSC : bons jeux de référence, pas une conversion automatique en T₀

La page officielle DepMap/PRISM décrit un écran secondaire de 1 448 composés sur 499 lignées, à 8 doses en dilution 4 fois, et fournit des fichiers de mesures et paramètres dose-réponse ([PRISM officiel](https://depmap.org/repurposing/)). La documentation officielle Sanger indique 9 ou 5 doses pour GDSC1 et 7 pour GDSC2; elle précise que les données brutes sont normalisées par plaque et ajustées avec un modèle non linéaire mixte, en utilisant les réplicats d’une courbe ([documentation Drug Sensitivity](https://depmap.sanger.ac.uk/documentation/datasets/drug-sensitivity/)).

Ces données sont utiles pour un **benchmark de courbes ordonnées courtes**. Elles ne satisfont pas la longueur rapide de 50 points par courbe. Il faut garder les courbes par modèle et médicament, conserver les coordonnées réelles en concentration logarithmique, inclure les contrôles de plaque de façon traçable et comparer les sorties du pipeline à des références conventionnelles : ajustement dose-réponse, IC50 lorsque le modèle est identifiable, AUC, qualité d’ajustement et incertitude. Le résultat doit pouvoir être « indéterminé ». T₀ = IC50 reste une hypothèse testable, pas une identité définie.

## Recommandation de suite

### Étape A — Calibration avant ajout d’un mode court

Écrire une spécification distincte pour deux usages : (a) séquence ordonnée courte, par exemple dose ou temps; (b) groupe de petite taille, par exemple une comparaison de cohortes. Les deux ne doivent pas partager automatiquement le même seuil de N.

Pour le mode dose, comparer des séries synthétiques monotones avec seuil connu, courbes plates, bruits purs, plateaux hors de la fenêtre, effets non monotones et données manquantes. Évaluer biais de localisation, couverture des intervalles, taux de fausses alertes et abstention selon 7, 8, 10, 20, 30 et 50 points. Calibrer les seuils avant de les figer; ne pas choisir 95 % comme résultat parce qu’il paraît prudent.

### Étape B — Benchmark externe reproduisible

Construire un corpus public de courbes DepMap/GDSC par modèle, composé, plaque, réplicat et concentration. Comparer les sorties UNIVERSAL_LOG à AUC/IC50/fits standards sur des données tenues à part. Garder un fichier d’analyse par flux, les colonnes de contrôle, le statut de l’axe et toutes les abstentions.

### Étape C — PDAC, sans surinterpréter les combinaisons

Commencer par vérifier les courbes et comparateurs disponibles pour olaparib et les autres agents dans les jeux ouverts; la présence exacte de chaque agent doit être confirmée dans le fichier source avant d’extraire une cohorte. Pour le triplet, l’étape probante reste une matrice directement mesurée sur plusieurs modèles, incluant les traitements simples et doubles, des réplicats biologiques, des contrôles de cible/payload et une validation indépendante. Une analyse de signatures RNA ou de tableaux AUC ne prouve pas l’efficacité d’un traitement non testé.

## Reproduction

Depuis la racine du projet, avec .venv :

~~~powershell
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\AUDIT_RECOMMANDATIONS_PETITES_COHORTES\inspect_pdac_organoid_source.py
.\.venv\Scripts\python.exe .\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-21\AUDIT_RECOMMANDATIONS_PETITES_COHORTES\run_pdac_small_cohort_gate.py
~~~

Le premier script télécharge les classeurs Nature, calcule leurs empreintes et inventorie les feuilles. Le deuxième transmet séparément les colonnes de dose de la Figure 6d à apply_complexity du fichier v6.0.0; il ne lance pas le pipeline complet et n’en déduit aucun T₀/TLog.
