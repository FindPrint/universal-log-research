"""Hash all study artifacts and audit the retained run/input ledgers."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "expanded_runs"
PROJECT = HERE.parents[2]
PREVIOUS_OUT = PROJECT / "ising_classique_test" / "finite_size" / "multiflux_mcmc_pipeline_test"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    journal = HERE / "JOURNAL_DECISIONS.jsonl"
    run_journal = OUT / "RUN_JOURNAL.jsonl"
    run_events = [json.loads(line) for line in run_journal.read_text(encoding="utf-8").splitlines() if line.strip()]
    core_events = [x for x in run_events if x.get("event") == "pipeline_run_complete"]
    matched_events = [x for x in run_events if x.get("event") == "matched_version_run_complete"]
    trajectory = pd.read_csv(OUT / "trajectory_manifest.csv")
    raw_ok = all(Path(row.path).is_file() and digest(Path(row.path)) == row.sha256 for row in trajectory.itertuples())
    sampled_ok = all(Path(row.pipeline_input_path).is_file() and digest(Path(row.pipeline_input_path)) == row.pipeline_input_sha256 for row in trajectory.itertuples())
    comparison = pd.read_csv(OUT / "v58_v59_matched_estimator_comparison.csv")
    execution = json.loads((OUT / "execution_summary.json").read_text(encoding="utf-8"))
    checks = {
        "trajectory_rows": int(len(trajectory)),
        "trajectory_files_exist_and_match_sha256": bool(raw_ok),
        "sampled_input_files_exist_and_match_sha256": bool(sampled_ok),
        "core_run_events": len(core_events),
        "core_run_events_ok": sum(x.get("status") == "ok" for x in core_events),
        "matched_run_events": len(matched_events),
        "matched_run_events_ok": sum(x.get("status") == "ok" for x in matched_events),
        "paired_estimator_rows": int(len(comparison)),
        "paired_rows_exact_equal": int(comparison["absolute_difference"].eq(0).sum()),
        "execution_summary_agrees_with_run_ledger": (
            len(core_events) == execution["core_runs_completed"]
            and len(matched_events) == execution["matched_runs_completed"]
            and sum(x.get("status") == "ok" for x in core_events) == execution["core_runs_ok"]
            and sum(x.get("status") == "ok" for x in matched_events) == execution["matched_runs_ok"]
        ),
        "source_v59_sha256": execution["source_v59_sha256"],
        "derived_runtime_sha256": execution["derived_runtime_sha256"],
    }
    (HERE / "TRACE_AUDIT.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8")
    with journal.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": "trace_audit_and_manifest_finalized",
            "checks": checks,
            "analysis_tooling_note": "An exploratory query first treated DataFrame.max() as scalar, and a follow-up used pandas .T (transpose) instead of the T column; both were corrected with explicit numeric arrays and ['T'] selection. They changed no source or experiment data.",
            "decision": "Preserve all scripts, protocol, reports, inputs, outputs, per-run logs, source hashes, and run journal. No data or source edits during finalization.",
        }, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())

    # Rebuild output-only manifest after the last analysis/report changes.
    out_files = []
    for path in sorted(x for x in OUT.rglob("*") if x.is_file() and x.name != "output_manifest.csv"):
        out_files.append({"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})
    pd.DataFrame(out_files).to_csv(OUT / "output_manifest.csv", index=False)

    # The study manifest covers internal artifacts plus all external source/reference inputs.
    entries = []
    for path in sorted(x for x in HERE.rglob("*") if x.is_file() and x.name != "STUDY_MANIFEST.csv"):
        entries.append({"scope": "study", "path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})
    external = [
        PROJECT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py",
        PROJECT / "UNIVERSAL_LOG_v5.8.py",
        PROJECT / "ising_classique_test" / "multiflux_mcmc_pipeline_test.py",
        PROJECT / "ising_classique_test" / "finite_size" / "finite_size_results.csv",
        PREVIOUS_OUT / "pipeline_axis_flux_matrix.csv",
        PREVIOUS_OUT / "pipeline_estimator_outputs.csv",
    ]
    old_matrix = pd.read_csv(PREVIOUS_OUT / "pipeline_axis_flux_matrix.csv")
    for row in old_matrix.itertuples():
        external.append(PREVIOUS_OUT / "pipeline_inputs" / f"L{int(row.L)}_T{float(row.T):.6f}_chain{int(row.Chain)}.csv")
    seen = set()
    for path in external:
        path = Path(path).resolve()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        entries.append({"scope": "external_input", "path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})
    manifest_path = HERE / "STUDY_MANIFEST.csv"
    pd.DataFrame(entries).to_csv(manifest_path, index=False)
    print(json.dumps({
        "trace_audit": checks,
        "study_manifest": str(manifest_path),
        "study_manifest_entries": len(entries),
        "study_manifest_sha256": digest(manifest_path),
        "output_manifest_entries": len(out_files),
        "output_manifest_sha256": digest(OUT / "output_manifest.csv"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
