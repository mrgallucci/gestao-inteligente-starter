# Arquitetura

## Fluxo principal

```text
Campanha → Lead → CRM/Funil → Venda → Financeiro → Matrícula → Curso → Progresso → Analytics
```

## Autenticação

```text
Navegador
  → Next.js /api/session/login
  → FastAPI /api/auth/login
  → JWT
  → cookie HttpOnly no Next.js
```

Client Components não recebem o JWT. Eles chamam `/api/backend/...`, e o BFF adiciona `Authorization: Bearer <token>` no servidor.

Server Components usam `serverApi()` e `protectedJson()`.

## RBAC

- `admin`: visão estratégica e administrativa completa.
- `vendedor`: CRM, funil, follow-ups, vendas, omnichannel, automações e playbook do workshop.
- `aluno`: apenas sua área e suas matrículas.

A autorização relevante é feita no FastAPI. O menu do frontend é UX, não a fronteira de segurança.

## Banco

Tabelas principais:
- campaigns
- leads
- interactions
- products
- sales
- courses
- course_contents
- enrollments
- content_progress
- users

Alembic é a fonte de verdade para evolução do schema.

## Uploads

O modo padrão grava arquivos em `backend/uploads`. Para escala horizontal, substitua por storage persistente.
