# Changelog

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
