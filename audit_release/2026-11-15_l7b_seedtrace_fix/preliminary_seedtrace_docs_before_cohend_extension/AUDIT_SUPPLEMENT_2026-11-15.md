# Audit supplement — 2026-11-15: L7b seed traceability

## Purpose and status

This supplement records a narrow reporting correction found during review of the V2 audit package. The V2 whitepaper and archive remain the historical record of the v5.9.1 runs. This supplement adds a separately versioned v5.9.2 audit candidate and a focused regression check; it does not rewrite the archived results.

## Observation

The archived L7b-full result reports `graine_alternative: null`, although the v5.9.1 runner selects seed `123` when the reference seed is not `123`. In the v5.9.1 code, `_run_l7b_full_checks._one` knows the seed used for each rerun, but calls `_l7b_extract_summary(res)` without passing it. The summary therefore loses the run seed before the seed-stability check formats its output.

## Hypothesis, change, and scope

**Hypothesis:** the null value is a metadata propagation defect between the rerun helper and the L7b summary extractor. The numerical rerun and the seed-stability comparison can still complete.

**Change:** the v5.9.2 audit candidate lets `_l7b_extract_summary` accept the caller-known seed and adds it to the summary; `_one` passes the seed actually supplied to the rerun. The artifact version label changes to `v5.9.2-L7aL7b-DKind-AuditFix-SeedTrace`.

The generated unified diff contains no edits to estimator code, thresholds, score calculations, verdict rules, or physical interpretation. This patch is intended to repair traceability only.

## Verification performed

The focused tests used the project `.venv` Python 3.11.9. All five checks passed:

1. A known seed (`123`) is preserved by the summary extractor.
2. Seed zero is preserved rather than treated as missing.
3. Omitting the optional seed keeps the summary compatible with reference summaries.
4. The L7b seed check exports `123` in its `graine_alternative` field.
5. The actual `_run_l7b_full_checks` orchestration helper passes alternate seed `123` and reference seed `77` to a mocked pipeline; its summary records `123`. The mocked calls saw seeds `[123, 77, 77, 77]` for the seed, window, shuffle, and log reruns.

The helper-level test generated a 60-row synthetic CSV with positive target values. The pipeline engine was mocked to return a fixed valid-shaped result, so this verifies data flow and export wiring, not estimator calculations or physical behavior. The full 28-minute L7b integration was not rerun after this metadata-only correction.

## Reproduction

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\build_v5_9_2_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\test_l7b_seedtrace.py
```

The builder fails closed if any expected source code fragment differs from the archived v5.9.1 audit copy. It writes the patched pipeline, a unified diff, and a build record with source/output SHA-256 values. The test writes no project data; its temporary synthetic input is removed by the test harness.

## Trace files and hashes

The dated trace folder is `audit_release/2026-11-15_l7b_seedtrace_fix/`. It includes the exact patched source, deterministic patch builder, test code, final execution log, build record, and diff. The build record identifies the exact v5.9.1 input and output digests. Failed preflight attempts are retained as clearly named logs and are not counted as successful tests.

## Interpretation

**Observed software result:** the focused checks pass and the seed is propagated through the mocked L7b-full orchestration path. This supports the specific traceability fix.

**Not established:** that Ising's transition was identified, that L7b's verdicts are physically valid, or that the pipeline is universal. No new physics result is claimed by this correction.
