$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$pipeline = Join-Path $root 'UNIVERSAL_LOG_v5.9.2.py'
$dataPath = Join-Path $root 'ising_classique_test\finite_size\multiflux_mcmc_v59_study\expanded_runs\raw_trajectories\L16_T2.260000000_chain0.csv'
if (!(Test-Path -LiteralPath $python)) { throw "Python venv missing: $python" }
if (!(Test-Path -LiteralPath $pipeline)) { throw "Pipeline missing: $pipeline" }
if (!(Test-Path -LiteralPath $dataPath)) { throw "Input CSV missing: $dataPath" }

$rows = [int]((Get-Content -LiteralPath $dataPath | Measure-Object -Line).Lines - 1)
$columns = (Get-Content -LiteralPath $dataPath -TotalCount 1).Split(',')
$pythonVersion = (& $python --version 2>&1 | Out-String).Trim()
$sourceHash = (Get-FileHash -LiteralPath $pipeline -Algorithm SHA256).Hash.ToLowerInvariant()
$dataHash = (Get-FileHash -LiteralPath $dataPath -Algorithm SHA256).Hash.ToLowerInvariant()
$gitHead = (& git -C $root rev-parse HEAD).Trim()
$originalHashSeed = $env:PYTHONHASHSEED
$env:PYTHONHASHSEED = '0'
$runRecords = @()
$pipelineArgs = @(
    $pipeline,
    '--input', $dataPath,
    '--target', 'Abs_magnetization',
    '--control', 'MC_Update',
    '--control-mode', 'single',
    '--mode', 'fast',
    '--max-workers', '1',
    '--no-l7b',
    '--seed', '20261108'
)

function Invoke-ProfileRun([string]$Label, [bool]$Profiled) {
    $runDir = Join-Path $PSScriptRoot $Label
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    $outputDir = Join-Path $runDir 'pipeline_output'
    $logPath = Join-Path $runDir 'console.log'
    $arguments = $script:pipelineArgs + @('--output', $outputDir)
    $profilePath = Join-Path $runDir 'pipeline.pstats'
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $started = (Get-Date).ToUniversalTime().ToString('o')
    Push-Location $root
    try {
        if ($Profiled) {
            & $python -m cProfile -o $profilePath @arguments *> $logPath
        } else {
            & $python @arguments *> $logPath
        }
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
        $timer.Stop()
    }
    $record = [ordered]@{
        label = $Label
        profiled = $Profiled
        started_utc = $started
        elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 6)
        exit_code = $exitCode
        input_sha256 = $dataHash
        source_sha256 = $sourceHash
        output_directory = $outputDir
        console_log = $logPath
        profile_file = $(if ($Profiled) { $profilePath } else { $null })
    }
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDir 'run_record.json') -Encoding utf8
    if ($exitCode -ne 0) { throw "Run $Label failed with exit code $exitCode; see $logPath" }
    return [pscustomobject]$record
}

$manifest = [ordered]@{
    created_utc = (Get-Date).ToUniversalTime().ToString('o')
    purpose = 'End-to-end performance baseline and cProfile hotspot audit; software runtime only.'
    git_commit = $gitHead
    python = $python
    python_version = $pythonVersion
    pythonhashseed = '0'
    source = $pipeline
    source_sha256 = $sourceHash
    input = $dataPath
    input_sha256 = $dataHash
    rows = $rows
    columns = $columns
    target = 'Abs_magnetization'
    control = 'MC_Update'
    control_mode = 'single'
    mode = 'fast'
    max_workers = 1
    l7b = 'off'
    seed = 20261108
    flux_selection = 'Pipeline default: remaining numeric columns from input; selection reported in pipeline artifacts.'
    interpretation_limit = 'Input is a simulated classical Ising Monte Carlo trajectory, not an external experimental dataset. This run does not establish cross-domain validity.'
    runs = @()
}
try {
    foreach ($i in 1..3) {
        $label = 'baseline_run_{0:d2}' -f $i
        $record = Invoke-ProfileRun -Label $label -Profiled $false
        $runRecords += $record
        $manifest.runs = $runRecords
        $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'PROFILE_MANIFEST.json') -Encoding utf8
    }
    $record = Invoke-ProfileRun -Label 'cprofile_run' -Profiled $true
    $runRecords += $record
    $manifest.runs = $runRecords
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'PROFILE_MANIFEST.json') -Encoding utf8
    $reportPath = Join-Path $PSScriptRoot 'cprofile_top_cumulative.txt'
    $profileFile = Join-Path (Join-Path $PSScriptRoot 'cprofile_run') 'pipeline.pstats'
    $reportCode = "import pstats,sys; pstats.Stats(sys.argv[1]).strip_dirs().sort_stats('cumtime').print_stats(100)"
    & $python -c $reportCode $profileFile *> $reportPath
    if ($LASTEXITCODE -ne 0) { throw "Could not render cProfile report: $reportPath" }
} finally {
    if ($null -eq $originalHashSeed) { Remove-Item Env:PYTHONHASHSEED -ErrorAction SilentlyContinue }
    else { $env:PYTHONHASHSEED = $originalHashSeed }
}
