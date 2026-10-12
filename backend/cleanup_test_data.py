"""CLI da limpeza controlada. Veja docs/LIMPEZA_DADOS.md.

Dry-run (padrão, não altera nada):
    python cleanup_test_data.py --preserve-lead-ids 1,2,3,4 --report-dir ./relatorios

Execução (somente numa CÓPIA do banco, após backup e revisão do dry-run):
    python cleanup_test_data.py --preserve-lead-ids 1,2,3,4 --approved aprovacao.json \\
        --execute --backup-file backups/x.dump --expect-db-name gestao_homolog_limpa
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from sqlalchemy.engine import make_url

from data_cleanup import CleanupError, build_report, execute_cleanup
from database import DATABASE_URL, SessionLocal


def _ids(text: str) -> set[int]:
    try:
        return {int(part) for part in text.split(",") if part.strip()}
    except ValueError as exc:
        raise SystemExit(f"IDs inválidos: {text!r}") from exc


def _db_name() -> str:
    url = make_url(DATABASE_URL)
    return (url.database or "?") if url.drivername.startswith(("postgresql", "sqlite")) else "?"


def _markdown(report: dict, outcome=None) -> str:
    lines = [
        f"# Relatório de limpeza — {report['modo']}",
        "",
        f"- Banco: `{report['banco']}`  |  Gerado em: {report['gerado_em']}",
        f"- Leads preservados (IDs): {report['preservar_lead_ids']}",
        f"- IDs preservados inexistentes: {report['preservar_lead_ids_inexistentes']}",
        "",
        "## Candidatos por nome (confirme os IDs!)",
    ]
    for name, items in report["candidatos_por_nome"].items():
        lines.append(f"- **{name}**: " + (", ".join(f"#{i['id']} {i['nome']} <{i['email']}>" for i in items) or "NENHUM"))
        if len(items) > 1:
            lines.append("  - ⚠ mais de um candidato (homônimo): escolha o ID correto.")
    lines += ["", "## Contagens", ""] + [f"- {k}: {v}" for k, v in report["contagens"].items()]
    lines += ["", "## Resumo por classe", ""] + [f"- {k}: {v}" for k, v in report["resumo_por_classe"].items()]
    if outcome is not None:
        lines += ["", "## Resultado", f"- Commit: {'sim' if outcome.committed else 'NÃO (rollback)'}"]
        lines += [f"- Excluídos {k}: {v}" for k, v in outcome.deleted.items()]
        lines += [f"- Ignorados: {s}" for s in outcome.skipped]
        lines += ["", "### Contagens depois"] + [f"- {k}: {v}" for k, v in outcome.counts_after.items()]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--preserve-lead-ids", required=True, help="IDs dos cadastros reais, ex.: 1,2,3,4")
    parser.add_argument("--report-dir", default="./relatorios-limpeza")
    parser.add_argument("--approved", help="JSON de aprovação com lead_ids e user_ids")
    parser.add_argument("--execute", action="store_true", help="Executa de verdade (padrão: dry-run)")
    parser.add_argument("--backup-file", help="Arquivo de backup existente (obrigatório com --execute)")
    parser.add_argument("--expect-db-name", help="Nome do banco esperado (obrigatório com --execute)")
    parser.add_argument("--rehearsal", action="store_true", help="Com --execute: roda tudo e faz ROLLBACK")
    args = parser.parse_args()

    preserve = _ids(args.preserve_lead_ids)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")

    with SessionLocal() as db:
        report = build_report(db, preserve, database_name=_db_name())

        if not args.execute:
            (report_dir / f"dry-run-{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            (report_dir / f"dry-run-{stamp}.md").write_text(_markdown(report))
            print(f"Dry-run concluído. Nada foi alterado. Relatório em {report_dir}/dry-run-{stamp}.(json|md)")
            return 0

        try:
            if not args.approved:
                raise CleanupError("--execute exige --approved (arquivo de aprovação humana).")
            if not args.backup_file or not Path(args.backup_file).is_file() or Path(args.backup_file).stat().st_size == 0:
                raise CleanupError("--execute exige --backup-file apontando para um backup existente e não vazio.")
            if args.expect_db_name != _db_name():
                raise CleanupError(f"--expect-db-name ({args.expect_db_name!r}) difere do banco conectado ({_db_name()!r}).")
            approved = json.loads(Path(args.approved).read_text())
            outcome = execute_cleanup(
                db,
                preserve_lead_ids=preserve,
                approved_lead_ids=set(approved.get("lead_ids", [])),
                approved_user_ids=set(approved.get("user_ids", [])),
                commit=not args.rehearsal,
            )
        except CleanupError as exc:
            print(f"ABORTADO: {exc}", file=sys.stderr)
            return 2

        report["modo"] = "ensaio (rollback)" if args.rehearsal else "execução"
        (report_dir / f"execucao-{stamp}.json").write_text(
            json.dumps({**report, "resultado": outcome.__dict__}, ensure_ascii=False, indent=2, default=str)
        )
        (report_dir / f"execucao-{stamp}.md").write_text(_markdown(report, outcome))
        print(f"{report['modo']} concluída. Relatório em {report_dir}/execucao-{stamp}.(json|md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
