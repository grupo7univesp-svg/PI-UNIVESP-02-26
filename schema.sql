CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS producoes (
    id BIGSERIAL PRIMARY KEY,
    relatorio_id UUID NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    data_producao DATE NOT NULL,
    etapa VARCHAR(30) NOT NULL,
    produto VARCHAR(120) NOT NULL,
    observacao TEXT DEFAULT '',
    genero VARCHAR(20) NOT NULL,
    quantidade_p INTEGER NOT NULL DEFAULT 0,
    quantidade_m INTEGER NOT NULL DEFAULT 0,
    quantidade_g INTEGER NOT NULL DEFAULT 0,
    quantidade_gg INTEGER NOT NULL DEFAULT 0,
    quantidade_xg INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_producoes_usuario_data ON producoes(usuario_id, data_producao);
CREATE INDEX IF NOT EXISTS idx_producoes_relatorio ON producoes(relatorio_id);

INSERT INTO usuarios (id, nome, ativo)
VALUES (1, 'Administrador', TRUE)
ON CONFLICT (id) DO NOTHING;
