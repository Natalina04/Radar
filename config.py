"""Configuração compartilhada do Radar (economia/crédito + remanufatura digital).

Carrega variáveis de ambiente de um arquivo .env (se existir) e expõe caminhos
e parâmetros usados por mais de um módulo. Parâmetros específicos de cada
fonte de dados ficam no topo do próprio script de ingestão.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "radar.db"

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HTTP_TIMEOUT_SECONDS = 30
HTTP_USER_AGENT = "radar-economia-remanufatura/0.1 (uso pessoal)"
