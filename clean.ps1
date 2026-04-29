param(
    [string]$MsysShell = "C:\msys64\usr\bin\bash.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $MsysShell)) {
    Write-Error "MSYS2 bash not found at '$MsysShell'. Install MSYS2 or pass -MsysShell with the correct path."
}

$ProjectPath = (Resolve-Path ".").Path
$MsysProjectPath = "/" + $ProjectPath.Substring(0, 1).ToLower() + $ProjectPath.Substring(2).Replace("\", "/")

& $MsysShell -lc "cd '$MsysProjectPath' && make clean"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Clean complete."
