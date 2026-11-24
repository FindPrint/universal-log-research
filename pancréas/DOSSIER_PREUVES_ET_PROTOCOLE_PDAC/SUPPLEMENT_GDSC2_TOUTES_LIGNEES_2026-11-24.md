# Supplément au livre blanc — analyse GDSC2 toutes lignées

**Date :** 24 novembre 2026
**Documents auxquels ce supplement se rapporte :**

- `UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_INTEGRAL_V12.pdf`
- `DOSSIER_SCIENTIFIQUE_PREUVES_ET_PROTOCOLE_PDAC_TLOG.pdf`

Ce document compagnon intègre les résultats de l'extraction GDSC2 et de l'essai du modèle obtenus après la publication des PDF ci-dessus. Il ne modifie ni ne remplace les archives V12; il doit être joint à tout partage de ces versions.

## Resultats observes

Le fichier brut officiel GDSC2 (release du 24 juillet 2022) a ete traite pour les cinq medicaments cibles dans toutes les lignees. L'extracteur a retenu 7 327 scans controles, produit 179 515 puits normalises et 125 230 points dose-reponse, couvrant 968 lignees. Les scans ont tous passe les controles implementes. La normalisation par controles a ete verifiee independamment sur 21 puits de trois scans.

| Medicament | DRUG_ID | Combinaisons avec reference officielle | Combinaisons dont au moins un scan franchit 50 % |
|---|---:|---:|---:|
| Cisplatine | 1005 | 760 | 264 |
| Olaparib | 1017 | 967 | 122 |
| 5-Fluorouracile | 1073 | 968 | 274 |
| Paclitaxel | 1080 | 958 | 445 |
| Gemcitabine | 1190 | 960 | 664 |
| **Total** | | **4 613** | **1 769** |

La couverture brute recoupe 4 613 combinaisons lignée-medicament de la table ajustee officielle. Six combinaisons brutes sans reference ajustee ont ete exclues de la comparaison; aucune combinaison de reference n'etait sans donnees brutes correspondantes.

## Essai du modele officiel

Le paquet `gdscIC50` version 0.99.4 a ete utilise avec sa structure de modele. Les puits ont ete moyennes par lignee, medicament et dose, comme le fait la fonction officielle `groupNlmeData`. L'ajustement comprenait 56 332 moyennes dose-reponse pour les 4 613 combinaisons.

- `isLargeData=TRUE` : echec du controle de convergence, matrice de precision singuliere; ses coefficients ne sont pas interpretes.
- `isLargeData=FALSE` : convergence en 3 iterations, matrice de covariance approximative definie positive et aucun avertissement; 4 613 comparaisons ont ete produites.

Sur ces comparaisons descriptives, la correlation de Pearson entre les `LN_IC50` recalcules et les references officielles est de **0,953**. La difference signee moyenne (modele moins reference) est de **+1,201** en unite logarithmique naturelle, soit un facteur geometrique d'environ **3,32**. La difference absolue mediane est de **0,922**. L'accord n'est donc pas suffisant pour presenter la seule correlation comme une validation.

## Limites d'interpretation

La comparaison n'est pas independante : les valeurs de reference officielles proviennent des memes experiences GDSC2. Le modele ajuste ici ne couvre que cinq medicaments et ne reproduit pas l'analyse globale GDSC2.

Parmi les 17 555 courbes scan-medicament, 4 580 presentent des mesures de part et d'autre du seuil de viabilite de 50 %. Seulement 1 769 des 4 613 combinaisons lignée-medicament ont au moins un scan franchissant ce seuil; pour les 2 844 autres, aucune courbe observee ne le franchit dans la plage testee. La difference absolue mediane est de 0,223 log pour les combinaisons avec franchissement et de 1,652 log pour celles sans franchissement. Ces dernieres estimations dependent donc davantage de l'extrapolation.

Ces donnees sont des essais in vitro sur des lignees cellulaires. Les puits et scans ne sont pas automatiquement des replicats biologiques independants. Cette analyse n'evalue pas TLog, ne valide pas un biomarqueur clinique et ne permet pas de predire la reponse d'un patient ou un benefice therapeutique.

Le sous-ensemble PDAC precedent (AsPC-1, BxPC-3 et CAPAN-1) n'a pas passe les controles de convergence; aucun coefficient de ce sous-ensemble n'est retenu.

## Etat d'avancement et suite recommandee

Le projet dispose maintenant d'une extraction brute GDSC2 reproductible, d'un controle ponctuel de normalisation, d'une comparaison a la reference ajustee et d'un diagnostic explicite des limites. L'etape suivante est une evaluation de TLog predefinie sur les mesures dose-reponse observables, en separant les donnees avec et sans franchissement du seuil, en reservant les lignees de test avant tout reglage et en publiant les echecs et abstentions. Cela restera une evaluation in vitro; une validation clinique necessite une cohorte independante, un protocole preenregistre et une gouvernance clinique.

Les scripts, la provenance, les resultats detailles et le guide de reproduction sont dans le depot `FindPrint/universal-log-research`, branche `publication/pdac-pipeline-caveats`. Les CSV de donnees et de comparaison, ainsi que le fichier brut de 2,1 Go, restent hors du depot.

Pour les effectifs, les empreintes des sources, les commandes de reproduction et les diagnostics complets, voir `GDSC2_AUDIT_SOURCE_ET_PLAN_REANALYSE.md` et `PIPELINES_ET_CODE_SOURCE/LISEZMOI_PIPELINES_ET_REPRODUCTION.md`.
