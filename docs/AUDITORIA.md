# Auditoria técnica — Gestão Inteligente 2.0.0 → 2.0.1

Data: 2026-10-09. Base: ZIP `gestao-inteligente-starter-entrega` + briefing oficial "Briefing Comercial e Plano de Conclusão do Sistema". O briefing foi usado como fonte de verdade: nada do roadmap foi implementado, nenhum módulo novo foi criado, o posicionamento comercial e a stack não foram alterados.

## 1. Como a auditoria foi feita — e o que NÃO foi possível executar

O ambiente em que a auditoria rodou **não tem acesso ao PyPI nem ao npm** (política de rede). Consequência direta:

| Verificação | Status |
|---|---|
| Leitura completa do backend (`main.py`, models, migrations, scripts) e do BFF/libs/config do frontend | ✅ feita |
| Compilação/sintaxe Python (`py_compile`) e análise estática (ruff, regras F/E9: nomes indefinidos, imports) | ✅ feita |
| Sintaxe de 44 arquivos TS/TSX + resolução dos imports `@/…` | ✅ feita (0 erros) |
| `package.json` × `package-lock.json` consistentes (`npm ci --dry-run --offline`) | ✅ feita |
| YAML do compose e do CI, `bash -n` e execução do smoke test contra um servidor falso | ✅ feita |
| `pip install`, `alembic upgrade head`, **`pytest`** | ❌ **não executado** |
| `npm ci` real, `tsc --noEmit`, **`next build`**, `eslint` | ❌ **não executado** |
| `docker compose build/up` | ❌ **não executado** |

**Os testes novos foram escritos com cuidado e conferidos contra o código, mas nunca rodaram.** Podem conter ajustes a fazer. O primeiro passo da homologação é rodar `pytest` e `npm run build` (ou abrir um push/PR: o CI em `.github/workflows/ci.yml` faz tudo isso).

## 2. Achados corrigidos

| # | Sev. | Achado | Correção |
|---|---|---|---|
| A1 | **Crítica** | A coluna `leads.area_profissional` existe no model e é usada pelo CRM e pelo endpoint público de e-book, mas **não estava na migration inicial** nem no `legacy_upgrade.py`. Em instalação limpa, `alembic upgrade head` criava `leads` sem a coluna e qualquer consulta a Leads falhava. | Nova migration idempotente `9c4e1a7b2d10`; coluna adicionada ao `legacy_upgrade.py`; testes de regressão (`test_health_and_migrations.py`). |
| A2 | Alta | Erros de validação (HTTP 422) devolviam `detail` como lista de objetos; as telas fazem `setMensagem(data.detail)` e renderizam o valor, o que quebra o React ("Objects are not valid as a React child"). | Handler que devolve `detail` em texto (`Dados inválidos — campo: motivo`). |
| A3 | Média | Admin abrindo conteúdo ou atualizando progresso de uma matrícula **suspensa** (reembolso/cancelamento) a reativava silenciosamente ("Em andamento"), quebrando a integração Venda → Financeiro → LMS. | Matrícula suspensa só volta pelo financeiro (venda Paga). Teste de regressão. |
| A4 | Média | `JWT_SECRET_KEY` com o texto placeholder do `.env.example` (ou curta) era aceita. | Com `APP_ENV=production` a API não sobe sem chave ≥ 32 caracteres e diferente do placeholder. |
| A5 | Média | CORS com `localhost:5500` fixo em qualquer ambiente e `allow_methods/headers = *` com credenciais. | Origens vêm de `FRONTEND_URL` + `CORS_ORIGINS`; 5500 só em desenvolvimento; métodos e cabeçalhos explícitos. |
| A6 | Média | `url_conteudo` aceitava qualquer texto e é renderizado como `href` para alunos (`javascript:`/`data:`). | Só `http://` ou `https://`. |
| A7 | Baixa | Login respondia mais rápido para e-mail inexistente (enumeração de usuários por tempo). | Verificação Argon2 descartável quando o e-mail não existe. |
| A8 | Baixa | Sem validação básica: preço/custo negativos, nomes vazios, `tipo_cliente` livre, e-mail sem formato, idade/equipe absurdas. | Validação Pydantic (compatível com o que os formulários já enviam). |
| A9 | Baixa | Cookie de sessão com 8 h fixas, independente de `ACCESS_TOKEN_EXPIRE_MINUTES`. | Login devolve `expires_in`; o BFF usa o mesmo prazo (fallback 8 h). |
| A10 | Baixa | `package.json` com `"latest"` em todas as dependências; `npm run lint` sem configuração ESLint (falhava sempre); sem script de typecheck. | Versões fixadas nas do lockfile (lock coerente); `eslint.config.mjs`; `npm run typecheck`. |
| A11 | Baixa | Sem cabeçalhos de segurança no Next. | `next.config.mjs` (nosniff, X-Frame-Options, Referrer-Policy, Permissions-Policy). CSP **não** foi adicionada (exige teste em navegador). |
| A12 | Baixa | `/health/database` retornava 500 com banco fora do ar. | 503 sem detalhes de conexão. |
| A13 | Operação | Compose sem healthcheck, restart e rotação de logs; `frontend/public/` vazio não sobrevive ao Git e o Dockerfile faz `COPY public`. | Healthcheck, `restart`, `json-file` com rotação, `public/.gitkeep`. |
| A14 | Processo | O projeto não tinha nenhum teste automatizado. | Suíte `pytest` (seção 5) + CI. |
| A15 | Documentação | `VALIDACAO.md` afirmava "alembic check limpo" e smoke test aprovado, o que o código contradizia (A1). | `VALIDACAO.md` reescrito com o que foi e o que não foi verificado. |

## 3. Pontos conhecidos que NÃO foram alterados (decisão registrada)

**Segurança / produção**

- **D1 — `/uploads` é público.** O FastAPI serve `backend/uploads` sem autenticação. Os nomes são UUID de 128 bits (não adivinháveis), mas quem tem o link continua acessando o arquivo, inclusive um aluno cuja matrícula foi suspensa. É a "limitação do upload local" que o briefing permite aceitar formalmente na primeira entrega (instância única). Para fechar: storage privado (S3/Supabase Storage com URL assinada) — está em `ROADMAP.md`.
- **D2 — Endpoint público do e-book** (`POST /api/public/leads/ebook`): sem rate limit/captcha, e o 409 revelava se um e-mail já estava cadastrado (**corrigido na 2.1.0-rc.4**: resposta idêntica 201 para e-mail novo e existente). Mitigar no proxy reverso (limite por IP). Se a página do e-book rodar em outro domínio, inclua-o em `CORS_ORIGINS`.
- **D3 — Login sem rate limit/bloqueio.** Aplicar limite no proxy reverso. Um bloqueio por conta na aplicação foi evitado de propósito (permitiria bloquear o admin de fora).
- **D4 — `bootstrap-admin` fica aberto até existir o primeiro usuário.** Crie o administrador imediatamente após o primeiro deploy (ver `DEPLOY.md`).
- **D5 — JWT sem revogação.** O logout apaga o cookie, mas o token continua válido até expirar (8 h por padrão). Desativar o usuário bloqueia o token na hora (o backend consulta o banco a cada chamada).
- **D6 — Containers rodam como root; TLS não faz parte do compose** (use proxy reverso/plataforma com HTTPS).

**Regras de negócio N1–N4 — decididas e implementadas na 2.0.2-rc.1** (com testes em `backend/tests/test_business_rules.py`; detalhes no `CHANGELOG.md`):

- N1 — Venda Paga não rebaixa Lead em "Pós-venda".
- N2 — Nova compra Paga restaura matrícula suspensa.
- N3 — Reembolso/cancelamento só suspende sem outra venda Paga do mesmo curso.
- N4 — Restauração preserva "Concluído"/"Em andamento".

**Engenharia (não refatorada, conforme o briefing: "não reescrever módulos que funcionam")**

- `main.py` monolítico (~4,7 mil linhas) e algumas listagens com consultas por item (ex.: `/api/my/enrollments`). Aceitável no volume de um piloto; revisar após uso real.
- `@types/node` 26 no lockfile enquanto o runtime é Node 22 — funciona, mas vale alinhar na próxima atualização de dependências.
- E2E de navegador (Playwright) não incluído: os fluxos críticos estão cobertos por testes de API de ponta a ponta; o roteiro manual de telas está em `HOMOLOGACAO.md`.

## 4. Conferência com o briefing (seção 9 — "o que falta para considerar entregue")

| Item | Situação |
|---|---|
| Instalação limpa reproduzível | Backend/frontend: lockfile consistente e versões fixas; **aguarda execução real** |
| Banco por Alembic sem ajustes manuais | A1 corrigido; coberto por teste; **aguarda execução** |
| Build de produção do frontend | **Não executado aqui** — rodar `npm run build` (CI faz) |
| Testes automáticos dos fluxos principais | Escritos (API); **aguardam primeira execução** |
| Regressão de RBAC (admin/vendedor/aluno) | Coberta em `test_rbac.py` e `test_ownership.py` |
| Storage persistente ou limitação aceita | Limitação documentada (D1) |
| Ambiente de produção (domínio, banco, segredos, HTTPS) | Depende da conta de produção — guia em `DEPLOY.md` |
| Logs, monitoramento, backup | Logs rotacionados, healthchecks, `scripts/backup_db.sh`/`restore_db.sh`, `scripts/smoke_test.sh` |
| Documentação revisada | `README`, `DEPLOY`, `HOMOLOGACAO`, `ROADMAP`, `VALIDACAO`, `CHANGELOG` |
| Homologação com operação real do SargLab | Pendente (passo humano) |

Nada de WhatsApp/e-mail real, IA generativa, ERP, multiempresa ou novos módulos foi implementado.

## 5. Suíte de testes (`backend/tests`)

Rodam sobre SQLite temporário criado **pelas migrations** (não por `create_all`):

- `test_health_and_migrations.py` — `alembic upgrade head`, head único, **models × schema sem drift** (equivalente a `alembic check`), regressão A1.
- `test_auth.py` — bootstrap único, login, JWT adulterado/expirado, perfil vindo do banco, conta inativa, regras de usuários.
- `test_rbac.py` — matriz de rotas para admin, vendedor (403 em áreas administrativas) e aluno; criação restrita; endpoint público do e-book.
- `test_ownership.py` — aluno não acessa matrícula alheia (GET/access/open/progress).
- `test_crm_flow.py` — Lead, edição, funil, interações, follow-ups/agenda, campanha e atribuição, analytics.
- `test_sales_lms_flow.py` — venda paga → matrícula automática; reembolso/cancelamento suspende; Pago restaura; progresso e conclusão; financeiro; regressão A3.
- `test_uploads_and_validation.py` — uploads (tipos, 50 MB, nome seguro), validações, URL de conteúdo.
- `test_security_config.py` — CORS e chave JWT em produção.

Rodar: `cd backend && pip install -r requirements-dev.txt && python -m pytest`.
