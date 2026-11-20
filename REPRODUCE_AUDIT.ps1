$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Python .venv absent. Créez .venv et installez audit_release\requirements-lock.txt.'
}
Push-Location $root
try {
    & $python 'audit_release\build_v5_9_1_auditfix.py'
    if ($LASTEXITCODE -ne 0) { throw "Le patch dérivé a échoué (code $LASTEXITCODE)." }
    & $python 'audit_release\validate_v5_9_1_auditfix.py'
    if ($LASTEXITCODE -ne 0) { throw "La validation a échoué (code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}
