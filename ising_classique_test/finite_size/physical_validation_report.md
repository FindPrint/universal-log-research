# Validation physique Ising — contrôle par chaîne

## Protocole et référence

La réanalyse porte sur le simulateur FSS séparé de `UNIVERSAL_LOG` : réseau carré 2D, conditions périodiques, champ nul, `J = k_B = 1`, mises à jour de Wolff, tailles `L = 8, 12, 16, 24, 32, 48, 64`. Les moments sauvegardés couvrent 76 températures et ont la forme `(7, 76, 150, 6)`. Selon les métadonnées, les 150 blocs par cellule proviennent de trois chaînes indépendantes, avec 50 blocs de 80 mises à jour de cluster par chaîne.

La référence exacte en limite thermodynamique est `Tc = 2 / ln(1 + sqrt(2)) = 2.269185314...` pour le modèle carré isotrope. Elle découle de la condition critique d’Onsager pour le réseau carré à champ nul ([Onsager, *Physical Review* 65, 117 (1944)](https://journals.aps.org/pr/abstract/10.1103/PhysRev.65.117)).

## Contrôle de reproduction

Le nouveau script recalcule `Cv`, la susceptibilité connectée à `|m|`, le cumulant `U4` et `|m|` depuis les moments de blocs, sur toutes les 532 cellules `(L,T)`. L’écart absolu maximal par rapport à `finite_size_results.csv` est inférieur à `7.2e-15` pour les quatre observables. Le CSV et l’archive de moments sont donc cohérents à la précision numérique.

## Résultats de taille finie

- Le croisement `U4(L=48)` / `U4(L=64)` est `Tc = 2.26997`; le bootstrap hiérarchique par chaîne puis par blocs donne `2.26320–2.27731` à 95 %, ce qui contient la référence exacte.
- L’ajustement Binder avec correction `L^-2` donne `Tc = 2.26937` et `nu = 1.021`. Avec bootstrap hiérarchique, les intervalles 95 % sont `[2.26773, 2.27102]` pour `Tc` et `[0.945, 1.096]` pour `nu`; ils contiennent les références.
- Sans correction, l’ajustement donne `Tc = 2.26823`, `nu = 1.069`, avec intervalle hiérarchique de `nu` `[1.025, 1.116]`. La correction rapproche `nu` de 1, mais le choix du terme `L^-2`, de la fenêtre thermique et du polynôme reste une hypothèse de modèle. Les critères AIC/BIC de l’analyse précédente ne départagent pas nettement ces modèles.
- Les intervalles du croisement `48/64` restent proches avec trois schémas : blocs mélangés, blocs rééchantillonnés dans chaque chaîne, et bootstrap hiérarchique chaîne/bloc. Pour le bootstrap hiérarchique, la demi-largeur 95 % est environ `0.0071`, contre `0.0064` pour le bootstrap groupé. L’incertitude augmente modestement quand la variation entre chaînes est prise en compte.

## Autocorrélation et limites

Les trajectoires complètes par mise à jour ne sont pas archivées. Le script estime donc l’autocorrélation uniquement sur 50 moyennes de blocs consécutives par chaîne, près de `Tc`; l’estimation maximale observée est `1.49 blocs` (énergie, `L=32`). Ce diagnostic ne révèle pas de forte dépendance entre blocs, mais 50 points par chaîne sont trop courts pour démontrer que `80` mises à jour par bloc suffisent partout. Il faut conserver les séries temporelles brutes dans une prochaine simulation pour choisir la longueur des blocs à partir d’une autocorrélation fiable.

Le bootstrap hiérarchique n’a que trois chaînes à rééchantillonner et reste lui-même une analyse de sensibilité, pas un intervalle universellement calibré. Les ajustements gardent fixes les erreurs ponctuelles et ne propagent pas l’incertitude de fenêtre, de forme de correction ou d’exposant de correction.

Enfin, `ising_temperature_sweep.csv`, utilisé pour le test d’intégration de `UNIVERSAL_LOG`, est un jeu distinct à `L=16`, avec 35 températures et seulement 3 répétitions de 30 mesures par température. Il vérifie le passage des paramètres et la production des sorties; il ne permet pas une estimation robuste de `Tc`. L’analyse FSS ci-dessus est le test physique pertinent, mais demeure indépendante de `UNIVERSAL_LOG`.

## Reproduction

```powershell
.\.venv\Scripts\python.exe .\ising_classique_test\chain_bootstrap_validation.py --replicates 300 --seed 20261109
```

Sorties : `chain_bootstrap_validation.json`, `chain_bootstrap_validation.csv` et `chain_bootstrap_validation.png` dans `finite_size/`.
