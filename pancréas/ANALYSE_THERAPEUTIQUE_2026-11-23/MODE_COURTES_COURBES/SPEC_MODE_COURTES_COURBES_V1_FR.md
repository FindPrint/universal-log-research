# SPÉCIFICATION TECHNIQUE — MODE COURTES COURBES DOSE-RÉPONSE TLOG (v1.0.0)

**Date :** 23 novembre 2026  
**Auteur :** Antigravity / Swarm Worker `shortcurves`  
**Statut :** Spécification formelle & Implémentation validée  
**Localisation :** `C:\Users\citys\Desktop\10-31-2026\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-23\MODE_COURTES_COURBES\`  
**Module Python associé :** [UNIVERSAL_LOG_dose_response_v1.py](file:///C:/Users/citys/Desktop/10-31-2026/pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/MODE_COURTES_COURBES/UNIVERSAL_LOG_dose_response_v1.py)  

---

## 1. Contexte, Problématique et Architecture

### 1.1 Contexte des criblages thérapeutiques
Dans le cadre de l'analyse thérapeutique de modèles d'adénocarcinome canalaire pancréatique (PDAC), les criblages pharmacologiques modernes évaluent la sensibilité à des dizaines ou centaines de molécules thérapeutiques. Les jeux de données majeurs de référence présentent une résolution de concentration restreinte :
- **Yin et al. (Nature Communications 2025)** : 46 modèles d'organoïdes dérivés de patients (PDO) × 63 médicaments criblés, avec seulement **7 à 8 concentrations** par molécule.
- **GDSC2 (Genomics of Drug Sensitivity in Cancer)** : 7 à 9 concentrations par courbe avec IC50 de référence.
- **PRISM DepMap (Broad Institute)** : 8 concentrations par composé.

### 1.2 Le verrou du pipeline standard v6.0.1
Le pipeline central `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py` a été conçu pour l'analyse multi-échelles de séries temporelles dynamiques (physique statistique, dynamiques de repliement, séries climatiques, flux financiers). Il intègre un **garde-fou confirmatoire strict exigeant $N \ge 50$ observations** (`MIN_SERIES_LENGTH = 80`, `min_len = 50` en mode rapide).
Appliqué aux données de criblage d'organoïdes (comme Yin 2025), le pipeline v6.0.1 rejette l'intégralité des courbes (150/150 colonnes rejetées) en raison de cette contrainte de longueur.

### 1.3 Décision architecturale : Isolation stricte
> [!IMPORTANT]
> **Le seuil $N \ge 50$ du pipeline standard v6.0.1 NE DOIT JAMAIS être abaissé.**
> Abaisser ce seuil dans le pipeline général compromettrait la stabilité statistique des 29 estimateurs sur les séries temporelles et dénaturerait les analyses confirmatoires de physique/finance.
> La solution adoptée est la création d'un **module satellite dédié et autonome : `UNIVERSAL_LOG_dose_response_v1.py`**, spécialement calibré pour les courbes dose-réponse courtes ($N \in [7, 20]$).

---

## 2. Taxonomie des Estimateurs : Sélection et Rejets

Sur les 29 estimateurs de complexité d'Universal Log v6.0.1, la grande majorité est mathématiquement invalide ou massivement biaisée lorsque la série ne compte que 7 à 20 points.

### 2.1 Les 5 Estimateurs Retenus (Robustes sur séries courtes)

| Estimateur | Référence | Domaine mathématique | Condition de validité | Comportement sur dose-réponse |
| :--- | :--- | :--- | :--- | :--- |
| **Katz FD** | Katz (1988) | Dimension fractale géométrique | $N \ge 3$ | Mesure la compacité et la tortuosité globale du profil. $D \approx 1.0$ sur sigmoïde lisse ou profil plat ; $D$ augmente en présence de bruit ou d'oscillations. |
| **Petrosian FD** | Petrosian (1995) | Morphologie de la dérivée | $N \ge 4$ | Compte les inversions de signe de la dérivée première $\Delta Y$. $D = 1.0$ pour toute courbe strictement monotone (sigmoïde propre) ; $D > 1.0$ dès l'apparition d'oscillations ou de non-monotonie. |
| **Sevcik FD** | Sevcik (1998) | Topologie dans le carré unitaire | $N \ge 4$ | Longueur de corde normalisée dans $[0, 1]^2$. Très stable sur séries ultra-courtes ($N=7..10$). $D \approx 1.0$ sur profil plat ; $D \in [1.1, 1.25]$ sur sigmoïde active. |
| **SampleEntropy** | Richman & Moorman (2000) | Entropie régularisée ($m=1$) | $N \ge 5, \sigma > 0$ | Évalue la régularité des motifs. Sur $N \in [7, 20]$, l'ordre $m=1$ est utilisé pour éviter la dégénérescence des correspondances de templates. Abstention ($NaN$) si $\sigma < 10^{-12}$. |
| **DFA** | Peng et al. (1994) | Fluctuations sans tendance ($s \ge 3$) | $N \ge 9$ | Analyse en loi de puissance des fluctuations sur fenêtres $s \in [3, \lfloor N/2 \rfloor]$. Exige au minimum 3 échelles distinctes. Retourne honnêtement $NaN$ pour $N < 9$. |

### 2.2 Les 24 Estimateurs Rejetés (et Justifications Formelles)

| Famille v6.0.1 | Estimateurs Rejetés | Cause formelle du rejet sur $N \in [7, 20]$ |
| :--- | :--- | :--- |
| **Fractals classiques** | `Higuchi`, `Hurst`, `BoxCounting` | `Higuchi` exige $k_{max} \ge 3$ sous-échantillonné ($N \ge 16$). `Hurst (R/S)` impose $N/2 \ge 8$ ($N \ge 16$) avec un biais R/S massif sur très courts blocs. `BoxCounting` dégénère sous 16 points. |
| **Entropies & Information** | `PermutationEntropy`, `KolmogorovLZ`, `InformationD1` | Pour $m=3$, $3! = 6$ permutations possibles ; sur 8 points, l'histogramme des motifs est sous-échantillonné. `KolmogorovLZ` n'a aucun sens asymptotique sur 8 symboles. |
| **Espace de phase & Chaos** | `CorrelationD2`, `GrassbergerProcaccia`, `Lyapunov` | Le plongement de Takens de dimension $m \ge 2$ génère $\le 6$ vecteurs de phase. L'intégrale de corrélation et les trajectoires chaotiques ne convergent pas. |
| **Dimension Intrinsèque** | `TwoNN`, `DANCo`, `Fisher`, `LevinaBickel`, `PCAIntrinsic`, `LocalPCA` | Ces algorithmes exigent un voisinage $k$-NN dense ($k \ge 5..10$) et un nuage continu d'au moins 50 à 100 points. Sur 8 doses scalaires, la matrice de covariance est de rang insuffisant. |
| **Théorie des Graphes** | `VisibilityGraph`, `GraphDimension` | Le graphe de visibilité sur 8 nœuds est totalement dominé par les effets de bord discrets. |
| **Topologie & Fréquence** | `PersistentHomology`, `MFA`, `SpectralBeta`, `SpectralDimension`, `MultifractalDeltaAlpha`, `SingularityFmax`, `Hurst2mH` | La FFT sur 8 points ne fournit que 4 fréquences, interdisant toute régression spectrale $1/f^\beta$. L'homologie persistante produit des diagrammes triviaux. Le spectre multifractal est indéterminé. |

---

## 3. Garde-Fous Scientifiques et Règles d'Abstention

### 3.1 Règle d'Abstention Obligatoire (< 3 Estimateurs)
> [!CAUTION]
> **Règle absolue d'intégrité :**  
> Si le nombre d'estimateurs finis et valides parmi les 5 est strictement inférieur à 3 ($N_{finite} < 3$), le module conclut obligatoirement par le statut :
> $$\text{status} = \text{"INDÉTERMINÉ"}$$
> Aucun résultat n'est forcé. $T0_{dose}$, $IC50_{tlog}$ et $AUC_{tlog}$ sont positionnés à `NaN`, et `abstention = True` est consigné dans les métadonnées.

### 3.2 Unité de Rééchantillonnage : Réplicat Biologique Strict
- Dans les criblages pharmacologiques, les concentrations $c_1 < c_2 < \dots < c_N$ constituent un continuum physico-chimique ordonné.
- **Interdiction formelle :** Ne jamais permuter, shuffler ou rééchantillonner des concentrations individuelles isolées.
- **Unité d'analyse :** Le **réplicat biologique** (la courbe complète du modèle cellulaire). Le rééchantillonnage bootstrap s'effectue exclusivement en tirant avec remise des réplicats entiers parmi les $R$ répétitions biologiques, préservant l'autocorrélation et la monotonie intrinsèque.

---

## 4. Métriques de Sortie TLog Dose-Réponse

Le module extrait quatre paramètres fondamentaux pour caractériser l'effet pharmacologique :

```
Viabilité (Y)
1.0 +-------+==========================\  <- Plateau haut basal (Y_top)
    |       |                           \
    |       |<- T0_dose (Rupture)        \
    |       |                             \
0.5 + - - - + - - - - - - - - - - - - - - -\- - - <- IC50_tlog (Inflexion médiane)
    |       |                               \
    |       |                                \
0.0 +-------+---------------------------------+====\  <- Plateau bas (Y_bottom)
   c_min   T0                                IC50  c_max   Dose log10
    |<------------------- AUC_tlog (Aire sous courbe) ------------------>|
```

### 4.1 T0_dose (Point de Décrochage / Rupture de Régime)
- **Définition :** Analogue au seuil $T_0$ d'Universal Log temporel. Repère la concentration critique à laquelle la viabilité quitte le plateau de tolérance basal (perte $\ge 15\%$ de l'amplitude de réponse).
- **Unités :** Exprimé en concentration brute ($\mu\text{M}$ ou nM) et en pourcentage de progression sur l'intervalle logarithmique des doses ($T0_{\%}$).

### 4.2 IC50_tlog (Point d'Inflexion Médian TLog)
- **Définition :** Concentration médiane de transition où la viabilité atteint le point milieu entre le plateau basal supérieur et le plateau résiduel inférieur :
  $$Y_{mid} = \min(Y_{top}, Y_{bottom}) + 0.5 \cdot |Y_{top} - Y_{bottom}|$$
- **Estimation :** Interpolation linéaire robuste sur l'axe $\log_{10}(\text{dose})$. Ne dépend pas d'une hypothèse de distribution symétrique.

### 4.3 AUC_tlog (Aire Normalisée Sous la Courbe)
- **Formule :** Intégration trapézoïdale sur l'axe $\log_{10}(\text{doses})$ normalisée par l'étendue logarithmique totale :
  $$\text{AUC}_{tlog} = \frac{1}{\log_{10}(c_{max}) - \log_{10}(c_{min})} \int_{\log_{10}(c_{min})}^{\log_{10}(c_{max})} Y(c) \, d\log_{10}(c)$$
- **Intervalle de confiance :** Estimé par bootstrap non paramétrique (95% CI) sur les réplicats biologiques ($R \ge 2$).

### 4.4 Diagnostic de Régime TLog
- `CRITICALITY` : Transition sigmoïde nette, sensibilité pharmacologique active ($Y_{span} \ge 0.15$).
- `SATURATION` : Résistance complète ou composé inactif, viabilité stable ($Y_{span} < 0.12$).
- `PERTURBATION` : Réponse non monotone, présence d'hormésis, de rebond ou de bruit de criblage.
- `INDETERMINATE` : Série corrompue, hors plage $N \in [7, 20]$, ou $N_{finite} < 3$.

---

## 5. Comparaison avec l'Ajustement 4PL Conventionnel

Pour chaque profil, le module ajuste l'équation sigmoïde conventionnelle à 4 paramètres (Hill) :
$$Y(x) = \text{Bottom} + \frac{\text{Top} - \text{Bottom}}{1 + 10^{(x - \log_{10}(\text{IC50})) \cdot \text{Hill}}}$$

### 5.1 Diagnostics de Comparaison
- Statut de convergence 4PL (`fit_4pl_converged`).
- Coefficient de détermination $R^2_{4PL}$.
- Écart logarithmique absolu :
  $$\Delta \log_{10}(\text{IC50}) = |\log_{10}(\text{IC50}_{tlog}) - \log_{10}(\text{IC50}_{4PL})|$$

### 5.2 Avantages Comparatifs Déterminés
- **Sur courbes sigmoïdes nettes :** Excellente concordance mathématique ($\Delta < 0.15$ dex, $r > 0.97$).
- **Sur courbes plates (composés inactifs) :** Le modèle 4PL diverge ou heurte artificiellement les bornes d'optimisation ($R^2 = 0$, Hill $\to 0.1$ ou IC50 hors bornes). Le module TLog qualifie immédiatement et sans ambiguïté le régime en `SATURATION / RÉSISTANT_PLAT`, évitant les faux positifs d'IC50.
- **Sur profils non monotones (hormésis) :** Le 4PL force un lissage monotone qui masque la stimulation à faible dose. Le module TLog détecte la non-monotonie via Petrosian FD et Sevcik FD et classe la réponse en `PERTURBATION`.

---

## 6. Validation Expérimentale sur Données Synthétiques

Un banc d'essai de 18 conditions expérimentales indépendantes a été généré et exécuté avec 3 réplicats biologiques indépendants ($R=3$, $N=8$ ou 9 concentrations) :
- **10 Courbes Sigmoïdes :** Vrais IC50 échelonnés de $0.05\,\mu\text{M}$ à $14.0\,\mu\text{M}$, pentes Hill de 1.0 à 2.5, bruit biologique réaliste ($\sigma = 0.02 - 0.035$).
- **5 Courbes Plates :** Niveaux de viabilité 1.0, 0.95, 0.85, 0.50, et contrôle plat bruité ($\sigma = 0.06$).
- **3 Courbes Non-Monotones :** Hormésis (stimulation +25% puis chute), réponse biphasique avec rebond, et artéfact oscillant de criblage.

### 6.1 Résultats Métriques Synthétiques

| Groupe de Test | Nombre | Statut TLog Obtenu | Métriques Clés | Concordance 4PL |
| :--- | :---: | :--- | :--- | :--- |
| **Sigmoïdes** | 10 | 10/10 `VALIDE` | Corrélation $r(\text{TLog vs Vrai}) = \mathbf{0.9848}$ | Corrélation $r(\text{TLog vs 4PL}) = \mathbf{0.9759}$ |
| | | | Écart moyen $\Delta \log_{10} = \mathbf{0.1220}$ dex | Écart max $\Delta \log_{10} = 0.6338$ dex |
| **Plates** | 5 | 5/5 `RÉSISTANT_PLAT` | Régime `SATURATION` (100%) | 4PL non-convergent (0/5, $R^2 = 0.0$) |
| | | | $T0 = \text{NaN}$, $\text{IC50}_{tlog} = \text{NaN}$ | Pas de faux IC50 généré |
| **Non-Monotones** | 3 | 3/3 `NON_MONOTONE` | Régime `PERTURBATION` (100%) | Détection par Petrosian FD ($> 1.04$) |
| | | | Signalement formel d'inversions | et Sevcik FD ($> 1.20$) |
| **Garde-fou $N < 7$** | 1 | 1/1 `INDÉTERMINÉ` | Abstention obligatoire activée | $N=5 \implies$ Rejet immédiat propre |

### 6.2 Artefacts Produits lors de la Validation
- Données tabulaires complètes : [SYNTHETIC_TEST_RESULTS.csv](file:///C:/Users/citys/Desktop/10-31-2026/pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/MODE_COURTES_COURBES/SYNTHETIC_TEST_RESULTS.csv)
- Données structurées JSON : [SYNTHETIC_TEST_RESULTS.json](file:///C:/Users/citys/Desktop/10-31-2026/pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/MODE_COURTES_COURBES/SYNTHETIC_TEST_RESULTS.json)
- Graphique 9 panneaux de comparaison : [SYNTHETIC_TEST_CURVES.png](file:///C:/Users/citys/Desktop/10-31-2026/pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/MODE_COURTES_COURBES/SYNTHETIC_TEST_CURVES.png)
- Résumé machine validé : [VALIDATION_SUMMARY.json](file:///C:/Users/citys/Desktop/10-31-2026/pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/MODE_COURTES_COURBES/VALIDATION_SUMMARY.json)

---

## 7. Mode d'Emploi et Exemple d'Utilisation

### Exemple d'Appel Programmatique en Python :

```python
import numpy as np
from UNIVERSAL_LOG_dose_response_v1 import analyze_dose_response_curve

# Concentrations testées (ex. demi-logs en µM)
doses = [0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]

# 3 réplicats biologiques indépendants (matrice 3 x 8)
replicates = [
    [0.98, 0.99, 0.92, 0.74, 0.33, 0.12, 0.06, 0.05],
    [1.02, 0.97, 0.94, 0.71, 0.30, 0.09, 0.04, 0.06],
    [0.99, 1.01, 0.91, 0.76, 0.34, 0.10, 0.05, 0.04],
]

# Analyse
res = analyze_dose_response_curve(
    doses=doses,
    replicates=replicates,
    drug_name="Gemcitabine",
    cell_id="PDO_PAAD_01",
    n_bootstrap=100
)

print(f"Statut : {res.status}")
print(f"Régime : {res.regime_tlog}")
print(f"T0_dose : {res.t0_dose:.4f} µM ({res.t0_dose_pct:.1f}%)")
print(f"IC50_tlog : {res.ic50_tlog:.4f} µM")
print(f"IC50_4PL : {res.ic50_4pl:.4f} µM (R2 = {res.r2_4pl:.3f})")
print(f"AUC_tlog : {res.auc_tlog:.3f} [IC95%: {res.auc_tlog_ci_low:.3f} - {res.auc_tlog_ci_high:.3f}]")
```

---

## 8. Conclusion et Perspectives

Le mode courtes courbes dose-réponse (v1.0.0) apporte une réponse rigoureuse, mathématiquement fondée et protectrice pour le traitement des données de pharmacotypage (Yin 2025, GDSC2, PRISM) :
1. **Intégrité méthodologique préservée :** Le pipeline standard v6.0.1 reste strictement inchangé avec son garde-fou confirmatoire $N \ge 50$.
2. **Abstention honnête :** Aucune interpolation forcée ni résultat fantaisiste n'est produit sur des séries incomplètes ($< 3$ estimateurs finis ou $N < 7$).
3. **Respect de l'unité biologique :** Le rééchantillonnage s'effectue strictement au niveau du réplicat complet.
4. **Performance validée :** Forte corrélation avec la vérité terrain ($r = 0.985$), robustesse supérieure au 4PL sur profils plats et non monotones.
