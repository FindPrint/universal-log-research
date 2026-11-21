"""Reproduce the archived nine-control Ising v2 sweep in fixed fast mode."""

import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import sys
import time

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "pipeline_autonomev2.py"
CSV = HERE / "ising_2d_data.csv"
OUT = HERE / "rerun_fixed_fast"
OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("archived_ising_v2", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

frame = pd.read_csv(CSV)
controls = list(frame.select_dtypes(include="number").columns)
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
protocol = {
    "source_sha256": digest(SOURCE),
    "input_sha256": digest(CSV),
    "rows": len(frame),
    "controls": controls,
    "mode": "fast",
    "statistic": "cohen_d",
    "window": 80,
    "optimization": "disabled; same fixed settings for each control",
    "control_role_rule": "selected column is the control; remaining numeric columns are the flux candidates",
}
(OUT / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
records = []
for control in controls:
    started = time.perf_counter()
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            result, *_ = module.run_pipeline(
                "custom",
                str(CSV),
                {"control_col": control, "flux_mapping": {}},
                "fast",
                {"w_size": 80, "test": "cohen_d", "full_triangulation": False, "auto_optimize_threshold": False},
            )
        metadata = result.get("metadata", {})
        item = {
            "control": control,
            "success": bool(result.get("success")),
            "threshold": metadata.get("opt_threshold"),
            "control_label": metadata.get("control_label"),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "error": None,
        }
    except Exception as exc:
        item = {
            "control": control,
            "success": False,
            "threshold": None,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "error": repr(exc),
        }
    item["stdout_tail"] = captured.getvalue()[-1000:]
    records.append(item)
    (OUT / "results.json").write_text(
        json.dumps({"protocol": protocol, "results": records}, indent=2, default=str),
        encoding="utf-8",
    )
    print(control, item["success"], item["threshold"], item["elapsed_seconds"], item["error"])
