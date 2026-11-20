$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project virtual environment Python not found: $Python"
}

& $Python '.\audit_release\2026-11-15_l7b_seedtrace_fix\build_v5_9_2_seedtrace.py'
if ($LASTEXITCODE -ne 0) { throw "v5.9.2 seed-trace build failed: $LASTEXITCODE" }

& $Python '.\audit_release\2026-11-15_l7b_seedtrace_fix\build_cohend_only_variants.py'
if ($LASTEXITCODE -ne 0) { throw "Cohen-d-only variants build failed: $LASTEXITCODE" }

& $Python '.\audit_release\2026-11-15_l7b_seedtrace_fix\benchmark_cliff_vs_cohen.py'
if ($LASTEXITCODE -ne 0) { throw "Cliff-vs-Cohen benchmark failed: $LASTEXITCODE" }

& $Python '.\audit_release\2026-11-15_l7b_seedtrace_fix\test_l7b_seedtrace.py'
if ($LASTEXITCODE -ne 0) { throw "seed-trace regression checks failed: $LASTEXITCODE" }

& $Python '.\audit_release\2026-11-15_l7b_seedtrace_fix\test_cohend_only_variants.py'
if ($LASTEXITCODE -ne 0) { throw "Cohen-d-only regression checks failed: $LASTEXITCODE" }

Write-Output 'Reproduction complete: variants built, benchmark recorded, and focused checks passed.'
