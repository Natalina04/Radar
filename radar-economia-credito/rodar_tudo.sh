#!/usr/bin/env bash
# Prepara o ambiente e roda a ingestão completa do radar-economia-credito.
# Uso (no Terminal do Posit Cloud ou local):
#   cd radar-economia-credito && ./rodar_tudo.sh
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
    echo "   Preencha FRED_API_KEY em .env e rode de novo para captar dados do FRED."
    cp .env.example .env
fi

echo ""
echo "== Backup do banco =="
./backup_db.sh

echo ""
echo "== Bacen SGS (Selic, IPCA, câmbio) =="
python -m ingest.bacen_sgs

echo ""
echo "== FRED (Fed funds rate, US CPI) =="
python -m ingest.fred

echo ""
echo "== Mercado (Ibovespa, S&P500, VIX) =="
python -m ingest.mercado

echo ""
echo "== Relatório =="
data_hoje=$(date +%Y-%m-%d)
python -m reports.relatorio --markdown --saida "relatorio_${data_hoje}.md"
python -m reports.relatorio

echo ""
echo "== Painel visual =="
python dashboard.py

echo ""
echo ">> Concluído. Relatório em relatorio_${data_hoje}.md, painel em dashboard.html."
echo "   Relatório mensal analítico: python -m reports.relatorio_mensal (rode 1x/mês)."
