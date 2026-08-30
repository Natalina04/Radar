"""Configuração do projeto xbrain (fábrica de remanufatura digital).

Projeto independente — não importa nada de radar-economia-credito. A única
coisa que os dois projetos compartilham é o arquivo SQLite da base de
conhecimento (tabela "sinais"), apontado por RADAR_DB_PATH.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Caminho do banco compartilhado entre radar-economia-credito e xbrain.
# Mesma variável de ambiente (RADAR_DB_PATH) deve ser configurada nos dois
# projetos, apontando para o mesmo arquivo. Sem ela, os dois caem no mesmo
# default (~/.radar/radar.db), então já funciona compartilhado sem nada
# configurar.
DB_PATH = Path(os.getenv("RADAR_DB_PATH", str(Path.home() / ".radar" / "radar.db")))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HTTP_TIMEOUT_SECONDS = 30
HTTP_USER_AGENT = "xbrain/0.1 (uso pessoal)"
