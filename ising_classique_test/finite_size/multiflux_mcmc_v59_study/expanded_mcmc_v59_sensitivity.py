"""Expanded Ising MCMC sensitivity study for the user-supplied v5.9 source.

The source is preserved. A derived copy changes only the landscape scan
resolution (120 -> 24) to match the archived v5.8 experiment cost/settings.
Raw trajectories, sampled inputs, run logs, hashes, and outcomes are retained.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
TEST_DIR = PROJECT / "ising_classique_test"
FINITE = TEST_DIR / "finite_size"
SOURCE_V59 = PROJECT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py"
SOURCE_V58 = PROJECT / "UNIVERSAL_LOG_v5.8.py"
PREVIOUS_HELPER = TEST_DIR / "multiflux_mcmc_pipeline_test.py"
PREVIOUS_OUT = FINITE / "multiflux_mcmc_pipeline_test"
OUT = HERE / "expanded_runs"
RAW = OUT / "raw_trajectories"
INPUTS = OUT / "pipeline_inputs"
LOGS = OUT / "pipeline_logs"
FEATURES = OUT / "feature_landscapes"
RUNTIME = OUT / "runtime"
TC = float(2.0 / np.log(1.0 + np.sqrt(2.0)))
SIZES = (16, 32, 48)
TEMPERATURES = tuple(float(x) for x in np.arange(2.24, 2.4401, 0.02)) + (TC,)
N_CHAINS = 5
N_BURN = 1000
N_MEASURE = 8000
PIPELINE_STRIDE = 20
WINDOW_SIZE = 40
LANDSCAPE_POINTS = 24
PIPELINE_SEED = 20261108
COMMON_FLUXES = ["Abs_magnetization", "M_squared", "M_fourth", "Cluster_fraction", "Noise_flux"]
PHYSICAL_NO_NOISE = ["Abs_magnetization", "M_squared", "M_fourth", "Cluster_fraction"]
FULL_FLUXES = [
    "Energy_per_spin", "Magnetization", "Abs_magnetization", "M_squared",
    "M_fourth", "Nearest_neighbor_correlation", "Cluster_fraction",
    "Noise_axis", "Noise_flux", "Abs_magnetization_shuffled",
]
ALT_AXES = ["Energy_per_spin", "Magnetization", "Nearest_neighbor_correlation", "Noise_axis", "Abs_magnetization_shuffled"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def append_jsonl(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prepare_runtime() -> tuple[Path, str]:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    derived = RUNTIME / "UNIVERSAL_LOG_v5_9_exp_landscape24.py"
    source = SOURCE_V59.read_text(encoding="utf-8")
    old_line = "scan_points = np.linspace(progress.min(), progress.max(), 120)"
    new_line = "scan_points = np.linspace(progress.min(), progress.max(), 24)"
    if source.count(old_line) != 1:
        raise RuntimeError(f"Expected exactly one landscape resolution line, found {source.count(old_line)}")
    derived.write_text(source.replace(old_line, new_line), encoding="utf-8")
    patch_file = RUNTIME / "v5.9_landscape24.patch.txt"
    patch_file.write_text(
        "Only source change in derived experiment copy:\n- " + old_line + "\n+ " + new_line + "\n",
        encoding="utf-8",
    )
    return derived, sha256(derived)


def build_run_specs() -> list[dict]:
    specs: list[dict] = []

    def add(L: int, T: float, chain: int, control: str, set_name: str, fluxes: list[str], family: str):
        specs.append({
            "L": int(L), "T": float(T), "Chain": int(chain), "control": control,
            "flux_set": set_name, "flux_names": list(fluxes), "family": family,
        })

    for L in SIZES:
        for T in TEMPERATURES:
            add(L, T, 0, "MC_Update", "common", COMMON_FLUXES, "temperature_grid")
    for L in SIZES:
        for chain in range(1, N_CHAINS):
            add(L, TC, chain, "MC_Update", "common", COMMON_FLUXES, "chain_repeats_at_Tc")
    for L in SIZES:
        for axis in ALT_AXES:
            add(L, TC, 0, axis, "common", COMMON_FLUXES, "axis_contrast_at_Tc")
    for L in (32, 48):
        add(L, TC, 0, "MC_Update", "all_fluxes", FULL_FLUXES, "full_flux_at_Tc")
    ablations = [
        ("target_absM_only", ["Abs_magnetization"]),
        ("order_parameter_family", ["Abs_magnetization", "M_squared", "M_fourth"]),
        ("physical_without_noise", PHYSICAL_NO_NOISE),
        ("all_fluxes", FULL_FLUXES),
    ]
    for chain in range(N_CHAINS):
        for set_name, fluxes in ablations:
            add(16, TC, chain, "MC_Update", set_name, fluxes, "flux_ablation_L16_Tc")
    return specs


def config_id(spec: dict, prefix: str = "v59") -> str:
    t = f"{spec['T']:.9f}".replace(".", "p")
    axis = spec["control"].replace(" ", "_")
    return f"{prefix}_L{spec['L']}_T{t}_C{spec['Chain']}_{axis}_{spec['flux_set']}"


def main() -> None:
    for directory in (OUT, RAW, INPUTS, LOGS, FEATURES, RUNTIME):
        directory.mkdir(parents=True, exist_ok=True)
    journal = HERE / "JOURNAL_DECISIONS.jsonl"
    run_journal = OUT / "RUN_JOURNAL.jsonl"
    derived, derived_hash = prepare_runtime()

    # Load the v5.8 taxonomy as an explicitly external interpretation layer.
    v58 = load_module("taxonomy_v58_for_v59_study", SOURCE_V58)
    v59 = load_module("universal_v59_exp_landscape24", derived)
    previous = load_module("previous_multiflux_experiment_helper", PREVIOUS_HELPER)
    previous.ul = v59
    previous.OUT = OUT
    previous.LOGS = LOGS
    previous.WINDOW_SIZE = WINDOW_SIZE
    previous.LANDSCAPE_SCAN_POINTS = LANDSCAPE_POINTS
    previous.PIPELINE_SEED = PIPELINE_SEED
    v59.PARAMETERS["modes"]["fast"]["w_size"] = WINDOW_SIZE

    protocol = {
        "protocol": "predeclared expanded v5.9 Ising MCMC multi-axis/multi-flux study",
        "source_v59": str(SOURCE_V59), "source_v59_sha256": sha256(SOURCE_V59),
        "derived_runtime": str(derived), "derived_runtime_sha256": derived_hash,
        "source_v58_taxonomy_sha256": sha256(SOURCE_V58),
        "helper_sha256": sha256(PREVIOUS_HELPER),
        "raw_simulation": "2D zero-field Ising Wolff cluster updates; one saved row per cluster update",
        "sizes": list(SIZES), "temperatures": list(TEMPERATURES), "Tc_exact": TC,
        "n_chains_per_cell": N_CHAINS, "burn_updates": N_BURN, "measure_updates": N_MEASURE,
        "pipeline_stride": PIPELINE_STRIDE, "pipeline_rows_per_trajectory": math.ceil(N_MEASURE / PIPELINE_STRIDE),
        "window_size_rows": WINDOW_SIZE, "landscape_scan_points": LANDSCAPE_POINTS,
        "pipeline_seed": PIPELINE_SEED,
        "core_call_count_expected": 85, "matched_v58_v59_call_count_expected": 20,
        "threshold_policy": "v5.9 L7b thresholds are implementation heuristics, not scientifically calibrated here",
        "external_d_kind_policy": "Any d_kind label uses the v5.8 registry externally because v5.9 has no native typed registry.",
        "predeclared_hypotheses": [
            "H1: MCMC thermodynamic estimates are compared with archived finite-size estimates and their uncertainty; no binary pass threshold.",
            "H2: same data/fluxes under alternate controls may change pipeline outputs; values and chain repeats are reported without causal interpretation.",
            "H3: flux composition/redundancy effects are compared across five L16,Tc chains.",
            "H4: regime labels over the temperature grid are descriptive and exploratory, not a validated criticality detector.",
            "H5: v5.9 is compared with archived v5.8 on the same 20 sampled CSVs/configurations.",
        ],
    }
    (OUT / "protocol_and_provenance.json").write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8")
    append_jsonl(journal, {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "expanded_v59_execution_started", "protocol": str(OUT / "protocol_and_provenance.json"),
        "runtime_copy_sha256": derived_hash, "planned_core_runs": 85, "planned_matched_runs": 20,
        "decision": "User requested continuation and complete traceability; all outputs go to a new study directory.",
    })
    append_jsonl(run_journal, {"event": "protocol_frozen", **protocol})

    # Set generation globals in the already reviewed trajectory helper.
    previous.N_BURN = N_BURN
    previous.N_MEASURE = N_MEASURE
    previous.PIPELINE_STRIDE = PIPELINE_STRIDE
    previous.SIZES = SIZES
    previous.TEMPERATURES = TEMPERATURES
    previous.N_CHAINS = N_CHAINS
    trajectory_frames: dict[tuple[int, float], list[tuple[int, pd.DataFrame]]] = {}
    raw_manifest = []
    relationship_rows = []
    lag_rows = []
    print(f"Creating {len(SIZES) * len(TEMPERATURES) * N_CHAINS} independent trajectories...", flush=True)
    for L in SIZES:
        for T in TEMPERATURES:
            entries = []
            for chain in range(N_CHAINS):
                frame = previous.generate_frame(L, T, chain)
                raw_path = RAW / f"L{L}_T{T:.9f}_chain{chain}.csv"
                frame.to_csv(raw_path, index=False, float_format="%.17g")
                raw_hash = sha256(raw_path)
                seed = int(frame["Seed"].iloc[0])
                raw_manifest.append({
                    "L": L, "T": T, "Chain": chain, "seed": seed,
                    "n_rows": len(frame), "path": str(raw_path), "sha256": raw_hash,
                })
                entries.append((chain, frame))
                relationship_rows.extend(previous.make_relationship_rows(frame, L, T, chain))
                for flux in ["Energy_per_spin", "Magnetization", "Abs_magnetization", "Cluster_fraction", "Abs_magnetization_shuffled"]:
                    lag_rows.append({"L": L, "T": T, "Chain": chain, "flux": flux, **previous.integrate_autocorrelation(frame[flux])})
                sampled = frame.iloc[::PIPELINE_STRIDE].reset_index(drop=True)
                input_path = INPUTS / f"L{L}_T{T:.9f}_chain{chain}.csv"
                sampled.to_csv(input_path, index=False, float_format="%.17g")
                raw_manifest[-1]["pipeline_input_path"] = str(input_path)
                raw_manifest[-1]["pipeline_input_sha256"] = sha256(input_path)
                if chain % 2 == 1:
                    del frame
            trajectory_frames[(L, T)] = entries
            print(f"  L={L}, T={T:.9f}: {N_CHAINS} chains × {N_MEASURE} cluster updates", flush=True)
    pd.DataFrame(raw_manifest).to_csv(OUT / "trajectory_manifest.csv", index=False)
    pd.DataFrame(relationship_rows).to_csv(OUT / "flux_relationships_spearman.csv", index=False)
    pd.DataFrame(lag_rows).to_csv(OUT / "flux_autocorrelation_diagnostics.csv", index=False)
    chain_physics, cell_physics = previous.physical_checks(trajectory_frames)
    chain_physics.to_csv(OUT / "mcmc_physical_estimates_by_chain.csv", index=False)
    cell_physics.to_csv(OUT / "mcmc_physical_comparison_to_reference.csv", index=False)
    append_jsonl(run_journal, {
        "event": "trajectories_complete", "count": len(raw_manifest),
        "total_rows": int(sum(row["n_rows"] for row in raw_manifest)),
        "manifest": str(OUT / "trajectory_manifest.csv"),
    })

    # The trajectory table occupies several hundred MB; keep it alive only as long as needed.
    del trajectory_frames

    run_specs = build_run_specs()
    if len(run_specs) != 85:
        raise RuntimeError(f"Frozen design expected 85 core runs, got {len(run_specs)}")
    summaries = []
    estimator_rows = []
    run_events = []
    taxonomy = getattr(v58, "ESTIMATOR_D_KIND", {})
    print(f"Running the v5.9 derived copy on {len(run_specs)} predeclared configurations...", flush=True)
    for index, spec in enumerate(run_specs, start=1):
        run_id = config_id(spec)
        input_path = INPUTS / f"L{spec['L']}_T{spec['T']:.9f}_chain{spec['Chain']}.csv"
        frame = pd.read_csv(input_path)
        start = time.monotonic()
        summary, rows, _typed = previous.pipeline_run(
            run_id, input_path, frame, spec["L"], spec["T"], spec["Chain"],
            spec["control"], spec["flux_set"], spec["flux_names"],
        )
        summary["landscape_scan_points_source_metadata"] = summary.get("landscape_scan_points")
        summary["landscape_scan_points_effective_observed"] = summary.get("n_landscape_rows")
        summary["landscape_metadata_consistent"] = (
            summary.get("landscape_scan_points") == summary.get("n_landscape_rows")
        )
        summary.update({"family": spec["family"], "pipeline_input_sha256": sha256(input_path)})
        for row in rows:
            row["family"] = spec["family"]
            row["d_kind_v59_native"] = row.get("d_kind")
            row["d_kind_external_v58"] = taxonomy.get(row["estimator"])
            row["taxonomy_provenance"] = "external v5.8 ESTIMATOR_D_KIND registry; not native v5.9 output"
        elapsed = time.monotonic() - start
        summaries.append(summary)
        estimator_rows.extend(rows)
        event = {
            "event": "pipeline_run_complete", "index": index, "total": len(run_specs),
            "run_id": run_id, "configuration": spec, "status": summary.get("status"),
            "input_path": str(input_path), "input_sha256": sha256(input_path),
            "log_path": str(LOGS / f"{run_id}.log"), "elapsed_seconds": elapsed,
            "n_estimators_returned": len(rows), "summary": summary,
        }
        append_jsonl(run_journal, event)
        run_events.append(event)
        print(f"  [{index}/{len(run_specs)}] {run_id}: {summary.get('status')} ({elapsed:.1f}s)", flush=True)
        pd.DataFrame(summaries).to_csv(OUT / "pipeline_axis_flux_matrix.partial.csv", index=False)
        pd.DataFrame(estimator_rows).to_csv(OUT / "pipeline_estimator_outputs.partial.csv", index=False)

    core_matrix = pd.DataFrame(summaries)
    core_estimators = pd.DataFrame(estimator_rows)
    core_matrix.to_csv(OUT / "pipeline_axis_flux_matrix.csv", index=False)
    core_estimators.to_csv(OUT / "pipeline_estimator_outputs.csv", index=False)
    core_estimators[core_estimators["d_kind_external_v58"].notna()].groupby(
        ["run_id", "L", "T", "Chain", "control", "flux_set", "d_kind_external_v58"], dropna=False
    )["raw_median"].agg(["median", "count"]).reset_index().to_csv(
        OUT / "estimator_group_medians_external_v58_taxonomy.csv", index=False
    )

    # Matched non-regression replay on the exact 20 archived v5.8 pipeline inputs.
    old_matrix = pd.read_csv(PREVIOUS_OUT / "pipeline_axis_flux_matrix.csv")
    old_estimators = pd.read_csv(PREVIOUS_OUT / "pipeline_estimator_outputs.csv")
    if len(old_matrix) != 20:
        raise RuntimeError(f"Expected 20 archived v5.8 configs, found {len(old_matrix)}")
    matched_summaries = []
    matched_estimators = []
    print("Replaying the 20 archived inputs for paired v5.8/v5.9 comparison...", flush=True)
    for index, old in old_matrix.iterrows():
        L, T, chain = int(old["L"]), float(old["T"]), int(old["Chain"])
        old_id = str(old["run_id"])
        input_path = PREVIOUS_OUT / "pipeline_inputs" / f"L{L}_T{T:.6f}_chain{chain}.csv"
        frame = pd.read_csv(input_path)
        new_id = config_id({"L": L, "T": T, "Chain": chain, "control": str(old["control"]), "flux_set": str(old["flux_set"])}, "matched59")
        flux_names = [part for part in str(old["flux_names"]).split(",") if part]
        summary, rows, _typed = previous.pipeline_run(
            new_id, input_path, frame, L, T, chain, str(old["control"]), str(old["flux_set"]), flux_names,
        )
        summary["landscape_scan_points_source_metadata"] = summary.get("landscape_scan_points")
        summary["landscape_scan_points_effective_observed"] = summary.get("n_landscape_rows")
        summary["landscape_metadata_consistent"] = (
            summary.get("landscape_scan_points") == summary.get("n_landscape_rows")
        )
        summary.update({"paired_v58_run_id": old_id, "family": "matched_v58_v59", "pipeline_input_sha256": sha256(input_path)})
        for row in rows:
            row["paired_v58_run_id"] = old_id
            row["d_kind_v59_native"] = row.get("d_kind")
            row["d_kind_external_v58"] = taxonomy.get(row["estimator"])
        matched_summaries.append(summary)
        matched_estimators.extend(rows)
        append_jsonl(run_journal, {
            "event": "matched_version_run_complete", "index": int(index + 1), "total": 20,
            "paired_v58_run_id": old_id, "v59_run_id": new_id, "status": summary.get("status"),
            "input_path": str(input_path), "input_sha256": sha256(input_path),
            "n_estimators_returned": len(rows), "summary": summary,
        })
        print(f"  [{index+1}/20] {old_id}: {summary.get('status')}", flush=True)
    pd.DataFrame(matched_summaries).to_csv(OUT / "matched_v59_run_summaries.csv", index=False)
    matched_df = pd.DataFrame(matched_estimators)
    matched_df.to_csv(OUT / "matched_v59_estimator_outputs.csv", index=False)
    paired = old_estimators.merge(
        matched_df[["paired_v58_run_id", "estimator", "raw_median"]].rename(columns={"raw_median": "raw_median_v59"}),
        left_on=["run_id", "estimator"], right_on=["paired_v58_run_id", "estimator"], how="outer", indicator=True,
    )
    paired["difference_v59_minus_v58"] = paired["raw_median_v59"] - paired["raw_median"]
    paired["absolute_difference"] = paired["difference_v59_minus_v58"].abs()
    paired["within_1e-6_stored_precision"] = paired["absolute_difference"].le(1e-6)
    paired.to_csv(OUT / "v58_v59_matched_estimator_comparison.csv", index=False)

    # Descriptive aggregation tables for temperature and axis dependence.
    if not core_matrix.empty:
        core_matrix.groupby(["L", "T", "control", "flux_set", "family"], dropna=False).agg(
            n_runs=("status", "size"), n_ok=("status", lambda x: int((x == "ok").sum())),
            d_sat_mean=("d_sat", "mean"), d_crit_mean=("d_crit", "mean"),
            d_div_mean=("d_div", "mean"), d_null_mean=("d_null", "mean"),
        ).reset_index().to_csv(OUT / "pipeline_descriptive_group_summary.csv", index=False)
    core_matrix.to_csv(OUT / "pipeline_axis_flux_matrix.csv", index=False)
    ok_core = int(core_matrix.get("status", pd.Series(dtype=str)).eq("ok").sum())
    ok_matched = int(pd.DataFrame(matched_summaries).get("status", pd.Series(dtype=str)).eq("ok").sum())
    exact_summary = {
        "core_runs_planned": 85, "core_runs_completed": int(len(core_matrix)), "core_runs_ok": ok_core,
        "matched_runs_planned": 20, "matched_runs_completed": len(matched_summaries), "matched_runs_ok": ok_matched,
        "matched_estimator_rows": int(len(paired)),
        "matched_rows_with_both_versions": int(paired["_merge"].eq("both").sum()),
        "matched_rows_within_1e-6": int(paired["within_1e-6_stored_precision"].fillna(False).sum()),
        "matched_max_abs_difference": float(paired["absolute_difference"].max()) if paired["absolute_difference"].notna().any() else None,
        "generated_trajectory_count": len(raw_manifest),
        "generated_measurement_rows": int(sum(row["n_rows"] for row in raw_manifest)),
        "source_v59_sha256": sha256(SOURCE_V59), "derived_runtime_sha256": sha256(derived),
    }
    (OUT / "execution_summary.json").write_text(json.dumps(exact_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    append_jsonl(run_journal, {"event": "study_complete", **exact_summary})
    append_jsonl(journal, {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "expanded_v59_execution_complete", "summary": exact_summary,
        "outputs": str(OUT),
    })
    output_manifest = []
    for path in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "output_manifest.csv"):
        output_manifest.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    pd.DataFrame(output_manifest).to_csv(OUT / "output_manifest.csv", index=False)
    print(json.dumps(exact_summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
