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
INPUT_CSV = DATA_DIR / "Tiriac2018_60PDO_completecase_drug_AUC.csv"
INPUT_MANIFEST = DATA_DIR / "PIPELINE_INPUT_MANIFEST.json"
PIPELINE = Path(__file__).resolve().parents[2] / "UNIVERSAL_LOG_v5.9.4.py"
PYTHON = Path(sys.executable)
RUN_ROOT = HERE / "Tiriac2018_Gemcitabine_all_controls_PDACDomain"
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
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.")
    return cleaned or "column"


def run_control(control: str) -> dict:
    out_dir = RUN_ROOT / "by_control" / safe_name(control)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "console.log"
    status_path = out_dir / "run_status.json"
    command = [
        str(PYTHON), str(PIPELINE),
        "--input", str(INPUT_CSV),
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
        print(
            f"DONE control={control!r}: {status['status']} exit={exit_code}; "
            f"elapsed={status['elapsed_seconds']:.1f}s",
            flush=True,
        )
    return status


def main() -> int:
    if not INPUT_CSV.is_file() or not INPUT_MANIFEST.is_file():
        raise FileNotFoundError("Run prepare_Tiriac2018_pipeline_data.py before this matrix runner")
    if not PIPELINE.is_file():
        raise FileNotFoundError(PIPELINE)
    input_manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
    numeric_fluxes = [*input_manifest["chemo_fluxes"], *input_manifest["targeted_fluxes"]]
    if TARGET not in numeric_fluxes:
        raise ValueError(f"Prespecified target {TARGET!r} is absent")
    controls = [column for column in numeric_fluxes if column != TARGET]
    if len(controls) != len(set(controls)) or len(controls) != len(numeric_fluxes) - 1:
        raise ValueError("Control list does not cover every non-target flux exactly once")
    if input_manifest["observations"] < 50:
        raise ValueError(f"Input has only {input_manifest['observations']} complete PDOs")

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    run_manifest = {
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pipeline_path": str(PIPELINE),
        "pipeline_sha256": sha256(PIPELINE),
        "python_path": str(PYTHON),
        "input_csv": str(INPUT_CSV),
        "input_sha256": sha256(INPUT_CSV),
        "input_manifest": str(INPUT_MANIFEST),
        "input_observations": input_manifest["observations"],
        "target": TARGET,
        "target_rationale": "Prespecified common chemotherapy comparator represented in the source pharmacotyping tables; used as an analysis anchor only.",
        "controls": controls,
        "requested_target_control_pairs": len(controls),
        "domain": "pdac",
        "mode": "fast",
        "seed": SEED,
        "l7b": "light",
        "plots": "disabled; numerical exports retained",
        "max_concurrent_pipeline_processes": MAX_CONCURRENT,
        "max_workers_per_pipeline_process": 1,
        "axis_limitation": "Cross-sectional PDO cohort. AUC control columns are used as axes per the pipeline; pipeline T0 is not a calendar-time transition or validated treatment threshold.",
    }
    (RUN_ROOT / "RUN_MATRIX_MANIFEST.json").write_text(
        json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"START Gemcitabine all-controls run: N={input_manifest['observations']}, "
        f"target={TARGET}, controls={len(controls)}, concurrency={MAX_CONCURRENT}",
        flush=True,
    )

    statuses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        future_map = {executor.submit(run_control, control): control for control in controls}
        for future in concurrent.futures.as_completed(future_map):
            try:
                statuses.append(future.result())
            except Exception as exc:
                statuses.append({"control": future_map[future], "status": "runner_error", "error": repr(exc)})

    statuses.sort(key=lambda item: item.get("control", ""))
    summary = {
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target": TARGET,
        "n_controls_requested": len(controls),
        "n_completed": sum(status.get("status") == "ok" for status in statuses),
        "n_error": sum(status.get("status") != "ok" for status in statuses),
        "statuses": statuses,
    }
    summary_path = RUN_ROOT / "RUN_MATRIX_STATUS.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "statuses"}, indent=2), flush=True)
    print(f"STATUS: {summary_path}", flush=True)
    return 0 if summary["n_error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
