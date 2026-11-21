import importlib.util
import json
import pathlib
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-20" / "REPLICATION_P2_010_GEO_2026-11-20" / "pipeline_source" / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
spec = importlib.util.spec_from_file_location("universal_log_v601_mapping_cases", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
frame = pd.DataFrame({"Control": [0.0, 1.0, 0.0], "FluxA": [2.0, 3.0, 4.0], "FluxB": [4.0, 5.0, 6.0]})
cases = {
    "empty_automatic_map": {},
    "explicit_control_alias": {"Alias": "Control"},
    "composite_includes_control": {"Composite": ["Control", "FluxA", "FluxB"]},
    "non_control_source": {"FluxA_alias": "FluxA"},
}
results = {}
for name, mapping in cases.items():
    filtered, exclusions = module._filter_control_from_flux_mapping(frame, mapping, "Control")
    results[name] = {"filtered": filtered, "exclusions": exclusions}
assert results["empty_automatic_map"]["filtered"] == {}
assert results["explicit_control_alias"]["filtered"] == {}
assert results["composite_includes_control"]["filtered"] == {"Composite": ["FluxA", "FluxB"]}
assert results["non_control_source"]["filtered"] == {"FluxA_alias": "FluxA"}
assert all(
    column != "Control"
    for entry in results.values()
    for value in entry["filtered"].values()
    for column in (value if isinstance(value, list) else [value])
)
output = HERE / "results" / "mapping_edge_cases_result.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
