import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
RESULTS = HERE / "results"
RESULTS.mkdir(parents=True, exist_ok=True)
CSV = RESULTS / "synthetic_nonmonotone_control.csv"

x = np.linspace(0.0, 1.0, 120)
control = x + 0.2 * np.sin(12 * np.pi * x)
pd.DataFrame({
    "Control": control,
    "FluxA": np.sin(8 * np.pi * x) + 0.05 * np.cos(53 * x),
    "FluxB": np.cos(4 * np.pi * x),
}).to_csv(CSV, index=False)

spec = importlib.util.spec_from_file_location("universal_log_v601_regression", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
mapping = {"control_col": "Control", "flux_mapping": {"Control_as_flux": "Control", "FluxA": "FluxA"}}
captured = io.StringIO()
started = time.perf_counter()
with contextlib.redirect_stdout(captured):
    result, features, fluxes, fluxes_ui = module.run_pipeline(
        "custom", str(CSV), mapping, "fast",
        {"auto_optimize_threshold": False, "full_triangulation": False, "random_seed": 42},
    )

record = {
    "purpose": "Synthetic integration regression: selected nonmonotone control must not also be a flux.",
    "source": SOURCE.name,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "pipeline_version": module.VERSION_MASTER,
    "input": CSV.name,
    "input_sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(),
    "n": len(features),
    "control": "Control",
    "control_monotone_increasing": bool(np.all(np.diff(control) >= 0)),
    "control_monotone_decreasing": bool(np.all(np.diff(control) <= 0)),
    "control_descending_steps": int(np.sum(np.diff(control) < 0)),
    "control_ascending_steps": int(np.sum(np.diff(control) > 0)),
    "mapping": mapping,
    "flux_keys": list(fluxes),
    "control_as_flux_present": "Control_as_flux" in fluxes,
    "success": bool(result.get("success")),
    "metadata_exclusions": result.get("metadata", {}).get("control_flux_exclusions", []),
    "elapsed_seconds": round(time.perf_counter() - started, 3),
    "captured_warning": "[CONTROL-FLUX-EXCLUDED]" in captured.getvalue(),
}
(RESULTS / "control_flux_exclusion_result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps(record, indent=2))
assert record["success"]
assert not record["control_monotone_increasing"] and not record["control_monotone_decreasing"]
assert "Control_as_flux" not in record["flux_keys"]
assert "FluxA" in record["flux_keys"]
assert record["captured_warning"]
assert any(item.get("column") == "Control" for item in record["metadata_exclusions"])
