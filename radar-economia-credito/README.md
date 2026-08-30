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
validacao.py           # intervalo plausível por indicador (controle de dado)
logging_utils.py       # log de auditoria de execução (logs/ingestao.log)
backup_db.sh           # backup do banco antes de cada rodada (backups/)
analise.py             # classificação de tendência + frases de leitura (sem LLM)
streamlit_app.py       # painel visual interativo (boletim de cenário)
CONTROLES.md           # controles internos do projeto, mapeados ao COSO
storage/
  schema.sql            # DDL da tabela "sinais"
  db.py                  # init_db, insert_signal, get_recent_signals, ...
  tags.py                # empacota/lê data_ref e valor no campo tags
ingest/
  bacen_sgs.py           # Selic, IPCA, câmbio — Bacen SGS (sem chave)
  fred.py                # Fed funds rate, US CPI — FRED (requer API key)
  mercado.py             # Ibovespa, S&P500, VIX — yfinance (diário)
reports/
  relatorio.py            # lista sinais recentes por módulo/status
  relatorio_mensal.py      # leitura analítica mês a mês (regra simples)
```

## Setup rápido (Posit Cloud ou local)

```bash
cd radar-economia-credito
./rodar_tudo.sh
```

**Se você já tinha sinais capturados antes do painel/relatório mensal
existirem** (tags no formato antigo, sem `data_ref`/`valor`), rode uma vez,
depois de atualizar o código (`git pull`):

```bash
source .venv/bin/activate   # ou deixe o rodar_tudo.sh criar o venv primeiro
python migrar_tags.py
```

Isso preenche `data_ref`/`valor` nos sinais antigos a partir do `resumo` já
salvo — nada é apagado, e rodar de novo não duplica nem tem efeito (é
seguro repetir). Sem isso, esses sinais não aparecem no painel nem no
relatório mensal (mas continuam intactos na base).

Isso faz backup do banco, cria o `.venv`, instala as dependências, copia
`.env.example` para `.env` na primeira vez (preencha `FRED_API_KEY`
depois), roda as três ingestões e gera `relatorio_AAAA-MM-DD.md`. Rode de
novo sempre que quiser atualizar os dados — duplicatas são ignoradas
automaticamente. Depois, abra o painel visual (ver seção abaixo).

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

# painel visual interativo (abre um servidor local)
streamlit run streamlit_app.py

# relatório operacional (lista bruta)
python -m reports.relatorio
python -m reports.relatorio --markdown --saida relatorio.md
python -m reports.relatorio --modulo economia_credito --limite 10

# relatório analítico mensal (rode ~1x por mês)
python -m reports.relatorio_mensal
```

## Painel visual

`streamlit_app.py` é um boletim de cenário interativo, não uma lista de
gráficos soltos: resumo executivo em prosa (leitura do cenário por seção),
depois abas Brasil / Global / Mercado / Regulatório, cada indicador com
métrica + variação + gráfico de série histórica + uma frase de leitura.
Pontos fora do intervalo plausível (ver Controles internos, abaixo)
aparecem como losango vermelho no gráfico e um aviso no texto — nunca
escondidos. A seção Regulatório mostra a contagem de normas capturadas
(`tipo = "regulatorio"`) com link direto para cada uma — hoje ainda vazia
por padrão, porque este projeto não tem (ainda) uma fonte de ingestão de
normativos (Bacen/CMN/Open Finance); o placeholder deixa isso explícito em
vez de esconder a lacuna.

```bash
streamlit run streamlit_app.py
```

**No Posit Cloud**: depois de rodar o comando acima no Terminal, uma
notificação/botão **"Open in Browser"** aparece no canto da aba do
Terminal — clique nele para abrir o painel numa nova aba. Se não aparecer,
acesse pela URL do projeto trocando a porta pela que o Streamlit imprimiu
(normalmente 8501). O processo fica rodando enquanto a sessão estiver
aberta — para encerrar, `Ctrl+C` no Terminal.

## Relatório mensal analítico

`reports/relatorio_mensal.py` compara o mês de referência mais recente com
o mês anterior, indicador a indicador, e classifica a variação (estável /
em alta / em queda) por um limiar fixo — é uma leitura de regra simples,
não uma análise qualitativa gerada por IA. Gera
`relatorio_mensal_AAAA-MM.md`. Não há agendamento automático (o projeto não
faz deploy) — rode manualmente todo início de mês, ou quando quiser
reavaliar o cenário.

## Controles internos

Este projeto aplica um conjunto enxuto de controles alinhados ao framework
COSO (Control Environment, Risk Assessment, Control Activities, Information
& Communication, Monitoring) — ver **[`CONTROLES.md`](CONTROLES.md)** para o
detalhamento completo. Resumo do que está implementado:

- **Validação de intervalo plausível** (`validacao.py`) antes de cada
  inserção — valor fora do esperado nunca é descartado, mas entra com
  `status = "investigando"` e tag `anomalia`, sinalizado no painel.
- **Log de auditoria** (`logs/ingestao.log`) de cada rodada de cada fonte.
- **Backup automático do banco** (`backup_db.sh`) antes de cada ingestão,
  mantendo os 10 backups mais recentes.
- **Segredos nunca versionados** (`.env` no `.gitignore`).
- **Erro isolado por fonte** — uma fonte fora do ar não derruba as outras.

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
| `status` | `novo` \| `investigando` \| `testado` \| `validado` \| `descartado` — `investigando` também marca anomalia de validação |
| `evidencias` | link para o dado bruto/notebook/teste/repositório |
| `decisao` | o que foi feito com essa informação |
| `licenca` | só usado por sinais do xbrain (MIT/Apache-2.0/etc); aqui sempre `NULL` |
| `tags` | rótulos livres + pares `chave=valor` (`data_ref`, `valor`, opcionalmente `anomalia`) — ver `storage/tags.py` |

Este projeto sempre grava `modulo = "economia_credito"`. Duplicatas (mesma
`fonte` + `tipo` + `resumo`) são ignoradas na inserção, então rodar os
scripts de ingestão repetidamente é seguro.

## Banco compartilhado

Por padrão, o banco fica em `~/.radar/radar.db` — o mesmo default usado pelo
projeto `xbrain`, então os dois já compartilham a base sem nenhuma
configuração extra. Se quiser um caminho diferente, defina `RADAR_DB_PATH`
no `.env` **dos dois projetos**, apontando para o mesmo arquivo.

## O que ainda não existe (de propósito)

- Sem classificação/resumo automático por LLM no relatório mensal (é regra
  simples, ver acima) — pode virar uma evolução futura, se fizer sentido.
- Sem deploy nem agendamento automático — roda local, sob demanda.
- Bacen SCR (crédito/inadimplência) e fontes regulatórias (Open Finance)
  ainda não têm ingestão própria — os tipos `credito` e `regulatorio` já
  existem no schema, prontos para quando essas fontes forem adicionadas.
