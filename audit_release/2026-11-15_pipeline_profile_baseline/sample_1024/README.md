# Deterministic 1,024-row profile

This sample is derived from the full 8,000-row Ising Monte Carlo input by copying its header and first 1,024 rows in original order. It is not a separate empirical dataset or a random sample.

The runner performs three ordinary end-to-end timings and one cProfile run using the same source, seed, target, control, mode, and flux-selection defaults. The cProfile wall time is not compared to the ordinary runs.

The 8,000-row attempt is preserved in the sibling folder baseline_run_01; it was interrupted after 373.048 seconds with exit code -1 before output artifacts appeared. Treat that as a bounded incomplete run, not a successful runtime benchmark.

Reproduce:
powershell -ExecutionPolicy Bypass -File .\audit_release\2026-11-15_pipeline_profile_baseline\sample_1024\run_profile_sample.ps1
