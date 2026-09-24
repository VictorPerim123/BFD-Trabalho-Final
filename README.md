# SavePoint

SavePoint é uma aplicação Flask para gerenciamento de backlog e acompanhamento da jornada do jogador. Além da biblioteca Steam, o sistema reúne progresso de conquistas, favoritos e prioridades, builds flexíveis, desafios pessoais, runs/speedrun, recordes pessoais e histórico por jogo.

## Principais recursos

- sincronização da biblioteca Steam, capas, tempo jogado, atividade recente e conquistas com ícones;
- detalhamento das conquistas por jogo;
- backlog com busca, filtros, ordenação, paginação, favoritos e prioridade;
- página de detalhes com abas para visão geral, conquistas filtráveis, Jornada, desafios e histórico;
- dashboard com saúde do backlog e jogos quase concluídos;
- Jornada unificada para builds, runs, categorias e recordes pessoais;
- builds com atributos flexíveis para diferentes gêneros;
- desafios pessoais de backlog, conquistas e speedrun;
- runs por categoria, associação com build e identificação automática de PB;
- evolução do banco com Flask-Migrate/Alembic.

## Execução local

Crie e ative um ambiente virtual, instale as dependências e configure o ambiente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Crie ou atualize o banco:

```powershell
flask --app run.py db upgrade
```

Execute:

```powershell
python run.py
```

A aplicação fica disponível em `http://localhost:5000`.

Sem `DATABASE_URL`, o projeto usa SQLite em `instance/savepoint.sqlite3`.

## PostgreSQL local

Defina no `.env` uma URL de conexão válida:

```text
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/savepoint
```

Depois execute:

```powershell
flask --app run.py db upgrade
python run.py
```

## Banco criado antes da adoção do Alembic

As migrações foram preparadas para adotar o schema das versões anteriores. Faça backup do banco e execute:

```powershell
flask --app run.py db upgrade
```

## Dados de demonstração

Depois das migrações:

```powershell
python database\seed.py
```

Login de demonstração:

```text
usuário: demo
senha: SavePoint123
```

## Steam

Defina `STEAM_API_KEY` no `.env`. Para importar biblioteca e conquistas, o perfil e os detalhes dos jogos da conta consultada precisam estar disponíveis para a API da Steam.

A importação possui uma etapa de prévia: o sistema analisa a biblioteca e mostra quantos jogos serão adicionados, associados, atualizados ou preservados antes da confirmação. A sincronização final atualiza jogos já vinculados sem duplicá-los e preserva dados válidos quando uma consulta externa falha. O usuário pode manter novos jogos como `Quero jogar` ou classificá-los automaticamente como `Quero jogar`, `Jogando`, `Jogado` ou `Platinado` conforme atividade, tempo e conquistas disponíveis na Steam.

## Testes

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

## Docker

```powershell
docker compose up --build
```

O container web executa `flask db upgrade` antes de iniciar a aplicação.
