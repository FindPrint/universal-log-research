# Protocole V6.0 - profilage TLog autour de la transition d'Ising

**Version du protocole :** 1.0, 15 novembre 2026.  
**Date de gel :** avant le premier calcul des sorties v6.0 sur les courbes de ce jeu.  
**Nature :** adaptation de l'ancien protocole pilote TLog a la version Cohen-d v6.0; elle n'est pas une preregistration independante du projet.

## Question et hypothese

La couche TLog geometrique de `UNIVERSAL_LOG v6.0.0 (Cohen-d)` signale-t-elle, sans utiliser l'observable cible, les temperatures proches des pics physiques de susceptibilite de l'Ising 2D, et evite-t-elle de declencher sur des courbes lisses sans transition?

L'hypothese testee est une detection candidate si la mediane de classe `d` passe dans la bande [3.5, 4.5] autour de la transition. Une alerte dans cette bande n'est ni une detection validee ni une estimation d'exposant critique.

## Donnees et repere physique

- Source physique : `ising_classique_test/finite_size/finite_size_results.csv`, tailles L=8, 12, 16, 24, 32, 48, 64 et grille T=1.90 a 2.65 par pas de 0.01.
- Entree TLog : `E_per_spin` seulement; `Temperature` ordonne les points. Aucun flux de susceptibilite n'entre dans les estimateurs TLog.
- Repere cible : pic de susceptibilite connectee de |m| et intervalle bootstrap en blocs issus de `finite_size_peaks.csv`.
- L=8 reste descriptif, mais est retire du decompte de localisation parce que l'intervalle bootstrap du pic est censure par la limite de la grille. Les six tailles evaluables sont L=12, 16, 24, 32, 48 et 64.

## Calcul TLog, fixe avant l'analyse

- Version source exacte : `pancréas/Archive complète PDAC v6 — ZIP/universal_v6.0.0_cohen.py`, SHA-256 `bb8bbdba4eb1f8c55b49748274ae8fbfef8a43f6c1b890964f18ba77960c0773`.
- Pour chaque centre interieur, calculer les estimateurs par `apply_complexity` du code v6 avec le profil complet `all` et une fenetre de 31 ou 41 points. Le code normalise chaque fenetre locale selon ses propres regles avant les estimateurs.
- Garder exactement les quatre groupes declares par `DIMENSION_FOR_TLOG` dans ce fichier : `saturation`, `criticality`, `divergence` et `null_reference`. Aucune nouvelle attribution d'estimateur ou reclassification n'est permise.
- Dans chaque fenetre et chaque groupe, `d` est la mediane des estimateurs dimensionnels finis du groupe. Si le groupe n'a aucune sortie finie, la valeur reste manquante.
- Fixer `n` au nombre de lignes du CSV complet, soit `n=76`, comme le fait v6 lorsque `compute_holographic_tension_state(..., n_samples=len(df))` est appele. `n` reste 76 pour chaque fenetre locale de 31 ou 41 points. Calculer `T_log=(d-4)*ln(76)`. Ce choix suit l'implementation v6 et differe de l'ancien protocole v5.8, qui prenait `n=w`; les valeurs numeriques de TLog ne sont donc pas directement comparables entre ces deux versions. La bande candidate est exprimee sur `d` et reste la meme.
- Un candidat existe dans une courbe si, pour un groupe, au moins un centre a `|d-4| <= 0.5`. Le centre predit est celui qui minimise `|d-4|`, sans acces au repere physique.
- Un candidat est localise si son centre tombe dans l'intervalle bootstrap du pic de susceptibilite, elargi de 0.01 en temperature de chaque cote. La couverture d'un groupe est la proportion de centres interieurs avec `d` fini.

## Controles negatifs sans transition

Reutiliser exactement la construction fixee par `TLOG_TRANSITION_VALIDATION_PROTOCOL.md` : courbes quadratiques lisses ajustees aux energies observees, bruit gaussien independant tire avec les erreurs-types ponctuelles des tailles de reference L=16 et L=64, 10 repetitions par taille, neuf centres par fenetre, fenetres 31 et 41. La graine des controles nuls est 20261108. Il y a 40 balayages nuls au total. Une fausse alerte familiale survient si au moins un des quatre groupes atteint la bande candidate dans une des fenetres echantillonnees.

## Criteres de criblage, inchanges

Un groupe est un **candidat pilote** seulement s'il satisfait simultanement :

1. couverture d'au moins 80 % des centres pour chaque fenetre;
2. localisation dans l'intervalle physique sur au moins 4 des 6 tailles evaluables, pour chacune des deux fenetres;
3. taux familial de fausses alertes au plus 10 % parmi les 40 balayages nuls;
4. derive mediane de temperature predite entre fenetres au plus 0.05 sur les tailles detectees.

Le seuil `|d-4| <= 0.5`, le padding de localisation et le seuil nul de 10 % sont des choix de criblage, pas des constantes deduites de la theorie. Avec 40 nuls, le taux familial reste une estimation pilote grossiere.

## Limites et provenance

Cette adaptation evalue le code v6.0 et sa taxonomie geometrique a quatre classes; le resultat precedent v5.8 groupe les estimateurs par 13 `d_kind`. Ces regroupements ne sont pas interchangeables. Ce protocole n'utilise pas de series temporelles de trajectoire, ne teste pas d'autres domaines et ne valide pas l'universalite de TLog. L'intervalle du repere physique est propage, mais l'incertitude et les biais des estimateurs dimensionnels locaux ne sont pas propages. Le benchmark ne compare pas la sortie de classe a une prediction apprise; il applique le critere descriptif ci-dessus.

Empreintes d'entree au gel :

- `finite_size_results.csv`: SHA-256 `6749b0fb12ebbcf10ac784fa9b4514fba5dd37e96057451fb0694e1290da196e`.
- `finite_size_peaks.csv`: SHA-256 `740b4c509f0b6f7df5673553c2191e1de35bea0afe74b2d7634101af82b4b4fa`.
- Protocole historique repris : `TLOG_TRANSITION_VALIDATION_PROTOCOL.md`, SHA-256 `c46f42ae405406d5dac80dadc396ce50202d4f009f9a0d19384bd454ea68dc09`.
