# Integração do site sargtech.com.br (rodada de integração)

Status: **homologação local pendente**. Nada foi publicado. Variáveis do Render não foram tocadas.

## O que foi alterado no backend (branch `integracao-site-v6`)

| Item | Mudança |
|---|---|
| Atribuição/UTM | Tabela nova `lead_touchpoints` (modelo `LeadTouchpoint`, migration `c3a8e5d1f402`, down_revision `b7d2f4a91c33`). Guarda utm_source/medium/campaign/content/term, referrer, landing_url, canal, origem e vínculo opcional com `Campaign`. Um lead pode ter vários toques; o primeiro é a origem. |
| Leitura | `GET /api/leads/{id}/touchpoints` (admin, vendedor) e `GET /api/marketing-analytics/attribution?dias=` (admin). |
| E-book | `POST /api/public/leads/ebook` aceita os campos novos (opcionais, retrocompatível) e grava o toque nos dois ramos (lead novo e existente). Resposta 201 uniforme, como antes. |
| Contato | `POST /api/public/leads/contact`, endpoint separado. Origens aceitas: `site-contato`, `sarglab-cursos-aviso` (gravada como `site-sarglab-aviso`). Cria/reutiliza o lead, registra Interaction "Contato pelo site" e o toque (canal `contato`). Resposta 201 uniforme. |
| Rate limit | Dependência `public_rate_limit`, desligada por padrão (`PUBLIC_RATE_LIMIT_PER_MIN=0`). |
| Não alterado | RBAC, LMS, Sale, Enrollment, Product, Course, User. Nenhuma tabela existente foi modificada. |

`backend-reference/001_sargtech_commerce.sql` **não foi aplicado** e foi removido do pacote do site (duplicava Product, Sale, Course, CourseContent, Enrollment, ContentProgress e User).

## Status dos testes (honesto)

- **Não executado:** a suíte real (`pytest`) e `alembic upgrade head` / `alembic check` **não rodaram** neste ambiente: o pypi.org está bloqueado pela política de rede e pytest/fastapi/sqlalchemy/alembic/argon2 não estão instalados. Não houve contorno.
- Executado: `py_compile` em `main.py`, `models.py`, migration e `test_public_leads_attribution.py` (sintaxe apenas).
- Escrito e **não executado**: `backend/tests/test_public_leads_attribution.py` (~20 testes: persistência de UTM nos dois ramos do e-book, vínculo com campanha, contato com origem identificável, validações, uniformidade da resposta, rate limit, permissões das rotas de leitura).
- Para rodar localmente:
  ```
  cd backend && pip install -r requirements-dev.txt
  pytest
  alembic upgrade head && alembic check
  ```
  Atenção ao teste de drift: o índice composto `ix_lead_touchpoints_utm` existe na migration **e** no modelo.

## Item 6 — RBAC/LMS: o que já existe e quais testes cobrem

Nenhuma alteração de código foi feita. O mapeamento abaixo é por leitura dos testes existentes; **não foram executados nesta sessão**.

| Requisito | Onde está coberto |
|---|---|
| Aluno não acessa o CRM admin | `tests/test_rbac.py` (rotas protegidas por `require_roles`) |
| Aluno vê só a própria matrícula | `tests/test_ownership.py`, `tests/test_sales_lms_flow.py` (`/api/me/enrollments`) |
| Matrícula suspensa bloqueia conteúdo | `tests/test_sales_lms_flow.py`, `tests/test_business_rules.py` (`validate_enrollment_access`) |
| Admin e vendedor mantêm acesso | `tests/test_rbac.py` |

Se algum falhar na execução local, o ajuste deve ser mínimo e feito sobre o resultado real.

## Item 9 — CORS

O código lê `FRONTEND_URL` + `CORS_ORIGINS`. Para o cutover basta o valor abaixo no Render, **somente com autorização**:
`CORS_ORIGINS=https://sarg-tech.github.io,https://sargtech.com.br,https://www.sargtech.com.br` (FRONTEND_URL=https://crm.sargtech.com.br já entra automaticamente)
Ordem: merge, migration, deploy do backend, homologação; só então a troca de CORS. Não ligar `TRUST_PROXY_HEADERS` em produção até validar o cabeçalho de IP no Render.

## Lacunas e riscos conhecidos

- `/uploads` é público sem autenticação (limitação D1 já documentada em `docs/AUDITORIA.md`).
- Não existe tela no frontend Next.js para a atribuição; apenas a API.
- Onboarding do aluno após pagamento: decidido (token de ativação, sem senha temporária); implementação pendente, ver `MERCADO_PAGO.md`.
