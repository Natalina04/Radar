"""Acesso à base de conhecimento SQLite (tabela "sinais").

Pensado para ser trocado por Postgres depois: nada aqui usa sintaxe
específica do SQLite além do próprio arquivo de schema, e todas as
funções recebem/retornam apenas tipos simples (dict, list, str).
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

CAMPOS_SINAL = (
    "data_captura", "fonte", "modulo", "tipo", "resumo",
    "por_que_importa", "status", "evidencias", "decisao", "licenca", "tags",
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria a tabela "sinais" (e índices) se ainda não existir."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def insert_signal(
    fonte,
    modulo,
    tipo,
    resumo=None,
    por_que_importa=None,
    status="novo",
    evidencias=None,
    decisao=None,
    licenca=None,
    tags=None,
):
    """Insere um sinal novo. Duplicado (mesma fonte+tipo+resumo) é ignorado.

    Retorna True se um registro novo foi inserido, False se já existia.
    """
    data_captura = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO sinais
                (data_captura, fonte, modulo, tipo, resumo, por_que_importa,
                 status, evidencias, decisao, licenca, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data_captura, fonte, modulo, tipo, resumo, por_que_importa,
             status, evidencias, decisao, licenca, tags),
        )
        return cursor.rowcount > 0


def get_recent_signals(modulo=None, status=None, limit=20):
    """Retorna os sinais mais recentes, opcionalmente filtrando por módulo/status."""
    query = "SELECT * FROM sinais WHERE 1=1"
    params = []
    if modulo:
        query += " AND modulo = ?"
        params.append(modulo)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY data_captura DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def count_by_modulo_status():
    """Retorna contagem de sinais agrupada por (módulo, status), para o relatório."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT modulo, status, COUNT(*) AS total FROM sinais "
            "GROUP BY modulo, status ORDER BY modulo, status"
        ).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print(f"Base inicializada em {DB_PATH}")
