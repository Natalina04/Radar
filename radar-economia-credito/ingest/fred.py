"""Ingestão de indicadores globais via FRED (Federal Reserve Economic Data).

Requer uma API key gratuita: https://fred.stlouisfed.org/docs/api/api_key.html
Salve em um arquivo .env na raiz do projeto como FRED_API_KEY=xxxxx

Rode com:  python -m ingest.fred
"""

import requests

from config import FRED_API_KEY, HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT
from storage.db import init_db, insert_signal

# ---------------------------------------------------------------------------
# PARÂMETROS — adicione/remova séries do FRED aqui.
# Busque códigos em https://fred.stlouisfed.org/
# ---------------------------------------------------------------------------
SERIES = {
    "fed_funds_rate": {
        "id": "FEDFUNDS",
        "descricao": "Fed Funds Effective Rate (% a.a.)",
    },
    "us_cpi": {
        "id": "CPIAUCSL",
        "descricao": "US CPI - All Urban Consumers (índice, não sazonalizado)",
    },
}

QTD_ULTIMAS_OBSERVACOES = 3

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
# ---------------------------------------------------------------------------


def buscar_serie(series_id, qtd=QTD_ULTIMAS_OBSERVACOES):
    resposta = requests.get(
        BASE_URL,
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": qtd,
        },
        headers={"User-Agent": HTTP_USER_AGENT},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resposta.raise_for_status()
    return resposta.json().get("observations", [])


def ingerir_series():
    if not FRED_API_KEY:
        print("[fred] FRED_API_KEY não configurada — defina no .env. Abortando.")
        return

    init_db()
    total_novos = 0

    for chave, meta in SERIES.items():
        try:
            observacoes = buscar_serie(meta["id"])
        except requests.RequestException as erro:
            print(f"[fred] falha ao buscar {chave} ({meta['id']}): {erro}")
            continue

        for obs in observacoes:
            if obs.get("value") == ".":  # FRED usa "." para valor ausente
                continue
            resumo = f"{meta['descricao']} em {obs['date']}: {obs['value']}"
            inserido = insert_signal(
                fonte=f"FRED - {meta['id']} ({chave})",
                modulo="economia_credito",
                tipo="macro_global",
                resumo=resumo,
                evidencias=f"https://fred.stlouisfed.org/series/{meta['id']}",
                tags=f"fred,{chave}",
            )
            if inserido:
                total_novos += 1
                print(f"[fred] novo: {resumo}")

    print(f"[fred] concluído — {total_novos} sinal(is) novo(s) inserido(s).")


if __name__ == "__main__":
    ingerir_series()
