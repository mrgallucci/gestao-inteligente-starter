# Checklist — Gestão Inteligente reconstruído

Legenda: ✅ concluído | 🔌 depende de provedor/credencial externo | 🚀 configuração de ambiente de publicação

## Fundação
- ✅ Next.js + React + TypeScript + Tailwind.
- ✅ FastAPI + SQLAlchemy.
- ✅ PostgreSQL/Supabase compatível.
- ✅ Alembic restaurado com migration inicial completa.
- ✅ Utilitário `legacy_upgrade.py` para recuperar banco antigo quando o código/histórico de migrations foi perdido.
- ✅ `.env.example` para backend e frontend.
- ✅ Ambiente limpo: sem `.venv`, `node_modules`, `.next` ou segredos no pacote final.

## CRM SargLab
- ✅ Leads B2B/B2C.
- ✅ Campos empresa, cargo, e-mail, telefone e consentimento.
- ✅ Segmento e tamanho de equipe.
- ✅ Dor/gatilho, oferta, formato, orçamento e origem.
- ✅ Próxima ação + data.
- ✅ Edição completa da ficha comercial.
- ✅ Pipeline atual: Lead → Contato realizado → Interessado → Reunião → Proposta → Negociação → Fechado → Pós-venda.
- ✅ Perdido + motivo.
- ✅ Interações e histórico.
- ✅ Follow-ups e próximas ações em agenda única.
- ✅ Kanban.
- ✅ Busca real de Leads.

## Workshop / operação
- ✅ Área Workshop IA com SargLab e SARGTECH.
- ✅ Método CLARO atualizado.
- ✅ Starter Kit com referência atual de 60 prompts.
- ✅ Referências comerciais atuais.
- ✅ Contexto B2B 5–80 pessoas.
- ✅ Pós-venda operacional documentado.

## Marketing / Analytics
- ✅ Campanhas, custo e UTMs.
- ✅ CPL, CAC, ROI e conversão.
- ✅ Dashboard comercial.
- ✅ Customer Analytics B2B/B2C.
- ✅ Análises por segmento, equipe, oferta, formato, cidade, orçamento e objetivo.

## Produtos / Vendas / Financeiro
- ✅ Produtos.
- ✅ Vendas.
- ✅ Pagamento Pago/Pendente/Cancelado/Reembolsado.
- ✅ Venda paga atualiza Lead e pode criar matrícula.
- ✅ Cancelamento/reembolso suspende acesso ao curso.
- ✅ Retorno para Pago pode restaurar matrícula.
- ✅ Resumo financeiro com receita, contas a receber, cancelamentos, reembolsos e saldo líquido.

## LMS
- ✅ Cursos e conteúdos.
- ✅ Upload local de materiais até 50 MB.
- ✅ Admin de conteúdo com criar/editar/desativar/reativar.
- ✅ Matrícula automática vinculada à venda paga.
- ✅ Área do aluno.
- ✅ Progresso e conclusão.
- ✅ LMS Analytics.
- ✅ Indicador simples de possível abandono.
- ✅ Ownership: aluno acessa apenas a própria matrícula.

## Segurança / usuários
- ✅ Usuários admin/vendedor/aluno.
- ✅ Hash Argon2.
- ✅ JWT.
- ✅ Bootstrap do primeiro admin.
- ✅ Gestão visual de usuários.
- ✅ Ativar/desativar conta.
- ✅ Aluno vinculado a Lead único.
- ✅ Cookie HttpOnly + BFF no Next.js.
- ✅ Token não persistido em localStorage.
- ✅ RBAC no backend.
- ✅ Proteção de APIs administrativas.
- ✅ Proteção de CRM/vendas para admin+vendedor.
- ✅ Proteção de LMS e dados próprios do aluno.

## Omnichannel / Automação
- ✅ Painel Omnichannel baseado nas interações do CRM.
- ✅ Insights operacionais por regras.
- 🔌 WhatsApp/e-mail bidirecional real depende da API/provedor escolhido.
- 🔌 IA generativa externa depende do provedor e chave escolhidos.

## Deploy
- ✅ Dockerfiles.
- ✅ `docker-compose.yml` para frontend/backend.
- ✅ Variáveis de ambiente para URL interna do backend e URLs públicas.
- 🚀 Publicação efetiva exige domínio/host, banco e segredos da conta de produção.
- 🚀 Storage persistente é recomendado para uploads em produção.
