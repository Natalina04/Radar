"""Ingestão de indicadores do Bacen SGS (Sistema Gerenciador de Séries Temporais).

API pública, sem chave: https://api.bcb.gov.br/dados/serie/bcdata.sgs.<codigo>/dados

Rode com:  python -m ingest.bacen_sgs
"""

from datetime import datetime

import requests

from config import HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT
from logging_utils import registrar_execucao
from storage.db import init_db, insert_signal
from storage.tags import montar_tags
from validacao import validar_valor

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
    total_anomalias = 0
    total_falhas = 0

    for chave, meta in SERIES.items():
        try:
            pontos = buscar_serie(meta["codigo"])
        except requests.RequestException as erro:
            print(f"[bacen_sgs] falha ao buscar {chave} (código {meta['codigo']}): {erro}")
            total_falhas += 1
            continue

        for ponto in pontos:
            data_iso = datetime.strptime(ponto["data"], "%d/%m/%Y").date().isoformat()
            valor = float(ponto["valor"])
            valido = validar_valor(chave, valor)

            resumo = f"{meta['descricao']} em {ponto['data']}: {ponto['valor']}"
            if not valido:
                resumo += " [ATENÇÃO: fora do intervalo plausível — revisar]"
                print(f"[bacen_sgs] anomalia: {resumo}")
                total_anomalias += 1

            tags = montar_tags(
                "bacen", "sgs", chave, *(["anomalia"] if not valido else []),
                data_ref=data_iso, valor=ponto["valor"],
            )
            inserido = insert_signal(
                fonte=f"Bacen SGS - série {meta['codigo']} ({chave})",
                modulo="economia_credito",
                tipo="macro_brasil",
                resumo=resumo,
                status="novo" if valido else "investigando",
                evidencias=BASE_URL.format(codigo=meta["codigo"], qtd=QTD_ULTIMOS_VALORES),
                tags=tags,
            )
            if inserido:
                total_novos += 1
                if valido:
                    print(f"[bacen_sgs] novo: {resumo}")

    print(f"[bacen_sgs] concluído — {total_novos} sinal(is) novo(s) inserido(s) "
          f"({total_anomalias} anomalia(s), {total_falhas} falha(s) de busca).")
    registrar_execucao("bacen_sgs", total_novos, total_falhas, total_anomalias)


if __name__ == "__main__":
    ingerir_series()
