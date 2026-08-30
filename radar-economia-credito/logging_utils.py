"""Log de execução das ingestões — trilha de auditoria (COSO: Control
Activities / Monitoring). Cada rodada de cada fonte grava uma linha em
logs/ingestao.log com quando rodou, quantos sinais novos e quantas falhas.

Não substitui os prints no console (que continuam existindo) — é um
registro persistente para auditoria/monitoramento posterior, já que o
console some quando o terminal fecha.
"""

from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_PATH = LOG_DIR / "ingestao.log"


def registrar_execucao(fonte, novos, falhas, anomalias=0):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    momento = datetime.now(timezone.utc).isoformat(timespec="seconds")
    linha = f"{momento} | {fonte} | novos={novos} | anomalias={anomalias} | falhas={falhas}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(linha)
