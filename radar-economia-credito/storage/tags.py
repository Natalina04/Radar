"""Codifica/decodifica o campo "tags" da tabela sinais como uma lista de
rótulos livres + pares chave=valor (ex: "bacen,sgs,selic_meta,data_ref=2026-09-12,valor=14.00").

Isso permite ao dashboard e ao relatório mensal recuperar a série temporal
(data de referência + valor numérico) de cada indicador sem mudar o schema
da tabela sinais nem a lógica de dedup (que continua baseada em
fonte+tipo+resumo).
"""


def montar_tags(*rotulos, **campos):
    partes = list(rotulos)
    partes += [f"{chave}={valor}" for chave, valor in campos.items()]
    return ",".join(str(p) for p in partes)


def parse_tags(tags_str):
    """Retorna um dict com os pares chave=valor encontrados, mais uma
    chave especial "_rotulos" com a lista de rótulos livres (sem "=")."""
    campos = {"_rotulos": []}
    for parte in (tags_str or "").split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            campos[chave] = valor
        else:
            campos["_rotulos"].append(parte)
    return campos
