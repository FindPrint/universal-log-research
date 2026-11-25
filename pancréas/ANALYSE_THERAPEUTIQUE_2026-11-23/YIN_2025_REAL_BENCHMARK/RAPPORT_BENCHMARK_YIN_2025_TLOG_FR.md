# RAPPORT SCIENTIFIQUE — RÉSOUDRE LE VERROU YIN ET AL. (2025)
## Évaluation Complète des 75 Conditions d'Organoïdes PDAC par le Mode Courtes Courbes TLog

**Date :** 23 novembre 2026  
**Article :** Yin et al., « Pathogenic germline variants in Chinese pancreatic adenocarcinoma patients », *Nature Communications* 16, 2214 (2025), Figure 6d. [DOI](https://doi.org/10.1038/s41467-025-57520-3), PMID 40044664, PMCID PMC11882848.

**Fichier source :** `41467_2025_57520_MOESM17_ESM.xlsx` (Figure 6)
**Résultats initiaux (supersédés) :** `YIN_2025_PDO_TLOG_BENCHMARK_RESULTS.csv` / `.json`
**Module utilisé :** `UNIVERSAL_LOG_dose_response_v1.py`

## Correction du 24 novembre 2026 — unités d'entrée du 4PL

L'exécution initiale décrite ci-dessous est **supersédée** pour l'interprétation de la convergence 4PL : elle a transmis au module des réponses exprimées en pourcentage (environ 0,83 à 140,31) alors que l'entrée dose-réponse et les bornes du 4PL sont en fraction de viabilité. Le résultat initial « 0/75 ajustement 4PL convergent » n'est donc pas valide et doit être retiré.

La réanalyse corrigée convertit les pourcentages en fractions, agrège les deux colonnes source disponibles par dose sans imputation, et n'applique pas de bootstrap puisque le classeur ne démontre pas que ces colonnes sont des réplicats biologiques indépendants. Elle obtient des sorties TLog et des ajustements 4PL en plage pour 75/75 courbes; la différence absolue médiane `log10(IC50_TLog)`–`log10(IC50_4PL)` est 0,190 (comparaison des méthodes sur les mêmes courbes, pas une mesure d'exactitude). Les sorties corrigées sont produites séparément par `run_yin2025_full_evaluation.py`; les anciens CSV/JSON ne sont pas écrasés.

La provenance bibliographique a été vérifiée : le résumé PubMed de l'article indique un criblage pharmacologique sur organoïdes dérivés de patients; le texte décrit des courbes dose-réponse de 15 PDO traités par correcteurs de CFTR (Figure 6d). La feuille supplémentaire porte l'en-tête `Drug Concentration(Log)` et des conditions `DAC_...` avec les molécules correspondantes. Le contrôle du DOI et du fichier source est consigné dans l'addendum; cela confirme la pertinence du jeu, sans établir l'indépendance biologique des colonnes ni l'exactitude des estimations.

Cette analyse a lieu après consultation des mêmes données et règles; elle reste exploratoire et ne constitue ni une évaluation indépendante ni une validation de TLog. Le classeur source, les unités et les limites sont documentés dans `ADDENDUM_YIN_2025_CORRECTION_UNITES_2026-11-24.md`.

Les nouveaux résultats corrigés sont `YIN_2025_FIG6D_TLOG_CORRECTED_UNITS_RESULTS.csv` et `.json`; ils ne remplacent pas les sorties historiques.

---

## 1. Contexte & Historique de la Découverte

Le 21 novembre 2026, un audit du pipeline central `v6.0.0` confronté aux 150 colonnes de réponses pharmacologiques de la Figure 6d de l'étude Yin 2025 (organoïdes dérivés de patients atteints de cancer du pancréas) avait conclu à un blocage technique majeur :
> *« 150/150 séries ont été rejetées à l’étape de longueur ($N < 50$) ; 0/29 estimateurs ont produit une valeur finie ; aucun $T_0$, TLog ou résultat biologique n’a été calculé. »*

Le 23 novembre 2026, le **Mode Courtes Courbes Dose-Réponse TLog (`UNIVERSAL_LOG_dose_response_v1.py`)** a été exécuté sur les 75 conditions extraites de la Figure 6d (150 colonnes de mesures regroupées par condition). Les colonnes sont traitées comme réplicats par le script; leur statut biologique ou technique n'est pas établi par le code.

---

## 2. Résultats Majeurs du Benchmark

* **Conditions expérimentales analysées :** **75 / 75** (100 %)
* **Statut logiciel `VALIDE` :** **75 / 75 (100.0 %)** selon les règles de statut implémentées dans le module; cela ne signifie pas que les estimations sont exactes.
* **Statut d'abstention :** **0 / 75 INDÉTERMINÉ (0.0 %)**
* **Seuils $T_{0,\text{dose}}$ calculés :** **75 / 75 (100.0 %)**
* **Points d'inflexion $IC_{50,\text{tlog}}$ calculés :** **75 / 75 (100.0 %)**
* **Ajustements Hill 4PL après conversion d'unités :** **75 / 75** convergents et en plage. Cette comparaison reste interne aux mêmes observations et dépend de l'implémentation.
* **Nombre moyen d'estimateurs finis :** **3.88 sur 5**
* **Temps de calcul observé lors de cette exécution :** **0.94 seconde**; dépend du matériel et de l'environnement.

---

## 3. Analyse Comparative : TLog vs Modèle Paramétrique 4PL (Hill)

| Propriété | Modèle Sigmoïde Conventionnel (Hill 4PL) | Mode Courtes Courbes TLog v1.0.0 |
|---|---|---|
| **Résultat de la réanalyse corrigée** | 75/75 ajustements convergents et en plage | 75 courbes classées `VALIDE` par les règles du module |
| **Sensibilité au bruit expérimental** | À mesurer sur des données contrôlées | Les estimateurs calculés ne constituent pas, à eux seuls, un filtrage validé |
| **Profils non monotones** | La comparaison doit utiliser une implémentation et des critères définis à l'avance | Le module attribue un statut selon sa règle de monotonie; ce statut reste à valider indépendamment |
| **Point de rupture initial** | Le 4PL standard ne fournit pas cette métrique | Le module calcule $T_{0,\text{dose}}$ selon sa définition opérationnelle |
| **Temps d'exécution** | Non comparé ici de façon contrôlée | Temps observé pour cette exécution; pas de benchmark de performance |

---

## 4. Exemple Concret : DAC_2 sous Lumacaftor

Pour l'organoïde `DAC_2` exposé à des concentrations logarithmiques de Lumacaftor (de $0.012\,\mu\text{M}$ à $200\,\mu\text{M}$) :
* **Doses :** 8 points ($N=8$, 2 réplicats).
* **Consensus Dimensionnel $D$ :** $1.303$ (Katz = 1.351, Petrosian = 1.096, Sevcik = 1.255, SampEn = 1.792).
* **Point de rupture initial $T_{0,\text{dose}}$ :** $71.42\,\mu\text{M}$ ($89.39\%$ de l'amplitude logarithmique).
* **Point d'inflexion $IC_{50,\text{tlog}}$ :** $82.04\,\mu\text{M}$ ($\log_{10} = 1.914$).
* **Ajustement 4PL après conversion en fraction :** convergent et en plage pour cette courbe. Cela ne constitue pas un test de référence indépendant du modèle 4PL.

---

## 5. Conclusion Scientifique

Cette exécution montre que le module court peut produire des estimations pour les 75 conditions de ce fichier public sans abaisser le seuil du moteur général. Elle ne démontre ni l'exactitude des IC50/T0, ni une supériorité générale sur 4PL, ni une capacité à recommander un traitement. La convergence des ajustements 4PL doit être reproduite avec une méthode de référence indépendante et des paramètres documentés. La validation suivante devrait comparer, en aveugle et sur des données indépendantes, les estimations à des valeurs de référence définies avant analyse.

## Reproduction et provenance des entrées

Le fichier supplémentaire XLSX de l'article n'est pas redistribué avec ce rapport. Téléchargez-le depuis les ressources supplémentaires de l'article associé au DOI ci-dessus, puis exécutez depuis la racine du dépôt :

```powershell
python "pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/YIN_2025_REAL_BENCHMARK/run_yin2025_full_evaluation.py" `
  --source "CHEMIN/VERS/41467_2025_57520_MOESM17_ESM.xlsx" `
  --output-dir "CHEMIN/VERS/RESULTATS"
```

Le temps de calcul, les seuils et les classifications rapportés décrivent cette implémentation et ce fichier; ils ne constituent pas une validation clinique.
Le script vérifie le SHA-256 attendu (`917a1011426c5ee749343ccabf8126e35923a65c4719ec929f84aa29a511f7b1`) ainsi que l'en-tête, les concentrations et le nombre de conditions avant d'écrire des résultats.
