[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "O ambiente ainda não foi configurado." -ForegroundColor Yellow
    Write-Host "Executando a configuração inicial..."
    & (Join-Path $ProjectRoot "scripts\setup.ps1")
}

& $VenvPython (Join-Path $ProjectRoot "app.py")
