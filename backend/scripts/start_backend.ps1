param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload,
    [switch]$OnlineHuggingFace
)

$ErrorActionPreference = "Stop"

$BackendDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$CondaPython = "D:\anaconda3\envs\keeperkit\python.exe"

if (-not (Test-Path $CondaPython)) {
    throw "KeeperKit conda Python not found: $CondaPython"
}

if (-not $OnlineHuggingFace) {
    $env:HF_HUB_OFFLINE = "1"
    $env:TRANSFORMERS_OFFLINE = "1"
}

Write-Host "KeeperKit backend"
Write-Host "Python: $CondaPython"
Write-Host "Backend: $BackendDir"
Write-Host "URL: http://$HostName`:$Port"
Write-Host "HF offline: $(-not $OnlineHuggingFace)"

$Args = @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    $HostName,
    "--port",
    $Port
)

if ($Reload) {
    $Args += "--reload"
}

Push-Location $BackendDir
try {
    & $CondaPython @Args
}
finally {
    Pop-Location
}
