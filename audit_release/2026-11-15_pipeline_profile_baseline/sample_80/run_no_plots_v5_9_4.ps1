$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$pipeline = Join-Path $root 'UNIVERSAL_LOG_v5.9.4.py'
$dataPath = Join-Path $root 'audit_release\2026-11-14_l7b_full_reduced\data\L16_T2.269185_chain0_first80.csv'
$runDir = Join-Path $PSScriptRoot 'no_plots_v5_9_4'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$outputDir = Join-Path $runDir 'pipeline_output'
$logPath = Join-Path $runDir 'console.log'
$rows = [int]((Get-Content -LiteralPath $dataPath | Measure-Object -Line).Lines - 1)
$columns = (Get-Content -LiteralPath $dataPath -TotalCount 1).Split(',')
$pythonVersion = (& $python --version 2>&1 | Out-String).Trim()
$sourceHash = (Get-FileHash -LiteralPath $pipeline -Algorithm SHA256).Hash.ToLowerInvariant()
$dataHash = (Get-FileHash -LiteralPath $dataPath -Algorithm SHA256).Hash.ToLowerInvariant()
$gitHead = (& git -C $root rev-parse HEAD).Trim()
$arguments = @(
    $pipeline,
    '--input', $dataPath,
    '--target', 'Abs_magnetization',
    '--control', 'MC_Update',
    '--control-mode', 'single',
    '--mode', 'fast',
    '--max-workers', '1',
    '--no-l7b',
    '--no-plots',
    '--seed', '20261108',
    '--output', $outputDir
)
$originalHashSeed = $env:PYTHONHASHSEED
$env:PYTHONHASHSEED = '0'
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$started = (Get-Date).ToUniversalTime().ToString('o')
Push-Location $root
try {
    & $python @arguments *> $logPath
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
    $timer.Stop()
    if ($null -eq $originalHashSeed) { Remove-Item Env:PYTHONHASHSEED -ErrorAction SilentlyContinue }
    else { $env:PYTHONHASHSEED = $originalHashSeed }
}
$record = [ordered]@{
    label = 'no_plots_v5_9_4'
    profiled = $false
    started_utc = $started
    elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 6)
    exit_code = $exitCode
    source = $pipeline
    source_sha256 = $sourceHash
    input = $dataPath
    input_sha256 = $dataHash
    rows = $rows
    columns = $columns
    python = $python
    python_version = $pythonVersion
    pythonhashseed = '0'
    git_commit = $gitHead
    command_arguments = $arguments
    output_directory = $outputDir
    console_log = $logPath
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runDir 'run_record.json') -Encoding utf8
if ($exitCode -ne 0) { throw "Run failed with exit code $exitCode; see $logPath" }
Write-Output ($record | ConvertTo-Json -Depth 8)
