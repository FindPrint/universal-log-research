from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE / "NatureComm2025_46PDO_63Drug_AUC.csv"
INPUT_MANIFEST = HERE / "PIPELINE_INPUT_MANIFEST.json"
PIPELINE = Path(__file__).resolve().parents[3] / "UNIVERSAL_LOG_v5.9.4.py"
PYTHON = Path(sys.executable)
RUN_ROOT = HERE / "NatureComm2025_Gemcitabine_all_controls_PDACPilot"
TARGET = "Gemcitabine"
MAX_CONCURRENT = 4
SEED = 42
PRINT_LOCK = threading.Lock()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.") or "column"


def read_fluxes() -> list[str]:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as stream:
        return next(csv.reader(stream))[1:]


def run_control(control: str) -> dict:
    out_dir = RUN_ROOT / "by_control" / safe_name(control)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "console.log"
    status_path = out_dir / "run_status.json"
    command = [
        str(PYTHON), str(PIPELINE),
        "--input", str(INPUT),
        "--target", TARGET,
        "--control", control,
        "--control-mode", "single",
        "--target-mode", "fixed",
        "--domain", "pdac",
        "--mode", "fast",
        "--l7b-light",
        "--no-plots",
        "--seed", str(SEED),
        "--max-workers", "1",
        "--output", str(out_dir / "pipeline_output"),
    ]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    error = None
    with log_path.open("w", encoding="utf-8", errors="replace", newline="\n") as log:
        log.write(f"PILOT_STATUS: below N>=50 confirmatory floor; exploratory only\n")
        log.write("TARGET: " + TARGET + "\n")
        log.write("CONTROL: " + control + "\n")
        log.write("STARTED_UTC: " + started + "\n")
        log.write("COMMAND: " + json.dumps(command, ensure_ascii=False) + "\n\n")
        log.flush()
        child_env = os.environ.copy()
        for env_name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            child_env[env_name] = "1"
        try:
            completed = subprocess.run(
                command,
                cwd=str(PIPELINE.parent),
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                env=child_env,
            )
            exit_code = int(completed.returncode)
        except Exception as exc:
            exit_code = -999
            error = repr(exc)
            log.write("\nLAUNCH_EXCEPTION: " + error + "\n")
        finished = dt.datetime.now(dt.timezone.utc).isoformat()
    status = {
        "target": TARGET,
        "control": control,
        "domain": "pdac",
        "status": "ok" if exit_code == 0 else "error",
        "exit_code": exit_code,
        "launch_error": error,
        "started_utc": started,
        "finished_utc": finished,
        "elapsed_seconds": round((dt.datetime.fromisoformat(finished) - dt.datetime.fromisoformat(started)).total_seconds(), 3),
        "console_log": str(log_path),
        "console_log_sha256": sha256(log_path),
        "output_dir": str(out_dir / "pipeline_output"),
        "command": command,
    }
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with PRINT_LOCK:
        print(f"DONE control={control!r}: {status['status']} exit={exit_code}; elapsed={status['elapsed_seconds']:.1f}s", flush=True)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploratory all-controls pilot for Nature Communications 2025 PAAD PDO AUC data")
    parser.add_argument("--limit", type=int, default=None, help="Run the first N source-ordered controls, then resume without --limit")
    args = parser.parse_args()
    manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
    fluxes = read_fluxes()
    if manifest["observations"] != 46 or len(fluxes) != 63:
        raise ValueError("Input no longer matches the locked 46-PDO x 63-drug pilot matrix")
    if TARGET not in fluxes:
        raise ValueError(f"Prespecified target {TARGET!r} is absent")
    controls = [column for column in fluxes if column != TARGET]
    if len(controls) != 62 or len(set(controls)) != len(controls):
        raise ValueError("Expected every non-target flux exactly once as a control")
    if not PIPELINE.is_file():
        raise FileNotFoundError(PIPELINE)

    if manifest["observations"] < 50 and args.limit is None:
        prior_statuses = []
        for control in controls:
            status_path = RUN_ROOT / "by_control" / safe_name(control) / "run_status.json"
            if status_path.exists():
                prior_statuses.append(json.loads(status_path.read_text(encoding="utf-8")))
        n_completed = sum(item.get("status") == "ok" and item.get("exit_code") == 0 for item in prior_statuses)
        n_error = sum(item.get("status") != "ok" or item.get("exit_code") != 0 for item in prior_statuses)
        stopped = {
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "target": TARGET,
            "n_controls_requested": len(controls),
            "n_completed": n_completed,
            "n_error": n_error,
            "n_remaining": len(controls) - len(prior_statuses),
            "pilot_only_below_N50": True,
            "matrix_disposition": "not_launched_because_pipeline_requires_N_at_least_50",
            "statuses": prior_statuses,
        }
        (RUN_ROOT / "RUN_MATRIX_STATUS.json").write_text(json.dumps(stopped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("BLOCKED: N=46 is below the pipeline's runtime minimum of 50; remaining controls were not launched.", flush=True)
        return 2

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    matrix_manifest = {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pipeline_path": str(PIPELINE),
        "pipeline_sha256": sha256(PIPELINE),
        "python_path": str(PYTHON),
        "input_csv": str(INPUT),
        "input_sha256": sha256(INPUT),
        "input_observations": manifest["observations"],
        "target": TARGET,
        "target_rationale": "Fixed anchor selected before inspecting this pilot's pipeline outcomes, matching the previous Gemcitabine control-axis sweep.",
        "controls_in_source_order": controls,
        "requested_target_control_pairs": len(controls),
        "domain": "pdac",
        "mode": "fast",
        "seed": SEED,
        "l7b": "light",
        "plots": "disabled; numerical exports retained",
        "max_concurrent_pipeline_processes": MAX_CONCURRENT,
        "max_workers_per_pipeline_process": 1,
        "confirmatory_eligibility": False,
        "eligibility_note": "N=46 actual PDO models; below the locked N>=50 floor. This is a pilot only and cannot count as external confirmation.",
        "axis_limitation": "Cross-sectional, source-ordered PDO models; row order is not time or a biological trajectory.",
        "data_handling": "The published AUC values were transposed without scaling, imputation, filtering, or reordering.",
    }
    manifest_path = RUN_ROOT / "RUN_MATRIX_MANIFEST.json"
    if manifest_path.exists():
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("pipeline_sha256", "input_sha256", "target", "controls_in_source_order", "domain", "mode", "seed"):
            if old_manifest.get(key) != matrix_manifest.get(key):
                raise ValueError(f"Resume settings differ from locked matrix manifest: {key}")
    else:
        manifest_path.write_text(json.dumps(matrix_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pending = []
    for control in controls:
        status_path = RUN_ROOT / "by_control" / safe_name(control) / "run_status.json"
        if status_path.exists():
            prior = json.loads(status_path.read_text(encoding="utf-8"))
            if prior.get("status") == "ok" and prior.get("exit_code") == 0:
                continue
        pending.append(control)
    if args.limit is not None:
        pending = pending[: max(0, args.limit)]
    completed_before = len(controls) - len(pending)
    print(f"START pilot: N=46, target={TARGET}, previously_completed={completed_before}, pending_this_call={len(pending)}, planned_controls={len(controls)}", flush=True)

    statuses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = {executor.submit(run_control, control): control for control in pending}
        for future in concurrent.futures.as_completed(futures):
            try:
                statuses.append(future.result())
            except Exception as exc:
                statuses.append({"control": futures[future], "status": "runner_error", "error": repr(exc)})

    all_statuses = []
    for control in controls:
        status_path = RUN_ROOT / "by_control" / safe_name(control) / "run_status.json"
        if status_path.exists():
            all_statuses.append(json.loads(status_path.read_text(encoding="utf-8")))
    completed_count = sum(status.get("status") == "ok" and status.get("exit_code") == 0 for status in all_statuses)
    error_count = sum(status.get("status") != "ok" or status.get("exit_code") != 0 for status in all_statuses)
    matrix_status = {
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target": TARGET,
        "n_controls_requested": len(controls),
        "n_completed": completed_count,
        "n_error": error_count,
        "n_remaining": len(controls) - completed_count - error_count,
        "pilot_only_below_N50": True,
        "statuses": all_statuses,
    }
    status_out = RUN_ROOT / "RUN_MATRIX_STATUS.json"
    status_out.write_text(json.dumps(matrix_status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in matrix_status.items() if key != "statuses"}, indent=2), flush=True)
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
