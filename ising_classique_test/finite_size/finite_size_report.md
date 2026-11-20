# Ising 2D — étude de taille finie

## Protocole

Réseau carré périodique à champ nul, J=kB=1, mises à jour de Wolff. Tailles L=8, 12, 16, 24, 32, 48, 64; températures 1.90–2.65 par pas de 0.01. Chaque point (L,T) utilise 3 chaînes de 4,000 mesures après 500 mises à jour de thermalisation; blocs de 80. L’analyse bootstrap rééchantillonne les blocs 500 fois.

Tc exacte (limite infinie) = 2.26918531.

Les grandeurs sont Cv/N=L² Var(e)/T²; χabs/N=L²(<m²>−<|m|>²)/T; U4=1−<m⁴>/(3<m²>²). À H=0, χabs retire la contribution des basculements complets entre les états +M et −M. Les intervalles de pics et de croisements sont des IC bootstrap à 95 %.

## Pics observés

| L | Pic χabs : T [IC 95 %] | χabs max | Pic Cv : T [IC 95 %] | Cv max | U4 à Tc |
|---:|---:|---:|---:|---:|---:|
| 8 | 2.47 [2.47, 2.58] | 1.79 | 2.35 [2.30, 2.42] | 1.23 | 0.6143 |
| 12 | 2.44 [2.39, 2.47] | 3.69 | 2.39 [2.28, 2.39] | 1.41 | 0.6127 |
| 16 | 2.40 [2.37, 2.42] | 6.19 | 2.33 [2.28, 2.34] | 1.58 | 0.6135 |
| 24 | 2.36 [2.32, 2.37] | 12.50 | 2.30 [2.28, 2.35] | 1.83 | 0.6116 |
| 32 | 2.34 [2.33, 2.34] | 21.30 | 2.29 [2.26, 2.32] | 1.91 | 0.6116 |
| 48 | 2.32 [2.30, 2.32] | 42.63 | 2.27 [2.27, 2.29] | 2.24 | 0.6094 |
| 64 | 2.30 [2.30, 2.31] | 70.51 | 2.28 [2.27, 2.29] | 2.32 | 0.6099 |

Le pic de χabs descend de 2.47 à 2.30 lorsque L passe de 8 à 64; son amplitude augmente de 1.79 à 70.51. Le fit χabs,max∝L^(γ/ν) donne γ/ν=1.7673, IC bootstrap [1.7494, 1.7774], à comparer à 1,75.
À Tc, le fit <|m|>∝L^(−β/ν) donne β/ν=0.1280, IC [0.1221, 0.1333], contre 0,125 attendu.
Cv,max croît avec ln L; la pente ajustée est 0.5438, IC [0.4786, 0.5941]. C’est compatible avec la divergence logarithmique de Cv en 2D.

## Croisements de Binder

| Tailles | T croisement | IC bootstrap 95 % | U4 au croisement |
|---:|---:|---:|---:|
| 8/12 | 2.24812 | [2.24448, 2.28829] | 0.6204 |
| 12/16 | 2.27272 | [2.25491, 2.28358] | 0.6110 |
| 16/24 | 2.26545 | [2.25738, 2.27980] | 0.6153 |
| 24/32 | 2.26903 | [2.25680, 2.28110] | 0.6118 |
| 32/48 | 2.26341 | [2.25510, 2.27607] | 0.6179 |
| 48/64 | 2.26997 | [2.26373, 2.27603] | 0.6083 |

Le croisement L=48/64 est à 2.26997, IC [2.26373, 2.27603]; l’IC contient Tc. U4 à Tc pour L=48 et 64 vaut 0.6094 et 0.6099, près de la valeur universelle ≈0,6107.

À titre de comparaison, l’extrapolation linéaire simple des températures de pic de χabs en 1/L donne 2.28998, IC [2.25673, 2.29241]. Cette extrapolation est moins informative que les croisements de Binder sur cet intervalle de tailles.

## Interprétation

Les intervalles bootstrap des deux exposants contiennent les valeurs théoriques, la capacité calorifique augmente avec ln L, et le croisement des deux plus grandes tailles est compatible avec Tc. C’est un bon test de cohérence du simulateur. Les IC ne couvrent pas les corrections de taille finie ni un éventuel biais résiduel des blocs; les fits sur sept tailles restent des estimations, pas des valeurs de précision.

La simulation est un banc d’essai distinct; UNIVERSAL_LOG ne calcule pas lui-même ces observables FSS.

Fichiers : `finite_size_ising.py`, `finite_size_results.csv`, `finite_size_peaks.csv`, `binder_crossings.csv`, `finite_size_summary.json`, `finite_size_block_moments.npz`, `finite_size_ising.png`.

## Ajustement conjoint de Binder

### Modèles

Les 77 points de L=8–64 dans T=[2,22; 2,32] sont ajustés simultanément. La fonction d’échelle est un polynôme cubique en x=(T−Tc)L^(1/ν). Le modèle corrigé ajoute L^(−2)(c0+c1x); ω=2 est fixé. Les IC à 95 % proviennent de 500 rééchantillonnages des blocs Monte Carlo à chaque (L,T).

### Estimations

| Modèle | Tc [IC 95 %] | ν [IC 95 %] | U* [IC 95 %] | χ²/dof | AIC | BIC |
|---|---:|---:|---:|---:|---:|---:|
| Sans correction | 2.268227 [2.267203, 2.269191] | 1.0691 [1.0344, 1.1039] | 0.61287 [0.61213, 0.61371] | 0.818 | 70.06 | 84.12 |
| Correction L^-2 | 2.269369 [2.267922, 2.270955] | 1.0213 [0.9662, 1.0777] | 0.61116 [0.60947, 0.61285] | 0.736 | 66.81 | 85.56 |

Références : Tc=2.269185, ν=1; le cumulant universel attendu pour un carré périodique est environ 0,6107.

Le modèle corrigé ramène ν de 1.069 à 1.021 et donne un intervalle qui inclut ν=1; son estimation de Tc est 2.26937. L’ajout de la correction améliore AIC de 3.25, tandis que BIC favorise légèrement le modèle plus simple (ΔBIC corrigé−non corrigé = 1.44). Les critères donnent donc une préférence modeste, pas une décision nette.

Le résultat dépend du choix ω=2, du polynôme cubique et de la fenêtre d’ajustement. Les intervalles bootstrap couvrent le bruit d’échantillonnage; ils ne couvrent pas cette incertitude de modèle. À lire comme un test de cohérence avec le modèle 2D Ising, pas comme une mesure de précision de Tc ou ν.

Voir `binder_scaling_fit.py` pour reproduire les deux ajustements; `binder_joint_scaling_collapse.png` montre l’effondrement sans et avec correction.

