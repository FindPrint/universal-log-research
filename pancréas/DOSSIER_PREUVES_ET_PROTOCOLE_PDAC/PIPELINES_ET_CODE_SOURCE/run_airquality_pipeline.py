#!/usr/bin/env python
"""Universal Log v6.0.1 - UCI Air Quality Pipeline Runner.

Ce script exécute la rotation complète des 15 axes de contrôle sur le benchmark Air Quality UCI
conformément aux spécifications du README V12 et au protocole du pipeline v6.0.1.

Contraintes respectées :
- Pas de modification du seuil N >= 50 du pipeline
- NMHC(GT) (12 bins valides < 50) est marqué 'insuffisant' (garde-fou v6.0.1)
- Moins de 3 estimateurs finis -> marqué 'indéterminé'
- Pipeline v6.0.1 source intact
- Sauvegarde JSON et CSV complète
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import platform
import sys
import time
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Chemins de référence
HERE = Path(__file__).resolve().parent
WORKSPACE = Path(r"C:\Users\citys\Desktop\10-31-2026")
PIPELINE_PATH = WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
LOCAL_DATA_DIR = HERE / "data"
LOCAL_SOURCE = LOCAL_DATA_DIR / "AirQualityUCI.csv"
INPUT_DIR = HERE / "inputs"
INPUT_CSV = INPUT_DIR / "air_quality_100_time_bins.csv"
RUNS_DIR = HERE / "runs"
RESULTS_DIR = HERE / "results"
STATE_FILE = RESULTS_DIR / "run_state.json"
SUMMARY_CSV = RESULTS_DIR / "airquality_pipeline_summary.csv"
SUMMARY_JSON = RESULTS_DIR / "airquality_pipeline_summary.json"
MANIFEST_JSON = RESULTS_DIR / "campaign_manifest.json"

TARGET = "CO(GT)"
N_BINS = 100
SCENARIOS = 8
SEED_BASE = 20261124
MIN_CONTROL_POINTS = 50
SENTINEL = -200

# 15 contrôles numériques prévus dans README V12
ALL_15_CONTROLS = [
    "CO(GT)",
    "PT08.S1(CO)",
    "NMHC(GT)",
    "C6H6(GT)",
    "PT08.S2(NMHC)",
    "NOx(GT)",
    "PT08.S3(NOx)",
    "NO2(GT)",
    "PT08.S4(NO2)",
    "PT08.S5(O3)",
    "T",
    "RH",
    "AH",
    "time_index_hours",
    "missing_fraction_numeric",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    temp.replace(path)


def locate_or_fetch_source() -> Path:
    """Trouve AirQualityUCI.csv dans le workspace ou le télécharge."""
    if LOCAL_SOURCE.is_file() and LOCAL_SOURCE.stat().st_size > 1000:
        return LOCAL_SOURCE

    candidates = [
        WORKSPACE / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-22" / "DATA_PUBLIC_BENCHMARK_V3_AIR_QUALITY" / "source" / "AirQualityUCI.csv",
        WORKSPACE / "AirQualityUCI.csv",
    ]
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size > 1000:
            LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(candidate, LOCAL_SOURCE)
            print(f"[SOURCE] Copié depuis {candidate} vers {LOCAL_SOURCE}")
            return LOCAL_SOURCE

    # Téléchargement depuis UCI si non trouvé localement
    print("[SOURCE] Données non trouvées localement, téléchargement depuis UCI ML Repository...")
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://archive.ics.uci.edu/static/public/360/air+quality.zip"
    zip_path = LOCAL_DATA_DIR / "air_quality.zip"
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith("AirQualityUCI.csv"):
                with zf.open(member) as src, LOCAL_SOURCE.open("wb") as dst:
                    dst.write(src.read())
                break
    if not LOCAL_SOURCE.is_file():
        raise FileNotFoundError(f"Impossible de récupérer AirQualityUCI.csv depuis {url}")
    print(f"[SOURCE] Téléchargé et extrait vers {LOCAL_SOURCE}")
    return LOCAL_SOURCE


def prepare_binned_input(source_path: Path) -> tuple[Path, dict[str, int], dict[str, float]]:
    """Prépare les 100 bins temporels en excluant -200 (marqué NaN sans imputation)."""
    frame = pd.read_csv(source_path, sep=";", decimal=",", encoding="latin-1")
    frame = frame.loc[:, [c for c in frame.columns if not str(c).startswith("Unnamed:") and frame[c].notna().any()]]
    frame = frame.loc[~frame.isna().all(axis=1)].reset_index(drop=True)

    timestamp = pd.to_datetime(
        frame["Date"].astype(str).str.strip() + " " + frame["Time"].astype(str).str.strip(),
        format="%d/%m/%Y %H.%M.%S",
        errors="raise",
    )
    timestamp_ns = timestamp.astype("datetime64[ns]").astype("int64")
    first_timestamp_ns = int(timestamp_ns.iloc[0])

    numeric_names = [name for name in frame.columns if name not in {"Date", "Time"}]
    numeric = frame[numeric_names].apply(pd.to_numeric, errors="raise").replace(SENTINEL, np.nan)

    groups = np.array_split(np.arange(len(frame)), N_BINS)
    binned_rows = []
    for positions in groups:
        row = numeric.iloc[positions].mean(axis=0, skipna=True).to_dict()
        times = timestamp_ns.iloc[positions].to_numpy(dtype=np.int64)
        row["time_index_hours"] = float(((times - first_timestamp_ns) / 3_600_000_000_000).mean())
        raw_block = frame.iloc[positions][numeric_names].apply(pd.to_numeric, errors="coerce")
        row["missing_fraction_numeric"] = float(raw_block.eq(SENTINEL).sum().sum() / raw_block.size)
        binned_rows.append(row)

    binned = pd.DataFrame(binned_rows)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    binned.to_csv(INPUT_CSV, index=False, na_rep="", float_format="%.12g")

    valid_counts = {col: int(binned[col].notna().sum()) for col in ALL_15_CONTROLS}
    missing_pct = {col: float(binned[col].isna().mean()) for col in numeric_names}
    return INPUT_CSV, valid_counts, missing_pct


def load_pipeline_module(no_plots: bool = True):
    """Charge dynamiquement le module pipeline v6.0.1 avec suppression optionnelle des plots."""
    spec = importlib.util.spec_from_file_location("universal_log_v6_0_1_air_quality", PIPELINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger le pipeline : {PIPELINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plot_functions = sorted(name for name, value in vars(module).items() if name.startswith("plot_") and callable(value))
    if no_plots:
        for name in plot_functions:
            setattr(module, name, lambda *args, **kwargs: None)
    return module, plot_functions


def count_finite_estimators(result: dict, output_dir: Path) -> tuple[int, list[str]]:
    """Compte le nombre d'estimateurs ayant produit des valeurs finies pour ce run."""
    # Source 1 : csd_fractal_estimators.csv
    csv_path = output_dir / "csd_fractal_estimators.csv"
    if csv_path.is_file():
        try:
            df_est = pd.read_csv(csv_path)
            if "status" in df_est.columns and "estimator" in df_est.columns:
                computed_df = df_est[df_est["status"] == "computed"]
                computed_names = sorted(computed_df["estimator"].dropna().unique().tolist())
                return len(computed_names), computed_names
        except Exception:
            pass

    # Source 2 : df_feat.csv
    feat_path = output_dir / "df_feat.csv"
    if feat_path.is_file():
        try:
            df_feat = pd.read_csv(feat_path)
            # colonnes numériques avec au moins une valeur finie
            numeric_cols = [c for c in df_feat.columns if np.issubdtype(df_feat[c].dtype, np.number) and df_feat[c].notna().sum() > 0]
            return len(numeric_cols), numeric_cols
        except Exception:
            pass

    # Source 3 : metadata / holographic_tension_state
    holographic = result.get("holographic_tension_state", {}) or {}
    per_est = (holographic.get("per_estimator", {}) or {})
    finite_from_holo = [k for k, v in per_est.items() if isinstance(v, dict) and v.get("raw_median") is not None]
    if finite_from_holo:
        return len(finite_from_holo), sorted(finite_from_holo)

    return 0, []


def execute_single_control(task_dict: dict) -> dict:
    """Exécute un run de pipeline pour un axe de contrôle donné (adapté au parallélisme)."""
    key = task_dict["run_key"]
    control = task_dict["control"]
    seed = task_dict["seed"]
    valid_bins = task_dict["valid_bins"]
    input_csv = Path(task_dict["input_csv"])
    no_plots = task_dict["no_plots"]

    result_dir = RUNS_DIR / key
    output_dir = result_dir / "pipeline_output"
    result_path = result_dir / "pipeline_result.json"
    log_path = result_dir / "pipeline.log"
    result_dir.mkdir(parents=True, exist_ok=True)

    # Reprise sur cache si déjà complété
    if result_path.is_file():
        try:
            cached_data = json.loads(result_path.read_text(encoding="utf-8"))
            cached_summary = cached_data.get("summary", cached_data)
            if cached_summary.get("status") in {"complete", "insuffisant", "indéterminé"}:
                print(f"[REPRIS/CACHE] {control:25s} | Statut: {cached_summary.get('status')} | T0: {cached_summary.get('t0_pct')}", flush=True)
                return cached_summary
        except Exception:
            pass

    # Règle N >= 50 et cas NMHC(GT)
    if valid_bins < MIN_CONTROL_POINTS or control == "NMHC(GT)":
        record = {
            "run_key": key,
            "control": control,
            "seed": seed,
            "status": "insuffisant",
            "reason": f"Points de contrôle valides ({valid_bins}) < {MIN_CONTROL_POINTS} (seuil de support minimal v6.0.1)",
            "valid_bins": valid_bins,
            "target_requested": TARGET,
            "target_used": TARGET,
            "target_fallback_used": False,
            "target_fallback_reason": None,
            "diagonal_control_requested": control == TARGET,
            "control_monotone": None,
            "control_direction": None,
            "t0_status": "unavailable",
            "t0_pct": None,
            "t0_raw_control_value": None,
            "t0_raw_control_ambiguous": None,
            "analysis_flux_count": None,
            "control_excluded_from_analysis_fluxes": True,
            "finite_estimators_count": 0,
            "finite_estimators_names": [],
            "dominant_regime": "indeterminate",
            "pipeline_elapsed_seconds": 0.0,
            "pipeline_version": "v6.0.1",
        }
        result_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with log_path.open("w", encoding="utf-8") as f:
            f.write(f"Contrôle {control} ignoré : support insuffisant ({valid_bins} bins valides < {MIN_CONTROL_POINTS})\n")
        return record

    module, _ = load_pipeline_module(no_plots=no_plots)
    config = {
        "csv_path": str(input_csv),
        "target_col": TARGET,
        "control_col": control,
        "control_mode": "single",
        "target_policy": "fixed",
        "domain": "generic",
        "mode": "fast",
        "n_scenarios": SCENARIOS,
        "seed": seed,
        "output_dir": str(output_dir),
        "max_workers": 1,
        "harmonic_validation": False,
        "l7b_mode": "light",
    }

    started = time.perf_counter()
    try:
        with log_path.open("w", encoding="utf-8") as log_f, contextlib.redirect_stdout(log_f), contextlib.redirect_stderr(log_f):
            result = module.run_full_unified_pipeline(**config)
        elapsed = time.perf_counter() - started

        meta = result.get("metadata", {}) or {}
        core = result.get("run_pipeline", {}) or {}
        threshold = core.get("threshold_metadata", {}) or {}
        t0 = (meta.get("thresholds_in_control_units", {}) or {}).get("T_0_Monte_Carlo_Central", {}) or {}
        global_stats = meta.get("global_flux_stats", {}) or {}
        mono = meta.get("control_monotonicity", {}) or {}
        if not isinstance(mono, dict):
            mono = {}
        holo = result.get("holographic_tension_state", {}) or {}
        regime = holo.get("dominant_regime") or "indeterminate"

        n_finite, finite_names = count_finite_estimators(result, output_dir)

        # Statut : si moins de 3 estimateurs finis -> indéterminé
        if n_finite < 3:
            status = "indéterminé"
            status_reason = f"Moins de 3 estimateurs finis ({n_finite} trouvés)"
        else:
            status = "complete"
            status_reason = "Exécution réussie avec consensus d'estimateurs"

        record = {
            "run_key": key,
            "control": control,
            "seed": seed,
            "status": status,
            "status_reason": status_reason,
            "target_requested": meta.get("target_requested", TARGET),
            "target_used": meta.get("target_used", TARGET),
            "target_fallback_used": meta.get("target_fallback_used", False),
            "target_fallback_reason": meta.get("target_fallback_reason"),
            "diagonal_control_requested": control == TARGET,
            "valid_bins": valid_bins,
            "n_samples": meta.get("n_samples", valid_bins),
            "control_monotone": mono.get("monotone"),
            "control_direction": mono.get("direction"),
            "t0_status": threshold.get("threshold_status", "available"),
            "t0_pct": t0.get("threshold_pct"),
            "t0_raw_control_value": t0.get("control_value_raw"),
            "t0_raw_control_ambiguous": t0.get("ambiguous"),
            "analysis_flux_count": len(global_stats),
            "control_excluded_from_analysis_fluxes": control not in global_stats,
            "finite_estimators_count": n_finite,
            "finite_estimators_names": finite_names,
            "dominant_regime": regime,
            "pipeline_elapsed_seconds": elapsed,
            "pipeline_version": result.get("version", "v6.0.1"),
        }
        result_payload = {
            "summary": record,
            "result": result,
            "configuration": {k: v for k, v in config.items() if k not in {"csv_path", "output_dir"}},
        }
        result_path.write_text(json.dumps(result_payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        return record

    except ValueError as exc:
        elapsed = time.perf_counter() - started
        is_short = "Série trop courte" in str(exc)
        record = {
            "run_key": key,
            "control": control,
            "seed": seed,
            "status": "insuffisant" if is_short else "error",
            "reason": str(exc),
            "valid_bins": valid_bins,
            "target_requested": TARGET,
            "target_used": TARGET,
            "target_fallback_used": False,
            "target_fallback_reason": None,
            "diagonal_control_requested": control == TARGET,
            "control_monotone": None,
            "control_direction": None,
            "t0_status": "unavailable",
            "t0_pct": None,
            "t0_raw_control_value": None,
            "t0_raw_control_ambiguous": None,
            "analysis_flux_count": None,
            "control_excluded_from_analysis_fluxes": True,
            "finite_estimators_count": 0,
            "finite_estimators_names": [],
            "dominant_regime": "indeterminate",
            "pipeline_elapsed_seconds": elapsed,
            "pipeline_version": "v6.0.1",
        }
        result_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return record

    except Exception as exc:
        elapsed = time.perf_counter() - started
        record = {
            "run_key": key,
            "control": control,
            "seed": seed,
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
            "valid_bins": valid_bins,
            "target_requested": TARGET,
            "target_used": TARGET,
            "target_fallback_used": False,
            "target_fallback_reason": None,
            "diagonal_control_requested": control == TARGET,
            "control_monotone": None,
            "control_direction": None,
            "t0_status": "error",
            "t0_pct": None,
            "t0_raw_control_value": None,
            "t0_raw_control_ambiguous": None,
            "analysis_flux_count": None,
            "control_excluded_from_analysis_fluxes": True,
            "finite_estimators_count": 0,
            "finite_estimators_names": [],
            "dominant_regime": "indeterminate",
            "pipeline_elapsed_seconds": elapsed,
            "pipeline_version": "v6.0.1",
        }
        result_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Log v6.0.1 - UCI Air Quality Rotation")
    parser.add_argument("--workers", type=int, default=4, help="Nombre de processus concurrents pour les 15 contrôles (défaut: 4)")
    parser.add_argument("--with-plots", action="store_true", help="Activer la génération des graphiques matplotlib")
    parser.add_argument("--max-runs", type=int, default=None, help="Limiter le nombre de contrôles exécutés")
    args = parser.parse_args()

    print("=" * 80)
    print("UNIVERSAL_LOG v6.0.1 — CAMPAGNE UCI AIR QUALITY (15 CONTRÔLES)")
    print("=" * 80)

    # 1. Source et préparation
    source_csv = locate_or_fetch_source()
    print(f"✓ Source localisée : {source_csv} ({source_csv.stat().st_size:,} octets)")

    input_csv, valid_counts, missing_rates = prepare_binned_input(source_csv)
    print(f"✓ Entrée binnée préparée : {input_csv} (100 bins)")
    for col, count in valid_counts.items():
        print(f"  - {col:25s} : {count} bins valides")

    # 2. Planification des 15 tâches
    tasks = []
    for i, ctrl in enumerate(ALL_15_CONTROLS):
        safe_name = ctrl.replace(" ", "_").replace("/", "_").replace(".", "_")
        key = f"control_{i+1:02d}_{safe_name}"
        seed = SEED_BASE + i * 100
        tasks.append({
            "run_key": key,
            "control": ctrl,
            "seed": seed,
            "valid_bins": valid_counts[ctrl],
            "input_csv": str(input_csv),
            "no_plots": not args.with_plots,
        })

    if args.max_runs is not None:
        tasks = tasks[:args.max_runs]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Exécution (parallèle ou séquentielle)
    records = []
    start_total = time.perf_counter()

    print(f"\nLancement de {len(tasks)} contrôles avec {args.workers} workers concurrents...")
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            future_to_task = {executor.submit(execute_single_control, t): t for t in tasks}
            for future in as_completed(future_to_task):
                t = future_to_task[future]
                try:
                    res = future.result()
                    records.append(res)
                    print(f"[{res['status'].upper()}] {res['control']:25s} | T0: {str(res['t0_pct']):10s} | Est: {res['finite_estimators_count']:2d} | Durée: {res['pipeline_elapsed_seconds']:.1f}s")
                except Exception as exc:
                    print(f"[FAIL] {t['control']}: {exc}")
    else:
        for t in tasks:
            res = execute_single_control(t)
            records.append(res)
            print(f"[{res['status'].upper()}] {res['control']:25s} | T0: {str(res['t0_pct']):10s} | Est: {res['finite_estimators_count']:2d} | Durée: {res['pipeline_elapsed_seconds']:.1f}s")

    total_elapsed = time.perf_counter() - start_total
    print(f"\n✓ Tous les contrôles terminés en {total_elapsed:.1f} s ({total_elapsed/60:.2f} min)")

    # 4. Ordonner selon l'ordre initial des contrôles
    order_dict = {ctrl: i for i, ctrl in enumerate(ALL_15_CONTROLS)}
    records.sort(key=lambda r: order_dict.get(r["control"], 999))

    # 5. Sauvegarde CSV et JSON
    summary_df = pd.DataFrame(records)
    summary_df.to_csv(SUMMARY_CSV, index=False)
    write_json(SUMMARY_JSON, records)

    manifest = {
        "title": "UCI Air Quality Pipeline v6.0.1 Control Rotation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_controls_planned": len(tasks),
        "total_elapsed_seconds": total_elapsed,
        "completed_count": sum(1 for r in records if r["status"] == "complete"),
        "insufficient_count": sum(1 for r in records if r["status"] == "insuffisant"),
        "indeterminate_count": sum(1 for r in records if r["status"] == "indéterminé"),
        "error_count": sum(1 for r in records if r["status"] == "error"),
        "source_sha256": sha256_file(source_csv),
        "input_binned_sha256": sha256_file(input_csv),
        "pipeline_source_sha256": sha256_file(PIPELINE_PATH),
        "runner_script_sha256": sha256_file(Path(__file__).resolve()),
        "summary_csv": str(SUMMARY_CSV.relative_to(HERE)),
        "summary_json": str(SUMMARY_JSON.relative_to(HERE)),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    write_json(MANIFEST_JSON, manifest)
    print(f"✓ Synthèse sauvegardée : {SUMMARY_CSV}")
    print(f"✓ Manifeste sauvegardé : {MANIFEST_JSON}")


if __name__ == "__main__":
    main()
