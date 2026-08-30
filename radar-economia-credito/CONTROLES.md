# Controles internos — radar-economia-credito

Aplicação enxuta do framework COSO (Internal Control – Integrated Framework,
5 componentes) a um projeto pessoal de captação de dados públicos. **Não é**
um controle de nível corporativo/auditoria formal — é uma tradução prática
dos princípios do COSO para o tamanho real deste projeto (um usuário, dados
públicos, sem ambiente de produção compartilhado). Revise este documento
quando a base de dados ou o uso do radar mudar de escopo.

## 1. Ambiente de controle (Control Environment)

Quem é responsável e como o projeto é governado.

| Controle | Como está implementado |
|---|---|
| Responsável único e claro | Natalina Costa é a única dona/operadora do projeto e da base. |
| Trilha de mudanças no código | Todo código versionado em git (`Natalina04/Radar`); histórico de commits é a trilha de auditoria de "quem mudou o quê e quando" na lógica de ingestão. |
| Documentação do propósito e escopo | `README.md` de cada projeto descreve fontes, schema e limites (o que o sistema não faz). |
| Segregação código vs. segredo | Chaves de API (`FRED_API_KEY`) e caminho do banco nunca ficam no código — só em `.env`, fora do controle de versão. |

## 2. Avaliação de riscos (Risk Assessment)

Riscos identificados para este sistema, e por que importam:

| Risco | Impacto se materializar |
|---|---|
| Fonte pública muda formato/código de série sem aviso (ex: Bacen troca o código da Selic) | Ingestão para de capturar aquele indicador silenciosamente, sem erro visível. |
| Valor capturado está corrompido ou é um outlier de fonte (ex: erro de parsing, falha momentânea da API) | Dado errado alimenta o relatório mensal e o painel como se fosse fato. |
| Chave de API (FRED, GitHub) vazada | Uso indevido da chave em nome da conta dela (baixo risco real, mas ainda uma exposição). |
| Perda ou corrupção do arquivo SQLite compartilhado | Perde todo o histórico de sinais capturado, sem como recuperar. |
| Execução manual esquecida (sem rotina) | Base fica desatualizada sem ninguém perceber. |

## 3. Atividades de controle (Control Activities)

Controles concretos implementados para mitigar os riscos acima:

| Controle | Onde está no código | Risco que mitiga |
|---|---|---|
| **Validação de intervalo plausível** — todo valor capturado passa por `validar_valor()` antes de entrar na base; fora do intervalo esperado (`validacao.py`), o sinal é gravado com `status="investigando"` e tag `anomalia`, nunca descartado silenciosamente. | `validacao.py`, usado nos 3 scripts de `ingest/` | Dado corrompido virar "fato" sem revisão |
| **Log de auditoria de execução** — cada rodada de cada fonte grava uma linha em `logs/ingestao.log` (quando rodou, quantos novos, quantas anomalias, quantas falhas). | `logging_utils.py` | Falha silenciosa de fonte passar despercebida |
| **Backup do banco antes de cada rodada** — `backup_db.sh` copia o banco compartilhado para `backups/` com timestamp antes de qualquer ingestão, mantendo os 10 mais recentes. | `backup_db.sh`, chamado por `rodar_tudo.sh` | Perda/corrupção do banco |
| **Dedup automático** — mesma fonte+tipo+resumo nunca duplica (constraint `UNIQUE` no schema). | `storage/schema.sql` | Rodar a ingestão várias vezes inflar a base |
| **Segredos fora do versionamento** — `.env` no `.gitignore`; `.env.example` documenta o que precisa ser preenchido sem expor valores reais. | `.gitignore`, `.env.example` | Vazamento de chave de API |
| **Tratamento de erro por fonte, sem crash** — falha em uma fonte (rede, API fora do ar) não derruba as outras nem interrompe o script. | `try/except` em cada `ingest/*.py` | Uma fonte instável travar a captura inteira |

## 4. Informação e comunicação (Information & Communication)

Como os dados capturados viram informação útil e chegam a quem decide (você mesma):

- **`streamlit_app.py`** — painel visual interativo com métrica + série histórica por indicador; pontos fora do intervalo plausível aparecem destacados (losango vermelho) para revisão manual.
- **`reports/relatorio.py`** — listagem bruta dos sinais mais recentes por módulo/status (visão operacional).
- **`reports/relatorio_mensal.py`** — leitura analítica mês a mês (variação e classificação de tendência por regra simples), pensado para rodar mensalmente e formar uma série de "fotografias" do cenário.

## 5. Atividades de monitoramento (Monitoring Activities)

- Revisar periodicamente `logs/ingestao.log` em busca de `falhas > 0` recorrentes na mesma fonte (sinal de que a API mudou e o código precisa de ajuste).
- Revisar sinais com `status = "investigando"` (anomalias) antes de usar os dados numa análise — eles existem justamente para não virar "fato" sem revisão.
- Reavaliar os limites em `validacao.py` se um indicador legítimo começar a cair fora do intervalo com frequência (limite pode estar errado, não o dado).
- Sugestão: revisar este documento a cada trimestre, ou sempre que uma fonte nova for adicionada.

## Fora de escopo (de propósito, dado o tamanho do projeto)

- Controle de acesso multiusuário / segregação de funções (projeto de uma pessoa só).
- Criptografia do banco em repouso (dado é público, sem informação sensível).
- Alertas automáticos (e-mail/push) em cima do log de auditoria — hoje é revisão manual.
