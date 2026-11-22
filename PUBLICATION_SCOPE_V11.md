# Scope of the public source repository — V11

V11 adds a frozen, reproducible synthetic sensitivity campaign covering null, weak, and strong generated signals; series lengths of 64 and 100; selected replicate seeds; and rotation of every numeric measurement stream as control. The dated publication manifest records the exact source and compact result files, byte counts, and SHA-256 values.

The test uses generated data only. It does not contain patient data, clinical measurements, a therapy comparison, a biomarker claim, or a treatment recommendation. The archived v6.0.1 pipeline source is called without modification.

The full whitepaper and full-project snapshot ZIP remain separate local/archive artifacts and are excluded from the public source commit. The PDF does not contain the ZIP. Detailed per-run JSON, figures, CSV outputs, and console traces are preserved in the snapshot.

## Research limits

The V2 campaign completed 35/35 calls and passed eight frozen software-integrity assertions. T0 was emitted in 15/15 null calls; this is not a false-alarm rate because no alarm/abstention rule was specified. On four non-null temporal-axis calls, absolute error from the injected 58% center ranged from 3.99 to 38.15 percentage points (median 28.00), with sparse and uneven replication. These observations show configuration sensitivity in the tested synthetic cases, not validated threshold accuracy.

The public run manifest uses repository-relative paths. The local execution manifest with workstation-specific absolute paths remains in the private working archive and V11 snapshot, and is excluded from the GitHub publication.

Four calls exceeded 300 seconds; the maximum was 729.6 seconds. These are end-to-end runtimes only, with no per-estimator profiling or established cause. The runtime table is descriptive.

The campaign supports only the tested synthetic configuration and software-integrity assertions. It does not establish a false-alarm rate, general universality, clinical utility, or PDAC biology.

## Licensing

Project code is MIT licensed. Project-authored documentation and results are CC BY 4.0. Third-party sources retain their own terms.
