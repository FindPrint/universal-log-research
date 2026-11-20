$ErrorActionPreference = 'Stop'

$AuditDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Join-Path $AuditDir 'data_GSE57495'
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $AuditDir)
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$MatrixPath = Join-Path $DataDir 'GSE57495_series_matrix.txt.gz'
$PlatformPath = Join-Path $DataDir 'GPL15048_official_geo.txt'

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python de l'environnement .venv introuvable : $Python"
}
if (-not (Test-Path -LiteralPath $MatrixPath)) {
    Invoke-WebRequest -Uri 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE57nnn/GSE57495/matrix/GSE57495_series_matrix.txt.gz' -OutFile $MatrixPath
}
if (-not (Test-Path -LiteralPath $PlatformPath)) {
    Invoke-WebRequest -Uri 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15048&targ=self&form=text&view=full' -OutFile $PlatformPath
}

& $Python (Join-Path $AuditDir 'analyze_gse57495_holdout.py')
if ($LASTEXITCODE -ne 0) {
    throw "L'analyse a échoué avec le code $LASTEXITCODE"
}
