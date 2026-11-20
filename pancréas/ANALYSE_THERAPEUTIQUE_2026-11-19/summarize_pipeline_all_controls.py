from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path


ANALYSIS = Path(__file__).resolve().parent
ROOT = ANALYSIS.parents[1]
RUN_DIR = ANALYSIS / "pipeline_runs_parallel15" / "PC69_target_basal"
PIPELINE = ROOT / "UNIVERSAL_LOG_v5.9.4.py"
INPUT = ANALYSIS / "pipeline_inputs_balanced_15" / "GSE271300_PC69_balanced15_multiflux.csv"
INPUT_MANIFEST = ANALYSIS / "pipeline_inputs_balanced_15" / "BALANCED15_PIPELINE_INPUT_MANIFEST.json"
OUTPUT_CSV = RUN_DIR / "ALL_CONTROLS_SUMMARY.csv"
OUTPUT_JSON = RUN_DIR / "ALL_CONTROLS_SUMMARY.json"
OUTPUT_MD = RUN_DIR / "ALL_CONTROLS_SUMMARY.md"
OUTPUT_AUDIT = RUN_DIR / "ALL_CONTROLS_AUDIT_MANIFEST.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value):
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    return value


def at(obj, *keys, default=None):
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key)
    return default if obj is None else obj


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def one_run(control: str, expected: dict) -> dict:
    folder = RUN_DIR / control
    status_path = folder / "run_status.json"
    master_path = folder / "master_results.json"
    console_path = folder / "console.log"
    status = load_json(status_path)
    master = load_json(master_path)
    metadata = master.get("metadata", {})
    monotonicity = metadata.get("control_monotonicity", {}) or {}
    cascade = master.get("five_threshold_cascade", {}) or {}
    thresholds = metadata.get("thresholds_in_control_units", {}) or {}
    t0_raw = thresholds.get("T_0_Monte_Carlo_Central", {}) or {}
    prediction = master.get("prediction_levels", {}) or {}
    l1 = prediction.get("L1_L2_target", {}) or {}
    validation = l1.get("validation", {}) or {}
    walk = l1.get("walk_forward", {}) or {}
    l7a = prediction.get("L7a_coherence", {}) or {}
    l7b = prediction.get("L7b_robustesse", {}) or {}
    predictive_mc = l1.get("predictive_mc_complexity", {}) or {}
    noise = at(master, "run_pipeline", "noise_diagnostic", default={}) or {}
    noise_diags = noise.get("all_flux_diagnostics", []) or []
    component_keys = ("q5", "correlation", "memory", "spectral")
    component_counts = {
        key: sum(1 for diag in noise_diags if (diag.get("component_availability", {}) or {}).get(key) is True)
        for key in component_keys
    }
    coverage_values = [
        float(diag["score_coverage"]) for diag in noise_diags
        if isinstance(diag.get("score_coverage"), (int, float)) and math.isfinite(float(diag["score_coverage"]))
    ]
    tension = master.get("holographic_tension_state", {}) or {}
    footprint = master.get("instrumental_tool_footprint", {}) or {}
    early = master.get("early_warning_alert", {}) or {}
    fallback_raw = metadata.get("target_fallback_used")
    if isinstance(fallback_raw, str):
        fallback_used = fallback_raw.strip().lower() in {"true", "1", "yes"}
    else:
        fallback_used = bool(fallback_raw)

    console = console_path.read_text(encoding="utf-8", errors="replace")
    warning_lines = [
        line.strip() for line in console.splitlines()
        if ("WARNING" in line or "[AVERTISSEMENT" in line or "[ERREUR" in line)
    ]
    t0_pct = cascade.get("T_0_Monte_Carlo_Central")
    row = {
        "control": control,
        "status": status.get("status"),
        "exit_code": status.get("exit_code"),
        "elapsed_seconds": status.get("elapsed_seconds"),
        "n_samples": metadata.get("n_samples"),
        "target_requested": metadata.get("target_requested"),
        "target_used": metadata.get("target_used"),
        "target_fallback_used": fallback_used,
        "target_fallback_reason": metadata.get("target_fallback_reason"),
        "control_direction": monotonicity.get("direction"),
        "control_monotone": monotonicity.get("monotone"),
        "control_constant": monotonicity.get("constant"),
        "control_spearman_r": monotonicity.get("spearman_order_vs_value_r"),
        "control_spearman_p": monotonicity.get("spearman_p"),
        "cascade_status": cascade.get("status"),
        "T0_pct": t0_pct,
        "T0_control_raw": t0_raw.get("control_value_raw"),
        "T0_control_raw_median_near": t0_raw.get("control_value_raw_median_near"),
        "T0_control_raw_min_near": t0_raw.get("control_value_raw_min_near"),
        "T0_control_raw_max_near": t0_raw.get("control_value_raw_max_near"),
        "T0_control_raw_spread_near": t0_raw.get("control_value_raw_spread_near"),
        "T0_ambiguous": t0_raw.get("ambiguous"),
        "Tminus2_pct": at(cascade, "T_-2_F2_pre_onset"),
        "Tminus1_pct": at(cascade, "T_-1_F1_pre_inflection"),
        "Tplus1_pct": at(cascade, "T_+1_F1_post_deceleration"),
        "Tplus2_pct": at(cascade, "T_+2_F2_post_attractor"),
        "max_F1_velocity": cascade.get("max_F1_velocity"),
        "max_F2_curvature": cascade.get("max_F2_curvature"),
        "noise_status": noise.get("status"),
        "noise_label": noise.get("diagnostic_label"),
        "noise_flux_diagnostic_count": len(noise_diags),
        "noise_complete_score_count": noise.get("n_complete_scores"),
        "noise_partial_diagnostic_count": noise.get("n_partial_diagnostics"),
        "noise_q5_available_flux_count": component_counts["q5"],
        "noise_correlation_available_flux_count": component_counts["correlation"],
        "noise_memory_available_flux_count": component_counts["memory"],
        "noise_spectral_available_flux_count": component_counts["spectral"],
        "noise_score_coverage_median": statistics.median(coverage_values) if coverage_values else None,
        "instrumental_tool_footprint": footprint.get("has_tool_footprint"),
        "instrumental_discrete_levels": footprint.get("discrete_levels_count"),
        "holographic_status": tension.get("status"),
        "Delta_tension": tension.get("Delta_tension"),
        "dominant_regime": tension.get("dominant_regime"),
        "regime_is_physical_call": tension.get("regime_is_physical_call"),
        "early_warning_status": early.get("status"),
        "L1_direction": l1.get("direction"),
        "L1_relative_change": l1.get("relative_change"),
        "L1_confidence": l1.get("confidence"),
        "L1_R2": validation.get("r2"),
        "L1_directional_accuracy_pct": validation.get("directional_accuracy"),
        "predictive_mc_status": predictive_mc.get("status"),
        "predictive_mc_method": predictive_mc.get("method"),
        "predictive_mc_n_scenarios": predictive_mc.get("n_scenarios"),
        "predictive_mc_n_estimators_requested": predictive_mc.get("n_estimators_requested"),
        "predictive_mc_estimator_profile": predictive_mc.get("estimator_profile"),
        "walk_forward_status": walk.get("status"),
        "walk_forward_n_folds": walk.get("n_folds"),
        "walk_forward_mean_RMSE": walk.get("mean_rmse"),
        "walk_forward_mean_MAE": walk.get("mean_mae"),
        "walk_forward_directional_accuracy_pct": walk.get("directional_accuracy_pct"),
        "L7a_status": l7a.get("status"),
        "L7a_consensus_direction": l7a.get("consensus_direction"),
        "L7a_global_confidence": l7a.get("global_confidence"),
        "L7b_mode": l7b.get("mode"),
        "L7b_status": l7b.get("status"),
        "requested_target_control_diagonal": str(metadata.get("target_requested")) == control,
        "used_target_control_diagonal": str(metadata.get("target_used")) == control,
        "tension_null_significant_nonlinearity": at(tension, "falsification_vs_null", "is_significant_nonlinearity"),
        "console_warning_count": len(warning_lines),
        "master_results_path": str(master_path),
    }
    row = {key: finite(value) for key, value in row.items()}
    expected_files = set(status.get("output_files", []))
    actual_files = {
        path.name for path in folder.iterdir()
        if path.is_file() and path.name not in {"run_status.json", "console.log"}
    }
    row["status_file_matches_output_inventory"] = expected_files == actual_files
    row["expected_output_files"] = len(expected_files)
    row["actual_output_files"] = len(actual_files)
    row["warnings"] = warning_lines
    return row


def main() -> None:
    progress_path = RUN_DIR / "RUN_PROGRESS.json"
    summary_path = RUN_DIR / "RUN_SUMMARY.json"
    progress = load_json(progress_path)
    summary = load_json(summary_path)
    controls = progress.get("controls_from_numeric_csv_columns", [])
    rows = [one_run(control, progress) for control in controls]

    fields = [key for key in rows[0] if key != "warnings"]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    completed = [row for row in rows if row["status"] == "completed" and row["exit_code"] == 0]
    durations = [float(row["elapsed_seconds"]) for row in completed if row.get("elapsed_seconds") is not None]
    input_header = []
    with INPUT.open("r", newline="", encoding="utf-8-sig") as handle:
        input_header = next(csv.reader(handle))
    input_manifest = load_json(INPUT_MANIFEST)
    pc69_record = next(item for item in input_manifest["records"] if item["model"] == "PC69")
    verified_expected_counts = all(row["status_file_matches_output_inventory"] for row in rows)
    raw_result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "One fixed target (CellState_basal), every numeric CSV column tested in turn as control.",
        "pipeline": str(PIPELINE),
        "pipeline_sha256": progress.get("pipeline_sha256"),
        "input": str(INPUT),
        "input_sha256": progress.get("input_sha256"),
        "input_rows": pc69_record.get("rows_selected"),
        "input_header": input_header,
        "target": "CellState_basal",
        "controls_requested": controls,
        "run_configuration": {
            "control_mode_per_process": "single",
            "target_mode": "fixed",
            "domain": "pdac",
            "mode": "fast",
            "statistical_test": "cohen_d",
            "seed": progress.get("seed"),
            "parallel_processes": progress.get("max_parallel_processes"),
            "l7b": "disabled by --no-l7b",
            "harmonic_validation": "disabled by --no-harmonic-validation",
            "dashboard": "disabled by --no-dashboard",
            "plots": "disabled by --no-plots",
            "telemetry": "disabled by --no-telemetry",
            "adaptive_walk_forward": "disabled by --no-adaptive-walk-forward",
            "regime_weights": "disabled by --no-regime-weights",
            "triangulation": "implicit pipeline default; option omitted",
        },
        "sampling_design": {
            "purpose": pc69_record.get("purpose", input_manifest.get("purpose")),
            "selection": pc69_record.get("selection"),
            "grouping_key": pc69_record.get("grouping_key"),
            "groups": pc69_record.get("groups"),
            "time_or_progress_column_in_csv": any(
                name.lower() in {"time", "timestamp", "progress", "timepoint", "day"}
                for name in input_header
            ),
            "notes": [
                "The PC69 balanced input contains 90 cells, 15 sampled from each of six animal groups.",
                "Animal_ID is text metadata; the 90 cells are not 90 independent biological replicates.",
                "The input contains no time/progress field. The pipeline produces a percentage axis internally; it is not an observed disease-time axis.",
            ],
        },
        "run_summary_status": summary.get("status"),
        "progress_status": progress.get("status"),
        "requested_control_count": len(controls),
        "completed_exit_zero_count": len(completed),
        "failed_or_incomplete_controls": [
            row["control"] for row in rows
            if not (row["status"] == "completed" and row["exit_code"] == 0)
        ],
        "output_inventory_matches_run_status_for_every_control": verified_expected_counts,
        "duration_seconds": {
            "min": min(durations) if durations else None,
            "median": statistics.median(durations) if durations else None,
            "mean": statistics.mean(durations) if durations else None,
            "max": max(durations) if durations else None,
            "sum_parallel_wall_work": sum(durations),
        },
        "rows": rows,
    }
    stats = raw_result["duration_seconds"]
    numeric = lambda key: [float(row[key]) for row in rows if row.get(key) is not None]
    aggregate_observed = {
        "all_controls_non_monotone_count": sum(row.get("control_direction") == "non_monotone" for row in rows),
        "all_t0_raw_ambiguous_count": sum(row.get("T0_ambiguous") is True for row in rows),
        "t0_pct_min": min(numeric("T0_pct")) if numeric("T0_pct") else None,
        "t0_pct_max": max(numeric("T0_pct")) if numeric("T0_pct") else None,
        "noise_scores_unavailable_count": sum(row.get("noise_status") == "scores_unavailable" for row in rows),
        "noise_complete_score_total": sum(int(row.get("noise_complete_score_count") or 0) for row in rows),
        "noise_partial_diagnostics_total": sum(int(row.get("noise_partial_diagnostic_count") or 0) for row in rows),
        "predictive_mc_completed_count": sum(row.get("predictive_mc_status") == "completed" for row in rows),
        "predictive_mc_scenarios_values": sorted(set(row.get("predictive_mc_n_scenarios") for row in rows)),
        "predictive_mc_estimators_values": sorted(set(row.get("predictive_mc_n_estimators_requested") for row in rows)),
        "L7b_disabled_count": sum(row.get("L7b_status") == "disabled" for row in rows),
        "L1_negative_R2_count": sum(float(row["L1_R2"]) < 0 for row in rows if row.get("L1_R2") is not None),
        "L1_R2_min": min(numeric("L1_R2")) if numeric("L1_R2") else None,
        "L1_R2_max": max(numeric("L1_R2")) if numeric("L1_R2") else None,
        "L1_directional_accuracy_min": min(numeric("L1_directional_accuracy_pct")) if numeric("L1_directional_accuracy_pct") else None,
        "L1_directional_accuracy_max": max(numeric("L1_directional_accuracy_pct")) if numeric("L1_directional_accuracy_pct") else None,
        "holographic_regime_counts": {},
        "tension_null_significant_count": sum(row.get("tension_null_significant_nonlinearity") is True for row in rows),
        "target_diagonal_fallback_controls": [row["control"] for row in rows if row.get("target_fallback_used") is True],
    }
    for row in rows:
        label = row.get("dominant_regime") or "missing"
        aggregate_observed["holographic_regime_counts"][label] = aggregate_observed["holographic_regime_counts"].get(label, 0) + 1
    raw_result["aggregate_observed_pipeline_outputs"] = aggregate_observed

    lines = [
        "# UNIVERSAL_LOG v5.9.4 — exécution PC69 sur tous les contrôles numériques",
        "",
        f"Généré UTC : {raw_result['created_utc']}",
        "",
        "## Protocole exécuté",
        "",
        f"- Cible fixe : `{raw_result['target']}`.",
        f"- Contrôles testés : {len(controls)} colonnes numériques, chacune dans un lancement isolé `--control-mode single`.",
        "- Mode : `fast`, avec Cohen-d; cible fixe, domaine `pdac`, seed 42.",
        "- Le code et l’entrée sont identifiés par SHA-256 dans `ALL_CONTROLS_AUDIT_MANIFEST.json`.",
        "- Les sorties complètes du pipeline sont gardées dans un sous-dossier par contrôle.",
        "",
        "## Contrôle d’exécution",
        "",
        f"- Statut global : `{summary.get('status')}`.",
        f"- Runs terminés avec exit code 0 : {len(completed)}/{len(controls)}.",
        f"- Inventaires déclarés conformes aux fichiers présents : `{verified_expected_counts}`.",
        f"- Durée par run (secondes) : min {stats['min']:.1f}, médiane {stats['median']:.1f}, moyenne {stats['mean']:.1f}, max {stats['max']:.1f}.",
        "",
        "## Résumé mécanique des sorties",
        "",
        "Le CSV joint donne une ligne par colonne de contrôle, avec les cinq seuils, les métriques de dérivée, les statuts diagnostiques, les champs de prédiction et les avertissements consignés par le pipeline. Ce tableau résume les valeurs logicielles; il ne transforme pas à lui seul les sorties en preuve biologique.",
        "",
        "### Résultats logiciels observés",
        "",
        f"- Contrôles non monotones : {aggregate_observed['all_controls_non_monotone_count']}/{len(rows)}; T0 brut marqué ambigu : {aggregate_observed['all_t0_raw_ambiguous_count']}/{len(rows)}.",
        f"- T0 sur l’axe pourcentage interne : {aggregate_observed['t0_pct_min']:.2f} à {aggregate_observed['t0_pct_max']:.2f} pour cent.",
        f"- Diagnostic bruit : `scores_unavailable` dans {aggregate_observed['noise_scores_unavailable_count']}/{len(rows)}; scores complets cumulés = {aggregate_observed['noise_complete_score_total']}, diagnostics partiels cumulés = {aggregate_observed['noise_partial_diagnostics_total']}.",
        f"- Monte-Carlo prédictif : complété dans {aggregate_observed['predictive_mc_completed_count']}/{len(rows)}; scénarios demandés {aggregate_observed['predictive_mc_scenarios_values']}, estimateurs demandés {aggregate_observed['predictive_mc_estimators_values']}.",
        f"- R2 L1 négatif : {aggregate_observed['L1_negative_R2_count']}/{len(rows)}; plage R2 {aggregate_observed['L1_R2_min']:.3f} à {aggregate_observed['L1_R2_max']:.3f}; précision directionnelle rapportée {aggregate_observed['L1_directional_accuracy_min']:.1f} à {aggregate_observed['L1_directional_accuracy_max']:.1f} pour cent.",
        f"- Régimes internes de tension : {aggregate_observed['holographic_regime_counts']}; test interne de non-linéarité significative contre le nul : {aggregate_observed['tension_null_significant_count']}/{len(rows)}.",
        f"- L7b est désactivé dans {aggregate_observed['L7b_disabled_count']}/{len(rows)} runs; il n’y a donc pas d’étiquette de robustesse L7b à rapporter.",
        "",
        "### Interprétation délimitée",
        "",
        "Ces nombres décrivent la sortie du programme sur cet ordre de lignes. Comme l’entrée est une coupe transversale de cellules, échantillonnée puis mélangée, sans colonne de temps/progression, les pourcentages internes ne représentent pas un moment biologique de transition. Les T0 présents ne donnent donc pas un seuil temporel ou thérapeutique du cancer.",
        "",
        "| Contrôle | Exit | Durée (s) | Monotonie | T0 (%) | Ambigu T0 brut | Statut diagnostic bruit | Statut tension | L7a | L7b |",
        "|---|---:|---:|---|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['control']} | {row['exit_code']} | {row['elapsed_seconds']:.1f} | "
            f"{row['control_direction']} | {row['T0_pct'] if row['T0_pct'] is not None else 'NA'} | "
            f"{row['T0_ambiguous']} | {row['noise_status']} | {row['holographic_status']} | "
            f"{row['L7a_status']} | {row['L7b_status']} |"
        )
    lines += [
        "",
        "## Portée et limites de cet essai",
        "",
            "- Le fichier PC69 contient 90 cellules échantillonnées (15 dans chacun de six groupes animaux); les cellules ne remplacent pas les souris comme unités biologiques indépendantes.",
        "- Les lignes ont été sélectionnées puis mélangées selon le manifeste. Le CSV ne contient ni temps ni progression expérimentale observée.",
        "- L’axe en pourcentage créé par le pipeline ne doit donc pas être présenté ici comme le temps d’apparition d’une résistance ou d’une transition tumorale.",
        "- `T0_ambiguous`, la monotonie du contrôle, les avertissements et les désaccords de couches doivent être consultés avec chaque sortie complète, et non remplacés par un seul score.",
        "- L7b a été désactivé pour ces lancements par `--no-l7b`; L7a seul ne constitue pas une validation robuste.",
        "- Ce test exécute le pipeline; il ne teste pas un traitement sur patients, ne démontre pas une guérison et ne constitue pas une validation indépendante de la théorie.",
        "",
        "## Fichiers d’audit",
        "",
        f"- `{OUTPUT_CSV.name}` — table des 17 contrôles.",
        f"- `{OUTPUT_JSON.name}` — même synthèse en JSON, avec commandes, statuts et avertissements.",
        f"- `{OUTPUT_AUDIT.name}` — SHA-256 de chaque fichier de sortie, ainsi que du code et de l’entrée.",
        "- Chaque dossier de contrôle conserve `master_results.json`, `reading_synthesis.json`, les tables d’estimateurs, diagnostics, rapports et journal de console.",
        "",
    ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUTPUT_JSON.write_text(json.dumps(raw_result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    inventory = []
    for control in controls:
        folder = RUN_DIR / control
        for path in sorted(folder.iterdir()):
            if path.is_file():
                inventory.append({
                    "control": control,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
    evidence_paths = [
        INPUT_MANIFEST,
        ANALYSIS / "prepare_pipeline_inputs_GSE271300.py",
        ANALYSIS / "make_balanced_pipeline_inputs.py",
        ANALYSIS / "run_pipeline_all_controls_parallel.py",
        ANALYSIS / "summarize_pipeline_all_controls.py",
        ANALYSIS / "GSE271300_PIPELINE_INPUTS.json",
        OUTPUT_CSV,
        OUTPUT_JSON,
        OUTPUT_MD,
    ]
    evidence = [
        {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in evidence_paths if path.is_file()
    ]
    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline": {"path": str(PIPELINE), "sha256": sha256(PIPELINE)},
        "input": {"path": str(INPUT), "sha256": sha256(INPUT), "bytes": INPUT.stat().st_size},
        "run_progress": {"path": str(progress_path), "sha256": sha256(progress_path)},
        "run_summary": {"path": str(summary_path), "sha256": sha256(summary_path)},
        "control_count": len(controls),
        "file_count": len(inventory),
        "files": inventory,
        "additional_evidence": evidence,
    }
    OUTPUT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Summary CSV: {OUTPUT_CSV}")
    print(f"Summary JSON: {OUTPUT_JSON}")
    print(f"Summary MD: {OUTPUT_MD}")
    print(f"Audit manifest: {OUTPUT_AUDIT}")
    print(f"Completed exit-zero: {len(completed)}/{len(controls)}; inventory match: {verified_expected_counts}; hashed files: {len(inventory)}")


if __name__ == "__main__":
    main()
