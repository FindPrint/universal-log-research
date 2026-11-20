# Matrice d’alignement — 29 estimateurs et T_log

**Objet.** Distinguer ce que classe le code v5.3 de ce que nomme le document `TLog.txt`. Cette matrice est un état des lieux, pas un arbitrage définitif de la théorie.

La classification sémantique ajoutée en v5.8 est décrite dans [D_KIND_TAXONOMIE_V5_8.md](D_KIND_TAXONOMIE_V5_8.md); elle complète cette matrice sans remplacer les classes historiques.

Pour une explication sans prérequis, voir le [guide débutant Universal Log](GUIDE_DEBUTANT_UNIVERSAL_LOG.md). Dans la colonne « T_log direct », « Oui » signifie uniquement que la sortie est reliée à la couche géométrique du code; plusieurs méthodes sont des proxys, et leur comparabilité physique reste à vérifier par domaine.

Dans la colonne « T_log direct », **oui** signifie que le code v5.3 utilise l’estimateur comme sortie dimensionnelle dans la couche géométrique. **Non** ne signifie pas que la méthode est ignorée : elle reste disponible dans la couche relative des 29 signatures.

| Nom exact dans le code v5.3 | Classe du code | T_log direct | Mention / point à vérifier dans `TLog.txt` |
|---|---|:---:|---|
| Higuchi | Saturation | Oui | Nommé en classe 1 |
| DFA | Saturation | Oui | Nommé avec Hurst dans « DFA + Hurst » |
| Katz | Saturation | Oui | Nommé en classe 1 |
| Petrosian | Saturation | Oui | Nommé en classe 1 |
| Sevcik | Saturation | Oui | Nommé en classe 1 |
| BoxCounting | Saturation | Oui | Nommé en classe 1 |
| Hurst2mH | Saturation | Oui | Correspondance possible avec `d = 2 − H`, mais le nom exact manque |
| PermutationEntropy | Saturation | Non | Nommé en classe 1; le code l’exclut de la dimension T_log car c’est une entropie |
| CorrelationD2 | Criticité | Oui | Nommé comme dimension de corrélation D₂ |
| GrassbergerProcaccia | Criticité | Oui | Nommé en classe 2 |
| InformationD1 | Criticité | Oui | Nommé comme dimension d’information D₁ |
| VisibilityGraph | Criticité | Oui | Nommé en classe 2 |
| TwoNN | Criticité | Oui | Nommé en classe 2 |
| DANCo | Criticité | Oui | La théorie nomme DANCo; le code calcule une approximation allégée MLE + angles, pas l’algorithme KL DANCo complet |
| Fisher | Criticité | Oui | La théorie nomme la métrique d’information de Fisher; le code emploie une dimension effective par participation des valeurs propres de la covariance inverse |
| LevinaBickel | Divergence | Oui | Nommé en classe 3 |
| PCAIntrinsic | Divergence | Oui | PCA est en classe 3, mais aussi proposée comme ancre de transition dans la section « trois ancres »; le code transmet le ratio de participation, pas le compte de composantes à 95 % |
| LocalPCA | Divergence | Oui | Nommé en classe 3 |
| GraphDimension | Divergence | Oui | Nommé en classe 3 |
| PersistentHomology | Divergence | Oui | Nommé en classe 3; le code estime une pente de fusion des composantes H0, approximation dont la validité comme dimension `d` reste à tester |
| MFA | Divergence | Oui | Nommé en classe 3; le code fait k-means puis PCA locale à 95 % et garde le maximum, pas un modèle complet de mixture factor analysis |
| KolmogorovLZ | Divergence | Non | Nommé en classe 3; le code le garde comme complexité algorithmique, pas comme dimension T_log |
| SpectralBeta | Référence nulle | Non | Nommé en classe 4 comme pente spectrale |
| SpectralDimension | Référence nulle | Oui | La notion spectrale est évoquée, mais cet estimateur n’est pas nommé dans la liste des méthodes; le code utilise `d=(5-β)/2`, correspondance à valider selon le domaine |
| Hurst | Référence nulle | Non | Nommé en classe 4 et également dans « DFA + Hurst » de la classe 1 |
| SampleEn | Référence nulle | Non | Nommé en classe 4 |
| Lyapunov | Référence nulle | Non | Nommé en classe 4 |
| MultifractalDeltaAlpha | Référence nulle | Non | Nommé en classe 4 |
| SingularityFmax | Référence nulle | Non | Nommé en classe 4 |

## Résumé du code v5.3

- 29 estimateurs, répartis en quatre classes : 8 saturation, 7 criticité, 7 divergence et 7 référence nulle.
- 21 estimateurs contribuent directement à la couche géométrique de T_log : 7 saturation, 7 criticité, 6 divergence et SpectralDimension.
- Les 8 autres n’entrent pas directement dans T_log : PermutationEntropy, KolmogorovLZ, SpectralBeta, Hurst, SampleEn, Lyapunov, MultifractalDeltaAlpha et SingularityFmax. Elles restent incluses dans la couche relative, qui compare les 29 estimateurs.

## Décisions théoriques ouvertes

1. Confirmer si `Hurst` et `Hurst2mH` sont deux estimateurs différents dans la théorie; préciser la formule et le rôle de chacun.
2. Décider si PCAIntrinsic est une ancre de divergence, de criticité, ou si une règle explicite permet deux usages distincts.
3. Pour chaque estimateur marqué « T_log direct », documenter pourquoi sa sortie représente une dimension comparable à `d` et quelle incertitude l’accompagne.
4. Définir, selon la question étudiée, le type de `n` et la définition de `d`; le code ne doit pas remplacer ces choix sans les enregistrer.
5. Formaliser la triangulation des ancres, ou garder le résultat comme profil/vectoriel tant qu’une formule globale n’est pas justifiée.

## Principe de lecture

Cette liste est évolutive. Une nouvelle définition peut ajouter ou déplacer une méthode, à condition de versionner la taxonomie, de préserver les sorties par estimateur et d’indiquer comment le changement modifie T_log.
