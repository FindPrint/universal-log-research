<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# UNIVERSAL_LOG audit package - supplement 2026-11-14

This update adds an exact matched replay of 20 archived Ising control/flux configurations on v5.9.1, plus real L7b-light and L7b-full integration output. The original white paper and archive remain preserved as V1. The V2 white paper appends this supplement and embeds the complete new trace set.

## Main findings

- All 20 replay configurations completed. The 580 v5.9.0/v5.9.1 estimator medians matched exactly, and all 20 D-vectors and dominant-regime labels matched.
- v5.9.1 populated `d_kind`, `quantity_type`, and TLog membership for 580/580 estimator rows. It emitted 260 TLog-by-kind rows over 13 registered kinds.
- L7b-light completed for `MC_Update` and `Noise_axis`, with shared fixed target `Abs_magnetization`. Both heuristic verdicts were `FRAGILE`, for different checks.
- L7b-full completed on a predeclared 80-row slice and returned `FRAGILE`: seed PASS, window FAIL, shuffled-target FAIL, log scale INVARIANT.
- The default outer full mode did not return within 15 minutes. The tested L7b integrations used outer mode `fast`; the separate L7b-full check still ran all four internal perturbation pipelines.

These are software replay and integration results. They do not establish that the pipeline localizes the Ising transition or that its method is universal.

## Reproduce the matched replay

From the extracted project root, with the locked `.venv`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r audit_release\requirements-lock.txt
.\.venv\Scripts\python.exe audit_release\run_matched_v59_v591_replay.py --output-dir audit_release\matched_replay_rerun
```

The run requires the archived v5.8 input matrix and the original 200-row CSV inputs. It holds the seed (20261108), 40-row window, 24-point landscape, axes, and flux lists fixed. It writes hashes, per-run logs, feature landscapes, estimator rows, and TLog-by-kind rows to the new output directory.

## Reproduce L7b-light on multiple control columns

```powershell
.\.venv\Scripts\python.exe audit_release\run_l7b_integration.py --modes light --output-dir audit_release\l7b_light_rerun
```

This uses 200 rows from the archived L16,Tc,chain0 CSV; target `Abs_magnetization`; controls `MC_Update` and `Noise_axis`; fixed target policy; seed 20261108; and outer mode `fast`. The detailed L7b checks are saved in each control's `master_results.json`.

## Reproduce L7b-full

```powershell
.\.venv\Scripts\python.exe audit_release\run_l7b_full_reduced.py --output-dir audit_release\l7b_full_rerun
```

This runs `run_full_unified_pipeline` with `l7b_mode=full` on the first 80 rows of the same archived CSV, control `MC_Update`, target `Abs_magnetization`, seed 20261108, and outer mode `fast`. It runs the alternate seed, 80-percent window, shuffled-target, and log-scale checks. The 80-row input bounds software execution cost; it is not a scientific sample-size recommendation.

## Trace and interpretation

The exact executed runner copies, predeclared protocols, input hashes, output tables, logs, plots, and complete JSON outputs are embedded in the white paper and stored under `audit_release/2026-11-14_*`. `PROJECT_FILE_CATALOG_V2.csv` and `SHA256SUMS_V2.txt` cover the V2 archive entries; each manifest excludes itself and the archive hash sidecar excludes the archive itself.

After generating or reviewing the V2 white paper, create the updated archive and validate its CRC and file hashes with:

```powershell
.\.venv\Scripts\python.exe audit_release\finalize_v2_package.py
```

The finalizer appends the supplement files and V2 white paper to the preserved V1 ZIP, writes the V2 catalog and SHA-256 list, verifies every payload hash, and creates an external `.sha256` sidecar.

The v5.9.1 L7b-full result has a traceability defect: the alternative-seed check passes but exports `graine_alternative: null`, because the summary extractor drops the seed value. The tested source is preserved unchanged; see `audit_release/2026-11-14_l7b_full_reduced/PROTOCOL_ERRATUM.md`.

## Licenses

Code: MIT. This guide, the supplement, results, logs, and figures: CC BY 4.0, subject to the original third-party notices and source material recorded in `LICENSES.md`.
