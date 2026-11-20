"""Reproducible matched replay: archived v5.9.0 vs audit-fixed v5.9.1.

Run with the project virtual environment from the project root. Outputs go into
the dated audit_release directory and do not replace historical study files.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit_release" / "2026-11-14_matched_v59_v591_replay_run03"
STUDY = ROOT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_v59_study" / "expanded_runs"
PREVIOUS = ROOT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test"
INPUTS = PREVIOUS / "pipeline_inputs"
HELPER_PATH = ROOT / "ising_classique_test" / "multiflux_mcmc_pipeline_test.py"
V590_DERIVED = STUDY / "runtime" / "UNIVERSAL_LOG_v5_9_exp_landscape24.py"
V591_SOURCE = ROOT / "audit_release" / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
V591_DERIVED = OUT / "runtime" / "UNIVERSAL_LOG_v5_9_1_AUDITFIX_landscape24.py"
SCAN_120 = "scan_points = np.linspace(progress.min(), progress.max(), 120)"
SCAN_24 = "scan_points = np.linspace(progress.min(), progress.max(), 24)"
PIPELINE_SEED = 20261108
WINDOW_SIZE = 40
LANDSCAPE_POINTS = 24


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> None:
    if OUT.exists() and any(p.is_file() for p in OUT.rglob("*")):
        raise FileExistsError(f"Refusing to overwrite existing replay outputs in {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "runtime").mkdir(exist_ok=True)
    (OUT / "logs").mkdir(exist_ok=True)
    (OUT / "feature_landscapes").mkdir(exist_ok=True)

    old_matrix_path = PREVIOUS / "pipeline_axis_flux_matrix.csv"
    old_estimators_path = PREVIOUS / "pipeline_estimator_outputs.csv"
    old_summaries_path = STUDY / "matched_v59_run_summaries.csv"
    old_v590_estimators_path = STUDY / "matched_v59_estimator_outputs.csv"
    for p in [HELPER_PATH, V590_DERIVED, V591_SOURCE, old_matrix_path, old_estimators_path,
              old_summaries_path, old_v590_estimators_path]:
        if not p.is_file():
            raise FileNotFoundError(p)

    old_matrix = pd.read_csv(old_matrix_path)
    old_estimators = pd.read_csv(old_estimators_path)
    v590_summaries = pd.read_csv(old_summaries_path)
    v590_estimators = pd.read_csv(old_v590_estimators_path)
    if len(old_matrix) != 20:
        raise AssertionError(f"Expected 20 archived configurations, found {len(old_matrix)}")
    if len(v590_summaries) != 20 or len(v590_estimators) != 580:
        raise AssertionError(f"Unexpected archived v5.9.0 baseline sizes: {len(v590_summaries)} summaries, {len(v590_estimators)} estimator rows")
    if old_estimators.duplicated(["run_id", "estimator"]).any():
        raise AssertionError("Archived v5.8 baseline has duplicate run/estimator keys")
    if v590_estimators.duplicated(["paired_v58_run_id", "estimator"]).any():
        raise AssertionError("Archived v5.9.0 baseline has duplicate paired-run/estimator keys")

    # Preserve the v5.9.0 experiment's 24 point landscape resolution, changing
    # exactly one source line in a derived copy so the version comparison uses
    # the same resolution. The released source remains untouched.
    source_text = V591_SOURCE.read_text(encoding="utf-8")
    if source_text.count(SCAN_120) != 1:
        raise AssertionError(f"Expected one 120-point scan line in v5.9.1 source; got {source_text.count(SCAN_120)}")
    V591_DERIVED.write_text(source_text.replace(SCAN_120, SCAN_24), encoding="utf-8")

    configurations = []
    for _, row in old_matrix.iterrows():
        L, T, chain = int(row["L"]), float(row["T"]), int(row["Chain"])
        inp = INPUTS / f"L{L}_T{T:.6f}_chain{chain}.csv"
        frame = pd.read_csv(inp)
        fluxes = [part for part in str(row["flux_names"]).split(",") if part]
        missing = [c for c in [str(row["control"]), *fluxes] if c not in frame.columns]
        if missing:
            raise AssertionError(f"Missing configured columns in {inp.name}: {missing}")
        configurations.append({
            "v58_run_id": str(row["run_id"]),
            "L": L, "T": T, "Chain": chain,
            "control": str(row["control"]), "flux_set": str(row["flux_set"]),
            "flux_names": fluxes, "input": str(inp.relative_to(ROOT)),
            "input_sha256": sha256(inp), "input_rows": len(frame),
        })
    if len({c["input"] for c in configurations}) != 8:
        raise AssertionError(f"Expected 8 distinct CSVs reused across 20 configurations; got {len({c['input'] for c in configurations})}")

    script_path = Path(__file__).resolve()
    protocol = {
        "title": "Matched replay v5.9.0 versus audit-fixed v5.9.1",
        "status": "predeclared_before_execution",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Rerun the same 20 archived control/flux configurations over their original 200-row CSVs, then compare v5.9.1 with the archived v5.9.0 outputs.",
        "hypotheses_not_results": [
            "H1: identical rows, control, flux list, seed, window size, and 24-point landscape resolution should preserve the 29 estimator raw medians to stored precision unless an audited code change affects the estimator calculation.",
            "H2: v5.9.1 should populate registered estimator kind, quantity type, and TLog-by-kind exports that were absent or untyped in the v5.9.0 matched output.",
            "H3: output state labels may change because v5.9.1 repairs taxonomy and missing-data semantics; label changes are descriptive and do not establish physical criticality or causality.",
        ],
        "comparison_rules": {
            "primary_numeric": "Paired estimator raw_median by archived configuration and estimator; report exact equality and absolute differences, with 1e-6 only as a stored-precision descriptive threshold.",
            "typed_output": "Record populated d_kind, quantity_type, TLog membership, and per-run TLog-by-kind entries.",
            "state": "Compare state_status, dominant_regime, and D_vector components descriptively; no pass/fail scientific threshold.",
            "scope_limit": "This is a software replay on archived synthetic Ising MCMC CSVs, not an independent universality validation.",
        },
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "seed": PIPELINE_SEED,
            "window_size_rows": WINDOW_SIZE,
            "landscape_scan_points": LANDSCAPE_POINTS,
            "estimator_profile": "all",
            "max_workers": 1,
            "auto_optimize_threshold": False,
            "optimization_iterations": 0,
            "mc_complexity_enabled": False,
        },
        "source_hashes": {
            "v5.9.0_derived_runtime_24": {"path": str(V590_DERIVED.relative_to(ROOT)), "sha256": sha256(V590_DERIVED)},
            "v5.9.1_release_source": {"path": str(V591_SOURCE.relative_to(ROOT)), "sha256": sha256(V591_SOURCE)},
            "v5.9.1_derived_runtime_24": {"path": str(V591_DERIVED.relative_to(ROOT)), "sha256": sha256(V591_DERIVED), "transformation": "Only scan_points: 120 -> 24; released source preserved."},
            "runner": {"path": str(script_path.relative_to(ROOT)), "sha256": sha256(script_path)},
            "v5.8_config_matrix": {"path": str(old_matrix_path.relative_to(ROOT)), "sha256": sha256(old_matrix_path)},
            "v5.8_estimator_baseline": {"path": str(old_estimators_path.relative_to(ROOT)), "sha256": sha256(old_estimators_path)},
            "v5.9.0_summaries": {"path": str(old_summaries_path.relative_to(ROOT)), "sha256": sha256(old_summaries_path)},
            "v5.9.0_estimator_baseline": {"path": str(old_v590_estimators_path.relative_to(ROOT)), "sha256": sha256(old_v590_estimators_path)},
        },
        "configuration_count": len(configurations),
        "configurations": configurations,
    }
    write_json(OUT / "protocol_predeclared.json", protocol)

    helper = load_module("matched_replay_helper_v58", HELPER_PATH)
    v591 = load_module("universal_log_v591_matched_replay", V591_DERIVED)
    helper.ul = v591
    helper.OUT = OUT
    helper.LOGS = OUT / "logs"
    helper.WINDOW_SIZE = WINDOW_SIZE
    helper.LANDSCAPE_SCAN_POINTS = LANDSCAPE_POINTS
    helper.PIPELINE_SEED = PIPELINE_SEED
    v591.PARAMETERS["modes"]["fast"]["w_size"] = WINDOW_SIZE

    results = []
    new_estimator_rows = []
    new_typed_rows = []
    started_all = time.time()
    with (OUT / "RUN_JOURNAL.jsonl").open("w", encoding="utf-8", newline="\n") as journal:
        for index, cfg in enumerate(configurations, 1):
            inp = ROOT / cfg["input"]
            frame = pd.read_csv(inp)
            run_id = f"matched591_L{cfg['L']}_T{cfg['T']:.9f}_C{cfg['Chain']}_{cfg['control'].replace(' ', '_')}_{cfg['flux_set']}"
            started = time.time()
            summary, estimator_rows, typed_rows = helper.pipeline_run(
                run_id, inp, frame, cfg["L"], cfg["T"], cfg["Chain"],
                cfg["control"], cfg["flux_set"], cfg["flux_names"],
            )
            summary.update({
                "paired_v58_run_id": cfg["v58_run_id"],
                "paired_v590_run_id": next((str(x) for x in v590_summaries.loc[v590_summaries["paired_v58_run_id"].astype(str).eq(cfg["v58_run_id"]), "run_id"]), None),
                "family": "matched_v58_v59_v591",
                "pipeline_input_sha256": cfg["input_sha256"],
                "runtime_sha256": sha256(V591_DERIVED),
                "wall_seconds": round(time.time() - started, 3),
            })
            for row in estimator_rows:
                row["paired_v58_run_id"] = cfg["v58_run_id"]
                row["paired_v590_run_id"] = summary["paired_v590_run_id"]
                row["d_kind_v591_native"] = row.get("d_kind")
                row["runtime_sha256"] = sha256(V591_DERIVED)
            for row in typed_rows:
                row["paired_v58_run_id"] = cfg["v58_run_id"]
                row["paired_v590_run_id"] = summary["paired_v590_run_id"]
                row["runtime_sha256"] = sha256(V591_DERIVED)
            results.append(summary)
            new_estimator_rows.extend(estimator_rows)
            new_typed_rows.extend(typed_rows)
            event = {
                "index": index, "total": len(configurations), "v58_run_id": cfg["v58_run_id"],
                "v591_run_id": run_id, "status": summary.get("status"),
                "input": cfg["input"], "input_sha256": cfg["input_sha256"],
                "control": cfg["control"], "flux_set": cfg["flux_set"], "flux_names": cfg["flux_names"],
                "estimator_rows": len(estimator_rows), "tlog_by_kind_rows": len(typed_rows),
                "state_status": summary.get("state_status"), "dominant_regime": summary.get("dominant_regime"),
                "wall_seconds": summary.get("wall_seconds"), "error": summary.get("error"),
            }
            journal.write(json.dumps(event, ensure_ascii=False, sort_keys=True, default=str) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
            print(f"[{index}/{len(configurations)}] {cfg['v58_run_id']} -> {summary.get('status')} | estimators={len(estimator_rows)} TLogKinds={len(typed_rows)} | {summary.get('wall_seconds')} s", flush=True)

    pd.DataFrame(results).to_csv(OUT / "v591_run_summaries.csv", index=False)
    new_estimators_df = pd.DataFrame(new_estimator_rows)
    new_typed_df = pd.DataFrame(new_typed_rows)
    new_estimators_df.to_csv(OUT / "v591_estimator_outputs.csv", index=False)
    new_typed_df.to_csv(OUT / "v591_tlog_by_kind.csv", index=False)

    baseline590 = v590_estimators.copy()
    baseline590["paired_v58_run_id"] = baseline590["paired_v58_run_id"].astype(str)
    paired = baseline590.merge(
        new_estimators_df,
        on=["paired_v58_run_id", "estimator"], how="outer", suffixes=("_v590", "_v591"), indicator=True,
    )
    paired["difference_v591_minus_v590"] = pd.to_numeric(paired.get("raw_median_v591"), errors="coerce") - pd.to_numeric(paired.get("raw_median_v590"), errors="coerce")
    paired["absolute_difference"] = paired["difference_v591_minus_v590"].abs()
    paired["exact_equal"] = paired["absolute_difference"].eq(0)
    paired["within_1e_6"] = paired["absolute_difference"].le(1e-6)
    paired.to_csv(OUT / "v590_v591_estimator_comparison.csv", index=False)

    summaries = pd.DataFrame(results)
    old_by_v58 = v590_summaries.set_index(v590_summaries["paired_v58_run_id"].astype(str), drop=False)
    new_by_v58 = summaries.set_index(summaries["paired_v58_run_id"].astype(str), drop=False)
    summary_comparisons = []
    for key in sorted(set(old_by_v58.index) & set(new_by_v58.index)):
        a, b = old_by_v58.loc[key], new_by_v58.loc[key]
        row = {"paired_v58_run_id": key, "v590_run_id": a.get("run_id"), "v591_run_id": b.get("run_id"),
               "control_v590": a.get("control"), "control_v591": b.get("control"),
               "flux_set_v590": a.get("flux_set"), "flux_set_v591": b.get("flux_set"),
               "state_status_v590": a.get("state_status"), "state_status_v591": b.get("state_status"),
               "dominant_regime_v590": a.get("dominant_regime"), "dominant_regime_v591": b.get("dominant_regime"),
               "d_sat_v590": a.get("d_sat"), "d_sat_v591": b.get("d_sat"),
               "d_crit_v590": a.get("d_crit"), "d_crit_v591": b.get("d_crit"),
               "d_div_v590": a.get("d_div"), "d_div_v591": b.get("d_div"),
               "d_null_v590": a.get("d_null"), "d_null_v591": b.get("d_null"),
               "landscape_rows_v590": a.get("n_landscape_rows"), "landscape_rows_v591": b.get("n_landscape_rows"),
               "status_v591": b.get("status")}
        summary_comparisons.append(row)
    pd.DataFrame(summary_comparisons).to_csv(OUT / "v590_v591_summary_comparison.csv", index=False)

    merge_counts = paired["_merge"].value_counts(dropna=False).to_dict()
    matched_rows = paired.loc[paired["_merge"].eq("both")]
    numeric_diff = pd.to_numeric(matched_rows["absolute_difference"], errors="coerce")
    filled_kind = int(new_estimators_df.get("d_kind_v591_native", pd.Series(dtype=object)).notna().sum())
    filled_quantity = int(new_estimators_df.get("quantity_type", pd.Series(dtype=object)).notna().sum())
    filled_tlog_membership = int(new_estimators_df.get("tlog_membership", pd.Series(dtype=object)).notna().sum())
    summary = {
        "status": "completed",
        "started_wall_seconds": round(time.time() - started_all, 3),
        "configurations_planned": len(configurations),
        "configurations_ok": int(summaries.get("status", pd.Series(dtype=str)).astype(str).eq("ok").sum()),
        "configurations_error": int(summaries.get("status", pd.Series(dtype=str)).astype(str).ne("ok").sum()),
        "v590_estimator_rows": len(v590_estimators), "v591_estimator_rows": len(new_estimators_df),
        "paired_estimator_merge_counts": {str(k): int(v) for k, v in merge_counts.items()},
        "matched_estimator_rows": len(matched_rows),
        "raw_median_exact_equal_rows": int(matched_rows["exact_equal"].fillna(False).sum()),
        "raw_median_within_1e_6_rows": int(matched_rows["within_1e_6"].fillna(False).sum()),
        "raw_median_max_abs_difference": float(numeric_diff.max()) if numeric_diff.notna().any() else None,
        "raw_median_median_abs_difference": float(numeric_diff.median()) if numeric_diff.notna().any() else None,
        "v591_native_d_kind_populated_rows": filled_kind,
        "v591_quantity_type_populated_rows": filled_quantity,
        "v591_tlog_membership_populated_rows": filled_tlog_membership,
        "v591_tlog_by_kind_rows": len(new_typed_df),
        "v591_tlog_d_kinds": sorted(new_typed_df["d_kind"].dropna().astype(str).unique().tolist()) if "d_kind" in new_typed_df else [],
        "hypotheses_remain_hypotheses": True,
        "interpretation": "Software replay only. Numerical agreement/disagreement and restored typed outputs do not prove universal validity or physical criticality detection.",
    }
    write_json(OUT / "replay_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
