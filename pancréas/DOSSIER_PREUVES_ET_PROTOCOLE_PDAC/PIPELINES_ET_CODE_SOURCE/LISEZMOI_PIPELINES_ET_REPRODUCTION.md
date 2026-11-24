# SUITE EXPLORATOIRE DE PIPELINES T-LOG
**Dossier d'exécution et de reproduction — V12, 23 novembre 2026**

---

## 1. Vue d'Ensemble de la Suite Logicielle

Ce répertoire rassemble des modules logiciels, validateurs d'ingress, simulateurs et scripts de benchmark **Universal Log / T-Log**. Il s'agit d'un ensemble de recherche exploratoire, et non d'un dispositif clinique validé. Les résultats d'une simulation ou d'un test logiciel ne démontrent ni utilité clinique, ni bénéfice thérapeutique.

Les scripts ciblés ici utilisent Python 3.10+ et notamment `numpy`, `scipy`, `pandas` et, selon les tâches, `openpyxl`/`reportlab`. Vérifiez les dépendances installées dans l'environnement du projet avant de les lancer.

---

## 2. Démarrage Rapide : Vérification Complète en 1 Clic

Pour exécuter les vérifications fonctionnelles disponibles :

```powershell
& ..\..\..\.venv\Scripts\python.exe .\verify_all_pipelines.py
```

Le premier contrôle exécute un estimateur Katz du moteur central; il ne teste pas à lui seul l'ensemble des 29 estimateurs ou le pipeline complet. Les autres contrôles testent une courbe dose-réponse synthétique et sa règle d'abstention, recalculent les métriques sur l'émulation ctDNA et les courbes GDSC2-inspired, puis comparent deux scénarios du simulateur. Un échec renvoie un code de sortie non nul. Ces tests vérifient certains comportements logiciels; ils ne constituent pas une validation complète du moteur ni une preuve mathématique, biologique ou clinique.

L'évaluation Yin 2025 est un script séparé (`pancréas/ANALYSE_THERAPEUTIQUE_2026-11-23/YIN_2025_REAL_BENCHMARK/run_yin2025_full_evaluation.py`) qui nécessite le fichier supplémentaire XLSX de l'article; ce fichier source n'est pas inclus dans le paquet. Les instructions et les limites sont consignées dans le rapport Yin.

---

## 3. Inventaire Détaillé des Fichiers et Rôles

| Fichier Script / Données | Catégorie | Rôle et Spécification Mathématique |
| :--- | :--- | :--- |
| `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py` | **Moteur Coeur** | Pipeline maître universel v6.0.1. Implémente les 29 estimateurs non-paramétriques, la compensation de discrétisation, la dérive de Cohen et la règle formelle d'exclusion des flux de contrôle ($N \ge 50$). |
| `UNIVERSAL_LOG_dose_response_v1.py` | **Recherche** | Calcule des métriques dose-réponse sur des courbes courtes ($N = 7..20$). Fournit des estimations non paramétriques et une comparaison exploratoire au modèle 4PL; la présence d'une sortie ne garantit pas sa précision. |
| `ctdna_ingress_validator.py` | **Ingestion** | Associe des noms de colonnes à un schéma et effectue une normalisation de base des séries ctDNA. Ce n'est pas une validation clinique complète ni un contrôle de provenance des mesures. |
| `emulate_and_benchmark_ctdna_cohort.py` | **Émulation** | Génère une cohorte ctDNA synthétique de 70 profils et calcule une détection/avance sur progression définie dans cette simulation. Les métriques ne sont pas des résultats observés chez des patients. |
| `run_gdsc2_pdac_benchmark.py` | **Benchmark simulé** | Génère des courbes synthétiques inspirées de profils IC50 associés à GDSC2, puis compare les estimations TLog aux valeurs de référence fournies par le générateur. Ce ne sont pas 675 mesures brutes extraites de Sanger. |
| `extract_gdsc2_pdac_raw_curves.py` | **Prétraitement expérimental** | Extrait des mesures des lignées et médicaments ciblés du CSV brut officiel, applique la normalisation `gdscIC50` par scan et journalise les exclusions. Ne calcule pas de métrique TLog ni l'ajustement à effets mixtes GDSC. |
| `extract_gdsc2_target_drugs_all_cell_lines.py` | **Prétraitement expérimental** | Extrait les cinq médicaments GDSC2 ciblés dans toutes les lignées du CSV brut, produit un audit de scan et un manifeste; ne calcule pas de métrique TLog. |
| `compare_gdsc2_target_drugs_all_cell_lines_gdscic50.R` | **Ajustement exploratoire** | Tente l'ajustement `gdscIC50` sur les cinq médicaments et toutes les lignées, vérifie la convergence avant d'écrire le tableau comparatif et conserve un diagnostic même en cas d'échec. |
| `build_gdsc2_whitepaper_supplement.py` | **Publication** | Génère le supplément PDF daté avec les résultats tous-lignées et leurs limites; ne modifie pas les PDF archivés V12. |
| `tlog_oncotwin_simulator.py` | **Simulation** | Compare deux scénarios tumoraux déterminés par des paramètres codés dans le simulateur. Les différences de PFS simulées ne sont pas des estimations de bénéfice clinique. |
---

## 4. Données de Test et de Validation Incluses

1. `SYNTHETIC_TEST_RESULTS.csv` : courbes synthétiques de test; elles vérifient des comportements définis par le scénario, pas la performance sur des patients.
2. `EMULATION_KIRCHWEGER_70P_LONGITUDINAL.csv` : émulation synthétique de 70 trajectoires sur 14 visites, avec des statuts et temps de progression générés. Ce fichier n'est pas une cohorte clinique de Kirchweger.
3. `GDSC2_PDAC_REFERENCE_CURVES.csv` : 675 points générés synthétiquement à partir de profils IC50 de référence codés dans le générateur. Ne pas les citer comme mesures brutes Sanger/GDSC2.

### Extraction des données brutes GDSC2

Le CSV officiel `GDSC2_public_raw_data_24Jul22.csv` fait environ 2,1 Go et n'est pas inclus dans le dépôt. Après l'avoir obtenu depuis l'index Sanger, lancer depuis ce répertoire :

```powershell
python .\extract_gdsc2_pdac_raw_curves.py `
  --raw-csv "C:\chemin\GDSC2_public_raw_data_24Jul22.csv" `
  --output-dir "C:\chemin\gdsc2_pdac_extracted"
```

Le script lit le fichier en flux, applique les exclusions `FAIL`/médicament non attribué, calcule pour chaque scan la moyenne des contrôles `NC-1` et des blancs `B`, puis normalise chaque puits par `(INTENSITY - mean(B)) / (mean(NC-1) - mean(B))`, tronqué à `[0, 1]`. Il produit les puits normalisés, les moyennes par concentration et un audit par scan; les réponses sont des fractions de viabilité compatibles avec l'entrée `1.0 = viabilité témoin` de l'exemple TLog. Les puits d'une même plaque sont des répétitions techniques, pas des réplicats biologiques. Une moyenne par dose ne justifie donc pas un intervalle de confiance bootstrap biologique. Le script ne reproduit pas l'ajustement non linéaire à effets mixtes du paquet R officiel `gdscIC50` et ne constitue pas un benchmark TLog. Le CSV source reste à l'extérieur du dépôt.

Une extraction du fichier officiel complet a produit 1 708 puits normalisés et 637 points pour `AsPC-1`, `BxPC-3` et `CAPAN-1`; aucune ligne n'a été trouvée sous les noms exacts `PANC-1` et `MIA PaCa-2`. La taille et l'empreinte de cette source, les effectifs par lignée et les limites d'interprétation sont consignés dans `../GDSC2_AUDIT_SOURCE_ET_PLAN_REANALYSE.md`. Les fichiers de sortie et le manifeste de cette exécution sont des résultats locaux, non inclus dans le dépôt.

Un contrôle indépendant de 21 puits tirés de trois scans correspond exactement à la normalisation décrite dans le code source `gdscIC50`. Il ne s'agit pas d'une exécution du paquet R ni d'une reproduction de son ajustement à effets mixtes; ces étapes restent à valider avant toute revendication d'équivalence au pipeline officiel.

La comparaison descriptive avec les ajustements GDSC2 officiels est consignée dans l'audit parent. Dans les 91 courbes par scan extraites, seules 8 encadrent 50 % de mortalité dans les doses mesurées; ne pas rapporter d'IC50 calculée par extrapolation comme si elle était directement observée ou comme une validation de TLog.

### Essai du modèle officiel `gdscIC50`

Le script `compare_gdsc2_pdac_subset_gdscic50.R` tente le modèle mixte officiel sur les trois lignées et cinq médicaments extraits. Il requiert `gdscIC50` 0.99.4 et les deux CSV locaux (points extraits et table ajustée officielle) :

```powershell
Rscript -e "install.packages('remotes', repos='https://cloud.r-project.org')"
Rscript -e "remotes::install_github('CancerRxGene/gdscIC50@34d842254a33bd04f318449969ff9976237c9295')"

Rscript .\compare_gdsc2_pdac_subset_gdscic50.R `
  "C:\chemin\gdsc2_pdac_extracted\gdsc2_pdac_curve_points.csv" `
  "C:\chemin\GDSC2_fitted_dose_response_24Jul22.csv" `
  "C:\chemin\gdsc2_pdac_model_comparison.csv"
```

Si `Rscript` n'est pas dans le `PATH`, remplacer `Rscript` par le chemin complet vers `Rscript.exe`.

Le script n'écrit les comparaisons que si le modèle passe les contrôles de convergence; sinon il s'arrête sans produire de résultats à interpréter. Sur le sous-ensemble présent, les variantes testées ne convergent pas de façon acceptable. Cela ne reproduit pas l'ajustement GDSC2 global; voir les diagnostics et limites dans `../GDSC2_AUDIT_SOURCE_ET_PLAN_REANALYSE.md`. Les fonctions de préparation historiques du paquet appellent aussi des fonctions `dplyr` retirées; l'extraction et la vérification de normalisation sont donc rapportées séparément.

### Extraction et ajustement sur toutes les lignées

L'extracteur générique utilise les mêmes données brutes officielles, mais conserve les cinq médicaments ciblés pour toutes les lignées. Le CSV de 2,1 Go reste en local :

```powershell
python .\extract_gdsc2_target_drugs_all_cell_lines.py `
  --raw-csv "C:\chemin\GDSC2_public_raw_data_24Jul22.csv" `
  --output-dir "C:\chemin\gdsc2_all_lines_extracted"
```

Cette exécution a traité 7 327 scans valides, 179 515 puits et 125 230 points pour 968 lignées. Les mesures brutes ont recoupé 4 613 combinaisons lignée-médicament de la table officielle; six combinaisons brutes sans référence ajustée ont été exclues de la comparaison. Les fichiers d'extraction et leur manifeste ne sont pas inclus dans Git.

Le modèle nécessite `gdscIC50` 0.99.4 et le fichier ajusté officiel. Le dernier argument facultatif choisit `isLargeData` (`true` par défaut, ou `false`) :

```powershell
Rscript .\compare_gdsc2_target_drugs_all_cell_lines_gdscic50.R `
  "C:\chemin\gdsc2_all_lines_extracted\gdsc2_all_lines_normalized_wells.csv" `
  "C:\chemin\GDSC2_fitted_dose_response_24Jul22.csv" `
  "C:\chemin\gdsc2_all_lines_model_comparison.csv" `
  "C:\chemin\gdsc2_all_lines_model_diagnostic.csv" `
  false
```

Le script agrège les puits par lignée, médicament et dose (`FUN = mean`), comme le prétraitement `groupNlmeData` du paquet. L'option `isLargeData=TRUE` a produit une matrice de précision singulière; `isLargeData=FALSE` a convergé en 3 itérations avec une covariance définie positive. Le tableau descriptif contient 4 613 comparaisons; son diagnostic rapporte aussi les écarts aux références et la présence de courbes observées franchissant 50 %. La convergence ne valide pas l'adéquation des IC50 : les références proviennent des mêmes expériences, le biais moyen observé est notable et une majorité des combinaisons n'a aucun scan qui franchisse le seuil dans la plage mesurée. Ce résultat n'est ni une reproduction du modèle GDSC2 global ni une validation biologique ou clinique de TLog. Les CSV générés doivent rester des résultats locaux, hors du dépôt.

### Supplément PDF du livre blanc

Les PDF V12, dates du 23 novembre 2026, restent des archives historiques. Le supplément compagnon `../SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.pdf` y ajoute les résultats et les limites sans modifier ces originaux. Son contenu source est `../SUPPLEMENT_GDSC2_TOUTES_LIGNEES_2026-11-24.md`; l'erratum `../ERRATA_LIVRE_BLANC_V12.md` consigne ce statut. Pour le reconstruire avec `reportlab` installé :

```powershell
python .\build_gdsc2_whitepaper_supplement.py
```

Tests du prétraitement :

```powershell
python -m unittest -v test_extract_gdsc2_pdac_raw_curves
```

---

## 5. Comment Intégrer de Nouvelles Données Cliniques ou Organoïdes

### A. Nouvelles courbes d'organoïdes ou de lignées ($N = 7..20$ doses) :
```python
import numpy as np
from UNIVERSAL_LOG_dose_response_v1 import analyze_dose_response_curve

doses = np.array([0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0])  # µM
# replicates : matrice (N_replicats, N_doses), 1.0 = viabilité témoin
replicates = np.array([
    [0.98, 0.95, 0.88, 0.65, 0.32, 0.12, 0.04, 0.02],
    [1.02, 0.97, 0.85, 0.61, 0.29, 0.10, 0.03, 0.01],
    [0.95, 0.93, 0.90, 0.68, 0.35, 0.15, 0.05, 0.03],
])

result = analyze_dose_response_curve(doses, replicates, drug_name="Nouvelle_Molecule", cell_id="Patient_PDO_01")
print(f"Statut : {result.status} | IC50 TLog : {result.ic50_tlog} µM | T0 : {result.t0_dose} µM")
```

### B. Nouvelles séries ctDNA d'un patient :
```python
from pathlib import Path
from ctdna_ingress_validator import validate_and_normalize

# Vérifie le schéma minimal et normalise les noms de colonnes reconnus.
# Une revue de provenance, d'unités et de qualité par un spécialiste reste nécessaire.
df_patient, metadata = validate_and_normalize(Path("votre_fichier_patient.csv"))
print(f"Validation réussie : {metadata['n_patients']} patient(s) détecté(s).")
```

---
Ce guide décrit l'état du dossier à la date indiquée. Avant toute diffusion, confirmer la provenance des données, figer les dépendances et publier la licence applicable; aucune licence n'est présumée par ce document.
