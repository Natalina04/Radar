-- Base de conhecimento compartilhada entre os dois módulos do Radar.
-- Um único "sinal" pode vir do módulo de economia/crédito (indicadores,
-- mercado, regulatório) ou do módulo de remanufatura digital (candidatos
-- a incorporação encontrados em repositórios abertos).

CREATE TABLE IF NOT EXISTS sinais (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    data_captura     TEXT    NOT NULL,  -- ISO 8601, momento em que o sinal foi salvo
    fonte            TEXT    NOT NULL,  -- nome + URL/API de origem
    modulo           TEXT    NOT NULL CHECK (modulo IN ('economia_credito', 'remanufatura_digital')),
    tipo             TEXT    NOT NULL CHECK (tipo IN (
                         'macro_brasil', 'macro_global', 'mercado_curto_prazo',
                         'credito', 'regulatorio', 'tecnologia'
                     )),
    resumo           TEXT,              -- descrição curta do sinal (indicador+data+valor, ou repo+descrição)
    por_que_importa  TEXT,              -- texto livre, preenchido manualmente na revisão
    status           TEXT    NOT NULL DEFAULT 'novo' CHECK (status IN (
                         'novo', 'investigando', 'testado', 'validado', 'descartado'
                     )),
    evidencias       TEXT,              -- link para dado bruto/notebook/teste/repositório
    decisao          TEXT,              -- o que foi feito com essa informação
    licenca          TEXT,              -- só se aplica a remanufatura_digital (MIT/Apache-2.0/etc ou NULL)
    tags             TEXT,              -- lista separada por vírgula

    -- evita duplicar o mesmo sinal a cada nova rodada de ingestão
    UNIQUE (fonte, tipo, resumo)
);

CREATE INDEX IF NOT EXISTS idx_sinais_modulo_status ON sinais (modulo, status);
CREATE INDEX IF NOT EXISTS idx_sinais_data_captura ON sinais (data_captura);
