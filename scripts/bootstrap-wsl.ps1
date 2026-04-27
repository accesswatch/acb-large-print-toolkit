# =============================================================================
# bootstrap-wsl.ps1 -- Run bootstrap-wsl.sh inside a WSL Ubuntu distro
# =============================================================================
# Usage:
#   .\scripts\bootstrap-wsl.ps1
#   .\scripts\bootstrap-wsl.ps1 -Distro Ubuntu-24.04
#
# To export the distro image after bootstrapping:
#   .\scripts\bootstrap-wsl.ps1 -Export
#   (saves glow-ubuntu.tar to D:\wsl-backups\ by default)
# =============================================================================
[CmdletBinding()]
param(
    [string]$Distro    = "Ubuntu",
    [string]$ExportDir = "D:\wsl-backups",
    [switch]$Export
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Msg) Write-Host "[bootstrap-wsl] $Msg" -ForegroundColor Cyan }

# Verify distro exists
$wslList = (& wsl -l -q) -replace "`0", "" | Where-Object { $_ -match '\S' }
if ($wslList -notcontains $Distro) {
    Write-Host "Distro '$Distro' not found. Available distros:" -ForegroundColor Red
    $wslList | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    Write-Host "To install Ubuntu 24.04:" -ForegroundColor Yellow
    Write-Host "  wsl --install -d Ubuntu-24.04"
    exit 1
}

$repoRoot  = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scriptWsl = "/mnt/" + ($repoRoot -replace "\\", "/" -replace "^([A-Za-z]):", '$1').ToLower()
$scriptWsl = "$scriptWsl/scripts/bootstrap-wsl.sh"

Write-Step "Running bootstrap-wsl.sh in distro '$Distro'"
Write-Step "Script path (WSL): $scriptWsl"
Write-Host ""

& wsl -d $Distro -- bash $scriptWsl
if ($LASTEXITCODE -ne 0) {
    Write-Host "Bootstrap failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

if ($Export) {
    Write-Host ""
    Write-Step "Exporting WSL image to $ExportDir"
    if (-not (Test-Path $ExportDir)) { New-Item -ItemType Directory -Path $ExportDir | Out-Null }

    $stamp    = Get-Date -Format "yyyyMMdd-HHmm"
    $tarPath  = Join-Path $ExportDir "glow-ubuntu-$stamp.tar"

    Write-Step "wsl --export $Distro $tarPath"
    & wsl --export $Distro $tarPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Export failed" -ForegroundColor Red
        exit 1
    }

    $sizeMB = [math]::Round((Get-Item $tarPath).Length / 1MB)
    Write-Host ""
    Write-Host "Exported: $tarPath ($sizeMB MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "To restore on a new machine:" -ForegroundColor Yellow
    Write-Host "  wsl --import glow-ubuntu C:\WSL\glow-ubuntu $tarPath --version 2"
    Write-Host "  wsl -d glow-ubuntu"
}
