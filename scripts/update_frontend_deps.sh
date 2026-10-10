#!/usr/bin/env bash
# Atualização/validação controlada das dependências do frontend.
# Requer acesso ao registry npm. Não usa `npm audit fix --force` e não usa
# `npm audit fix --omit=dev`, pois esse comando pode remover devDependencies
# do node_modules antes de typecheck/lint/build.
set -euo pipefail

cd "$(dirname "$0")/../frontend"

echo "==> Fixando Next.js e eslint-config-next em 16.3.8"
npm install --save-exact --package-lock-only next@16.3.8 eslint-config-next@16.3.8

echo "==> Aplicando overrides de produção já definidos em package.json"
npm install --package-lock-only

echo "==> Instalação limpa a partir do lockfile"
rm -rf node_modules
npm ci

echo "==> Auditoria de produção (falha com high/critical)"
npm audit --omit=dev --audit-level=high

echo "==> Auditoria completa (informativa; devDependencies podem ter advisories)"
npm audit || true

echo "==> typecheck, lint e build"
npm run typecheck
npm run lint
npm run build

echo
echo "Concluído. Versões resolvidas:"
npm ls next sharp source-map-js eslint-config-next 2>/dev/null || true
