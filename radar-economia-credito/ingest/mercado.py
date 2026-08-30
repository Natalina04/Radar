"""Ingestão de oscilações de curto prazo (mercado de ações, volatilidade)
via yfinance. Dados diários (fechamento), não intradiário.

Rode com:  python -m ingest.mercado
"""

import yfinance as yf

from storage.db import init_db, insert_signal

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

    for chave, meta in TICKERS.items():
        try:
            fechamentos = buscar_fechamentos(meta["symbol"])
        except Exception as erro:  # yfinance não expõe uma exceção específica estável
            print(f"[mercado] falha ao buscar {chave} ({meta['symbol']}): {erro}")
            continue

        for data_pregao, valor in fechamentos.items():
            resumo = f"{meta['descricao']} em {data_pregao.date()}: {valor:.2f}"
            inserido = insert_signal(
                fonte=f"Yahoo Finance - {meta['symbol']} ({chave})",
                modulo="economia_credito",
                tipo="mercado_curto_prazo",
                resumo=resumo,
                evidencias=f"https://finance.yahoo.com/quote/{meta['symbol']}",
                tags=f"yfinance,{chave}",
            )
            if inserido:
                total_novos += 1
                print(f"[mercado] novo: {resumo}")

    print(f"[mercado] concluído — {total_novos} sinal(is) novo(s) inserido(s).")


if __name__ == "__main__":
    ingerir_series()
