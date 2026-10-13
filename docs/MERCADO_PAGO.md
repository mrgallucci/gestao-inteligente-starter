# Mercado Pago — arquitetura no modelo atual (desenho; nada habilitado)

Status: sem rota de webhook, sem checkout, sem credenciais, sem migration. Checkout de produção desligado.

## Fluxo
checkout → pedido (`payment_orders`) → Mercado Pago → webhook validado → `Sale` paga → matrículas → usuário aluno → ativação → acesso.

## Reuso do que existe
`Product` (preço no servidor, nunca do navegador), `Sale` (criada/atualizada pela lógica existente com `status_pagamento="Pago"`, que aplica N1–N4), `Enrollment` (único por lead+curso) e `User.lead_id`.

## Pacote (Programa Completo)
Exige a relação explícita produto → cursos concedidos descrita em `PROPOSTA_MODULOS.md` (tabela de grants), **antes** de ativar checkout. Sem lógica por nome/ID de produto.

## Tabelas novas previstas (só mediante aprovação)
1. `payment_orders`: lead_id, product_id, valor calculado no servidor, status, `external_reference` único, `mp_preference_id`, `sale_id` (nulo até pagar).
2. `payment_events`: `mp_payment_id`, tipo/ação, payload, recebido/processado, resultado; **unicidade** por pagamento+ação (idempotência).
3. `product_course_grants` (ver acima).
4. Token de ativação de aluno (ver abaixo).

## Webhook (quando implementado)
1. Validar assinatura (`x-signature`/`x-request-id`) com segredo em variável de ambiente.
2. Não confiar no corpo: consultar o pagamento na API do MP e conferir status, valor e `external_reference` com o pedido.
3. Gravar evento (idempotente). Se `approved` e pedido ainda não pago, executar o fluxo abaixo.
4. Reembolso/chargeback: via `update_sale_payment_status`.

## Fluxo no `approved` (decisão de 13/10/2026)
1. Localizar ou criar o Lead pelo e-mail.
2. Registrar a venda.
3. Conceder as matrículas da compra (todas as do grant do produto).
4. Verificar se há `User` associado ao Lead.
5. Se não houver, criar `User` com `role="aluno"` em **estado de ativação** (sem senha utilizável).
6. Enviar link de primeiro acesso por e-mail (destino de exemplo: `https://crm.sargtech.com.br/ativar`).
7. O aluno define a própria senha.
8. Só depois usa a área do aluno.

Regras:
- **Nunca enviar senha temporária.**
- Token de ativação: aleatório, armazenado só como **hash**, **uso único**, com **expiração**, invalidado após definir a senha.
- Já existe usuário aluno: apenas conceder a nova matrícula.
- Já existe usuário com o mesmo e-mail como **admin ou vendedor**: **não alterar a role**; marcar o caso para tratamento específico (decisão pendente sobre múltiplos papéis).

## Segredos
`MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET` e chave pública somente em variáveis de ambiente do Render. Nada no repositório nem no site.

## Pendências não técnicas
CNPJ/conta recebedora, termos de reembolso e revisão jurídica.
