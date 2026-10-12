# Changelog

## 2.1.0-rc.5 — correções de E2E/CI (2026-10-12)

Somente correções de teste e de workflow. **Nenhuma funcionalidade nova, nenhuma regra de negócio alterada, N1–N4 intactas.** Código de produção inalterado (apenas a string de versão da API).

### Contexto (informado pela gerência sobre a rc.4)
- A rc.4 passou **Backend, Frontend e Docker no GitHub Actions** (204/204 testes backend, PostgreSQL/Alembic sem drift, npm ci, audit, typecheck, lint, build, homologação manual e N1–N4).
- O **E2E da rc.4 falhou por sincronização/asserção do teste**, não por defeito de regra de negócio. **Nenhuma falha de N1–N4 foi identificada.**
- O workflow falhava nos steps "Logs" e "Derruba a stack" porque **`CI_JWT_SECRET` não persistia entre steps**.

### Correções
1. **E2E — criação de curso:** o teste esperava a mensagem transitória "Curso criado e vinculado ao produto.", que some quando `router.refresh()` remonta a árvore. Agora aguarda a resposta `POST …/api/backend/api/courses` (2xx) e confirma "Curso vinculado" em `/products`. A regra e a mensagem da interface não mudaram.
2. **E2E — race de login:** helper `loginAsAdmin(page)` compartilhado, que aguarda `not.toHaveURL(/\/login/)` antes de navegar; usado pelos dois testes. `page`/`context` não são compartilhados.
3. **CI — `CI_JWT_SECRET`:** o step "Sobe a stack" grava a variável em `$GITHUB_ENV` (com `::add-mask::`), de modo que "Logs em caso de falha" e "Derruba a stack" (`down -v`, `if: always()`) também a recebem. Segredo temporário de banco/stack descartável; nada commitado.
4. **Playwright:** `@playwright/test` 1.55.1, `npm ci` e `e2e/package-lock.json` mantidos (lockfile versionado pela gerência).
5. **`continue-on-error: true` mantido.** A gerência removerá a flag após a primeira execução E2E totalmente verde.

> **Validação desta rc.5:** nada executado (sem registry npm/PyPI/Docker/GitHub Actions neste ambiente). Playwright **não** é declarado verde.

## 2.1.0-rc.4 — fechamento técnico: anti-enumeração no e-book e E2E determinístico (2026-10-11)

Somente os refinamentos abaixo. **Nenhum módulo novo, nenhuma feature de negócio nova, nenhuma regra aprovada alterada** (N1–N4, matrícula retroativa, Produto → Curso, entrega LMS, identidade, JWT/BFF, RBAC, limpeza, e-mail comercial, fornecedor e roadmap intactos).

> **Estado de validação:** a gerência informou, para a rc.3, 200 testes aprovados, migration `b7d2f4a91c33` consistente em banco limpo e Alembic head sem drift. **Nada da rc.4 foi executado** (sem PyPI/npm/Docker/registry neste ambiente). Ver `docs/VALIDACAO.md`.

### 1. Resposta pública do e-book indistinguível (correção de enumeração de e-mails)
- `POST /api/public/leads/ebook` devolve **HTTP 201 e o mesmo corpo, byte a byte**, para e-mail novo e e-mail já existente: `{"mensagem": "Solicitação registrada com sucesso. Verifique seu e-mail."}`. Sem `id`, `nome`, `email`, `status` nem flags created/reused. Status mantido em 201 (não há justificativa técnica para outro).
- Antes (rc.3) o e-mail novo devolvia `id/nome/email/status` e o existente devolvia outro formato — distinguíveis.
- Comportamento interno **inalterado**: Lead novo é criado; existente é reutilizado (sem duplicata), com Interação "Download e-book" e consentimento registrado; e-mail disparado conforme flag/consentimento; falha de provedor não impede o fluxo; `email_logs` preservados. Validações (400 sem nome/e-mail/consentimento) idênticas nos dois casos.
- **Mudança de contrato:** consumidores externos (página do e-book) não podem mais ler `id/status` da resposta.
- **Testes:** 4 novos em `test_email_automation.py` (uniformidade byte a byte, comportamento interno, falha de provedor, consentimento). 4 testes **existentes** da rc.2/rc.3 liam `response.json()["id"]` do endpoint público; passaram a obter o id pelo CRM (`GET /api/leads`) — ajuste forçado pela mudança de contrato, sem enfraquecer asserções.
- Suíte esperada: **200 + 4 = 204** (a confirmar por execução real; a contagem exata de coleta vem do pytest).

### 2. E2E reprodutível
- Workflow usa `npm ci` no job `e2e` e falha com mensagem clara se `e2e/package-lock.json` não existir. Versões inalteradas (`@playwright/test` 1.55.0).
- **O `package-lock.json` do E2E NÃO foi gerado/versionado:** o ambiente não tem acesso ao registry npm e o arquivo não foi fabricado à mão (hashes de integridade). Pendente: `cd e2e && npm install --package-lock-only` e commit.
- `continue-on-error: true` **mantido (temporário)**, com comentário: "Remover continue-on-error após a primeira execução verde aprovada pela gerência." Não há execução verde ainda.

### Documentação / versão
- `VERSION` e versão da API: 2.1.0-rc.4. `docs/EMAIL.md`, `docs/AUDITORIA.md` (D2), `docs/HOMOLOGACAO.md`, `docs/VALIDACAO.md` e o relatório da RC atualizados.

## 2.1.0-rc.3 — decisões da gerência sobre a rc.2 + assets oficiais (2026-10-10)

Sem expansão de escopo. A gerência informou **200 testes de backend aprovados** (162 anteriores + **38** novos: `test_product_course_delivery` 12, `test_email_automation` 17, `test_data_cleanup` 9) em ambiente independente. Correção de documentação: a referência a "30 novos" valia só para a rc.1; o pacote rc.2/rc.3 tem 38.

> **Estado de validação:** alterações verificadas estaticamente. `alembic`/PostgreSQL, `npm ci`, audit, typecheck, lint, build, Docker, CI e Playwright **não foram executados** neste ambiente (sem PyPI/npm/Docker/PostgreSQL/rede liberada). Ver `docs/VALIDACAO.md`.

- **"Sem matrícula" → "Matrícula não gerada"**, apresentado como estado de **atenção** (cor de aviso + texto `aviso` na listagem). **Não há matrícula retroativa automática** para vendas anteriores ao vínculo Produto → Curso (poderia alterar direito adquirido; depende de decisão operacional futura). Teste cobre que vincular o curso depois não matricula.
- **Assets oficiais SARGTECH v0.1** (pacote da gerência): SVGs de símbolo (cobalt/white), lockups claro/escuro, app icon e `favicon.svg` em `frontend/public/brand/`; favicon do app em `frontend/src/app/icon.svg`. PNG temporário removido. README e tokens oficiais (CSS/JSON) copiados para `docs/identidade/`. Tokens de `globals.css` alinhados ao pacote (borda `#DEE4EF`, raios sm/md/lg, `shadow-card`). Login usa os lockups oficiais.
- Nota: os SVGs de lockup usam `<text>` (Inter/Manrope); como `<img>`, o navegador usa fallback de sistema se a fonte não estiver instalada. Para fidelidade exata, solicitar versão com texto convertido em curvas.
- Versão: 2.1.0-rc.3.

## 2.1.0-rc.2 — ajustes da revisão da gerência (2026-10-10)

Sem novos módulos. Resposta aos 11 pontos da revisão da 2.1.0-rc.1 (a gerência informou 162 + 38 testes passando em ambiente independente).

> **Estado de validação desta rc.2:** os ajustes abaixo foram verificados **estaticamente** (compilação, ruff F/E9, sintaxe TS/TSX). `pytest`, Alembic/PostgreSQL, `npm ci`/audit/typecheck/lint/build, Docker, CI e Playwright **não foram executados** aqui (sem PyPI/npm/Docker). Ver `docs/VALIDACAO.md`.

- **(1) Download repetido do e-book:** `POST /api/public/leads/ebook` não retorna mais 409 para e-mail já existente. Reutiliza o Lead (sem duplicata), registra a Interação "Download e-book", registra o consentimento dado no download e dispara o e-mail conforme flag/consentimento. A resposta para e-mail existente não expõe id/status do Lead. Consentimento continua obrigatório (400 sem ele). *Teste antigo que esperava 409 foi atualizado para 201 + sem duplicata.*
- **(2) Entrega em Vendas:** separado **tipo** de **status**. `entrega_tipo` = `"LMS"` (produto com curso) ou `null`; `entrega_status` ∈ `Acesso liberado` | `Aguardando pagamento` | `Acesso suspenso` | `Não aplicável` (+ `Sem matrícula` para venda paga sem matrícula gerada, p.ex. curso vinculado depois da venda). Pendente/Cancelado/Reembolsado nunca aparecem como acesso liberado (exceto "acesso mantido por outra venda paga", explicado no detalhe). Campos novos: `entrega_status`, `aviso`, `curso_ativo`; `entrega_tipo` mudou de valor ("Acesso LMS"/"Não aplicável" → "LMS"/null).
- **(3) Curso inativo:** venda segue permitida; aviso destacado no formulário ("Atenção: curso inativo… NÃO gerará matrícula") e na listagem (`aviso`).
- **(4)(5) E-mail:** sem agendador; fornecedor indefinido; automação desligada por padrão (inalterado).
- **(6) Descadastro:** `EMAIL_COMMERCIAL_ENABLED` é **ignorado com `APP_ENV=production`** (CTA comercial bloqueado + aviso em log) até existir mecanismo de descadastro.
- **(7)(8) Limpeza/admin:** inalterados (somente clone, dry-run, aprovação por ID; produtos/cursos/campanhas nunca excluídos automaticamente; `admin@teste.local` preservado).
- **(9) E2E:** continua `continue-on-error` somente até a primeira execução verde; depois deve virar gate obrigatório (registrado em `docs/VALIDACAO.md`). Seletores do E2E atualizados para tipo/status.
- **(10) Símbolo:** removido o SVG provisório. Agora usa o símbolo **extraído do lockup oficial** do Guia v0.1 (`public/brand/sargtech-symbol.png`, `sargtech-lockup.png`, favicon `app/icon.png`). **O pacote vetorial oficial (SVG/CSS/JSON) não está nos arquivos que recebi** — só o lockup PNG embutido no .docx; enviar o pacote para trocar por SVG.
- **(11) Pacote:** gerado sem `.ruff_cache`, `.pytest_cache`, `__pycache__`, `node_modules`, `.next`, `.env` (verificado antes de zipar).
- Versão: 2.1.0-rc.2 (API, `VERSION`).

## 2.1.0-rc.1 — Produto → Curso → Matrícula, e-mail pós e-book, limpeza segura e identidade SARGTECH (2026-10-10)

Base: 2.0.2-rc.3. Sem WhatsApp, IA generativa, ERP ou multiempresa. Arquitetura preservada; `main.py` não foi refatorado.

> **Estado de validação:** tudo abaixo foi **implementado e verificado estaticamente** (compilação Python, ruff F/E9, sintaxe de 46 arquivos TS/TSX, YAML do CI). **pytest, `npm ci`/typecheck/lint/build, Docker, CI e E2E NÃO foram executados** no ambiente de desenvolvimento (sem acesso a PyPI/npm/Docker). Veja `docs/VALIDACAO.md`.

### Produto → Curso → Matrícula
- **Admin Cursos**: novo formulário de criação de Curso (produto obrigatório — só aparecem produtos sem curso —, nome, descrição, status). A relação 1 Produto → no máximo 1 Curso foi mantida (409 no backend); não existe "tipo de produto = curso".
- **Produtos**: cada card mostra "Curso vinculado" (com status) ou "Este produto não libera curso." + atalho "Criar curso para este produto". `GET /api/products` agora devolve `curso_id`, `curso_nome`, `curso_ativo`, `libera_lms`.
- **Venda**: antes de confirmar, aviso explícito se libera LMS e qual curso será concedido (ou que não libera / curso inativo / aguarda pagamento).
- **Listagem de Vendas**: nova coluna "Entrega" — `Acesso LMS` (com curso e estado da matrícula) ou `Não aplicável`. `GET /api/sales` devolve `entrega_tipo`, `entrega_detalhe`, `curso_id`, `curso_nome`, `matricula_status`.
- Regras N1–N4 e fluxo Pago → matrícula, Reembolsado → suspensão, Pago → restauração **inalterados** (novos testes de ponta a ponta).
- Validação de `CourseCreate` (nome obrigatório/trim, 422 em texto).

### E-mail pós e-book (desligado por padrão)
- Nova camada `email_service.py` desacoplada de fornecedor (`console` e `smtp`), templates `entrega_material` e `convite_comercial`, consentimento respeitado, sem chaves/URLs no código. Detalhes em `docs/EMAIL.md`.
- Tabela `email_logs` + `GET /api/email-logs` (admin); sucesso registra Interação "E-mail automático"; falha nunca bloqueia o Lead.
- **Migration nova:** `b7d2f4a91c33_add_email_logs` (idempotente; down_revision `9c4e1a7b2d10`).

### Limpeza segura de dados
- `backend/cleanup_test_data.py` + `data_cleanup.py`: dry-run padrão, classificação REAL / TESTE_PROVAVEL / SISTEMA-ADMIN / INDETERMINADO, preservação por ID, exclusão apenas de IDs aprovados, transação com invariantes, relatórios sem segredos. Guia em `docs/LIMPEZA_DADOS.md`. **Nenhuma limpeza foi executada.**

### Identidade visual SARGTECH v0.1
- Tokens em `globals.css` (`@theme`): Midnight, Cobalt (escala), Indigo, Ice, Steel, status success/warning/danger, raio de card 18 px, foco visível. Verde → Cobalt em botões/seleção; sidebar Midnight com indicador ativo Cobalt; fundo Ice; cards brancos.
- Símbolo na sidebar e no login (na rc.2 trocado pelo derivado do lockup oficial); ícone de cérebro removido. Sem gradientes, glow, sombras fortes ou animações decorativas. Tipografia: pilha `Inter, Manrope, system-ui` **sem baixar fonte** (hospedar Inter licenciada é pendência).
- Labels de formulários associados aos campos (acessibilidade e testabilidade).
- **Kanban**: indicador "Salvando…", bloqueio de arrastar durante a gravação, rollback do card com mensagem de erro inline (substitui `alert`) também em falha de rede.

### Testes
- Novos arquivos: `test_product_course_delivery.py`, `test_email_automation.py`, `test_data_cleanup.py`. Os 162 testes anteriores não foram alterados.
- E2E Playwright em `e2e/` (pasta isolada para não mexer no lockfile do frontend) + job `e2e` no CI **não bloqueante** até a primeira execução verde.

### Ajustes menores
- Removido import `engine` não utilizado em `main.py`. Versão da API/VERSION: 2.1.0-rc.1.

## 2.0.2-rc.3 — correção final do lint remanescente (2026-10-10)

Sem novos módulos e sem expansão de escopo.

### Frontend
- `course-content-admin.tsx`: removida a chamada direta de `loadContents()` dentro do `useEffect`, que ainda era sinalizada por `react-hooks/set-state-in-effect`.
- A carga inicial de conteúdos agora usa `clientApi(...).then(...)` dentro do effect, com cancelamento no cleanup; atualizações de estado ocorrem somente nos callbacks assíncronos.
- Nenhuma regra ESLint foi desabilitada.

### Validação confirmada na rc.2 antes desta correção
- `npm audit --omit=dev --audit-level=high`: **0 vulnerabilidades**.
- `npm run typecheck`: **aprovado**.
- `npm run build`: **aprovado**, Next.js 16.3.8, 22/22 rotas geradas.
- `npm run lint`: restava **1 erro**, exatamente no effect corrigido nesta rc.3.
- Backend: **162 passed, 0 failed, 1 warning não bloqueante**.

### Pendente de confirmação na rc.3
- Reexecutar `npm ci`, audit, typecheck, lint e build após esta correção pontual.
- Docker/CI continua pendente em ambiente com Docker.

## 2.0.2-rc.2 — correção de dependências e fechamento da RC (2026-10-09)

Sem novos módulos e sem itens de roadmap.

### Segurança / dependências
- Next.js e `eslint-config-next` fixados em **16.3.8**.
- `package.json` passa a forçar `sharp` **0.35.5** e `source-map-js` **1.2.2** via `overrides`, versões que corrigem os advisories de produção identificados na homologação.
- `package-lock.json` atualizado para refletir Next 16.3.8, binários `@next/swc-*` 16.3.8, sharp 0.35.5/libvips 1.3.4 e source-map-js 1.2.2.
- `scripts/update_frontend_deps.sh` não usa mais `npm audit fix --omit=dev` antes das validações, evitando remover TypeScript/ESLint/Tailwind do `node_modules`.

### Validação já confirmada externamente
- Backend da RC 2.0.2: **162 testes passaram, 0 falhas, 1 warning não bloqueante**.
- N1–N4 estão cobertas pelos 11 testes de regressão adicionados na RC anterior.

### Pendente de execução em ambiente com registry/Docker
- `npm ci`, `npm audit --omit=dev`, `npm run typecheck`, `npm run lint`, `npm run build` desta rc.2.
- `scripts/docker_check.sh`.

## 2.0.2-rc.1 — Release Candidate (2026-10-09)

Rodada de correção após a validação local da 2.0.1. Sem novos módulos nem itens de roadmap.
Status de validação (o que foi e não foi executado) em `docs/VALIDACAO.md`.

### Regras de negócio (decisões N1–N4 da auditoria) — com testes de regressão
- **N1** — Venda/pagamento Pago não faz mais um Lead em "Pós-venda" voltar para "Fechado".
- **N2** — Nova venda Paga do mesmo curso restaura a matrícula suspensa (sem duplicar matrícula).
- **N3** — Cancelar/reembolsar uma venda só suspende o acesso se não existir outra venda Paga do mesmo produto/curso para o mesmo Lead.
- **N4** — Ao restaurar, o estado acadêmico é preservado: "Concluído" (se havia conclusão), "Em andamento" (se já houve acesso) ou "Acesso liberado" (sem acesso prévio). O progresso dos conteúdos nunca é alterado.

### Frontend / ESLint (sem desabilitar regras)
- `followups/page.tsx`: `Date.now()` saiu do render (capturado junto com os dados).
- `usuarios/page.tsx` e `auth-provider.tsx`: carga inicial via função de busca sem `setState` + `.then` no effect; `loadData()`/`refreshUser()` mantêm o comportamento para os handlers.
- `course-content-admin.tsx`: lista vazia derivada no render (sem `setContents([])` no effect); `handleUnauthorized`/`handleForbidden` em `useCallback` com dependências corretas.

### Dependências e Docker
- `scripts/update_frontend_deps.sh`: atualização controlada (Next ≥ 16.3.6, `npm audit fix --omit=dev`, sem `--force`) com a sequência completa de verificação.
- CI: `npm audit --omit=dev --audit-level=high`, lint bloqueante e job Docker (`scripts/docker_check.sh`: config, build, up com PostgreSQL descartável, migrations, healthchecks, login pelo BFF e smoke test).
- `docker-compose.ci.yml` (somente validação) e healthcheck do frontend no compose.

## 2.0.1 — preparação para homologação (2026-10-09)

Auditoria técnica e endurecimento, sem novas funcionalidades. Detalhes em `docs/AUDITORIA.md`.

### Corrigido
- **Instalação limpa quebrava o CRM**: a coluna `leads.area_profissional` não existia nas migrations. Nova migration `9c4e1a7b2d10` (idempotente); `legacy_upgrade.py` atualizado.
- Erros de validação (422) agora devolvem `detail` em texto, evitando tela quebrada nos formulários.
- Admin não reativa mais, sem querer, uma matrícula suspensa ao abrir conteúdo/atualizar progresso.

### Segurança
- `APP_ENV=production` exige `JWT_SECRET_KEY` ≥ 32 caracteres e diferente do placeholder.
- CORS por `FRONTEND_URL` + `CORS_ORIGINS` (5500 só em desenvolvimento); métodos/cabeçalhos explícitos.
- `url_conteudo` aceita apenas http(s).
- Login sem diferença de tempo entre e-mail inexistente e senha errada.
- Validação de entrada (preço/custo ≥ 0, nomes obrigatórios, `tipo_cliente` B2B/B2C, e-mail, idade, equipe).
- Cookie de sessão com a mesma validade do token (`expires_in`).
- Cabeçalhos de segurança no Next (`next.config.mjs`).

### Build, testes e operação
- Dependências do frontend fixadas nas versões do lockfile; `eslint.config.mjs` e `npm run typecheck`.
- Suíte `pytest` (migrations/drift, auth, RBAC, ownership, CRM, vendas/LMS/financeiro, uploads, validação) e CI no GitHub Actions.
- Compose com healthcheck, restart e rotação de logs; `/health/database` responde 503 quando o banco cai.
- Scripts `smoke_test.sh`, `backup_db.sh`, `restore_db.sh`.
- Documentação: `DEPLOY`, `HOMOLOGACAO`, `ROADMAP`, `AUDITORIA`, `VALIDACAO` revisados.

## 2.0.0 — reconstrução
Ver `REBUILD_NOTES.md`.
