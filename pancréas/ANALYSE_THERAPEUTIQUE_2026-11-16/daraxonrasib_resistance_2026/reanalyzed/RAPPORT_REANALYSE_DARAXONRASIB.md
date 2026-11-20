# Réanalyse traçable: résistance au daraxonrasib dans le PDAC

Généré (UTC): 2026-11-17T01:02:07+00:00  
Article primaire: Aronchik et al., Nature Medicine (2026), https://doi.org/10.1038/s41591-026-04537-w.  
Nature de ce travail: réplication arithmétique/descriptive de données publiées. Ce n'est ni une découverte thérapeutique indépendante, ni une preuve de guérison, ni un avis médical.

## Résumé scientifique

L'article décrit des altérations acquises de signalisation RAS dans un groupe sélectionné de patients ayant bénéficié initialement du daraxonrasib puis progressé. Les données publiées et les expériences précliniques pointent vers une réactivation du flux RAS/MAPK et évaluent des associations avec ciblage RTK, double inhibition RAS(ON), ou réponse aux dommages de l'ADN (DDR). Ces pistes sont déjà rapportées par les auteurs; notre apport ici est de préserver et recalculer une partie des tables/données source, avec des limites explicites.

## Contexte clinique actuel

Au 16 novembre 2026, la FDA a approuvé le daraxonrasib (RASONQUE) le 26 août 2026 pour certains adultes atteints d'un adénocarcinome pancréatique métastatique après au moins une ligne systémique ou non candidats à une thérapie multi-agents. Dans l'essai randomisé de 500 personnes, la médiane de survie globale rapportée était 13,2 contre 6,7 mois (HR 0,40), et la médiane de survie sans progression 7,2 contre 3,6 mois. Ce bénéfice important ne signifie pas guérison: l'étude de résistance que nous réanalysons porte précisément sur la progression après un bénéfice initial. Ces résultats cliniques ne valident pas les doubles combinaisons testées chez la souris; l'intérêt de ce projet est de prioriser les questions de résistance et de biomarqueurs, pas de conseiller un traitement à une personne. Source FDA: https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma.

Mise à jour clinique vérifiée le 16 novembre 2026: un essai randomisé de phase III actif (RASolute 309; NCT07805954) évalue daraxonrasib + zoldonrasib contre gemcitabine + nab-paclitaxel en première ligne chez des patients avec PDAC métastatique KRAS G12D. L'essai est une question clinique déjà en cours, pas un résultat d'efficacité ni une preuve de guérison. Source NCI: https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2026-06840.

## Réplication des comptes cliniques du supplément

- Cohorte à 160–300 mg/j: n=44; altération acquise signalée dans les colonnes « RAS signaling pathway »: 26; KRAS amplification acquise: 16.
- Cohorte distincte à ≤120 mg/j: n=13; événements dans ces colonnes: 4; KRAS amplification: 1. Ce n'est pas un bras témoin randomisé.
- KRAS amplification par statut TP53 prétraitement dans la cohorte haute dose: TP53-mut 15/32; TP53-wt 1/12.
- Plus d'un événement textuel trouvé par séparation des points-virgules dans les deux colonnes d'altérations: 11. Ce compte mécanique n'est pas une nouvelle classification de voies.
- Variants KRAS secondaires repérés par motif textuel simple: 0; ce contrôle ne remplace pas l'annotation experte.

Tests de Fisher recalculés:
- TP53 status vs acquired KRAS amplification: OR=9.706; Fisher p=0.032154; table=[[15, 17], [1, 11]]
- 160-300 mg vs <=120 mg: pathway acquisition: OR=3.25; Fisher p=0.11372; table=[[26, 18], [4, 9]]

Ces proportions concordent avec les chiffres de l'article (26/44 pour les altérations de voie et 16/44 pour KRAS amplification). La cohorte est sélectionnée sur une réponse/stabilisation initiale, puis une progression. Sans patients comparateurs qui ne progressent pas, cette table ne permet pas d'estimer un prédicteur général de résistance.

## Réanalyse exploratoire de points finaux précliniques Figures 4f, 5g et 5h

Les valeurs extraites des fichiers source Prism sont des pourcentages individuels de changement de volume tumoral: KP-4 avec amivantamab, HPAF-II parental et HPAF-II résistant avec double inhibition RAS(ON). Une valeur plus négative signifie une régression plus grande:

- Fig. 4f KP-4: Control (n=9): médiane 1205.8%, moyenne 1225.4%, régression <0: 0%, régression ≥30%: 0%.
- Fig. 4f KP-4: RMC-6236 25 mg/kg qd (n=9): médiane 39.8%, moyenne 27.4%, régression <0: 33%, régression ≥30%: 33%.
- Fig. 4f KP-4: Amivantamab 10 mg/kg ip biw (n=9): médiane 1192.8%, moyenne 1172.6%, régression <0: 0%, régression ≥30%: 0%.
- Fig. 4f KP-4: Combination  (n=9): médiane -62.6%, moyenne -61.2%, régression <0: 100%, régression ≥30%: 100%.
- Fig. 5g parental HPAF-II: Control (n=3): médiane 830.4%, moyenne 823.9%, régression <0: 0%, régression ≥30%: 0%.
- Fig. 5g parental HPAF-II: Zoldonrasib 100 mg/kg po qd (n=6): médiane -50.4%, moyenne -47.8%, régression <0: 100%, régression ≥30%: 67%.
- Fig. 5g parental HPAF-II: Daraxonrasib 25 mg/kg po qd (n=7): médiane -38.7%, moyenne -37.4%, régression <0: 100%, régression ≥30%: 86%.
- Fig. 5g parental HPAF-II: Daraxonrasib 10 mg/kg po qd + Zoldonrasib 100 mg/kg po qd (n=7): médiane -57.9%, moyenne -60.0%, régression <0: 100%, régression ≥30%: 100%.
- Fig. 5h résistant HPAF-II: Control (n=9): médiane 737.9%, moyenne 736.8%, régression <0: 0%, régression ≥30%: 0%.
- Fig. 5h résistant HPAF-II: Daraxonrasib 25 mg/kg po qd D24 (n=9): médiane 205.5%, moyenne 198.1%, régression <0: 0%, régression ≥30%: 0%.
- Fig. 5h résistant HPAF-II: Zoldonrasib 100 mg/kg po qd D24 (n=9): médiane 362.8%, moyenne 348.7%, régression <0: 0%, régression ≥30%: 0%.
- Fig. 5h résistant HPAF-II: Daraxonrasib 10 mg/kg po qd + Zoldonrasib 100 mg/kg po qd (n=8): médiane -7.5%, moyenne 1.6%, régression <0: 62%, régression ≥30%: 0%.

Comparaisons exploratoires de médianes à ce point final:
- Fig4f KP-4, daraxonrasib + amivantamab: Combination  vs Amivantamab 10 mg/kg ip biw: Δ médian -1255.4 points (IC bootstrap 95% -1939.3 à -702.6); p exact Mann–Whitney 4.114e-05; q BH dans le modèle 8.227e-05.
- Fig4f KP-4, daraxonrasib + amivantamab: Combination  vs RMC-6236 25 mg/kg qd: Δ médian -102.4 points (IC bootstrap 95% -150.8 à -12.5); p exact Mann–Whitney 0.007775; q BH dans le modèle 0.007775.
- Fig5g parental HPAF-II, RAS(ON) doublet: Daraxonrasib 10 mg/kg po qd + Zoldonrasib 100 mg/kg po qd vs Daraxonrasib 25 mg/kg po qd: Δ médian -19.2 points (IC bootstrap 95% -36.2 à -11.5); p exact Mann–Whitney 0.001166; q BH dans le modèle 0.002331.
- Fig5g parental HPAF-II, RAS(ON) doublet: Daraxonrasib 10 mg/kg po qd + Zoldonrasib 100 mg/kg po qd vs Zoldonrasib 100 mg/kg po qd: Δ médian -7.5 points (IC bootstrap 95% -32.3 à 8.2); p exact Mann–Whitney 0.1807; q BH dans le modèle 0.1807.
- Fig5h resistant HPAF-II, RAS(ON) doublet: Daraxonrasib 10 mg/kg po qd + Zoldonrasib 100 mg/kg po qd vs Daraxonrasib 25 mg/kg po qd D24: Δ médian -212.9 points (IC bootstrap 95% -262.2 à -116.9); p exact Mann–Whitney 8.227e-05; q BH dans le modèle 8.227e-05.
- Fig5h resistant HPAF-II, RAS(ON) doublet: Daraxonrasib 10 mg/kg po qd + Zoldonrasib 100 mg/kg po qd vs Zoldonrasib 100 mg/kg po qd D24: Δ médian -370.3 points (IC bootstrap 95% -495.7 à -176.2); p exact Mann–Whitney 8.227e-05; q BH dans le modèle 8.227e-05.

Ces tests sur les points finaux ne reproduisent pas l'ANOVA à mesures répétées des auteurs. Il s'agit des mêmes animaux et expériences que la publication; ce n'est pas une validation indépendante. Le fichier Fig. 5h contient 8 valeurs non manquantes pour le bras combiné malgré n=9 dans la légende. Ce manque est conservé comme limite de complétude de la source. Les petits effectifs, le modèle choisi et le biais de publication limitent toute extrapolation à des personnes.

## Durée avant progression dans le modèle KPC/Y (Figure 5d)

Le fichier source Prism contient les temps individuels jusqu'au doublement tumoral et les indicateurs de progression/censure des trois modèles. J'ai recalculé les courbes Kaplan–Meier, les médianes si atteintes, la moyenne de survie restreinte (RMST) jusqu'au dernier suivi commun et un test log-rank bilatéral contre chaque monothérapie. Le statut 1 est interprété comme progression et 0 comme censure, conformément au format de la table de survie GraphPad et à la définition PFS de l'article.

- RMC-6236 25 mg/kg: n=27, événements=19, censures=8, médiane KM=32.0 jours, RMST jusqu’à 42 j=32.32 jours.
- RMC-9805 100 mg/kg: n=27, événements=25, censures=2, médiane KM=28.0 jours, RMST jusqu’à 42 j=29.00 jours.
- RMC-9805 100 mg/kg + RMC-6236 25 mg/kg: n=27, événements=5, censures=22, médiane KM=non atteinte jours, RMST jusqu’à 42 j=41.44 jours.
- Vehicle: n=27, événements=27, censures=0, médiane KM=7.0 jours, RMST jusqu’à 42 j=7.22 jours.

Test log-rank omnibus recalculé sur les quatre bras: chi2(3)=169.713, p=1.468e-36. Comparaisons à deux groupes:
- RMC-6236 25 mg/kg vs RMC-9805 100 mg/kg: n=27/27, événements=19/25, log-rank chi2(1)=3.957, p=0.046684, q BH sur les trois comparaisons=0.046684.
- RMC-9805 100 mg/kg + RMC-6236 25 mg/kg vs RMC-6236 25 mg/kg: n=27/27, événements=5/19, log-rank chi2(1)=19.621, p=9.4444e-06, q BH sur les trois comparaisons=1.4167e-05.
- RMC-9805 100 mg/kg + RMC-6236 25 mg/kg vs RMC-9805 100 mg/kg: n=27/27, événements=5/25, log-rank chi2(1)=43.100, p=5.2002e-11, q BH sur les trois comparaisons=1.56e-10.

Le recalcul retrouve p≈0,046684 pour les deux monothérapies et p<0,0001 pour chacune des comparaisons doublet/monothérapie, cohérent avec les analyses Prism embarquées et la légende de la figure. Ce contrôle de cohérence vérifie l'extraction/calcul, pas une réplication indépendante. Le test groupé n'inclut pas de stratification par modèle.

## Usage honnête du pipeline universel ici

1. Des colonnes pertinentes comme TP53 prétraitement, variant KRAS, dose, altérations acquises, VAF pré/on/fin, modèle préclinique, traitement et volume tumoral peuvent être traitées comme flux liés et documentés; chaque flux doit garder son unité d'observation et son rôle causal supposé.
2. Le contrôle de sélection important est le patient ou l'animal. Les trois prélèvements d'une personne ne peuvent pas être concaténés et considérés comme trois personnes indépendantes. Les données ctDNA disponibles sont 44 personnes sélectionnées, pas un axe libre de 132 observations.
3. Pas de T0/TLog calculé sur cette table: le protocole courant exige n≥50; en outre, l'axe par personne est longitudinal/irrégulier, et l'inclusion est conditionnée à la progression. Le bon travail sur le pipeline est un mode longitudinal avec permutations par blocs (au niveau patient/animal), critères d'abstention et correction multiple définie avant de lire les résultats.
4. Le criblage PRISM de l'audit précédent a comparé 6 790 flux médicamenteux à 13 contrôles de dépendance sur au plus 38 modèles PDAC. Aucun résultat ne franchissait la correction globale des comparaisons. Le signal KRAS–AS-77 avait q=0,0413 dans la famille KRAS mais q=0,246 après correction sur les 13 contrôles; AS-77 n'est donc pas une piste validée. Le daraxonrasib n'était pas dans PRISM 24Q2: ce criblage ne valide aucune des combinaisons de l'étude récente.
5. « Tous les contrôles » ne signifie pas traiter chaque champ numérique comme un axe scientifique équivalent. L'identifiant patient/animal est une unité de regroupement, le bras de traitement est catégoriel, le temps est longitudinal, et les mesures biologiques ont des unités et des limites de détection. Le futur mode multi-contrôles doit conserver ces types, le lien entre flux et contrôle, ainsi que les blocs patient/animal, sans ordonner artificiellement des cellules ou des lignées.

## Décisions de recherche recommandées

1. Valider une cohorte externe avec prélèvements prétraitement, tôt sous traitement, progression et groupe sans progression, en corrigeant les limites de détection/shedding et en préenregistrant les définitions d'événements.
2. Prioriser des combinaisons par biomarqueur, pas de façon universelle: HER2 élevé/induit pour T-DXd; activité EGFR/MET pour amivantamab; amplification KRAS/flux RAS élevé pour intensifier blocage RAS; TP53 altéré et stress réplicatif pour DDR. Les associations sont déjà des hypothèses publiées à vérifier, et les profils bénéfice/risque diffèrent.
3. Refaire les essais de combinaison en matrices de dose dans des organoïdes humains indépendants, avec bras véhicule/mono/combo, réplicats biologiques, critères Bliss/Loewe/HSA prédéfinis, mesures de viabilité/apoptose et toxicité sur cellules non tumorales.
4. Actualiser le criblage cellulaire et génétique avec des données DepMap/PRISM versionnées et annotées. Le précédent écran PRISM était 24Q2; il ne comprend pas daraxonrasib.
5. Suivre les résultats de RASolute 309 et préparer une validation externe par biomarqueur. Le projet ne doit pas présenter la double inhibition comme traitement établi avant que l'essai rapporte ses résultats.

## Fichiers générés

- reanalyze_daraxonrasib_source_data.py: extraction/calculs reproductibles; aucune dépendance installée.
- clinical_replication_metrics.csv, clinical_replication_tests.csv: comptes et Fisher.
- clinical_high_dose_44.csv, clinical_lower_dose_13.csv et autres CSV: suppléments extraits.
- prism_waterfall_animals.csv, prism_waterfall_summary.csv: mesures individuelles/descriptives extraites des feuilles source « Waterfall » Figures 4 et 5; cellules exclues par GraphPad conservées mais non utilisées pour les résumés.
- preclinical_combo_endpoint_comparisons.csv: comparaisons exploratoires pour Fig. 4f et Fig. 5g/h.
- fig5d_mouse_time_to_doubling.csv, fig5d_KM_summary.csv, fig5d_logrank_combo_vs_monos.csv, fig5d_logrank_omnibus.csv, figure5d_pfs_km.png: réanalyse de temps-événement et graphiques.
- manifest.json: empreintes SHA-256 et sources.

## Reproduction

Depuis PowerShell, lancer le script avec l'interpréteur de l'environnement .venv du projet. Le code n'installe pas de paquet et conserve les suppléments téléchargés à côté de lui.

## Limites

- Phase 1/2 simple bras; échantillonnage ctDNA conditionné par shedding et progression; aucune combinaison testée chez l'humain par cet article.
- Environ 40% des personnes de l'analyse n'ont pas de mécanisme génomique de résistance identifié.
- Les données précliniques proviennent d'expériences publiées, pas d'un laboratoire indépendant.
- Une réponse animale ou une association statistique n'est pas un remède ni une preuve d'efficacité clinique.

## Journal de correction

La première extraction locale (v1, générée le 2026-11-17 à 00:23 UTC) a interprété incorrectement le format GraphPad imbriqué des fichiers Fig. 5 comme une matrice plate: elle produisait n=1 par bras. Après inspection du format interne, la version actuelle suit les blocs de 7 sous-colonnes, les groupes réellement tracés et les cellules exclues par GraphPad. Les résumés Fig. 5 de v1 sont supersédés et ne doivent pas être cités. La Fig. 4f était au format de table plate; son extraction n'a pas changé.

Le manifeste exclut le PDF généré et son fichier .sha256 afin d'éviter un hachage circulaire (le PDF contient le manifeste et le .sha256 contient le hachage du PDF). Le PDF est vérifié indépendamment par son fichier .sha256.
