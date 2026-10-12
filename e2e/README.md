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

## Lockfile e `npm ci`

O CI usa `npm ci` (nunca `npm install`) e exige `e2e/package-lock.json` versionado, com
`@playwright/test` **1.55.1**. O lockfile foi gerado e versionado pela gerência no repositório
homologado; **não o recrie nem altere a versão**. Se o arquivo estiver ausente, o job falha de
propósito com mensagem explicativa.

## Sincronização dos testes (rc.5)

- **Login:** função `loginAsAdmin(page)` usada por todos os testes; só retorna depois de
  `expect(page).not.toHaveURL(/\/login/)` (cookie de sessão criado). Cada teste usa o seu `page`.
- **Criação de Curso:** o teste não depende da mensagem transitória do formulário (o
  `router.refresh()` remonta a árvore). Aguarda o `POST /api/backend/api/courses`, exige status 2xx
  e confirma o "Curso vinculado" em `/products`.
- **Banco descartável:** nunca aponte o E2E para base real/homologação.

O job `e2e` segue `continue-on-error: true` (temporário) até a primeira execução verde
aprovada pela gerência, que removerá a flag e reexecutará o workflow.
