# Radar Desk

Aplicativo Windows, local-first, para abertura e gerenciamento de chamados. A versão atual é a **1.0.0 oficial**, com instalador, atalhos, atualização assistida, dados demonstrativos e processo automatizado de publicação.

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
- painel de relatórios com filtro por período de abertura;
- chamados agrupados por status, categoria e prioridade;
- volume de chamados por dia e relação de SLAs atrasados;
- cálculo do tempo médio até a resolução;
- avaliação de atendimento de 1 a 5 estrelas por chamado concluído;
- exportação de relatório detalhado para Excel (`.xlsx`);
- geração de relatório operacional em PDF;
- ícone oficial para aplicativo e instalador;
- empacotamento reproduzível com PyInstaller;
- instalador por usuário com atalhos no menu Iniciar e na área de trabalho;
- verificação automática de novas versões oficiais no GitHub;
- carga opcional e idempotente de dados demonstrativos;
- workflow para testar e publicar releases do Windows;
- documentação de instalação, uso, publicação e vídeo;
- diretórios locais de dados, arquivos e logs;
- estrutura modular preparada para as próximas versões;
- testes automatizados da base e da interface.

Esta é a primeira versão oficial para distribuição no Windows.

## Instalação oficial

Baixe o instalador mais recente na página de [releases](https://github.com/tulioradames/radar-desk/releases). Consulte [docs/INSTALACAO.md](docs/INSTALACAO.md) para verificar o SHA-256, instalar, atualizar ou desinstalar.

## Primeiro acesso

Ao abrir o Radar Desk pela primeira vez, o aplicativo solicita a criação do administrador local. Nos acessos seguintes, use essa conta para entrar. As credenciais permanecem no SQLite local e a senha nunca é armazenada em texto puro.

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

## Gerar o aplicativo Windows

Com o Inno Setup 6 instalado:

```powershell
.\scripts\build.ps1
```

Os artefatos são gravados em `dist\RadarDesk` e `dist\installer`. O mesmo processo é executado pelo workflow de release do GitHub.

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

## Documentação

- [Instalação](docs/INSTALACAO.md)
- [Guia rápido](docs/GUIA_RAPIDO.md)
- [Publicação de versões](docs/PUBLICACAO.md)
- [Roteiro do vídeo](docs/VIDEO-ROTEIRO.md)

## Licença

Distribuído sob a licença MIT. Consulte `LICENSE`.
