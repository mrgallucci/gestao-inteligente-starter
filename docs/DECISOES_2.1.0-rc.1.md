# Decisões — 2.1.0-rc.1 / rc.2

Status após a revisão da gerência (2026-10-10).

## Decididas pela gerência
| # | Tema | Decisão | Implementação |
|---|---|---|---|
| 1 | Entrega em Vendas | Separar **tipo** ("LMS") de **status** (Acesso liberado / Aguardando pagamento / Acesso suspenso / Não aplicável). | rc.2: `entrega_tipo` + `entrega_status` (+ `Matrícula não gerada`, ver pendência A). |
| 2 | Curso inativo | Venda permitida, com aviso claro. | Aviso no formulário e na listagem. |
| 3 | Convite comercial | Sem agendador nesta versão; CTA só no e-mail de entrega, com flag e URL reais. | Inalterado. |
| 4 | Fornecedor de e-mail | Indefinido; automação desligada até domínio/remetente/ambiente definidos. | Inalterado (`console`/`smtp` genérico). |
| 5 | Descadastro | Nada comercial em produção antes de mecanismo adequado. | rc.2: CTA comercial **bloqueado** com `APP_ENV=production`. |
| 6 | Limpeza | Só em clone, dry-run, aprovação por ID; produtos/cursos/campanhas nunca automáticos. | Inalterado. |
| 7 | `admin@teste.local` | Preservar na homologação. | Inalterado. |
| 8 | E2E | `continue-on-error` só até a 1ª execução verde; depois gate obrigatório. | `continue-on-error` removido após a 1ª execução verde (run `38284823908`: Backend, Frontend, Docker e E2E GREEN), no commit `7c95834e72e512422ccf5047184f3542adbf46f3`; o E2E é agora **gate obrigatório**. A 2ª execução, já com o gate bloqueante (run `38286043714`: Backend, Frontend, Docker e E2E Playwright gate obrigatório GREEN), também ficou GREEN. |
| 9 | Símbolo | Usar assets oficiais v0.1. | rc.3: SVGs oficiais aplicados. |
| 10 | Download repetido do e-book | Reutilizar o Lead, registrar interação, permitir e-mail; resposta pública idêntica para novo/existente. | rc.2 reutilização; rc.4 resposta uniforme (HTTP 201 + corpo genérico). |
| 11 | E2E determinístico | `npm ci` com lockfile; `continue-on-error` só até a 1ª execução verde. | rc.4: workflow com `npm ci`; lockfile versionado pela gerência (Playwright 1.55.1) — `npm ci` + lockfile mantidos. rc.5: corrigidas a sincronização/login do teste e a persistência de `CI_JWT_SECRET`. 1ª execução E2E GREEN (run `38284823908`); `continue-on-error` removido (commit `7c95834e72e512422ccf5047184f3542adbf46f3`); 2ª execução GREEN com E2E bloqueante (run `38286043714`). |

## Ainda em aberto (precisa de resposta)
| # | Tema | Situação |
|---|---|---|
| A | Matrícula retroativa | **Decidido:** estado passa a "Matrícula não gerada" (atenção). Matrícula retroativa automática **não** será implementada (pode alterar direito adquirido); depende de decisão operacional futura. |
| B | Pacote oficial de assets | **Resolvido na rc.3:** SVGs/tokens oficiais v0.1 aplicados (`public/brand`, `docs/identidade`). Pendente apenas versão dos lockups com texto em curvas (opcional). |
| C | Fornecedor, domínio, remetente, URL do e-book e do produto pago | Pendentes (e-mail desligado). |
| D | Descadastro | Definir o mecanismo (link com token + lista de supressão) antes de qualquer envio comercial. |
| E | Limpeza | IDs dos 4 cadastros reais e demais dados reais só no dry-run do clone. |
| F | Fonte Inter | Autorizar hospedagem (OFL). |
| G | Contraste | Texto secundário em `slate-500` (AA) em vez de Steel `#7B879B` (~3,6:1, abaixo de AA para texto corrido). |
| H | `admin@teste.local` | Reavaliar antes do lançamento público. |
