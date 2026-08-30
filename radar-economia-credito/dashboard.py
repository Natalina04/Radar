"""Painel visual do radar-economia-credito — um boletim de cenário, não um
amontoado de gráficos: resumo executivo, leitura por indicador e seção
regulatória, tudo em um único HTML autocontido (SEM JavaScript — os
gráficos são SVG puro, então renderizam em qualquer visualizador,
inclusive o preview embutido do Posit Cloud).

Rode com:  python dashboard.py
"""

from datetime import datetime, timezone

from analise import analisar_serie, clausula, formatar_numero
from storage.db import get_recent_signals
from storage.tags import parse_tags

# ---------------------------------------------------------------------------
# PARÂMETROS
# ---------------------------------------------------------------------------
SAIDA_HTML = "dashboard.html"

MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

SECOES = [
    {
        "titulo": "Brasil",
        "indicadores": [
            {"chave": "selic_meta", "titulo": "Selic (meta)", "unidade": "% a.a."},
            {"chave": "ipca_mensal", "titulo": "IPCA (mensal)", "unidade": "%"},
            {"chave": "cambio_usd_venda", "titulo": "Câmbio USD/BRL", "unidade": " R$"},
        ],
    },
    {
        "titulo": "Global",
        "indicadores": [
            {"chave": "fed_funds_rate", "titulo": "Fed Funds Rate", "unidade": "% a.a."},
            {"chave": "us_cpi", "titulo": "US CPI", "unidade": " pts"},
        ],
    },
    {
        "titulo": "Mercado (curto prazo)",
        "indicadores": [
            {"chave": "ibovespa", "titulo": "Ibovespa", "unidade": " pts"},
            {"chave": "sp500", "titulo": "S&P 500", "unidade": " pts"},
            {"chave": "vix", "titulo": "VIX", "unidade": " pts"},
        ],
    },
]
# ---------------------------------------------------------------------------


def data_por_extenso(momento):
    return f"{momento.day} de {MESES_PT[momento.month]} de {momento.year}"


def carregar_dados():
    sinais = get_recent_signals(modulo="economia_credito", limit=5000)
    series = {}
    regulatorios = []

    for s in sinais:
        campos = parse_tags(s["tags"])
        if s["tipo"] == "regulatorio":
            regulatorios.append(s)
            continue
        chave = next((c for c in campos.get("_rotulos", [])
                      if any(c == ind["chave"] for secao in SECOES for ind in secao["indicadores"])), None)
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


def montar_sparkline_svg(pontos, largura=440, altura=110):
    """SVG puro (sem JS) — funciona em qualquer visualizador. Ponto mais
    recente destacado; anomalias marcadas com um anel, nunca escondidas."""
    if not pontos:
        return '<p class="sem-dado">sem dados suficientes para o gráfico</p>'

    valores = [p[1] for p in pontos]
    minimo, maximo = min(valores), max(valores)
    span = (maximo - minimo) or 1
    pad_x, pad_y = 6, 16
    n = len(pontos)

    def x_de(i):
        return pad_x if n == 1 else pad_x + i * (largura - 2 * pad_x) / (n - 1)

    def y_de(v):
        return altura - pad_y - (v - minimo) / span * (altura - 2 * pad_y)

    coords = [(x_de(i), y_de(p[1])) for i, p in enumerate(pontos)]
    path_linha = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    base = altura - pad_y
    path_area = path_linha + f" L {coords[-1][0]:.1f},{base:.1f} L {coords[0][0]:.1f},{base:.1f} Z"

    marcadores = []
    for i, (x, y) in enumerate(coords):
        if pontos[i][2]:
            marcadores.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="none" '
                f'stroke="var(--critico)" stroke-width="2"/>'
            )
        elif i == n - 1:
            marcadores.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="var(--acento)"/>')

    svg = (
        f'<svg viewBox="0 0 {largura} {altura}" width="100%" height="{altura}" '
        'preserveAspectRatio="none" role="img" aria-label="série histórica">'
        f'<line x1="{pad_x}" y1="{base:.1f}" x2="{largura - pad_x}" y2="{base:.1f}" '
        'stroke="var(--hairline)" stroke-width="1"/>'
        f'<path d="{path_area}" fill="var(--acento)" opacity="0.12" stroke="none"/>'
        f'<path d="{path_linha}" fill="none" stroke="var(--acento)" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        f'{"".join(marcadores)}'
        '</svg>'
    )
    return svg


def montar_chip_delta(analise, tem_anomalia):
    if tem_anomalia:
        return '<span class="chip chip-critico">⚠ revisar — fora do intervalo plausível</span>'
    if analise is None or analise["delta_pct"] is None:
        return '<span class="chip chip-neutro">— sem histórico</span>'
    seta = "▲" if analise["delta_pct"] > 0 else ("▼" if analise["delta_pct"] < 0 else "●")
    return f'<span class="chip chip-neutro">{seta} {formatar_numero(analise["delta_pct"], forcar_sinal=True)}% no período</span>'


def montar_bloco_indicador(meta, pontos):
    validos = [(d, v) for d, v, anomalia in pontos if not anomalia]
    tem_anomalia = any(anomalia for _, _, anomalia in pontos)
    analise = analisar_serie(validos)

    if analise is None:
        valor_fmt = "—"
        data_fmt = "sem dado válido"
    else:
        valor_fmt = f"{formatar_numero(analise['valor_atual'])}{meta['unidade']}"
        data_fmt = analise["data_atual"]

    leitura = clausula(meta["titulo"], meta["unidade"], analise)
    aviso_anomalia = (
        '<p class="nota-anomalia">Há ponto(s) fora do intervalo plausível nesta série '
        '(círculo vermelho no gráfico) — excluído(s) desta leitura, revisar na base '
        '(<code>status = "investigando"</code>).</p>' if tem_anomalia else ""
    )

    return f"""
    <div class="indicador">
      <div class="indicador-rotulo">
        <span class="eyebrow">{meta['titulo']}</span>
        <span class="valor">{valor_fmt}</span>
        {montar_chip_delta(analise, False)}
        <span class="data-ref">{data_fmt}</span>
      </div>
      <div class="indicador-grafico">
        {montar_sparkline_svg(pontos)}
      </div>
      <p class="leitura">{leitura}.</p>
      {aviso_anomalia}
    </div>
    """


def montar_resumo_executivo(series):
    frases_por_secao = []
    for secao in SECOES:
        clausulas = []
        for ind in secao["indicadores"]:
            pontos = series.get(ind["chave"], [])
            validos = [(d, v) for d, v, anomalia in pontos if not anomalia]
            analise = analisar_serie(validos)
            if analise is None:
                continue
            clausulas.append(clausula(ind["titulo"], ind["unidade"], analise))
        if clausulas:
            frases_por_secao.append(f"Em <strong>{secao['titulo']}</strong>, {'; '.join(clausulas)}.")

    if not frases_por_secao:
        return ("<p>Ainda não há dados suficientes para uma leitura de cenário — "
                "rode as ingestões (<code>./rodar_tudo.sh</code>) primeiro.</p>")

    return "".join(f"<p>{frase}</p>" for frase in frases_por_secao)


def montar_secao_regulatorio(regulatorios):
    if not regulatorios:
        return """
        <section class="secao">
          <div class="secao-cabecalho">
            <h2>Regulatório</h2>
            <span class="contagem">0 normas capturadas</span>
          </div>
          <p class="placeholder">
            Este projeto ainda não tem uma ingestão automática de normativos
            (Bacen, CMN, Open Finance) — o tipo <code>regulatorio</code> já existe
            no schema, pronto para quando essa fonte for adicionada. Até lá, esta
            seção fica vazia por padrão, não por engano.
          </p>
        </section>
        """

    linhas = []
    for r in regulatorios:
        link = (f'<a class="link-norma" href="{r["evidencias"]}">Acessar norma →</a>'
                if r.get("evidencias") else "")
        linhas.append(f"""
        <div class="norma">
          <p class="norma-resumo">{r['resumo'] or r['fonte']}</p>
          <div class="norma-meta">
            <span class="chip chip-neutro">{r['status']}</span>
            <span class="norma-fonte">{r['fonte']}</span>
            {link}
          </div>
        </div>
        """)

    return f"""
    <section class="secao">
      <div class="secao-cabecalho">
        <h2>Regulatório</h2>
        <span class="contagem">{len(regulatorios)} norma(s) capturada(s)</span>
      </div>
      {"".join(linhas)}
    </section>
    """


CSS = """
:root {
  --papel: #f4f3ee;
  --cartao: #fbfaf7;
  --tinta: #20242b;
  --tinta-2: #5b5f66;
  --tinta-muda: #898f97;
  --hairline: #dcdad2;
  --acento: #1f6f78;
  --acento-suave: rgba(31,111,120,0.12);
  --critico: #a63d40;
  --critico-suave: rgba(166,61,64,0.12);
}
@media (prefers-color-scheme: dark) {
  :root {
    --papel: #14171c;
    --cartao: #1c2027;
    --tinta: #e8e6df;
    --tinta-2: #a9adb3;
    --tinta-muda: #6f747b;
    --hairline: #2c313a;
    --acento: #46a5ae;
    --acento-suave: rgba(70,165,174,0.16);
    --critico: #d1787b;
    --critico-suave: rgba(209,120,123,0.16);
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--papel);
  color: var(--tinta);
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif;
  line-height: 1.5;
}
.pagina { max-width: 840px; margin: 0 auto; padding: 48px 24px 80px; }
.masthead { margin-bottom: 40px; }
.eyebrow-topo {
  text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.72rem;
  color: var(--tinta-muda); font-weight: 500;
}
h1.titulo {
  font-family: "Newsreader", Georgia, serif;
  font-size: 2.1rem; font-weight: 600; margin: 6px 0 4px;
  text-wrap: balance;
}
.subtitulo { color: var(--tinta-2); font-size: 0.92rem; margin: 0; }
.resumo-executivo {
  background: var(--cartao); border: 1px solid var(--hairline);
  border-radius: 4px; padding: 24px 28px; margin-bottom: 44px;
}
.resumo-executivo .eyebrow { display:block; margin-bottom: 10px; }
.resumo-executivo p {
  font-family: "Newsreader", Georgia, serif; font-size: 1.08rem;
  font-style: italic; color: var(--tinta); margin: 0 0 10px;
}
.resumo-executivo p:last-child { margin-bottom: 0; }
.secao { margin-bottom: 44px; }
.secao-cabecalho {
  display: flex; align-items: baseline; justify-content: space-between;
  border-bottom: 1px solid var(--hairline); padding-bottom: 8px; margin-bottom: 4px;
}
.secao-cabecalho h2 {
  font-family: "Newsreader", Georgia, serif; font-size: 1.3rem; font-weight: 600; margin: 0;
}
.contagem { font-size: 0.8rem; color: var(--tinta-muda); font-variant-numeric: tabular-nums; }
.indicador {
  display: grid; grid-template-columns: 200px 1fr; gap: 8px 24px;
  padding: 22px 0; border-bottom: 1px solid var(--hairline);
}
.indicador:last-child { border-bottom: none; }
.indicador-rotulo { display: flex; flex-direction: column; gap: 4px; }
.eyebrow {
  text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.7rem;
  color: var(--tinta-muda); font-weight: 500;
}
.valor {
  font-family: "IBM Plex Mono", monospace; font-size: 1.7rem; font-weight: 500;
  font-variant-numeric: tabular-nums; color: var(--tinta);
}
.data-ref { font-size: 0.78rem; color: var(--tinta-muda); }
.chip {
  display: inline-block; font-size: 0.76rem; padding: 3px 9px; border-radius: 100px;
  width: fit-content; font-variant-numeric: tabular-nums;
}
.chip-neutro { background: var(--acento-suave); color: var(--acento); }
.chip-critico { background: var(--critico-suave); color: var(--critico); }
.indicador-grafico { grid-row: span 2; align-self: center; }
.leitura { grid-column: 1 / -1; margin: 4px 0 0; color: var(--tinta-2); font-size: 0.92rem; }
.nota-anomalia {
  grid-column: 1 / -1; margin: 2px 0 0; font-size: 0.82rem; color: var(--critico);
}
.nota-anomalia code, .placeholder code {
  background: var(--critico-suave); padding: 1px 5px; border-radius: 3px; font-size: 0.85em;
}
.placeholder code { background: var(--acento-suave); color: var(--acento); }
.placeholder { color: var(--tinta-2); font-size: 0.92rem; }
.norma {
  padding: 16px 0; border-bottom: 1px solid var(--hairline);
}
.norma:last-child { border-bottom: none; }
.norma-resumo { margin: 0 0 6px; }
.norma-meta { display: flex; align-items: center; gap: 12px; font-size: 0.82rem; color: var(--tinta-muda); }
.link-norma { color: var(--acento); text-decoration: none; font-weight: 500; }
.link-norma:hover { text-decoration: underline; }
.rodape { margin-top: 56px; font-size: 0.78rem; color: var(--tinta-muda); }
"""


def gerar_dashboard():
    series, regulatorios = carregar_dados()
    agora = datetime.now(timezone.utc)

    blocos_secoes = []
    for secao in SECOES:
        blocos_indicadores = [
            montar_bloco_indicador(ind, series.get(ind["chave"], []))
            for ind in secao["indicadores"]
            if series.get(ind["chave"])
        ]
        if not blocos_indicadores:
            continue
        blocos_secoes.append(f"""
        <section class="secao">
          <div class="secao-cabecalho"><h2>{secao['titulo']}</h2></div>
          {"".join(blocos_indicadores)}
        </section>
        """)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radar Econômico</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,600;1,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="pagina">
  <div class="masthead">
    <span class="eyebrow-topo">Radar Econômico</span>
    <h1 class="titulo">Boletim de cenário</h1>
    <p class="subtitulo">Gerado em {data_por_extenso(agora)} · {agora.strftime('%H:%M')} UTC</p>
  </div>

  <div class="resumo-executivo">
    <span class="eyebrow">Leitura do cenário</span>
    {montar_resumo_executivo(series)}
  </div>

  {"".join(blocos_secoes)}

  {montar_secao_regulatorio(regulatorios)}

  <p class="rodape">
    Leitura gerada por regra simples (limiar de variação), não por modelo ou IA —
    use como ponto de partida. Pontos fora do intervalo plausível são sinalizados,
    nunca escondidos.
  </p>
</div>
</body>
</html>"""

    with open(SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard salvo em {SAIDA_HTML}")


if __name__ == "__main__":
    gerar_dashboard()
