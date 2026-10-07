# Gestão Inteligente — SARGTECH / SargLab

CRM + funil comercial + BI + Marketing Analytics + Customer Analytics + vendas + financeiro + LMS + autenticação/RBAC, reconstruído e atualizado para a operação atual do **SargLab**.

A aplicação usa o Workshop **SargLab — IA no Dia a Dia** / apresentação corporativa **IA no Trabalho** como caso operacional inicial, mas a arquitetura continua reutilizável para outros produtos e serviços.

> Posicionamento SargLab: **IA prática para quem trabalha. Método CLARO · prompts · produtividade.**

## O que está incluído

- CRM de Leads B2B/B2C com ficha comercial completa.
- Pipeline: `Lead → Contato realizado → Interessado → Reunião → Proposta → Negociação → Fechado → Pós-venda`, mais `Perdido` com motivo.
- Campos para empresa, cargo, consentimento, dor/gatilho, próxima ação, segmento, equipe, oferta, formato e campanha.
- Histórico de interações e follow-ups.
- Funil Kanban.
- Produtos e vendas, com status `Pago`, `Pendente`, `Cancelado` e `Reembolsado`.
- Venda paga pode liberar matrícula automaticamente quando o produto está ligado a um curso.
- Cancelamento/reembolso suspende o acesso da matrícula; pagamento restaurado pode reativá-lo.
- Dashboard comercial, Customer Analytics, Marketing Analytics, Financeiro e Omnichannel Analytics.
- Campanhas com custo e UTMs; cálculo de CPL, CAC, ROI e conversão.
- LMS: cursos, conteúdos, upload local de materiais, matrículas, progresso, conclusão e analytics.
- Área do aluno com validação de ownership da matrícula.
- Gestão de usuários `admin`, `vendedor` e `aluno`.
- JWT no FastAPI + cookie **HttpOnly** no Next.js + BFF/proxy para chamadas do navegador.
- RBAC aplicado no backend; esconder menu não é usado como única camada de segurança.
- Automações/insights operacionais por regras: follow-up vencido, Lead sem interação, pagamento pendente e risco de abandono no LMS.
- Playbook do Workshop dentro do sistema (`/workshop`) com Método CLARO e referências comerciais atuais.

## Estrutura

```text
gestao-inteligente-reconstruido/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── migrations/
│   ├── uploads/
│   └── seed_sarglab.py
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── .env.example
├── docs/
├── CHECKLIST.md
├── docker-compose.yml
└── README.md
```

## Requisitos locais

- Python 3.11+.
- Node.js 20.9+ (Node 22 recomendado).
- PostgreSQL/Supabase para uso persistente.
- Windows PowerShell, Terminal ou equivalente.

## 1. Backend

Entre na pasta:

```powershell
cd backend
```

Crie o ambiente virtual:

```powershell
python -m venv .venv
```

**O que faz:** cria um Python isolado para as dependências do projeto.

Ative no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

**O que faz:** passa a usar o Python e os pacotes da `.venv`.

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

**O que faz:** instala FastAPI, SQLAlchemy, Alembic, driver PostgreSQL, Argon2 e JWT.

Crie seu `.env` a partir de `.env.example` e preencha `DATABASE_URL` e `JWT_SECRET_KEY`. Para gerar uma chave forte:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**O que faz:** gera uma chave aleatória adequada para assinar tokens JWT. Não publique essa chave.

Aplique o banco:

```powershell
alembic upgrade head
```

**O que faz:** cria/atualiza a estrutura do PostgreSQL conforme as migrations.

### Se o banco antigo ainda existir

Se o código foi perdido, mas o PostgreSQL/Supabase antigo ainda contém as tabelas do Gestão Inteligente, **faça backup do banco antes** e use:

```powershell
python legacy_upgrade.py
```

**O que faz:** recupera de forma idempotente os campos/tabelas que faltam, converte as etapas antigas do funil para o pipeline atual e recompõe a referência do Alembic. Depois execute `alembic upgrade head`. Em banco novo, não use esse script; use apenas a migration normal.

Suba a API:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**O que faz:** inicia o FastAPI em `http://127.0.0.1:8000`.

Swagger:

```text
http://127.0.0.1:8000/docs
```

### Primeiro administrador

Com o banco vazio, use no Swagger:

```text
POST /api/auth/bootstrap-admin
```

Ele só funciona enquanto não houver nenhum usuário. Depois, todo gerenciamento de contas é feito pela área **Usuários**.

### Seed opcional SargLab

Depois da migration, você pode carregar produtos/campanha/curso demonstrativos atuais:

```powershell
python seed_sarglab.py
```

**O que faz:** cria dados operacionais do SargLab sem criar contas, senhas ou casos fictícios de clientes.

## 2. Frontend

Em outro terminal:

```powershell
cd frontend
npm ci
```

**O que faz:** instala exatamente as versões registradas no `package-lock.json`.

Se necessário, copie `.env.example` para `.env.local`. Em desenvolvimento local, o valor padrão já aponta para a API local.

Suba o Next.js:

```powershell
npm run dev
```

**O que faz:** inicia o frontend em `http://localhost:3000`.

## Supabase

Quando a conexão direta não funcionar em rede IPv4, use o **Shared Session Pooler** do Supabase no `DATABASE_URL`. O projeto usa `postgresql+psycopg://...`.

Nunca envie o `.env`, senha do banco ou `JWT_SECRET_KEY` para o Git.

## Perfis e permissões

| Recurso | Admin | Vendedor | Aluno |
|---|:---:|:---:|:---:|
| Dashboard/BI estratégico | ✅ | ❌ | ❌ |
| CRM / Leads / Funil / Follow-ups | ✅ | ✅ | ❌ |
| Interações e Omnichannel | ✅ | ✅ | ❌ |
| Vendas | ✅ | ✅ | ❌ |
| Consultar produtos/campanhas para operação | ✅ | ✅ | ❌ |
| Criar produtos/campanhas | ✅ | ❌ | ❌ |
| Customer/Marketing/LMS Analytics | ✅ | ❌ | ❌ |
| Financeiro | ✅ | ❌ | ❌ |
| Gestão de cursos/conteúdos | ✅ | ❌ | ❌ |
| Gestão de usuários | ✅ | ❌ | ❌ |
| Próprias matrículas e conteúdos | ✅ | ❌ | ✅ |

A Área do Aluno verifica no backend se `Enrollment.lead_id == User.lead_id`; trocar manualmente o ID da URL não concede acesso a outra matrícula.

## Segurança da sessão

1. O navegador envia e-mail/senha para `/api/session/login` no Next.js.
2. O Next autentica no FastAPI.
3. O JWT é armazenado em cookie `HttpOnly`, `SameSite=Lax`.
4. O token não é gravado em `localStorage` e não é devolvido ao JavaScript após o login.
5. Client Components usam `/api/backend/...`, um BFF do Next que anexa o JWT no servidor.
6. Server Components usam `serverApi()` / `protectedJson()`.
7. O FastAPI valida JWT, usuário ativo, role e ownership quando necessário.

## Upload de materiais

`POST /api/course-contents/upload` aceita arquivos administrativos de até **50 MB** e grava em `backend/uploads/`.

Isso é adequado para desenvolvimento, homologação e instalações simples. Em produção com múltiplas instâncias, substitua por storage persistente (por exemplo, Supabase Storage/S3 compatível) e configure `UPLOAD_BASE_URL`.

## Workshop SargLab atualizado

O CRM foi preparado para a operação atual:

- Workshop com duração de **2 horas**, aproximadamente **80% prático**.
- Método CLARO: Contexto e papel; Linha de chegada; Amarras; Roteiro de saída; Olhar crítico.
- Prioridade B2B: pequenas e médias empresas/equipes de aproximadamente 5 a 80 pessoas.
- Materiais: Starter Kit SargLab com **60 prompts**, cartão CLARO, guia de uso seguro e certificado.
- Referências comerciais configuradas no seed/playbook: B2C piloto R$ 47, lançamento R$ 97, cheio R$ 147; presencial R$ 197–297; piloto B2B R$ 1.200–1.600.
- Pós-venda: materiais/certificados em até 24h, pesquisa, depoimento, indicações e próximo passo comercial.

Veja `docs/WORKSHOP_SARGLAB.md`.

## Docker / preparação para deploy

Com os arquivos `.env` configurados:

```powershell
docker compose up --build
```

**O que faz:** constrói e inicia frontend e backend em containers. O banco continua externo (Supabase/PostgreSQL), evitando duplicar a base de produção.

Consulte `docs/DEPLOY.md` antes de publicar.

## Integrações externas

O repositório funciona sem fornecedor externo de IA ou mensageria. A camada Omnichannel atual consolida as interações registradas no CRM, e a área Automações produz insights por regras.

Para envio/recebimento real por WhatsApp/e-mail e para IA generativa externa, ainda são necessárias contas, chaves e webhooks do fornecedor escolhido. Esses segredos não podem ser embutidos no ZIP.

## Verificações da reconstrução

A reconstrução foi validada com:

- compilação Python (`py_compile`);
- migration Alembic em banco SQLite limpo;
- smoke test da API com criação de admin, login, campanha, Lead, interação, produto, curso, conteúdo, venda, matrícula, analytics e RBAC;
- teste de suspensão/restauração de matrícula por situação financeira;
- análise sintática de todos os arquivos TypeScript/TSX;
- varredura para impedir envio de `.env`, `.venv`, `node_modules`, `.next`, bancos locais e caches.

O build completo do Next deve ser executado após `npm ci` no ambiente com acesso ao registry npm.
