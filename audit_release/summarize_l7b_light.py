# SPDX-License-Identifier: MIT
"""Summarize persisted L7b-light JSON for each control axis."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "audit_release" / "2026-11-14_l7b_integration_fast"
SOURCE_INPUT = ROOT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test" / "pipeline_inputs" / "L16_T2.269185_chain0.csv"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    axes = {}
    for control in ("MC_Update", "Noise_axis"):
        path = BASE / "light" / control / "master_results.json"
        master = json.loads(path.read_text(encoding="utf-8"))
        l7b = ((master.get("prediction_levels") or {}).get("L7b_robustesse") or {})
        axes[control] = {
            "pipeline_status": "ok" if master else "empty",
            "l7b_mode": l7b.get("mode"),
            "l7b_status": l7b.get("status"),
            "verdict": l7b.get("verdict"),
            "checks": l7b.get("checks"),
            "master_results": str(path.relative_to(ROOT)),
            "master_results_sha256": sha256(path),
        }
    result = {
        "status": "light_completed_full_reduced_separate",
        "elapsed_seconds_for_two_controls": 900.79,
        "outer_mode": "fast",
        "control_mode": "multi",
        "input": str(SOURCE_INPUT.relative_to(ROOT)),
        "input_sha256": sha256(SOURCE_INPUT),
        "rows": 200,
        "target": "Abs_magnetization",
        "target_policy": "fixed",
        "axes": axes,
        "interpretation": "L7b verdicts are implementation heuristic outputs, not scientific classifications of Ising criticality.",
        "full_mode_note": "The two-axis full run was not started after measuring about 7 minutes per axis for L7b-light. A separate one-axis, 80-row L7b-full integration is recorded under 2026-11-14_l7b_full_reduced.",
        "exact_executed_runner": str((BASE / "runner_executed_exact.py").relative_to(ROOT)),
        "runner_sha256": sha256(BASE / "runner_executed_exact.py"),
    }
    (BASE / "light_axis_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BASE / "integration_summary.json").write_text(json.dumps({
        "status": result["status"],
        "results": {control: {"verdict": item["verdict"], "checks": item["checks"]} for control, item in axes.items()},
        "elapsed_seconds_for_two_controls": result["elapsed_seconds_for_two_controls"],
        "full_mode_note": result["full_mode_note"],
        "interpretation": result["interpretation"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
