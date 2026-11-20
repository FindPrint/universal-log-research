$ErrorActionPreference = 'Stop'

$AuditDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $AuditDir)
$PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$AnalysisScript = Join-Path $AuditDir 'reanalyze_raw_expression.py'
$LogPath = Join-Path $AuditDir 'independent_reanalysis.log'
$ManifestPath = Join-Path $AuditDir 'analysis_manifest.json'
$ReportPath = Join-Path $AuditDir 'REVUE_SCIENTIFIQUE_PDACS.md'

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python .venv introuvable: $PythonExe"
}

& $PythonExe $AnalysisScript *> $LogPath
if ($LASTEXITCODE -ne 0) {
    Get-Content -LiteralPath $LogPath -Tail 100
    throw "L'analyse a échoué avec le code $LASTEXITCODE"
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Manifest | Add-Member -NotePropertyName reproducibility -NotePropertyValue ([pscustomobject]@{
    command = '& .\.venv\Scripts\python.exe "pancréas\REVUE_INDEPENDANTE_2026-11-15\reanalyze_raw_expression.py"'
    script_sha256 = (Get-FileHash -LiteralPath $AnalysisScript -Algorithm SHA256).Hash.ToLowerInvariant()
    execution_log = $LogPath
    execution_log_sha256 = (Get-FileHash -LiteralPath $LogPath -Algorithm SHA256).Hash.ToLowerInvariant()
    wrapper_sha256 = (Get-FileHash -LiteralPath $MyInvocation.MyCommand.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    report_sha256 = if (Test-Path -LiteralPath $ReportPath) { (Get-FileHash -LiteralPath $ReportPath -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
}) -Force
$Json = $Manifest | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($ManifestPath, $Json, [System.Text.UTF8Encoding]::new($false))
Get-Content -LiteralPath $LogPath -Tail 30
