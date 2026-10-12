# Checklist — Gestão Inteligente 2.1.0-rc.5

Legenda: ✅ concluído | 🔌 depende de provedor/credencial externo | 🚀 configuração de ambiente de publicação | 🧪 escrito, aguardando primeira execução

## Fundação
- ✅ Next.js + React + TypeScript + Tailwind.
- ✅ FastAPI + SQLAlchemy.
- ✅ PostgreSQL/Supabase compatível.
- ✅ Alembic: migration inicial + `9c4e1a7b2d10` (coluna `area_profissional` que faltava).
- ✅ Utilitário `legacy_upgrade.py` para recuperar banco antigo quando o código/histórico de migrations foi perdido.
- ✅ `.env.example` para backend e frontend.
- ✅ Ambiente limpo: sem `.venv`, `node_modules`, `.next` ou segredos no pacote final.

## CRM SargLab
- ✅ Leads B2B/B2C.
- ✅ Campos empresa, cargo, e-mail, telefone e consentimento.
- ✅ Segmento e tamanho de equipe.
- ✅ Dor/gatilho, oferta, formato, orçamento e origem.
- ✅ Próxima ação + data.
- ✅ Edição completa da ficha comercial.
- ✅ Pipeline atual: Lead → Contato realizado → Interessado → Reunião → Proposta → Negociação → Fechado → Pós-venda.
- ✅ Perdido + motivo.
- ✅ Interações e histórico.
- ✅ Follow-ups e próximas ações em agenda única.
- ✅ Kanban.
- ✅ Busca real de Leads.

## Workshop / operação
- ✅ Área Workshop IA com SargLab e SARGTECH.
- ✅ Método CLARO atualizado.
- ✅ Starter Kit com referência atual de 60 prompts.
- ✅ Referências comerciais atuais.
- ✅ Contexto B2B 5–80 pessoas.
- ✅ Pós-venda operacional documentado.

## Marketing / Analytics
- ✅ Campanhas, custo e UTMs.
- ✅ CPL, CAC, ROI e conversão.
- ✅ Dashboard comercial.
- ✅ Customer Analytics B2B/B2C.
- ✅ Análises por segmento, equipe, oferta, formato, cidade, orçamento e objetivo.

## Produtos / Vendas / Financeiro
- ✅ Produtos.
- ✅ Vendas.
- ✅ Pagamento Pago/Pendente/Cancelado/Reembolsado.
- ✅ Venda paga atualiza Lead e pode criar matrícula.
- ✅ Cancelamento/reembolso suspende acesso ao curso.
- ✅ Retorno para Pago pode restaurar matrícula.
- ✅ Resumo financeiro com receita, contas a receber, cancelamentos, reembolsos e saldo líquido.

## LMS
- ✅ Cursos e conteúdos.
- ✅ Upload local de materiais até 50 MB.
- ✅ Admin de conteúdo com criar/editar/desativar/reativar.
- ✅ Matrícula automática vinculada à venda paga.
- ✅ Área do aluno.
- ✅ Progresso e conclusão.
- ✅ LMS Analytics.
- ✅ Indicador simples de possível abandono.
- ✅ Ownership: aluno acessa apenas a própria matrícula.

## Segurança / usuários
- ✅ Usuários admin/vendedor/aluno.
- ✅ Hash Argon2.
- ✅ JWT.
- ✅ Bootstrap do primeiro admin.
- ✅ Gestão visual de usuários.
- ✅ Ativar/desativar conta.
- ✅ Aluno vinculado a Lead único.
- ✅ Cookie HttpOnly + BFF no Next.js.
- ✅ Token não persistido em localStorage.
- ✅ RBAC no backend.
- ✅ Proteção de APIs administrativas.
- ✅ Proteção de CRM/vendas para admin+vendedor.
- ✅ Proteção de LMS e dados próprios do aluno.

## Omnichannel / Automação
- ✅ Painel Omnichannel baseado nas interações do CRM.
- ✅ Insights operacionais por regras.
- 🔌 WhatsApp/e-mail bidirecional real depende da API/provedor escolhido.
- 🔌 IA generativa externa depende do provedor e chave escolhidos.

## Deploy
- ✅ Dockerfiles.
- ✅ `docker-compose.yml` para frontend/backend.
- ✅ Variáveis de ambiente para URL interna do backend e URLs públicas.
- 🚀 Publicação efetiva exige domínio/host, banco e segredos da conta de produção.
- 🚀 Storage persistente é recomendado para uploads em produção.

## Entrega / homologação (RC 2.0.2-rc.3)
- ✅ Auditoria técnica registrada em `docs/AUDITORIA.md`.
- ✅ Suíte de backend executada em ambiente local: **162 passed, 0 failed, 1 warning não bloqueante**.
- ✅ N1–N4 cobertas pelos 11 testes de regressão em `backend/tests/test_business_rules.py`.
- ✅ Banco PostgreSQL/Alembic validado na 2.0.1: migration `9c4e1a7b2d10` aplicada e `alembic check` sem drift; a RC 2.0.2 não adiciona mudança de schema.
- ✅ CI configurado com `pytest`, auditoria npm, typecheck, lint, build e job Docker.
- ✅ Correções anteriores de ESLint validadas parcialmente; a homologação local encontrou 1 erro remanescente em `course-content-admin.tsx`, corrigido na rc.3 sem `eslint-disable`.
- ✅ Dependências-alvo registradas: Next.js/`eslint-config-next` 16.3.8, `sharp` 0.35.5 e `source-map-js` 1.2.2.
- ✅ Homologação local da rc.2: `npm audit --omit=dev --audit-level=high` = 0 vulnerabilidades; `npm run typecheck` = aprovado; `npm run build` = aprovado (22/22 rotas); `npm run lint` encontrou 1 erro remanescente, corrigido nesta rc.3.
- 🧪 Reexecutar na rc.3: `npm ci`, `npm audit --omit=dev --audit-level=high`, `npm run typecheck`, `npm run lint`, `npm run build`.
- 🧪 Ainda executar em ambiente com Docker: `scripts/docker_check.sh` / job `docker` do CI.
- ✅ `scripts/update_frontend_deps.sh` corrigido para não remover devDependencies antes de typecheck/lint/build.
- ✅ Compose com healthcheck, restart e rotação de logs; scripts de smoke test e backup/restauração.
- ✅ Limitação do upload local documentada (`docs/DEPLOY.md` §5).
- 🚀 Homologação com a operação real do SargLab (`docs/HOMOLOGACAO.md`).
- Roadmap futuro separado em `docs/ROADMAP.md`.

## 2.1.0-rc.5
- ✅ Implementado: criação de Curso pela UI; vínculo Produto→Curso visível em Produtos e Vendas; coluna "Entrega".
- ✅ Implementado: camada de e-mail desligada por padrão + `email_logs` (migration `b7d2f4a91c33`).
- ✅ Implementado: script de limpeza com dry-run, aprovação por ID e transação.
- ✅ Implementado: tokens SARGTECH v0.1, Kanban com "Salvando…" e rollback.
- 🧪 Aguardando execução: `pytest` (162 + novos), `alembic upgrade head`/drift, `npm ci`, audit, typecheck, lint, build, Docker, CI, E2E.
- 👤 Pendente: homologação manual (`docs/HOMOLOGACAO.md` §G), limpeza real na cópia do banco, aprovação visual, decisões de `docs/DECISOES_2.1.0-rc.5.md`.
