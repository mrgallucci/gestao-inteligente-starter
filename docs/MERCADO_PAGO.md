# Mercado Pago — arquitetura no modelo atual (proposta, nada habilitado)

Status: **desenho**. Sem rota de webhook, sem checkout, sem credenciais, sem migration. Checkout de produção desligado.

## Fluxo

checkout → pedido (order) → Mercado Pago → webhook validado → `Sale` paga → `Enrollment` → usuário aluno → acesso.

## Reuso do que existe

- `Product` (preço, ativo) e `Course` (liga a um `Product`) permanecem a fonte de preço e de conteúdo. O preço nunca vem do navegador.
- `Sale` é criada/atualizada com `status_pagamento="Pago"` pela lógica já existente (`create_sale` / `update_sale_payment_status`), que aplica as regras N1–N4 (venda paga não rebaixa "Pós-venda"; nova compra restaura matrícula suspensa; reembolso só suspende se não houver outra venda paga do mesmo curso; restauração preserva "Concluído"/"Em andamento").
- `Enrollment` (único por lead+curso) é criada/restaurada por essa mesma lógica. Nada de criar matrícula pelo webhook por fora dela.

## Tabelas novas permitidas (só mediante aprovação)

1. `payment_orders`: id, lead_id, product_id, valor (calculado no servidor), status (`criado`, `aguardando`, `pago`, `cancelado`, `expirado`), `external_reference` único (nosso id opaco enviado ao MP), `mp_preference_id`, `sale_id` (nulo até pagar), criado_em/atualizado_em.
2. `payment_events`: id, `mp_payment_id`, `event_type`, `payload` (JSON), recebido_em, processado_em, resultado. **Unicidade** em (`mp_payment_id`, `event_type`/ação) para idempotência: o mesmo webhook repetido não gera segunda venda.

## Webhook (quando for implementado)

1. Validar assinatura (`x-signature`/`x-request-id`) com o segredo do webhook em variável de ambiente.
2. Nunca confiar no corpo: consultar o pagamento na API do MP com o token de acesso do servidor e conferir `status`, valor e `external_reference` contra o pedido.
3. Gravar o evento (idempotente). Se `approved` e pedido ainda não pago: criar/atualizar `Sale` pela lógica existente e vincular `sale_id`.
4. Reembolso/chargeback: mesma via de `update_sale_payment_status`.
5. Responder 200 rápido; reprocessar por tabela de eventos, não por retry cego.

## Segredos

`MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET` e chave pública apenas em variáveis de ambiente do Render. Nada no repositório nem no site. O site só chamaria o endpoint de checkout do nosso backend.

## Lacuna a decidir antes de vender: usuário aluno

`Enrollment` liga Lead↔Curso; o acesso exige um `User` com `lead_id`. Hoje o admin cria usuários em `/api/users`. Para vender, é preciso definir: criação automática do `User` (role aluno) no pagamento aprovado e como o aluno define a senha (convite por e-mail com token de uso único). **Decisão pendente.**

## Pendências não técnicas

CNPJ/conta recebedora no Mercado Pago, termos de reembolso e revisão jurídica de privacidade/termos.
