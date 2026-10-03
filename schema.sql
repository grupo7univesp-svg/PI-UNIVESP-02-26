CREATE TABLE IF NOT EXISTS usuarios (

    id BIGSERIAL PRIMARY KEY,

    nome VARCHAR(120) NOT NULL,

    usuario VARCHAR(120) UNIQUE NOT NULL,

    senha_hash VARCHAR(255) NOT NULL,

    tipo VARCHAR(20) NOT NULL DEFAULT 'func',

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    pode_corte BOOLEAN NOT NULL DEFAULT FALSE,

    pode_costura BOOLEAN NOT NULL DEFAULT FALSE,

    pode_colagem BOOLEAN NOT NULL DEFAULT FALSE,

    valor_corte NUMERIC(10,2) NOT NULL DEFAULT 0,

    valor_costura NUMERIC(10,2) NOT NULL DEFAULT 0,

    valor_colagem NUMERIC(10,2) NOT NULL DEFAULT 0

);


CREATE TABLE IF NOT EXISTS producoes (

    id BIGSERIAL PRIMARY KEY,

    relatorio_id UUID NOT NULL,

    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),

    data_producao DATE NOT NULL,

    quantidade_p INTEGER NOT NULL DEFAULT 0,

    quantidade_m INTEGER NOT NULL DEFAULT 0,

    quantidade_g INTEGER NOT NULL DEFAULT 0,

    quantidade_gg INTEGER NOT NULL DEFAULT 0,

    quantidade_xg INTEGER NOT NULL DEFAULT 0

    criado_em TIMESTAMP NOT NULL DEFAULT NOW()

);


CREATE INDEX IF NOT EXISTS idx_producoes_usuario_data
ON producoes(usuario_id, data_producao);


CREATE INDEX IF NOT EXISTS idx_producoes_relatorio
ON producoes(relatorio_id);