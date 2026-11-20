# Protocole — extension Ising MCMC multi-axes, multi-flux et v5.9

Ce protocole est écrit avant les nouveaux calculs. Les seuils internes de la v5.9 ne sont pas traités comme des critères scientifiques calibrés.

## Hypothèses à évaluer

**H1 — cohérence physique.** Les trajectoires MCMC aux mêmes `(L,T)` reproduisent raisonnablement les observables de l’étude finie précédente. Résultat rapporté : valeurs par chaîne, moyenne, dispersion et écarts à la référence; pas de décision binaire fondée sur un seuil ad hoc.

**H2 — dépendance à l’axe.** Avec les mêmes lignes et les mêmes flux observés, les sorties de géométrie/TLog peuvent varier selon l’axe de contrôle (ordre MCMC, énergie, aimantation, corrélation de voisins, axe aléatoire, aimantation mélangée). L’amplitude et la répétabilité de ces variations seront rapportées sans verdict « réussi/échoué » arbitraire.

**H3 — dépendance à la composition des flux.** Les flux redondants `|m|`, `m²`, `m⁴`, la grappe, l’énergie et le flux indépendant peuvent contribuer différemment à l’agrégation du pipeline. Les ablations seront répétées sur les cinq chaînes de `L=16,Tc`; médiane, étendue et valeurs par chaîne seront publiées.

**H4 — spécificité à Tc.** Les valeurs de la règle de régime/criticité du pipeline peuvent-elles distinguer les températures voisines de `Tc` des contrôles hors voisinage et des axes négatifs? L’expérience ne possède que 12 températures et trois tailles : un résultat reste exploratoire, sans déclaration de détecteur validé.

**H5 — non-régression de v5.9.** Sur 20 CSV déjà analysés par v5.8, avec les mêmes réglages et la même grille réduite explicitement, les 29 sorties et les quatre ancres `D_vector` de v5.9 sont comparées aux résultats archivés v5.8. Les écarts seront mesurés directement; « identique » ou « différent » sera décidé par égalité numérique documentée, non par appréciation visuelle.

## Choix de données et raisons

- **Tailles `L=16,32,48`** : 16 et 32 prolongent le test précédent; 48 apporte une taille plus grande déjà simulée dans l’étude finie.
- **Températures** : `2.24, 2.26, …, 2.44` par pas de `0.02`, plus la valeur analytique exacte `Tc=2/ln(1+sqrt(2))`. Cette grille inclut les croisements Binder précédemment observés près de `2.26–2.27` et les intervalles bootstrap des pics `chi_abs` déjà obtenus pour L16 (`2.37–2.42`), L32 (`2.33–2.34`) et L48 (`2.30–2.32`). Le pas `0.02` est un compromis exploratoire, pas une résolution de transition revendiquée.
- **Cinq chaînes indépendantes** par cellule `(L,T)` : augmente le nombre de répétitions par rapport aux trois précédentes; cinq chaînes restent trop peu pour une calibration précise d’incertitude.
- **Chauffe 1 000 et 8 000 mesures Wolff par chaîne** : la mesure est doublée par rapport au pilote MCMC précédent de 4 000 mises à jour; l’autocorrélation et les moyennes première/deuxième moitié seront publiées pour auditer l’adéquation de cette durée.
- Une mesure = une mise à jour de grappe Wolff. Ce compte n’est pas un temps physique.
- **Entrée pipeline** : trajectoire brute conservée; une ligne sur 20 alimente le cœur (400 points), fenêtre fixe de 40 lignes et 24 positions de paysage. La v5.8 garde son réglage explicite; la v5.9 est exécutée depuis une copie expérimentale dont seule la grille paysage est réduite de 120 à 24. Le défaut des deux fichiers source ne sera pas modifié.

## Colonnes et contrastes prévus

- Flux physiques liés : `Energy_per_spin`, `Magnetization`, `Abs_magnetization`, `M_squared`, `M_fourth`, `Nearest_neighbor_correlation`, `Cluster_fraction`.
- Contrôles sans lien ajouté : `Noise_axis` et `Noise_flux`, tirés indépendamment par chaîne.
- Contrôle de dépendance temporelle : `Abs_magnetization_shuffled`, qui garde les valeurs et détruit leur ordre.
- Contrôle principal commun de flux : `Abs_magnetization`, `M_squared`, `M_fourth`, `Cluster_fraction`, `Noise_flux`.
- Flux complets : les sept colonnes physiques et les trois contrôles (bruit d’axe, bruit de flux, aimantation mélangée).
- Le contrôle `Nearest_neighbor_correlation` est déterministement redondant avec l’énergie : `Nearest_neighbor_correlation=-Energy_per_spin/2` dans cette définition à champ nul. La comparaison est documentée comme redondance exacte, pas comme flux indépendant.

## Matrice d’exécution fixée avant calcul

- Cœur v5.9 : contrôle `MC_Update` + flux communs pour les 36 cellules `(3 tailles × 12 températures)` avec chaîne 0.
- À Tc : répéter le contrôle temporel/flux communs sur chaînes 1–4 pour les trois tailles (12 appels supplémentaires).
- À Tc et chaîne 0 : cinq axes alternatifs (`Energy_per_spin`, `Magnetization`, `Nearest_neighbor_correlation`, `Noise_axis`, `Abs_magnetization_shuffled`) pour chaque taille (15 appels).
- À Tc, chaîne 0 : jeu complet de flux pour L32 et L48 (2 appels; L16 est inclus dans les ablations ci-dessous).
- À L16,Tc, chacune des cinq chaînes : jeu complet commun, `Abs_magnetization` seul, famille `|m|,m²,m⁴`, flux physiques sans bruit, et jeu complet de dix flux. Les configurations communes des cinq chaînes sont déjà comptées; les quatre configurations non communes de chaîne 0 et ces quatre configurations sur les chaînes 1–4 sont exécutées (20 appels additionnels).
- Total prévu du cœur sur nouvelles trajectoires : **85 appels**.
- Comparaison de non-régression v5.9 : les **20 appels** des entrées précédentes, ajoutés séparément.

## Hypothèses vs résultats et garde-fous de lecture

- Toute valeur L7b est étiquetée « règle d’implémentation v5.9 non calibrée ici ».
- `d=4` est rapporté comme référence de la formule actuelle TLog; cela ne justifie pas 4 pour chaque estimateur ou domaine.
- Les valeurs de `d_kind` ajoutées aux sorties v5.9, si calculées, viennent explicitement du registre v5.8 comme couche d’analyse externe. Elles ne seront jamais présentées comme produites nativement par v5.9.
- Aucune causalité n’est inférée du tri des lignes par un contrôle non monotone.
- Résultats négatifs, échecs de calcul, colonnes invalides et divergence entre hypothèse et mesure restent dans le journal et les exports.
