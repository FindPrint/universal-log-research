"""Reproducible, synthetic edge-case audit of the v5.9 L7b pure helpers.

This does not run the predictive pipeline or validate scientific thresholds.
It records how source-code rules classify missing and signed values.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py"
OUT = PROJECT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_v59_study"


def main():
    raw = SOURCE.read_bytes()
    spec = importlib.util.spec_from_file_location("universal_v59_l7b_edge_audit", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    reference = {"T0_pct": 50.0, "consensus_direction": "up", "Delta": 2.0, "L7_status": "ok"}
    same = dict(reference)
    scenarios = [
        ("available_reference_shuffle_preserves_signal", reference, same, same, same),
        ("seed_rerun_missing_T0", reference,
         {**same, "T0_pct": None}, same, same),
        ("window_rerun_missing_T0", reference, same,
         {**same, "T0_pct": None}, same),
        ("reference_Delta_missing", {**reference, "Delta": None}, same, same,
         {**same, "Delta": 1.0}),
        ("signed_Delta_magnitude_halved", {**reference, "Delta": -2.0},
         {**same, "Delta": -2.0}, {**same, "Delta": -2.0},
         {**same, "Delta": -1.0}),
        ("positive_Delta_shuffled_below_half", reference, same, same,
         {**same, "Delta": 0.8}),
    ]
    rows = []
    for name, ref, seed, window, shuffled in scenarios:
        result = module.level_robustness_L7b_from_summaries(
            ref, seed, window, shuffled, None
        )
        rows.append({
            "case": name,
            "inputs": {"reference": ref, "seed_alt": seed, "window_80": window, "shuffled": shuffled},
            "observed_verdict": result.get("verdict"),
            "checks": result.get("checks"),
        })

    l7 = {
        "status": "ok", "l1_horizon_stability": 0.8,
        "l3_horizon_stability": 0.8, "l5_horizon_stability": 0.8,
        "semantic_split": {"disagreement": False}, "contradiction_penalty": 0.0,
    }
    light = module.level_robustness_L7b_light(
        {}, {}, {}, l7, {"t0_std": 10.0},
        {"T_0_Monte_Carlo_Central": 50.0}, {"Delta_tension": 2.0},
    )
    rows.append({
        "case": "light_values_exactly_at_implementation_cutoffs",
        "inputs": {"L7": l7, "walkforward": {"t0_std": 10.0}},
        "observed_verdict": light.get("verdict"),
        "checks": {k: v for k, v in (light.get("checks") or {}).items() if isinstance(v, dict)},
    })

    result = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "version": module.VERSION_MASTER,
        "test_kind": "direct synthetic inputs to pure helper functions; not a pipeline integration test",
        "scientific_validity_of_thresholds": "not evaluated by these edge cases",
        "scenarios": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "l7b_synthetic_edge_cases.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {OUT / 'l7b_synthetic_edge_cases.json'}")


if __name__ == "__main__":
    main()
