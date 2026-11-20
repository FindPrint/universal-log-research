# SPDX-License-Identifier: MIT
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Python .venv absent. Créez .venv et installez audit_release\requirements-lock.txt.'
}
Push-Location $root
try {
    & $python 'audit_release\run_matched_v59_v591_replay.py' --output-dir 'audit_release\matched_replay_rerun'
    if ($LASTEXITCODE -ne 0) { throw "Le replay apparié a échoué (code $LASTEXITCODE)." }
    & $python 'audit_release\run_l7b_integration.py' --modes light --output-dir 'audit_release\l7b_light_rerun'
    if ($LASTEXITCODE -ne 0) { throw "L'intégration L7b-light a échoué (code $LASTEXITCODE)." }
    & $python 'audit_release\run_l7b_full_reduced.py' --output-dir 'audit_release\l7b_full_rerun'
    if ($LASTEXITCODE -ne 0) { throw "L'intégration L7b-full a échoué (code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}
