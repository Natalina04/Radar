"""Configuração do projeto radar-economia-credito.

Projeto independente — não importa nada de xbrain.
A única coisa que os dois projetos compartilham é o arquivo SQLite da base de
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

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

HTTP_TIMEOUT_SECONDS = 30
HTTP_USER_AGENT = "radar-economia-credito/0.1 (uso pessoal)"
