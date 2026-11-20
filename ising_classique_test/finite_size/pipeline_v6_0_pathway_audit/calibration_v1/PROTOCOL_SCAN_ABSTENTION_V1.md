# Protocole — calibration préliminaire du scan et de l’abstention

Date : 2026-11-16  
Statut : préspécifié avant exécution; benchmark synthétique exploratoire  
Code testé : `scan_critical_threshold` de v6.0.0-CohenD, sans modifier le pipeline

## Question

Le maximum du score moyen `abs(Cohen's d)` du scan peut-il séparer une rupture simulée de deux classes sans rupture discrète, tout en tenant compte de la sélection du meilleur seuil?

## Configuration

- Contrôle fixe : rang monotone régulier de 0 à 100.
- Longueurs : N = 76, 150, 300, 600.
- Scan : mode `fast` (fenêtre 80, ramenée à N/2 si nécessaire; `min_grp=2`; Cohen-d); grille de seuils choisie par les bornes de loupe du code.
- Trois compositions de flux : cible seule; cible + deux flux liés; cible + deux flux liés + trois flux indépendants.
- Processus de base autocorrélé AR(1), rho=0,6, écart-type stationnaire unitaire.
- Nuls : AR(1) stationnaire; dérive linéaire totale d’amplitude 1 écart-type + AR(1), sans rupture discrète.
- Alternatives : marche de taille 0,5 ou 1,0 écart-type; transition sigmoïde de même amplitude et largeur 5 % de N.
- 200 réalisations indépendantes d’entraînement par classe nulle; 200 par classe nulle en validation; 200 par classe alternative/amplitude en validation.
- Graine principale : 20261116; les sous-graines sont déterminées par générateur séparé et enregistrées.

## Règle exploratoire d’abstention

Pour chaque longueur et composition de flux, le seuil du score est le maximum des quantiles empiriques 95 % des deux distributions nulles d’entraînement (AR(1) stationnaire et dérive). Une détection est signalée seulement si le maximum du scan d’une réalisation de validation dépasse strictement ce seuil. Sinon, `T0` reste rapporté comme position candidate et la sortie de détection serait « abstention ».

Le quantile 95 % est un objectif de conception choisi pour ce benchmark, pas un seuil scientifiquement établi ou universel. La validation utilise des graines disjointes de l’entraînement. Chaque réalisation réexécute le scan complet et son argmax; la sélection du meilleur seuil est ainsi incluse dans les distributions simulées. Ce protocole n’est pas un test de permutation, ne calibre que les processus nuls déclarés, et ne valide pas le chemin complet du pipeline (axe Monte-Carlo adaptatif, optimisation de fenêtre, estimateurs/TLog/Q/F/L7).

## Sorties

Le script produit les cas, maxima de Cohen-d, seuils calibrés, taux d’alerte/détection, intervalles binomiaux de Wilson, T0 candidat et erreur de localisation pour les alternatives. Aucun résultat simulé n’est une preuve biologique ou d’universalité.
