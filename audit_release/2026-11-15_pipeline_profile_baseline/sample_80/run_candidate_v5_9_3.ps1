$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$pipeline = Join-Path $root 'UNIVERSAL_LOG_v5.9.3.py'
$dataPath = Join-Path $root 'audit_release\2026-11-14_l7b_full_reduced\data\L16_T2.269185_chain0_first80.csv'
$runDir = Join-Path $PSScriptRoot 'optimized_v5_9_3'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$outputDir = Join-Path $runDir 'pipeline_output'
$logPath = Join-Path $runDir 'console.log'
$sourceHash = (Get-FileHash -LiteralPath $pipeline -Algorithm SHA256).Hash.ToLowerInvariant()
$dataHash = (Get-FileHash -LiteralPath $dataPath -Algorithm SHA256).Hash.ToLowerInvariant()
$gitHead = (& git -C $root rev-parse HEAD).Trim()
$originalHashSeed = $env:PYTHONHASHSEED
$env:PYTHONHASHSEED = '0'
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
    label = 'optimized_v5.9.3_scalar_divide'
    profiled = $false
    started_utc = $started
    elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 6)
    exit_code = $exitCode
    git_base_commit = $gitHead
    source = $pipeline
    source_sha256 = $sourceHash
    input = $dataPath
    input_sha256 = $dataHash
    rows = 80
    target = 'Abs_magnetization'
    control = 'MC_Update'
    control_mode = 'single'
    mode = 'fast'
    max_workers = 1
    l7b = 'off'
    seed = 20261108
    pythonhashseed = '0'
    output_directory = $outputDir
    console_log = $logPath
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDir 'run_record.json') -Encoding utf8
if ($exitCode -ne 0) { throw "Optimized run failed with exit code $exitCode; see $logPath" }
