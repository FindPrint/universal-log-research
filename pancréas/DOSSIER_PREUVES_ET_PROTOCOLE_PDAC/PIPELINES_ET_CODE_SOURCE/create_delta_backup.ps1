<#
.SYNOPSIS
    Sauvegarde incrémentale ultra-légère (DELTA) pour le projet Universal Log.
    Permet de sauvegarder uniquement les fichiers créés ou modifiés récemment
    sans jamais dupliquer les 10 Go du projet complet.

.DESCRIPTION
    Ce script :
    1. Cible le dossier de travail C:\Users\citys\Desktop\10-31-2026
    2. Exclut .venv, .git, __pycache__, GITHUB_REPO, archive_sources
    3. Filtre les fichiers modifiés depuis $Days jours (défaut: 2 jours)
    4. Crée une archive compressée légère (généralement < 20 Mo)
    5. La dépose dans D:\UNIVERSAL_LOG_BACKUPS\deltas\
#>

param(
    [int]$Days = 2,
    [string]$SourceDir = "C:\Users\citys\Desktop\10-31-2026",
    [string]$BackupBase = "D:\UNIVERSAL_LOG_BACKUPS\deltas"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   UNIVERSAL LOG — PROTOCOLE DE SAUVEGARDE DELTA LÉGÈRE   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $BackupBase)) {
    New-Item -ItemType Directory -Path $BackupBase -Force | Out-Null
}

$sinceDate = (Get-Date).AddDays(-$Days)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipName = "DELTA_UNIVERSAL_LOG_${timestamp}.zip"
$zipPath = Join-Path $BackupBase $zipName
$tempListDir = Join-Path $env:TEMP "delta_backup_$timestamp"

Write-Host "Recherche des fichiers modifiés depuis : $sinceDate" -ForegroundColor Yellow

$excludePatterns = @(
    "*\.venv\*",
    "*\.git\*",
    "*\GITHUB_REPO\*",
    "*\__pycache__\*",
    "*\archive_sources\*",
    "*\.idea\*",
    "*\.vscode\*",
    "*\*.zip"
)

$modifiedFiles = Get-ChildItem -Path $SourceDir -Recurse -File | Where-Object {
    $file = $_
    $file.LastWriteTime -ge $sinceDate -and -not ($excludePatterns | Where-Object { $file.FullName -like $_ })
}

$count = ($modifiedFiles | Measure-Object).Count
$totalBytes = ($modifiedFiles | Measure-Object -Property Length -Sum).Sum
$totalMo = [math]::Round($totalBytes / 1MB, 2)

Write-Host "Fichiers détectés : $count ($totalMo Mo)" -ForegroundColor Green

if ($count -eq 0) {
    Write-Host "Aucun fichier modifié récemment. Rien à sauvegarder." -ForegroundColor Gray
    exit 0
}

# Création du dossier temporaire pour structurer l'archive
New-Item -ItemType Directory -Path $tempListDir -Force | Out-Null

try {
    foreach ($f in $modifiedFiles) {
        $relPath = $f.FullName.Substring($SourceDir.Length).TrimStart('\')
        $destFile = Join-Path $tempListDir $relPath
        $destDir = Split-Path $destFile -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item -Path $f.FullName -Destination $destFile -Force
    }

    Write-Host "Compression de l'archive delta..." -ForegroundColor Yellow
    Compress-Archive -Path "$tempListDir\*" -DestinationPath $zipPath -CompressionLevel Optimal -Force

    $zipSizeMo = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
    Write-Host "✓ Sauvegarde delta créée avec succès :" -ForegroundColor Green
    Write-Host "  Fichier : $zipPath" -ForegroundColor White
    Write-Host "  Taille  : $zipSizeMo Mo (au lieu de 10 Go !)" -ForegroundColor White

    # Manifeste JSON associé
    $manifest = @{
        timestamp = (Get-Date).ToString("o")
        since_date = $sinceDate.ToString("o")
        files_count = $count
        total_uncompressed_bytes = $totalBytes
        zip_size_bytes = (Get-Item $zipPath).Length
        zip_file = $zipName
    }
    $manifestPath = [System.IO.Path]::ChangeExtension($zipPath, ".json")
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $manifestPath -Encoding UTF8
    Write-Host "✓ Manifeste : $manifestPath" -ForegroundColor Gray

} finally {
    if (Test-Path $tempListDir) {
        Remove-Item -Path $tempListDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
