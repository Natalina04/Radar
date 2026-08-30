# xbrain

Fábrica de remanufatura digital: radar tecnológico que busca em
repositórios abertos do GitHub projetos com stack/abordagem parecida com os
meus, filtra por licença permissiva e registra candidatos a incorporação
para eu revisar manualmente. Parte do ecossistema Torre.

Compartilha com o projeto irmão `radar-economia-credito` apenas o conceito
de base de conhecimento — a tabela `sinais`, no mesmo arquivo SQLite
(`RADAR_DB_PATH`, ver Setup). Fora isso, os dois projetos são totalmente
independentes: ambientes, dependências e ritmo de evolução separados.

**Nada aqui copia código automaticamente.** Cada achado vira uma linha
`status = novo` na tabela `sinais`; a decisão de investigar, testar ou
adaptar é sempre manual.

## Estrutura

```
config.py             # config (RADAR_DB_PATH compartilhado, GITHUB_TOKEN)
storage/
  schema.sql            # DDL da tabela "sinais" (idêntico ao radar-economia-credito)
  db.py                 # init_db, insert_signal, get_recent_signals, ...
ingest/
  github_scan.py         # busca GitHub por topic/linguagem + filtro de licença
reports/
  relatorio.py            # lista sinais recentes por módulo/status
```

## Setup

```bash
cd xbrain
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # GITHUB_TOKEN é opcional (aumenta o rate limit de busca)
```

## Uso

Rode sempre a partir desta pasta (`xbrain/`):

```bash
# inicializa o banco (a ingestão também faz isso sozinha)
python -m storage.db

python -m ingest.github_scan

python -m reports.relatorio
python -m reports.relatorio --markdown --saida relatorio.md
python -m reports.relatorio --modulo remanufatura_digital --limite 10
```

Edite a lista `MEUS_PROJETOS` no topo de `ingest/github_scan.py` com seus
projetos reais (linguagem, tópicos, problema que resolvem) — é isso que
gera as buscas no GitHub.

## Regras de licença

Licenças permissivas aceitas sem aviso: MIT, Apache-2.0, BSD-2-Clause,
BSD-3-Clause. Qualquer outra licença (ou ausência de licença) é registrada
mesmo assim, mas com aviso `[ATENÇÃO: licença restritiva/ausente]` no
resumo — nunca é descartada silenciosamente, para que a revisão manual
decida.

## Schema — tabela `sinais`

Idêntico ao usado pelo projeto `radar-economia-credito` (mesmo arquivo,
mesma tabela):

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
| `licenca` | MIT/Apache-2.0/etc, ou aviso de licença restritiva/ausente |
| `tags` | lista separada por vírgula |

Este projeto sempre grava `modulo = "remanufatura_digital"` e `tipo =
"tecnologia"`. Duplicatas (mesma `fonte` + `tipo` + `resumo`) são ignoradas
na inserção, então rodar a busca repetidamente é seguro.

## Banco compartilhado

Por padrão, o banco fica em `~/.radar/radar.db` — o mesmo default usado pelo
projeto `radar-economia-credito`, então os dois já compartilham a base sem
nenhuma configuração extra. Se quiser um caminho diferente, defina
`RADAR_DB_PATH` no `.env` **dos dois projetos**, apontando para o mesmo
arquivo.

## O que ainda não existe (de propósito)

- Sem dashboard visual.
- Sem classificação/resumo automático por LLM.
- Sem deploy — roda local.
- Hugging Face / Papers with Code como fontes adicionais de busca (cogitado
  para depois, se fizer sentido para os projetos).
