# Radar Desk

Aplicativo Windows, local-first, para abertura e gerenciamento de chamados. A versão atual é a **0.2.0** e já permite administrar chamados sem depender de internet.

## O que já está pronto

- janela principal responsiva em PySide6;
- menu superior com navegação horizontal por módulos;
- identidade visual própria, com marca vetorial do Radar Desk;
- modos claro e escuro com preferência persistente;
- banco SQLite local, versionado e verificado na inicialização;
- criação, edição e exclusão de chamados;
- protocolos automáticos no formato `RD-2026-0001`;
- título, descrição, categoria, prioridade e status;
- registro automático das datas de abertura e atualização;
- painel com totais e chamados ativos;
- diretórios locais de dados, arquivos e logs;
- estrutura modular preparada para as próximas versões;
- testes automatizados da base e da interface.

Diagnóstico, relatórios e recursos operacionais avançados permanecem preparados como módulos futuros.

## Requisitos

- Windows 10 ou 11;
- Python 3.11 ou superior;
- PowerShell 5.1 ou superior.

## Configuração automática

No PowerShell, dentro da pasta do projeto:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```

O script cria `.venv`, atualiza o `pip` e instala todas as dependências com versões fixadas.

## Executar

```powershell
.\run.ps1
```

Também é possível executar diretamente:

```powershell
.\.venv\Scripts\python.exe app.py
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Dados locais

Por padrão, os dados são gravados em:

```text
%LOCALAPPDATA%\RadarDesk\
├── radar_desk.sqlite3
├── arquivos\
└── logs\
```

Durante testes ou desenvolvimento, o caminho pode ser alterado com a variável `RADARDESK_DATA_DIR`.

## Estrutura

```text
RadarDesk/
├── radar_desk/
│   ├── core/       # configuração e logs
│   ├── data/       # SQLite e futuras migrações
│   ├── resources/  # identidade visual
│   ├── services/   # casos de uso das próximas versões
│   └── ui/         # janela, componentes e temas
├── scripts/        # preparação do ambiente
├── tests/          # testes automatizados
├── app.py          # atalho para execução
└── pyproject.toml  # metadados e dependências
```

## Arquitetura futura

O SQLite permanece como fonte local para o funcionamento offline. A sincronização com Supabase será adicionada somente na versão 0.7, por uma camada separada de sincronização, sem inserir credenciais ou dependência de rede no aplicativo atual.

## Licença

Distribuído sob a licença MIT. Consulte `LICENSE`.
