# Deploy e operação

Guia para publicar, operar, recuperar e atualizar o Gestão Inteligente. O banco PostgreSQL/Supabase é externo; frontend e backend rodam em containers (ou equivalente na sua plataforma).

## 1. Pré-requisitos de produção

- Domínio(s) com **HTTPS** (proxy reverso, load balancer ou plataforma gerenciada). O compose não termina TLS.
- PostgreSQL/Supabase de produção (use o Session Pooler quando a rede for IPv4).
- Segredos em variáveis de ambiente do servidor — nunca no Git.

## 2. Variáveis de ambiente

### Backend (`backend/.env`)

| Variável | Obrigatória | Observação |
|---|---|---|
| `APP_ENV` | sim | `production` em produção (valida a chave JWT e restringe o CORS). O compose já usa `production` por padrão. |
| `DATABASE_URL` | sim | `postgresql+psycopg://usuario:senha@host:5432/banco` |
| `JWT_SECRET_KEY` | sim | ≥ 32 caracteres aleatórios. `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Em produção a API **não sobe** com o placeholder ou chave curta. |
| `JWT_ALGORITHM` | não | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | não | `480`. O cookie da sessão usa o mesmo prazo. |
| `FRONTEND_URL` | sim | `https://app.seu-dominio` (única origem liberada no CORS, além de `CORS_ORIGINS`). |
| `CORS_ORIGINS` | não | Origens extras separadas por vírgula (ex.: a página do e-book em outro domínio). |
| `UPLOAD_BASE_URL` | sim | `https://api.seu-dominio/uploads` — prefixo dos links de materiais enviados. |

### Frontend

- `BACKEND_URL`: endereço usado pelo **servidor** Next para alcançar o FastAPI. No compose: `http://backend:8000`. O navegador nunca fala direto com o FastAPI; usa o BFF `/api/backend/...`.
- O cookie de sessão é `HttpOnly`, `SameSite=Lax` e `Secure` quando `NODE_ENV=production` (a imagem já usa `production`). Sem HTTPS o login não persiste.

## 3. Primeira publicação

1. Preencha `backend/.env` (a partir de `backend/.env.example`).
2. `docker compose up --build -d`. O backend executa `alembic upgrade head` antes de iniciar o Uvicorn.
3. Confira: `docker compose ps` (backend `healthy`) e `curl https://api.seu-dominio/health/database`.
4. **Crie o primeiro administrador imediatamente** (o endpoint fica aberto enquanto não existir usuário):

   ```bash
   curl -X POST https://api.seu-dominio/api/auth/bootstrap-admin \
     -H 'Content-Type: application/json' \
     -d '{"nome":"Seu Nome","email":"voce@empresa.com","senha":"uma-senha-forte"}'
   ```

   Depois disso o endpoint responde 409 e as contas passam a ser criadas em **Usuários**.
5. Seed opcional do SargLab (produtos, campanha e curso — não cria usuários): `docker compose exec backend python seed_sarglab.py`.
6. Rode o smoke test (seção 7).

Migrations em execução com **mais de uma instância** do backend: rode `alembic upgrade head` uma única vez como etapa de deploy e remova a migration do `CMD` do Dockerfile, para evitar corrida.

## 4. Banco legado

Se o código foi perdido mas o banco antigo existe: **faça backup**, rode `python legacy_upgrade.py` e depois `alembic upgrade head`. Em banco novo, use somente a migration normal.

## 5. Uploads — limitação aceita da primeira entrega

- Os materiais ficam em `backend/uploads` (volume `./backend/uploads` no compose) e são servidos em `/uploads/<uuid>.<ext>` **sem autenticação**. Os nomes são UUID aleatórios, mas quem tiver o link acessa o arquivo — inclusive um aluno cuja matrícula foi suspensa depois de copiá-lo.
- Funciona com **uma única instância** e volume persistente. Em plataformas com disco efêmero ou várias instâncias, os arquivos se perdem/ficam inconsistentes: antes disso, migrar para storage privado (S3/Supabase Storage com URL assinada) — ver `ROADMAP.md`.
- Para materiais realmente sensíveis, prefira hospedar em plataforma de vídeo/arquivos com acesso controlado e cadastrar o link (`https://…`) no conteúdo.
- Faça backup da pasta de uploads junto com o banco.

## 6. Logs, monitoramento e backup

**Logs**: backend e frontend escrevem em stdout/stderr; o compose guarda em `json-file` com rotação (5 × 10 MB por serviço). Consulte com `docker compose logs -f backend`. Em plataformas gerenciadas, use o coletor de logs da própria plataforma.

**Monitoramento mínimo**:
- `GET /health` (processo no ar) e `GET /health/database` (banco acessível; 503 se não). Aponte um monitor externo (UptimeRobot, Better Stack etc.) para os dois e para `https://app.seu-dominio/login`.
- Alerta sugerido: falha em 2 verificações seguidas.
- O healthcheck do compose já reinicia o container do backend se `/health` falhar.

**Backup do banco**:
- Supabase: ative os backups automáticos do projeto e/ou use `scripts/backup_db.sh` (`pg_dump` formato custom) em cron diário, guardando fora do servidor, com retenção definida por você (sugestão: 7 diários + 4 semanais).
- `DATABASE_URL=... ./scripts/backup_db.sh /caminho/backups`

**Recuperação (testar antes de precisar)**:
1. Restaure em um banco de teste: `DATABASE_URL=<teste> ./scripts/restore_db.sh arquivo.dump`.
2. `cd backend && alembic current` deve apontar para o head atual (`alembic heads`).
3. Suba a API apontando para esse banco e rode o smoke test.
4. Restaure também a pasta de uploads.

## 7. Smoke test pós-deploy

```bash
API_URL=https://api.seu-dominio \
FRONTEND_URL=https://app.seu-dominio \
ADMIN_EMAIL=... ADMIN_PASSWORD=... \
VENDEDOR_EMAIL=... VENDEDOR_PASSWORD=... \
./scripts/smoke_test.sh
```

Só faz leituras: saúde da API/banco, páginas do frontend, rotas protegidas sem login (401), e — se você informar contas — login e bloqueio de áreas administrativas para o vendedor. Termina com código ≠ 0 se algo falhar.

## 8. Atualização de versão

1. Faça backup do banco e dos uploads.
2. Atualize o código e confira o `CHANGELOG.md`.
3. `docker compose up --build -d` (migrations rodam no start do backend).
4. Rode o smoke test. Se falhar: volte a imagem anterior; se uma migration já foi aplicada e precisa ser desfeita, restaure o backup (`downgrade` só quando a migration documentar que é seguro).

## 9. Perfis e permissões

Matriz completa no `README.md`. Resumo: **admin** (tudo), **vendedor** (CRM, funil, follow-ups, vendas, omnichannel, automações), **aluno** (apenas as próprias matrículas). As regras são aplicadas no backend; esconder o menu não é a única camada.

## 10. Serviços externos (fora do escopo desta entrega)

WhatsApp/e-mail bidirecional e IA generativa não existem no produto e não têm credenciais. Se forem contratados no futuro, mantenha os segredos apenas no ambiente do servidor.
