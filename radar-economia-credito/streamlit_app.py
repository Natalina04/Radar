"""Radar Econômico — boletim de cenário (app Streamlit).

Painel interativo do radar-economia-credito: resumo executivo, leitura por
indicador (Brasil / Global / Mercado) e seção regulatória, lendo direto da
base compartilhada.

Rode com:
    streamlit run streamlit_app.py

No Posit Cloud, depois de rodar o comando acima no Terminal, use o botão
"Open in Browser" que aparece no canto superior direito da aba do Terminal
(ou o link http://localhost:<porta> que o Streamlit imprime).
"""

from datetime import datetime, timezone

import altair as alt
import pandas as pd
import streamlit as st

from analise import analisar_serie, clausula, formatar_numero
from storage.db import get_recent_signals
from storage.tags import parse_tags

# ---------------------------------------------------------------------------
# PARÂMETROS
# ---------------------------------------------------------------------------
MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

SECOES = {
    "Brasil": [
        {"chave": "selic_meta", "titulo": "Selic (meta)", "unidade": "% a.a."},
        {"chave": "ipca_mensal", "titulo": "IPCA (mensal)", "unidade": "%"},
        {"chave": "cambio_usd_venda", "titulo": "Câmbio USD/BRL", "unidade": " R$"},
    ],
    "Global": [
        {"chave": "fed_funds_rate", "titulo": "Fed Funds Rate", "unidade": "% a.a."},
        {"chave": "us_cpi", "titulo": "US CPI", "unidade": " pts"},
    ],
    "Mercado": [
        {"chave": "ibovespa", "titulo": "Ibovespa", "unidade": " pts"},
        {"chave": "sp500", "titulo": "S&P 500", "unidade": " pts"},
        {"chave": "vix", "titulo": "VIX", "unidade": " pts"},
    ],
}

COR_ACENTO = "#2a8a92"
COR_CRITICO = "#c1484b"
# ---------------------------------------------------------------------------


def data_por_extenso(momento):
    return f"{momento.day} de {MESES_PT[momento.month]} de {momento.year}"


@st.cache_data(ttl=60)
def carregar_dados():
    sinais = get_recent_signals(modulo="economia_credito", limit=5000)
    series = {}
    regulatorios = []

    todas_chaves = {ind["chave"] for indicadores in SECOES.values() for ind in indicadores}

    for s in sinais:
        campos = parse_tags(s["tags"])
        if s["tipo"] == "regulatorio":
            regulatorios.append(dict(s))
            continue
        chave = next((c for c in campos.get("_rotulos", []) if c in todas_chaves), None)
        if chave is None or "data_ref" not in campos or "valor" not in campos:
            continue
        try:
            valor = float(campos["valor"])
        except ValueError:
            continue
        anomalia = "anomalia" in campos.get("_rotulos", [])
        series.setdefault(chave, []).append((campos["data_ref"], valor, anomalia))

    for chave in series:
        series[chave].sort(key=lambda ponto: ponto[0])

    return series, regulatorios


def montar_resumo_executivo(series):
    frases = []
    for nome_secao, indicadores in SECOES.items():
        clausulas = []
        for ind in indicadores:
            pontos = series.get(ind["chave"], [])
            validos = [(d, v) for d, v, anomalia in pontos if not anomalia]
            analise = analisar_serie(validos)
            if analise is None:
                continue
            clausulas.append(clausula(ind["titulo"], ind["unidade"], analise))
        if clausulas:
            frases.append(f"<strong>{nome_secao}</strong> — {'; '.join(clausulas)}.")
    return frases


def montar_grafico(pontos, unidade):
    df = pd.DataFrame(pontos, columns=["data_ref", "valor", "anomalia"])
    df["data_ref"] = pd.to_datetime(df["data_ref"])
    df_normais = df[~df["anomalia"]]

    # domínio calculado só com pontos válidos — uma anomalia (ex: 999 no VIX)
    # nunca deve distorcer a escala e achatar o resto da série.
    vmin, vmax = df_normais["valor"].min(), df_normais["valor"].max()
    folga = (vmax - vmin) * 0.2 or abs(vmax) * 0.05 or 1
    dominio = [vmin - folga, vmax + folga]

    tooltip_valor = [
        alt.Tooltip("data_ref:T", title="data", format="%d/%m/%Y"),
        alt.Tooltip("valor:Q", title="valor", format=",.2f"),
    ]

    linha = (
        alt.Chart(df_normais)
        .mark_line(color=COR_ACENTO, strokeWidth=2, point=alt.OverlayMarkDef(color=COR_ACENTO, size=45))
        .encode(
            x=alt.X("data_ref:T", title=None, axis=alt.Axis(format="%d/%m", grid=False, tickCount=5)),
            y=alt.Y("valor:Q", title=None, scale=alt.Scale(domain=dominio), axis=alt.Axis(grid=True, gridOpacity=0.2)),
            tooltip=tooltip_valor,
        )
    )

    camadas = [linha]

    if df["anomalia"].any():
        pontos_anomalia = (
            alt.Chart(df[df["anomalia"]])
            .mark_point(size=100, color=COR_CRITICO, shape="diamond", strokeWidth=2, filled=False)
            .encode(
                x=alt.X("data_ref:T"),
                y=alt.Y("valor:Q", scale=alt.Scale(domain=dominio, clamp=True)),
                tooltip=[alt.Tooltip("data_ref:T", title="data", format="%d/%m/%Y"),
                         alt.Tooltip("valor:Q", title="valor (anomalia)", format=",.2f")],
            )
        )
        camadas.append(pontos_anomalia)

    return alt.layer(*camadas).properties(height=140).configure_view(strokeWidth=0)


def render_indicador(ind, series):
    pontos = series.get(ind["chave"], [])
    if not pontos:
        st.caption(f"**{ind['titulo']}** — ainda sem dado capturado.")
        return

    validos = [(d, v) for d, v, anomalia in pontos if not anomalia]
    tem_anomalia = any(a for _, _, a in pontos)
    analise = analisar_serie(validos)

    col_kpi, col_grafico = st.columns([1, 2], gap="large")

    with col_kpi:
        if analise is None:
            st.metric(ind["titulo"], "—")
        else:
            valor_fmt = f"{formatar_numero(analise['valor_atual'])}{ind['unidade']}"
            delta_fmt = (
                f"{formatar_numero(analise['delta_pct'], forcar_sinal=True)}%"
                if analise["delta_pct"] is not None else None
            )
            st.metric(ind["titulo"], valor_fmt, delta=delta_fmt, delta_color="off")
            st.caption(f"em {analise['data_atual']}")
        st.write(clausula(ind["titulo"], ind["unidade"], analise) + ".")
        if tem_anomalia:
            st.error(
                "Há ponto(s) fora do intervalo plausível (losango, no gráfico) — "
                "excluído(s) desta leitura. Revisar na base "
                "(`status = \"investigando\"`).",
                icon="⚠️",
            )

    with col_grafico:
        st.altair_chart(montar_grafico(pontos, ind["unidade"]), width="stretch")


def render_regulatorio(regulatorios):
    if not regulatorios:
        st.info(
            "Este projeto ainda não tem uma ingestão automática de normativos "
            "(Bacen, CMN, Open Finance) — o tipo `regulatorio` já existe no "
            "schema, pronto para quando essa fonte for adicionada. Até lá, esta "
            "seção fica vazia por padrão, não por engano.",
            icon="📋",
        )
        return

    st.caption(f"{len(regulatorios)} norma(s) capturada(s)")
    for r in regulatorios:
        with st.container(border=True):
            st.write(r["resumo"] or r["fonte"])
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.caption(f"{r['fonte']} · status: {r['status']}")
            with col_b:
                if r.get("evidencias"):
                    st.link_button("Acessar norma →", r["evidencias"])


def main():
    st.set_page_config(page_title="Radar Econômico", page_icon="📡", layout="wide")

    st.markdown(
        """
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,600;1,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
        <style>
        html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Newsreader', Georgia, serif; }
        [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }
        .resumo-executivo em { font-family: 'Newsreader', Georgia, serif; font-style: italic; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    series, regulatorios = carregar_dados()
    agora = datetime.now(timezone.utc)

    st.caption("RADAR ECONÔMICO")
    st.title("Boletim de cenário")
    st.caption(f"Gerado em {data_por_extenso(agora)} · {agora.strftime('%H:%M')} UTC")

    with st.container(border=True):
        st.markdown("**Leitura do cenário**")
        frases = montar_resumo_executivo(series)
        if frases:
            for frase in frases:
                st.markdown(f"<div class='resumo-executivo'><em>{frase}</em></div>", unsafe_allow_html=True)
        else:
            st.write("Ainda não há dados suficientes — rode as ingestões (`./rodar_tudo.sh`) primeiro.")

    abas = st.tabs(list(SECOES.keys()) + ["Regulatório"])

    for aba, (nome_secao, indicadores) in zip(abas[:-1], SECOES.items()):
        with aba:
            for i, ind in enumerate(indicadores):
                render_indicador(ind, series)
                if i < len(indicadores) - 1:
                    st.divider()

    with abas[-1]:
        render_regulatorio(regulatorios)

    st.caption(
        "Leitura gerada por regra simples (limiar de variação), não por modelo ou IA — "
        "use como ponto de partida. Pontos fora do intervalo plausível são sinalizados, "
        "nunca escondidos."
    )


if __name__ == "__main__":
    main()
