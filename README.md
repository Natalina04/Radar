# Radar

Dois projetos independentes que compartilham apenas o conceito de base de
conhecimento (tabela `sinais`, no mesmo arquivo SQLite) — parte do
ecossistema Torre.

- **[`radar-economia-credito/`](radar-economia-credito/)** — indicadores
  macro do Brasil e globais, oscilações de curto prazo (mercado/volatilidade),
  e futuramente crédito e regulatório. Fontes: Bacen SGS, FRED, yfinance.
- **[`xbrain/`](xbrain/)** — fábrica de remanufatura digital: radar
  tecnológico que busca repositórios abertos no GitHub, filtra por licença
  permissiva e registra candidatos a incorporação para revisão manual
  (nunca copia código automaticamente).

Cada projeto tem seu próprio `requirements.txt`, `config.py` e scripts de
execução — um não depende do outro para rodar. Veja o README de cada pasta
para setup e uso. Por padrão os dois escrevem no mesmo banco
(`~/.radar/radar.db`), configurável via `RADAR_DB_PATH` em cada `.env`.
