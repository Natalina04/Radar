#!/usr/bin/env bash
# Backup do banco compartilhado antes de cada rodada de ingestão — controle
# de continuidade (COSO: Control Activities) contra perda/corrupção do dado
# já capturado. Mantém só os 10 backups mais recentes.
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${RADAR_DB_PATH:-}" ] && [ -f ".env" ]; then
    linha_db_path=$(grep -E '^RADAR_DB_PATH=' .env || true)
    if [ -n "$linha_db_path" ]; then
        export "$linha_db_path"
    fi
fi

db_path="${RADAR_DB_PATH:-$HOME/.radar/radar.db}"
backup_dir="$(dirname "$0")/backups"

if [ -f "$db_path" ]; then
    mkdir -p "$backup_dir"
    timestamp=$(date +%Y%m%d_%H%M%S)
    cp "$db_path" "$backup_dir/radar_${timestamp}.db"
    echo ">> Backup salvo em backups/radar_${timestamp}.db"
    ls -1t "$backup_dir"/radar_*.db 2>/dev/null | tail -n +11 | xargs -r rm --
else
    echo ">> Nenhum banco encontrado em $db_path ainda — pulando backup."
fi
