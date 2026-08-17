# Instalação do Radar Desk 1.0

## Instalador oficial

1. Abra a página de [releases do Radar Desk](https://github.com/tulioradames/radar-desk/releases).
2. Baixe `RadarDesk-Setup-1.0.0.exe`.
3. Compare o SHA-256 do arquivo com `RadarDesk-Setup-1.0.0.exe.sha256`.
4. Execute o instalador e escolha se deseja criar o atalho na área de trabalho.
5. Abra o Radar Desk pelo menu Iniciar e crie o administrador local no primeiro acesso.

O instalador é por usuário e grava o programa em `%LOCALAPPDATA%\Programs\Radar Desk`. Os dados permanecem separados em `%LOCALAPPDATA%\RadarDesk`, portanto uma atualização não remove chamados ou evidências.

Enquanto o projeto não possuir um certificado comercial de assinatura de código, o Windows pode exibir o aviso do SmartScreen. Baixe somente pela release oficial e confira o SHA-256 antes de prosseguir.

## Verificação do SHA-256

```powershell
Get-FileHash .\RadarDesk-Setup-1.0.0.exe -Algorithm SHA256
```

## Execução pelo código-fonte

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
.\run.ps1
```

## Desinstalação

Use **Configurações > Aplicativos > Aplicativos instalados > Radar Desk > Desinstalar**. A desinstalação preserva os dados locais para evitar perda acidental. Para removê-los deliberadamente, exclua `%LOCALAPPDATA%\RadarDesk` após criar um backup.
