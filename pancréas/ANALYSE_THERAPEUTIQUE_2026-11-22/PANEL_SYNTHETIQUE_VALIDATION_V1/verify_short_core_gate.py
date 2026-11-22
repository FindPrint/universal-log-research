#!/usr/bin/env python
"""Directly confirm the v6.0.1 fast-mode refusal for one 32-row patient series."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PIPELINE = (
    PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20"
    / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source"
    / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
)
INPUT = HERE / "inputs" / "SYN-P01.csv"
SHORT_INPUT = HERE / "inputs" / "SYN-P01_short32.csv"
OUTPUT_DIR = HERE / "short_core_gate_output"
LOG = HERE / "logs" / "short_core_gate.log"
RESULT = HERE / "short_core_gate_check.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pipeline():
    spec = importlib.util.spec_from_file_location("universal_log_v6_0_1_short_gate", PIPELINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load pipeline: {PIPELINE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    frame = pd.read_csv(INPUT)
    short = frame.sort_values("week_from_start", kind="stable").head(32).reset_index(drop=True)
    short.to_csv(SHORT_INPUT, index=False, float_format="%.12g", encoding="utf-8")
    pipeline = load_pipeline()
    caught = None
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with LOG.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            pipeline.run_full_unified_pipeline(
                csv_path=str(SHORT_INPUT),
                target_col="signal_primary",
                control_col="week_from_start",
                control_mode="single",
                target_policy="fixed",
                domain="generic",
                mode="fast",
                n_scenarios=8,
                seed=20261123,
                output_dir=str(OUTPUT_DIR),
                max_workers=1,
                harmonic_validation=False,
                l7b_mode="off",
            )
        except Exception as exc:
            caught = {"type": type(exc).__name__, "message": str(exc)}
    expected = (
        caught is not None
        and caught["type"] == "ValueError"
        and "Série trop courte" in caught["message"]
        and "32 points valides" in caught["message"]
        and "Au moins 50" in caught["message"]
    )
    result = {
        "status": "passed" if expected else "failed",
        "scope": "One generated 32-row patient trajectory; no clinical data.",
        "pipeline_version": getattr(pipeline, "VERSION_MASTER", None),
        "pipeline_sha256": sha256(PIPELINE),
        "input_sha256": sha256(SHORT_INPUT),
        "rows_in_this_patient_series": int(len(short)),
        "rows_if_three_patients_were_pooled": 96,
        "mode": "fast",
        "expected_minimum": 50,
        "observed_core_exception": caught,
        "interpretation": "The actual v6.0.1 full entry point rejected this individual short series. The grouped-panel wrapper separately abstains before calling it for all 15 short patient/control pairs.",
    }
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
