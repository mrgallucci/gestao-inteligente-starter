# Limpeza controlada de dados de teste (2.1.0-rc.1)

Ferramenta: `backend/cleanup_test_data.py` (lógica em `backend/data_cleanup.py`, testada em `tests/test_data_cleanup.py`).

> **Status:** implementada e coberta por testes escritos; **nenhuma limpeza foi executada** em base real. Os IDs dos cadastros reais só podem ser confirmados no relatório dry-run da sua base.

## Princípios

1. **Nunca limpar a única cópia.** Backup → clone → dry-run → execução **na cópia** → validação → promoção (briefing, seção 4).
2. **Dry-run é o padrão.** Sem `--execute`, nada é alterado.
3. **Preservação por ID.** `--preserve-lead-ids` é obrigatório. Os nomes (Carlos Madison, Nathan Catta Preta, Renato Fonseca, Daniele) só servem para *listar candidatos*; homônimos aparecem sinalizados.
4. **Exclusão só com aprovação humana.** O dry-run sugere `TESTE_PROVAVEL` por marcadores conservadores (e-mail `@teste.*`, `@example/exemplo.*`, nome iniciando com "Teste"/"QA"…), mas **só IDs listados no arquivo de aprovação são excluídos**. `INDETERMINADO` nunca é excluído automaticamente.
5. **Preservados são intocáveis**: aprovar um ID preservado, o admin `admin@teste.local` ou um usuário ligado a lead preservado aborta tudo.
6. **Produtos, cursos e campanhas não são excluídos** pelo script (ficam `INDETERMINADO`, ou `REAL` quando referenciados por registros preservados). Remoção deles é manual, depois de decisão.
7. **Transação única + invariantes**: após as exclusões o script confere que o admin existe e que os leads preservados mantêm exatamente as mesmas dependências (interações, vendas, matrículas, progresso, usuário). Qualquer divergência → rollback.
8. Relatórios (`.json` e `.md`) **não contêm senha, hash nem a URL do banco**; só o nome do banco.

## Passo a passo

```bash
# 1. Backup integral do banco atual
DATABASE_URL='...' ./scripts/backup_db.sh ./backups

# 2. Restaurar o backup num banco NOVO (clone), ex.: gestao_homolog_limpa
#    (use scripts/restore_db.sh apontando DATABASE_URL para o clone)

# 3. Dry-run no clone (nada é alterado)
cd backend
DATABASE_URL='<clone>' python cleanup_test_data.py --preserve-lead-ids 12,15,18,21 --report-dir ./relatorios
```

Revise `relatorios/dry-run-*.md`:
- cada nome real tem **exatamente um** candidato? (se houver homônimo, escolha o ID correto);
- a lista `TESTE_PROVAVEL` contém só lixo de teste? Existe algum dado legítimo não listado no briefing?

```bash
# 4. Crie aprovacao.json copiando "aprovacao_modelo" do relatório e REMOVENDO o que não deve sair
#    { "lead_ids": [3, 4], "user_ids": [7] }

# 5. Ensaio (executa tudo e faz ROLLBACK) — confira o relatório
DATABASE_URL='<clone>' python cleanup_test_data.py --preserve-lead-ids 12,15,18,21 \
  --approved aprovacao.json --execute --rehearsal \
  --backup-file ../backups/<arquivo>.dump --expect-db-name gestao_homolog_limpa

# 6. Execução real (commit) — mesmo comando sem --rehearsal
```

`--execute` recusa rodar sem: `--approved`, `--backup-file` existente e não vazio, e `--expect-db-name` igual ao banco conectado (evita atingir a base errada).

## Depois

Validar na cópia: login (`admin@teste.local`), CRM, funil, vendas, LMS e analytics; comparar as contagens do relatório; só então adotar a cópia como base canônica da 2.1.0-rc.1. Para produção, o briefing recomenda banco novo via migrations + importação só dos registros reais aprovados; e reavaliar o e-mail `admin@teste.local` antes do lançamento público.
