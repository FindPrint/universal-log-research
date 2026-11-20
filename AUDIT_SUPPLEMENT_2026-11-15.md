# Audit supplement — 2026-11-15

## Cohen-d-only variants and L7b seed traceability

This supplement extends the historical V2 audit package. The V2 PDF and ZIP remain unchanged. V3 adds a separate set of versioned pipeline copies, benchmark evidence, focused tests, and a correction for the L7b-full seed field.

## 1. Metric choice: hypothesis and decision

**User hypothesis:** Cohen's d may be faster, yield the same pipeline results, and provide a more informative scale than Cliff's delta.

**Conceptual check:** Cohen's d is a signed standardized mean difference and is mathematically unbounded. Cliff's delta is also signed, but bounded from -1 to +1; it measures the difference between the probabilities that a random observation in one group exceeds one in the other. The measures answer different questions. A larger numerical range does not itself mean more information, and equal values or equal selected thresholds are not guaranteed.

The current pipeline already has a fast Cohen-d scan. In v5.9.1, the `robust`, `full`, and `predict` presets instead choose Cliff's delta and route through a legacy scan. This audit tested the user-requested Cohen-only behavior in derived copies. It does not rewrite the historical source files.

**Formula correction:** the archived helper named `cohen_d` divided by `sqrt((s1²+s2²)/2)`, an equal-weight variance average. The Cohen-d-only variants use the conventional pooled SD, weighting each group variance by its degrees of freedom. Since scan groups can have different sizes, this changes effect values relative to the archived helper even in modes that already used its `cohen_d` label. The new variants therefore include both a metric selection change and a formula correction; their results are not interchangeable with historical output without this context.

## 2. Matched scan benchmark

The benchmark used the project `.venv` Python, the Cohen-d-only v5.9.2 candidate for the Cohen scan and archived v5.9.1 for the Cliff scan, `MC_Update` as control, the same three flux columns (`Abs_magnetization`, `Energy_per_spin`, `M_squared`), 31 threshold candidates, the same window and minimum-group settings within each pair, one warm-up, and five timed scan calls per metric. Inputs were the archived 80-row slice and its 200-row source CSV. Cohen used the fast scanner and degrees-of-freedom weighted pooled SD; Cliff used the archived legacy scanner.

| Input | Mode preset | Cohen threshold | Cliff threshold | Median scan time: Cohen | Median scan time: Cliff | Cliff/Cohen time ratio |
|---|---:|---:|---:|---:|---:|---:|
| 80 rows | robust | 36.67 | 40.00 | 0.0034 s | 0.0671 s | 19.56× |
| 80 rows | full | 36.67 | 40.00 | 0.0032 s | 0.0639 s | 19.90× |
| 80 rows | predict | 36.67 | 40.00 | 0.0034 s | 0.0712 s | 20.76× |
| 200 rows | robust | 63.33 | 63.33 | 0.0037 s | 0.1216 s | 32.67× |
| 200 rows | full | 63.33 | 63.33 | 0.0035 s | 0.1936 s | 55.20× |
| 200 rows | predict | 63.33 | 63.33 | 0.0080 s | 0.1218 s | 15.25× |

The 80-row thresholds differ by one 31-point scan interval; the 200-row thresholds coincide for these runs. Score-curve rank correlations were high (0.950–0.996), but the curves and thresholds were not generally identical. Thus this benchmark supports faster scan execution on these cases; it rejects a universal “same results” claim. The measured ratios (15.25×–55.20×) are scan-call timings, not whole-pipeline speedups, and varied with system load.

## 3. Code variants produced

The build script creates copies and leaves source versions untouched:

- `UNIVERSAL_LOG_v5.3_COHEND_ONLY.py`
- `UNIVERSAL_LOG_v5.8_COHEND_ONLY.py`
- `UNIVERSAL_LOG_v5.9.0_COHEND_ONLY.py`
- `UNIVERSAL_LOG_v5.9.2.py` — current audit candidate, combining the v5.9.1 audit fixes, L7b seed trace correction, and Cohen-d-only active paths.

All four variants set every shipped mode preset to Cohen's d, route threshold scans through the fast Cohen path, compute the cross-class effect-size diagnostic with Cohen's d, and rename its output field to `cohen_d_between_classes`. Custom Cliff requests are rejected. The old `cliff_delta` helper remains only for imported-code compatibility and has zero active call sites in these variants. The derived historical copies do not inherit future fixes and have not received full end-to-end scientific revalidation.

The metric change can affect selected thresholds, scores, and downstream classifications. In particular, the 80-row benchmark demonstrates a threshold change. Consumers expecting the old `cliff_between_classes` result key must switch to `cohen_d_between_classes`.

The candidate continues to include the TLog layer and its final formula (T_{\log}(d)=(d-4)\ln(n)), with `n` defined by the pipeline as the number of CSV rows. TLog eligibility remains limited to dimension-proxy estimators; z-scores are not fed into the formula. The final 80-row fast-mode smoke run exported 21 eligible estimator TLog values, 13 `d_kind` summaries, and 4 class medians. Cohen-d-only changes the scan and relative separation diagnostics, not the TLog formula; upstream estimator values can still change when the selected scan configuration changes.

## 4. L7b seed traceability correction

The archived L7b-full result contains `graine_alternative: null`, although the v5.9.1 runner chooses seed 123 when the reference seed is not 123. The helper knows the seed, but `_l7b_extract_summary` dropped it before result formatting.

The v5.9.2 candidate passes the known seed into the summary extractor and exports it. This patch changes metadata transport and the displayed version label; it does not change estimator calculations, thresholds, or L7b decision formulas.

## 5. Tests and evidence boundary

Five seed-trace checks and seven Cohen-only variant checks passed. The Cohen-only checks import all four copies, confirm all presets use Cohen's d, verify that Cliff calls are absent from active code, test rejection of custom Cliff requests, verify the weighted pooled-SD formula, confirm the seed-trace fix remains in the latest candidate, and reproduce the Cohen scan thresholds in the benchmark.

The orchestration-level seed test uses a 60-row synthetic CSV and a mocked pipeline engine. It verifies the seeds `[123, 77, 77, 77]` reach the summary path; it does not run the estimators. The metric benchmark is a software comparison on one Ising control axis and selected archived data. No full L7b rerun was performed after the metadata patch, and no result here validates (T_c), transition identification, or universality.

An additional full `fast` CLI smoke run completed successfully on an archived 80-row CSV with `MC_Update` control, `Abs_magnetization` target, seed 20261108, and L7b disabled. It reported internal T0=89.29%, L7a `UP` with 50% confidence, and dominant regime `criticality`; these are pipeline outputs, not a Tc estimate. It used 13 scan candidates, window 35, and minimum group 4. TLog used n=80 and exported 21 estimator values; the four historical class medians were saturation -11.011224, criticality -6.045236, divergence -2.905474, and null_reference -6.538934. These are pipeline diagnostics, not physical Ising dimensions. The console recorded a near-constant moment precision warning, two zero/insufficient-spectrum diagnostics, a Matplotlib deprecation warning, and an IEEE 754 mantissa-truncation notice; they remain visible in the attached evidence.

## 6. Reproduction

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\build_v5_9_2_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\build_cohend_only_variants.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\benchmark_cliff_vs_cohen.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\test_l7b_seedtrace.py
.\.venv\Scripts\python.exe .\audit_release\2026-11-15_l7b_seedtrace_fix\test_cohend_only_variants.py
```

The builders fail closed if their expected source fragments are missing or ambiguous. The benchmark JSON records exact input/source hashes, scan settings, thresholds, score curves, and timings. The dated trace directory retains the build records, diffs, logs, tests, preliminary attempts, and exact candidate source.

## 7. Method references

- Norman Cliff (1993), “Dominance statistics: Ordinal analyses to answer ordinal questions,” *Psychological Bulletin* 114(3), 494–509. [DOI](https://doi.org/10.1037/0033-2909.114.3.494).
- Philomena Marfo and G. A. Okyere (2019), “The accuracy of effect-size estimates under normals and contaminated normals in meta-analysis,” *Heliyon* 5(6):e01838. [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6562325/).
