param(
    [string]$MsysShell = "C:\msys64\usr\bin\bash.exe",
    [int]$Port = 3000
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed or not in PATH. Install Node.js and retry."
}

& ".\build.ps1" -MsysShell $MsysShell
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$env:PORT = "$Port"
node ".\ui\server.js"
