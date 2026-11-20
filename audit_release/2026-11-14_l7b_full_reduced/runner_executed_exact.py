"""Bounded L7b-full integration replay on a deterministic 80-row slice."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit_release" / "2026-11-14_l7b_full_reduced"
SOURCE = ROOT / "audit_release" / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
INPUT = ROOT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test" / "pipeline_inputs" / "L16_T2.269185_chain0.csv"
SUBSET = OUT / "data" / "L16_T2.269185_chain0_first80.csv"
TARGET = "Abs_magnetization"
CONTROL = "MC_Update"
SEED = 20261108
N_ROWS = 80


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("universal_log_v591_l7b_full_reduced", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def walk_l7b(value, path="$"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if "l7b" in str(key).lower() or (isinstance(child, dict) and str(child.get("version", "")).startswith("L7b")):
                found.append({"path": f"{path}.{key}", "value": child})
            found.extend(walk_l7b(child, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(walk_l7b(child, f"{path}[{index}]"))
    return found


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> None:
    if OUT.exists() and any(p.is_file() for p in OUT.rglob("*")):
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    SUBSET.parent.mkdir(parents=True, exist_ok=True)
    frame_all = pd.read_csv(INPUT)
    if len(frame_all) < N_ROWS or any(c not in frame_all.columns for c in (TARGET, CONTROL)):
        raise AssertionError("Input is too short or missing selected target/control")
    frame = frame_all.iloc[:N_ROWS].copy()
    frame.to_csv(SUBSET, index=False)
    if len(frame[CONTROL].dropna().unique()) < 2:
        raise AssertionError("Selected slice has no control variation")

    protocol = {
        "title": "v5.9.1 L7b-full integration - bounded sample",
        "status": "predeclared_before_execution",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hypotheses_not_results": [
            "H1: the real run_full_unified_pipeline path with l7b_mode=full emits all four perturbation checks and a structured L7b result.",
            "H2: absent/failed evidence remains INDETERMINE; the software does not convert missing checks into a robust verdict.",
        ],
        "choice_and_reason": "Use the first 80 rows of the archived L16,Tc,chain0 CSV to bound an expensive integration test while retaining two 40-row windows. This is an engineering test subset, not a scientific sample-size choice.",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "input": str(INPUT.relative_to(ROOT)),
        "input_sha256": sha256(INPUT),
        "subset": str(SUBSET.relative_to(ROOT)),
        "subset_sha256": sha256(SUBSET),
        "subset_rule": "rows [0:80], original row order retained",
        "rows_original": len(frame_all),
        "rows_used": len(frame),
        "target": TARGET,
        "control": CONTROL,
        "target_policy": "fixed",
        "l7b_mode": "full",
        "outer_mode": "fast",
        "seed": SEED,
        "other_arguments": "run_full_unified_pipeline defaults retained: domain=generic, risk=moderate, horizon=None, horizons=None, n_scenarios=48; max_workers=1.",
        "limitation": "Software integration evidence only; the 80-row slice and heuristic verdicts do not validate Ising criticality detection.",
    }
    protocol["runner_sha256"] = sha256(Path(__file__).resolve())
    save_json(OUT / "protocol_predeclared.json", protocol)

    module = load_module(SOURCE)
    log_path = OUT / "console.log"
    output_dir = OUT / "pipeline_output"
    started = time.time()
    record = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat()}
    save_json(OUT / "execution_status.json", record)
    try:
        with log_path.open("w", encoding="utf-8", newline="\n", buffering=1) as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            result = module.run_full_unified_pipeline(
                csv_path=str(SUBSET), target_col=TARGET, control_col=CONTROL,
                control_mode="single", target_policy="fixed", seed=SEED,
                output_dir=str(output_dir), mode="fast", max_workers=1,
                l7b_mode="full",
            )
        elapsed = round(time.time() - started, 3)
        l7b = walk_l7b(result)
        saved_master = output_dir / "master_results.json"
        master_l7b = None
        if saved_master.is_file():
            master = json.loads(saved_master.read_text(encoding="utf-8"))
            master_l7b = ((master.get("prediction_levels") or {}).get("L7b_robustesse"))
        record = {
            "status": "returned", "elapsed_seconds": elapsed,
            "result_type": type(result).__name__,
            "result_keys": sorted(result.keys()) if isinstance(result, dict) else None,
            "return_l7b_occurrences": l7b,
            "persisted_l7b": master_l7b,
            "console_log": str(log_path.relative_to(ROOT)),
            "console_log_sha256": sha256(log_path),
            "pipeline_output": str(output_dir.relative_to(ROOT)),
            "master_results_sha256": sha256(saved_master) if saved_master.is_file() else None,
        }
    except Exception as exc:
        record.update({"status": "exception", "elapsed_seconds": round(time.time() - started, 3), "error_type": type(exc).__name__, "error": str(exc), "console_log": str(log_path.relative_to(ROOT)), "console_log_sha256": sha256(log_path) if log_path.exists() else None})
    save_json(OUT / "result.json", record)
    save_json(OUT / "execution_status.json", {"status": record["status"], "elapsed_seconds": record.get("elapsed_seconds"), "finished_utc": datetime.now(timezone.utc).isoformat()})

    files = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "file_manifest.json":
            files.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    save_json(OUT / "file_manifest.json", files)
    print(f"L7b-full bounded integration: {record['status']} ({record.get('elapsed_seconds')} seconds)", flush=True)


if __name__ == "__main__":
    main()
