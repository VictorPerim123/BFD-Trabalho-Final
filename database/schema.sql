CREATE TABLE IF NOT EXISTS usuario (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(120) NOT NULL,
    username      VARCHAR(60)  NOT NULL UNIQUE,
    email         VARCHAR(160) NOT NULL UNIQUE,
    senha_hash    VARCHAR(255) NOT NULL,
    steam_id      VARCHAR(32),
    criado_em     TIMESTAMP NOT NULL DEFAULT NOW()
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
                         CHECK (status IN ('quero_jogar', 'jogando', 'zerado', 'platinado', 'abandonado')),
    nota                 REAL CHECK (nota IS NULL OR (nota >= 0 AND nota <= 10)),
    tempo_jogado_horas   INTEGER NOT NULL DEFAULT 0,
    total_conquistas     INTEGER NOT NULL DEFAULT 0,
    conquistas_obtidas   INTEGER NOT NULL DEFAULT 0,
    steam_appid          INTEGER,
    criado_em            TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_jogo_usuario_id ON jogo (usuario_id);

-- Relacao N:M entre Jogo e Categoria
CREATE TABLE IF NOT EXISTS jogo_categoria (
    jogo_id       INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    categoria_id  INTEGER NOT NULL REFERENCES categoria(id) ON DELETE CASCADE,
    PRIMARY KEY (jogo_id, categoria_id)
);

CREATE TABLE IF NOT EXISTS run_diario (
    id                 SERIAL PRIMARY KEY,
    jogo_id            INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    data               DATE NOT NULL,
    duracao_segundos   INTEGER NOT NULL DEFAULT 0,
    resultado          VARCHAR(10) NOT NULL CHECK (resultado IN ('vitoria', 'derrota')),
    causa_morte        VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS ix_run_diario_jogo_id ON run_diario (jogo_id);

CREATE TABLE IF NOT EXISTS build_anotacao (
    id                     SERIAL PRIMARY KEY,
    jogo_id                INTEGER NOT NULL REFERENCES jogo(id) ON DELETE CASCADE,
    nome_build             VARCHAR(120) NOT NULL,
    detalhes_equipamento   TEXT,
    habilidades            TEXT
);

CREATE INDEX IF NOT EXISTS ix_build_anotacao_jogo_id ON build_anotacao (jogo_id);

CREATE TABLE IF NOT EXISTS amizade (
    usuario_solicitante_id  INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    usuario_receptor_id     INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    status_solicitacao      VARCHAR(10) NOT NULL DEFAULT 'pendente'
                             CHECK (status_solicitacao IN ('pendente', 'aceita', 'recusada')),
    PRIMARY KEY (usuario_solicitante_id, usuario_receptor_id)
);
