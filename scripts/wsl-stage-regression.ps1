[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [int]$Port = 8000,
    [switch]$SkipPytest,
    [switch]$SkipE2E,
    [switch]$KeepRunning,
    [switch]$EnableAI,
    [string]$DocxPath = "",
    [string]$AudioPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[GLOW WSL] $Message"
}

function Invoke-WslCommand {
    param(
        [string]$DistroName,
        [string[]]$ArgumentList
    )

    & wsl -d $DistroName -- @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "WSL command failed: $($ArgumentList -join ' ')"
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$webRoot = Join-Path $repoRoot "web"
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Expected Python virtual environment at $pythonExe."
}

$wslList = & wsl -l -q
if ($LASTEXITCODE -ne 0 -or -not ($wslList -contains $Distro)) {
    throw "WSL distro '$Distro' was not found. Run 'wsl -l -v' and retry with -Distro."
}

$dockerVersion = & wsl -d $Distro -- docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw (
        "Docker is not available inside WSL distro '$Distro'. Enable Docker Desktop " +
        "WSL integration for that distro, then rerun this script."
    )
}

$wslRepo = (& wsl -d $Distro -- wslpath -a $repoRoot | Out-String).Trim()
if (-not $wslRepo) {
    throw "Could not translate repo path '$repoRoot' into a WSL path."
}

$wslStageScript = "$wslRepo/scripts/wsl-stage-stack.sh"

$docxCandidate = if ($DocxPath) {
    $DocxPath
} else {
    Join-Path $repoRoot "samples\GLOW Test 2.docx"
}

if (-not (Test-Path $docxCandidate)) {
    throw "DOCX regression sample not found at $docxCandidate. Pass -DocxPath to override."
}

$aiValue = if ($EnableAI) { "1" } else { "0" }
$stageEnv = @(
    "env",
    "GLOW_WSL_PORT=$Port",
    "GLOW_ENABLE_AI=$aiValue",
    "GLOW_ENABLE_AI_CHAT=$aiValue",
    "GLOW_ENABLE_AI_WHISPERER=$aiValue",
    "GLOW_ENABLE_AI_HEADING_FIX=$aiValue",
    "GLOW_ENABLE_AI_ALT_TEXT=$aiValue",
    "GLOW_ENABLE_AI_MARKITDOWN_LLM=$aiValue"
)

$savedPythonPath = $env:PYTHONPATH
$savedBaseUrl = $env:E2E_BASE_URL
$savedPort = $env:E2E_PORT
$savedDocx = $env:E2E_UPLOAD_DOCX
$savedAudio = $env:E2E_UPLOAD_AUDIO

Write-Step "Starting WSL staging stack in $Distro on port $Port"
Invoke-WslCommand -DistroName $Distro -ArgumentList ($stageEnv + @("bash", $wslStageScript, "up"))

try {
    if (-not $SkipPytest) {
        Write-Step "Running focused pytest regression suite"
        $env:PYTHONPATH = "$repoRoot\web\src;$repoRoot\desktop\src"
        & $pythonExe -m pytest `
            web/tests/test_ai_feature_gates.py `
            web/tests/test_customization_warning.py `
            web/tests/test_fix_routes.py `
            web/tests/test_app.py `
            -q
        if ($LASTEXITCODE -ne 0) {
            throw "Focused pytest regression suite failed."
        }
    }

    if (-not $SkipE2E) {
        if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
            throw "npm is not available. Install Node.js before running Playwright regression tests."
        }

        if (-not (Test-Path (Join-Path $webRoot "node_modules"))) {
            throw "web/node_modules is missing. Run 'cd web; npm install' before using the WSL staging regression script."
        }

        Write-Step "Running Playwright regression suite against http://127.0.0.1:$Port"
        Push-Location $webRoot
        try {
            $env:E2E_BASE_URL = "http://127.0.0.1:$Port"
            $env:E2E_PORT = "$Port"
            $env:E2E_UPLOAD_DOCX = $docxCandidate
            if ($AudioPath) {
                $env:E2E_UPLOAD_AUDIO = $AudioPath
            }

            & npm run test:e2e:report
            if ($LASTEXITCODE -ne 0) {
                throw "Playwright regression suite failed."
            }
        }
        finally {
            Pop-Location
        }
    }
}
finally {
    $env:PYTHONPATH = $savedPythonPath
    $env:E2E_BASE_URL = $savedBaseUrl
    $env:E2E_PORT = $savedPort
    $env:E2E_UPLOAD_DOCX = $savedDocx
    $env:E2E_UPLOAD_AUDIO = $savedAudio

    if (-not $KeepRunning) {
        Write-Step "Stopping WSL staging stack"
        Invoke-WslCommand -DistroName $Distro -ArgumentList @("bash", $wslStageScript, "down")
    }
    else {
        Write-Step "Leaving WSL staging stack running"
    }
}

Write-Step "WSL staging regression pass completed"