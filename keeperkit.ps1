param(
    [Parameter(Position = 0)]
    [ValidateSet("backend", "api")]
    [string]$Command = "backend",
    [switch]$Reload,
    [switch]$OnlineHuggingFace,
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot

switch ($Command) {
    { $_ -in @("backend", "api") } {
        & (Join-Path $RootDir "backend\scripts\start_backend.ps1") `
            -HostName $HostName `
            -Port $Port `
            -Reload:$Reload `
            -OnlineHuggingFace:$OnlineHuggingFace
        break
    }
}
