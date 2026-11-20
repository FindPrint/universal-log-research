"""One-run integration check for the derived v5.9 experiment runtime."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PREVIOUS_OUT = PROJECT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test"
SMOKE = HERE / "expanded_runs" / "smoke_test"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    study = load("expanded_study_for_smoke", HERE / "expanded_mcmc_v59_sensitivity.py")
    derived, derived_hash = study.prepare_runtime()
    v59 = load("v59_smoke_runtime", derived)
    helper = load("multiflux_helper_for_smoke", study.PREVIOUS_HELPER)
    helper.ul = v59
    helper.OUT = SMOKE
    helper.LOGS = SMOKE / "pipeline_logs"
    helper.WINDOW_SIZE = 40
    helper.PIPELINE_SEED = 20261108
    v59.PARAMETERS["modes"]["fast"]["w_size"] = 40
    (SMOKE / "pipeline_logs").mkdir(parents=True, exist_ok=True)
    (SMOKE / "feature_landscapes").mkdir(parents=True, exist_ok=True)

    old = __import__("pandas").read_csv(PREVIOUS_OUT / "pipeline_axis_flux_matrix.csv").iloc[0]
    L, T, chain = int(old["L"]), float(old["T"]), int(old["Chain"])
    input_path = PREVIOUS_OUT / "pipeline_inputs" / f"L{L}_T{T:.6f}_chain{chain}.csv"
    frame = __import__("pandas").read_csv(input_path)
    run_id = "smoke_v59_" + str(old["run_id"])
    start = time.monotonic()
    summary, rows, _typed = helper.pipeline_run(
        run_id, input_path, frame, L, T, chain, str(old["control"]), str(old["flux_set"]),
        [x for x in str(old["flux_names"]).split(",") if x],
    )
    summary["landscape_scan_points_source_metadata"] = summary.get("landscape_scan_points")
    summary["landscape_scan_points_effective_observed"] = summary.get("n_landscape_rows")
    summary["landscape_metadata_consistent"] = (
        summary.get("landscape_scan_points") == summary.get("n_landscape_rows")
    )
    result = {
        "source_v59_sha256": study.sha256(study.SOURCE_V59),
        "derived_runtime_sha256": derived_hash,
        "input_path": str(input_path), "input_sha256": digest(input_path),
        "run_id": run_id, "status": summary.get("status"),
        "state_status": summary.get("state_status"), "n_estimator_rows": len(rows),
        "elapsed_seconds": time.monotonic() - start,
        "summary": summary, "estimator_names": [row.get("estimator") for row in rows],
        "log_path": str(helper.LOGS / f"{run_id}.log"),
        "feature_path": str(SMOKE / "feature_landscapes" / f"{run_id}_df_feat.csv"),
    }
    (SMOKE / "smoke_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if summary.get("status") != "ok" or len(rows) != 29:
        raise RuntimeError(f"v5.9 integration smoke failed: status={summary.get('status')}, estimators={len(rows)}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
