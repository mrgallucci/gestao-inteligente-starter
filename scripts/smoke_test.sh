#!/usr/bin/env bash
# Smoke test pós-deploy do Gestão Inteligente.
#
# Uso:
#   API_URL=https://api.seu-dominio FRONTEND_URL=https://app.seu-dominio ./scripts/smoke_test.sh
#
# Opcional (valida login e RBAC com contas reais de homologação):
#   ADMIN_EMAIL=... ADMIN_PASSWORD=... VENDEDOR_EMAIL=... VENDEDOR_PASSWORD=...
#
# Não cria nem altera dados: só faz leituras.
set -u

API_URL="${API_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"
API_URL="${API_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

failures=0

check() {
  # check "descrição" "esperado" "obtido"
  if [ "$2" = "$3" ]; then
    echo "  OK    $1"
  else
    echo "  FALHA $1 (esperado $2, obtido $3)"
    failures=$((failures + 1))
  fi
}

status() {
  local code
  code="$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$@")" || true
  echo "${code:-000}"
}

json_field() {
  # json_field campo  (lê JSON do stdin)
  python3 -c "import json,sys; print(json.load(sys.stdin).get('$1',''))" 2>/dev/null
}

echo "== Infraestrutura =="
check "API /health" 200 "$(status "$API_URL/health")"
check "API /health/database" 200 "$(status "$API_URL/health/database")"
check "Frontend /login" 200 "$(status "$FRONTEND_URL/login")"

echo "== Proteção de rotas (sem login) =="
check "API /api/leads exige token" 401 "$(status "$API_URL/api/leads")"
check "API /api/users exige token" 401 "$(status "$API_URL/api/users")"
check "BFF /api/backend/api/leads exige sessão" 401 "$(status "$FRONTEND_URL/api/backend/api/leads")"
check "BFF /api/session/me sem sessão" 401 "$(status "$FRONTEND_URL/api/session/me")"

login_token() {
  curl -s --max-time 15 -X POST "$API_URL/api/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$1\",\"senha\":\"$2\"}" | json_field access_token
}

if [ -n "${ADMIN_EMAIL:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
  echo "== Admin =="
  token="$(login_token "$ADMIN_EMAIL" "$ADMIN_PASSWORD")"
  if [ -z "$token" ]; then
    echo "  FALHA login do admin"
    failures=$((failures + 1))
  else
    auth=(-H "Authorization: Bearer $token")
    check "admin /api/auth/me" 200 "$(status "${auth[@]}" "$API_URL/api/auth/me")"
    check "admin /api/dashboard/summary" 200 "$(status "${auth[@]}" "$API_URL/api/dashboard/summary")"
    check "admin /api/finance/summary" 200 "$(status "${auth[@]}" "$API_URL/api/finance/summary")"
    check "admin /api/users" 200 "$(status "${auth[@]}" "$API_URL/api/users")"
  fi
fi

if [ -n "${VENDEDOR_EMAIL:-}" ] && [ -n "${VENDEDOR_PASSWORD:-}" ]; then
  echo "== Vendedor =="
  token="$(login_token "$VENDEDOR_EMAIL" "$VENDEDOR_PASSWORD")"
  if [ -z "$token" ]; then
    echo "  FALHA login do vendedor"
    failures=$((failures + 1))
  else
    auth=(-H "Authorization: Bearer $token")
    check "vendedor /api/leads" 200 "$(status "${auth[@]}" "$API_URL/api/leads")"
    check "vendedor /api/finance/summary bloqueado" 403 "$(status "${auth[@]}" "$API_URL/api/finance/summary")"
    check "vendedor /api/users bloqueado" 403 "$(status "${auth[@]}" "$API_URL/api/users")"
  fi
fi

echo
if [ "$failures" -eq 0 ]; then
  echo "Smoke test concluído sem falhas."
else
  echo "Smoke test com $failures falha(s)."
  exit 1
fi
