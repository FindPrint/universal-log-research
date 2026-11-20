$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$pipeline = Join-Path $root 'UNIVERSAL_LOG_v5.9.2.py'
$dataPath = Join-Path $root 'audit_release\2026-11-14_l7b_full_reduced\data\L16_T2.269185_chain0_first80.csv'
$runDir = Join-Path $PSScriptRoot 'horizons_1_3_6_12'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$outputDir = Join-Path $runDir 'pipeline_output'
$logPath = Join-Path $runDir 'console.log'
$sourceHash = (Get-FileHash -LiteralPath $pipeline -Algorithm SHA256).Hash.ToLowerInvariant()
$dataHash = (Get-FileHash -LiteralPath $dataPath -Algorithm SHA256).Hash.ToLowerInvariant()
$originalHashSeed = $env:PYTHONHASHSEED
$env:PYTHONHASHSEED = '0'
$cliArgs = @(
    $pipeline,
    '--input', $dataPath,
    '--target', 'Abs_magnetization',
    '--control', 'MC_Update',
    '--control-mode', 'single',
    '--mode', 'fast',
    '--horizons', '1,3,6,12',
    '--max-workers', '1',
    '--no-l7b',
    '--seed', '20261108',
    '--output', $outputDir
)
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$started = (Get-Date).ToUniversalTime().ToString('o')
Push-Location $root
try {
    & $python @cliArgs *> $logPath
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
    $timer.Stop()
    if ($null -eq $originalHashSeed) { Remove-Item Env:PYTHONHASHSEED -ErrorAction SilentlyContinue }
    else { $env:PYTHONHASHSEED = $originalHashSeed }
}
$record = [ordered]@{
    label = 'v5.9.2_fast_four_horizons'
    profiled = $false
    started_utc = $started
    elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 6)
    exit_code = $exitCode
    source_sha256 = $sourceHash
    input_sha256 = $dataHash
    rows = 80
    target = 'Abs_magnetization'
    control = 'MC_Update'
    control_mode = 'single'
    mode = 'fast'
    horizons = '1,3,6,12'
    max_workers = 1
    l7b = 'off'
    seed = 20261108
    pythonhashseed = '0'
    output_directory = $outputDir
    console_log = $logPath
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDir 'run_record.json') -Encoding utf8
if ($exitCode -ne 0) { throw "Four-horizon run failed with exit code $exitCode; see $logPath" }
