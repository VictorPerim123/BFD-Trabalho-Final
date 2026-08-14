-- Script do banco
CREATE TABLE IF NOT EXISTS usuarios (
    "idUsuario" INTEGER GENERATED ALWAYS AS IDENTITY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senhaHash VARCHAR(255) NOT NULL,

    PRIMARY KEY ("idUsuario"),
    UNIQUE (username),
    UNIQUE (email)
);


CREATE TABLE IF NOT EXISTS jogo (
    "idJogo" INTEGER GENERATED ALWAYS AS IDENTITY,
    "idUsuario" INTEGER NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    status VARCHAR(100),
    nota NUMERIC(3,1),
    "tempoJogado" INTERVAL,
    "totalConquista" INTEGER DEFAULT 0,
    "conquistaObtida" INTEGER DEFAULT 0,

    PRIMARY KEY ("idJogo"),

    FOREIGN KEY ("idUsuario")
        REFERENCES usuarios("idUsuario"),

    CHECK (nota >= 0 AND nota <= 10),
    CHECK ("totalConquista" >= 0),
    CHECK ("conquistaObtida" >= 0),
    CHECK ("conquistaObtida" <= "totalConquista")
);


CREATE TABLE IF NOT EXISTS categoria (
    "idCategoria" INTEGER GENERATED ALWAYS AS IDENTITY,
    "idUsuario" INTEGER NOT NULL,
    nome VARCHAR(100) NOT NULL,
    cor VARCHAR(100),

    PRIMARY KEY ("idCategoria"),

    FOREIGN KEY ("idUsuario")
        REFERENCES usuarios("idUsuario")
);


CREATE TABLE IF NOT EXISTS "jogoCategoria" (
    "idJogoCategoria" INTEGER GENERATED ALWAYS AS IDENTITY,
    "idJogo" INTEGER NOT NULL,
    "idCategoria" INTEGER NOT NULL,

    PRIMARY KEY ("idJogoCategoria"),

    FOREIGN KEY ("idJogo")
        REFERENCES jogo("idJogo"),

    FOREIGN KEY ("idCategoria")
        REFERENCES categoria("idCategoria"),

    UNIQUE ("idJogo", "idCategoria")
);


CREATE TABLE IF NOT EXISTS "runDiario" (
    "idRunDiario" INTEGER GENERATED ALWAYS AS IDENTITY,
    "idJogo" INTEGER NOT NULL,
    "dataRun" DATE NOT NULL,
    "tempoDuracao" INTERVAL,
    resultado VARCHAR(100),
    "causaMorte" VARCHAR(100),

    PRIMARY KEY ("idRunDiario"),

    FOREIGN KEY ("idJogo")
        REFERENCES jogo("idJogo")
);


CREATE TABLE IF NOT EXISTS "buildAnotacao" (
    "idBuildAnotacao" INTEGER GENERATED ALWAYS AS IDENTITY,
    "idJogo" INTEGER NOT NULL,
    "nomeBuild" VARCHAR(100) NOT NULL,
    "detalheEquipamento" VARCHAR(100),
    habilidades VARCHAR(100),

    PRIMARY KEY ("idBuildAnotacao"),

    FOREIGN KEY ("idJogo")
        REFERENCES jogo("idJogo")
);


select * from jogo;