# Résultats — calibration préliminaire T0 et composante walk-forward L7b

Date d’exécution : 2026-11-16  
Statut : résultat synthétique exploratoire; aucune modification du code v6

## Résumé d’exécution

- **Scan Cohen :** 19 200 appels à la fonction v6 `scan_critical_threshold`; 0 échec. Les seuils sont calibrés séparément selon N et la composition des flux, puis évalués sur des graines de validation distinctes.
- **Walk-forward L7b :** 4 800 appels à `adaptive_walk_forward_validation`; 0 échec; cinq folds par appel. Cela teste le composant `t0_std` seulement, pas le verdict L7b entier.
- L’axe de contrôle est un rang croissant fixe 0–100. Les données sont simulées, avec AR(1) de rho 0,6; les alternatives comprennent des marches et des sigmoïdes.

Les détails préspécifiés, le code, les données brutes par simulation et les empreintes sont dans ce dossier. L’erreur initiale d’export du CSV résumé après exécution des scans est consignée dans `scan_calibration_manifest.json`; les résultats bruts avaient été écrits et ont servi à reconstruire le résumé sans relancer les calculs.

## Résultat 1 — le maximum Cohen-d peut recevoir une règle d’abstention, mais la règle calibrée ici manque beaucoup de signaux

La règle exploratoire signale une alerte lorsque le score maximal observé dépasse le plus grand des quantiles 95 % de deux distributions nulles d’entraînement (AR(1) stationnaire et dérive linéaire). Cela ajuste empiriquement le seuil au fait que le meilleur résultat parmi plusieurs coupures est retenu. Le seuil est spécifique à N et au nombre/type de flux.

| Scénario en validation | Alertes | Réalisations | Taux | IC 95 % Wilson |
|---|---:|---:|---:|---:|
| AR(1) stationnaire, aucun événement | 11 | 2 400 | 0,46 % | 0,26–0,82 % |
| Dérive linéaire sans rupture | 102 | 2 400 | 4,25 % | 3,51–5,13 % |
| Marche, amplitude 0,5 écart-type | 106 | 2 400 | 4,42 % | 3,67–5,32 % |
| Marche, amplitude 1,0 écart-type | 851 | 2 400 | 35,46 % | 33,57–37,40 % |
| Sigmoïde, amplitude 0,5 écart-type | 58 | 2 400 | 2,42 % | 1,88–3,11 % |
| Sigmoïde, amplitude 1,0 écart-type | 637 | 2 400 | 26,54 % | 24,81–28,34 % |

**Interprétation bornée :** avec ces deux nuls et ces paramètres, le taux d’alerte moyen de dérive est proche de la cible de conception de 5 %. Il varie toutefois entre 2,5 % et 8 % selon la longueur et le mélange de flux (200 validations par groupe). Un signal de 0,5 écart-type est presque jamais distingué des nuls. Même à 1 écart-type, le pipeline n’alerte que dans environ un tiers des marches et un quart des sigmoïdes. Ce n’est donc pas encore un détecteur robuste.

La localisation du seuil est un problème distinct de la détection. Pour les marches d’amplitude 1,0, la proportion de tous les `T0` candidats à moins de 5 % de la vraie frontière passe en moyenne d’environ 9 % à N=76–150 à 31 % à N=300 et 65 % à N=600. Parmi les seules réalisations alertées, les proportions sont proches : 10 %, 11 %, 31 % et 70 %. Le résultat justifie de continuer à étudier l’incertitude de localisation; il ne justifie pas encore un `T0=None` de production.

Le mélange de flux a changé le résultat : à N=600, pour une marche de 1 écart-type, la puissance observée était 50,5 % avec la cible seule, 51,0 % avec deux flux liés et 30,5 % en ajoutant trois flux indépendants. Ces valeurs décrivent ces simulations; elles ne prouvent pas qu’un flux indépendant nuit toujours à une analyse réelle.

## Résultat 2 — le seuil actuel `t0_std <= 10` est très rarement atteint et ne distingue pas les scénarios testés

Le walk-forward exécuté est la fonction v6 exacte. Il réestime T0 sur cinq fenêtres glissantes et calcule l’écart-type des positions T0 sur le rang 0–100. Sur les 4 800 réalisations, le critère actuel passe dans 34 cas, soit **0,71 %**. Les médianes `t0_std` par groupe et par N sont toutes entre 23,36 et 29,36 points de rang, qu’il s’agisse de bruit, de dérive ou des transitions simulées. Les taux PASS varient de 0 à 2,5 %.

**Interprétation bornée :** avec ce réglage, le test de stabilité marque presque tous les scénarios `FAIL`, y compris les transitions réelles simulées et les nuls. Dans cette expérience il ne discrimine donc pas stabilité utile et instabilité sous nul. La normalisation `t0_std/N` diminue automatiquement avec N (médiane moyenne des groupes : 0,318 à N=76 contre 0,048 à N=600); ce redimensionnement introduirait une dépendance à N sans démontrer une meilleure prédiction de l’erreur de localisation.

**Décision :** ne pas changer le seuil 10 ni le remplacer par `t0_std/N` à partir de ces données. Il faut étudier la construction du diagnostic : T0 de chaque fold est une position relative réestimée dans sa fenêtre; sa dispersion n’est pas une métrique de localisation par rapport à la même frontière globale. La comparaison doit inclure erreur de localisation sur vérité connue, nuls et transitions, et les folds doivent conserver l’axe physique/global lorsqu’il est disponible.

## Limites et prochaine expérience

Ce benchmark teste le cœur Cohen scan et le composant walk-forward, pas tout UNIVERSAL_LOG. Il n’inclut pas la sélection d’axe Monte-Carlo dépendant des données, l’optimisation de fenêtres, les 29 estimateurs, TLog, Q1–Q6, F1/F2, ni le vote L7a. Les deux nulls ne couvrent pas tous les domaines, distributions, autocorrélations, points aberrants, tendances non linéaires ou contrôles multivariés. Les seuils 5 % et amplitudes sont des choix de protocole explicites, pas des constantes universelles.

Prochaine étape recommandée : comparer, sur le même ensemble de simulations et à graines gelées, le scan v6 à des méthodes de référence de détection de ruptures; puis ajouter des nulls non linéaires, hétéroscédastiques et des contrôles corrélés au flux. Pour L7b, d’abord changer l’évaluation pour mesurer une stabilité de localisation globale par fold, avant tout nouveau seuil. Aucune conclusion sur GSE141017 ou le cancer n’est tirée de ces simulations.
