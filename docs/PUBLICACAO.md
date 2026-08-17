# Publicação de uma versão

## Build local

Pré-requisitos: Python 3.11 ou superior e Inno Setup 6.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
.\scripts\build.ps1
```

O processo executa os testes, gera os ícones, cria `dist\RadarDesk\RadarDesk.exe`, compila o instalador e grava o SHA-256 em `dist\installer`.

## Release automatizada

1. Atualize `APP_VERSION`, `pyproject.toml`, `packaging/version_info.txt` e `packaging/RadarDesk.iss`.
2. Execute a suíte localmente.
3. Crie e envie a tag, por exemplo `v1.0.0`.
4. O workflow **Windows Release** testa, empacota, cria o instalador e publica os arquivos na release.

```powershell
git tag v1.0.0
git push origin v1.0.0
```

Não reutilize uma tag publicada. Para correções, incremente a versão e gere uma nova release.
