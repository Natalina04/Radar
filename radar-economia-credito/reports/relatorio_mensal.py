"""Relatório mensal analítico do cenário econômico (Brasil + global + mercado).

Compara o mês de referência mais recente disponível na base com o mês
anterior, indicador a indicador, e classifica a direção/magnitude da
variação por regra simples (limiar fixo) — não usa LLM nem julgamento
qualitativo; é um ponto de partida para a sua leitura, não uma conclusão.

Sinais marcados como anomalia pela validação (fora do intervalo plausível,
ver validacao.py) são EXCLUÍDOS do cálculo — nunca viram "o valor do mês"
só por serem o ponto mais recente.

Rode uma vez por mês (ou quando quiser reavaliar o cenário):
    python -m reports.relatorio_mensal
"""

from collections import defaultdict
from datetime import datetime, timezone

from analise import classificar, formatar_numero
from storage.db import get_recent_signals
from storage.tags import parse_tags

# ---------------------------------------------------------------------------
# PARÂMETROS
# ---------------------------------------------------------------------------
INDICADORES = {
    "selic_meta": "Selic (meta)",
    "ipca_mensal": "IPCA (mensal)",
    "cambio_usd_venda": "Câmbio USD/BRL",
    "fed_funds_rate": "Fed Funds Rate",
    "us_cpi": "US CPI",
    "ibovespa": "Ibovespa",
    "sp500": "S&P 500",
    "vix": "VIX",
}
# ---------------------------------------------------------------------------


def carregar_por_mes():
    sinais = get_recent_signals(modulo="economia_credito", limit=5000)
    # chave -> {"AAAA-MM": [(data_ref, valor, anomalia), ...]}
    por_indicador = defaultdict(lambda: defaultdict(list))

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
        mes = campos["data_ref"][:7]
        por_indicador[chave][mes].append((campos["data_ref"], valor, anomalia))

    return por_indicador


def meses_com_dado_valido(pontos_por_mes):
    """Filtra anomalias e retorna só os meses que sobraram com ao menos um
    ponto válido, junto com a contagem de anomalias excluídas por mês."""
    validos = {}
    anomalias_por_mes = {}
    for mes, pontos in pontos_por_mes.items():
        pontos_validos = [(d, v) for d, v, anomalia in pontos if not anomalia]
        n_anomalias = sum(1 for _, _, anomalia in pontos if anomalia)
        if pontos_validos:
            validos[mes] = pontos_validos
        if n_anomalias:
            anomalias_por_mes[mes] = n_anomalias
    return validos, anomalias_por_mes


def ultimo_valor_do_mes(pontos_do_mes):
    return sorted(pontos_do_mes)[-1][1]


def montar_relatorio():
    por_indicador = carregar_por_mes()

    linhas = [
        "# Relatório mensal — cenário econômico",
        "",
        f"_Gerado em {datetime.now(timezone.utc).isoformat(timespec='seconds')}_",
        "",
        "Leitura gerada por regra simples (limiar de variação percentual), "
        "não por análise qualitativa ou modelo — use como ponto de partida. "
        "Sinais marcados como anomalia (fora do intervalo plausível) são "
        "excluídos do cálculo.",
        "",
        "| Indicador | Mês atual | Valor atual | Mês anterior | Valor anterior | Variação |",
        "|---|---|---|---|---|---|",
    ]
    comentarios = []
    avisos_anomalia = []
    algum_dado = False

    for chave, titulo in INDICADORES.items():
        meses_validos, anomalias_por_mes = meses_com_dado_valido(por_indicador.get(chave, {}))

        for mes, n in sorted(anomalias_por_mes.items()):
            avisos_anomalia.append(
                f"- {titulo}: {n} sinal(is) de {mes} marcados como anomalia, excluído(s) do cálculo."
            )

        meses = sorted(meses_validos.keys())
        if not meses:
            continue
        algum_dado = True

        mes_atual = meses[-1]
        valor_atual = ultimo_valor_do_mes(meses_validos[mes_atual])

        if len(meses) >= 2:
            mes_anterior = meses[-2]
            valor_anterior = ultimo_valor_do_mes(meses_validos[mes_anterior])
            delta_pct = ((valor_atual - valor_anterior) / abs(valor_anterior)) * 100 if valor_anterior else None
        else:
            mes_anterior, valor_anterior, delta_pct = "—", None, None

        variacao_txt = f"{formatar_numero(delta_pct, forcar_sinal=True)}%" if delta_pct is not None else "—"
        valor_anterior_txt = formatar_numero(valor_anterior) if valor_anterior is not None else "—"
        linhas.append(
            f"| {titulo} | {mes_atual} | {formatar_numero(valor_atual)} | {mes_anterior} | "
            f"{valor_anterior_txt} | {variacao_txt} |"
        )

        classificacao = classificar(delta_pct)
        detalhe = f" ({formatar_numero(delta_pct, forcar_sinal=True)}% no mês)" if delta_pct is not None else ""
        comentarios.append(f"- **{titulo}**: {classificacao}{detalhe}.")

    if not algum_dado:
        linhas.append("| _(nenhum dado válido capturado ainda)_ | | | | | |")

    linhas += ["", "## Leitura do cenário", ""]
    linhas += comentarios if comentarios else ["_(sem dados suficientes para leitura ainda)_"]

    if avisos_anomalia:
        linhas += ["", "## Anomalias excluídas do cálculo", ""]
        linhas += avisos_anomalia
        linhas += ["", "_Revise esses sinais (`status = \"investigando\"` na base) antes de confiar neles._"]

    return "\n".join(linhas)


def main():
    conteudo = montar_relatorio()
    mes_ref = datetime.now(timezone.utc).strftime("%Y-%m")
    caminho = f"relatorio_mensal_{mes_ref}.md"

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"Relatório mensal salvo em {caminho}")
    print()
    print(conteudo)


if __name__ == "__main__":
    main()
