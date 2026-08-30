"""Ingestão de oscilações de curto prazo (mercado de ações, volatilidade)
via yfinance. Dados diários (fechamento), não intradiário.

Rode com:  python -m ingest.mercado
"""

import yfinance as yf

from logging_utils import registrar_execucao
from storage.db import init_db, insert_signal
from storage.tags import montar_tags
from validacao import validar_valor

# ---------------------------------------------------------------------------
# PARÂMETROS — tickers do Yahoo Finance a acompanhar.
# ---------------------------------------------------------------------------
TICKERS = {
    "ibovespa": {"symbol": "^BVSP", "descricao": "Ibovespa (fechamento)"},
    "sp500": {"symbol": "^GSPC", "descricao": "S&P 500 (fechamento)"},
    "vix": {"symbol": "^VIX", "descricao": "VIX - índice de volatilidade (fechamento)"},
}

QTD_ULTIMOS_DIAS_UTEIS = "5d"
# ---------------------------------------------------------------------------


def buscar_fechamentos(symbol, periodo=QTD_ULTIMOS_DIAS_UTEIS):
    historico = yf.Ticker(symbol).history(period=periodo, interval="1d")
    return historico["Close"].dropna()


def ingerir_series():
    init_db()
    total_novos = 0
    total_anomalias = 0
    total_falhas = 0

    for chave, meta in TICKERS.items():
        try:
            fechamentos = buscar_fechamentos(meta["symbol"])
        except Exception as erro:  # yfinance não expõe uma exceção específica estável
            print(f"[mercado] falha ao buscar {chave} ({meta['symbol']}): {erro}")
            total_falhas += 1
            continue

        for data_pregao, valor in fechamentos.items():
            valor = float(valor)
            valido = validar_valor(chave, valor)
            data_iso = str(data_pregao.date())

            resumo = f"{meta['descricao']} em {data_iso}: {valor:.2f}"
            if not valido:
                resumo += " [ATENÇÃO: fora do intervalo plausível — revisar]"
                print(f"[mercado] anomalia: {resumo}")
                total_anomalias += 1

            tags = montar_tags(
                "yfinance", chave, *(["anomalia"] if not valido else []),
                data_ref=data_iso, valor=f"{valor:.2f}",
            )
            inserido = insert_signal(
                fonte=f"Yahoo Finance - {meta['symbol']} ({chave})",
                modulo="economia_credito",
                tipo="mercado_curto_prazo",
                resumo=resumo,
                status="novo" if valido else "investigando",
                evidencias=f"https://finance.yahoo.com/quote/{meta['symbol']}",
                tags=tags,
            )
            if inserido:
                total_novos += 1
                if valido:
                    print(f"[mercado] novo: {resumo}")

    print(f"[mercado] concluído — {total_novos} sinal(is) novo(s) inserido(s) "
          f"({total_anomalias} anomalia(s), {total_falhas} falha(s) de busca).")
    registrar_execucao("mercado", total_novos, total_falhas, total_anomalias)


if __name__ == "__main__":
    ingerir_series()
