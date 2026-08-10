[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"

Write-Host "Radar Desk - configuração do ambiente" -ForegroundColor Cyan

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue

if ($PythonLauncher) {
    & $PythonLauncher.Source -3 -m venv $VirtualEnvironment
}
elseif ($PythonCommand) {
    & $PythonCommand.Source -m venv $VirtualEnvironment
}
else {
    throw "Python 3.11 ou superior não foi encontrado. Instale-o em https://python.org/downloads/"
}

$VenvPython = Join-Path $VirtualEnvironment "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements-dev.txt")

Write-Host ""
Write-Host "Ambiente configurado com sucesso." -ForegroundColor Green
Write-Host "Execute .\run.ps1 para abrir o Radar Desk."
