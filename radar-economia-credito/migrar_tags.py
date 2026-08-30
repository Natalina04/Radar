"""Migração única: preenche data_ref/valor no campo tags dos sinais que já
existiam ANTES da versão com tags estruturadas (ver storage/tags.py).

Sem isso, sinais capturados antes desta mudança não aparecem no dashboard
nem no relatório mensal — mas continuam intactos na base (nada é apagado
nem sobrescrito além do campo tags). Sinal que já está no formato novo é
ignorado (idempotente — seguro rodar mais de uma vez).

Rode uma vez, depois de atualizar o código (ex: após um git pull):
    python migrar_tags.py
"""

import re
from datetime import datetime

from storage.db import get_connection
from storage.tags import montar_tags, parse_tags

PADRAO_FONTE_CHAVE = re.compile(r"\(([a-z0-9_]+)\)\s*$")
PADRAO_DATA_VALOR = re.compile(r"em (\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}):\s*([\d.]+)")


def normalizar_data(data_str):
    if "/" in data_str:
        return datetime.strptime(data_str, "%d/%m/%Y").date().isoformat()
    return data_str


def migrar():
    with get_connection() as conn:
        linhas = conn.execute(
            "SELECT id, fonte, resumo, tags FROM sinais WHERE modulo = 'economia_credito'"
        ).fetchall()

        atualizados = 0
        ignorados_sem_padrao = 0

        for linha in linhas:
            campos = parse_tags(linha["tags"])
            if "data_ref" in campos:
                continue  # já está no formato novo

            m_chave = PADRAO_FONTE_CHAVE.search(linha["fonte"] or "")
            m_data_valor = PADRAO_DATA_VALOR.search(linha["resumo"] or "")
            if not m_chave or not m_data_valor:
                ignorados_sem_padrao += 1
                continue

            data_ref = normalizar_data(m_data_valor.group(1))
            valor = m_data_valor.group(2)
            novas_tags = montar_tags(*campos["_rotulos"], data_ref=data_ref, valor=valor)

            conn.execute("UPDATE sinais SET tags = ? WHERE id = ?", (novas_tags, linha["id"]))
            atualizados += 1

    print(f"[migrar_tags] {atualizados} sinal(is) atualizado(s) com data_ref/valor.")
    if ignorados_sem_padrao:
        print(f"[migrar_tags] {ignorados_sem_padrao} sinal(is) não bateram com o padrão esperado "
              "(revise manualmente se quiser que apareçam no dashboard).")


if __name__ == "__main__":
    migrar()
