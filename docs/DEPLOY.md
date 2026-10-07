# Preparação para deploy

## Variáveis obrigatórias do backend

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=480`
- `FRONTEND_URL=https://seu-dominio`
- `UPLOAD_BASE_URL=https://api.seu-dominio/uploads`

## Frontend

- `BACKEND_URL`: endereço usado pelo servidor Next para alcançar o FastAPI. Em Docker Compose: `http://backend:8000`.

## Banco

Execute antes de subir uma nova versão:

```bash
alembic upgrade head
```

O Dockerfile do backend já executa a migration antes do Uvicorn.

## HTTPS

Em produção, sirva o frontend por HTTPS. O cookie de sessão é marcado como `Secure` quando `NODE_ENV=production`.

## Uploads

O filesystem do container pode ser efêmero. Para produção, configure volume persistente ou migre o endpoint de upload para Supabase Storage/S3.

## Serviços externos

WhatsApp, e-mail transacional e IA generativa não têm credenciais incorporadas. Configure um provedor e mantenha os segredos apenas no ambiente do servidor.
