[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ServerHost,

    [string]$ServerUser = "deploy",

    [string]$LocalGggPath = "C:\code\ggg",

    [string]$RemoteGggPath = "~/ggg",

    [switch]$ApplyGggRuntime,

    [string]$AppRoot = "~/app",

    [string]$WebRoot = "~/app/web"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandAvailable {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Invoke-Remote {
    param([Parameter(Mandatory = $true)][string]$Command)

    $target = "$ServerUser@$ServerHost"
    Write-Host "[remote] $Command"
    & ssh $target $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed (exit $LASTEXITCODE): $Command"
    }
}

Write-Host "== GGG sync from Windows to server =="
Write-Host "Server: $ServerUser@$ServerHost"
Write-Host "Local:  $LocalGggPath"
Write-Host "Remote: $RemoteGggPath"
Write-Host "Apply runtime: $ApplyGggRuntime"
Write-Host ""

Test-CommandAvailable -Name "ssh"
Test-CommandAvailable -Name "tar"
Test-CommandAvailable -Name "scp"

if (-not (Test-Path -LiteralPath $LocalGggPath)) {
    throw "Local path does not exist: $LocalGggPath"
}

if (-not (Test-Path -LiteralPath (Join-Path $LocalGggPath "site"))) {
    Write-Warning "Expected site directory missing at $LocalGggPath\site. Continuing anyway."
}

# Sanity-check SSH connectivity up front.
Write-Host "Checking SSH connectivity..."
Invoke-Remote -Command "echo connected"
Write-Host "SSH check passed."
Write-Host ""

# Clean remote source folder before upload so removed local files are not left behind.
Write-Host "Preparing remote folder..."
Invoke-Remote -Command "mkdir -p '$RemoteGggPath'; find '$RemoteGggPath' -mindepth 1 -maxdepth 1 -exec rm -rf {} +"
Write-Host "Remote folder prepared."
Write-Host ""

# Package then upload with scp, then extract remotely.
Write-Host "Uploading all GGG files (including media) ..."
$tempTar = Join-Path $env:TEMP ("ggg-sync-" + [Guid]::NewGuid().ToString("N") + ".tar")

try {
    & tar -C $LocalGggPath -cf $tempTar .
    if ($LASTEXITCODE -ne 0) {
        throw "Failed creating tar archive (exit $LASTEXITCODE)."
    }

    $remoteTar = "$RemoteGggPath/ggg-upload.tar"
    & scp $tempTar "${ServerUser}@${ServerHost}:$remoteTar"
    if ($LASTEXITCODE -ne 0) {
        throw "Upload failed during scp (exit $LASTEXITCODE)."
    }

    Invoke-Remote -Command "tar -xf '$remoteTar' -C '$RemoteGggPath'; rm -f '$remoteTar'"
}
finally {
    if (Test-Path -LiteralPath $tempTar) {
        Remove-Item -LiteralPath $tempTar -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Upload complete."
Write-Host ""

Write-Host "Verifying remote content..."
Invoke-Remote -Command "set -e; test -f '$RemoteGggPath/Caddyfile'; test -d '$RemoteGggPath/site'; test -f '$RemoteGggPath/site/feed.xml' || true; ls -lah '$RemoteGggPath' | head; ls -lah '$RemoteGggPath/site' | head"
Write-Host "Remote verification complete."
Write-Host ""

if ($ApplyGggRuntime) {
    Write-Host "Applying GGG-only runtime changes on server..."
    Invoke-Remote -Command "mkdir -p '$AppRoot/ggg'"

    # Mirror source into runtime folder. Prefer rsync; fallback to cp.
    Invoke-Remote -Command "if command -v rsync >/dev/null 2>&1; then rsync -av --delete '$RemoteGggPath/' '$AppRoot/ggg/'; else rm -rf '$AppRoot/ggg'/*; cp -a '$RemoteGggPath/'* '$AppRoot/ggg/'; fi"

    # Recreate only ggg + caddy services so route/content updates are picked up.
    Invoke-Remote -Command "cd '$WebRoot' && docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate ggg caddy"

    Write-Host "Running quick remote checks..."
    Invoke-Remote -Command "curl -sSI https://lp.csedesigns.com/ggg/ | head -n 5"
    Invoke-Remote -Command "curl -sSI https://lp.csedesigns.com/ggg/feed.xml | head -n 5"
    Write-Host "GGG runtime apply completed."
}

Write-Host ""
Write-Host "Done."
Write-Host "Only GGG content/actions were applied. No full Glow deploy steps were run by this script."