"""Lógica de leitura de cenário compartilhada entre o dashboard e o
relatório mensal: classifica a variação de cada indicador e monta as
frases de análise. Regra simples (limiar fixo) — não usa LLM nem
julgamento qualitativo; é o texto que baseia a sua própria leitura.
"""

LIMIAR_ESTAVEL_PCT = 0.5


def formatar_numero(valor, casas=2, forcar_sinal=False):
    """Formata no padrão brasileiro: ponto de milhar, vírgula decimal."""
    especificador = f"{{:{'+' if forcar_sinal else ''},.{casas}f}}"
    texto = especificador.format(valor)
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def classificar(delta_pct):
    if delta_pct is None:
        return "sem histórico suficiente"
    if abs(delta_pct) < LIMIAR_ESTAVEL_PCT:
        return "estável"
    return "em alta" if delta_pct > 0 else "em queda"


def analisar_serie(pontos_validos):
    """pontos_validos: [(data_ref, valor), ...] ordenado por data (sem
    anomalias). Retorna None se não houver nenhum ponto válido."""
    if not pontos_validos:
        return None

    data_atual, atual = pontos_validos[-1]
    if len(pontos_validos) > 1:
        _, anterior = pontos_validos[-2]
        delta_pct = ((atual - anterior) / abs(anterior)) * 100 if anterior else None
    else:
        anterior, delta_pct = None, None

    return {
        "data_atual": data_atual,
        "valor_atual": atual,
        "valor_anterior": anterior,
        "delta_pct": delta_pct,
        "classificacao": classificar(delta_pct),
    }


def clausula(titulo, unidade, analise):
    """Uma frase curta descrevendo o estado de um indicador, para compor
    o resumo executivo ou a leitura do cenário."""
    if analise is None:
        return f"{titulo} ainda sem dado capturado"
    valor_fmt = formatar_numero(analise["valor_atual"])
    if analise["delta_pct"] is None:
        return f"{titulo} em {valor_fmt}{unidade} (ainda sem histórico anterior para comparar)"
    delta_fmt = formatar_numero(analise["delta_pct"], forcar_sinal=True)
    return (
        f"{titulo} {analise['classificacao']} "
        f"({delta_fmt}% no período, agora em {valor_fmt}{unidade})"
    )
