"""Limpeza controlada de dados de teste (2.1.0-rc.1).

Regras de segurança (briefing, seção 4):
- DRY-RUN é o padrão: nada é alterado, apenas um relatório é gerado.
- Os registros preservados são resolvidos por ID (`--preserve-lead-ids`), nunca só por nome.
  Nomes servem apenas para LISTAR candidatos no relatório.
- Classificação: REAL / TESTE_PROVAVEL / SISTEMA-ADMIN / INDETERMINADO. Nada é excluído
  por heurística: a exclusão só atinge IDs que um humano aprovou explicitamente num
  arquivo (`--approved`), e nunca um ID preservado.
- INDETERMINADO nunca é excluído automaticamente.
- Produtos, cursos e campanhas NÃO são excluídos por este script (sempre INDETERMINADO ou
  REAL por referência): remoção manual, após decisão.
- A execução roda em UMA transação, confere invariantes (admin e preservados intactos) e
  só faz commit se tudo passar.
- O relatório não contém senhas, hashes nem a URL completa do banco.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    Campaign,
    ContentProgress,
    Course,
    EmailLog,
    Enrollment,
    Interaction,
    Lead,
    Product,
    Sale,
    User,
)

ADMIN_EMAIL = "admin@teste.local"
PRESERVED_NAMES = ["Carlos Madison", "Nathan Catta Preta", "Renato Fonseca", "Daniele"]

CLASS_REAL = "REAL"
CLASS_TEST = "TESTE_PROVAVEL"
CLASS_ADMIN = "SISTEMA-ADMIN"
CLASS_UNDETERMINED = "INDETERMINADO"

# Marcadores conservadores. Servem só para SUGERIR candidatos; um humano aprova.
_TEST_EMAIL = re.compile(r"@([\w.-]*\.)?(teste|test|example|exemplo|mailinator|fake|invalid)([.\w-]*)$", re.I)
_TEST_NAME = re.compile(r"^(teste|test|qa|fulano|ciclano|lead teste)\b", re.I)


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())


def looks_like_test(nome: str | None, email: str | None) -> bool:
    return bool((email and _TEST_EMAIL.search(email.strip())) or (nome and _TEST_NAME.match(nome.strip())))


class CleanupError(Exception):
    """Violação de regra de segurança: a limpeza é abortada."""


# ---------------------------------------------------------------------------
# Inventário e classificação
# ---------------------------------------------------------------------------


def table_counts(db: Session) -> dict[str, int]:
    models = {
        "users": User, "leads": Lead, "interactions": Interaction, "campaigns": Campaign,
        "products": Product, "sales": Sale, "courses": Course, "enrollments": Enrollment,
        "content_progress": ContentProgress, "email_logs": EmailLog,
    }
    return {name: db.query(func.count(model.id)).scalar() or 0 for name, model in models.items()}


def name_candidates(db: Session) -> dict[str, list[dict]]:
    """Leads cujo nome coincide com os cadastros reais informados (para o humano escolher IDs)."""
    leads = db.query(Lead).all()
    result: dict[str, list[dict]] = {}
    for wanted in PRESERVED_NAMES:
        key = normalize(wanted)
        result[wanted] = [
            {"id": lead.id, "nome": lead.nome, "email": lead.email, "status": lead.status}
            for lead in leads
            if normalize(lead.nome) == key or normalize(lead.nome).startswith(key + " ")
        ]
    return result


def _lead_dependencies(db: Session, lead_id: int) -> dict[str, int]:
    enrollment_ids = [e.id for e in db.query(Enrollment.id).filter(Enrollment.lead_id == lead_id)]
    return {
        "interactions": db.query(func.count(Interaction.id)).filter(Interaction.lead_id == lead_id).scalar() or 0,
        "sales": db.query(func.count(Sale.id)).filter(Sale.lead_id == lead_id).scalar() or 0,
        "enrollments": len(enrollment_ids),
        "content_progress": (
            db.query(func.count(ContentProgress.id))
            .filter(ContentProgress.enrollment_id.in_(enrollment_ids))
            .scalar() or 0
        ) if enrollment_ids else 0,
        "email_logs": db.query(func.count(EmailLog.id)).filter(EmailLog.lead_id == lead_id).scalar() or 0,
        "users": db.query(func.count(User.id)).filter(User.lead_id == lead_id).scalar() or 0,
    }


def protected_references(db: Session, preserve_lead_ids: set[int]) -> dict[str, set[int]]:
    """Produtos/cursos/campanhas referenciados por registros preservados (viram REAL)."""
    products: set[int] = set()
    courses: set[int] = set()
    campaigns: set[int] = set()
    if preserve_lead_ids:
        for sale in db.query(Sale).filter(Sale.lead_id.in_(preserve_lead_ids)):
            products.add(sale.product_id)
        for enrollment in db.query(Enrollment).filter(Enrollment.lead_id.in_(preserve_lead_ids)):
            courses.add(enrollment.course_id)
        for lead in db.query(Lead).filter(Lead.id.in_(preserve_lead_ids)):
            if lead.campaign_id:
                campaigns.add(lead.campaign_id)
    if courses:
        for course in db.query(Course).filter(Course.id.in_(courses)):
            products.add(course.product_id)
    return {"products": products, "courses": courses, "campaigns": campaigns}


def build_report(db: Session, preserve_lead_ids: set[int], *, database_name: str = "?") -> dict:
    existing_lead_ids = {row[0] for row in db.query(Lead.id)}
    missing = sorted(preserve_lead_ids - existing_lead_ids)
    preserve = preserve_lead_ids & existing_lead_ids

    leads_out = []
    for lead in db.query(Lead).order_by(Lead.id):
        if lead.id in preserve:
            classe = CLASS_REAL
        elif looks_like_test(lead.nome, lead.email):
            classe = CLASS_TEST
        else:
            classe = CLASS_UNDETERMINED
        leads_out.append({
            "id": lead.id, "nome": lead.nome, "email": lead.email, "classe": classe,
            "dependencias": _lead_dependencies(db, lead.id),
        })

    users_out = []
    for user in db.query(User).order_by(User.id):
        if user.email.lower() == ADMIN_EMAIL:
            classe = CLASS_ADMIN
        elif user.lead_id in preserve:
            classe = CLASS_REAL
        elif looks_like_test(user.nome, user.email):
            classe = CLASS_TEST
        else:
            classe = CLASS_UNDETERMINED
        users_out.append({
            "id": user.id, "email": user.email, "role": user.role, "lead_id": user.lead_id, "classe": classe,
        })

    refs = protected_references(db, preserve)
    catalog_out = {
        "products": [
            {"id": p.id, "nome": p.nome, "classe": CLASS_REAL if p.id in refs["products"] else CLASS_UNDETERMINED}
            for p in db.query(Product).order_by(Product.id)
        ],
        "courses": [
            {"id": c.id, "nome": c.nome, "classe": CLASS_REAL if c.id in refs["courses"] else CLASS_UNDETERMINED}
            for c in db.query(Course).order_by(Course.id)
        ],
        "campaigns": [
            {"id": c.id, "nome": c.nome, "classe": CLASS_REAL if c.id in refs["campaigns"] else CLASS_UNDETERMINED}
            for c in db.query(Campaign).order_by(Campaign.id)
        ],
    }

    summary: dict[str, dict[str, int]] = {}
    for section, items in [("leads", leads_out), ("users", users_out), *catalog_out.items()]:
        counts: dict[str, int] = {}
        for item in items:
            counts[item["classe"]] = counts.get(item["classe"], 0) + 1
        summary[section] = counts

    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "banco": database_name,
        "modo": "dry-run",
        "preservar_lead_ids": sorted(preserve),
        "preservar_lead_ids_inexistentes": missing,
        "candidatos_por_nome": name_candidates(db),
        "contagens": table_counts(db),
        "resumo_por_classe": summary,
        "leads": leads_out,
        "users": users_out,
        **catalog_out,
        "aprovacao_modelo": {
            "lead_ids": [item["id"] for item in leads_out if item["classe"] == CLASS_TEST],
            "user_ids": [item["id"] for item in users_out if item["classe"] == CLASS_TEST],
            "_instrucoes": (
                "Copie este bloco para um arquivo JSON de aprovação, REMOVA os IDs que não "
                "devem ser excluídos e passe com --approved. Nada é excluído sem essa aprovação."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------


@dataclass
class CleanupOutcome:
    deleted: dict[str, int] = field(default_factory=dict)
    skipped: list[dict] = field(default_factory=list)
    counts_before: dict[str, int] = field(default_factory=dict)
    counts_after: dict[str, int] = field(default_factory=dict)
    committed: bool = False


def execute_cleanup(
    db: Session,
    *,
    preserve_lead_ids: set[int],
    approved_lead_ids: set[int],
    approved_user_ids: set[int],
    commit: bool,
) -> CleanupOutcome:
    """Exclui SOMENTE os IDs aprovados, numa transação. `commit=False` faz rollback (ensaio)."""
    if not preserve_lead_ids:
        raise CleanupError("Informe --preserve-lead-ids: a limpeza não roda sem os IDs preservados.")
    existing = {row[0] for row in db.query(Lead.id)}
    if preserve_lead_ids - existing:
        raise CleanupError(f"IDs preservados inexistentes: {sorted(preserve_lead_ids - existing)}")
    overlap = approved_lead_ids & preserve_lead_ids
    if overlap:
        raise CleanupError(f"Aprovação inclui leads preservados: {sorted(overlap)}")

    admin = db.query(User).filter(func.lower(User.email) == ADMIN_EMAIL).first()
    if admin is None:
        raise CleanupError(f"Usuário administrativo {ADMIN_EMAIL} não existe neste banco.")
    if admin.id in approved_user_ids:
        raise CleanupError("Aprovação inclui o usuário administrativo.")
    for user in db.query(User).filter(User.id.in_(approved_user_ids or {-1})):
        if user.lead_id in preserve_lead_ids:
            raise CleanupError(f"Usuário {user.id} está ligado a um lead preservado.")

    outcome = CleanupOutcome(counts_before=table_counts(db))
    preserved_snapshot = {lid: _lead_dependencies(db, lid) for lid in preserve_lead_ids}

    # Leads aprovados cujo usuário vinculado NÃO foi aprovado são ignorados (bloqueio).
    deletable: set[int] = set()
    for lead_id in sorted(approved_lead_ids & existing):
        blockers = [u.id for u in db.query(User).filter(User.lead_id == lead_id) if u.id not in approved_user_ids]
        if blockers:
            outcome.skipped.append({"lead_id": lead_id, "motivo": f"usuário vinculado não aprovado: {blockers}"})
        else:
            deletable.add(lead_id)

    deleted = {k: 0 for k in ("content_progress", "enrollments", "sales", "interactions", "email_logs", "users", "leads")}
    try:
        if deletable:
            enrollment_ids = [e.id for e in db.query(Enrollment.id).filter(Enrollment.lead_id.in_(deletable))]
            if enrollment_ids:
                deleted["content_progress"] = (
                    db.query(ContentProgress)
                    .filter(ContentProgress.enrollment_id.in_(enrollment_ids))
                    .delete(synchronize_session=False)
                )
            deleted["enrollments"] = (
                db.query(Enrollment).filter(Enrollment.lead_id.in_(deletable)).delete(synchronize_session=False)
            )
            deleted["sales"] = db.query(Sale).filter(Sale.lead_id.in_(deletable)).delete(synchronize_session=False)
            deleted["interactions"] = (
                db.query(Interaction).filter(Interaction.lead_id.in_(deletable)).delete(synchronize_session=False)
            )
            deleted["email_logs"] = (
                db.query(EmailLog).filter(EmailLog.lead_id.in_(deletable)).delete(synchronize_session=False)
            )
        if approved_user_ids:
            deleted["users"] = db.query(User).filter(User.id.in_(approved_user_ids)).delete(synchronize_session=False)
        if deletable:
            deleted["leads"] = db.query(Lead).filter(Lead.id.in_(deletable)).delete(synchronize_session=False)
        db.flush()

        # Invariantes: admin e preservados intactos (dependências idênticas).
        if db.query(User).filter(func.lower(User.email) == ADMIN_EMAIL).first() is None:
            raise CleanupError("Invariante violada: administrador removido.")
        for lead_id, before in preserved_snapshot.items():
            if db.query(Lead).filter(Lead.id == lead_id).first() is None:
                raise CleanupError(f"Invariante violada: lead preservado {lead_id} removido.")
            if _lead_dependencies(db, lead_id) != before:
                raise CleanupError(f"Invariante violada: dependências do lead preservado {lead_id} mudaram.")

        outcome.deleted = deleted
        outcome.counts_after = table_counts(db)
        if commit:
            db.commit()
            outcome.committed = True
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    return outcome
