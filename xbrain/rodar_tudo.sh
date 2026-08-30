#!/usr/bin/env bash
# Prepara o ambiente e roda a ingestão completa do xbrain.
# Uso (no Terminal do Posit Cloud ou local):
#   cd xbrain && ./rodar_tudo.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${VIRTUAL_ENV:-}" ]; then
    if [ ! -d ".venv" ]; then
        echo ">> Criando ambiente virtual (.venv)..."
        python3 -m venv .venv
    fi
    echo ">> Ativando .venv..."
    # shellcheck source=/dev/null
    source .venv/bin/activate
fi

echo ">> Instalando dependências..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo ">> Nenhum .env encontrado — copiando .env.example."
    echo "   GITHUB_TOKEN é opcional (sem ele, o rate limit de busca é menor)."
    cp .env.example .env
fi

echo ""
echo "== Busca no GitHub (candidatos a incorporação) =="
echo "   Edite MEUS_PROJETOS em ingest/github_scan.py para refletir seus projetos reais."
python -m ingest.github_scan

echo ""
echo "== Relatório =="
data_hoje=$(date +%Y-%m-%d)
python -m reports.relatorio --markdown --saida "relatorio_${data_hoje}.md"
python -m reports.relatorio

echo ""
echo ">> Concluído. Relatório salvo em relatorio_${data_hoje}.md"
