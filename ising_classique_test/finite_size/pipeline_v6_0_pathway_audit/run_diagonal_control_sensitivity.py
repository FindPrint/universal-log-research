#!/usr/bin/env python
"""Run the predeclared L=16 case where control equals target."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PIPELINE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
ADDENDUM = HERE / "ADDENDUM_AXE_CONTROLE_EGAL_CIBLE.md"
INPUT = HERE / "inputs" / "ising_L16_physical.csv"
OUTPUT = HERE / "runs" / "diagonal_L16_energy_as_target_and_control"
LOG = HERE / "runs" / "diagonal_L16_energy_as_target_and_control.log"
MANIFEST = HERE / "diagonal_sensitivity_manifest.json"
SEED = 20261115


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    data = pd.read_csv(INPUT)
    spec = importlib.util.spec_from_file_location("universal_log_v6_diagonal_audit", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger le pipeline : {PIPELINE}")
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    status, error = "complete", None
    try:
        with LOG.open("w", encoding="utf-8") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = pipeline.run_full_unified_pipeline(
                csv_path=str(INPUT), target_col="Energy_per_spin", control_col="Energy_per_spin",
                control_mode="single", target_policy="fixed", domain="physics", mode="fast",
                seed=SEED, output_dir=str(OUTPUT), max_workers=1,
                triangulation_estimators="default", l7b_mode="light",
            )
        (OUTPUT / "master_results.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    except Exception as exc:
        status, error = "error", repr(exc)
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write("\n" + traceback.format_exc())
    manifest = {
        "status": status, "error": error,
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": time.perf_counter() - clock, "L": 16, "n_rows": len(data),
        "target": "Energy_per_spin", "control": "Energy_per_spin", "diagonal": True,
        "target_policy": "fixed", "mode": "fast", "seed": SEED, "max_workers": 1,
        "triangulation": "default", "l7b_mode": "light", "expected_mc_iterations": 12,
        "addendum": str(ADDENDUM.resolve()), "addendum_sha256": sha256(ADDENDUM),
        "script": str(Path(__file__).resolve()), "script_sha256": sha256(Path(__file__).resolve()),
        "pipeline": str(PIPELINE.resolve()), "pipeline_sha256": sha256(PIPELINE),
        "input": str(INPUT.resolve()), "input_sha256": sha256(INPUT),
        "output": str(OUTPUT.resolve()), "log": str(LOG.resolve()),
        "python": sys.version, "python_executable": sys.executable,
        "venv_prefix": sys.prefix, "platform": platform.platform(),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{status}: {OUTPUT}; durée={manifest['elapsed_seconds']:.1f}s")
    if error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
