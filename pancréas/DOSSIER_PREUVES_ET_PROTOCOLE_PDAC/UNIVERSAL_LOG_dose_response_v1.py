# -*- coding: utf-8 -*-
"""
UNIVERSAL_LOG_dose_response_v1.py — Mode Courtes Courbes Dose-Réponse (N=7 à 20 points)
========================================================================================

Module autonome pour l'analyse fractale et non-linéaire TLog de profils dose-réponse
courts (N = 7 à 20 concentrations), adapté aux criblages pharmacologiques modernes
(ex. GDSC2, PRISM DepMap, Yin 2025 PDOs de cancer du pancréas).

PRINCIPES MÉTHODOLOGIQUES ET GARDE-FOUS :
------------------------------------------
1. SÉPARATION STRICTE :
   Ce module est complètement indépendant du pipeline standard v6.0.1.
   Le seuil confirmatoire N >= 50 du pipeline standard reste intact et n'est
   en aucun cas abaissé.

2. ESTIMATEURS SÉLECTIONNÉS (5 ROBUSTES SUR COURTES SÉRIES) :
   - Katz FD (Katz, 1988) : compacité et tortuosité du profil. Valide dès N >= 3.
   - Petrosian FD (Petrosian, 1995) : mesure des inversions de pente (dérivée première). Valide dès N >= 4.
   - Sevcik FD (Sevcik, 1998) : longueur de corde normalisée sur l'espace unitaire [0,1]^2. Valide dès N >= 4.
   - SampleEntropy (Richman & Moorman, 2000) : régularité avec m=1 adapté aux séries courtes.
   - DFA (Peng et al., 1994) : analyse des fluctuations sans tendance sur fenêtres courtes (s >= 3).

3. LES 24 ESTIMATEURS REJETÉS :
   Higuchi, Hurst (R/S), BoxCounting, PermutationEntropy, CorrelationD2,
   GrassbergerProcaccia, InformationD1, VisibilityGraph, TwoNN, DANCo, Fisher,
   LevinaBickel, PCAIntrinsic, LocalPCA, GraphDimension, PersistentHomology,
   MFA, KolmogorovLZ, SpectralBeta, SpectralDimension, Hurst2mH, Lyapunov,
   MultifractalDeltaAlpha, SingularityFmax.
   Raison du rejet : instabilité mathématique, dégénérescence géométrique,
   absence de degrés de liberté suffisants ou biais d'échantillonnage massif pour N < 20.

4. RÈGLE D'ABSTENTION OBLIGATOIRE (HONNÊTETÉ SCIENTIFIQUE) :
   Si le nombre d'estimateurs finis valides parmi les 5 est strictement inférieur à 3 (< 3),
   le module conclut impérativement par le statut "INDÉTERMINÉ" (jamais de forçage).

5. UNITÉ DE RÉÉCHANTILLONNAGE BIOLOGIQUE :
   Le rééchantillonnage bootstrap s'effectue exclusivement au niveau du RÉPLICAT BIOLOGIQUE
   (les courbes entières), JAMAIS au niveau des concentrations individuelles isolées,
   préservant ainsi l'ordre physico-chimique et l'autocorrélation des concentrations.

6. SORTIES COMPARATIVES :
   - T0_dose : point de décrochage / transition critique de viabilité.
   - IC50_tlog : point d'inflexion médian non paramétrique TLog.
   - AUC_tlog : aire sous la courbe normalisée trapézoïdale sur log10(dose).
   - IC50_4PL : ajustement conventionnel sigmoïde 4-paramètres (Hill) avec diagnostic
     de convergence et comparaison delta.
"""

import sys
import os
import math
import json
import warnings
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit


# =============================================================================
# CONSTANTES ET CONFIGURATION DU MODULE
# =============================================================================

VERSION = "1.0.0"
MIN_DOSE_POINTS = 7
MAX_DOSE_POINTS = 20
MIN_FINITE_ESTIMATORS = 3  # Règle d'abstention : minimum 3/5 estimateurs finis

ROBUST_ESTIMATOR_NAMES = ["Katz", "Petrosian", "Sevcik", "SampleEn", "DFA"]

REJECTED_ESTIMATORS = {
    "Higuchi": "Exige k_max >= 3 sous-échantillonné, dégénère sous N < 16",
    "Hurst": "Exige N/2 >= 8 (donc N >= 16), biais R/S massif sur très courts blocs",
    "BoxCounting": "Exige au minimum 16 points pour remplir des boîtes multi-échelles",
    "PermutationEntropy": "Ordre m=3 requiert N >> 3!=6 ; sous-échantillonnage massif pour N=8",
    "CorrelationD2": "Plongement de phase impossible (trop peu de paires de vecteurs)",
    "GrassbergerProcaccia": "Intégrale de corrélation non convergente sur nuage < 20 points",
    "InformationD1": "Probabilités de Shannon sur boîtes dégénérées",
    "VisibilityGraph": "Réseau complexe de 8 nœuds dominé par les effets de bord discrets",
    "TwoNN": "Estimation k-NN impossible sans voisinage dense",
    "DANCo": "Estimateur de variété requiert des centaines de points",
    "Fisher": "Matrice d'information singulière sur courtes séries",
    "LevinaBickel": "Maximum de vraisemblance k-NN non convergent pour N < 20",
    "PCAIntrinsic": "Décomposition spectrale non significative sur covariance 8x8",
    "LocalPCA": "Voisinages locaux vides ou redondants",
    "GraphDimension": "Topologie de graphe dégénérée",
    "PersistentHomology": "Diagrammes de persistance triviaux / artéfacts de bruit",
    "MFA": "Analyse multifractale exige de grands intervalles d'échelle",
    "KolmogorovLZ": "Complexité algorithmique non asymptotique sur courtes chaînes",
    "SpectralBeta": "FFT fournit <= 4 fréquences, régression spectrale invalide",
    "SpectralDimension": "Densité d'états spectrale non résoluble",
    "Hurst2mH": "Inférence 2 - H non fiable",
    "Lyapunov": "Divergence de trajectoires sans attracteur reconstructible",
    "MultifractalDeltaAlpha": "Spectre de singularité indéterminé",
    "SingularityFmax": "Maximum f(alpha) non calculable"
}


# =============================================================================
# 1. ESTIMATEURS DE COMPLEXITÉ SPÉCIALISÉS POUR COURTES SÉRIES
# =============================================================================

def katz_fd(y: np.ndarray) -> float:
    """
    Dimension fractale de Katz (1988) sur série 1D.
    D = log10(n - 1) / (log10(d_max / L) + log10(n - 1))
    Valide pour n >= 3.
    """
    y = np.asarray(y, dtype=float).flatten()
    n = len(y)
    if n < 3:
        return np.nan
    diffs = np.diff(y)
    l_sum = float(np.sum(np.sqrt(1.0 + diffs ** 2)))
    d_max = float(np.max(np.sqrt(np.arange(n) ** 2 + (y - y[0]) ** 2)))
    if l_sum < 1e-12 or d_max < 1e-12:
        return 1.0
    den = np.log10(d_max) - np.log10(l_sum) + np.log10(n - 1)
    if abs(den) < 1e-12:
        return 1.0
    val = float(np.log10(n - 1) / den)
    return val if np.isfinite(val) and val >= 0.5 else np.nan


def petrosian_fd(y: np.ndarray) -> float:
    """
    Dimension fractale de Petrosian (1995).
    D = log10(N) / (log10(N) + log10(N / (N + 0.4 * N_delta)))
    où N_delta est le nombre d'inversions de signe de la dérivée première.
    Valide pour n >= 4.
    """
    y = np.asarray(y, dtype=float).flatten()
    n = len(y)
    if n < 4:
        return np.nan
    diff = np.diff(y)
    signs = np.sign(diff)
    nz = signs[signs != 0]
    nd = int(np.sum(nz[1:] * nz[:-1] < 0)) if len(nz) > 1 else 0
    if nd == 0:
        return 1.0  # Monotonie stricte
    den = np.log10(n) + np.log10(n / (n + 0.4 * nd))
    if abs(den) < 1e-12:
        return 1.0
    val = float(np.log10(n) / den)
    return val if np.isfinite(val) else np.nan


def sevcik_fd(y: np.ndarray) -> float:
    """
    Dimension fractale de Sevcik (1998).
    Normalisation dans le carré unité [0,1]^2 puis calcul de la longueur de corde.
    D = 1 + ln(L) / ln(2 * (n - 1))
    Valide pour n >= 4.
    """
    y = np.asarray(y, dtype=float).flatten()
    n = len(y)
    if n < 4:
        return np.nan
    span = float(np.ptp(y))
    if span < 1e-12:
        return 1.0  # Ligne horizontale plate
    y_norm = (y - np.min(y)) / span
    dx = 1.0 / (n - 1)
    dy = np.diff(y_norm)
    length = float(np.sum(np.hypot(dx, dy)))
    if length <= 1.0:
        return 1.0
    den = np.log(2.0 * (n - 1))
    if abs(den) < 1e-12:
        return 1.0
    val = float(1.0 + np.log(length) / den)
    return val if np.isfinite(val) else np.nan


def sample_entropy_short(y: np.ndarray, m: int = 1, r_factor: float = 0.2) -> float:
    """
    Sample Entropy (Richman & Moorman 2000) adaptée aux séries courtes (N=7..20).
    Sur très courtes séries, m=1 est robuste et prévient la disparition des motifs.
    Tolérance r = r_factor * std(y).
    Abstention stricte (retourne NaN) si std < 1e-12 ou si cm == 0 ou cm1 == 0.
    """
    y = np.asarray(y, dtype=float).flatten()
    n = len(y)
    std_y = float(np.std(y))
    if std_y < 1e-12 or n < m + 2:
        return np.nan
    r = r_factor * std_y

    def _matches(pattern_len: int) -> int:
        count = 0
        templates = np.array([y[i:i + pattern_len] for i in range(n - pattern_len + 1)])
        n_templates = len(templates)
        for i in range(n_templates):
            if i + 1 < n_templates:
                diffs = np.max(np.abs(templates[i + 1:] - templates[i]), axis=1)
                count += int(np.sum(diffs < r))
        return count

    cm = _matches(m)
    cm1 = _matches(m + 1)
    if cm > 0 and cm1 > 0:
        ratio = cm1 / float(cm)
        if ratio > 0:
            return float(-np.log(ratio))
    return np.nan


def dfa_exponent_short(y: np.ndarray, min_scale: int = 3) -> float:
    """
    Detrended Fluctuation Analysis (DFA) adapté aux courtes séries (N=7..20).
    Échelles admissibles s in [min_scale, n // 2].
    Exige au moins 3 échelles distinctes valides pour une régression linéaire honnête.
    Pour N < 9 (ex. N=7 ou 8), retourne NaN par abstention méthodologique.
    DFA Dimension D = 2.0 - alpha.
    """
    y = np.asarray(y, dtype=float).flatten()
    n = len(y)
    if n < 7:
        return np.nan
    max_scale = n // 2
    if max_scale < min_scale:
        return np.nan
    scales = np.arange(min_scale, max_scale + 1)
    if len(scales) < 3:
        return np.nan

    y_cum = np.cumsum(y - np.mean(y))
    fluctuations: List[float] = []
    scales_used: List[int] = []

    for sc in scales:
        segments = n // sc
        if segments < 1:
            continue
        y_trunc = y_cum[:segments * sc]
        seg_matrix = y_trunc.reshape(segments, sc)
        x = np.arange(sc)
        x_mean = (sc - 1) / 2.0
        x_var = float(np.var(x))
        if x_var < 1e-12:
            continue
        y_m = np.mean(seg_matrix, axis=1, keepdims=True)
        cov = np.mean((seg_matrix - y_m) * (x - x_mean), axis=1)
        slope = cov / x_var
        intercept = y_m.squeeze(axis=-1) - slope * x_mean
        trend = slope[:, None] * x + intercept[:, None]
        rms = np.mean((seg_matrix - trend) ** 2, axis=1)
        fl_val = float(np.sqrt(np.mean(rms)))
        if fl_val > 1e-12 and np.isfinite(fl_val):
            fluctuations.append(fl_val)
            scales_used.append(int(sc))

    fl_arr = np.asarray(fluctuations, dtype=float)
    sc_arr = np.asarray(scales_used, dtype=float)
    ok = np.isfinite(fl_arr) & (fl_arr > 1e-12) & np.isfinite(sc_arr) & (sc_arr > 0)
    if int(np.sum(ok)) >= 3:
        slope, *_ = stats.linregress(np.log(sc_arr[ok]), np.log(fl_arr[ok]))
        if np.isfinite(slope):
            return float(2.0 - slope)
    return np.nan


def compute_short_complexity_profile(y: np.ndarray) -> Dict[str, float]:
    """
    Calcule le profil des 5 estimateurs robustes sur une série courte.
    """
    y = np.asarray(y, dtype=float).flatten()
    return {
        "Katz": katz_fd(y),
        "Petrosian": petrosian_fd(y),
        "Sevcik": sevcik_fd(y),
        "SampleEn": sample_entropy_short(y, m=1),
        "DFA": dfa_exponent_short(y, min_scale=3)
    }


# =============================================================================
# 2. AJUSTEMENT CONVENTIONNEL SIGMOÏDE 4-PARAMÈTRES (4PL HILL CYTOTOXIQUE)
# =============================================================================

def sigmoid_4pl(x: np.ndarray, bottom: float, top: float, log_ic50: float, hill: float) -> np.ndarray:
    """
    Équation logistique standard 4PL pour cytotoxicité / viabilité :
    Y = Bottom + (Top - Bottom) / (1 + 10^((x - log10(IC50)) * Hill))
    où x = log10(concentration).
    À basse dose (x << log_ic50) : Y -> Top (ex: 1.0 = 100% viabilité).
    À haute dose (x >> log_ic50) : Y -> Bottom (ex: 0.05 = mortalité).
    """
    return bottom + (top - bottom) / (1.0 + 10.0 ** ((x - log_ic50) * hill))


def fit_4pl_sigmoid(doses: np.ndarray, response: np.ndarray) -> Dict[str, Any]:
    """
    Ajustement 4PL conventionnel par moindres carrés non linéaires.
    Retourne IC50_4PL, Bottom, Top, HillSlope, R2, et statut de convergence.
    """
    doses = np.asarray(doses, dtype=float).flatten()
    response = np.asarray(response, dtype=float).flatten()
    log_doses = np.log10(doses)

    resp_min = float(np.min(response))
    resp_max = float(np.max(response))
    span = resp_max - resp_min

    if span < 0.10:
        # Courbe plate, 4PL non identifiable
        return {
            "converged": False,
            "ic50_4pl": np.nan,
            "log_ic50_4pl": np.nan,
            "top": float(np.median(response)),
            "bottom": float(np.median(response)),
            "hill_slope": 0.0,
            "r2": 0.0,
            "reason": "Courbe sans amplitude de réponse (span < 0.10)"
        }

    p0 = [max(0.0, resp_min), min(1.2, resp_max), float(np.median(log_doses)), 1.5]
    bounds = (
        [-0.1, 0.5, float(log_doses[0] - 2.5), 0.1],
        [0.5, 1.5, float(log_doses[-1] + 2.5), 15.0]
    )

    try:
        popt, _ = curve_fit(
            sigmoid_4pl, log_doses, response,
            p0=p0, bounds=bounds, maxfev=4000
        )
        bottom, top, log_ic50, hill = popt
        fitted = sigmoid_4pl(log_doses, *popt)
        ss_res = float(np.sum((response - fitted) ** 2))
        ss_tot = float(np.sum((response - np.mean(response)) ** 2))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 0.0

        ic50_val = float(10.0 ** log_ic50)
        in_range = (log_doses[0] - 0.5) <= log_ic50 <= (log_doses[-1] + 0.5)

        return {
            "converged": True,
            "ic50_4pl": ic50_val,
            "log_ic50_4pl": float(log_ic50),
            "top": float(top),
            "bottom": float(bottom),
            "hill_slope": float(hill),
            "r2": float(max(0.0, r2)),
            "in_range": in_range,
            "reason": "Convergence réussie"
        }
    except Exception as exc:
        return {
            "converged": False,
            "ic50_4pl": np.nan,
            "log_ic50_4pl": np.nan,
            "top": np.nan,
            "bottom": np.nan,
            "hill_slope": np.nan,
            "r2": 0.0,
            "reason": f"Échec d'ajustement: {str(exc)}"
        }


# =============================================================================
# 3. EXTRACTION TLOG DOSE-RÉPONSE (T0_dose, IC50_tlog, AUC_tlog)
# =============================================================================

def compute_trapezoidal_auc(log_doses: np.ndarray, response: np.ndarray) -> float:
    """
    Calcule l'AUC normalisée sur l'intervalle log10(doses) :
    AUC = (1 / (x_max - x_min)) * sum_i 0.5 * (y_i + y_{i+1}) * (x_{i+1} - x_i)
    Valeur comprise entre 0.0 (toxicité totale immédiate) et 1.0 (aucune inhibition).
    """
    x = np.asarray(log_doses, dtype=float)
    y = np.asarray(response, dtype=float)
    total_range = float(x[-1] - x[0])
    if total_range <= 1e-12:
        return float(np.mean(y))
    auc = float(np.trapz(y, x)) / total_range
    return float(max(0.0, min(2.0, auc)))


def compute_ic50_tlog(doses: np.ndarray, response: np.ndarray) -> Tuple[float, float, str]:
    """
    Estimation non paramétrique robuste TLog de l'IC50.
    Identifie le point où la viabilité atteint le point médian de transition
    (50% de la transition observée entre le plateau haut et le plateau bas).
    
    Retourne : (ic50_tlog, log_ic50_tlog, method_flag)
    """
    doses = np.asarray(doses, dtype=float)
    response = np.asarray(response, dtype=float)
    log_doses = np.log10(doses)
    n = len(doses)

    # Plateaux haut (2 premières doses) et bas (2 dernières doses)
    y_top = float(np.median(response[:2]))
    y_bottom = float(np.median(response[-2:]))
    delta_resp = abs(y_top - y_bottom)

    if delta_resp < 0.15:
        # Absence d'inhibition claire (> 15% requis pour transition)
        return np.nan, np.nan, "NO_TRANSITION_FLAT"

    # Inflexion médiane cible (50% de l'amplitude)
    y_mid = min(y_top, y_bottom) + 0.5 * delta_resp

    # Recherche de l'intervalle encadrant y_mid le long des doses
    found_idx = -1
    for i in range(n - 1):
        if (response[i] >= y_mid >= response[i + 1]) or (response[i] <= y_mid <= response[i + 1]):
            found_idx = i
            break

    if found_idx != -1:
        x1, x2 = log_doses[found_idx], log_doses[found_idx + 1]
        y1, y2 = response[found_idx], response[found_idx + 1]
        denom = y2 - y1
        if abs(denom) > 1e-12:
            frac = (y_mid - y1) / denom
            log_ic50 = float(x1 + frac * (x2 - x1))
            return float(10.0 ** log_ic50), log_ic50, "TLOG_LOG_LINEAR_INTERPOLATION"

    # Si pas de croisement direct, point le plus proche
    closest = int(np.argmin(np.abs(response - y_mid)))
    log_ic50 = float(log_doses[closest])
    return float(10.0 ** log_ic50), log_ic50, "TLOG_NEAREST_POINT"


def compute_t0_dose(doses: np.ndarray, response: np.ndarray) -> Tuple[float, float, float, str]:
    """
    Détection de T0_dose : seuil critique de décrochage (Point of Departure / rupture de régime).
    Analogue au T0 d'Universal Log v6.0.1, mais sur la progression des concentrations.
    
    T0_dose repère la concentration où la viabilité quitte le régime basal
    non perturbé pour entrer dans la transition active (seuil de perte de viabilité >= 15%).
    
    Retourne : (t0_dose_units, log_t0_dose, t0_progression_pct, method_flag)
    """
    doses = np.asarray(doses, dtype=float)
    response = np.asarray(response, dtype=float)
    log_doses = np.log10(doses)
    n = len(doses)

    baseline_top = float(np.median(response[:2]))
    bottom = float(np.median(response[-2:]))
    amplitude = baseline_top - bottom

    if amplitude < 0.15:
        # Courbe plate, aucun décrochage détectable
        return np.nan, np.nan, np.nan, "NO_T0_FLAT_RESISTANT"

    # Seuil de départ : perte de 15% de l'amplitude totale par rapport au plateau
    y_threshold = baseline_top - 0.15 * amplitude

    cross_idx = -1
    for i in range(n - 1):
        if response[i] >= y_threshold > response[i + 1]:
            cross_idx = i
            break

    if cross_idx != -1:
        x1, x2 = log_doses[cross_idx], log_doses[cross_idx + 1]
        y1, y2 = response[cross_idx], response[cross_idx + 1]
        denom = y2 - y1
        frac = (y_threshold - y1) / denom if abs(denom) > 1e-12 else 0.5
        log_t0 = float(x1 + frac * (x2 - x1))
    else:
        # Chute immédiate dès la première dose
        log_t0 = float(log_doses[0])

    t0_units = float(10.0 ** log_t0)
    log_span = log_doses[-1] - log_doses[0]
    t0_pct = float(((log_t0 - log_doses[0]) / log_span) * 100.0) if log_span > 1e-12 else 0.0
    t0_pct = float(max(0.0, min(100.0, t0_pct)))

    return t0_units, log_t0, t0_pct, "TLOG_POD_THRESHOLD"


# =============================================================================
# 4. MODULE PRINCIPAL D'ANALYSE DOSE-RÉPONSE TLOG
# =============================================================================

@dataclass
class DoseResponseResult:
    drug_name: str
    cell_id: str
    n_doses: int
    n_replicates: int
    status: str                    # "VALIDE", "INDÉTERMINÉ", "RÉSISTANT_PLAT", "NON_MONOTONE"
    abstention: bool               # True si règle d'abstention appliquée
    abstention_reason: str
    
    # Estimateurs de complexité (valeurs sur la courbe moyenne)
    katz_fd: float
    petrosian_fd: float
    sevcik_fd: float
    sample_entropy: float
    dfa_exponent: float
    n_finite_estimators: int
    d_consensus: float             # Médiane des dimensions fractales finies
    
    # Sorties TLog
    t0_dose: float                 # Seuil de décrochage critique (unités dose)
    t0_dose_pct: float             # Seuil en % de l'axe de progression log
    ic50_tlog: float               # Point d'inflexion médian TLog
    log_ic50_tlog: float
    auc_tlog: float                # Aire sous la courbe trapézoïdale normalisée
    auc_tlog_ci_low: float         # IC95% bootstrap (réplicats)
    auc_tlog_ci_high: float
    
    # Comparaison 4PL conventionnel
    fit_4pl_converged: bool
    ic50_4pl: float
    log_ic50_4pl: float
    hill_slope_4pl: float
    r2_4pl: float
    delta_log_ic50: float          # |log10(IC50_tlog) - log10(IC50_4PL)|
    
    # Diagnostic qualitatif
    regime_tlog: str               # "CRITICALITY", "SATURATION", "DIVERGENCE", "PERTURBATION"
    monotonicity_flag: str         # "MONOTONIC_DECREASING", "FLAT", "NON_MONOTONIC"


def analyze_dose_response_curve(
    doses: Union[List[float], np.ndarray],
    replicates: Union[List[List[float]], np.ndarray],
    drug_name: str = "Drug_X",
    cell_id: str = "Cell_01",
    n_bootstrap: int = 100,
    random_seed: int = 42
) -> DoseResponseResult:
    """
    Analyse complète d'une courte courbe dose-réponse selon le protocole TLog.
    """
    doses = np.asarray(doses, dtype=float).flatten()
    n_doses = len(doses)

    # Vérification stricte de la longueur
    if n_doses < MIN_DOSE_POINTS or n_doses > MAX_DOSE_POINTS:
        return DoseResponseResult(
            drug_name=drug_name, cell_id=cell_id, n_doses=n_doses, n_replicates=0,
            status="INDÉTERMINÉ", abstention=True,
            abstention_reason=f"Nombre de doses N={n_doses} hors plage admissible [{MIN_DOSE_POINTS}, {MAX_DOSE_POINTS}]",
            katz_fd=np.nan, petrosian_fd=np.nan, sevcik_fd=np.nan,
            sample_entropy=np.nan, dfa_exponent=np.nan, n_finite_estimators=0, d_consensus=np.nan,
            t0_dose=np.nan, t0_dose_pct=np.nan, ic50_tlog=np.nan, log_ic50_tlog=np.nan,
            auc_tlog=np.nan, auc_tlog_ci_low=np.nan, auc_tlog_ci_high=np.nan,
            fit_4pl_converged=False, ic50_4pl=np.nan, log_ic50_4pl=np.nan,
            hill_slope_4pl=np.nan, r2_4pl=np.nan, delta_log_ic50=np.nan,
            regime_tlog="INDETERMINATE", monotonicity_flag="UNKNOWN"
        )

    # Mise en forme des réplicats (R x N)
    rep_arr = np.asarray(replicates, dtype=float)
    if rep_arr.ndim == 1:
        rep_arr = rep_arr.reshape(1, n_doses)
    n_replicates = rep_arr.shape[0]

    # Profil moyen biologique
    mean_response = np.mean(rep_arr, axis=0)

    # 1. Calcul des 5 estimateurs de complexité sur le profil moyen
    comp_profile = compute_short_complexity_profile(mean_response)
    k_fd = comp_profile["Katz"]
    p_fd = comp_profile["Petrosian"]
    s_fd = comp_profile["Sevcik"]
    se_val = comp_profile["SampleEn"]
    dfa_val = comp_profile["DFA"]

    finite_list = [v for v in [k_fd, p_fd, s_fd, se_val, dfa_val] if np.isfinite(v)]
    n_finite = len(finite_list)
    d_cons = float(np.median(finite_list)) if n_finite > 0 else np.nan

    # RÈGLE D'ABSTENTION OBLIGATOIRE : si < 3 estimateurs finis -> INDÉTERMINÉ
    if n_finite < MIN_FINITE_ESTIMATORS:
        return DoseResponseResult(
            drug_name=drug_name, cell_id=cell_id, n_doses=n_doses, n_replicates=n_replicates,
            status="INDÉTERMINÉ", abstention=True,
            abstention_reason=f"Abstention obligatoire: seulement {n_finite}/5 estimateurs finis (requis >= {MIN_FINITE_ESTIMATORS})",
            katz_fd=k_fd, petrosian_fd=p_fd, sevcik_fd=s_fd,
            sample_entropy=se_val, dfa_exponent=dfa_val, n_finite_estimators=n_finite, d_consensus=d_cons,
            t0_dose=np.nan, t0_dose_pct=np.nan, ic50_tlog=np.nan, log_ic50_tlog=np.nan,
            auc_tlog=np.nan, auc_tlog_ci_low=np.nan, auc_tlog_ci_high=np.nan,
            fit_4pl_converged=False, ic50_4pl=np.nan, log_ic50_4pl=np.nan,
            hill_slope_4pl=np.nan, r2_4pl=np.nan, delta_log_ic50=np.nan,
            regime_tlog="INDETERMINATE", monotonicity_flag="INDETERMINATE"
        )

    # 2. Diagnostic robuste de monotonie et de bruit
    diffs = np.diff(mean_response)
    significant_inversions = 0
    inversion_amplitude = 0.0
    for i in range(len(diffs) - 1):
        if diffs[i] * diffs[i + 1] < 0:
            if abs(diffs[i]) > 0.04 and abs(diffs[i + 1]) > 0.04:
                significant_inversions += 1
                inversion_amplitude += min(abs(diffs[i]), abs(diffs[i + 1]))

    span = float(np.ptp(mean_response))

    if span < 0.12:
        monotonicity_flag = "FLAT"
        regime_tlog = "SATURATION"
    elif significant_inversions >= 2 or (significant_inversions >= 1 and inversion_amplitude > 0.10):
        monotonicity_flag = "NON_MONOTONIC"
        regime_tlog = "PERTURBATION"
    else:
        monotonicity_flag = "MONOTONIC_DECREASING"
        regime_tlog = "CRITICALITY"

    # 3. Calcul AUC TLog et Bootstrap sur les réplicats biologiques
    log_d = np.log10(doses)
    auc_mean = compute_trapezoidal_auc(log_d, mean_response)

    if n_replicates >= 2 and n_bootstrap > 0:
        rng = np.random.RandomState(random_seed)
        boot_aucs = []
        for _ in range(n_bootstrap):
            sampled_idx = rng.choice(n_replicates, size=n_replicates, replace=True)
            boot_mean_curve = np.mean(rep_arr[sampled_idx, :], axis=0)
            boot_aucs.append(compute_trapezoidal_auc(log_d, boot_mean_curve))
        auc_ci_low = float(np.percentile(boot_aucs, 2.5))
        auc_ci_high = float(np.percentile(boot_aucs, 97.5))
    else:
        auc_ci_low = auc_mean
        auc_ci_high = auc_mean

    # 4. Calcul T0_dose et IC50_tlog
    t0_val, log_t0, t0_pct, _ = compute_t0_dose(doses, mean_response)
    ic50_tlog_val, log_ic50_tlog, _ = compute_ic50_tlog(doses, mean_response)

    # 5. Ajustement 4PL conventionnel pour benchmark
    fit_res = fit_4pl_sigmoid(doses, mean_response)
    ic50_4pl_val = fit_res["ic50_4pl"]
    log_ic50_4pl_val = fit_res["log_ic50_4pl"]
    fit_conv = fit_res["converged"]
    hill_slope = fit_res["hill_slope"]
    r2_val = fit_res["r2"]

    # Comparaison TLog vs 4PL
    if np.isfinite(log_ic50_tlog) and np.isfinite(log_ic50_4pl_val):
        delta_log = float(abs(log_ic50_tlog - log_ic50_4pl_val))
    else:
        delta_log = np.nan

    # Statut synthétique
    if monotonicity_flag == "FLAT":
        final_status = "RÉSISTANT_PLAT"
    elif monotonicity_flag == "NON_MONOTONE":
        final_status = "NON_MONOTONE"
    else:
        final_status = "VALIDE"

    return DoseResponseResult(
        drug_name=drug_name,
        cell_id=cell_id,
        n_doses=n_doses,
        n_replicates=n_replicates,
        status=final_status,
        abstention=False,
        abstention_reason="",
        katz_fd=k_fd,
        petrosian_fd=p_fd,
        sevcik_fd=s_fd,
        sample_entropy=se_val,
        dfa_exponent=dfa_val,
        n_finite_estimators=n_finite,
        d_consensus=d_cons,
        t0_dose=t0_val,
        t0_dose_pct=t0_pct,
        ic50_tlog=ic50_tlog_val,
        log_ic50_tlog=log_ic50_tlog,
        auc_tlog=auc_mean,
        auc_tlog_ci_low=auc_ci_low,
        auc_tlog_ci_high=auc_ci_high,
        fit_4pl_converged=fit_conv,
        ic50_4pl=ic50_4pl_val,
        log_ic50_4pl=log_ic50_4pl_val,
        hill_slope_4pl=hill_slope,
        r2_4pl=r2_val,
        delta_log_ic50=delta_log,
        regime_tlog=regime_tlog,
        monotonicity_flag=monotonicity_flag
    )


def run_batch_dose_response(
    data_records: List[Dict[str, Any]],
    n_bootstrap: int = 100,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Exécute l'analyse dose-réponse sur une collection d'enregistrements.
    """
    results = []
    for rec in data_records:
        res = analyze_dose_response_curve(
            doses=rec["doses"],
            replicates=rec["replicates"],
            drug_name=rec.get("drug_name", "Unknown"),
            cell_id=rec.get("cell_id", "Unknown"),
            n_bootstrap=n_bootstrap,
            random_seed=random_seed
        )
        results.append(asdict(res))
    return pd.DataFrame(results)


if __name__ == "__main__":
    print(f"UNIVERSAL_LOG_dose_response_v1.py version {VERSION}")
    print("Module de traitement des courtes courbes dose-réponse (N=7..20).")
    print(f"Estimateurs retenus: {', '.join(ROBUST_ESTIMATOR_NAMES)}")
    print(f"Règle d'abstention: < {MIN_FINITE_ESTIMATORS} estimateurs finis -> INDÉTERMINÉ.")
