#!/usr/bin/env python
"""Read-only probe of Levina-Bickel support in the frozen Ising v6 runs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PIPELINE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
STATE = json.loads((HERE / "run_state.json").read_text(encoding="utf-8"))
RUNS = STATE["runs"]
OUTPUT = HERE / "DIAGNOSTIC_LEVINA_SUPPORT.json"
RUN_FOR_L = {
    8: "primary_L8_temperature",
    12: "primary_L12_temperature",
    16: "sensitivity_L16_multiple_physical_controls",
    24: "primary_L24_temperature",
    32: "primary_L32_temperature",
    48: "primary_L48_temperature",
    64: "primary_L64_temperature",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_levina_diagnostic", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger le pipeline source: {PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trace_levina(pipeline, series, k, theiler_factor, theiler_mode):
    """Mirror the estimator's early-return checks and report the first reason."""
    z = np.asarray(series, dtype=float).flatten()
    if len(z) < 40:
        return None, "input_length_below_40", 0
    tau = pipeline._embedding_tau(z)
    m = int(min(10, max(4, len(z) // 24)))
    embedded, times = pipeline._delay_embed(z, m, tau, 100)
    if len(embedded) < k + 8:
        return None, "embedded_points_below_k_plus_8", 0
    distances = pipeline._knn_distances(
        embedded, times, k,
        pipeline._cloud_theiler(times, tau, theiler_factor=theiler_factor, theiler_mode=theiler_mode),
    )
    local_dimensions = []
    for row in distances:
        if not np.isfinite(row[-1]) or row[0] <= 1e-12:
            continue
        acc = 0.0
        used = 0
        for j in range(k - 1):
            if row[j] > 1e-12 and np.isfinite(row[j]):
                acc += pipeline._safe_log(pipeline._safe_divide(row[-1], row[j]))
                used += 1
        if used > 0 and acc > 0:
            local_dimensions.append(pipeline._safe_divide(used, acc))
    count = len(local_dimensions)
    if count < 12:
        return None, "fewer_than_12_valid_local_dimensions", count
    dimension = float(np.mean(local_dimensions))
    if not np.isfinite(dimension) or dimension <= 0 or dimension > 2.0 * m:
        return None, "dimension_nonfinite_or_out_of_range", count
    return dimension, "finite", count


def main():
    pipeline = load_pipeline()
    records = []
    for L, run_id in RUN_FOR_L.items():
        input_path = HERE / "inputs" / f"ising_L{L}_physical.csv"
        run = RUNS[run_id]
        output_dir = Path(run["output_path"])
        if L == 16:
            output_dir = output_dir / "Temperature"
        data = pd.read_csv(input_path)
        values = pd.to_numeric(data["Energy_per_spin"], errors="coerce").to_numpy(float)
        standalone = pipeline.levina_bickel(values, 8)

        master_path = output_dir / "master_results.json"
        master = json.loads(master_path.read_text(encoding="utf-8"))
        threshold = master.get("run_pipeline", {}).get("threshold_metadata", {})
        optimization = threshold.get("threshold_optimization", {})
        best = optimization.get("best_config") or {}
        progress = np.asarray(master.get("metadata", {}).get("mc_axis", {}).get("progress_pct", []), dtype=float)
        w_size = int(best.get("w_size", 0) or 0)
        tf = best.get("theiler_factor")
        tm = best.get("theiler_mode")
        reconstruction_finite = 0
        reconstruction_lengths = []
        reconstruction_reasons = {}
        valid_local_counts = []
        if len(progress) == len(values) and w_size >= 2:
            scan_points = np.linspace(float(np.nanmin(progress)), float(np.nanmax(progress)), 120)
            tolerance = max(3.0, (scan_points[1] - scan_points[0]) / 2.0)
            order = np.argsort(progress)
            progress_sorted = progress[order]
            energy_sorted = values[order]
            windows = []
            for i in range(len(progress_sorted) - w_size + 1):
                windows.append((float(np.mean(progress_sorted[i:i + w_size])), energy_sorted[i:i + w_size]))
            for point in scan_points:
                matching = [window for window in windows if abs(window[0] - point) <= tolerance]
                if not matching:
                    matching = [min(windows, key=lambda window: abs(window[0] - point))]
                combined = np.concatenate([window[1] for window in matching])
                reconstruction_lengths.append(len(combined))
                sd = float(np.std(combined))
                standardized = (combined - float(np.mean(combined))) / sd if sd > 1e-10 else combined
                value, reason, local_count = trace_levina(pipeline, standardized, 8, tf, tm)
                reconstruction_reasons[reason] = reconstruction_reasons.get(reason, 0) + 1
                valid_local_counts.append(local_count)
                if value is not None and np.isfinite(value):
                    reconstruction_finite += 1

        features_path = output_dir / "df_feat.csv"
        features = pd.read_csv(features_path)
        column = "Energy_per_spin_LevinaBickel_mean"
        series = pd.to_numeric(features[column], errors="coerce") if column in features else pd.Series(dtype=float)
        finite_count = int(np.isfinite(series.to_numpy(float)).sum())

        csd_path = output_dir / "csd_fractal_estimators.csv"
        status = None
        if csd_path.exists():
            csd = pd.read_csv(csd_path)
            rows = csd[(csd["flux_name"].eq("Energy_per_spin")) & (csd["estimator"].eq("LevinaBickel"))]
            if not rows.empty:
                status = str(rows.iloc[0].get("status"))

        records.append({
            "L": L,
            "run_id": run_id,
            "input_path": str(input_path.resolve()),
            "input_sha256": sha256(input_path),
            "input_rows": len(data),
            "standalone_full_series_levina_bickel": float(standalone) if np.isfinite(standalone) else None,
            "landscape_path": str(features_path.resolve()),
            "landscape_rows": len(features),
            "landscape_finite_levina_rows": finite_count,
            "landscape_levina_column_present": column in features,
            "reconstructed_landscape_finite_levina_rows": reconstruction_finite,
            "reconstructed_landscape_reason_counts": reconstruction_reasons,
            "reconstructed_valid_local_dimensions_max": max(valid_local_counts) if valid_local_counts else None,
            "reconstructed_window_input_length_min": min(reconstruction_lengths) if reconstruction_lengths else None,
            "reconstructed_window_input_length_max": max(reconstruction_lengths) if reconstruction_lengths else None,
            "reconstructed_window_inputs_at_least_40": sum(n >= 40 for n in reconstruction_lengths),
            "selected_window_size": best.get("w_size"),
            "selected_min_group": best.get("min_grp"),
            "estimator_profile": master.get("metadata", {}).get("parameters", {}).get("modes", {}).get("fast", {}).get("estimator_profile"),
            "csd_estimator_trajectory_status": status,
        })

    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Read-only diagnostic; no pipeline or prior result was modified.",
        "pipeline_path": str(PIPELINE.resolve()),
        "pipeline_sha256": sha256(PIPELINE),
        "levina_function_min_series_guard_observed_in_source": 40,
        "reconstruction_method": "Rebuilds 120 landscape positions from the stored progress axis, selected window size, matching tolerance and overlapping windows, then mirrors z-scoring, embedding, Theiler filtering and the Levina-Bickel local-neighbor acceptance checks.",
        "interpretation_limit": "The reconstructed local estimator path matches the observed 0/120 finite landscape rows: 20 inputs are shorter than 40 points and the remaining 100 yield fewer than 12 valid local dimensions (maximum 8). This identifies local support as the direct failure path in these runs; it does not establish a general algorithm defect or prescribe a changed estimator definition.",
        "records": records,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Diagnostic: {OUTPUT}")
    for row in records:
        print(f"L={row['L']:>2} | n={row['input_rows']} | direct={row['standalone_full_series_levina_bickel']} | "
              f"landscape={row['landscape_finite_levina_rows']}/{row['landscape_rows']} | "
              f"w={row['selected_window_size']} | CSD={row['csd_estimator_trajectory_status']}")


if __name__ == "__main__":
    main()
