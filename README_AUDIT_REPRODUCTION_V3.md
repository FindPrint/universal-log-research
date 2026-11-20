# UNIVERSAL_LOG audit package V3 — reproduction guide

V3 extends the historical V2 package with Cohen-d-only variants and a targeted L7b seed-trace correction. V2 sources and results are retained unchanged. The new variants are derived copies; their metric change can alter scan thresholds, scores, and downstream classifications.

The latest `UNIVERSAL_LOG_v5.9.2.py` still contains the TLog layer and formula `T_log(d) = (d - 4) * ln(n)` (`n` is the number of CSV rows). The formula consumes only eligible dimension-proxy estimates; Cohen d replaces Cliff's delta in the separate scan and cross-class separation paths.

## Build the current candidate and historical variants

Run from PowerShell at the project root:

```powershell
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\build_v5_9_2_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\build_cohend_only_variants.py
```

This produces `UNIVERSAL_LOG_v5.9.2.py` as the current candidate, plus derived copies of v5.3, v5.8, and v5.9.0. The original source files are not changed. Build records contain source, output, and diff SHA-256 values.

## Reproduce benchmark and checks

```powershell
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\benchmark_cliff_vs_cohen.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\test_l7b_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\test_cohend_only_variants.py
```

The benchmark compares the candidate's fast Cohen scan, using a degrees-of-freedom weighted pooled SD, to the archived v5.9.1 Cliff legacy scan using identical 80-row and 200-row Ising inputs and matched scan settings. It reports scan-call timings and selected thresholds. Its results do not establish a full-pipeline speedup or physical correctness. The orchestration test uses a mocked pipeline engine.

The package also contains a full fast-mode smoke run on an archived 80-row Ising CSV. It completed with L7b disabled and exported TLog values for 21 eligible estimators, 13 typed groups, and 4 class medians. Its internal T0 is not a physical Tc measurement.

Example invocation of the delivered candidate:

```powershell
.\.venv\Scripts\python.exe .\UNIVERSAL_LOG_v5.9.2.py `
  --input .\audit_release\2026-11-14_l7b_full_reduced\data\L16_T2.269185_chain0_first80.csv `
  --target Abs_magnetization --control MC_Update --mode fast --no-l7b `
  --seed 20261108 --output .\my_v592_run
```

`--no-l7b` skips the robustness reruns for this quick example; the pipeline still computes and reports its internal TLog and L7a outputs.

## Rebuild the V3 whitepaper and archive

The PDF builder needs Python packages `pypdf` and `reportlab`; rendering the two appended pages needs Poppler (`pdftoppm`). These are document-build dependencies, not pipeline dependencies.

```powershell
python .\audit_release\build_v3_whitepaper_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\finalize_v3_package.py
```

The builder appends a dated two-page addendum to V2, embeds the new source versions and trace files, and adds a V3 attachment index. Render the two new pages and inspect them before distribution. The package finalizer appends V3 to V2 and validates ZIP CRC, duplicate paths, payload hashes, and `.venv` exclusion; it refuses to overwrite an existing V3 archive.

## Interpretation boundary

Cohen's d and Cliff's delta measure different quantities. On the 80-row archived input the selected threshold changed from 40.00 to 36.67; on the 200-row input these selected thresholds coincided. The Cohen-only variants also correct the archived `cohen_d` denominator from an equal-weight variance average to the conventional degrees-of-freedom weighted pooled SD; this changes outputs when group sizes differ. See `AUDIT_SUPPLEMENT_2026-11-15.md` for detailed results, exact settings, references, and limitations. This is not evidence that the pipeline identifies physical Tc or is universal.
