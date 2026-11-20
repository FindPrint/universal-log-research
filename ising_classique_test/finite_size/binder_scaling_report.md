# Ajustement conjoint du cumulant de Binder

## Modèles

Les 77 points de L=8–64 dans T=[2,22; 2,32] sont ajustés simultanément. La fonction d’échelle est un polynôme cubique en x=(T−Tc)L^(1/ν). Le modèle corrigé ajoute L^(−2)(c0+c1x); ω=2 est fixé. Les IC à 95 % proviennent de 500 rééchantillonnages des blocs Monte Carlo à chaque (L,T).

## Estimations

| Modèle | Tc [IC 95 %] | ν [IC 95 %] | U* [IC 95 %] | χ²/dof | AIC | BIC |
|---|---:|---:|---:|---:|---:|---:|
| Sans correction | 2.268227 [2.267203, 2.269191] | 1.0691 [1.0344, 1.1039] | 0.61287 [0.61213, 0.61371] | 0.818 | 70.06 | 84.12 |
| Correction L^-2 | 2.269369 [2.267922, 2.270955] | 1.0213 [0.9662, 1.0777] | 0.61116 [0.60947, 0.61285] | 0.736 | 66.81 | 85.56 |

Références : Tc=2.269185, ν=1; le cumulant universel attendu pour un carré périodique est environ 0,6107.

Le modèle corrigé ramène ν de 1.069 à 1.021 et donne un intervalle qui inclut ν=1; son estimation de Tc est 2.26937. L’ajout de la correction améliore AIC de 3.25, tandis que BIC favorise légèrement le modèle plus simple (ΔBIC corrigé−non corrigé = 1.44). Les critères donnent donc une préférence modeste, pas une décision nette.

Le résultat dépend du choix ω=2, du polynôme cubique et de la fenêtre d’ajustement. Les intervalles bootstrap couvrent le bruit d’échantillonnage; ils ne couvrent pas cette incertitude de modèle. À lire comme un test de cohérence avec le modèle 2D Ising, pas comme une mesure de précision de Tc ou ν.

Voir `binder_scaling_fit.py` pour reproduire les deux ajustements; `binder_joint_scaling_collapse.png` montre l’effondrement sans et avec correction.

