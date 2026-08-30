"""Relatório simples dos sinais mais recentes, por módulo e status.

Uso:
    python -m reports.relatorio                     # imprime no terminal
    python -m reports.relatorio --markdown           # imprime em Markdown
    python -m reports.relatorio --markdown --saida relatorio.md
    python -m reports.relatorio --limite 10 --modulo economia_credito
"""

import argparse
from datetime import datetime, timezone

from storage.db import count_by_modulo_status, get_recent_signals, init_db

MODULOS_VALIDOS = ("economia_credito", "remanufatura_digital")


def montar_relatorio_texto(limite, modulo=None):
    linhas = [f"Relatório Radar — gerado em {datetime.now(timezone.utc).isoformat(timespec='seconds')}", ""]

    linhas.append("Resumo por módulo/status:")
    for row in count_by_modulo_status():
        if modulo and row["modulo"] != modulo:
            continue
        linhas.append(f"  - {row['modulo']} / {row['status']}: {row['total']}")
    linhas.append("")

    for m in ([modulo] if modulo else MODULOS_VALIDOS):
        linhas.append(f"=== {m} — {limite} sinal(is) mais recente(s) ===")
        sinais = get_recent_signals(modulo=m, limit=limite)
        if not sinais:
            linhas.append("  (nenhum sinal ainda)")
        for s in sinais:
            linhas.append(f"  [{s['status']}] {s['data_captura']} — {s['resumo']}")
            if s["licenca"]:
                linhas.append(f"      licença: {s['licenca']}")
        linhas.append("")

    return "\n".join(linhas)


def montar_relatorio_markdown(limite, modulo=None):
    linhas = [f"# Relatório Radar\n\n_Gerado em {datetime.now(timezone.utc).isoformat(timespec='seconds')}_\n"]

    linhas.append("## Resumo por módulo/status\n")
    linhas.append("| Módulo | Status | Total |")
    linhas.append("|---|---|---|")
    for row in count_by_modulo_status():
        if modulo and row["modulo"] != modulo:
            continue
        linhas.append(f"| {row['modulo']} | {row['status']} | {row['total']} |")
    linhas.append("")

    for m in ([modulo] if modulo else MODULOS_VALIDOS):
        linhas.append(f"## {m} — {limite} sinal(is) mais recente(s)\n")
        sinais = get_recent_signals(modulo=m, limit=limite)
        if not sinais:
            linhas.append("_(nenhum sinal ainda)_\n")
            continue
        for s in sinais:
            licenca = f" _(licença: {s['licenca']})_" if s["licenca"] else ""
            linhas.append(f"- **[{s['status']}]** {s['data_captura']} — {s['resumo']}{licenca}")
        linhas.append("")

    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description="Relatório de sinais do Radar.")
    parser.add_argument("--limite", type=int, default=20, help="quantos sinais recentes listar por módulo")
    parser.add_argument("--modulo", choices=MODULOS_VALIDOS, help="filtrar por um único módulo")
    parser.add_argument("--markdown", action="store_true", help="gerar saída em Markdown em vez de texto simples")
    parser.add_argument("--saida", help="caminho de arquivo para salvar o relatório (senão, imprime no terminal)")
    args = parser.parse_args()

    init_db()

    if args.markdown:
        conteudo = montar_relatorio_markdown(args.limite, args.modulo)
    else:
        conteudo = montar_relatorio_texto(args.limite, args.modulo)

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"Relatório salvo em {args.saida}")
    else:
        print(conteudo)


if __name__ == "__main__":
    main()
