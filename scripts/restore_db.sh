#!/usr/bin/env bash
# Restaura um backup gerado por backup_db.sh.
#
# Uso:
#   DATABASE_URL='postgresql+psycopg://...' ./scripts/restore_db.sh arquivo.dump
#
# ATENÇÃO: apaga e recria os objetos do banco indicado. Restaure primeiro em um banco
# de teste. Depois confira com `alembic current` (deve apontar para o head atual).
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ] || [ -z "${1:-}" ]; then
  echo "Uso: DATABASE_URL=... $0 arquivo.dump" >&2
  exit 1
fi

PG_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"

echo "Isto vai SUBSTITUIR os dados do banco de destino."
read -r -p "Digite RESTAURAR para continuar: " confirm
[ "$confirm" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }

pg_restore --clean --if-exists --no-owner --no-privileges --dbname="$PG_URL" "$1"
echo "Restauração concluída. Rode: cd backend && alembic current"
