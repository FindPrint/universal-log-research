from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
INPUT = ANALYSIS / "pipeline_inputs_balanced_15" / "GSE271300_PC69_balanced15_multiflux.csv"
OUTPUT = ANALYSIS / "pipeline_runs_parallel15" / "PC69_target_basal"
PIPELINE = ROOT / "UNIVERSAL_LOG_v5.9.4.py"
MAX_PARALLEL = 4
TARGET = "CellState_basal"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def numeric_columns(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        rows = list(reader)
    output = []
    for name in names:
        if not rows:
            continue
        valid = 0
        nonempty = 0
        for row in rows:
            value = row.get(name, "")
            if value not in (None, ""):
                nonempty += 1
                try:
                    float(value)
                    valid += 1
                except (TypeError, ValueError):
                    pass
        if nonempty and valid == nonempty:
            output.append(name)
    return output


def run_one(control: str) -> dict:
    out_dir = OUTPUT / control
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "console.log"
    cmd = [
        sys.executable, "-u", str(PIPELINE),
        "--input", str(INPUT),
        "--target", TARGET,
        "--control", control,
        "--control-mode", "single",
        "--target-mode", "fixed",
        "--domain", "pdac",
        "--mode", "fast",
        "--no-l7b",
        "--no-harmonic-validation",
        "--no-dashboard",
        "--no-plots",
        "--no-telemetry",
        "--no-adaptive-walk-forward",
        "--no-regime-weights",
        "--seed", "42",
        "--output", str(out_dir),
    ]
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    with log.open("w", encoding="utf-8", newline="") as stream:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False)
    elapsed = time.perf_counter() - t0
    ended = datetime.now(timezone.utc)
    result = {
        "control": control,
        "command": cmd,
        "output_dir": str(out_dir),
        "console_log": str(log),
        "console_log_sha256": sha256(log),
        "started_utc": started.isoformat(),
        "ended_utc": ended.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": int(proc.returncode),
        "status": "completed" if proc.returncode == 0 else "error",
        "output_files": sorted(p.name for p in out_dir.iterdir() if p.is_file() and p.name != "console.log"),
    }
    (out_dir / "run_status.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    controls = numeric_columns(INPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    base = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline": str(PIPELINE),
        "pipeline_sha256": sha256(PIPELINE),
        "input": str(INPUT),
        "input_sha256": sha256(INPUT),
        "target_fixed": TARGET,
        "controls_from_numeric_csv_columns": controls,
        "control_mode_per_process": "single; one process per control; same fixed target and fast settings as the all-mode run",
        "triangulation_option": "omitted so the pipeline uses its implicit default, matching the all-mode run",
        "seed": 42,
        "max_parallel_processes": MAX_PARALLEL,
        "all_mode_partial_history": [
            {"control": "Treatment_code", "status": "completed in all-mode and also run separately for equivalence comparison"},
            {"control": "CellState_basal", "status": "completed in all-mode; explicit diagonal fallback to Treatment_code"},
            {"remaining_controls": max(0, len(controls) - 2), "status": "all-mode loop interrupted; rerun as separate control processes"},
        ],
        "results": [],
    }
    (OUTPUT / "RUN_PROGRESS.json").write_text(json.dumps(base, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Queue: {len(controls)} numeric controls; workers={MAX_PARALLEL}", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as executor:
        future_map = {executor.submit(run_one, name): name for name in controls}
        for future in concurrent.futures.as_completed(future_map):
            name = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"control": name, "status": "runner_exception", "error": repr(exc)}
            results.append(result)
            base["results"] = sorted(results, key=lambda row: row["control"])
            (OUTPUT / "RUN_PROGRESS.json").write_text(json.dumps(base, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[{len(results)}/{len(controls)}] {name}: {result.get('status')} ({result.get('elapsed_seconds')} s)", flush=True)
    base["completed_utc"] = datetime.now(timezone.utc).isoformat()
    base["status"] = "completed" if all(r.get("exit_code") == 0 for r in results) else "completed_with_errors"
    (OUTPUT / "RUN_SUMMARY.json").write_text(json.dumps(base, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Final summary: {OUTPUT / 'RUN_SUMMARY.json'} | status={base['status']}", flush=True)


if __name__ == "__main__":
    main()
