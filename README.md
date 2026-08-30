# Radar — Economia/Crédito + Fábrica de Remanufatura Digital

Parte do ecossistema Torre (hub de conhecimento que conecta dados, decisões e
descobertas). Este projeto tem dois módulos com pipelines de ingestão
diferentes, compartilhando a mesma base de conhecimento (`sinais`):

- **economia_credito** — indicadores macro do Brasil e globais, oscilações de
  curto prazo (mercado/volatilidade), crédito e regulatório.
- **remanufatura_digital** — radar tecnológico que busca em repositórios
  abertos projetos com stack/abordagem parecida com os meus, e registra
  candidatos a incorporação para eu revisar (nunca copia código automático).

## Estrutura

```
config.py                 # config compartilhada (caminhos, chaves de API via .env)
storage/
  schema.sql               # DDL da tabela "sinais"
  db.py                    # init_db, insert_signal, get_recent_signals, ...
ingest_economia/
  bacen_sgs.py              # Selic, IPCA, câmbio — Bacen SGS (sem chave)
  fred.py                   # Fed funds rate, US CPI — FRED (requer API key)
  mercado.py                # Ibovespa, S&P500, VIX — yfinance (diário)
ingest_remanufatura/
  github_scan.py            # busca GitHub por topic/linguagem + filtro de licença
processing/                 # reservado para normalização/dedup futuros
reports/
  relatorio.py               # lista sinais recentes por módulo/status
data/
  radar.db                   # criado automaticamente (não versionado)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha FRED_API_KEY (e opcionalmente GITHUB_TOKEN)
```

## Uso

```bash
# inicializa o banco (as ingestões também fazem isso sozinhas)
python -m storage.db

# módulo economia/crédito
python -m ingest_economia.bacen_sgs
python -m ingest_economia.fred
python -m ingest_economia.mercado

# módulo remanufatura digital
python -m ingest_remanufatura.github_scan

# relatório
python -m reports.relatorio
python -m reports.relatorio --markdown --saida relatorio.md
python -m reports.relatorio --modulo economia_credito --limite 10
```

## Schema — tabela `sinais`

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
| `licenca` | só para remanufatura_digital (MIT/Apache-2.0/etc, ou N/A) |
| `tags` | lista separada por vírgula |

Duplicatas (mesma `fonte` + `tipo` + `resumo`) são ignoradas na inserção, então
rodar os scripts de ingestão repetidamente é seguro.

## Regras de licença (módulo remanufatura)

Busca filtra por linguagem/tópico dos meus projetos atuais (lista editável no
topo de `ingest_remanufatura/github_scan.py`) e classifica a licença de cada
repositório encontrado. Licenças permissivas aceitas sem aviso: MIT,
Apache-2.0, BSD-2-Clause, BSD-3-Clause. Qualquer outra licença (ou ausência de
licença) é registrada mesmo assim, mas com aviso `[ATENÇÃO: licença
restritiva/ausente]` no resumo — nunca é descartada silenciosamente, para que
a revisão manual decida.

**Nada aqui copia código automaticamente.** Cada achado vira uma linha
`status = novo` na tabela `sinais`; a decisão de investigar, testar ou adaptar
é sempre manual.

## O que ainda não existe (de propósito)

- Sem dashboard visual.
- Sem classificação/resumo automático por LLM.
- Sem deploy — roda local.
- Bacen SCR (crédito/inadimplência) e fontes regulatórias (Open Finance)
  ainda não têm ingestão própria — os tipos `credito` e `regulatorio` já
  existem no schema, prontos para quando essas fontes forem adicionadas.
