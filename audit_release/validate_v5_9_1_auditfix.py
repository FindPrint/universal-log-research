"""Targeted checks for v5.9.1 taxonomy restoration and L7b edge semantics."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RELEASE = Path(__file__).resolve().parent
SOURCE_59 = PROJECT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py"
SOURCE_58 = PROJECT / "UNIVERSAL_LOG_v5.8.py"
PATCHED = RELEASE / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
FEATURES = PROJECT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_v59_study" / "expanded_runs" / "feature_landscapes" / "v59_L16_T2p269185314_C0_MC_Update_common_df_feat.csv"
OUT = RELEASE / "validation_exports"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    v58 = load("audit_v58_taxonomy", SOURCE_58)
    v59 = load("audit_v59_original", SOURCE_59)
    fixed = load("audit_v591_fixed", PATCHED)
    checks = []

    same_names = list(v58.ESTIMATOR_NAMES) == list(v59.ESTIMATOR_NAMES) == list(fixed.ESTIMATOR_NAMES)
    checks.append({"check": "same_ordered_29_estimator_names", "passed": same_names, "count": len(fixed.ESTIMATOR_NAMES)})
    same_partition = v58.DIMENSION_FOR_TLOG == v59.DIMENSION_FOR_TLOG == fixed.DIMENSION_FOR_TLOG
    checks.append({"check": "same_historical_dimension_partition", "passed": same_partition})
    checks.append({
        "check": "complete_taxonomy_partition",
        "passed": set(fixed.ESTIMATOR_D_KIND) == set(fixed.ESTIMATOR_NAMES)
                  and len(fixed.ESTIMATOR_MEASUREMENT_TYPES) == 29
                  and sum(x["quantity_type"] == "dimension_proxy" for x in fixed.ESTIMATOR_MEASUREMENT_TYPES.values()) == 21,
        "dimension_proxy_count": sum(x["quantity_type"] == "dimension_proxy" for x in fixed.ESTIMATOR_MEASUREMENT_TYPES.values()),
        "signature_count": sum(x["quantity_type"] == "signature" for x in fixed.ESTIMATOR_MEASUREMENT_TYPES.values()),
    })

    # Compare old and fixed state on a saved real feature landscape. Estimator values
    # and legacy D_vector must stay unchanged while typed annotations return.
    features = pd.read_csv(FEATURES)
    old_state = v59.compute_holographic_tension_state(features, n_samples=400, control_col="MC_Update")
    new_state = fixed.compute_holographic_tension_state(features, n_samples=400, control_col="MC_Update")
    old_raw = {k: v.get("raw_median") for k, v in old_state.get("per_estimator", {}).items()}
    new_raw = {k: v.get("raw_median") for k, v in new_state.get("per_estimator", {}).items()}
    raw_exact = old_raw == new_raw
    d_old = old_state.get("D_vector", {})
    d_new = new_state.get("D_vector", {})
    d_exact = d_old == d_new
    checks.append({"check": "real_landscape_29_raw_medians_unchanged", "passed": raw_exact, "n": len(new_raw)})
    checks.append({"check": "real_landscape_legacy_D_vector_unchanged", "passed": d_exact, "before": d_old, "after": d_new})
    geom = new_state.get("geometric_layer", {})
    kind_profiles = geom.get("T_log_by_d_kind") or {}
    used_names = [name for item in kind_profiles.values() for name in item.get("estimators_used", [])]
    checks.append({
        "check": "typed_tlog_profiles_cover_each_admissible_estimator_once",
        "passed": len(used_names) == 21 and len(set(used_names)) == 21
                  and set(used_names) == {name for group in fixed.DIMENSION_FOR_TLOG.values() for name in group},
        "profile_count": len(kind_profiles), "typed_estimators": len(used_names),
    })
    checks.append({
        "check": "per_estimator_taxonomy_present",
        "passed": all(x.get("d_kind") and x.get("quantity_type") for x in new_state["per_estimator"].values()),
        "n": len(new_state["per_estimator"]),
    })

    OUT.mkdir(parents=True, exist_ok=True)
    export_paths = fixed._write_estimator_measurement_type_exports(OUT)
    taxonomy_csv = pd.read_csv(export_paths["csv"])
    taxonomy_json = json.loads(Path(export_paths["json"]).read_text(encoding="utf-8"))
    checks.append({
        "check": "taxonomy_csv_json_exports_have_29_methods",
        "passed": len(taxonomy_csv) == 29 and len(taxonomy_json.get("estimators", {})) == 29,
        "csv_rows": len(taxonomy_csv), "json_estimators": len(taxonomy_json.get("estimators", {})),
    })

    cli_help = subprocess.run(
        [sys.executable, str(PATCHED), "--help"],
        capture_output=True, text=True, timeout=90,
    )
    checks.append({
        "check": "cli_help_exits_cleanly_and_lists_l7b_options",
        "passed": cli_help.returncode == 0 and "--l7b-full" in cli_help.stdout,
        "returncode": cli_help.returncode,
        "stderr_tail": cli_help.stderr[-1000:],
    })

    ref = {"T0_pct": 50.0, "consensus_direction": "up", "Delta": 2.0, "L7_status": "ok"}
    ready = dict(ref)
    cases = [
        ("missing_reference_T0", {**ref, "T0_pct": None}, ready, ready, ready, ready, "graine", "INDETERMINE"),
        ("missing_seed_T0", ref, {**ready, "T0_pct": None}, ready, ready, ready, "graine", "INDETERMINE"),
        ("missing_window_T0", ref, ready, {**ready, "T0_pct": None}, ready, ready, "fenetre", "INDETERMINE"),
        ("missing_reference_Delta", {**ref, "Delta": None}, ready, ready, {**ready, "Delta": 1.0}, ready, "melange", "INDETERMINE"),
        ("negative_Delta_magnitude_halved", {**ref, "Delta": -2.0}, {**ready, "Delta": -2.0}, {**ready, "Delta": -2.0}, {**ready, "Delta": -1.0}, ready, "melange", "PASS"),
        ("missing_shuffled_Delta", ref, ready, ready, {**ready, "Delta": None}, ready, "melange", "INDETERMINE"),
        ("shuffled_Delta_sign_reversed", ref, ready, ready, {**ready, "Delta": -2.0}, ready, "melange", "INDETERMINE"),
        ("shuffled_signal_unchanged", ref, ready, ready, ready, ready, "melange", "FAIL"),
        ("positive_Delta_40pct_after_shuffle", ref, ready, ready, {**ready, "Delta": 0.8}, ready, "melange", "PASS"),
        ("missing_log_T0_is_informative_only", ref, ready, ready, {**ready, "Delta": 0.2}, {**ready, "T0_pct": None}, "echelle", "INDETERMINE"),
    ]
    case_rows = []
    for name, reference, seed, window, shuffled, log_run, check_name, expected in cases:
        observed = fixed.level_robustness_L7b_from_summaries(reference, seed, window, shuffled, log_run)
        status = (observed.get("checks", {}).get(check_name) or {}).get("statut")
        ok = status == expected
        case_rows.append({"case": name, "expected_check": expected, "observed_check": status,
                          "overall_verdict": observed.get("verdict"), "passed": ok,
                          "inputs": {"reference": reference, "seed_alt": seed, "window_80": window, "shuffled": shuffled, "log_run": log_run},
                          "output": observed})
    checks.append({"check": "l7b_missing_data_and_signed_delta_cases", "passed": all(x["passed"] for x in case_rows), "cases": len(case_rows)})

    # Ensure the original source stayed byte-identical to the recorded source.
    provenance = json.loads((RELEASE / "v5.9.1_patch_provenance.json").read_text(encoding="utf-8"))
    checks.append({"check": "supplied_v59_source_unchanged", "passed": sha(SOURCE_59) == provenance["source_v5_9_sha256"], "sha256": sha(SOURCE_59)})
    result = {
        "patched_source": str(PATCHED), "patched_source_sha256": sha(PATCHED),
        "original_v59_sha256": sha(SOURCE_59), "v58_taxonomy_source_sha256": sha(SOURCE_58),
        "feature_input": str(FEATURES), "feature_input_sha256": sha(FEATURES),
        "checks": checks, "l7b_synthetic_cases": case_rows,
        "all_checks_passed": all(x["passed"] for x in checks),
        "scope_note": "Direct helper tests plus full compute_holographic_tension_state on one retained feature landscape; not a full run_full_unified_pipeline L7b integration or scientific threshold calibration.",
    }
    (RELEASE / "v5.9.1_validation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (RELEASE / "v5.9.1_L7b_edge_cases.json").write_text(json.dumps(case_rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"all_checks_passed": result["all_checks_passed"], "checks": checks, "taxonomy_exports": export_paths}, indent=2, ensure_ascii=False))
    if not result["all_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
