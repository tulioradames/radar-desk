# Radar Desk

Aplicativo Windows, local-first, para abertura e gerenciamento de chamados. A versão atual é a **0.7.0** e adiciona usuários, auditoria e sincronização opcional sem comprometer o funcionamento offline.

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
- busca geral por protocolo, conteúdo e responsável;
- filtros por status, prioridade, categoria e período;
- responsável pelo atendimento;
- histórico automático de alterações;
- comentários e interações por chamado;
- reabertura de chamados resolvidos;
- coleta de sistema operacional, computador, usuário e IP local;
- uso de memória e armazenamento;
- estado da conexão e teste de ping;
- prévia exata de todos os dados antes do anexo;
- captura da tela principal somente após autorização explícita;
- relatórios JSON organizados por protocolo e vinculados ao chamado;
- anexos de imagens, documentos e logs com limite de 50 MB por arquivo;
- arrastar e soltar arquivos diretamente no chamado;
- visualizador interno de imagens com zoom, ajuste, rotação e navegação;
- abertura de documentos e logs no programa padrão do Windows;
- organização automática de evidências nas pastas do protocolo;
- prazos de SLA por prioridade: Crítica 4h, Alta 8h, Média 24h e Baixa 48h;
- destaque visual para chamados atrasados e próximos do vencimento;
- notificações nativas do Windows para alertas de SLA;
- categorização automática por palavras-chave durante o cadastro;
- confirmação antes de encerrar um chamado resolvido;
- primeiro acesso com criação segura do administrador local;
- login offline com senhas protegidas por PBKDF2 e salt individual;
- perfis de Solicitante, Atendente e Administrador;
- permissões operacionais aplicadas conforme o perfil;
- auditoria de login, chamados, comentários, arquivos, diagnósticos e sincronização;
- fila local compactada, com novas tentativas quando a internet retornar;
- sincronização opcional com Supabase sem duplicar chamados pelo protocolo;
- resolução determinística de conflitos por versão e data de atualização;
- diretórios locais de dados, arquivos e logs;
- estrutura modular preparada para as próximas versões;
- testes automatizados da base e da interface.

Relatórios e distribuição permanecem preparados como módulos futuros.

## Primeiro acesso

Ao abrir a versão 0.7 pela primeira vez, o Radar Desk solicita a criação do administrador local. Nos acessos seguintes, use essa conta para entrar. As credenciais permanecem no SQLite local e a senha nunca é armazenada em texto puro.

## Sincronização opcional com Supabase

O aplicativo funciona integralmente sem servidor. Para habilitar a sincronização, execute [`supabase/schema.sql`](supabase/schema.sql) no projeto Supabase e defina antes de iniciar:

```powershell
$env:SUPABASE_URL="https://seu-projeto.supabase.co"
$env:SUPABASE_ANON_KEY="sua-chave"
$env:SUPABASE_ACCESS_TOKEN="token-jwt-de-um-usuario-autenticado"
```

As alterações feitas sem conexão permanecem na fila SQLite. O aplicativo tenta novamente automaticamente a cada minuto e também oferece sincronização manual. As chaves e o token não são gravados no código nem no banco local. O token deve pertencer a um usuário autenticado no Supabase, conforme a política RLS fornecida.

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
│   └── RD-2026-0001\
│       ├── imagens\
│       ├── documentos\
│       └── diagnosticos\
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
