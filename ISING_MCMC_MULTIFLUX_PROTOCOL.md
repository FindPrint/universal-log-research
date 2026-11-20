# Protocole exploratoire Ising MCMC multi-flux

## Objectif

Étudier comment la sortie du cœur v5.8 varie quand l'axe de contrôle ou l'ensemble des flux observés change, à partir de trajectoires MCMC réelles à température fixe. Cette expérience est exploratoire; elle ne redéfinit pas le protocole de validation TLog précédent.

## Simulation

- Ising carré 2D, conditions périodiques, `J=1`, champ externe `H=0`, mises à jour de Wolff.
- Tailles `L=16` et `L=32`; températures `T=2.0`, `Tc=2/ln(1+sqrt(2))`, et `T=2.5`.
- Trois chaînes indépendantes par couple `(L,T)`, 500 mises à jour de chauffe et 4 000 observations après chauffe par chaîne.
- Une observation correspond à une mise à jour de grappe Wolff, pas à un balayage Metropolis ni à une unité de temps physique.
- Les CSV bruts gardent toutes les observations; seule l'entrée du cœur v5.8 est décimée régulièrement à une observation sur 20 (200 lignes) pour limiter le coût de calcul de ses fenêtres chevauchantes.

## Colonnes observées

- Physiques : `Energy_per_spin`, `Magnetization`, `Abs_magnetization`, `M_squared`, `M_fourth`, `Nearest_neighbor_correlation` et `Cluster_fraction`.
- Contrôles négatifs : `Noise_axis` et `Noise_flux` indépendants; `Abs_magnetization_shuffled` conserve la distribution de l'aimantation absolue mais détruit son alignement temporel.
- `Temperature`, `L`, `Chain` et `Seed` sont des métadonnées; elles ne sont jamais injectées par erreur comme flux observés dans les analyses de trajectoire.

## Comparaisons par le cœur v5.8

- Pour les six cellules `(L,T)`, comparer le même jeu de cinq flux communs (`Abs_magnetization`, `M_squared`, `M_fourth`, `Cluster_fraction`, `Noise_flux`) sous contrôle `MC_Update` et sous un jeu « tous flux » plus large.
- À `Tc`, pour `L=16`, conserver les cinq flux communs et comparer les axes `MC_Update`, `Energy_per_spin`, `Magnetization`, `Nearest_neighbor_correlation`, `Noise_axis` et `Abs_magnetization_shuffled`. Pour `L=32`, comparer `MC_Update`, `Energy_per_spin` et `Noise_axis`.
- À `L=16,Tc`, comparer en plus des ensembles de flux emboîtés : cible seule, famille d'ordre (`|M|, M², M⁴`), observables physiques proches (`|M|, M², M⁴, Cluster_fraction`), jeu commun incluant le bruit, et tous les flux.
- Répéter l'analyse commune sur la deuxième chaîne au point critique pour les deux tailles afin de vérifier la sensibilité à la graine.
- Garder une fenêtre fixe de 40 lignes après décimation, le profil de 29 estimateurs, 24 positions de paysage (option explicitement ajoutée à v5.8; 120 reste le défaut) et désactiver l'optimisation Monte Carlo du seuil pour rendre les comparaisons reproductibles.

Les contrôles énergie, aimantation, grappe, mélange et bruit ne sont généralement pas monotones dans l'ordre MCMC. Le pipeline les trie pour former une coupe; leurs résultats sont des associations conditionnelles selon l'axe demandé, pas des relations causales ni du temps physique. La comparaison avec `MC_Update` sert à rendre cette dépendance visible.

## Diagnostics

- Vérifier les moments thermodynamiques (`Cv`, `chi_|m|`, Binder) des trajectoires contre les tableaux de taille finie déjà calculés.
- Mesurer les corrélations de rang des flux liés, des flux redondants, du flux bruit et du flux mélangé, ainsi que l'autocorrélation de `Energy_per_spin` et `Abs_magnetization`.
- Conserver, pour chaque run, l'axe choisi, les flux explicitement passés, la monotonie du contrôle, le statut d'axe, la fenêtre, le seuil pipeline et le vecteur géométrique/TLog.

Les contrôles négatifs sont petits et synthétiques; les résultats servent à diagnostiquer la sensibilité à la configuration CSV et au choix d'axe, pas à certifier un détecteur universel.
