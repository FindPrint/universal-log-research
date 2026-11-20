# UNIVERSAL_LOG audit package V3 — reproduction guide

V3 extends the V2 archive with a dated correction for L7b-full seed traceability. The earlier V2 PDF/ZIP are preserved as historical artifacts. V3 includes them unchanged and adds the correction source, its focused tests, logs, report, and hashes.

## Rebuild the code candidate and run the focused checks

Use the project virtual environment from the project root:

```powershell
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\build_v5_9_2_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\test_l7b_seedtrace.py
```

Expected test summary: **5 tests, all passing**. One orchestration check uses a mocked pipeline engine and a generated 60-row CSV. It verifies seed propagation, not L7b estimator behavior or a physical Ising result.

## Rebuild the V3 whitepaper and archive

The PDF builder uses `pypdf`, `reportlab`, and Windows Arial fonts; it appends the dated two-page audit addendum to the V2 whitepaper, embeds the new trace files, and writes a new attachment index. Render the two appended pages with Poppler and inspect them before distribution.

```powershell
python .\audit_release\build_v3_whitepaper_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\finalize_v3_package.py
```

The package finalizer copies V2 and appends only V3 payloads and manifests. It validates ZIP CRC, duplicate paths, file hashes, and exclusion of `.venv`. It refuses to overwrite existing V3 outputs.

## Evidence boundary

The code patch changes seed metadata transport and the displayed version label. The estimator calculations, L7b thresholds, and verdict formulas are unchanged in the generated diff. The full L7b integration was not rerun after this change; see `AUDIT_SUPPLEMENT_2026-11-15.md` for the observation, hypothesis, exact test scope, and limitations.
