"""Validação de intervalo plausível por indicador — controle de atividade
(COSO: Control Activities) que roda antes de cada inserção na base.

Um valor fora do intervalo NUNCA é descartado silenciosamente: o sinal é
inserido com status="investigando" e a tag "anomalia", para revisão manual.
Isso protege contra dado corrompido/erro de fonte virar "fato" na base sem
ninguém perceber.
"""

# ---------------------------------------------------------------------------
# PARÂMETROS — ajuste os limites se um indicador novo passar a ser capturado,
# ou se algum limite se mostrar apertado/frouxo demais na prática.
# ---------------------------------------------------------------------------
LIMITES_PLAUSIVEIS = {
    "selic_meta": (0, 100),          # % a.a.
    "ipca_mensal": (-5, 5),          # % no mês
    "cambio_usd_venda": (0, 50),     # R$
    "fed_funds_rate": (0, 25),       # % a.a.
    "us_cpi": (0, 500),              # índice
    "ibovespa": (0, 1_000_000),      # pontos
    "sp500": (0, 50_000),            # pontos
    "vix": (0, 100),                 # índice
}
# ---------------------------------------------------------------------------


def validar_valor(chave, valor):
    """True se o valor está dentro do intervalo plausível cadastrado.

    Indicador sem limite cadastrado é considerado válido (não bloqueia a
    ingestão de indicadores novos que ainda não tiveram limite definido).
    """
    limites = LIMITES_PLAUSIVEIS.get(chave)
    if limites is None:
        return True
    minimo, maximo = limites
    return minimo <= valor <= maximo
