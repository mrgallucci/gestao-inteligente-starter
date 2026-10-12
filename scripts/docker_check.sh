#!/usr/bin/env bash
# Valida o Docker de ponta a ponta com um PostgreSQL descartável:
#   1. docker compose config   (YAML/variáveis válidos)
#   2. docker compose build    (imagens do backend e do frontend)
#   3. docker compose up --wait (migrations no start + healthchecks)
#   4. smoke: bootstrap do admin, login pelo BFF (cookie HttpOnly), rota protegida
#      pelo BFF, RBAC e scripts/smoke_test.sh
#
# Uso (na raiz do projeto, com Docker + Compose v2 instalados):
#   ./scripts/docker_check.sh
#
# Não toca em dados reais: sobe um banco novo e remove tudo ao final.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.ci.yml)
API=http://127.0.0.1:8000
APP=http://127.0.0.1:3000
ADMIN_EMAIL="admin-ci@exemplo.local"
ADMIN_PASSWORD="senha-ci-$(date +%s)-forte"
CREATED_ENV=""

cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then
    echo "--- logs do backend ---"
    "${COMPOSE[@]}" logs --tail=80 backend 2>/dev/null || true
    echo "--- logs do frontend ---"
    "${COMPOSE[@]}" logs --tail=40 frontend 2>/dev/null || true
  fi
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  [ -n "$CREATED_ENV" ] && rm -f backend/.env
  exit "$status"
}
trap cleanup EXIT

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  CREATED_ENV=1
fi

CI_JWT_SECRET="$(head -c 48 /dev/urandom | base64 | tr -d '\n=+/')"
export CI_JWT_SECRET

step() { echo; echo "==> $*"; }
fail() { echo "FALHA: $*" >&2; exit 1; }

expect_status() {
  # expect_status "descrição" esperado curl-args...
  local label="$1" expected="$2"
  shift 2
  local got
  got="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$@")" || true
  [ "${got:-000}" = "$expected" ] || fail "$label: esperado $expected, obtido ${got:-000}"
  echo "  OK    $label"
}

step "docker compose config"
"${COMPOSE[@]}" config -q

step "docker compose build"
"${COMPOSE[@]}" build

step "docker compose up --wait"
"${COMPOSE[@]}" up -d --wait --wait-timeout 240

step "Migrations aplicadas no PostgreSQL"
CURRENT="$("${COMPOSE[@]}" exec -T backend alembic current 2>&1)"
echo "$CURRENT"
echo "$CURRENT" | grep -q "(head)" || fail "alembic current não está no head"
"${COMPOSE[@]}" exec -T backend alembic check

step "Saúde"
expect_status "API /health" 200 "$API/health"
expect_status "API /health/database" 200 "$API/health/database"
expect_status "Frontend /login" 200 "$APP/login"

step "Primeiro administrador e sessão pelo BFF"
expect_status "bootstrap-admin" 201 -X POST "$API/api/auth/bootstrap-admin" \
  -H 'Content-Type: application/json' \
  -d "{\"nome\":\"Admin CI\",\"email\":\"$ADMIN_EMAIL\",\"senha\":\"$ADMIN_PASSWORD\"}"
expect_status "bootstrap-admin repetido" 409 -X POST "$API/api/auth/bootstrap-admin" \
  -H 'Content-Type: application/json' \
  -d "{\"nome\":\"Outro\",\"email\":\"outro@exemplo.local\",\"senha\":\"$ADMIN_PASSWORD\"}"

HEADERS="$(curl -s -D - -o /dev/null --max-time 20 -X POST "$APP/api/session/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"senha\":\"$ADMIN_PASSWORD\"}")"
echo "$HEADERS" | head -1 | grep -q " 200" || fail "login pelo BFF não retornou 200"
COOKIE_LINE="$(echo "$HEADERS" | tr -d '\r' | grep -i '^set-cookie: gi_access_token=' || true)"
[ -n "$COOKIE_LINE" ] || fail "cookie gi_access_token não foi definido"
echo "$COOKIE_LINE" | grep -qi 'httponly' || fail "cookie sem HttpOnly"
echo "$COOKIE_LINE" | grep -qi 'secure' || fail "cookie sem Secure em produção"
echo "  OK    cookie HttpOnly + Secure"
TOKEN="$(echo "$COOKIE_LINE" | sed -E 's/^[Ss]et-[Cc]ookie: gi_access_token=([^;]*).*/\1/')"

expect_status "BFF /api/session/me com cookie" 200 -H "Cookie: gi_access_token=$TOKEN" "$APP/api/session/me"
expect_status "BFF /api/backend/api/leads com cookie" 200 -H "Cookie: gi_access_token=$TOKEN" "$APP/api/backend/api/leads"
expect_status "BFF /api/backend/api/leads sem cookie" 401 "$APP/api/backend/api/leads"
expect_status "Página protegida (/leads) responde com cookie" 200 -H "Cookie: gi_access_token=$TOKEN" "$APP/leads"

step "smoke_test.sh"
API_URL="$API" FRONTEND_URL="$APP" ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  ./scripts/smoke_test.sh

echo
echo "Docker validado: config, build, up, migrations, healthchecks, sessão e smoke test."
