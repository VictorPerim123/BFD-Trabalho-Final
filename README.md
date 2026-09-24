# SavePoint

SavePoint é uma aplicação web desenvolvida com Flask para gerenciamento de backlog de jogos e acompanhamento da jornada do jogador.

Além da integração com a biblioteca Steam, o sistema permite acompanhar conquistas, favoritos, prioridades, builds, desafios pessoais, runs, speedruns, recordes pessoais e o histórico de cada jogo.

## Principais recursos

- sincronização da biblioteca Steam;
- importação de capas, tempo jogado e atividade recente;
- sincronização de conquistas com ícones;
- detalhamento das conquistas por jogo;
- backlog com busca, filtros, ordenação, paginação, favoritos e prioridades;
- página de detalhes do jogo com visão geral, conquistas, Jornada, desafios e histórico;
- dashboard com informações sobre a saúde do backlog e jogos próximos da conclusão;
- Jornada unificada para builds, runs, categorias e recordes pessoais;
- builds com atributos flexíveis para diferentes gêneros de jogos;
- desafios pessoais de backlog, conquistas e speedrun;
- runs organizadas por categoria e associáveis a builds;
- identificação automática de recordes pessoais (PB);
- evolução do banco de dados utilizando Flask-Migrate e Alembic.

## Tecnologias

### Backend

- **Python 3**;
- **Flask** — framework web;
- **Flask-SQLAlchemy / SQLAlchemy** — ORM e acesso ao banco de dados;
- **Flask-Migrate / Alembic** — versionamento e migração do schema;
- **Flask-WTF** — proteção CSRF;
- **Requests** — comunicação com a Steam Web API;
- **python-dotenv** — carregamento das variáveis de ambiente.

### Frontend

- **HTML5** com templates **Jinja2**;
- **CSS3** com CSS Grid, media queries e layout responsivo;
- **JavaScript Vanilla**;
- **Fetch API** para consumo dos endpoints JSON do backend;
- práticas básicas de acessibilidade com HTML semântico e atributos ARIA.

### Banco de dados

- **SQLite** como opção padrão para desenvolvimento local;
- **PostgreSQL** por meio da variável `DATABASE_URL`;
- **psycopg2** como driver PostgreSQL.

### Testes e infraestrutura

- **Pytest** para testes automatizados;
- **Docker** e **Docker Compose** para execução em containers;
- **Git/GitHub** para versionamento e colaboração.

## Arquitetura

O SavePoint utiliza **Application Factory**, **Blueprints**, uma camada de serviços para as principais regras de negócio e persistência com SQLAlchemy.

O diagrama e a descrição detalhada da arquitetura estão disponíveis em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

## Execução local

### 1. Criar o ambiente virtual

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows — PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 3. Criar o arquivo de configuração

#### Linux / macOS

```bash
cp .env.example .env
```

#### Windows — PowerShell

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env` conforme necessário.

### 4. Criar ou atualizar o banco de dados

```bash
python -m flask --app run.py db upgrade
```

Para verificar a migração atual:

```bash
python -m flask --app run.py db current
```

### 5. Executar a aplicação

```bash
python run.py
```

A aplicação ficará disponível em:

```text
http://localhost:5000
```

## Banco de dados

### SQLite

Caso `DATABASE_URL` não seja definida, o SavePoint utiliza SQLite automaticamente em:

```text
instance/savepoint.sqlite3
```

Mesmo que o arquivo SQLite já exista, ainda é necessário aplicar as migrações em uma instalação nova:

```bash
python -m flask --app run.py db upgrade
```

## Dados de demonstração

Depois de aplicar as migrações:

```bash
python database/seed.py
```

Login de demonstração:

```text
usuário: demo
senha: SavePoint123
```

## Integração com a Steam

Para utilizar a integração com a Steam, defina `STEAM_API_KEY` no arquivo `.env`:

```text
STEAM_API_KEY=SUA_CHAVE
```

Para importar biblioteca e conquistas, o perfil Steam e os detalhes dos jogos da conta consultada precisam estar disponíveis para a API da Steam.

A importação possui uma etapa de prévia. Antes da confirmação, o sistema analisa a biblioteca e informa quantos jogos serão adicionados, associados, atualizados ou preservados.

A sincronização final atualiza jogos já vinculados sem duplicá-los e preserva dados válidos quando uma consulta externa falha.

Durante a importação, o usuário pode manter novos jogos como `Quero jogar` ou permitir que o sistema os classifique automaticamente como:

- `Quero jogar`;
- `Jogando`;
- `Jogado`;
- `Platinado`.

A classificação automática considera informações disponíveis na Steam, como atividade recente, tempo jogado e progresso de conquistas.

## Testes

Instale as dependências de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
```

Execute a suíte de testes:

```bash
pytest -q
```

## Docker

```bash
docker compose up --build
```

O container da aplicação executa `flask db upgrade` antes de iniciar o servidor web.

## Equipe e Contato

- **Adriano Silva** — GitHub: [@Tahuno](https://github.com/Tahuno)
- **Victor Perim** — GitHub: [@VictorPerim123](https://github.com/VictorPerim123)

**Repositório do projeto:** [github.com/VictorPerim123/BFD-Trabalho-Final](https://github.com/VictorPerim123/BFD-Trabalho-Final)

## Fluxo rápido para uma instalação nova

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m flask --app run.py db upgrade
python run.py
```

### Windows — PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m flask --app run.py db upgrade
python run.py
```

Depois, acesse:

```text
http://localhost:5000
```
