# Relatório de entrega — Gestão Inteligente 2.1.0-rc.4 (acumula rc.1–rc.3)

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
