param(
    [string]$SqlFile = "input.sql",
    [string]$Query = "",
    [string]$MsysShell = "C:\msys64\usr\bin\bash.exe"
)

$ErrorActionPreference = "Stop"

& ".\build.ps1" -MsysShell $MsysShell
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($Query -and $Query.Trim().Length -gt 0) {
    & ".\run.ps1" -Query $Query
    exit $LASTEXITCODE
}

& ".\run.ps1" -SqlFile $SqlFile
exit $LASTEXITCODE
