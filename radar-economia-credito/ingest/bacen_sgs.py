"""Ingestão de indicadores do Bacen SGS (Sistema Gerenciador de Séries Temporais).

API pública, sem chave: https://api.bcb.gov.br/dados/serie/bcdata.sgs.<codigo>/dados

Rode com:  python -m ingest.bacen_sgs
"""

import requests

from config import HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT
from storage.db import init_db, insert_signal

# ---------------------------------------------------------------------------
# PARÂMETROS — ajuste aqui os códigos de série e a janela de datas.
# Consulte/confirme códigos em https://www3.bcb.gov.br/sgspub
# ---------------------------------------------------------------------------
SERIES = {
    "selic_meta": {
        "codigo": 432,
        "descricao": "Meta Selic definida pelo Copom (% a.a.)",
    },
    "ipca_mensal": {
        "codigo": 433,
        "descricao": "IPCA - variação mensal (%)",
    },
    "cambio_usd_venda": {
        "codigo": 1,
        "descricao": "Taxa de câmbio - dólar americano, venda, diária (R$)",
    },
}

# Quantos últimos valores buscar por série (a API do Bacen também aceita
# datas explícitas via dataInicial/dataFinal, se preferir uma janela fixa).
QTD_ULTIMOS_VALORES = 5

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{qtd}"
# ---------------------------------------------------------------------------


def buscar_serie(codigo, qtd=QTD_ULTIMOS_VALORES):
    url = BASE_URL.format(codigo=codigo, qtd=qtd)
    resposta = requests.get(
        url,
        params={"formato": "json"},
        headers={"User-Agent": HTTP_USER_AGENT},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resposta.raise_for_status()
    return resposta.json()  # lista de {"data": "DD/MM/AAAA", "valor": "12.34"}


def ingerir_series():
    init_db()
    total_novos = 0

    for chave, meta in SERIES.items():
        try:
            pontos = buscar_serie(meta["codigo"])
        except requests.RequestException as erro:
            print(f"[bacen_sgs] falha ao buscar {chave} (código {meta['codigo']}): {erro}")
            continue

        for ponto in pontos:
            resumo = f"{meta['descricao']} em {ponto['data']}: {ponto['valor']}"
            inserido = insert_signal(
                fonte=f"Bacen SGS - série {meta['codigo']} ({chave})",
                modulo="economia_credito",
                tipo="macro_brasil",
                resumo=resumo,
                evidencias=BASE_URL.format(codigo=meta["codigo"], qtd=QTD_ULTIMOS_VALORES),
                tags=f"bacen,sgs,{chave}",
            )
            if inserido:
                total_novos += 1
                print(f"[bacen_sgs] novo: {resumo}")

    print(f"[bacen_sgs] concluído — {total_novos} sinal(is) novo(s) inserido(s).")


if __name__ == "__main__":
    ingerir_series()
