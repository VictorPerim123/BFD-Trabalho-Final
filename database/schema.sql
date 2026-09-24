CREATE TABLE IF NOT EXISTS usuario (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(120) NOT NULL,
    username      VARCHAR(60)  NOT NULL UNIQUE,
    email         VARCHAR(160) NOT NULL UNIQUE,
    senha_hash    VARCHAR(255) NOT NULL,
    steam_id      VARCHAR(32),
    criado_em     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categoria (
    id            SERIAL PRIMARY KEY,
    usuario_id    INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    nome          VARCHAR(60) NOT NULL,
    cor_hex       VARCHAR(7) NOT NULL DEFAULT '#a78bfa',
    CONSTRAINT uq_categoria_usuario_nome UNIQUE (usuario_id, nome)
);

CREATE TABLE IF NOT EXISTS jogo (
    id                   SERIAL PRIMARY KEY,
    usuario_id           INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    titulo               VARCHAR(160) NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'quero_jogar'
                         CHECK (status IN ('quero_jogar', 'jogando', 'jogado', 'zerado', 'platinado', 'abandonado')),
    nota                 REAL CHECK (nota IS NULL OR (nota >= 0 AND nota <= 10)),
    favorito             BOOLEAN NOT NULL DEFAULT FALSE,
    prioridade           VARCHAR(10) NOT NULL DEFAULT 'normal'
                         CHECK (prioridade IN ('baixa', 'normal', 'alta')),
    tempo_jogado_horas   INTEGER NOT NULL DEFAULT 0 CHECK (tempo_jogado_horas >= 0),
    total_conquistas     INTEGER NOT NULL DEFAULT 0 CHECK (total_conquistas >= 0),
    conquistas_obtidas   INTEGER NOT NULL DEFAULT 0 CHECK (
                             conquistas_obtidas >= 0 AND conquistas_obtidas <= total_conquistas
                         ),
    steam_appid          INTEGER,
    capa_url             VARCHAR(500),
    criado_em            TIMESTAMP DEFAULT NOW(),
    atualizado_em        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_jogo_usuario_steam_appid UNIQUE (usuario_id, steam_appid)
);

CREATE INDEX IF NOT EXISTS ix_jogo_usuario_id ON jogo (usuario_id);
CREATE INDEX IF NOT EXISTS ix_jogo_status ON jogo (status);
CREATE INDEX IF NOT EXISTS ix_jogo_prioridade ON jogo (prioridade);
CREATE INDEX IF NOT EXISTS ix_jogo_steam_appid ON jogo (steam_appid);
CREATE INDEX IF NOT EXISTS ix_jogo_criado_em ON jogo (criado_em);

CREATE TABLE IF NOT EXISTS jogo_categoria (
    jogo_id       INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    categoria_id  INTEGER NOT NULL REFERENCES categoria(id) ON DELETE CASCADE,
    PRIMARY KEY (jogo_id, categoria_id)
);

CREATE TABLE IF NOT EXISTS build_anotacao (
    id                     SERIAL PRIMARY KEY,
    jogo_id                INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    nome_build             VARCHAR(120) NOT NULL,
    descricao              TEXT,
    objetivo               VARCHAR(160),
    status                 VARCHAR(20) NOT NULL DEFAULT 'planejada'
                           CHECK (status IN ('planejada', 'em_uso', 'finalizada', 'experimental')),
    nivel                  INTEGER,
    detalhes_equipamento   TEXT,
    habilidades            TEXT,
    observacoes            TEXT
);

CREATE INDEX IF NOT EXISTS ix_build_anotacao_jogo_id ON build_anotacao (jogo_id);

CREATE TABLE IF NOT EXISTS build_atributo (
    id         SERIAL PRIMARY KEY,
    build_id   INTEGER NOT NULL REFERENCES build_anotacao(id) ON DELETE CASCADE,
    nome       VARCHAR(80) NOT NULL,
    valor      VARCHAR(120) NOT NULL,
    ordem      INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_build_atributo_nome UNIQUE (build_id, nome)
);

CREATE INDEX IF NOT EXISTS ix_build_atributo_build_id ON build_atributo (build_id);

CREATE TABLE IF NOT EXISTS run_diario (
    id                 SERIAL PRIMARY KEY,
    jogo_id            INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    build_id           INTEGER REFERENCES build_anotacao(id) ON DELETE SET NULL,
    data               DATE NOT NULL,
    duracao_segundos   INTEGER NOT NULL DEFAULT 1 CHECK (duracao_segundos > 0),
    resultado          VARCHAR(10) NOT NULL CHECK (resultado IN ('vitoria', 'derrota')),
    categoria          VARCHAR(80) NOT NULL DEFAULT 'Casual',
    causa_morte        VARCHAR(200),
    observacao         VARCHAR(300),
    eh_pb              BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_run_diario_jogo_id ON run_diario (jogo_id);
CREATE INDEX IF NOT EXISTS ix_run_diario_build_id ON run_diario (build_id);
CREATE INDEX IF NOT EXISTS ix_run_jogo_categoria ON run_diario (jogo_id, categoria);

CREATE TABLE IF NOT EXISTS conquista_steam (
    id                    SERIAL PRIMARY KEY,
    jogo_id               INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    api_name              VARCHAR(160) NOT NULL,
    nome                  VARCHAR(200),
    descricao             TEXT,
    icone_url             VARCHAR(500),
    icone_bloqueada_url   VARCHAR(500),
    desbloqueada          BOOLEAN NOT NULL DEFAULT FALSE,
    desbloqueada_em       TIMESTAMP,
    CONSTRAINT uq_conquista_jogo_api_name UNIQUE (jogo_id, api_name)
);

CREATE INDEX IF NOT EXISTS ix_conquista_steam_jogo_id ON conquista_steam (jogo_id);

CREATE TABLE IF NOT EXISTS historico_jogo (
    id          SERIAL PRIMARY KEY,
    jogo_id     INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    tipo        VARCHAR(40) NOT NULL,
    descricao   VARCHAR(255) NOT NULL,
    criado_em   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_historico_jogo_jogo_criado ON historico_jogo (jogo_id, criado_em);

CREATE TABLE IF NOT EXISTS desafio (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    jogo_id        INTEGER REFERENCES jogo(id) ON DELETE CASCADE,
    titulo         VARCHAR(160) NOT NULL,
    descricao      TEXT,
    tipo           VARCHAR(30) NOT NULL DEFAULT 'personalizado'
                   CHECK (tipo IN ('backlog', 'conquistas', 'speedrun', 'personalizado')),
    meta           VARCHAR(120),
    progresso      VARCHAR(120),
    data_inicio    DATE NOT NULL DEFAULT CURRENT_DATE,
    data_limite    DATE,
    status         VARCHAR(20) NOT NULL DEFAULT 'ativo'
                   CHECK (status IN ('ativo', 'concluido', 'cancelado')),
    criado_em      TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_desafio_usuario_status ON desafio (usuario_id, status);
