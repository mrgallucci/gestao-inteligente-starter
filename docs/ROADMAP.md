# Roadmap — fora do escopo da entrega atual

Nada abaixo existe no produto entregue nem deve ser apresentado como funcionalidade. Só entra com autorização explícita e depois de uso real.

## Não implementar sem autorização

- WhatsApp/e-mail bidirecional real (depende de provedor, credenciais e webhooks).
- Agente ou IA generativa externa aplicada ao CRM.
- ERP fiscal/contábil (o Financeiro atual é comercial).
- Multiempresa / multi-tenant (e declarar o sistema como SaaS multiempresa).
- Novos módulos apenas para "parecer mais completo".
- Alterações de posicionamento comercial.

## Roadmap futuro (depende de evidência de uso)

1. Integração real de mensageria.
2. IA generativa aplicada ao CRM (resumos, sugestões, apoio comercial).
3. Trilha de auditoria completa de ações por usuário.
4. Responsável por oportunidade (operação com várias pessoas comerciais).
5. Multiempresa, após validação comercial.
6. Melhorias definidas após o uso real no SargLab.

## Endurecimento técnico recomendado (não bloqueia a homologação)

Vêm da auditoria (`AUDITORIA.md`) e não alteram o produto:

- Storage privado para uploads (URL assinada) e fim da dependência de disco local.
- Rate limit/captcha no endpoint público do e-book e no login (no proxy ou na aplicação).
- Revogação de sessão/token (lista de bloqueio ou tokens curtos com refresh).
- Imagens Docker sem root; migrations como etapa separada do deploy com múltiplas instâncias.
- Dividir `main.py` por domínio (CRM, vendas, LMS, usuários) com testes já existentes como rede de segurança.
- Content-Security-Policy no frontend (testando em navegador).
- E2E de navegador (Playwright): iniciado na 2.1.0-rc.1 (`e2e/`, fluxo Produto → Curso → Venda → Matrícula); ampliar para o restante do roteiro de `HOMOLOGACAO.md` após a primeira execução verde.
- E-mail: fila/retry, descadastro automatizado, convite comercial agendado e provedor definitivo (ver `DECISOES_2.1.0-rc.1.md`).
- Hospedar a fonte Inter e substituir o símbolo oficial; lockups com texto em curvas da SARGTECH.
