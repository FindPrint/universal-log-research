$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$pipeline = Join-Path $root 'UNIVERSAL_LOG_v5.9.2.py'
$dataPath = Join-Path $root 'audit_release\2026-11-14_l7b_full_reduced\data\L16_T2.269185_chain0_first80.csv'
$sourceHash = (Get-FileHash -LiteralPath $pipeline -Algorithm SHA256).Hash.ToLowerInvariant()
$dataHash = (Get-FileHash -LiteralPath $dataPath -Algorithm SHA256).Hash.ToLowerInvariant()
$runDir = Join-Path $PSScriptRoot 'cprofile_run'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$outputDir = Join-Path $runDir 'pipeline_output'
$logPath = Join-Path $runDir 'console.log'
$profilePath = Join-Path $runDir 'pipeline.pstats'
$originalHashSeed = $env:PYTHONHASHSEED
$env:PYTHONHASHSEED = '0'
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$started = (Get-Date).ToUniversalTime().ToString('o')
$cliArgs = @(
    $pipeline,
    '--input', $dataPath,
    '--target', 'Abs_magnetization',
    '--control', 'MC_Update',
    '--control-mode', 'single',
    '--mode', 'fast',
    '--max-workers', '1',
    '--no-l7b',
    '--seed', '20261108',
    '--output', $outputDir
)
Push-Location $root
try {
    & $python -m cProfile -o $profilePath @cliArgs *> $logPath
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
    $timer.Stop()
    if ($null -eq $originalHashSeed) { Remove-Item Env:PYTHONHASHSEED -ErrorAction SilentlyContinue }
    else { $env:PYTHONHASHSEED = $originalHashSeed }
}
$record = [ordered]@{
    label = 'cprofile_run'
    profiled = $true
    started_utc = $started
    elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 6)
    exit_code = $exitCode
    source_sha256 = $sourceHash
    input_sha256 = $dataHash
    profile_file = $profilePath
    output_directory = $outputDir
    console_log = $logPath
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDir 'run_record.json') -Encoding utf8
if ($exitCode -ne 0) { throw "cProfile run failed; see $logPath" }
$reportPath = Join-Path $PSScriptRoot 'cprofile_top_cumulative.txt'
$reportCode = "import pstats,sys; pstats.Stats(sys.argv[1]).strip_dirs().sort_stats('cumtime').print_stats(100)"
& $python -c $reportCode $profilePath *> $reportPath
if ($LASTEXITCODE -ne 0) { throw "Could not render cProfile report: $reportPath" }
