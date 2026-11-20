"""End-to-end L7b light/full integration on multi-column Ising controls."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit_release" / "2026-11-14_l7b_integration_fast"
SOURCE = ROOT / "audit_release" / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
INPUT = ROOT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test" / "pipeline_inputs" / "L16_T2.269185_chain0.csv"
SEED = 20261108
CONTROLS = ["MC_Update", "Noise_axis"]
TARGET = "Abs_magnetization"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("universal_log_v591_l7b_integration", path)
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


def main() -> None:
    if not INPUT.is_file() or not SOURCE.is_file():
        raise FileNotFoundError("Missing v5.9.1 source or archived Ising CSV")
    if OUT.exists() and any(p.is_file() for p in OUT.rglob("*")):
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    for mode in ("light", "full"):
        (OUT / mode).mkdir(exist_ok=True)

    import pandas as pd
    frame = pd.read_csv(INPUT)
    if any(col not in frame.columns for col in [TARGET, *CONTROLS]):
        raise AssertionError("Required target/control columns are missing")

    protocol = {
        "title": "v5.9.1 L7b end-to-end integration on the archived Ising CSV",
        "status": "predeclared_before_execution",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hypotheses_not_results": [
            "H1: L7b-light returns one structured result per requested control without launching robustness re-runs.",
            "H2: L7b-full executes alternate-seed, 80-percent window, shuffled-target, and log-scale checks for each requested control, with each check represented as ROBUSTE, FRAGILE, or INDETERMINE.",
            "H3: MC_Update and Noise_axis are treated as distinct analysis axes with a fixed shared target; differences across axes are descriptive and not causal.",
        ],
        "input": str(INPUT.relative_to(ROOT)),
        "input_sha256": sha256(INPUT),
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "rows": len(frame),
        "target": TARGET,
        "controls": CONTROLS,
        "shared_target_policy": "fixed",
        "control_mode": "multi",
        "seed": SEED,
        "other_call_arguments": "domain=generic, risk=moderate, horizon=None, horizons=None, n_scenarios=48, mode=fast (selected after the default full mode failed to return in 15 minutes); output_dir is mode-specific; max_workers=1.",
        "deviation_record": "A separate outer-mode=full light run was stopped at 15 minutes with no output and retained in audit_release/2026-11-14_l7b_integration/ATTEMPT_01_OUTER_FULL_TIMEOUT.txt. The light/full comparison below uses the faster outer mode so the L7b mode remains the tested factor.",
        "scope_limit": "This verifies software orchestration and output semantics on one archived synthetic Ising data file. It is not calibration of L7b thresholds or evidence of physical criticality detection.",
    }
    save_json(OUT / "protocol_predeclared.json", protocol)

    module = load_module(SOURCE)
    results = {}
    for l7b_mode in ("light", "full"):
        log_path = OUT / f"{l7b_mode}_console.log"
        start = time.time()
        try:
            with log_path.open("w", encoding="utf-8", newline="\n") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                result = module.run_full_unified_pipeline(
                    csv_path=str(INPUT),
                    target_col=TARGET,
                    control_columns=CONTROLS,
                    control_mode="multi",
                    target_policy="fixed",
                    seed=SEED,
                    output_dir=str(OUT / l7b_mode),
                    mode="fast",
                    max_workers=1,
                    l7b_mode=l7b_mode,
                )
            elapsed = round(time.time() - start, 3)
            l7b_results = walk_l7b(result)
            mode_record = {
                "status": "returned",
                "elapsed_seconds": elapsed,
                "result_type": type(result).__name__,
                "result_keys": sorted(result.keys()) if isinstance(result, dict) else None,
                "l7b_occurrences": l7b_results,
                "result": result,
                "console_log": str(log_path.relative_to(ROOT)),
                "console_log_sha256": sha256(log_path),
            }
        except Exception as exc:
            elapsed = round(time.time() - start, 3)
            mode_record = {
                "status": "exception",
                "elapsed_seconds": elapsed,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "console_log": str(log_path.relative_to(ROOT)),
                "console_log_sha256": sha256(log_path) if log_path.exists() else None,
            }
        results[l7b_mode] = mode_record
        save_json(OUT / f"{l7b_mode}_result.json", mode_record)
        print(f"{l7b_mode}: {mode_record['status']} ({elapsed}s), L7b occurrences={len(mode_record.get('l7b_occurrences', []))}", flush=True)

    save_json(OUT / "integration_summary.json", {
        "status": "completed" if all(v["status"] == "returned" for v in results.values()) else "partial_or_failed",
        "results": {k: {"status": v["status"], "elapsed_seconds": v["elapsed_seconds"], "l7b_occurrences": v.get("l7b_occurrences"), "error": v.get("error")} for k, v in results.items()},
        "interpretation": "Integration behavior only. Verdict labels are not validated scientific classifications.",
    })


if __name__ == "__main__":
    main()
