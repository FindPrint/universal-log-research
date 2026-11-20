#!/usr/bin/env python
"""Exploratory L=64 two-column control, specified in the adjacent addendum."""
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
PIPELINE_SOURCE = PROJECT / "pancréas" / "Archive complète PDAC v6 — ZIP" / "universal_v6.0.0_cohen.py"
ADDENDUM = HERE / "ADDENDUM_CONTROLE_FLUX_AVEUGLE.md"
INPUT_SOURCE = HERE / "inputs" / "ising_L64_physical.csv"
INPUT = HERE / "inputs" / "ising_L64_only_control_target.csv"
OUTPUT = HERE / "runs" / "blind_flux_L64_temperature_energy"
LOG = HERE / "runs" / "blind_flux_L64_temperature_energy.log"
MANIFEST = HERE / "blind_flux_sensitivity_manifest.json"
SEED = 20261115


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    frame = pd.read_csv(INPUT_SOURCE)[["Temperature", "Energy_per_spin"]].copy()
    frame.to_csv(INPUT, index=False, float_format="%.12g", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("universal_log_v6_blind_flux", PIPELINE_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger le pipeline : {PIPELINE_SOURCE}")
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    status = "complete"
    error = None
    try:
        with LOG.open("w", encoding="utf-8") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = pipeline.run_full_unified_pipeline(
                csv_path=str(INPUT), target_col="Energy_per_spin", control_col="Temperature",
                control_mode="single", target_policy="fixed", domain="physics", mode="fast",
                seed=SEED, output_dir=str(OUTPUT), max_workers=1,
                triangulation_estimators="default", l7b_mode="light",
            )
        (OUTPUT / "master_results.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    except Exception as exc:
        status = "error"
        error = repr(exc)
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write("\n" + traceback.format_exc())
    manifest = {
        "status": status, "error": error,
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": time.perf_counter() - clock,
        "l_size": 64, "input_rows": int(len(frame)), "input_columns": list(frame.columns),
        "seed": SEED, "mode": "fast", "target": "Energy_per_spin", "control": "Temperature",
        "control_mode": "single", "target_policy": "fixed", "max_workers": 1,
        "triangulation": "default", "l7b_mode": "light", "expected_mc_iterations": 12,
        "addendum_path": str(ADDENDUM.resolve()), "addendum_sha256": sha256(ADDENDUM),
        "script_path": str(Path(__file__).resolve()), "script_sha256": sha256(Path(__file__).resolve()),
        "pipeline_path": str(PIPELINE_SOURCE.resolve()), "pipeline_sha256": sha256(PIPELINE_SOURCE),
        "input_source_path": str(INPUT_SOURCE.resolve()), "input_source_sha256": sha256(INPUT_SOURCE),
        "input_path": str(INPUT.resolve()), "input_sha256": sha256(INPUT),
        "output_path": str(OUTPUT.resolve()), "log_path": str(LOG.resolve()),
        "python": sys.version, "python_executable": sys.executable,
        "venv_prefix": sys.prefix, "platform": platform.platform(),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{status}: {OUTPUT}")
    print(f"durée={manifest['elapsed_seconds']:.1f}s; manifeste={MANIFEST}")
    if error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
