$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$reference = Join-Path $PSScriptRoot 'baseline_run_01\pipeline_output'
$candidate = Join-Path $PSScriptRoot 'no_plots_v5_9_4\pipeline_output'
$names = @(
    'df_feat.csv', 'scores.json', 'transition_analysis.json',
    'estimator_redundancy.csv', 'estimator_redundancy.json',
    'estimator_four_tests.csv', 'estimator_measurement_types.csv',
    'estimator_measurement_types.json', 'csd_consensus.csv', 'csd_consensus.json',
    'csd_fractal_estimators.csv', 'csd_fractal_estimators.json',
    'noise_diagnostic.json', 'scan_curve.json', 'csd_correlation.json', 'fluxes_raw.csv'
)
Write-Output ('comparison_utc=' + (Get-Date).ToUniversalTime().ToString('o'))
Write-Output 'reference=baseline_run_01/pipeline_output'
Write-Output 'candidate=no_plots_v5_9_4/pipeline_output'
Write-Output 'Selected output SHA-256 comparisons:'
foreach ($name in $names) {
    $left = (Get-FileHash -LiteralPath (Join-Path $reference $name) -Algorithm SHA256).Hash.ToLowerInvariant()
    $right = (Get-FileHash -LiteralPath (Join-Path $candidate $name) -Algorithm SHA256).Hash.ToLowerInvariant()
    '{0} identical={1} sha256={2}' -f $name, ($left -eq $right), $right
}
Write-Output 'Recursive master_results.json and TLog comparison (paired NaNs treated as equal):'
& $python (Join-Path $PSScriptRoot '..\compare_output_modes.py') `
    (Join-Path $reference 'master_results.json') (Join-Path $candidate 'master_results.json')
if ($LASTEXITCODE -ne 0) { throw 'Recursive JSON comparison failed.' }
$referencePng = @(Get-ChildItem -LiteralPath $reference -Filter '*.png' -File).Count
$candidatePng = @(Get-ChildItem -LiteralPath $candidate -Filter '*.png' -File).Count
Write-Output "PNG count reference=$referencePng no_plots=$candidatePng"
