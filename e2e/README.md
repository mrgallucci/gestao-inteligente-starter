# E2E (Playwright) — Gestão Inteligente 2.1.0-rc.1

Cobre: Login admin → Produto → Curso → Lead → Venda Paga → Matrícula, e Produto sem Curso.

> **Status:** escrito na 2.1.0-rc.1, **ainda não executado** (o ambiente de desenvolvimento
> não tinha npm/navegador). Os seletores podem precisar de ajuste na primeira execução.

Use SEMPRE um banco descartável (o teste cria registros e depende do `bootstrap-admin`,
que só funciona com banco sem usuários):

```bash
# 1) sobe tudo com banco descartável
CI_JWT_SECRET=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))") \
  docker compose -f docker-compose.yml -f docker-compose.ci.yml up --build -d --wait
# 2) roda o E2E
cd e2e && npm ci && npm run install:browsers && npm test
```

Variáveis opcionais: `E2E_BASE_URL`, `E2E_API_URL`, `E2E_ADMIN_EMAIL`, `E2E_ADMIN_PASSWORD`.
O E2E fica em pasta própria para não alterar o `package-lock.json` do frontend.

## Lockfile (instalação determinística)

O CI usa `npm ci` e **exige `e2e/package-lock.json` versionado**. O lockfile não pôde ser
gerado no ambiente que produziu a 2.1.0-rc.4 (sem acesso ao registry npm) e **não foi
fabricado à mão**. Gere-o uma única vez, sem alterar versões (`package.json` fixa
`@playwright/test` em `1.55.0`), e faça commit:

```bash
cd e2e && npm install --package-lock-only && git add package-lock.json
```

Enquanto o arquivo não existir, o job `e2e` falha de propósito com mensagem explicativa
(o job é `continue-on-error` — temporário, até a primeira execução verde aprovada pela gerência).
