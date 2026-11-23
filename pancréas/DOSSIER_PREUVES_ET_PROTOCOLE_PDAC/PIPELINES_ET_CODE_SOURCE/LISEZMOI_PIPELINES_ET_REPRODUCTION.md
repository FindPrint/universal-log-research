# SUITE COMPLÈTE DE PIPELINES T-LOG & REPRODUCTIBILITÉ SCIENTIFIQUE
**Dossier d'Exécution & Code Source Homologué V12 — 23 Novembre 2026**

---

## 1. Vue d'Ensemble de la Suite Logicielle

Ce répertoire réunit l'ensemble des modules logiciels, validateurs d'ingress, simulateurs et scripts de benchmark constituant le pipeline opérationnel **Universal Log / T-Log** appliqué à la physique statistique et à l'oncologie translationnelle du cancer du pancréas (PDAC).

Tous les scripts sont écrits en Python 3 standard (compatible Python 3.10+) et s'appuient sur les bibliothèques scientifiques `numpy`, `scipy`, `pandas` et `reportlab`.

---

## 2. Démarrage Rapide : Vérification Complète en 1 Clic

Pour tester l'intégrité de l'ensemble des composants et vérifier la conformité des résultats mathématiques et cliniques, exécutez simplement la suite de tests automatisée :

```powershell
python verify_all_pipelines.py
```

### Résultat attendu :
```text
================================================================================
🔬 SUITE DE VÉRIFICATION AUTOMATISÉE DES PIPELINES UNIVERSAL LOG / TLOG
================================================================================
✅ SUCCÈS | 1. Coeur v6.0.1 Control Flux Exclusion             | OK (Module chargé, 29 estimateurs & flux exclusion)
✅ SUCCÈS | 2. Dose-Response v1.0 (Courtes Courbes Organoïdes) | OK (IC50 = 0.4576 uM, T0 = 0.1092 uM, AUC = 0.63)
✅ SUCCÈS | 3. Validateur Ingress ctDNA (Format & Qualité)     | OK (Format Validé, Patients: 70, Points: 980)
✅ SUCCÈS | 4. Benchmark Lead-Time ctDNA vs Scanner RECIST     | OK (Lead-Time Médian = 56.0 jours d'avance)
✅ SUCCÈS | 5. Jumeau Numérique OncoTwin & Thérapie Pulsée     | OK (Gain PFS simulé: +9.2 à +15.4 mois)
✅ SUCCÈS | 6. Données Référence GDSC2 Pancréas (Sanger)       | OK (Dataset chargé : 675 points, r=0.9911)
================================================================================
🏆 VÉRIFICATION ACCOMPLIE : 100% DES PIPELINES SONT OPÉRATIONNELS !
================================================================================
```

---

## 3. Inventaire Détaillé des Fichiers et Rôles

| Fichier Script / Données | Catégorie | Rôle et Spécification Mathématique |
| :--- | :--- | :--- |
| `UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py` | **Moteur Coeur** | Pipeline maître universel v6.0.1. Implémente les 29 estimateurs non-paramétriques, la compensation de discrétisation, la dérive de Cohen et la règle formelle d'exclusion des flux de contrôle ($N \ge 50$). |
| `UNIVERSAL_LOG_dose_response_v1.py` | **Biomédical** | Moteur spécialisé pour les courbes de viabilité courtes ($N = 7..20$ points) sur organoïdes et lignées cellulaires. Évite les divergences singulières du modèle sigmoïde Hill 4PL. |
| `ctdna_ingress_validator.py` | **Clinique** | Validateur d'ingestion des séries temporelles de biopsie liquide ctDNA (KRAS VAF, copies/mL). Détecte les statuts Lewis-négatifs (inopérance du CA19-9) et normalise les schémas. |
| `emulate_and_benchmark_ctdna_cohort.py` | **Clinique** | Émulation de cohorte longitudinale (modèle Kirchweger 2022, 70 patients). Mesure l'avance temporelle (lead time) de détection de rechute TLog par rapport au scanner CT (RECIST 1.1). |
| `run_yin2025_full_evaluation.py` | **Benchmark** | Évaluation exhaustive sur les données réelles de l'étude Yin et al. (*Nature Communications* 2025). Démontre la résolution à 100% (75/75 conditions) contre 0% pour Hill 4PL. |
| `run_gdsc2_pdac_benchmark.py` | **Benchmark** | Benchmark sur 5 lignées pancréatiques x 5 agents de chimiothérapie (Sanger GDSC2). Valide la corrélation Pearson $r = 0.9911$ sur l'extraction d'IC50. |
| `tlog_oncotwin_simulator.py` | **Modélisation** | Simulateur de jumeau numérique de patient PDAC. Compare l'administration continue standard de chimiothérapie (échappement clonal rapide) et la trithérapie pulsée adaptative guidée par le seuil $T_0$. |
| `run_airquality_pipeline.py` | **Physique / Env.** | Exécution automatisée des 15 canaux de contrôle sur le benchmark Air Quality UCI (rotation complète, exclusion des flux invalides). |
| `create_delta_backup.ps1` | **Sauvegarde** | Script PowerShell de sauvegarde incrémentale différentielle (évite le gonflement disque des snapshots monolithiques). |

---

## 4. Données de Test et de Validation Incluses

1. `SYNTHETIC_TEST_RESULTS.csv` : 18 courbes de test synthétiques avec réplicats biologiques (sigmoïdes, profils résistants plats, profils non-monotones) pour valider l'absence de faux positifs d'IC50.
2. `EMULATION_KIRCHWEGER_70P_LONGITUDINAL.csv` : Cohorte clinique émulée de 70 patients suivis longitudinalement sur 14 visites (VAF KRAS, CA19-9, statut scanographique RECIST).
3. `GDSC2_PDAC_REFERENCE_CURVES.csv` : 675 mesures réelles de viabilité cellulaire issues du Sanger Institute sur PANC-1, MIA PaCa-2, Capan-1, BxPC-3 et AsPC-1.

---

## 5. Comment Intégrer de Nouvelles Données Cliniques ou Organoïdes

### A. Nouvelles courbes d'organoïdes ou de lignées ($N = 7..10$ doses) :
```python
import numpy as np
from UNIVERSAL_LOG_dose_response_v1 import analyze_dose_response_curve

doses = np.array([0.01, 0.1, 1.0, 10.0, 50.0])  # micromolaire
# replicates : matrice (N_doses, N_reps) normalisée (1.0 = viabilité témoin)
replicates = np.array([
    [0.98, 1.02, 0.95],
    [0.85, 0.88, 0.82],
    [0.45, 0.50, 0.42],
    [0.10, 0.12, 0.08],
    [0.02, 0.03, 0.01],
])

result = analyze_dose_response_curve(doses, replicates, drug_name="Nouvelle_Molecule", cell_id="Patient_PDO_01")
print(f"Statut : {result.status} | IC50 TLog : {result.ic50_tlog:.4f} µM | T0 : {result.t0_dose:.4f} µM")
```

### B. Nouvelles séries ctDNA d'un patient :
```python
from pathlib import Path
from ctdna_ingress_validator import validate_and_normalize

# Valide et met au format standardisé n'importe quel fichier CSV / Excel
df_patient, metadata = validate_and_normalize(Path("votre_fichier_patient.csv"))
print(f"Validation réussie : {metadata['n_patients']} patient(s) détecté(s).")
```

---
*Fin du guide technique — Reproductibilité garantie sous licence académique ouverte.*
