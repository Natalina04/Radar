# radar-economia-credito

Projeto independente de radar tecnológico-econômico: indicadores macro do
Brasil e globais, oscilações de curto prazo (mercado/volatilidade) e
(futuramente) crédito e regulatório. Parte do ecossistema Torre.

Compartilha com o projeto irmão `xbrain` (fábrica de remanufatura digital)
apenas o conceito de base de conhecimento — a tabela `sinais`, no mesmo
arquivo SQLite (`RADAR_DB_PATH`, ver Setup). Fora isso, os dois projetos são
totalmente independentes: ambientes, dependências e ritmo de evolução
separados.

## Estrutura

```
config.py             # config (RADAR_DB_PATH compartilhado, FRED_API_KEY)
storage/
  schema.sql            # DDL da tabela "sinais"
  db.py                 # init_db, insert_signal, get_recent_signals, ...
ingest/
  bacen_sgs.py           # Selic, IPCA, câmbio — Bacen SGS (sem chave)
  fred.py                # Fed funds rate, US CPI — FRED (requer API key)
  mercado.py             # Ibovespa, S&P500, VIX — yfinance (diário)
reports/
  relatorio.py            # lista sinais recentes por módulo/status
```

## Setup rápido (Posit Cloud ou local)

```bash
cd radar-economia-credito
./rodar_tudo.sh
```

Isso cria o `.venv`, instala as dependências, copia `.env.example` para
`.env` na primeira vez (preencha `FRED_API_KEY` depois), roda as três
ingestões e gera `relatorio_AAAA-MM-DD.md`. Rode de novo sempre que quiser
atualizar os dados — duplicatas são ignoradas automaticamente.

## Setup manual

```bash
cd radar-economia-credito
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha FRED_API_KEY
```

## Uso

Rode sempre a partir desta pasta (`radar-economia-credito/`):

```bash
# inicializa o banco (as ingestões também fazem isso sozinhas)
python -m storage.db

python -m ingest.bacen_sgs
python -m ingest.fred
python -m ingest.mercado

python -m reports.relatorio
python -m reports.relatorio --markdown --saida relatorio.md
python -m reports.relatorio --modulo economia_credito --limite 10
```

## Schema — tabela `sinais`

Idêntico ao usado pelo projeto `xbrain` (mesmo arquivo, mesma tabela):

| campo | descrição |
|---|---|
| `id` | chave primária |
| `data_captura` | quando o sinal foi salvo (ISO 8601, UTC) |
| `fonte` | nome + URL/API de origem |
| `modulo` | `economia_credito` \| `remanufatura_digital` |
| `tipo` | `macro_brasil` \| `macro_global` \| `mercado_curto_prazo` \| `credito` \| `regulatorio` \| `tecnologia` |
| `resumo` | descrição curta do sinal |
| `por_que_importa` | texto livre, preenchido na revisão manual |
| `status` | `novo` \| `investigando` \| `testado` \| `validado` \| `descartado` |
| `evidencias` | link para o dado bruto/notebook/teste/repositório |
| `decisao` | o que foi feito com essa informação |
| `licenca` | só usado por sinais do xbrain (MIT/Apache-2.0/etc); aqui sempre `NULL` |
| `tags` | lista separada por vírgula |

Este projeto sempre grava `modulo = "economia_credito"`. Duplicatas (mesma
`fonte` + `tipo` + `resumo`) são ignoradas na inserção, então rodar os
scripts de ingestão repetidamente é seguro.

## Banco compartilhado

Por padrão, o banco fica em `~/.radar/radar.db` — o mesmo default usado pelo
projeto `xbrain`, então os dois já compartilham a base sem nenhuma
configuração extra. Se quiser um caminho diferente, defina `RADAR_DB_PATH`
no `.env` **dos dois projetos**, apontando para o mesmo arquivo.

## O que ainda não existe (de propósito)

- Sem dashboard visual.
- Sem classificação/resumo automático por LLM.
- Sem deploy — roda local.
- Bacen SCR (crédito/inadimplência) e fontes regulatórias (Open Finance)
  ainda não têm ingestão própria — os tipos `credito` e `regulatorio` já
  existem no schema, prontos para quando essas fontes forem adicionadas.
