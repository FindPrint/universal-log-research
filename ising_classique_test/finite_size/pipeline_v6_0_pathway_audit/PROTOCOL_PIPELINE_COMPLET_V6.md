# Audit comparatif des voies 1 et 2 - pipeline complet v6.0 sur Ising

**Gel local du plan :** 15 novembre 2026, avant tout appel v6.0 sur ces donnees.  
**Type de travail :** pilote exploratoire pre-sprecifie dans le projet, sans pretention de preregistration externe.  
**Code :** `pancréas/Archive complète PDAC v6 — ZIP/universal_v6.0.0_cohen.py`, Cohen-d; empreinte relevee au lancement dans le manifeste.

## Question

Dans un systeme de physique statistique ou les tailles, l'axe thermique et des observables de reference sont connus, comment les deux lectures de TLog et le pipeline complet repondent-ils quand on conserve les six questions Q1-Q6, le scan et son Monte-Carlo, la cascade des seuils, les derives F1/F2 avant/apres, les 29 estimateurs, la geometrie TLog, la triangulation, les controles d'axe, la coherence L7a et la robustesse L7b?

Le but est de mettre a l'epreuve la theorie operationnelle complete. Un resultat favorable d'un module ne valide pas a lui seul les autres.

## Sens des voies selon `TLog.txt`

- **Voie 1, loupe de surface :** lecture a estimateur unique par Higuchi. Elle sera comparee a la valeur `Higuchi` calculee par le pipeline sur exactement les memes CSV/flux/controles.
- **Voie 2, triangulation :** les trois ancres saturation, transition et divergence sont preservees separement; configuration principale fixee au trio v6 `Higuchi, InformationD1, LevinaBickel`. Les medians de classe, `d_sat/d_crit/d_div`, ecart divergence-saturation, `T_log` de classe, contrepoids spectral/null et Cohen-d sont aussi conserves. Aucune moyenne ne remplacera les ancres. Le preset `default` du code sera demande explicitement.
- Les six questions Q1-Q6, le seuil et le Monte-Carlo, les derivees F1/F2, les controles, les flux, L1-L7a/L7b font partie de l'objet d'audit; ils ne sont pas reduits a la formule `T_log`.

## Donnees et references physiques

- Fichier d'origine : `ising_classique_test/finite_size/finite_size_results.csv`, sept tailles L=8,12,16,24,32,48,64; temperatures 1.90 a 2.65, pas 0.01.
- Une analyse de pipeline utilise un seul L a la fois, lignes triees par temperature. Cela evite de melanger les tailles dans une fausse trajectoire unique.
- CSV physique principal : colonnes `Temperature`, `Energy_per_spin`, `abs_magnetization`, `chi_abs_per_spin`, `Cv_per_spin`, `Binder_U4`. Ces noms proviennent du fichier source. Toutes les colonnes numeriques sont donc visibles comme observables/flux selon les conventions du pipeline.
- Cible fixe pour les runs de comparaison : `Energy_per_spin`. L'energie est une observables continue; elle ne sert pas a construire le repere de validation.
- Repere d'evaluation tenu a part : pic de `chi_abs_per_spin` pour chaque L et croisements de Binder; `Tc=2.269185314213022` pour le modele infini. Aucune valeur du pic n'est passee comme cible au pipeline.
- L=8 reste descriptif pour le pic de susceptibilite car son intervalle est censure par le bord droit de la grille.

## Plan de runs

1. **Coupe principale par taille :** un run pipeline par L, controle `Temperature`, cible fixe `Energy_per_spin`, mode `fast`, graine 20261115, `control_mode=single`, `target_policy=fixed`, preset triangulation `default`, limite worker 1, L7b `light`. Conserver les reglages internes du mode et les diagnostics Monte-Carlo tels qu'implementes; les enregistrer exactement, y compris echecs/replis.
2. **Changement d'axe a L=16 :** meme cible fixe, meme jeu physique et meme graine, controls `Temperature`, `abs_magnetization`, `chi_abs_per_spin`, `Cv_per_spin`, `Binder_U4`, politique de cible fixe. Ce sont des observables reelles mais liees; les controles non monotones restent des coupes dependantes de l'axe et ne seront pas presentes comme temps.
3. **Interaction de flux a L=16, Temperature controle :** (a) ajouter un flux de bruit blanc gaussien independant, graine 20261116, ecart-type egal a un; (b) ajouter une copie affine exacte `Energy_redundant=2*Energy_per_spin+3`. Ces variantes sont controles diagnostiques synthetiques. Elles mesurent la sensibilite du pipeline au bruit independant et au double comptage; elles ne sont pas de nouvelles donnees physiques.
4. **Renversement d'ordre a L=16 :** repeter exactement le CSV physique de reference a l'envers (T decroissant), avec la meme graine, pour mesurer la sensibilite aux conventions d'ordre de lignes. Ce test est un controle d'orientation, pas un algorithme Reverse Monte Carlo.
5. **Sensibilite a la graine Monte-Carlo a L=16 :** repeter le CSV de reference avec graines 42 et 123, sans changer de parametre, pour comparer au run de graine 20261115.

Les runs sont seriellises. Chaque sortie inclut les logs bruts, CSV d'entree, fichiers du pipeline, hash d'entree/source, version et graine. Une erreur n'efface pas les runs precedents et est inscrite dans le journal.

## Mesures a conserver sans reduction

Pour chaque run et controle, extraire sans modifier le schema source :

1. statut, axe et monotonie, cible demandee/utilisee, politique de repli;
2. distribution et correlation des flux, selection/ordre des flux et resultats de complexite sur les 29 estimateurs;
3. scan du seuil, seuil choisi, source, optimum Monte-Carlo, diagnostics, graine, nombre d'iterations et intervalles/dispersion disponibles;
4. T-2, T-1, T0, T+1, T+2, puis F1/F2 et leurs fenetres, effectifs, signes, changements et deltas avant/apres;
5. Q1, Q2, Q3, Q4, Q5 et Q6, chaque carte de scores et top signatures; distinguer valeur zero d'une question non applicable/indisponible;
6. voie 1 Higuchi; voie 2 trio, trois ancres, classification des 29, gap d'ancre, contrepoids null, `T_log`, incertitude et Cohen-d; ne jamais fusionner des estimands distincts;
7. L1-L7a coherence et L7b robustesse, horizons/walk-forward, avertissements, sorties et diagnostics.

## Comparaisons physiques et regles de lecture

- Reporter T0 et les seuils en pourcentage **et** en valeur brute de controle si le pipeline les calcule; pour l'axe Temperature, comparer prudemment au pic physique et aux croisements. Ne pas reclamer une detection si le pipeline ne fournit qu'un rang sans localisation physique.
- Sur les 7 tailles, reporter erreur absolue `|T0-Tc|` et `|T0-T_peak_chi_abs(L)|`, seulement si la transformation seuil->controle est univoque et le run valide.
- Les predictions et diagnostics ne sont pas recalibres apres observation. Les non-localisations, configurations sans sorties finies, labels heuristiques et echecs sont conserves.
- Les comparaisons de controles et de flux a L=16 sont secondaires, car elles utilisent des observables correllees et des variantes de flux synthetiques. Aucune significativite n'est revendiquee par multiplicite de runs.
- Les sorties calculant une meme grandeur a partir de flux redondants ne sont pas des repliques independantes. Le flux affine teste justement cette ponderation.

## Monte-Carlo et « Reverse Monte Carlo »

La recherche dans le depot a retrouve l'optimisation harmonique guidee des parametres de seuil, les graines, les scenarios, les controles de permutation/melange et les validations Monte-Carlo; aucune fonction nommee **Reverse Monte Carlo** ou algorithme RMC n'a ete trouve dans la version v6.0 ou les documents identifies. Le protocole n'inventera donc pas une methode RMC. Le renversement explicite de l'ordre T et les permutations sont enregistres comme controles d'ordre/sensibilite, pas renommes RMC.

## Limites

Le modele Ising valide ici la simulation et fournit une reference connue; il ne valide pas la theorie universelle. Les observables viennent d'estimations Monte-Carlo physiques avec trois chaines; le pipeline recalcule des estimateurs non lineaires sur seulement 76 points par taille. Les echelles et fenetres du mode fast restent des choix de la version, pas des constantes physiques. Des observables Ising sont algebraiquement/dependamment liees. L'etude est un benchmark du comportement complet sous ces fichiers et ce protocole, pas une preuve generale.

## Presentation pour lecteurs novices

Le rapport separe une synthese en langage courant, un schema des voies 1/2, un diagramme « CSV -> controles/flux -> 29 estimateurs -> Q1-Q6/F1-F2/Monte-Carlo -> voies 1/2 -> decision », puis les resultats techniques bruts et les traces de reproduction. Toute phrase distingue **choix de protocole**, **observation**, **interpretation**, **limite**. Les couleurs ne portent jamais le verdict sans libelle textuel; axe, unite, taille L, n et graine restent visibles.
