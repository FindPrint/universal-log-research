"""Static compatibility audit of v6.0.1 for repeated-measures patient tables.

This is a source inspection, not a clinical data run. It checks whether the
analysis entry point accepts or applies patient-group boundaries.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PIPELINE = (
    ROOT
    / "pancréas"
    / "ANALYSE_THERAPEUTIQUE_2026-11-20"
    / "REPLICATION_P2_010_GEO_2026-11-20"
    / "pipeline_source"
    / "UNIVERSAL_LOG_v6.0.1_control_flux_exclusion.py"
)


def main() -> None:
    source = PIPELINE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(PIPELINE))
    lines = source.splitlines()
    run = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "run_pipeline"
    )
    params = [arg.arg for arg in run.args.args]
    group_calls = []
    patient_id_names = []
    for node in ast.walk(run):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr.lower() in {"groupby", "group_by"}:
                group_calls.append((node.lineno, func.attr))
        if isinstance(node, ast.Name) and re.search(r"patient|subject|group_id|group_key", node.id, re.I):
            patient_id_names.append((node.lineno, node.id))

    run_lines = lines[run.lineno - 1 : run.end_lineno]
    relevant = {
        "run_pipeline_line": run.lineno,
        "csv_read": next((i + run.lineno for i, s in enumerate(run_lines) if "pd.read_csv(target_path)" in s), None),
        "control_dropna": next((i + run.lineno for i, s in enumerate(run_lines) if "dropna(subset=[control_col])" in s), None),
        "control_vector": next((i + run.lineno for i, s in enumerate(run_lines) if "control_series = df[control_col].values" in s), None),
        "minimum_gate": next((i + run.lineno for i, s in enumerate(run_lines) if "min_required_points = max(" in s), None),
        "mc_axis_call": next((i + run.lineno for i, s in enumerate(run_lines) if "_build_mc_progress_axis(control_series, fluxes_raw, mode_cfg)" in s), None),
        "version": next((i for i, s in enumerate(lines, 1) if s.startswith('VERSION_MASTER = "v6.0.1-')), None),
    }
    fast_mode_line = next((i for i, s in enumerate(lines, 1) if "'fast': {'n_bootstrap': 1" in s), None)
    fast_mode_text = lines[fast_mode_line - 1] if fast_mode_line else ""
    checks = {
        "entry_point_has_no_patient_group_parameter": not any(re.search(r"patient|subject|group", p, re.I) for p in params),
        "entry_point_has_no_groupby_call": not group_calls,
        "entry_point_does_not_reference_patient_group_ids": not patient_id_names,
        "control_vector_is_built_from_all_retained_rows": relevant["control_vector"] is not None and relevant["control_dropna"] is not None,
        "progress_axis_receives_control_and_fluxes_without_group_metadata": relevant["mc_axis_call"] is not None,
        "fast_mode_has_50_minimum": "'min_len': 50" in fast_mode_text,
    }
    result = {
        "pipeline": str(PIPELINE.relative_to(ROOT)),
        "pipeline_sha256": hashlib.sha256(PIPELINE.read_bytes()).hexdigest(),
        "entry_point": "run_pipeline",
        "entry_point_parameters": params,
        "line_references": relevant,
        "fast_mode_line": fast_mode_line,
        "groupby_calls": group_calls,
        "patient_group_references_inside_entry_point": patient_id_names,
        "checks": checks,
        "static_audit_passed": all(checks.values()),
        "scope": "Source-level compatibility check only; no biological data were analyzed.",
    }
    output = Path(__file__).with_name("V6_0_1_GROUPED_INPUT_AUDIT.json")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["static_audit_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
