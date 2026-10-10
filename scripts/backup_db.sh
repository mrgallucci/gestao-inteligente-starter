#!/usr/bin/env bash
# Backup lógico do PostgreSQL/Supabase usado pelo Gestão Inteligente.
#
# Uso:
#   DATABASE_URL='postgresql+psycopg://...' ./scripts/backup_db.sh [pasta_destino]
#
# Gera <pasta>/gestao-inteligente-AAAAMMDD-HHMMSS.dump (formato custom do pg_dump).
# Requer pg_dump instalado (pacote postgresql-client), com versão >= a do servidor.
# Guarde os backups FORA do servidor da aplicação e teste a restauração periodicamente.
#
# Uploads locais (backend/uploads) NÃO fazem parte do dump: copie essa pasta junto
# (ou migre para storage persistente com backup próprio).
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "Defina DATABASE_URL." >&2
  exit 1
fi

DEST="${1:-./backups}"
mkdir -p "$DEST"

# pg_dump não entende o prefixo do SQLAlchemy.
PG_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"
FILE="$DEST/gestao-inteligente-$(date +%Y%m%d-%H%M%S).dump"

pg_dump --format=custom --no-owner --no-privileges --file="$FILE" "$PG_URL"
echo "Backup gerado: $FILE"
