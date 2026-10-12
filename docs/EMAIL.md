# E-mail pós e-book (2.1.0-rc.4)

Código: `backend/email_service.py`; disparo em `POST /api/public/leads/ebook`; log em `email_logs` (`GET /api/email-logs`, admin).

> **Status:** implementado e coberto por testes com provedor simulado. **Nenhum e-mail real foi enviado/validado.** A automação nasce **desligada**.

## Comportamento

- `EMAIL_AUTOMATION_ENABLED=false` (padrão): nada é enviado nem registrado.
- Ligada: após o Lead ser criado e confirmado no banco, uma tarefa em segundo plano envia o e-mail de **entrega do material**.
- **Falha do provedor nunca impede o Lead** (o envio acontece depois do commit, com tratamento total de exceções).
- Resultado sempre registrado em `email_logs` (`enviado` / `falha` / `ignorado`, sem segredos no detalhe). Em caso de **sucesso** cria também uma Interação do Lead: tipo **"E-mail automático"**.
- **Resposta pública uniforme (rc.4):** `POST /api/public/leads/ebook` devolve sempre HTTP 201 com `{"mensagem": "Solicitação registrada com sucesso. Verifique seu e-mail."}` para e-mail novo ou já existente — sem id, status ou flags — para impedir enumeração de e-mails.
- **Download repetido** (e-mail já existente): não cria duplicata nem bloqueia; reutiliza o Lead, registra Interação "Download e-book", grava o consentimento dado no download e dispara o e-mail conforme flag.
- **Produção**: `EMAIL_COMMERCIAL_ENABLED` é ignorado com `APP_ENV=production` até existir descadastro adequado (nenhuma comunicação comercial em produção antes disso).
- **Consentimento**: o e-mail só sai se `leads.consentimento_contato = true` (o endpoint do e-book já exige consentimento).
- **Sem link fictício**: o link do material vem de `EBOOK_DELIVERY_URL` (opcional). O CTA comercial só aparece se `EMAIL_COMMERCIAL_ENABLED=true` **e** `PAID_PRODUCT_URL` for uma URL http(s) válida; caso contrário o e-mail traz só entrega/agradecimento.
- Templates prontos: `entrega_material` (ativo) e `convite_comercial` (**inerte** até haver flag + URL; não é disparado automaticamente nesta versão — ver decisões pendentes).

## Variáveis (ver `backend/.env.example`)

`EMAIL_AUTOMATION_ENABLED`, `EMAIL_PROVIDER` (`console` | `smtp`), `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`, `EBOOK_DELIVERY_URL`, `EMAIL_COMMERCIAL_ENABLED`, `PAID_PRODUCT_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS`.

## Fornecedor

A camada é desacoplada: `EmailProvider.send(message)`. Hoje há `console` (só log, sem envio — use na homologação) e `smtp` (stdlib, serve a qualquer provedor com SMTP). Uma API específica (Resend, SES, etc.) é uma classe nova + uma linha em `build_provider`. **O fornecedor/domínio/remetente não foram escolhidos** (decisão pendente).

## Antes de ativar

1. Definir provedor, domínio e remetente; configurar SPF/DKIM/DMARC.
2. Homologar com `EMAIL_PROVIDER=console` (log) e depois com SMTP para uma caixa de teste própria.
3. Só então `EMAIL_AUTOMATION_ENABLED=true`. A etapa comercial exige produto e URL reais.
4. Limitações: o envio roda no mesmo processo (sem fila/retry); falhas ficam em `email_logs` para reenvio manual. Sem link de descadastro automatizado (o rodapé pede resposta ao e-mail) — avaliar antes de campanhas comerciais.
