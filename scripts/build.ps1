param(
    [switch]$SkipTests,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecFile = Join-Path $ProjectRoot "packaging\radar_desk.spec"
$InstallerScript = Join-Path $ProjectRoot "packaging\RadarDesk.iss"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Ambiente virtual não encontrado. Execute .\scripts\setup.ps1 primeiro."
}

Push-Location $ProjectRoot
try {
    & $PythonExe "scripts\create_icon.py"
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar os ícones." }

    if (-not $SkipTests) {
        & $PythonExe -m pytest
        if ($LASTEXITCODE -ne 0) { throw "Os testes falharam; o build foi interrompido." }
    }

    & $PythonExe -m PyInstaller --noconfirm --clean $SpecFile
    if ($LASTEXITCODE -ne 0) { throw "O PyInstaller não concluiu o executável." }

    if (-not $SkipInstaller) {
        $CompilerCandidates = @(
            (Get-Command iscc.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
        $Compiler = $CompilerCandidates | Select-Object -First 1
        if (-not $Compiler) {
            throw "Inno Setup 6 não encontrado. Instale-o ou execute com -SkipInstaller."
        }
        & $Compiler $InstallerScript
        if ($LASTEXITCODE -ne 0) { throw "O Inno Setup não concluiu o instalador." }

        $Installer = Get-ChildItem -LiteralPath "dist\installer" -Filter "*.exe" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        $Hash = (Get-FileHash -LiteralPath $Installer.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        Set-Content -LiteralPath "$($Installer.FullName).sha256" -Value "$Hash  $($Installer.Name)" -Encoding ascii
    }
}
finally {
    Pop-Location
}

Write-Host "Build da versão 1.0 concluído em $ProjectRoot\dist" -ForegroundColor Green
