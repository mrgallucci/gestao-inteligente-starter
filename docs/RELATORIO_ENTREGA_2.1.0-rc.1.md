# Relatório de entrega — Gestão Inteligente 2.1.0 estável (acumula rc.1–rc.5)

> **Status de release: 2.1.0 ESTÁVEL (2026-10-12).** Promovida da 2.1.0-rc.5 validada (GitHub Actions runs `38284823908` e `38286043714`: Backend, Frontend, Docker e E2E Playwright verdes; E2E é gate obrigatório). Nenhuma alteração funcional na promoção. O histórico técnico das RCs abaixo não foi reescrito.

## RC 2.1.0-rc.5 (validada; promovida a 2.1.0 estável)
**IMPLEMENTADO:** E2E de criação de curso valida o POST (2xx) + "Curso vinculado" em `/products`; helper `loginAsAdmin` com espera de saída de `/login`; `CI_JWT_SECRET` persistido via `$GITHUB_ENV`; Playwright 1.55.1; docs e versão.
**TESTADO (GitHub Actions, informado pela gerência):**
- 1ª execução, run `38284823908`: Backend GREEN, Frontend GREEN, Docker GREEN, E2E Playwright GREEN (E2E ainda com `continue-on-error`).
- `continue-on-error` removido (commit `7c95834e72e512422ccf5047184f3542adbf46f3`): E2E passou a gate obrigatório.
- 2ª execução, run `38286043714`, com o E2E bloqueante: Backend GREEN, Frontend GREEN, Docker GREEN, E2E Playwright (gate obrigatório) GREEN; stack descartável criada e derrubada com sucesso; workflow completo GREEN.
**NÃO EXECUTADO NESTE AMBIENTE DE DESENVOLVIMENTO:** pytest, npm, Docker, Playwright e GitHub Actions; a evidência acima é a da gerência.
**PENDÊNCIAS DA RELEASE 2.1.0:** nenhuma. Pendências de produção, tratadas à parte e que não são falha da release: publicação/ambiente, configuração de provedor de e-mail e URL comercial, limpeza real na cópia do banco, merge em `main` (decisão da gerência).

---

# Histórico — rc.4

## RC 2.1.0-rc.4 (esta rodada)
**IMPLEMENTADO:** resposta pública do e-book idêntica (HTTP 201 + corpo genérico) para e-mail novo/existente; workflow do E2E com `npm ci` e guarda de lockfile; comentário de remoção futura do `continue-on-error`; docs e versão.
**VALIDADO ESTATICAMENTE:** `py_compile`, ruff F/E9 (backend + testes), YAML do workflow, sintaxe TS/TSX inalterada (nenhum arquivo de frontend alterado).
**TESTADO AUTOMATICAMENTE:** nada nesta rodada. Evidência da gerência (rc.3): 200 testes, migration `b7d2f4a91c33` e head sem drift. Escritos na rc.4: +4 testes (esperado 204).
**NÃO EXECUTADO:** pytest, Alembic/PostgreSQL, `npm ci`/audit/typecheck/lint/build, Docker, CI, Playwright, homologação manual.
**PENDÊNCIAS:** gerar/versionar `e2e/package-lock.json`; execução real de tudo acima; 1ª execução E2E verde para remover `continue-on-error`; decisões C–H de `DECISOES_2.1.0-rc.1.md`; promoção a 2.1.0 só pela gerência.

---

# Histórico — rc.2

Formato exigido: IMPLEMENTADO / TESTADO / HOMOLOGADO / PENDENTE.

## Ajustes da rc.2 (revisão da gerência)
Download repetido do e-book reutiliza o Lead; entrega em Vendas separa tipo (LMS) de status; aviso de curso inativo; CTA comercial bloqueado em produção; símbolo derivado do lockup oficial; pacote limpo de caches. Detalhes no `CHANGELOG.md`.

## IMPLEMENTADO
- Criação de Curso pela UI (produto obrigatório, nome, descrição, status); 1 Produto → no máximo 1 Curso.
- Produtos: "Curso vinculado" / "Este produto não libera curso."; Venda: aviso prévio de liberação de LMS; Listagem de Vendas: coluna Entrega (tipo LMS + status).
- Camada de e-mail desacoplada (flag `EMAIL_AUTOMATION_ENABLED=false`), templates entrega/comercial, consentimento, `email_logs`, Interação "E-mail automático".
- Script de limpeza com dry-run, backup obrigatório, aprovação por ID, transação e relatórios.
- Identidade SARGTECH v0.1 (tokens, sidebar, cards, botões, foco), símbolo provisório, Kanban com "Salvando…" e rollback.
- E2E Playwright (pasta `e2e/`) e job de CI não bloqueante.

## TESTADO (automaticamente)
- **Neste ambiente:** apenas verificação estática (compilação Python, ruff F/E9, sintaxe de 46 arquivos TS/TSX, YAML do CI).
- **Gerência informou:** 162 + 38 testes (200) da rc.2 passaram em ambiente independente.
- **Escritos na rc.2 e não executados:** +5 em `test_email_automation.py`, +3 em `test_product_course_delivery.py`, asserções de entrega reescritas, `test_rbac.py` (duplicado → 201).
- **Pytest, alembic, npm ci/audit/typecheck/lint/build, Docker, CI, E2E: NÃO executados.**

## HOMOLOGADO (manualmente)
- Nada nesta versão. Roteiro em `docs/HOMOLOGACAO.md` §G.

## PENDENTE
- Executar tudo que está marcado como não executado; ajustar o que a primeira execução revelar.
- Screenshots das telas principais e aprovação visual da identidade.
- Limpeza real na cópia do banco (relatórios dry-run/pós-limpeza serão gerados pelo script na sua base).
- Decisões de `docs/DECISOES_2.1.0-rc.1.md`.

## Migrations
- `b7d2f4a91c33_add_email_logs` (down_revision `9c4e1a7b2d10`), idempotente.

## Limpeza de dados
- Ferramenta pronta e testada por testes escritos; **nenhum dado foi tocado**. IDs dos cadastros reais ainda precisam ser confirmados no dry-run.
