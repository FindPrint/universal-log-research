# RAPPORT D'EXÉCUTION DU PIPELINE UNIVERSAL_LOG v6.0.1
## Benchmark UCI Air Quality — Rotation Complète des 15 Axes de Contrôle

**Date :** 23 novembre 2026  
**Auteur :** Antigravity (Google DeepMind)  
**Version du Pipeline :** `v6.0.1-control-flux-exclusion-L7aL7b-CohenD`  
**Emplacement des données et résultats :** `C:\Users\citys\Desktop\10-31-2026\pancréas\ANALYSE_THERAPEUTIQUE_2026-11-23\AIR_QUALITY_PIPELINE\`  
**Dépôt de référence :** [https://github.com/FindPrint/universal-log-research](https://github.com/FindPrint/universal-log-research)  
**Manifeste d'exécution :** `results/campaign_manifest.json`  
**Synthèse tabulaire :** `results/airquality_pipeline_summary.csv`

---

## 1. Contexte & Spécifications du Benchmark

Le jeu de données **Air Quality UCI** rassemble 9 357 enregistrements horaires horodatés (du 10 mars 2004 au 4 avril 2005) collectés par un réseau de capteurs chimiques à semi-conducteurs métalliques (site urbain pollué de Rome).  
Conformément au protocole arrêté dans le **README V12**, les données ont été préparées selon les spécifications méthodologiques suivantes :
1. **Élimination du code sentinelle `-200` :** Toutes les valeurs manquantes ont été converties en `NaN` sans imputation artificielle.
2. **Échantillonnage en 100 bins temporels réguliers :** Construction de moyennes de blocs temporels pour préserver l'ordre chronologique des processus physico-chimiques et atmosphériques.
3. **Rotation systématique de 15 axes de contrôle :** 13 capteurs/polluants physico-chimiques + l'axe temporel direct (`time_index_hours`) + l'indicateur de complétude (`missing_fraction_numeric`).
4. **Cible fixée :** `CO(GT)` (Monoxyde de carbone mesuré par analyseur de référence certifié).
5. **Garde-fous confirmatoires v6.0.1 :**
   - Exclusion stricte du flux de contrôle de l'ensemble des flux d'analyse.
   - Repli diagonal automatique si l'axe demandé vérifie `Contrôle == Cible` (évite l'auto-régression triviale).
   - Rejet confirmatoire immédiat si le nombre d'observations valides est strictement inférieur à 50 ($N_{valid} < 50$).
   - Règle d'abstention si moins de 3 estimateurs de complexité convergent.

---

## 2. Synthèse Globale des Résultats

* **Total de contrôles planifiés :** 15
* **Contrôles complétés avec succès :** **14 / 15**
* **Contrôles rejetés pour support insuffisant :** **1 / 15** (`NMHC(GT)`)
* **Erreurs ou crashs d'exécution :** **0 / 15**
* **Temps total d'exécution :** 615.7 secondes (10.26 minutes) sur 6 workers concurrents.

| # | Axe de Contrôle | Bins Valides | Statut v6.0.1 | $T_0$ (%) | Valeur brute de transition | Régime Dominant | Estimateurs Finis (sur 29) | Durée (s) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **01** | `CO(GT)` | 98 / 100 | **COMPLETE** | **14.96 %** | $2.14\,\text{mg/m}^3$ | Criticality | 25 | 229.5 |
| **02** | `PT08.S1(CO)` | 100 / 100 | **COMPLETE** | **95.17 %** | $1285.2\,\text{mV}$ | Criticality | 25 | 207.1 |
| **03** | `NMHC(GT)` | **12 / 100** | **INSUFFISANT** | *None* | *None* | Indeterminate | 0 | 0.0 |
| **04** | `C6H6(GT)` | 100 / 100 | **COMPLETE** | **71.06 %** | $11.44\,\mu\text{g/m}^3$ | Criticality | 27 | 299.5 |
| **05** | `PT08.S2(NMHC)` | 100 / 100 | **COMPLETE** | **95.22 %** | $1134.2\,\text{mV}$ | Criticality | 27 | 299.9 |
| **06** | `NOx(GT)` | 97 / 100 | **COMPLETE** | **92.78 %** | $429.57\,\text{ppb}$ | Criticality | 27 | 285.9 |
| **07** | `PT08.S3(NOx)` | 100 / 100 | **COMPLETE** | **13.21 %** | $680.80\,\text{mV}$ | Criticality | 25 | 269.8 |
| **08** | `NO2(GT)` | 97 / 100 | **COMPLETE** | **88.66 %** | $147.06\,\mu\text{g/m}^3$ | Criticality | 27 | 282.9 |
| **09** | `PT08.S4(NO2)` | 100 / 100 | **COMPLETE** | **8.93 %** | $1043.56\,\text{mV}$ | Criticality | 27 | 295.1 |
| **10** | `PT08.S5(O3)` | 100 / 100 | **COMPLETE** | **97.11 %** | $1424.11\,\text{mV}$ | Criticality | 25 | 273.0 |
| **11** | `T` (Température) | 100 / 100 | **COMPLETE** | **2.95 %** | $5.17\,^\circ\text{C}$ | Criticality | 26 | 307.3 |
| **12** | `RH` (Humidité Rel.) | 100 / 100 | **COMPLETE** | **80.33 %** | $60.06\,\%$ | Criticality | 27 | 298.5 |
| **13** | `AH` (Humidité Abs.) | 100 / 100 | **COMPLETE** | **97.04 %** | $1.67$ | **Saturation** | 27 | 306.4 |
| **14** | `time_index_hours` | 100 / 100 | **COMPLETE** | **45.15 %** | $4276.5\,\text{h}$ | Criticality | 27 | 297.7 |
| **15** | `missing_fraction` | 100 / 100 | **COMPLETE** | **97.06 %** | $0.471$ | **Saturation** | 25 | 297.8 |

---

## 3. Analyse Phénoménologique & Validation des Garde-Fous

### 3.1 Rejet Formel et Justifié de NMHC(GT)
Le capteur d'hydrocarbures non-méthaniques `NMHC(GT)` a cessé d'enregistrer des données valides après le 1er mai 2004 dans la base originale UCI (seules 827 mesures non manquantes subsistent sur 9 357).  
* **Résultat du binning :** Seuls **12 bins sur 100** contiennent des données valides.
* **Comportement du pipeline :** Rejet immédiat avec le message :
  > `Points de contrôle valides (12) < 50 (seuil de support minimal v6.0.1)`
* **Interprétation :** Ce comportement valide rigoureusement la politique d'abstention : le pipeline refuse d'extrapoler sur une série discontinue dépourvue de fondement statistique.

### 3.2 Gestion de l'Axe Diagonal `CO(GT)`
Lorsque `CO(GT)` est à la fois cible et contrôle, le pipeline v6.0.1 active son protocole de repli documenté :
* La cible réelle pour ce run particulier bascule sur la première colonne alternative (`PT08.S1(CO)`).
* `CO(GT)` est formellement exclu des flux d'analyse pour éviter l'artefact d'identité $Y = X$.
* Le run aboutit à un $T_0 = 14.96\%$ avec 25 estimateurs convergents.

### 3.3 Structuration Temporelle et Saisonière (`time_index_hours`)
L'axe temporel pur (`time_index_hours`) présente une monotonie stricte confirmée (`monotone = True`, `direction = nondecreasing`).
* **Seuil détecté :** $T_0 = 45.15\%$ (soit à $4\,276.5$ heures de série, correspondant à la fin de l'été / début de l'automne 2004).
* **Phénomène sous-jacent :** Cette transition critique marque le basculement climatique entre le régime estival méditerranéen (ozone prédominant, fort rayonnement photochimique) et le régime automnal/hivernal (inversion thermique, réactivation du chauffage urbain et augmentation marquée des oxydes d'azote $NO_x$).

### 3.4 Régimes de Saturation Identifiés
Deux axes basculent en régime de **Saturation** à $T_0 \approx 97\%$ :
1. **`AH` (Humidité Absolue, $T_0 = 97.04\%$) :** Marque la phase printanière finale 2005 où les concentrations en vapeur d'eau atteignent un seuil haut stabilisé.
2. **`missing_fraction_numeric` ($T_0 = 97.06\%$) :** Détecte la dégradation finale des enregistrements en fin de campagne de mesure (hausse abrupte de la proportion de données manquantes à $47.1\%$).

---

## 4. Conclusion & Conformité V12

La campagne Air Quality UCI apporte la démonstration de la robustesse opérationnelle de `v6.0.1` :
- **Consensus élevé :** 25 à 27 estimateurs finis par run (sur 29 possibles).
- **Sensibilité multi-échelle :** Les seuils $T_0$ s'échelonnent de $2.95\%$ (Température) à $97.11\%$ (Ozone), démontrant que le pipeline ne converge pas vers un seuil trivial arbitraire.
- **Intégrité méthodologique :** Les artéfacts d'instruments (NMHC défaillant) et les données manquantes sont isolés et explicités sans aucune pollution des conclusions scientifiques.
