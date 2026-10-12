# Validação

Este arquivo separa o que foi **verificado de fato** do que **ainda precisa ser executado**. Não marque como aprovado o que não foi rodado.

## Histórico

### Reconstrução 2.0.0 (2026-10-07) — declarado na época
Compilação Python, migration em SQLite limpo, smoke test de API (30 verificações), análise sintática de 44 arquivos TS/TSX. **Ressalva da auditoria de 2026-10-09:** o registro dizia "`alembic check` sem operações pendentes", mas o model `Lead` tinha a coluna `area_profissional` ausente da migration inicial — a instalação limpa falhava nas consultas de Leads. Corrigido na 2.0.1 (migration `9c4e1a7b2d10`). Trate os resultados antigos como não confiáveis.

### Auditoria 2.0.1 (2026-10-09)

O ambiente da auditoria não alcançava PyPI/npm, então **dependências não puderam ser instaladas** e nada que exija FastAPI, SQLAlchemy, Alembic ou Next rodou.

Verificado:
- Leitura completa do backend e do BFF/config do frontend.
- `py_compile` e ruff (F, E9) em `main.py`, `legacy_upgrade.py`, `seed_sarglab.py`, migrations e testes — sem nomes indefinidos.
- 44 arquivos TS/TSX: 0 erros de sintaxe; 0 imports `@/…` ausentes.
- `npm ci --dry-run --offline`: `package.json` e `package-lock.json` coerentes.
- `docker-compose.yml` e `ci.yml` são YAML válidos; scripts passam em `bash -n`; `smoke_test.sh` executado contra servidor falso (sucesso e falha).
- Rotas chamadas pelo frontend × rotas do backend: nenhuma divergência (46 rotas, 43 referências).

**Não executado — fazer na homologação (ou deixar o CI fazer):**

| Comando | Onde | Resultado esperado |
|---|---|---|
| `pip install -r requirements-dev.txt && python -m pytest` | `backend/` | todos os testes passam |
| `alembic upgrade head && alembic check` | `backend/`, banco limpo | sem operações pendentes |
| `npm ci && npm run typecheck && npm run build` | `frontend/` | sem erros |
| `npm run lint` | `frontend/` | revisar avisos (não bloqueia) |
| `docker compose up --build` | raiz | backend `healthy`, frontend responde em `:3000` |
| `scripts/smoke_test.sh` | contra o ambiente publicado | sem falhas |

Registre aqui o resultado real quando rodar:

```text
Data:
Commit/versão:
pytest:
alembic upgrade head / check:
npm run build:
docker compose:
smoke_test.sh:
Observações:
```

### Validação local da 2.0.1 — informada pelo time (2026-10-09)

Executada pelo time em ambiente local (Python 3.14.7, PostgreSQL, Node/npm). Resultado informado, não reproduzido pela auditoria:

| Verificação | Resultado informado |
|---|---|
| `python -m pytest` | 151 passed, 0 failed, 1 warning não bloqueante |
| `alembic heads` / `upgrade head` / `current` | `9c4e1a7b2d10 (head)`; migration 387ce60e2db5 → 9c4e1a7b2d10 aplicada em PostgreSQL |
| `alembic check` | No new upgrade operations detected |
| `npm ci` / `npm run typecheck` / `npm run build` | aprovados |
| `npm run lint` | **4 erros + 1 warning** (corrigidos na RC, abaixo) |
| `npm audit --omit=dev` | **3 vulnerabilidades de produção (1 critical, 2 high)**: Next.js, sharp, source-map-js |
| `docker compose config/build/up` | não executado (Docker ausente no ambiente local) |

### RC 2.0.2-rc.1 — alterações feitas e estado de validação

O ambiente onde a RC foi preparada **não alcança PyPI/npm nem tem Docker**. Nada abaixo foi executado por quem escreveu o código; a coluna "Estado" é literal.

| Item | O que foi feito | Estado |
|---|---|---|
| ESLint (4 erros + 1 warning) | Reestruturação dos effects (ver `CHANGELOG.md`), sem `eslint-disable` | **Não verificado** — só sintaxe TS (44 arquivos, 0 erros). Rodar `npm run typecheck && npm run lint && npm run build` |
| N1–N4 | Implementados em `backend/main.py`; 11 testes novos em `tests/test_business_rules.py` | **Não executado** — `py_compile`/ruff ok. Esperado: 151 anteriores + 11 novos = 162 passando |
| Vulnerabilidades npm (Next crítico, sharp, source-map-js) | **NÃO corrigidas neste pacote**: atualizar o lockfile exige o registry npm. Fornecido `scripts/update_frontend_deps.sh` (Next ≥ 16.3.6, `npm audit fix --omit=dev`, sem `--force`) e gate no CI (`npm audit --omit=dev --audit-level=high`) | **Pendente** — a RC não pode ser liberada antes de rodar o script e fazer commit de `package.json`/`package-lock.json` |
| Docker build/up | `docker-compose.ci.yml`, `scripts/docker_check.sh`, healthcheck do frontend e job `docker` no CI | **Não executado** — `bash -n` e YAML válidos apenas |

Referência histórica da RC1: o advisory crítico de `ImageResponse` era corrigido em 16.3.6; a RC2 fixa **16.3.8**, que inclui correções de segurança posteriores ([aicybr — Next.js 16.3.6 / CVE-2026-94545](https://aicybr.com/blog/nextjs-16-3-6-cve-2026-94545-imageresponse-rce); [Next.js — August 2026 security update](https://nextjs.org/blog/nextjs-security-release-august-2026-update)). Na RC1, o lockfile estava em 16.3.5; na RC2 ele foi alinhado a 16.3.8.

**Critério de devolução da RC (preencher com resultados reais):**

```text
Data:
Commit/versão:
pytest (esperado 162):
alembic upgrade head / check:
npm ci:
npm audit --omit=dev:
npm audit:
npm run typecheck:
npm run lint:
npm run build:
scripts/docker_check.sh (config/build/up/smoke):
```

## Higiene do pacote

O pacote entregue não inclui `.env`, `.venv`, `node_modules`, `.next`, bancos locais, `__pycache__` nem arquivos de upload.

### RC 2.0.2-rc.2 — gerência de desenvolvimento (2026-10-09)

Alterações feitas sem expansão de escopo:

- Next.js e `eslint-config-next` fixados em 16.3.8.
- `sharp` fixado em 0.35.5 e `source-map-js` em 1.2.2 por `overrides`.
- Lockfile alinhado às versões acima.
- Script de atualização corrigido para não remover as devDependencies antes de typecheck/lint/build.

Validação confirmada pelo ambiente local do projeto antes desta revisão:

| Verificação | Resultado confirmado |
|---|---|
| `python -m pytest` | **162 passed, 0 failed, 1 warning não bloqueante** |
| N1–N4 | cobertas pelos 11 testes de `test_business_rules.py` |

Validação estática feita nesta revisão:

- Python: `compileall` e parse AST sem erros (19 arquivos `.py`).
- `package.json` e `package-lock.json`: versões-alvo e dependências de segurança alinhadas por inspeção estrutural.
- Scripts shell: sintaxe validada com `bash -n`.

Ainda precisa de execução em ambiente com acesso ao registry npm e Docker antes de promover a release:

```text
npm ci
npm audit --omit=dev --audit-level=high
npm run typecheck
npm run lint
npm run build
./scripts/docker_check.sh
```

Não foi implementado nenhum item de roadmap (WhatsApp/e-mail real, IA generativa, ERP ou multiempresa).


### RC 2.0.2-rc.3 — correção do último erro de lint (2026-10-10)

Resultados executados pelo usuário na rc.2 imediatamente antes desta revisão:

| Verificação | Resultado |
|---|---|
| `npm audit --omit=dev --audit-level=high` | **0 vulnerabilidades** |
| `npm run typecheck` | **aprovado** |
| `npm run build` | **aprovado**; Next.js 16.3.8; 22/22 rotas |
| `npm run lint` | **1 erro** em `course-content-admin.tsx`, linha 287 (`react-hooks/set-state-in-effect`) |
| `python -m pytest` | **162 passed, 0 failed, 1 warning não bloqueante** |

Correção aplicada nesta rc.3:
- o `useEffect` de `course-content-admin.tsx` não chama mais `loadContents()` diretamente; a busca é iniciada via Promise e os `setState` ficam nos callbacks assíncronos, com flag de cancelamento no cleanup.
- não houve `eslint-disable`, mudança de regra de negócio ou módulo novo.

Ainda é necessário reexecutar na rc.3:
```text
npm ci
npm audit --omit=dev --audit-level=high
npm run typecheck
npm run lint
npm run build
```

Docker/CI segue pendente de ambiente com Docker.


### RC 2.1.0-rc.1 — estado de validação (2026-10-10)

Base: 2.0.2-rc.3 (backend informado como 162 testes passando na rc.2; frontend: audit 0, typecheck e build aprovados na rc.2, lint corrigido na rc.3 — resultados informados pelo time, não reproduzidos aqui).

**Verificado neste ambiente (sem PyPI/npm/Docker/navegador):**
- `py_compile` e `ruff --select F,E9` em todo o backend, incluindo testes novos: sem erros.
- Sintaxe de 46 arquivos TS/TSX (transpile): 0 erros.
- `ci.yml` é YAML válido (4 jobs: backend, frontend, docker, e2e).

**NÃO executado (precisa de execução real/CI):**

| Verificação | Observação |
|---|---|
| `pytest` | testes novos: `test_product_course_delivery.py`, `test_email_automation.py`, `test_data_cleanup.py` — **nunca rodaram**; podem exigir pequenos ajustes |
| `alembic upgrade head` / drift | nova migration `b7d2f4a91c33` (tabela `email_logs`) — o teste de drift deve validar model × migration |
| `npm ci`, audit, typecheck, lint, build | `package.json`/lockfile do frontend **não foram alterados**; mudanças são só de código/CSS (tipos e regras de lint não verificados) |
| Docker / CI | job `e2e` novo, não bloqueante |
| E2E Playwright | escrito, nunca executado; seletores podem precisar de ajuste |
| Screenshots / revisão visual | **não produzidos** (não foi possível subir o Next aqui) |
| E-mail real | nenhum e-mail enviado; testes usam provedor simulado |
| Limpeza real | nenhuma limpeza executada; ver `docs/LIMPEZA_DADOS.md` |

```text
Data:
Commit/versão: 2.1.0-rc.1
pytest:
alembic upgrade head / check:
npm ci / audit / typecheck / lint / build:
docker_check.sh:
CI (GitHub Actions):
E2E:
Observações:
```

### RC 2.1.0-rc.2 — estado de validação (2026-10-10)

**Informado pela gerência (ambiente independente, não reproduzido aqui), sobre a 2.1.0-rc.1:** 162 testes anteriores + 30 novos passaram em rodadas separadas. *(Na rc.2 o total de novos passou a 38 — ver rc.3 abaixo.)*

**Alterações da rc.2 ainda NÃO executadas por ninguém:** testes novos/alterados da rc.2 (`test_email_automation.py` +5, `test_product_course_delivery.py` +3 e reescrita de asserções de entrega, `test_rbac.py` — duplicado agora devolve 201), mudanças de frontend (tela de Vendas, formulário de venda, `BrandMark` com `next/image`, assets em `public/brand`, `app/icon.png`).

Verificado neste ambiente: `py_compile`, `ruff --select F,E9`, sintaxe dos TS/TSX, resolução de imports `@/…`, `npm ci --dry-run --offline` (lockfile intacto).

**Para a devolução da RC (a executar em ambiente com acesso):** `pytest` completo; `alembic upgrade head`/`check` em PostgreSQL; `npm ci`, `npm audit --omit=dev --audit-level=high`, `typecheck`, `lint`, `build`; `scripts/docker_check.sh`; CI; Playwright.

**Gate:** o job `e2e` do CI é `continue-on-error` **somente até a primeira execução verde**; depois remover a flag para torná-lo obrigatório antes da versão estável. Não promover para estável sem homologação manual (`docs/HOMOLOGACAO.md`).

```text
Data:
Commit/versão: 2.1.0-rc.2
pytest:
alembic upgrade head / check (PostgreSQL):
npm ci / audit / typecheck / lint / build:
docker_check.sh:
CI:
Playwright:
Homologação manual:
```

### RC 2.1.0-rc.3 — estado de validação (2026-10-10)

**Informado pela gerência (ambiente independente, não reproduzido aqui), sobre a rc.2:** backend com **200 testes aprovados** = 162 anteriores + **38** novos (`test_product_course_delivery` 12, `test_email_automation` 17, `test_data_cleanup` 9). A menção anterior a "30 novos" valia apenas para a rc.1.

**Alterações da rc.3 (nunca executadas por ninguém):** rótulo "Matrícula não gerada" + `aviso` (backend, 1 teste ampliado), SVGs oficiais (`BrandMark`, login, favicon `app/icon.svg`), tokens em `globals.css`.

**Tentado neste ambiente e NÃO possível (sem acesso à rede de pacotes):** `npm ci` (registry inacessível, `ENOTFOUND`; cache offline vazio), instalação das dependências Python (PyPI sem acesso), `docker` (CLI presente, daemon ausente). Nada foi contornado. Portanto **nenhum resultado real** de: `pytest`, `alembic upgrade head`/PostgreSQL, `npm ci`, audit, typecheck, lint, build, Docker, CI, Playwright.

Verificado estaticamente: `py_compile`, `ruff F/E9`, sintaxe de 46 TS/TSX, imports `@/…`, `npm ci --dry-run --offline` (lockfile coerente), SVGs oficiais sem script/href/image embutido.

```text
Data:
Commit/versão: 2.1.0-rc.3
pytest (esperado: 200 + novas asserções):
alembic upgrade head / check (PostgreSQL):
npm ci / audit / typecheck / lint / build:
docker_check.sh:
CI:
Playwright (1ª execução verde → remover continue-on-error):
Homologação manual:
```


### RC 2.1.0-rc.4 — estado de validação (2026-10-11)

**Evidência independente informada pela gerência (rc.3):** 162 anteriores + 38 novos = 200 testes aprovados; migration `b7d2f4a91c33` consistente em banco limpo; Alembic head sem drift.

**Alterações da rc.4 (nunca executadas):** resposta pública uniforme do e-book; 4 testes novos (`test_email_automation.py`, esperado total 204); 4 testes existentes ajustados para obter o id do Lead pelo CRM; workflow `e2e` com `npm ci`.

**Verificado estaticamente:** `py_compile`, `ruff --select F,E9` (backend e testes), YAML do `ci.yml`.

**NÃO executado (sem PyPI/npm/registry/Docker neste ambiente):** `pytest`, Alembic/PostgreSQL, `npm ci`, audit, typecheck, lint, build, Docker, CI, Playwright. Nenhum teste é declarado aprovado por esta rodada.

**Pendência objetiva:** `e2e/package-lock.json` não existe — `npm install --package-lock-only` falhou por falta de acesso ao registry; não foi fabricado. Sem ele o job `e2e` falha com mensagem explícita (job ainda `continue-on-error`, temporário).

```text
Data:
Commit/versão: 2.1.0-rc.4
pytest (esperado 204):
alembic upgrade head / check (PostgreSQL):
npm ci / audit / typecheck / lint / build:
docker_check.sh:
CI:
Playwright (1ª execução verde → remover continue-on-error):
Homologação manual:
```
