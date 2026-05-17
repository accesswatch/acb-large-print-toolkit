[CmdletBinding()]
param(
    [string]$ServerHost = "lp.csedesigns.com",
    [string]$LocalGggPath = "C:\code\ggg",
    [switch]$Apply
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$mainScript = Join-Path $scriptRoot "sync-ggg-to-server.ps1"

if (-not (Test-Path -LiteralPath $mainScript)) {
    throw "Missing script: $mainScript"
}

$params = @{
    ServerHost = $ServerHost
    ServerUser = "jeffbis"
    LocalGggPath = $LocalGggPath
}

if ($Apply) {
    $params.ApplyGggRuntime = $true
}

& $mainScript @params
