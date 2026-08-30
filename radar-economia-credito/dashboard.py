"""Painel visual dos indicadores do radar-economia-credito.

Gera um único arquivo HTML autocontido (sem servidor, sem deploy) a partir
dos dados já capturados na base compartilhada. Abra o arquivo gerado no
navegador (ou no Viewer do Posit Cloud).

Rode com:  python dashboard.py
"""

import plotly.graph_objects as go

from storage.db import get_recent_signals
from storage.tags import parse_tags

# ---------------------------------------------------------------------------
# PARÂMETROS
# ---------------------------------------------------------------------------
SAIDA_HTML = "dashboard.html"

# chave (bate com a tag gravada pelos scripts de ingest) -> metadados de exibição
INDICADORES = {
    "selic_meta": {"titulo": "Selic (meta)", "unidade": "% a.a.", "secao": "Brasil"},
    "ipca_mensal": {"titulo": "IPCA (mensal)", "unidade": "%", "secao": "Brasil"},
    "cambio_usd_venda": {"titulo": "Câmbio USD/BRL (venda)", "unidade": "R$", "secao": "Brasil"},
    "fed_funds_rate": {"titulo": "Fed Funds Rate", "unidade": "% a.a.", "secao": "Global"},
    "us_cpi": {"titulo": "US CPI", "unidade": "índice", "secao": "Global"},
    "ibovespa": {"titulo": "Ibovespa", "unidade": "pontos", "secao": "Mercado (curto prazo)"},
    "sp500": {"titulo": "S&P 500", "unidade": "pontos", "secao": "Mercado (curto prazo)"},
    "vix": {"titulo": "VIX", "unidade": "índice", "secao": "Mercado (curto prazo)"},
}

# Paleta validada (dataviz skill): série = azul categórico slot 1;
# anomalia = status crítico; tons neutros de superfície/tinta.
COR_SERIE = "#2a78d6"
COR_ANOMALIA = "#d03b3b"
COR_SUPERFICIE = "#fcfcfb"
COR_TINTA_PRIMARIA = "#0b0b0b"
COR_TINTA_SECUNDARIA = "#52514e"
COR_GRADE = "#e1e0d9"
COR_EIXO = "#c3c2b7"
# ---------------------------------------------------------------------------


def carregar_series():
    sinais = get_recent_signals(modulo="economia_credito", limit=5000)
    series = {chave: [] for chave in INDICADORES}

    for s in sinais:
        campos = parse_tags(s["tags"])
        chave = next((c for c in INDICADORES if c in campos.get("_rotulos", [])), None)
        if chave is None or "data_ref" not in campos or "valor" not in campos:
            continue
        try:
            valor = float(campos["valor"])
        except ValueError:
            continue
        anomalia = "anomalia" in campos.get("_rotulos", [])
        series[chave].append((campos["data_ref"], valor, anomalia))

    for chave in series:
        series[chave].sort(key=lambda ponto: ponto[0])
    return series


def layout_base(titulo):
    return dict(
        title=dict(text=titulo, font=dict(color=COR_TINTA_PRIMARIA, size=16)),
        paper_bgcolor=COR_SUPERFICIE,
        plot_bgcolor=COR_SUPERFICIE,
        font=dict(color=COR_TINTA_SECUNDARIA, family="system-ui, -apple-system, sans-serif"),
        margin=dict(l=50, r=20, t=50, b=40),
        height=320,
        xaxis=dict(gridcolor=COR_GRADE, linecolor=COR_EIXO, showgrid=False),
        yaxis=dict(gridcolor=COR_GRADE, linecolor=COR_EIXO, zeroline=False),
        showlegend=True,
        legend=dict(orientation="h", y=1.15, font=dict(size=11)),
    )


def montar_grafico_linha(meta, pontos):
    datas = [p[0] for p in pontos]
    valores = [p[1] for p in pontos]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=datas, y=valores, mode="lines+markers",
        line=dict(color=COR_SERIE, width=2),
        marker=dict(color=COR_SERIE, size=8),
        name=meta["titulo"],
        hovertemplate="%{x}<br>%{y:.2f} " + meta["unidade"] + "<extra></extra>",
    ))

    datas_anomalia = [p[0] for p in pontos if p[2]]
    valores_anomalia = [p[1] for p in pontos if p[2]]
    if datas_anomalia:
        fig.add_trace(go.Scatter(
            x=datas_anomalia, y=valores_anomalia, mode="markers",
            marker=dict(color=COR_ANOMALIA, size=11, symbol="diamond",
                        line=dict(color=COR_SUPERFICIE, width=1)),
            name="fora do intervalo esperado — revisar",
            hovertemplate="%{x}<br>%{y:.2f} " + meta["unidade"] + " (anomalia)<extra></extra>",
        ))

    fig.update_layout(**layout_base(f"{meta['titulo']} ({meta['unidade']})"))
    return fig


def montar_kpi(meta, pontos):
    # KPI usa só pontos válidos — uma anomalia nunca vira "o número atual",
    # mesmo sendo o ponto mais recente da série (ver CONTROLES.md).
    validos = [p for p in pontos if not p[2]]
    if not validos:
        return None

    atual_data, atual = validos[-1][0], validos[-1][1]
    anterior = validos[-2][1] if len(validos) > 1 else None

    fig = go.Figure(go.Indicator(
        mode="number+delta" if anterior is not None else "number",
        value=atual,
        number=dict(suffix=f" {meta['unidade']}", font=dict(color=COR_TINTA_PRIMARIA, size=32)),
        delta=(
            dict(reference=anterior, increasing=dict(color=COR_TINTA_SECUNDARIA),
                 decreasing=dict(color=COR_TINTA_SECUNDARIA))
            if anterior is not None else None
        ),
        title=dict(text=f"{meta['titulo']} — {atual_data}",
                   font=dict(color=COR_TINTA_SECUNDARIA, size=13)),
    ))
    fig.update_layout(
        paper_bgcolor=COR_SUPERFICIE, height=150,
        margin=dict(l=20, r=20, t=50, b=10),
    )
    return fig


def gerar_dashboard():
    series = carregar_series()
    secoes = {}
    for chave, meta in INDICADORES.items():
        secoes.setdefault(meta["secao"], []).append((chave, meta))

    html = [
        "<!DOCTYPE html>",
        "<html lang=\"pt-BR\">",
        "<head><meta charset=\"utf-8\"><title>Radar Econômico</title></head>",
        "<body>",
        "<div style=\"font-family: system-ui, -apple-system, sans-serif; "
        f"max-width: 1000px; margin: 0 auto; padding: 24px; background: {COR_SUPERFICIE}; "
        f"color: {COR_TINTA_PRIMARIA};\">",
        "<h1 style=\"font-size: 22px;\">Radar Econômico — painel</h1>",
        f"<p style=\"color: {COR_TINTA_SECUNDARIA}; font-size: 13px;\">"
        "Pontos em losango vermelho ficam fora do intervalo plausível e têm status "
        "\"investigando\" na base — revisar antes de usar na análise.</p>",
    ]

    plotlyjs_incluido = False

    def renderizar(fig):
        nonlocal plotlyjs_incluido
        include_js = "inline" if not plotlyjs_incluido else False
        plotlyjs_incluido = True
        return fig.to_html(full_html=False, include_plotlyjs=include_js)

    for secao, itens in secoes.items():
        graficos_secao = [(chave, meta) for chave, meta in itens if series.get(chave)]
        if not graficos_secao:
            continue
        html.append(f"<h2 style=\"font-size: 17px; margin-top: 32px;\">{secao}</h2>")
        html.append("<div style=\"display: flex; flex-wrap: wrap; gap: 12px;\">")
        for chave, meta in graficos_secao:
            kpi = montar_kpi(meta, series[chave])
            if kpi is not None:
                html.append(f"<div style=\"flex: 1 1 220px;\">{renderizar(kpi)}</div>")
        html.append("</div>")
        for chave, meta in graficos_secao:
            linha = montar_grafico_linha(meta, series[chave])
            html.append(renderizar(linha))

    if all(not series.get(chave) for chave in INDICADORES):
        html.append(
            f"<p style=\"color: {COR_TINTA_SECUNDARIA};\">Nenhum dado capturado ainda — "
            "rode as ingestões (./rodar_tudo.sh) antes de gerar o painel.</p>"
        )

    html.append("</div>")
    html.append("</body></html>")

    with open(SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"Dashboard salvo em {SAIDA_HTML}")


if __name__ == "__main__":
    gerar_dashboard()
