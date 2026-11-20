# Benchmarks du pipeline — Universal Log v5.3

Date: 2026-11-07  
Environnement: Windows, Python de `.venv`, exécution mono-worker.

## But

Vérifier les comportements qui influencent l'interprétation d'une analyse : choix du contrôle, sélection des flux de complexité, distinction entre cible et flux, et statut des étiquettes de régime. Ce sont des benchmarks fonctionnels reproductibles, pas encore une comparaison de performances entre versions.

## Contrôles automatisés

Commande depuis `<PROJECT_ROOT>` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ising_classique_test -p 'test_pipeline_semantics.py' -v
```

Résultat initial : 8 tests réussis; après les profils T_log, le bootstrap mobile et l’override explicite de fenêtre fixe, 18 tests réussissent.

- Les modes `single`, `multi` et `all` restent disponibles; `single` est le défaut.
- Si `Time` est absent, la sélection du contrôle se replie sur la première colonne numérique et enregistre la raison.
- La sélection explicite des flux conserve uniquement les colonnes demandées et rejette une colonne absente, non numérique, ou identique au contrôle.
- Les classes de régime sur paysages synthétiques portent le statut heuristique; elles ne sont jamais déclarées comme conclusions physiques. Les données insuffisantes donnent `indeterminate`.
- La validation harmonique est désactivée par défaut, conformément à la documentation du script.

## Intégration sur le balayage Ising

Commande exécutée :

```powershell
.\.venv\Scripts\python.exe .\UNIVERSAL_LOG_v5_3.py `
  --input .\ising_classique_test\ising_temperature_sweep.csv `
  --target Abs_magnetization `
  --fluxes Energy_per_spin,Magnetization `
  --mode fast --seed 42 --max-workers 1 `
  --output .\ising_classique_test\results_explicit_fluxes
```

`--control-mode` et l'option de validation harmonique ont été omis pour vérifier les défauts.

Résultat : code de sortie 0; 105 observations; contrôle utilisé `Temperature`; cible `Abs_magnetization`; flux de complexité enregistrés `Energy_per_spin` et `Magnetization`; validation harmonique désactivée. Le tableau `df_feat.csv` contient les estimateurs issus de ces deux flux. Le fichier `fluxes_raw.csv` est l'export complet des données source; il ne représente pas la liste des flux employés dans les estimateurs.

Le résumé de régime enregistre `criticality`, avec `regime_is_heuristic=true`, `regime_is_physical_call=false` et `regime_classification_method=dimension_threshold_heuristic`. Ce libellé est donc une classification interne par seuils, pas une estimation validée de l'exposant critique ni une mesure de Tc.

Les seuils de la cascade calculée sont des rangs empiriques du contrôle. Ils ne doivent pas être comparés à la température critique connue sans analyse dédiée de taille finie et propagation d’incertitude. Pour l’Ising 2D carré, une comparaison physique de Tc doit venir d’un ajustement dédié en taille finie et de sa propagation d’incertitude; ce test d’intégration ne réalise pas cet ajustement.

## Avertissements et limites

L'exécution complète s'est terminée malgré un avertissement `Mean of empty slice` et un avertissement de dépréciation Matplotlib. Ils n'ont pas interrompu l'analyse; le premier mérite un traitement ultérieur si des cellules vides sont attendues dans les diagnostics. Ce test vérifie le passage des paramètres et la traçabilité des sorties, pas la validité statistique du modèle Ising ni le temps de calcul comparé à une version antérieure.

## Artefacts

- Code principal : `UNIVERSAL_LOG_v5_3.py`
- Tests : `ising_classique_test/test_pipeline_semantics.py`
- Entrée Ising : `ising_classique_test/ising_temperature_sweep.csv`
- Sortie d'intégration : `ising_classique_test/results_explicit_fluxes/`




## Profils T_log multi-échelle

Le pipeline accepte désormais plusieurs échelles étiquetées dans une même exécution. Exemple CLI :

```powershell
.\.venv\Scripts\python.exe .\UNIVERSAL_LOG_v5_3.py --input .\ising_classique_test\ising_temperature_sweep.csv --target Abs_magnetization --fluxes Energy_per_spin,Magnetization --mode fast --max-workers 1 --output .\ising_classique_test\results_tlog_profiles --tlog-scale observations=105 --tlog-scale system_size=256
```

Chaque profil conserve séparément les valeurs par estimateur et par ancre. L’incertitude sur `d` et `T_log` est calculée par bootstrap mobile de blocs sur les positions de progression; la longueur de bloc (24 positions ici) est dérivée de la fenêtre d’analyse (21 observations sur 105, projetée sur 120 positions). L’échelle `n` est traitée comme fixe. Ces intervalles ne couvrent ni les biais des estimateurs, ni l’incertitude de cette longueur de bloc, ni les choix de modèle. Aucune tension globale n’est fabriquée tant que la règle de triangulation n’est pas formalisée. La valeur par défaut reste `row_count`. Les tests fonctionnels vérifient la validation des échelles, l’incertitude par blocs et la syntaxe CLI.

Essai CLI terminé avec `observations=105` et `system_size=256` sur le balayage Ising `L=16`. Les deux profils sont écrits dans `results_tlog_profiles/master_results.json`; chacun présente 20 estimateurs dimensionnels disponibles et quatre ancres. La réexécution avec incertitudes est dans `results_tlog_uncertainty_verified/master_results.json`. Pour Higuchi, la valeur `d=1.85565` est la même; `T_log` passe de `-9.97972` à `-11.890801` parce que seule l’échelle `n` change. Le rapport texte affiche aussi les deux profils. Exécution terminée avec le code de sortie 0.

Résultat de l’intégration avec propagation : 300 réplications; pour l’ancre saturation, `d=1.251936` avec IC bootstrap `[1.179179, 1.297685]`; pour `observations=105`, `T_log=-12.789381` avec IC `[-13.127989, -12.576468]`. La dispersion inter-estimateurs de cette ancre est affichée séparément (IQR `0.428195`), car elle n’est pas la même chose que son incertitude bootstrap. Sortie : `results_tlog_uncertainty_verified/master_results.json`.

## Sensibilité aux blocs et chaînes indépendantes

La longueur de bloc bootstrap a été variée de 6 à 48 positions sur le paysage de 120 positions. Les médianes `d` des ancres saturation et référence nulle sont relativement stables; celle de divergence a un intervalle dont la largeur passe de `0.5164` à `0.1066`, selon le bloc choisi. Il faut donc présenter cette incertitude comme sensible au réglage, sans choisir le bloc donnant l’intervalle le plus étroit. Rapport et figure : `ising_classique_test/finite_size/tlog_sensitivity_report.md` et `tlog_block_sensitivity.png`.

Le suivi contrôlé utilise les 50 blocs archivés pour former une moyenne à chacune des 76 températures, soit 76 points par chaîne. Les trois chaînes partagent la fenêtre fixe `w_size=12`, la même graine pipeline et aucune optimisation Monte Carlo de fenêtre. À `n=256` sites, les moyennes de `d` entre chaînes sont `1.1004` (saturation), `1.9592` (criticalité), `2.5282` (divergence) et `2.2314` (référence nulle); leurs écarts-types descriptifs entre trois chaînes sont respectivement `0.0079`, `0.0182`, `0.0117` et `0.0200`. La classe appelée criticalité ne converge donc pas nécessairement vers la référence 4. Ces sorties T_log restent des indicateurs internes et ne localisent pas `Tc`. Rapport détaillé : `ising_classique_test/finite_size/tlog_sensitivity_report.md`; données : `ising_classique_test/finite_size/tlog_chain_comparison_controlled/`.

Pour rendre ce protocole explicite, `run_pipeline` accepte maintenant `opt_cfg={"mode_overrides": {"w_size": ...}}`. L’override est validé, appliqué à une copie du mode et enregistré dans le résultat; les défauts du mode ne changent pas. Les tests sémantiques couvrent les valeurs valides et invalides.

## Transfert au modèle d’Ising quantique

Une chaîne transverse quantique `H/J=-ΣZZ-gΣX` à `T=0`, tailles `N=8,10,12`, a été résolue exactement et analysée avec une fenêtre 16 constante. La réponse transverse culmine à `g=0,90`, `0,93`, `0,95`; le gap de même parité est minimal à `0,92`, `0,95`, `0,97`, en direction de `g_c=1`. Le gap spectral brut a un quasi-doublet ordonné et ne doit pas servir seul à localiser `g_c`.

Le pipeline calcule 29 colonnes; 18 sorties dimensionnelles étaient finies pour ces courbes. L’ancre `criticality` est proche de `d=0,96`, pas de la référence 4; les profils `T_log` sont négatifs et ne localisent pas le point critique. Cela valide le passage des données quantiques dans le pipeline, mais ne démontre ni une détection de transition par `T_log` ni l’universalité du cadre. Protocole, limites, données et figure : `ising_quantique_test/RAPPORT_ISING_QUANTIQUE.md` et `ising_quantique_test/`.
