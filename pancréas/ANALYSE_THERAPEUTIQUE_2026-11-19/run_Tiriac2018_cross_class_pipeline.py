from __future__ import annotations

import concurrent.futures
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
DATA_DIR = HERE / "candidate_Tiriac2018"
INPUT_CSV = DATA_DIR / "Tiriac2018_66PDO_drug_AUC.csv"
INPUT_MANIFEST = DATA_DIR / "PIPELINE_INPUT_MANIFEST.json"
PIPELINE = Path(__file__).resolve().parents[2] / "UNIVERSAL_LOG_v5.9.4.py"
PYTHON = Path(sys.executable)
RUN_ROOT = HERE / "Tiriac2018_cross_class_pipeline_runs"
N_TARGET_GROUPS = 4
SEED = 42
PRINT_LOCK = threading.Lock()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.")
    return cleaned or "column"


def run_target(target: str, controls: list[str], group_name: str) -> dict:
    out_dir = RUN_ROOT / "by_target" / safe_name(target)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "console.log"
    status_path = out_dir / "target_status.json"
    command = [
        str(PYTHON), str(PIPELINE),
        "--input", str(INPUT_CSV),
        "--target", target,
        "--controls", ",".join(controls),
        "--control-mode", "multi",
        "--target-mode", "fixed",
        "--mode", "fast",
        "--l7b-light",
        "--no-plots",
        "--seed", str(SEED),
        "--max-workers", "1",
        "--output", str(out_dir / "pipeline_output"),
    ]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    with log_path.open("w", encoding="utf-8", errors="replace", newline="\n") as log:
        log.write("RUN MATRIX GROUP: " + group_name + "\n")
        log.write("TARGET: " + target + "\n")
        log.write("CONTROLS: " + json.dumps(controls, ensure_ascii=False) + "\n")
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
            error = None
        except Exception as exc:
            exit_code = -999
            error = repr(exc)
            log.write("\nLAUNCH_EXCEPTION: " + error + "\n")
        finished = dt.datetime.now(dt.timezone.utc).isoformat()

    status = {
        "target": target,
        "controls": controls,
        "group": group_name,
        "status": "ok" if exit_code == 0 else "error",
        "exit_code": exit_code,
        "launch_error": error,
        "started_utc": started,
        "finished_utc": finished,
        "console_log": str(log_path),
        "output_dir": str(out_dir / "pipeline_output"),
        "command": command,
    }
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with PRINT_LOCK:
        print(
            f"DONE {target!r}: {status['status']} exit={exit_code}; "
            f"controls={len(controls)}; log={log_path}",
            flush=True,
        )
    return status


def main() -> int:
    if not INPUT_CSV.is_file() or not INPUT_MANIFEST.is_file():
        raise FileNotFoundError("Run prepare_Tiriac2018_pipeline_data.py before this matrix runner")
    if not PIPELINE.is_file():
        raise FileNotFoundError(PIPELINE)
    manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
    chemo = manifest["chemo_fluxes"]
    targeted = manifest["targeted_fluxes"]
    if manifest["observations"] < 50:
        raise ValueError(f"Input has only {manifest['observations']} observations")

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    jobs = []
    for target in chemo:
        jobs.append((target, targeted, "chemo_target__targeted_controls"))
    for target in targeted:
        jobs.append((target, chemo, "targeted_target__chemo_controls"))

    run_manifest = {
        "pipeline_path": str(PIPELINE),
        "pipeline_sha256": sha256(PIPELINE),
        "python_path": str(PYTHON),
        "input_csv": str(INPUT_CSV),
        "input_sha256": sha256(INPUT_CSV),
        "input_manifest": str(INPUT_MANIFEST),
        "input_observations": manifest["observations"],
        "seed": SEED,
        "pipeline_mode": "fast",
        "harmonic_validation": "pipeline default",
        "L7b": "light",
        "plots": "disabled for this 210-run matrix; numerical exports retained",
        "workers_per_target_process": 1,
        "target_process_concurrency": N_TARGET_GROUPS,
        "matrix": {
            "chemo_targets": chemo,
            "targeted_targets": targeted,
            "n_target_groups": len(jobs),
            "n_target_control_pairs": len(chemo) * len(targeted) * 2,
            "within_class_pairs": "not included in this first cross-class matrix",
        },
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (RUN_ROOT / "RUN_MATRIX_MANIFEST.json").write_text(
        json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"START matrix: observations={manifest['observations']}, "
        f"fluxes={len(chemo)+len(targeted)}, target_groups={len(jobs)}, "
        f"target-control_pairs={run_manifest['matrix']['n_target_control_pairs']}, "
        f"concurrency={N_TARGET_GROUPS}",
        flush=True,
    )

    statuses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=N_TARGET_GROUPS) as executor:
        future_map = {
            executor.submit(run_target, target, controls, group): target
            for target, controls, group in jobs
        }
        for future in concurrent.futures.as_completed(future_map):
            try:
                statuses.append(future.result())
            except Exception as exc:
                statuses.append({"target": future_map[future], "status": "runner_error", "error": repr(exc)})

    statuses.sort(key=lambda item: item.get("target", ""))
    summary = {
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "n_target_groups": len(statuses),
        "n_ok": sum(s.get("status") == "ok" for s in statuses),
        "n_error": sum(s.get("status") != "ok" for s in statuses),
        "n_target_control_pairs_requested": run_manifest["matrix"]["n_target_control_pairs"],
        "statuses": statuses,
    }
    summary_path = RUN_ROOT / "RUN_MATRIX_STATUS.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "statuses"}, indent=2), flush=True)
    print(f"STATUS: {summary_path}", flush=True)
    return 0 if summary["n_error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
