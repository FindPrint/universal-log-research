# Rapport — étude Ising MCMC multi-axes v5.9

## Cadre et traçabilité

- 180 trajectoires indépendantes, soit 1,440,000 observations brutes Wolff.
- 85/85 appels du plan principal et 20/20 rejeux appariés réussis.
- Chaque observation est une mise à jour de grappe Wolff; elle ne représente pas un pas de temps physique.
- Le fichier source v5.9 est inchangé. Le runtime expérimental est une copie dont la ligne de résolution paysage a été fixée à 24; différence et SHA-256 sont archivés dans `runtime/` et `protocol_and_provenance.json`.
- La métadonnée source annonce encore 120 positions alors que les fichiers de caractéristiques en ont 24. Les exports gardent la valeur source, le compte observé et un indicateur d’incohérence.

## Hypothèses et résultats mesurés

### H1 — cohérence des observables physiques

Sur 180 comparaisons cellule-métrique aux références archivées, 178 ont un écart standardisé combiné de valeur absolue ≤ 2; le maximum est 2.338. Le seuil 2 est présenté à titre descriptif seulement, sans verdict d’acceptation.
Les pics de susceptibilité sur la grille sont : L=16: T=2.40; L=32: T=2.34; L=48: T=2.30. C’est un maximum de grille espacée de 0,02, pas un ajustement continu. Voir la courbe de susceptibilité, chaleur spécifique et Binder ci-dessous.
À Tc, U4 vaut 0,6114, 0,6106 et 0,6081 pour L=16, 32 et 48; ces valeurs rapprochées suggèrent un croisement dans ce voisinage, sans ajustement ni extrapolation. Les moyennes et écarts entre chaînes figurent dans `post_analysis_summary.json`; 5 chaînes améliorent le contrôle de répétabilité sans fournir une calibration précise des incertitudes.

### H2 — effet de l’axe de contrôle

Les 15 contrastes d’axe donnent 12 labels `divergence`, 2 `saturation` et 1 `criticality`. Les contrôles par aimantation donnent `criticality` pour L=16 et `saturation` pour L=32,48, tandis que les quatre autres axes sont tous `divergence`. Le même état physique donne donc des sorties qui dépendent du contrôle choisi.
L’énergie et la corrélation de voisins sont exactement liées par la définition du modèle (`corr=-E/2`); elles ne constituent pas deux axes physiques indépendants. Le bruit et l’aimantation mélangée servent de contrôles négatifs et ne prouvent aucune causalité.

### H3 — composition des flux

Les moyennes de d_crit sur cinq chaînes sont : all_fluxes=3.415 ± 0.095; order_parameter_family=3.444 ± 0.137; physical_without_noise=3.415 ± 0.087; target_absM_only=2.866 ± 0.183. Le flux |m| seul donne une valeur plus faible que la famille redondante |m|, m², m⁴; ajouter les autres flux du lot complet déplace peu la moyenne par rapport aux flux physiques sans bruit dans ce test. Les 20 étiquettes restent `divergence`.
Dans la chaîne L=16,Tc, les corrélations de rang observées confirment les redondances : Spearman(E, corr voisins)=-1 et les paires |m|, m², m⁴ ont rho=1. Elles ne doivent pas être comptées comme preuves indépendantes.

### H4 — spécificité du label par rapport à Tc

Les 36 cellules de la grille thermique avec axe MC_Update et flux communs sont toutes étiquetées `divergence` (36/36). Le label actuel ne distingue donc pas Tc des températures voisines dans cette configuration. Les étiquettes dépendent aussi fortement de l’axe; elles ne sont pas validées ici comme détecteur universel de transition.

### H5 — comparaison appariée v5.8/v5.9

Sur les mêmes 20 CSV, les 580 paires de médianes brutes des 29 estimateurs sont présentes dans les deux versions et les 580 paires sont numériquement égales (écart maximal 0.0). Cela établit la non-régression des médianes brutes du cœur sur ces entrées. Cela ne rétablit pas les exports natifs `d_kind`/`T_log_by_d_kind`, absents de v5.9.

## Revue v5.9 : autres constats

- La revue de code confirme 29 noms d’estimateurs et le même AST pour le helper L7a comparé; la v5.9 ne conserve pas le registre de taxonomie v5.8.
- L’audit synthétique des helpers L7b montre que des T0 manquants deviennent `FAIL`, qu’un Delta de référence absent peut laisser le test mélangé à `PASS`, et qu’une comparaison de Delta signé peut mal classer un effet dont la magnitude est divisée par deux. Ce sont des cas synthétiques, non une validation prédictive.
- Les seuils L7b sont des seuils codés, non calibrés par cette expérience. L’intégration `run_full_unified_pipeline` en mode L7b `light/full` reste à tester.

## Figures et artefacts

- [Observables physiques multi-tailles](expanded_runs/observables_physiques_multi_tailles.png)
- [Sensibilité aux axes et aux flux](expanded_runs/sensibilite_axes_et_flux_v59.png)
- [Tableau des contrastes d’axe](expanded_runs/axis_contrast_at_Tc.csv)
- [Résumé des ablations](expanded_runs/flux_ablation_summary_L16_Tc.csv)
- [Résumé complet JSON](expanded_runs/post_analysis_summary.json)
- [Audit d’intégrité](TRACE_AUDIT.json) et [manifeste de l’étude](STUDY_MANIFEST.csv)
- [Journal des exécutions](expanded_runs/RUN_JOURNAL.jsonl) et [console d’exécution](expanded_runs/execution_console.log)

## Limites à garder en tête

- La grille de température est un pilote à pas 0,02, avec Tc analytique ajouté comme point supplémentaire; aucune interpolation critique n’est revendiquée.
- Cinq chaînes restent un petit échantillon. Les erreurs combinées comparent des campagnes finies différentes et doivent être lues comme diagnostic.
- L’autocorrélation de |m| donne un ESS médian d’environ 1248 sur 8 000 observations; pour l’énergie, l’ESS minimum est 82. Cela signale une dépendance temporelle non négligeable malgré les mises à jour Wolff.
- Les estimateurs géométriques/TLog ne sont pas des observables standard de l’Ising; leurs nombres décrivent le comportement du pipeline sous ces réglages.
- La cohérence sur ce système jouet ne démontre pas l’universalité sur d’autres domaines.
