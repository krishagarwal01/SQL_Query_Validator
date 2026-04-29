param(
    [string]$SqlFile = "input.sql",
    [string]$Query = "",
    [switch]$BuildFirst
)

$ErrorActionPreference = "Stop"

if ($BuildFirst) {
    & ".\build.ps1"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$Exe = Join-Path (Resolve-Path ".").Path "sqlparse_json.exe"
if (-not (Test-Path $Exe)) {
    Write-Error "sqlparse_json.exe not found. Run .\build.ps1 first or use -BuildFirst."
}

if ($Query -and $Query.Trim().Length -gt 0) {
    $Query | & $Exe
    exit $LASTEXITCODE
}

if (-not (Test-Path $SqlFile)) {
    Write-Error "SQL file '$SqlFile' not found."
}

Get-Content -Raw -Path $SqlFile | & $Exe
exit $LASTEXITCODE
