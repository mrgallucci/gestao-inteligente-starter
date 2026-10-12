# Checklist de homologação

Marque cada item ao validar. 🤖 = já coberto por teste automatizado (rode `pytest`/CI e confira que passou); 👤 = precisa ser feito por uma pessoa em ambiente real.

## A. Instalação limpa

- [ ] 🤖 CI verde: backend (`pytest`, incluindo `alembic upgrade head` e checagem de drift), frontend (`npm ci`, `npm audit --omit=dev --audit-level=high`, `typecheck`, `lint`, `build`) e Docker (`scripts/docker_check.sh`).
- [ ] 👤 `npm audit --omit=dev` sem vulnerabilidade high/critical (rode `scripts/update_frontend_deps.sh` e faça commit do lockfile).
- [ ] 👤 Clone limpo → `backend/.env` a partir do exemplo → `alembic upgrade head` → API sobe sem erro.
- [ ] 👤 `npm ci && npm run build && npm run start` no frontend, sem erro.
- [ ] 👤 `docker compose up --build` sobe os dois serviços; backend aparece como `healthy`.
- [ ] 👤 `git ls-files | grep -E '\.env$'` não retorna nada; nenhum segredo no repositório.

## B. Segurança e perfis

- [ ] 🤖 RBAC: vendedor recebe 403 em Dashboard/BI, Financeiro, Usuários, cursos, analytics e uploads.
- [ ] 🤖 Aluno só acessa a própria matrícula (trocar o ID na URL → 403).
- [ ] 🤖 Conta inativa e token expirado/adulterado → 401.
- [ ] 👤 Em produção: `APP_ENV=production`, `JWT_SECRET_KEY` forte, HTTPS ativo, cookie `Secure` visível no navegador.
- [ ] 👤 Nenhum JWT em `localStorage`/`sessionStorage` (DevTools → Application).
- [ ] 👤 Primeiro administrador criado logo após o deploy; `bootstrap-admin` passa a responder 409.

## C. Fluxos críticos (roteiro manual no navegador)

Admin:
- [ ] Login/logout; menu completo; Dashboard abre sem erro.
- [ ] Criar campanha (com UTMs) e produto; criar curso ligado ao produto com 2 conteúdos (um com upload).
- [ ] Criar Lead vinculado à campanha; editar ficha completa; mover entre etapas no Kanban; marcar Perdido com motivo.
- [ ] Registrar interação com follow-up; ver na Agenda (follow-up + próxima ação da ficha).
- [ ] Registrar venda **Paga** → Lead vai para Fechado → matrícula criada.
- [ ] Criar usuário **aluno** vinculado ao Lead; ver Financeiro, Marketing, Customer e LMS Analytics.
- [ ] Alterar a venda para Reembolsado → matrícula "Acesso suspenso"; voltar para Pago → "Acesso liberado".

Vendedor:
- [ ] Login; vê CRM, Funil, Follow-ups, Vendas, Omnichannel, Automações, Workshop.
- [ ] Digitar na barra de endereço `/financeiro`, `/usuarios`, `/lms` → é redirecionado/bloqueado.

Aluno:
- [ ] Login → Minha Área lista só os próprios cursos; abre conteúdo, marca progresso até concluir.
- [ ] Com acesso suspenso, a tela mostra o aviso de pagamento e não abre conteúdo.

## D. Telas e estados

- [ ] Loading, erro, vazio e sucesso nas telas principais (Leads, Funil, Vendas, Financeiro, LMS, Minha Área).
- [ ] Mensagens de validação legíveis ao enviar formulário vazio ou com preço negativo (devem ser texto, não tela quebrada).
- [ ] Desktop e largura móvel (~390 px): Login, Leads, Funil, Vendas, Minha Área e curso do aluno.

## E. Produção e operação

- [ ] 👤 `scripts/smoke_test.sh` sem falhas (com contas de admin e vendedor).
- [ ] 👤 Monitor externo apontando para `/health`, `/health/database` e `/login`.
- [ ] 👤 Backup do banco executado **e restauração testada** em banco de teste (`DEPLOY.md` §6).
- [ ] 👤 Pasta de uploads incluída no backup, ou limitação de instância única aceita por escrito.
- [ ] 👤 Proxy reverso com limite de requisições em `/api/auth/login` e `/api/public/leads/ebook`.
- [ ] 👤 `CORS_ORIGINS` inclui o domínio da página do e-book (se houver).

## F. Escopo

- [ ] Itens da lista "não vender como pronto" do briefing continuam fora do material comercial: WhatsApp/e-mail bidirecional, IA generativa, ERP, multiempresa, storage distribuído.
- [ ] Regras N1–N4 (`AUDITORIA.md`) conferidas na operação: Pós-venda não regride; nova compra restaura acesso; reembolso com outra venda paga não suspende; restauração mantém o andamento.
- [ ] Homologação com operação real do SargLab antes de ampliar o mercado.

## G. Novidades da 2.1.0-rc.1 (roteiro manual)

Produto → Curso → Matrícula
- [ ] 👤 Produtos: card sem curso mostra "Este produto não libera curso." + link "Criar curso para este produto".
- [ ] 👤 Admin Cursos: criar curso escolhendo um produto sem curso; produto some da lista; tentar vincular segundo curso ao mesmo produto é impossível pela tela e dá 409 pela API.
- [ ] 👤 Produtos: card passa a mostrar "Curso vinculado".
- [ ] 👤 Vendas: ao escolher Cliente + Produto, o aviso muda entre "libera acesso ao LMS", "após o pagamento" e "não libera curso" conforme produto e status.
- [ ] 👤 Venda Paga de produto com curso → listagem "LMS · Acesso liberado"; Reembolsado → "Acesso suspenso"; voltar a Pago → "Acesso liberado".
- [ ] 👤 Venda de produto SEM curso: permitida, "Não aplicável", nenhuma matrícula em LMS.
- [ ] 👤 Venda Pendente → "Aguardando pagamento"; Cancelada/Reembolsada sem acesso prévio → "Não aplicável"; produto com curso inativo → aviso laranja antes de registrar e na listagem.
- [ ] 🤖 Cobertos por `test_product_course_delivery.py` (API); 🧪 E2E `e2e/` aguardando primeira execução.

E-mail (ambiente seguro, nunca em produção real)
- [ ] 👤 Baixar o e-book duas vezes com o mesmo e-mail: um único Lead, Interações "Download e-book" e (com automação ligada) "E-mail automático" a cada envio; nunca erro 409.
- [ ] 👤 Resposta pública idêntica (HTTP e corpo) para e-mail novo e já existente: comparar as duas respostas com `curl -i`; nenhuma traz id/status.
- [ ] 👤 E2E: gerar e versionar `e2e/package-lock.json` (ver `e2e/README.md`) e rodar o job; só após a 1ª execução verde remover `continue-on-error`.
- [ ] 👤 Com `APP_ENV=production` e `EMAIL_COMMERCIAL_ENABLED=true`: o e-mail NÃO contém CTA comercial.
- [ ] 👤 Padrão: com `EMAIL_AUTOMATION_ENABLED=false`, baixar o e-book cria o Lead e nada é enviado.
- [ ] 👤 `EMAIL_PROVIDER=console` + flag ligada: log mostra o envio; Lead ganha Interação "E-mail automático"; `GET /api/email-logs` mostra `enviado`.
- [ ] 👤 SMTP de teste (caixa própria): e-mail chega, sem link comercial quando `PAID_PRODUCT_URL` está vazio.
- [ ] 👤 Derrubar o SMTP (senha errada): Lead continua sendo criado; `email_logs` registra `falha`.
- [ ] 🤖 Cobertos por `test_email_automation.py` (provedor simulado).

Limpeza de dados
- [ ] 👤 Seguir `docs/LIMPEZA_DADOS.md` numa CÓPIA: backup → clone → dry-run → revisar → ensaio (`--rehearsal`) → execução → validar login/CRM/vendas/LMS/analytics.
- [ ] 🤖 Regras do script cobertas por `test_data_cleanup.py`.

Visual SARGTECH
- [ ] 👤 Revisar Login, Dashboard, Leads, Funil, Produtos, Vendas, Admin Cursos: sidebar Midnight, ativo Cobalt, fundo Ice, sem efeitos decorativos; status (verde/âmbar/vermelho) continuam semânticos.
- [ ] 👤 Kanban: arrastar mostra "Salvando…"; derrubar a API e arrastar → card volta e aparece a mensagem de erro.
- [ ] 👤 Desktop e ~390 px. Capturar screenshots para aprovação da identidade.
