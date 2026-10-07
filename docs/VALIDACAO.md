# Validação da reconstrução

Data da reconstrução: 2026-10-07.

## Backend

- `py_compile` em todos os arquivos Python: aprovado.
- `alembic upgrade head` em banco limpo: aprovado.
- `alembic check` após upgrade: nenhuma operação pendente.
- Smoke test FastAPI: 30 verificações, 0 falhas.
- Fluxos validados no smoke test:
  - bootstrap e login admin;
  - JWT e `/api/auth/me`;
  - campanha + UTMs;
  - Lead SargLab e edição de ficha;
  - interação;
  - produto;
  - curso e conteúdo;
  - venda paga e matrícula;
  - Dashboard, Customer Analytics, Marketing Analytics, LMS Analytics, Financeiro, Omnichannel e Automações;
  - vendedor com CRM liberado e áreas admin bloqueadas;
  - aluno com matrícula própria liberada e área administrativa bloqueada;
  - reembolso suspendendo acesso e pagamento restaurado reativando acesso;
  - follow-up unificado com próxima ação da ficha comercial.
- `seed_sarglab.py` em banco limpo: aprovado.
- `legacy_upgrade.py` testado contra schema antigo mínimo: aprovado.

## Frontend

- 44 arquivos TypeScript/TSX analisados sintaticamente: 0 erros de sintaxe.
- Resolução dos imports locais `@/...`: 0 imports ausentes.
- Frontend varrido para impedir persistência do JWT em `localStorage`.
- Chamadas de Client Components centralizadas no BFF `/api/backend/...`.
- URLs do FastAPI em código server-side podem ser substituídas por `BACKEND_URL`.

O pacote não inclui `node_modules`. Portanto o build completo do Next.js deve ser executado depois de `npm ci`, como parte normal da instalação/deploy.

## Higiene do pacote

Antes da compactação final são removidos:
- `.env` reais;
- `.venv`;
- `node_modules`;
- `.next`;
- bancos locais de teste;
- `__pycache__` e `.pyc`;
- arquivos de upload usados apenas em teste.
